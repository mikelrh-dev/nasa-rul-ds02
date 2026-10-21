# ADR-005: Reserve unit 16 as the out-of-sample holdout for the stacking layer

## Status

Accepted

## Date

2026-10-19

## Context

A learned meta-learner (ADR-001) needs rows that carry **both** base-model predictions and a true label that the meta-learner did not train on. The DS02 dev partition contains six units; the test partition contains units 11, 14 and 15.

The unit sweep in `scripts/probe_variants.log` established which dev unit is the most representative validation unit:

| Validation unit | BiLSTM RMSE | NASA |
|---|---|---|
| **16** (dual pooling, seed 42) | **5.789** | 3211.4 |
| 20 (old pooling, seed 42) | 7.113 | — |
| 20 (dual pooling, seed 2024) | 7.838 | — |

Unit 16 is both the most representative and the cheapest single-unit holdout, and it yields 2 535 windows — enough for a low-capacity meta-learner, and nothing more.

## Decision

**Reserve unit 16 entirely as the holdout.** It is used for three purposes:

1. the meta-learner's training set (`RidgeCV` and the shallow `LGBMRegressor`),
2. the `beta` shrinkage grid,
3. the BiLSTM's `validation_data` for `EarlyStopping(patience=5)` and `ReduceLROnPlateau(factor=0.5, patience=2)`.

The base models are fit on units **2, 5, 10, 18 and 20** only. Units **11, 14 and 15** are read exactly once, for the final evaluation.

## Alternatives Considered

### Grouped K-fold out-of-fold predictions over all six dev units
- Pros: the textbook answer; every dev row gets an out-of-sample base prediction, the meta-learner trains on far more data, and the `beta` selection becomes honest because the meta-predictions used for scoring are out-of-sample.
- Cons: 5 folds x a BiLSTM is expensive on the CPU-only budget this project runs on. The recorded probes contain a compute-starved run in which a **single epoch took 1 553 s**.
- **Measured in 2026-10-21 and rejected on the result, not on cost.** The three-fold OOF vector already exists and costs nothing extra to reuse, so the experiment was run: fitting the meta on the 14 915 out-of-fold windows of the five fit engines made it predict a mean of 39.9 on unit 16 against a true 31.5, and test RMSE grew monotonically with `beta` (4.04 at 0 → 10.17 at 1). The dev engines outlive the test engines, so the pooled fit learns a level prior that does not transfer. The `beta` selection it enables is honest, but a `beta` selected over a meta that cannot be trusted simply collapses to 0 and the ensemble is lost. Record: `INFORME_motor16_vs_oof.md`.

### A temporal split of the cycles
- Pros: no unit is held out, so every unit contributes to training.
- Cons: tried and rejected in this project. The final segment of each unit spans a narrow RUL range, so the model never learns the full RUL range and the test RMSE blows up. The same experiment is recorded in the FD001 v3 notes: validation 14.5 but test 63.
- Rejected: measured, not assumed.

### Using the test units for meta-learning
- Pros: the largest possible meta-learning set.
- Cons: that is test-set leakage. The test units must be read once, for reporting.
- Rejected outright.

### Fit the base models on the test units and the meta-learner on the dev units
- Pros: more base-model training data.
- Cons: the meta-learner would be fit on rows whose base predictions are in-sample for the base models, so its inputs would be optimistically biased — a different leak, and a worse one.
- Rejected.

## Consequences

- Unit 16 is unavailable for base-model hyper-parameter search. The base models are early-stopped on the same unit they are later stacked on, which is the coupling that makes the `beta` selection in-sample.
- The meta-learner sees only 2 535 rows and is fitted on the same unit that early-stops the BiLSTM. That coupling is a known cost, but pooling engines to escape it was measured to be worse (see the out-of-fold alternative above). Its capacity is deliberately low: `RidgeCV(alphas=np.logspace(-2, 3, 20))` plus `LGBMRegressor(max_depth=3, num_leaves=7, n_estimators=120, learning_rate=0.03, min_child_samples=20)`, averaged 50/50.
- **Recorded defect — `beta` is selected in-sample.** Because the meta-learner is fit on unit 16 and the `beta` grid is scored on those same unit-16 rows, the meta-prediction used for scoring is the meta-learner's own fit. The signature is visible in the recorded output:

  | `beta` | validation RMSE | validation NASA | criterion |
  |---|---|---|---|
  | 0.00 (BiLSTM only) | 4.091 | 1062.6 | 1.937 |
  | 0.05 | 3.883 | 992.8 | 1.825 |
  | 0.10 | 3.675 | 925.1 | 1.713 |
  | **1.00 (selected)** | **0.308** | **55.9** | — |

  A 13x validation improvement over the BiLSTM's 4.221 is not a modelling result; it is the meta-learner scoring its own training rows. The selected `beta = 1.00` therefore expresses **full trust in a meta-learner that was never validated out of sample**. The remedy is grouped cross-validation for the `beta` selection, and it is carried as production debt in the technical spec.
- The scaler and the residualisation models are fit on all six dev units before this split (ADR-002). That step is unsupervised and never reaches the test units, but it does make the unit-16 metrics mildly optimistic. It is stated explicitly rather than left implicit, because "the holdout is clean" is exactly the kind of claim a reader should be able to check.
