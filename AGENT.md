# AGENT.md — NASA DS02 RUL project

## Stack
- Python (venv .venv, Python 3.10 artifacts loadable on 3.12 via portability fix).
- BiLSTM + LightGBM stacking ensemble for RUL prediction on N-CMAPSS DS02.
- Best model: LightGBM (RMSE 13.42). Worst: XGBoost (RMSE 26.16). Full comparison in v2_metrics.json.

## Key facts
- Conformal band calibrated on select_beta_grouped(oof..., span=5, use_cycle_feature=False)['oof_calib'] (fold-specific metas, 17450 rows), NOT the shipped meta on _p1_oof_cache.npz.
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