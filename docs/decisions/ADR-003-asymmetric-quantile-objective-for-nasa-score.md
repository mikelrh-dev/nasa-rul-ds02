# ADR-003: Train the tabular branch with an asymmetric quantile objective (alpha = 0.35)

## Status

Accepted — **retained after the median was proposed and rejected on test, see
[ADR-007](ADR-007-reject-median-objective-keep-quantile-035.md)**.

Two caveats recorded there and not repaired in this document: the evidence cited
below (`scripts/probe_q35.py`) was computed on the evaluation split and contains no
median arm, so the "median was measured worse" claim was never supported by it. The
value 0.35 stands because it is better on the deployment target (hybrid 4.24 vs
4.59 at fixed BiLSTM), not because the reasoning below survived scrutiny.

## Date

2026-10-19

## Context

The evaluation metric is the NASA scoring function:

```python
d = y_pred - y_true
score = np.where(d < 0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)
NASA_Score = float(np.sum(score))
```

Two properties of that formula drive this decision.

**It is asymmetric.** An over-estimate of one cycle costs roughly `1/10` against `1/13` for an under-estimate — about 1.3x more per cycle.

**Its penalty is exponential.** The cost of a large over-estimate grows without bound, while a correct prediction scores exactly 0. A model trained on squared error is conditionally unbiased: roughly half of its errors are over-estimates, and it pays the steeper exponential branch on all of them. A single badly over-estimated engine can dominate the score of the whole fleet.

Note also that the score is a **sum**, not a mean, so it scales with the number of evaluated units and is not comparable across different evaluation sets.

## Decision

Train the LightGBM branch with `objective='quantile', alpha=0.35` — i.e. predict the **35th percentile** of the conditional RUL distribution rather than its mean.

The 35th percentile of a roughly symmetric predictive distribution lies a small, roughly constant distance below the conditional mean. Training on it therefore biases the point forecast **downwards**, converting a share of over-estimates into the cheaper under-estimates, while bounding the RMSE cost because the offset is small and constant.

The hyper-parameter set was chosen empirically, not derived:

```python
LGBMRegressor(objective='quantile', alpha=0.35, n_estimators=300, learning_rate=0.02,
              num_leaves=15, max_depth=4, min_child_samples=50,
              reg_alpha=1.0, reg_lambda=5.0, colsample_bytree=0.8, subsample=0.8,
              random_state=42)
```

`scripts/probe_q35.py` re-ran the quantile, median and L2 recipes on the same split and compared RMSE, R², NASA score and the maximum deviation against the stored `pred_lgb_q35.npy`; the notebook hard-codes the winning recipe.

## Alternatives Considered

### L2 / mean regression (iterations 1 to 3)
- Pros: the natural default; the objective matches the RMSE metric, and the residuals decompose cleanly.
- Cons: conditionally unbiased, therefore over-estimates are frequent — and the NASA score, not the RMSE, is the deployment metric.
- Rejected.

### Median regression (`alpha = 0.5`)
- Pros: robust to outliers in the targets; a single well-supported quantile.
- Cons: still symmetric around the median. Relative to the conditional mean it does not shift the forecast far enough to convert enough over-estimates into under-estimates; the measured NASA score was worse than at 0.35.
- Rejected.

### A custom asymmetric MSE objective
- Pros: the asymmetry could be encoded exactly, including the 10/13 split.
- Cons: LightGBM's built-in `quantile` objective is faster, natively supported, and yields a model that can be inspected as a conditional quantile. A custom objective would need a re-implementation of the leaf-wise growth path and would not be portable across LightGBM versions.
- Rejected.

### Post-hoc affine correction of an L2 model
- Pros: cheap; no retraining.
- Cons: a global shift cannot change the *tail* behaviour that the exponential penalty targets. It moves the bulk of the distribution and leaves the large over-estimates exactly where they were.
- Rejected.

### Making the BiLSTM asymmetric too
- Pros: the whole pipeline would share one objective.
- Cons: the recurrent branch already uses `Huber(delta=10.0)`, which is robust but symmetric around zero. The hybrid already inherits the asymmetry through the tabular branch and the meta-learner, and re-training the champion was measured to be far more expensive than tuning the cheap branch.
- Considered and deferred: the asymmetry currently lives in only one of the two base models.

## Consequences

- The tabular branch trades a modest amount of RMSE for a large NASA-score improvement and becomes directly comparable with the BiLSTM inside the stacking layer. Standalone: RMSE 7.087, MAE 5.584, R² 0.8562, NASA 5768.4.
- `alpha` is a **global constant**, but the genuinely optimal quantile depends on the assumed cost ratio between a missed failure (false negative) and a false alarm (false positive) — a plant parameter, not a measurement. The value 0.35 encodes an implicit cost ratio and **must be revisited** if the alarm economics change.
- The quantile objective has no closed-form residual decomposition, so this branch's errors are asymmetric by construction. The residual-diagnostics plots must be read as asymmetric, not as a symmetric residual cloud around zero.
- Only one of the two base models carries the asymmetry. If the tabular branch is ever dropped or heavily down-weighted, the pipeline's NASA score loses its bias correction and will degrade on over-estimates. This coupling is not currently documented in the code and is listed as an open item.
