# `scripts/legacy/` — código de etapas cerradas

Estos scripts **no forman parte del sistema**. Se conservan rotulados para que la
historia del proyecto sea auditable. El sistema vigente es `src/ds02_rul/`
(bundle C) + `notebooks/01–07`.

Cinco de los ocho se archivaron el **2026-11-15** en `archive/scripts_legacy/`
(ni un test ni un módulo los importaba); esa carpeta salió del repo el
**2026-11-16** y solo vive en el backup externo. Los tres que quedan aquí lo
hacen por **contrato de test**, no por valor.

> **No ejecutar.** Al moverse un nivel, sus rutas relativas (`parents[1]`) ya no
> apuntan a la raíz del repo sino a `scripts/`. Además dependen de artefactos que
> no están versionados. Si necesitas el código, está también en el historial:
> `git log --follow scripts/legacy/<fichero>`.
>
> **Excepción que obliga a no mover los tres restantes:**
> `tests/test_joblib_guard.py` lee la fuente de `predict.py` y de
> `repackage_artifact.py`, y además **importa** `predict`, que hace
> `import v3_core`. Mover cualquiera de los tres rompe la suite, así que
> `v3_core.py` sigue aquí aunque ya no lo use nada vivo.

| Fichero | Qué era | Por qué está aquí | Estado |
|---|---|---|---|
| `v3_core.py` | Núcleo del pipeline FD001 (`archive/CMaps`) | `archive/CMaps` ya no existe; sustituido por DS02 | **se queda**: lo importa `predict.py`, que un test importa |
| `predict.py` | CLI de inferencia v3 (FD001) | Fuera de servicio; el vigente es `scripts/operativo/predict_ds02.py` | **se queda**: `test_joblib_guard` lee su fuente y lo importa |
| `repackage_artifact.py` | Migración del ensemble legacy a formato portable | Ejecutada el 2026-10-20; exige Python 3.10 y un `ensemble.joblib` raíz que ya no está | **se queda**: `test_joblib_guard` lee su fuente |
| `v3_lstm.py` | BiLSTM del pipeline FD001 | Ídem | archivado 2026-11-15 → `archive/scripts_legacy/` |
| `v3_run.py` | Entrenamiento del pipeline FD001 | Ídem | archivado 2026-11-15 → `archive/scripts_legacy/` |
| `v3_finalize.py` | Cierre del pipeline FD001 | Ídem, y además usaba `bundle` sin definir (`NameError`) | archivado 2026-11-15 → `archive/scripts_legacy/` |
| `patch_mlflow_live_notebooks.py` | One-shot: insertó las celdas MLflow en los 7 notebooks | Ya aplicado. **No volver a ejecutar**: reescribe los `.ipynb` | archivado 2026-11-15 → `archive/scripts_legacy/` |
| `run_nb06_0_25.py` | Ejecución puntual de NB06 con recorte 0–25 | One-off ya cumplido | archivado 2026-11-15 → `archive/scripts_legacy/` |

## Qué los sustituye

| Antes | Ahora |
|---|---|
| `predict.py` (FD001) | `scripts/operativo/predict_ds02.py` + `src/ds02_rul/inference.py` |
| `v3_*` | `src/ds02_rul/bundle_c.py` y los notebooks 03–06 |
| `patch_mlflow_live_notebooks.py` | `src/ds02_rul/mlflow_live.py` (las celdas ya están en los notebooks) |
| `run_nb06_0_25.py` | `notebooks/06_evaluacion_produccion_comparativa.ipynb` |
