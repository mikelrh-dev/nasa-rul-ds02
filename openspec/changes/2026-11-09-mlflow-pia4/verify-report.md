# Verification report — MLflow PIA-4

**Change:** `2026-11-09-mlflow-pia4`  
**Branch:** `mlflow-pia4`  
**Date:** 2026-11-09  
**Updated:** 2026-11-10 — 4 `cyc_norm` ablation runs added; store now has 17 runs  
**Scope:** phases 0–7. No notebook was executed or modified.

## Result

All gates pass.

| Check | Command | Result |
|---|---|---|
| Store/export/check (2026-11-09) | `python scripts/backfill_mlflow.py --check` | `OK: 13 runs (9 fila + 4 ventana), export y store coinciden, sin artefactos` |
| MLflow tests | `pytest tests/test_mlflow_backfill.py -q -rs` | **11 passed** |
| Full suite | `pytest tests -q -rs` | **406 passed** in 212.12 s |
| Rules freeze | `python scripts/freeze_rules_evidence.py` | exit 0; OOF coverage **0.901643**; pure OOF rows **14 915** |
| Instrument freeze | `python scripts/freeze_oof_instrument.py --check` | exit 0; 14 915 rows; units `[2, 5, 10, 18, 20]`; band reproduces |
| Contract hashes | `sha256sum -c .pytest_cache/hashes-pre-notebooks.txt` | 5/5 **OK** |
| Notebooks | `git status --short -- '*.ipynb'` | empty |
| MLflow artifacts | `find mlruns -path '*/artifacts/*' -type f` | empty |
| Store/export/check (2026-11-10 update) | `python scripts/backfill_mlflow.py --check` | `OK: 17 runs (9 fila + 4 ventana + 4 ablacion), export y store coinciden, sin artefactos` |

## What was produced

- `mlruns/` — text-only MLflow file store, versioned in git; 17 active runs in `ds02-clase` (9 row + 4 window + 4 ablation).
- `docs/evidencia/mlflow/comparativa.csv` — API export, 17 rows.
- `docs/evidencia/mlflow/compare_fila.png` — 9 row runs with `rmse_val`, `rmse_test`, `tiempo_s`.
- `docs/evidencia/mlflow/compare_ventana.png` — 4 window runs with `rmse_val`, `rmse_test`, `tiempo_s`.
- `docs/evidencia/mlflow/run_prod.png` — `prod__bundle_c` with the 8 metrics and the 4 SHA parameters.
- `docs/assets/dashboard_ds02.png` — Streamlit landing page: bundle C SHA, 6,196 windows, 90 % band.

## Decisions confirmed by the run

- Nine row runs and four window runs are kept separate; no shared comparison table mixes grains.
- The 4 ablation runs (`familia=ablacion_cycnorm`) are the 2×2 of `cyc_norm` ON/OFF × baseline delta over BiLSTM+EMA5, measured in `nb03` on test 11/14/15 (seed 42) and registered without retraining; the full 4×3 grid is in `resultados/ablacion_cycnorm.csv`.
- The row test is read once and only for the selected model: XGB `11.034`, MLP-E2 `7.7211`.
- Window production reference is the manifest: **4.338 / 3.227 / 0.9461 / 2336.2**.
- `bundle__lgbm_c` and `lgbm_adaptada` are the same model; one run, tag `alias=lgbm_adaptada`.
- EMA5 has no `tiempo_s` because it was not timed; the value is absent, not zero.
- `v3_bundle` is a tag (`archivado`), not a parameter.
- The four model SHAs are parameters of `prod__bundle_c`; no model binary is stored in MLflow.

## Notes and limitations

- MLflow 3.18 refuses the filesystem backend unless `MLFLOW_ALLOW_FILE_STORE=true`. The backfill script and the test set that opt-out before importing MLflow; this is not a migration to SQLite or a server.
- Installing MLflow moved `python-dateutil` from 4.0.0 to 2.9.0.post0 as a transitive dependency. `pip check` is clean and the model stack versions (numpy 2.5.4, pandas 3.0.6, scikit-learn 1.9.1, TensorFlow 2.21.0, LightGBM 4.7.0) did not change.
- No `log_model`, autolog, model registry, signature, dataset copy or tracking server is used.
- Phase 8 from the plan (re-executing the seven notebooks) was **not** run; the user does it separately. Notebooks do not import MLflow, so a rerun does not duplicate runs. If NB06 updates `resultados/bundle_c_multiseed.csv`, run `backfill_mlflow.py --write` only if the store should be refreshed from the new CSV.
- The captures are from the real MLflow 3.18 UI (Chrome headless/CDP) and the real Streamlit app; no synthetic comparison table was used.
