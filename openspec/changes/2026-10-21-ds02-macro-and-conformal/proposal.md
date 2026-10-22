# Proposal: report the per-engine metric and a calibrated prediction band

**Change:** `2026-10-21-ds02-macro-and-conformal`
**Status:** Implemented
**Capability:** [`rul-prediction-ds02`](../../specs/rul-prediction-ds02/spec.md)

---

## Why

The headline number is window-weighted, and that weighting flatters the model.
The engine with the worst error (14, RMSE 8.04) also has the fewest windows (760
of 6 196), so it contributes 43.7 % of the squared error while pulling only 12 %
of the average. The window-weighted RMSE was 4.26 and the per-engine macro-RMSE
4.88 on the same predictions: a 0.6-cycle gap between "what the fleet averages"
and "what a randomly chosen engine suffers".

Separately, a point prediction is not deployable in maintenance. There was no
band at all, so there was no way to say how much of the prediction to trust —
and the errors are visibly heteroscedastic (MAE 1.20 below 25 cycles of RUL,
5.26 between 50 and 75).

## What changes

1. **Macro-RMSE as a headline metric.** `metrics.macro_rmse()` returns the three
   per-engine RMSEs and their unweighted mean; the notebook prints it next to the
   window-weighted figure and the manifest records both.
2. **Split-conformal prediction intervals** (`ds02_rul/conformal.py`). Asymmetric
   quantiles of the signed residual, per predicted-RUL bin, calibrated on the
   **out-of-fold** rows of the six development engines — every row there was
   scored by a meta-learner fitted on the other engines, so the band is not
   measured against the meta's own fit.
3. `HybridStackingEnsemble.predict_interval(...)` returns `(point, lower, upper)`.
   `predict()` keeps its signature and its numbers: the API and the contract tests
   are untouched.
4. The manifest records `meta_training` and `conformal`, so the width and the
   sample behind the band are auditable from the artefact alone.

## What was tried and rejected

Fitting the meta-learners on the pooled out-of-fold vector of the five fit
engines (14 915 windows, RUL 0–88) was implemented, measured and reverted. On
unit 16 the pooled meta predicts a mean of 39.9 against a true 31.5, and the test
RMSE grows monotonically with `beta` (4.04 at 0 → 10.17 at 1). The dev engines
live longer than the test engines, so the pooled fit learns a **level prior that
does not transfer**. Full record: [`docs/informes/informe-2026-10-21-motor16-vs-oof.md`](../../../docs/informes/informe-2026-10-21-motor16-vs-oof.md).

## Impact

| | Value |
|---|---|
| Window-weighted RMSE (unchanged protocol) | see manifest `metrics.reference_row` |
| Macro-RMSE | reported alongside; always ≥ the weighted figure on this split |
| Prediction band | 90 % target, per motor coverage reported |
| Base models / `beta` protocol | unchanged |
| Artifacts | `models/ensemble.joblib` (+ root copy), manifest, notebook re-executed |
| Tests | `tests/test_artifact_contract.py` — 10/10 unchanged |
