# Notebooks — secuencia unificada (histórico 2026-11-03, ver bundle C vigente en `models/ds02_manifest.json` y `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md`)

Reestructuración completada: la secuencia `notebooks/01_eda_y_contexto.ipynb` → `06_evaluacion_produccion_comparativa.ipynb` cuenta la historia completa del modelo (datos, clásicos, MLP, feature engineering, BiLSTM/OOF, meta-ensemble/conformal, evaluación/producción), integrando la parte de clase (nulos, fase_vuelo, clásicos, MLP, LGBM adaptada, ensemble adaptado, SHAP, robustez) sin abrir `notebooks/ds02_ensemble/`.

## Secuencia unificada (6 notebooks)

| # | Notebook | Contenido | Fuente (ds02_ensemble/) | Ejecutado |
|---|----------|-----------|------------------------|-----------|
| 01 | `01_eda_y_contexto.ipynb` | EDA + nulos + fase_vuelo + residualización Ridge + ventanas + feature blocks | 01 (datos + preprocesado) | ✅ 11 celdas, 0 errores |
| 02 | `02_modelos_clasicos_y_mlp.ipynb` | 5 clásicos + GridSearchCV + LightGBM + BiLSTM + baseline | 01 (LGBM + BiLSTM) | ✅ 16 celdas, 0 errores |
| 03 | `03_feature_engineering_secuencial.ipynb` | Ablación cyc_norm + meta-learner + beta + EMA + MLP + SHAP | 02 (ablación + meta + beta + EMA) | ✅ 11 celdas, 0 errores |
| 04 | `04_arquitectura_bilstm_oof.ipynb` | BiLSTM triple pooling + OOF agrupado por motor + arquitectura | 02 (OOF + arquitectura) | ✅ 12 celdas, 0 errores |
| 05 | `05_meta_ensemble_y_conformal.ipynb` | Conformal + multisemilla + diagnósticos + meta-ensemble + beta + EMA | 03 (conformal + multisemilla + diagnósticos) | ✅ 20 celdas, 0 errores |
| 06 | `06_evaluacion_produccion_comparativa.ipynb` | Ensemble con nulos + robustez 3 vías + veredicto D11 + ecuaciones + comparativa | 03 (evidencia + multisemilla) | ✅ 16 celdas, 0 errores |

## Notas

- **Kernelspec:** `ds02-venv` en los 6 notebooks (Python 3.12.10).
- **Rutas:** descubrimiento robusto + `os.chdir(_ROOT)` (sin `../` relativo).
- **Artefactos:** reutilizados en `notebooks/ds02_ensemble/artifacts/` (no se creó nueva carpeta).
- **ds02_ensemble/:** no tocado (se mantiene intacto como referencia).
- **models/:** no tocado en esa fecha (hashes bundle B: ensemble 7acba335, bilstm d0c5ed7f). Vigente bundle C: ensemble `d6c70142…`, bilstm `bf9620a7…` (`models/ds02_manifest.json`).
- **Originales:** movidos a `notebooks/backup/` (01_eda, 02_modelos_A, 03_modelos_B, 04_lgbm_adaptada, 05_ensemble_adaptado).

## Discrepancia con el plan original

El plan original (`plan-reestructuracion-notebooks.md`) proponía 5 notebooks (01-05). La implementación creó 6 (01-06) para separar claramente:
- 04: arquitectura BiLSTM + OOF (antes mezclado en 03)
- 05: meta-ensemble + conformal (antes mezclado en 04)
- 06: evaluación + producción + comparativa (antes en 05)

Esto mejora la legibilidad y la separación de concerns.

## Verificación

- `nbconvert --execute --inplace` ejecutado en los 6 notebooks: 0 errores.
- `pytest tests/`: ver resultado en `scratch/pytest.log`.
- Modelos congelados: sha256 verificados (sin cambios).

## Fecha de completación

2026-11-03
path">
docs/NOTEBOOKS.md