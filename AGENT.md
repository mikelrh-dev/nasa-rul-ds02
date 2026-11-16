# AGENT.md — NASA DS02 RUL project

## Stack
- Python 3.12.10 (venv .venv; legacy Python 3.10 artifacts were migrated via `LastStepPooling`, no shim needed anymore).
- BiLSTM + LightGBM stacking ensemble for RUL prediction on N-CMAPSS DS02 (bundle C, deployed 2026-11-04, branch `mlflow-pia4`).
- Shipped: hybrid + EMA5 on the imputed base (MAR T30 + ffill with fit-unit medians) RMSE 4.338 / MAE 3.227 / R2 0.9461 / NASA 2336.2 (seed 42); multiseed variability 4.333+-0.040 / NASA 2335.1+-28.7 (from `resultados/bundle_c_multiseed.csv` + manifest; the previous 4.324+-0.107 / 2341.0+-54.1 is historical, commit 72035c3); the old 4.368 from `resultados/comparativa_c_multisemilla.csv` is obsolete; the printed NB06 4.322 and NB05 4.330 means are historical and not regenerable. Full record in `models/ds02_manifest.json`.
- (`models/v2_metrics.json` holds the older FD001 comparison: LightGBM 13.42 / XGBoost 26.16. Do not cite it for DS02.)

## Key facts
- Shipped band: split-conformal in `models/ds02_manifest.json` (dev rows, 17450). R6 band: `src/mia/calibracion_banda.json` (14915 pure OOF rows, units 2/5/10/18/20, no unit 16). Different bands, different uses.
- BiLSTM branch of oof_base_predictions is non-deterministic (p_lgb bit-identical, p_lstm max|diff| ~26 across seeded runs) → band not bit-reproducible.
- Rule-layer measurements: INFORME_reglas_oof.md (repo root). Probe scripts in Hermes scratch dir.

## Conventions
- Commits local-only; never `git push` without explicit order.
- Notebook is build output; package is source of truth. Contract tests in repo.
- Spanish communication with user; concise, student-style.

## References
- Project spec: `openspec/project.md` (workspace local; OpenSpec no se versiona)
- OpenSpec artifacts: `openspec/changes/…` (local)
- Memory: Engram project "nasa-rul-ds02" (decisions/discoveries). This file = stable pointers only.