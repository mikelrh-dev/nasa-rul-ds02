# `scripts/legacy/` — código de etapas cerradas

Estos scripts **no forman parte del sistema**. Se conservan rotulados para que la
historia del proyecto sea auditable, pero no los importa ningún test, notebook ni
la app. El sistema vigente es `src/ds02_rul/` (bundle C) + `notebooks/01–07`.

> **No ejecutar.** Al moverse un nivel, sus rutas relativas (`parents[1]`) ya no
> apuntan a la raíz del repo sino a `scripts/`. Además dependen de artefactos que
> no están versionados. Si necesitas el código, está también en el historial:
> `git log --follow scripts/legacy/<fichero>`.

| Fichero | Qué era | Por qué está aquí |
|---|---|---|
| `v3_core.py` | Núcleo del pipeline FD001 (`archive/CMaps`) | `archive/CMaps` ya no existe; sustituido por DS02 |
| `v3_lstm.py` | BiLSTM del pipeline FD001 | Ídem |
| `v3_run.py` | Entrenamiento del pipeline FD001 | Ídem |
| `v3_finalize.py` | Cierre del pipeline FD001 | Ídem, y además usaba `bundle` sin definir (`NameError`) |
| `predict.py` | CLI de inferencia v3 (FD001) | Fuera de servicio; el vigente es `scripts/operativo/predict_ds02.py` |
| `repackage_artifact.py` | Migración del ensemble legacy a formato portable | Ejecutada el 2026-10-20; exige Python 3.10 y un `ensemble.joblib` raíz que ya no está |
| `patch_mlflow_live_notebooks.py` | One-shot: insertó las celdas MLflow en los 7 notebooks | Ya aplicado. **No volver a ejecutar**: reescribe los `.ipynb` |
| `run_nb06_0_25.py` | Ejecución puntual de NB06 con recorte 0–25 | One-off ya cumplido |

## Qué los sustituye

| Antes | Ahora |
|---|---|
| `predict.py` (FD001) | `scripts/operativo/predict_ds02.py` + `src/ds02_rul/inference.py` |
| `v3_*` | `src/ds02_rul/bundle_c.py` y los notebooks 03–06 |
| `patch_mlflow_live_notebooks.py` | `src/ds02_rul/mlflow_live.py` (las celdas ya están en los notebooks) |
| `run_nb06_0_25.py` | `notebooks/06_evaluacion_produccion_comparativa.ipynb` |
