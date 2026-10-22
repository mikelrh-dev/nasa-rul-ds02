# ADR-004: Use gradient boosting and ridge rather than classical regressors

## Status

Accepted

## Date

2026-10-19

## Context

The pipeline needs two model families that (a) each read the same 50-cycle window in a different way, and (b) make different enough errors that a stacked combination has something to exploit. The classical baselines considered alongside them were **Random Forest**, **k-Nearest Neighbours** and **AdaBoost**.

## Decision

Retain **LightGBM** (gradient-boosted trees, leaf-wise growth) as the tabular branch and **RidgeCV** as the meta-learner. Reject Random Forest, k-NN and AdaBoost as pipeline members.

### Why each rejection

**Random Forest.** Averaged deep trees over a dense, highly collinear 93-dimensional window summary. The sibling FD001 pipeline measured this directly on the same feature construction: with a 30x24 flattened window, Random Forest reached RMSE 16.53 against LightGBM's 13.42 on 100 test engines, at 111.4 s versus LightGBM's 7.7 s. Bootstrap forests also cannot express the asymmetric conditional quantile the NASA metric requires; they would have to be replaced by a quantile-forest variant to compete at all.

**k-Nearest Neighbours.** The RUL signal is a temporal trajectory, not a metric neighbourhood. Two windows with nearly identical 93-dimensional summaries can belong to engines at very different life stages, and a distance metric over standardised, correlated descriptors has no reason to respect cycle ordering. The effective neighbourhood is sparse at 93 dimensions, and a k-NN prediction is piecewise constant — precisely the wrong inductive bias for a smoothly decaying target.

**AdaBoost.** Boosting on a dense, collinear window with a strongly asymmetric, exponential target is dominated by a handful of hard examples, and SAMME-style boosting offers no regularisation path comparable to LightGBM's `min_child_samples` / `reg_lambda` / `max_depth`. AdaBoost had already been superseded by LightGBM as the boosting family before this project began.

### Why the two retained families are complementary rather than redundant

| | BiLSTM (champion) | LightGBM (challenger) |
|---|---|---|
| Reads | the ordered 50-step trajectory | a flat 93-dimensional summary of the same window |
| Mechanism | learned recurrent state, 384-dim pooled head | leaf-wise axis-aligned splits, no explicit ordering |
| Loss | `Huber(delta=10.0)` — robust, symmetric | `quantile(0.35)` — asymmetric, conditional quantile |
| Inductive bias | temporal and smooth | tabular and asymmetric |
| Test RMSE | 5.693 | 7.087 |

Their errors are therefore only partially correlated, which is the precondition for stacking to help at all: a convex average needs *negative* error correlation to beat its best component (ADR-001), and a learned meta-learner needs the two branches to make *different* mistakes.

`RidgeCV` is used as the meta-learner rather than a GBDT because the meta-learning set is small — 2 535 unit-16 windows — and the meta-features are only **two**-dimensional (`[pred_lstm, pred_lgb]` since the clock was removed from this layer). A regularised linear model is the lowest-variance estimator that can combine two predictions without memorising the holdout. The audit confirms the point: the shallow GBDT meta-learner already overfits those 2 535 rows, so a heavier one would be worse still.

Growing the meta-learning set was tried in 2026-10-21 and **rejected on measurement**, not on principle: pooling the 14 915 out-of-fold windows of the five fit engines inflated predictions on unit 16 (mean 39.9 against a true 31.5) because the dev engines live longer than the test engines, and test RMSE grew monotonically with `beta` (4.04 at 0 → 10.17 at 1). More rows did not buy a better mapping; it bought a level prior that does not transfer. See `docs/informes/informe-2026-10-21-motor16-vs-oof.md`.

## Alternatives Considered

### Random Forest / k-NN / AdaBoost as pipeline members
- Pros: well-understood, no new dependencies.
- Cons: as detailed above.
- Rejected.

### A single model family (drop the tabular branch entirely)
- Pros: one artefact, one failure mode, far less to maintain.
- Cons: the hybrid strictly beats the BiLSTM alone on both RMSE and NASA score, so the tabular branch carries real signal that would be lost.
- Rejected.

### A deep tabular model (MLP, FT-Transformer)
- Pros: could model feature interactions without axis-aligned splits; the 93 features are few enough to feed an MLP.
- Cons: no measured gain over LightGBM on 17 450 training windows; it would remove the pipeline's CPU-only feasibility, which is a hard constraint in this environment.
- Rejected.

### Gradient boosting as the meta-learner only (drop Ridge)
- Pros: one fewer meta-model; more capacity to capture non-linear combinations.
- Cons: 2 535 rows and 2 meta-features; capacity is exactly what must be constrained here. The audit already shows the shallow GBDT overfitting, and enlarging the sample with pooled engines is measured to make the level worse, not the fit.
- Rejected; the 50/50 Ridge + shallow-GBDT average is retained because the two meta-models fail differently.

## Consequences

- The pipeline depends on **LightGBM, scikit-learn and Keras only**. No classical-baseline dependency is added.
- The LightGBM branch remains the weaker of the two on RMSE (7.087 vs 5.693) but is the one carrying the asymmetric objective that the NASA score rewards (ADR-003). Its role is not "the better model" but "the differently-biased model".
- **The complementarity claim is qualitative.** No residual-correlation or disagreement-rate diagnostic has been run; the claim is supported by the measured hybrid improvement, not by a direct measurement of error diversity. Adding that diagnostic is an open item in the technical spec, and it matters because the whole stacking layer rests on it.
- The evidence for rejecting Random Forest comes from the sibling FD001 pipeline on a related but different feature construction and dataset. It is strong evidence about the model family, but it is not a DS02 measurement, and DS02 has 4 operating-condition channels that FD001 does not. If Random Forest were to be reconsidered for DS02 specifically, it would need to be measured on DS02, not inherited from FD001.
