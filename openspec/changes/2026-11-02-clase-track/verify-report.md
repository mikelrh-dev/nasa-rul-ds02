# Verify report: Track de clase DS02 (Fase 4, sin commit)

**Change:** `2026-11-02-clase-track` · **Rama:** `clase-experimental` · **Fecha:** 2026-11-02
**Regla:** sin commit en este paso (a petición expresa).

## Gate

| Check | Resultado |
|---|---|
| `pytest tests -q` (suite completa) | **224 passed, 6 skipped** en 143 s |
| Tests nuevos de clase (dataset/pipeline/clásicos/MLP) | 11 passed (incluidos arriba) |
| `scripts/freeze_rules_evidence.py` | **No verificable aquí: exit 3**, falta instrumento `_p1_oof_cache.npz` (gitignored, nunca existió en este entorno; reconstruirlo exige reentrenar modelos base → fuera de alcance del change). Limitación preexistente, no causada por este change (no toca `mia/`, `models/` ni `src/ds02_rul/`). |
| Congelado (`models/ src/ds02_rul/ mia/ app/cache/ archive/`) | Intacto salvo `models/mejor_modelo_clase.joblib` (nuevo, aditivo; ningún artefacto existente modificado). Respaldo `app/registros_flota.json.hermes-respaldo` restaurado con `git checkout`. |

## Techos formales sin MLflow/n8n (registrado para el change siguiente)

| Apartado | Techo ahora | Qué lo desbloquea |
|---|---|---|
| SAA 9 (tabla + SHAP) | 7 formal / 10 técnico | Capturas MLflow |
| PIA 4 (MLflow) | 0 | Loguear 5+MLP + comparativa en MLflow |
| PIA 5 (app) | 7 | `POST` decisión a n8n desde `clase/app_clase.py` |
| MIA 3 (n8n) | 0 | Flujo real por decisión (HANGAR→Postgres+Calendar+correo, INSPECCIÓN→Sheets, APTO→log) |

## Pendiente fuera de este gate (no bloquea)

- Robustez AC 20-170 en NB 03 (dropout MAR → ΔRMSE + R1 por rachas).
- `requirements.txt`: pinnear `xgboost==3.4.1` (usado, no declarado); `shap` fuera a propósito con fallback documentado.
- Limpieza: borrar `notebooks/*_out.ipynb` (dobles de ejecución) y decidir qué `data/processed/*.parquet` se commitea.
- Decisión README raíz (fusionar `clase/README.md` o convivir).
