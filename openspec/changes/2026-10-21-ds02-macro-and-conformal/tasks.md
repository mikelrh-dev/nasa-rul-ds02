# Tasks: per-engine metric and calibrated intervals

**Change:** `2026-10-21-ds02-macro-and-conformal`
**Status:** Implemented
**Spec:** [spec.md](spec.md) · [proposal](proposal.md)

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 1.1 | `metrics.macro_rmse()` — per-engine RMSEs and their unweighted mean | Done | returns `per_unit_rmse`, `macro_rmse`, `n_units` |
| 1.2 | Notebook prints macro-RMSE next to the window-weighted figure | Done | both values and their difference printed |
| 1.3 | Manifest records `macro_rmse` | Done | `manifest["macro_rmse"]["per_unit_rmse"]` present |
| 2.1 | `ds02_rul/conformal.py` — fit / apply / coverage | Done | `lower <= point <= upper`, `lower >= 0` |
| 2.2 | Asymmetric quantiles per predicted-RUL bin, global fallback under `min_rows` | Done | bin with `n < 100` reports `source="global"` |
| 2.3 | `HybridStackingEnsemble.predict_interval()` without touching `predict()` | Done | API and dashboard call sites unchanged |
| 2.4 | Calibration on out-of-fold rows, not on the meta's own fit | Done | `select_beta_grouped` returns `oof_calib` covering all 17 450 rows |
| 2.5 | Coverage reported per engine and as "above the band" | Done | one row per test engine |
| 2.6 | Manifest records `meta_training` and `conformal` | Done | both keys in `models/ds02_manifest.json` |
| 3.1 | Re-execute the notebook end to end | Done | 35/35 code cells |
| 3.2 | Contract tests still pass | Done | `pytest tests -q` → 10 passed |

## Rejected in the same change

| Attempt | Measured outcome | Record |
| --- | --- | --- |
| Fit the meta-learners on the pooled OOF vector of the five fit engines | Unit-16 mean 39.9 vs true 31.5; test RMSE 4.04 → 10.17 as `beta` goes 0 → 1; hybrid degrades to the BiLSTM (5.77 vs 4.30) | `docs/informes/informe-2026-10-21-motor16-vs-oof.md` |

The experiment is kept reproducible through `fit_meta_learners` and
`score_beta_holdout` in `src/ds02_rul/stacking.py`, which are documented as the
instrument of the negative result rather than as pipeline code.
