# AGENT.md — NASA DS02 RUL project

## Stack
- Python 3.12.10 (venv .venv; legacy Python 3.10 artifacts were migrated via `LastStepPooling`, no shim needed anymore).
- BiLSTM + LightGBM stacking ensemble for RUL prediction on N-CMAPSS DS02 (bundle B, 2026-10-26).
- Shipped: hybrid + EMA5 ref RMSE 4.251 (mean 4.340 ± 0.101); BiLSTM solo 6.218 ± 0.541; LightGBM solo 7.098 ± 0.034. Full record in `models/ds02_manifest.json`.
- (`models/v2_metrics.json` holds the older FD001 comparison: LightGBM 13.42 / XGBoost 26.16. Do not cite it for DS02.)

## Key facts
- Shipped band: split-conformal in `models/ds02_manifest.json` (dev rows, 17450). R6 band: `mia/calibracion_banda.json` (14915 pure OOF rows, units 2/5/10/18/20, no unit 16). Different bands, different uses.
- BiLSTM branch of oof_base_predictions is non-deterministic (p_lgb bit-identical, p_lstm max|diff| ~26 across seeded runs) → band not bit-reproducible.
- Rule-layer measurements: INFORME_reglas_oof.md (repo root). Probe scripts in Hermes scratch dir.

## Conventions
- Commits local-only; never `git push` without explicit order.
- Notebook is build output; package is source of truth. Contract tests in repo.
- Spanish communication with user; concise, student-style.

## References
- Project spec: openspec/project.md
- OpenSpec artifacts: openspec/changes/2026-10-19-ds02-production-hardening/
- Memory: Engram project "nasa-rul-ds02" (decisions/discoveries). This file = stable pointers only.