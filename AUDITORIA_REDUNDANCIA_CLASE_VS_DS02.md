# Auditoría de redundancia: `clase/` vs `ds02_rul/`

**Fecha:** 2026-11-10  
**Ámbito:** `src/clase/` y `src/ds02_rul/`  
**Nota:** Análisis estructural, sin cambios aplicados. Ver la sección "Decisión" para prioridad.

---

## Resumen ejecutivo

La redundancia real no es "clase contra ds02_rul" en todo el código. Son dos problemas distintos:

1. **Métricas duplicadas**: `_metricas_train/test` en `train_clasicos.py` y `_m_train/test/oof` en `train_mlp.py` repiten lo que ya ofrece `ds02_rul/metrics.py` (`evaluate_predictions`).
2. **El bundle C vive estructuralmente en `clase/` pero es el artefacto DS02**: `train_ensemble_adaptado.py` define particiones, entrena el ensemble y lo que se despliega en `models/` es DS02. Eso hace que utilidades como `puente_c.py` y `evaluar_c_multisemilla.py` (que miden o cargan el bundle C) vivan en `clase/` en lugar de en `ds02_rul/`.

Si no se mueve nada, al menos hay dos frases de consolidación de bajo riesgo: las particiones en un único lugar, y quitar las métricas duplicadas de los scripts de clase.

---

## Diagnóstico archivo a archivo

### `src/clase/dataset_clase.py`

- Qué tiene: definición de columnas (`SENSOR_COLS`, `OP_COLS`, `ALT_COLS`…), particiones estilo clase, carga de la base de la clase (fila), `imputar_ffill()`.
- Quién lo importa: `train_clasicos.py`, `train_mlp.py`, `train_ensemble_adaptado.py` (solo `OP_COLS`, `SENSOR_COLS`, `imputar_ffill`).
- Veredicto: **Quedarse en `clase/`**. Es la ficha de datos del track de clase. No hay equivalente en `ds02_rul/` porque `ds02_rul/data.py` carga un formato distinto (HDF5, ventanas, stride).
- Riesgo de tocar: **2/10**.
- Beneficio de dejarlo igual: **7/10**.

### `src/clase/pipeline_clase.py`

- Qué tiene: `make_pre()`, `make_pipeline(reg)`, `predict_caso_nuevo()` — ColumnTransformer (StandardScaler + OneHot `fase_vuelo`) para los 5 clásicos + MLP.
- Quién lo importa: `train_clasicos.py`, `train_mlp.py`, `utils.py`, `shap_clase.py`, `shap_clase_e2.py`.
- Veredicto: **Quedarse en `clase/`**. Preprocesado exclusivo del track de clase (fila + OneHot `fase_vuelo`). No tiene equivalente en `ds02_rul/`.
- Riesgo: **1/10**.
- Beneficio: **8/10**.

### `src/clase/train_clasicos.py`

- Qué tiene: entrenamiento de 5 clásicos con GridSearchCV + GroupKFold, `_metricas_train/val/test` (duplicación de métricas), `entrenar_todo()` (elegir por val + medir test una vez).
- Quién lo importa: `train_mlp.py` (solo `grupos_validacion` para importancia por permutación), `tabla_final.py` (lee `resultados/comparativa.csv`).
- Veredicto: **Quedarse como script en `clase/`**; limpiar `_metricas_train/test` y usar `evaluate_predictions` desde `ds02_rul/metrics.py`.
- Riesgo de limpiar métricas duplicadas: **4/10** (cambio numérico controlado por redondeo).
- Beneficio: **7/10**.

### `src/clase/train_mlp.py`

- Qué tiene: entrenamiento de 4 experimentos MLP, `_m_train/test/oof` (otra duplicación de métricas), `entrenar_mlp()`, `persistir_e2()`, `importancia_mejor_clasico()`.
- Quién lo importa: `tabla_final.py` (lee `resultados/mlp_comparativa.csv`), `shap_clase_e2.py` (E2_MODEL_PATH, importancia).
- Veredicto: **Quedarse como script en `clase/`**; limpiar `_m_*` duplicadas y mover la responsabilidad de actualizar `models/ds02_manifest.json` (checksum E2) a `ds02_rul/persistence.py`.
- Riesgo: **6/10** (por el manifiesto).
- Beneficio: **7/10**.

### `src/clase/ventanas_adaptadas.py`

- Qué tiene: `ventanas_adaptadas()`, `FIT_UNITS`, `HOLDOUT_UNITS`, `TEST_UNITS`, `_imputar_con_medianas()` — base adaptada + ventaneado usando `build_windows`/`fit_preprocessing` de `ds02_rul/features`.
- Quién lo importa: `train_lgbm_adaptada.py` (5 llamadas), `puente_c.py` (indirecto), `tests/test_clase_ventanas.py`.
- Veredicto: **Límite difuso**. Está en `clase/` porque es la base "adaptada" del track de clase, pero redefine las particiones que también define `train_ensemble_adaptado.py`. Si se mantiene, debería consumir las particiones desde un lugar compartido (`ds02_rul/partitions.py`).
- Riesgo de mover/consolidar particiones: **5/10**.
- Beneficio: **8/10**.

### `src/clase/train_ensemble_adaptado.py`

- Qué tiene: `construir_raw_adaptado()`, `evaluar_semilla()`, `entrenar()`, particiones duplicadas (`FIT_UNITS`, `HOLDOUT_UNITS`, `TEST_UNITS`).
- Quién lo importa: `puente_c.py` (importa `construir_raw_adaptado`, `FIT_UNITS`, `HOLDOUT_UNITS`, `TEST_UNITS`), `evaluar_c_multisemilla.py` (importa `evaluar_semilla`), `scripts/build_ui_cache.py` (importa `construir_raw_adaptado`), `tests/test_clase_bundle_c.py`.
- Veredicto: **Candidato principal a `ds02_rul/`**. Entrena el bundle C, que es el artefacto desplegado de DS02, pero vive en `clase/` y redefine las particiones que luego consume `puente_c.py`.
- Riesgo de mover a `ds02_rul/`: **7/10**.
- Beneficio: **9/10**.

### `src/clase/puente_c.py`

- Qué tiene: puente hacia notebooks 03–05 muertos. Reconstruye `raw`, `dev`, `test`, `result` sin reentrenar, usando `construir_raw_adaptado()` desde `train_ensemble_adaptado.py` y `load_ensemble` desde `ds02_rul/persistence`.
- Quién lo importa: **Nadie aparte de sí mismo**. No hay tests que lo ejecuten.
- Veredicto: **Posible code muerto**. Su propósito declarado ya no existe si esos cuadernos no están. Si se mantiene como utilidad, debería vivir en `ds02_rul/` como carga de artefactos.
- Riesgo de borrar: **3/10**.
- Beneficio: **6/10**.

### `src/clase/evaluar_c_multisemilla.py`

- Qué tiene: estabilidad del bundle C: multisemilla (42, 7, 123), lectura de manifiesto, escritura de `resultados/comparativa_c_multisemilla.csv`.
- Quién lo importa: **Nadie aparte de sí mismo** (script `if __name__ == "__main__"`). No hay tests que lo ejecuten.
- Veredicto: **Límite difuso**. Mide estabilidad de un artefacto DS02, pero vive en `clase/` y depende de `train_ensemble_adaptado.py`. Si se mantiene, debería ser `ds02_rul/evaluar_estabilidad_bundle.py`.
- Riesgo: **4/10**.
- Beneficio: **7/10**.

### `src/clase/tabla_final.py`

- Qué tiene: `construir_tabla()` une 4 fuentes CSV (clasicos, mlp, ventanas, bundle_c) en una tabla con `grano` explícito. `main()` la escribe en `resultados/tabla_final_clase.csv` y declara un campeón por grano.
- Quién lo importa: **Nadie aparte de sí mismo**. Hay test (`tests/test_clase_tabla.py`) que prueba `construir_tabla`.
- Veredicto: **Discusión**. Si el README o informe final lo consume, es presentación legítima. Si no, el test protege código muerto. Bien ubicado en `clase/` si se mantiene.
- Riesgo de borrar: **5/10**.
- Beneficio: **5/10**.

### `src/clase/shap_clase.py` y `src/clase/shap_clase_e2.py`

- Qué tienen: SHAP sobre el mejor clásico (XGB) y sobre E2 (MLP).
- Veredicto: **Quedarse en `clase/`** si se usan. No hay duplicación obvia en `ds02_rul/shap_c.py` porque ese es SHAP del bundle C (modelo distinto).
- Riesgo: **3/10**.
- Beneficio: **6/10**.

### `src/ds02_rul/mlflow_live.py`

- Qué tiene: logging de MLflow del entrenamiento del ensemble.
- Veredicto: **Revisar si está activo**. Si el tracking está congelado, puede ser code zombi. Si está activo, está bien ubicado.
- Riesgo: **4/10**.
- Beneficio: **5/10**.

### `src/ds02_rul/viz.py` (funciones `tabla_modelos`, `comparar_con_base`)

- Qué tienen: resúmenes con media ± desviación, posiblemente de experimentos con múltiples semillas/correcciones.
- Veredicto: **Revisar si se usan**. Si solo se usa para el bundle C actual, parte de esa lógica puede ser zombi. Bien ubicado en `ds02_rul/`.
- Riesgo: **3/10**.
- Beneficio: **4/10**.

### `src/clase/mil_models.py`

- Qué tiene: **NO EXISTE** en el filesystem.
- Veredicto: **N/A**. No hay riesgo ni beneficio.

---

## Cruce de dependencias relevante

- `scripts/build_ui_cache.py` importa `construir_raw_adaptado` desde `src.clase.train_ensemble_adaptado`. Si se mueve ese archivo a `ds02_rul/`, este script también hay que actualizarlo.
- `puente_c.py` importa de `train_ensemble_adaptado.py`: `FIT_UNITS`, `HOLDOUT_UNITS`, `TEST_UNITS`, `construir_raw_adaptado`. Si se mueve el archivo, `puente_c.py` se rompe.
- Las particiones están duplicadas en `ventanas_adaptadas.py` y `train_ensemble_adaptado.py` (mismos valores).
- `train_mlp.py` toca `models/ds02_manifest.json` desde `clase/` — mezcla responsabilidades.

---

## Estructura final propuesta

```
src/
├── ds02_rul/                          ← core DS02 (artefacto desplegable)
│   ├── data.py                        ✓ ya está
│   ├── features.py                    ✓ ya está (build_windows, fit_preprocessing)
│   ├── pipeline.py                    ✓ ya está (make_lgbm, fit_bilstm, run_seed)
│   ├── metrics.py                     ✓ ya está (evaluate_predictions)
│   ├── persistence.py                 ✓ ya está (save/load_ensemble, checksums, manifiesto)
│   ├── ensemble.py                    ✓ ya está
│   ├── residualizer.py                ✓ ya está
│   ├── pooling.py                     ✓ ya está
│   ├── stacking.py                    ✓ ya está
│   ├── smoothing.py                   ✓ ya está
│   ├── conformal.py                   ✓ ya está
│   ├── shap_c.py                      ✓ ya está
│   ├── inference.py                   ✓ ya está
│   ├── viz.py                         ✓ ya está (tabla_modelos, evaluar_clase…)
│   ├── mlflow_live.py                 ← revisar si está activo; si no, quitar
│   ├── partitions.py                  ← NUEVO: FIT_UNITS, HOLDOUT_UNITS, TEST_UNITS (fuente única)
│   ├── evaluar_estabilidad_bundle.py  ← NUEVO: reemplaza clase/evaluar_c_multisemilla.py (si se mantiene)
│   └── load_bundle_dev.py             ← NUEVO: reemplaza clase/puente_c.py si se mantiene como utilidad
│
├── clase/                             ← track de clase PIA 3 (sin artefacto desplegado de DS02)
│   ├── dataset_clase.py               ✓ ya está
│   ├── pipeline_clase.py              ✓ ya está
│   ├── train_clasicos.py              ✓ ya está (script de ejecución); quitar _metricas_* duplicadas
│   ├── train_mlp.py                   ✓ ya está (script de ejecución); quitar _m_* duplicadas; mover registro del manifiesto a ds02_rul
│   ├── ventanas_adaptadas.py          ← quedaría como script de preparación de la base adaptada para el track clase; consume particiones desde ds02_rul/partitions.py
│   ├── train_ensemble_adaptado.py     ← MOVER A ds02_rul/ si el bundle C es artefacto DS02; si se mantiene en clase, al menos dejar de redefinir particiones
│   ├── shap_clase.py                  ← mantener si se usa
│   ├── shap_clase_e2.py               ← mantener si se usa
│   ├── tabla_final.py                 ← mantener si el informe final lo consume; si no, quitar
│   ├── puente_c.py                    ← quitar si es code muerto; si se mantiene, mover a ds02_rul/load_bundle_dev.py
│   ├── evaluar_c_multisemilla.py      ← quitar si se mueve su función a ds02_rul/evaluar_estabilidad_bundle.py; si se queda, más bien en ds02_rul/
│   └── __init__.py
│
└── mia/                               ← reglas de decisión (aparte, no entra en el cruce clase↔ds02)
```

---

## Tabla de cambios con riesgo y beneficio

### Cambios estructurales mayores

| # | Cambio | Riesgo (0–10) | Beneficio (0–10) | Prioridad |
|---|---|---|---|---|
| A | Mover `train_ensemble_adaptado.py` a `ds02_rul/` como `train_bundle_c.py` (o similar), actualizando `puente_c.py`, `evaluar_c_multisemilla.py`, `scripts/build_ui_cache.py` | **7/10** | **9/10** | Alta |
| B | Crear `ds02_rul/partitions.py` con `FIT_UNITS`, `HOLDOUT_UNITS`, `TEST_UNITS`, y consumirlo desde `clase/ventanas_adaptadas.py` y `clase/train_ensemble_adaptado.py` (o su sucesor en A) | **5/10** | **8/10** | Alta |
| C | Quitar `puente_c.py` si es code muerto (sin consumidores activos más allá de sí mismo) | **3/10** | **6/10** | Media |
| D | Mover `evaluar_c_multisemilla.py` a `ds02_rul/evaluar_estabilidad_bundle.py` si se mantiene como utilidad de estabilidad | **4/10** | **7/10** | Media |
| E | Mover la responsabilidad de actualizar `models/ds02_manifest.json` (checksum E2) desde `train_mlp.py` a `ds02_rul/persistence.py` | **6/10** | **7/10** | Media |

### Cambios menores / limpieza

| # | Cambio | Riesgo | Beneficio | Prioridad |
|---|---|---|---|---|
| F | Quitar `_metricas_train/test` de `train_clasicos.py` y usar `evaluate_predictions` desde `ds02_rul/metrics.py` | **4/10** | **7/10** | Baja-media |
| G | Quitar `_m_train/test/oof` de `train_mlp.py` y usar `evaluate_predictions` | **4/10** | **7/10** | Baja-media |
| H | Revisar si `mlflow_live.py` está activo; si no, quitar | **4/10** | **5/10** | Baja |
| I | Revisar si hay funciones zombi dentro de `viz.py` (`tabla_modelos`, `comparar_con_base`); si no se usan, quitar | **3/10** | **4/10** | Baja |
| J | Revisar si `tabla_final.py` se consume; si no, quitar (el test protege código muerto) | **5/10** | **5/10** | Baja |
| K | Revisar si `shap_clase.py` / `shap_clase_e2.py` se usan; si no, quitar | **3/10** | **4/10** | Baja |

### No hacer (código que está bien donde está)

| # | Qué dejar igual | Razón |
|---|---|---|
| L | `dataset_clase.py` en `clase/` | Ficha de datos del track de clase, no hay equivalente en DS02 |
| M | `pipeline_clase.py` en `clase/` | Preprocesado exclusivo del track de clase (fila + OneHot `fase_vuelo`) |
| N | `train_clasicos.py` y `train_mlp.py` como scripts en `clase/` | Entrenamientos del track de clase, no artefacto DS02 |
| O | `ventanas_adaptadas.py` en `clase/` (si se mantiene) | Base adaptada del track de clase; lo que cambia es que consume particiones desde un lugar compartido |
| P | `ds02_rul/` intacto salvo los cambios A–E arriba | El core DS02 ya está bien ubicado |

---

## Decisión sugerida (si se quisiera actuar)

Prioridad alta: **B (particiones compartidas)** y **A (mover el entrenamiento del bundle a DS02)**.  
Limpieza de menor riesgo en paralelo: **C (quitar puente_c si es muerto)** y **F/G (limpiar métricas duplicadas)**.

Si no se hace A por riesgo, la Opción B (particiones) + D (estabilidad en DS02) + E (manifiestos en DS02) + F/G (métricas) ya reducen la redundancia más confusa sin tocar el centro de gravedad del bundle C.

---

*Archivo generado con Codebuff 🤖*
