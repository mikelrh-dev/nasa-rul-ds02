# ADR-001: Reject linear blending in favour of a learned stacking meta-learner

## Status

Accepted

## Date

2026-10-19

## Context

The pipeline combines two base learners with deliberately different inductive biases: a gradient-boosted tree ensemble over flattened window statistics, and a bidirectional LSTM over the raw 50-step trajectory. The first two experimental iterations combined them with a **convex** combination.

| Iteration | Combination | BiLSTM RMSE | LightGBM RMSE | Blend RMSE | Blend NASA |
|---|---|---|---|---|---|
| 1 | Fixed weights `0.6 * LGBM + 0.4 * BiLSTM` | 6.939 (NASA 5278) | 10.82 | 8.091 (NASA 6747) | worse than the best component |
| 2 | Inverse-variance weights `0.23 LGBM + 0.77 BiLSTM` | 6.874 (NASA 5055.2) | 10.917 (NASA 12155.3) | 7.180 (NASA 5542.1) | still worse than the BiLSTM |

The failure is structural, not a matter of picking better weights. A convex combination `p = w·p_a + (1-w)·p_b` can only beat its best component when the two error series are strongly **negatively** correlated; otherwise the blend inherits the dominant branch's bias and adds the other branch's variance. Here the two branches were reading the same contaminated signal — in iteration 1 neither saw the flight regime at all, and in iteration 2 the tabular branch was fed noisy statistics of `W` — so their errors were positively correlated and any direct average degraded the stronger model.

## Decision

Replace the fixed-weight average with a **learned meta-learner**.

1. The two base predictions and the normalised cycle are stacked into `Z = [pred_lstm, pred_lgb, cyc_norm]`.
2. Two low-capacity regressors are fit on the reserved holdout: `RidgeCV(alphas=np.logspace(-2, 3, 20))` and a deliberately shallow `LGBMRegressor(max_depth=3, num_leaves=7, n_estimators=120, learning_rate=0.03, min_child_samples=20)`. Their predictions are averaged 50/50 into `p_meta`.
3. The meta prediction is merged back with the BiLSTM through a shrinkage factor `beta ∈ [0, 1]`:
   `p_raw = p_lstm + beta · (p_meta - p_lstm)`.
4. `beta` is selected on the holdout with a combined criterion `rmse_val/rmse_lstm_val + nasa_val/nasa_lstm_val` over the grid `np.linspace(0, 1, 21)`.
5. `p_raw` is then causally smoothed per unit (ADR-006) and clipped at 0.

The BiLSTM is the **champion**: the shrinkage bounds the damage the meta-learner can do when it is mis-specified, and `beta = 0` reproduces the BiLSTM exactly.

## Alternatives Considered

### Fixed weights (iteration 1)
- Pros: no holdout required, zero extra artefacts.
- Cons: measured worse than the best component on both RMSE and NASA score.
- Rejected: the convex-combination argument above.

### Inverse-variance weights on validation (iteration 2)
- Pros: adapts the weights to the observed error scale; measured better than fixed weights.
- Cons: still worse than the BiLSTM alone; weights are a function of validation noise and of the two models' variances rather than of their complementary structure.
- Rejected: same structural objection.

### Champion-challenger (run the BiLSTM, keep LightGBM as fallback)
- Pros: zero risk of regression, no extra artefact.
- Cons: forfeits the measured hybrid gain (RMSE 5.522 vs 5.693; NASA 3435.1 vs 3822.2) and leaves the tabular branch contributing nothing.
- Rejected: it discards signal that is demonstrably there.

### Pure stacking without the `beta` shrinkage
- Pros: one fewer hyper-parameter; the meta-learner already blends the two branches.
- Cons: gives the meta-learner full control of the output with no bound on its damage.
- Considered and modified: the shrinkage is retained because it makes the meta-learner's influence an explicit, auditable quantity — and because its selection is the single defect recorded in the technical audit (see Consequences).

## Consequences

- The hybrid now **strictly dominates** every individual model on both metrics: RMSE 5.522 (BiLSTM 5.693, LightGBM 7.087) and NASA score 3435.1 (BiLSTM 3822.2, LightGBM 5768.4).
- The pipeline gains a third trained artefact and a third failure mode. The meta-learner can only be fit on held-out rows, which is precisely what forces the reservation of unit 16 (ADR-005).
- **Recorded defect.** The meta-learner is fit on unit 16 and the `beta` grid is scored on those same unit-16 rows, so `beta` is selected in-sample. The signature is visible in the recorded output: at `beta = 1.00` the validation RMSE is 0.308 against the BiLSTM's 4.221 — an implausible 13x gain that is really the meta-learner scoring its own training rows. The selected `beta = 1.00` therefore expresses full trust in a meta-learner that was never validated out of sample. Tracked as production debt; the fix is grouped cross-validation for the `beta` selection.
- The complementarity claim is **quantitative but indirect**: the hybrid improvement is the evidence that the two branches make materially different errors. No residual-correlation or disagreement-rate diagnostic has been run, so the mechanism is inferred rather than measured. Adding that diagnostic is an open item in the technical spec.
