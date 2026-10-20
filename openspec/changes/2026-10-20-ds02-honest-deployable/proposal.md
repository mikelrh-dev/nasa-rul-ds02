# Proposal: DS02 honest protocol and deployable artifact

**Change:** `2026-10-20-ds02-honest-deployable`
**Status:** Implemented
**Date:** 2026-10-20
**Capability:** [`rul-prediction-ds02`](../../specs/rul-prediction-ds02/spec.md)
**Supersedes scope of:** `2026-10-19-ds02-production-hardening` (phases 0-2 executed; 3-4 partially)

---

## Why

Three defects blocked the DS02 pipeline from being either deployable or honest, and
all three were reproduced rather than inferred:

1. `ensemble.joblib` raised `AttributeError: Can't get attribute
   'HybridStackingEnsemble' on <module '__main__'>` in the repository's own
   interpreter (Python 3.12.10), because both classes were defined inside the
   notebook.
2. Even with the `__main__` dependency shimmed away, it raised
   `ValueError: bad marshal data (unknown type code)`, because the Keras graph
   embedded `Lambda(lambda z: z[:, -1, :])` and `marshal`'s code-object format is
   Python-minor-version specific.
3. The preprocessing objects (`scaler`, `scaler_w`, `poly_w`, the 14 residual
   `Ridge` models, `res_scaler`) were fitted on **all six** dev units before the
   holdout split, and `beta` was selected on the same unit-16 rows that fitted the
   meta-learners — the recorded validation RMSE of 0.308 against the BiLSTM's 4.221
   is the signature of that in-sample selection.

A fourth problem was methodological: claims about the cost of `cyc_norm` were
quoted from iteration 3, a *different design* (78 features, no residualisation),
and a validation table asserted numbers the code had never produced.

## What changes

| Area | Change |
| --- | --- |
| Importability | `SensorResidualizer`, `HybridStackingEnsemble`, `causal_ema_by_unit`, `calculate_nasa_score` move to `src/ds02_rul/` (verbatim behaviour) |
| Serialisation | Bare `Lambda` replaced by a registered `LastStepPooling` layer; the graph is persisted natively as `models/bilstm_ds02.keras` and is **not** pickled inside the bundle |
| Migration | `scripts/repackage_artifact.py` transfers the legacy weights under Python 3.10 → `npz` → rebuild in 3.12 with `set_weights`. **Zero gradient steps**, max abs difference `0.000e+00` |
| Leakage | `fit_preprocessing` is called on the fit units only; the split precedes every `.fit()` |
| Calibration | `beta` selected by grouped out-of-fold cross-validation (`GroupKFold`, 3 folds, per-fold refit of transforms); the legacy in-sample protocol retained as a labelled diagnostic |
| Ablation | `cyc_norm` on/off and a per-engine healthy-baseline delta are **measured** on the test units, not asserted |
| Reporting | Three seeds (`42, 7, 123`) reported as mean ± standard deviation |
| Ingestion | Silent C-MAPSS FD001 fallback removed; `load_ds02` raises and names the paths it probed |
| Provenance | `models/ds02_manifest.json` records shape, partition, seed, environment, fingerprint and metrics; `save_ensemble` refuses to write a bundle whose scaler is not 18-channel / `n_op != 4` |
| Environment | The `.venv` is registered as the `ds02-venv` kernel and the notebook declares it, so recorded outputs come from the repository environment |

## Rollback plan

Additive: the legacy artifact is preserved under `models/legacy/` and the previous
notebook remains recoverable from `scripts/build_02_notebook.py` history. Restoring
the prior state means checking out the previous builder revision and copying
`models/legacy/` back over `models/`.

## Artifacts that stay compatible

- `scripts/predict.py`, `models/v3_bundle.joblib`, `alarm_policy.json`,
  `psi_reference.json` and the whole FD001 pipeline are untouched.
- `scaler.joblib` keeps its 18-channel contract and its DS02 fingerprint.

## Not done (and why)

- `beta` is selected on a single seed; the multi-seed spread is reported for the
  metrics but not folded into the `beta` estimate.
- The `beta` selection refits base models 3 times; a nested refit per sample was
  explicitly out of budget.
- Docker images were written but not built in this environment (no daemon check
  was performed); `docker compose config` is the verified artefact.
