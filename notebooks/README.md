# Notebooks — qué hace cada uno y qué `.py` usa

Esta es la fuente autoritativa del mapa notebook → módulo. Si un notebook y este
documento no coinciden, manda el notebook ejecutado; si el notebook importa un
módulo que ya no existe, es un fallo de este mapa.

## Regla de propiedad

```text
src/ds02_rul/   modelo C + contrato compartido + protocolo
src/clase/      rúbrica: ML clásico + MLP + evidencia de clase
scripts/        operaciones (estabilidad del bundle, caché de UI, MLflow)
```

`clase` puede importar `ds02_rul`; `ds02_rul` **nunca** importa `clase`. El test
`tests/test_architecture.py` lo comprueba con AST.

Los notebooks **no escriben en `models/`**. El bundle C se lee con
`ds02_rul.persistence.load_ensemble` (SHA verificado antes de deserializar) y
solo lo escribe `src/ds02_rul/bundle_c.py:entrenar`.

## Secuencia

| # | Notebook | Pregunta que responde | Módulos `.py` que usa | Artefactos que escribe |
|---|---|---|---|---|
| 01 | `01_eda_y_contexto.ipynb` | ¿Cómo son los datos, las fases y las ventanas? | `ds02_rul/data.py`, `ds02_rul/features.py`, `clase/dataset_clase.py`, `clase/ventanas_adaptadas.py`, `ds02_rul/mlflow_live.py` | `resultados/eda_*.png` |
| 02 | `02_modelos_clasicos_y_mlp.ipynb` | ¿Qué rinden los 5 clásicos y los 4 MLP de la rúbrica? | `clase/train_clasicos.py`, `clase/train_mlp.py`, `clase/pipeline_clase.py`, `clase/shap_clase.py`, `ds02_rul/persistence.py`, `ds02_rul/mlflow_live.py` | `resultados/clasicos_real_vs_pred.png`, `resultados/mlp_real_vs_pred.png`, `resultados/shap_importancia.png` |
| 03 | `03_feature_engineering_secuencial.ipynb` | ¿Qué aporta `cyc_norm` y cómo se mide la ablación? | `ds02_rul/puente_c.py`, `ds02_rul/pipeline.py`, `ds02_rul/data.py`, `ds02_rul/mlflow_live.py` | `resultados/ablacion_cycnorm_rmse.png` |
| 04 | `04_arquitectura_bilstm_oof.ipynb` | ¿Cómo es el BiLSTM y cómo se generan las predicciones OOF? | `ds02_rul/puente_c.py`, `ds02_rul/pipeline.py`, `ds02_rul/stacking.py`, `ds02_rul/conformal.py`, `ds02_rul/smoothing.py`, `ds02_rul/ensemble.py`, `ds02_rul/viz.py`, `ds02_rul/mlflow_live.py` | `notebooks/artifacts_c/*.joblib` + `*.npy`, `resultados/ridge_meta_pesos_04.png` |
| 05 | `05_meta_ensemble_y_conformal.ipynb` | ¿Cómo se combinan las ramas, se elige beta y se calibra la banda? | `ds02_rul/puente_c.py`, `ds02_rul/pipeline.py`, `ds02_rul/stacking.py`, `ds02_rul/conformal.py`, `ds02_rul/ensemble.py`, `ds02_rul/smoothing.py`, `ds02_rul/viz.py`, `ds02_rul/metrics.py`, `ds02_rul/data.py`, `clase/ventanas_adaptadas.py`, `ds02_rul/mlflow_live.py` | `resultados/lgbm_adapt_real_vs_pred.png` |
| 06 | `06_evaluacion_produccion_comparativa.ipynb` | ¿Cómo se compara el bundle C con la rúbrica y con la base adaptada? | `ds02_rul/bundle_c.py`, `ds02_rul/data.py`, `ds02_rul/pipeline.py`, `ds02_rul/stacking.py`, `ds02_rul/conformal.py`, `ds02_rul/ensemble.py`, `ds02_rul/smoothing.py`, `ds02_rul/persistence.py`, `ds02_rul/features.py`, `ds02_rul/viz.py`, `ds02_rul/metrics.py`, `ds02_rul/puente_c.py`, `clase/tabla_final.py`, `ds02_rul/mlflow_live.py` | `resultados/loss_curve_c.png`, `resultados/real_vs_predicho_bundle_c.png`, `resultados/ridge_meta_pesos_06.png`, `resultados/bundle_c_cascada_rmse.png`, `resultados/bundle_c_rmse_por_motor.png`, `resultados/real_vs_predicho_viz_c.png`, `resultados/bundle_c_multiseed.csv` |
| 07 | `07_shap_c_bundle_c.ipynb` | ¿Qué canales/features pesan en las tres ramas del bundle C? | `ds02_rul/shap_c.py`, `ds02_rul/data.py`, `ds02_rul/persistence.py`, `ds02_rul/inference.py`, `ds02_rul/metrics.py`, `ds02_rul/mlflow_live.py` | `resultados/shap_bundle_C/{shap_*.csv,bar_*.png,metadata.json}` |

## Detalle por notebook

### 01 — EDA y contexto

- **Módulos directos:** `ds02_rul.data.imputar_ffill` / `SENSOR_COLS`,
  `clase.dataset_clase.elegibles_mar`, `ds02_rul.features.fit_preprocessing`,
  `clase.ventanas_adaptadas.ventanas_adaptadas`.
- **Qué no hace:** no entrena ningún `train_*.py`; no escribe `models/`.
- **MLflow:** la celda 0 tiene el bloque de cabecera colapsado en una sola línea
  comentada; la celda 39 intenta `log_live_run`. Para la regeneración de código
  esto no bloquea, pero no cuentes con un run de NB01 si no se corrige aparte.
- **Salidas:** `resultados/eda_barras_fase.png`, `eda_hist_rul.png`,
  `eda_box_t48_fase.png`, `eda_scatter_alt_mach.png`, `eda_heatmap_corr.png`,
  `eda_t48_resid_fase.png`.

### 02 — Clásicos y MLP

- **Módulos directos:** `clase.train_clasicos`, `clase.train_mlp`,
  `clase.pipeline_clase`, `clase.shap_clase`, `ds02_rul.persistence.verify_artifact_sha256`,
  `clase.pipeline_clase.make_pipeline`.
- **Qué no hace:** no entrena el bundle C; no escribe `models/ensemble.joblib`.
  Los joblib de clase los escriben los scripts `train_clasicos.py` /
  `train_mlp.py`, no el notebook.
- **Salidas:** tres PNG de comparación/importancia.

### 03 — Feature engineering secuencial

- **Módulos directos:** `ds02_rul.puente_c.puente_c` (carga el bundle congelado
  y reconstruye `raw/dev/test`), `ds02_rul.pipeline.ablation_table`,
  `ds02_rul.data` (particiones).
- **Qué no hace:** no reentrena el bundle; la ablación se mide en vivo con la
  tabla en memoria.
- **Salida:** `resultados/ablacion_cycnorm_rmse.png`.

### 04 — Arquitectura BiLSTM + OOF

- **Módulos directos:** `puente_c`, `pipeline.oof_base_predictions`,
  `stacking`, `conformal`, `smoothing`, `ensemble`, `viz`.
- **Artefactos intermedios:** escribe `notebooks/artifacts_c/` con los meta
  learners, la banda conformal y la evaluación. **NB05 los lee**; si reejecutas
  NB05 sin NB04, puede fallar el assert de recarga.
- **Qué no hace:** no escribe `models/`; el único `joblib.dump` va a
  `notebooks/artifacts_c/`.

### 05 — Meta-ensemble y conformal

- **Módulos directos:** `puente_c`, `pipeline.run_seed` / `seed_summary` /
  `make_lgbm`, `stacking.fit_meta_learners`, `conformal.empirical_coverage`,
  `ensemble`, `smoothing`, `viz.dispersion_por_semilla`,
  `clase.ventanas_adaptadas.ventanas_adaptadas`, `ds02_rul.data` (particiones),
  `ds02_rul.metrics`.
- **Dependencia:** recarga `notebooks/artifacts_c/` de NB04.
- **Qué no hace:** no entrena el bundle a disco.

### 06 — Evaluación de producción y comparativa

- **Módulos directos:** `ds02_rul.bundle_c` (solo constantes `EPOCHS` /
  `EPOCHS_OOF`), `ds02_rul.data.construir_raw_adaptado` y particiones,
  `pipeline`, `stacking`, `conformal`, `ensemble`, `smoothing`, `persistence`,
  `features.build_windows`, `viz.real_vs_predicho`,
  `clase.tabla_final.construir_tabla`.
- **Qué no hace:** no llama `bundle_c.entrenar()` ni escribe el bundle. Lee
  `models/ensemble.joblib` con `load_ensemble`; la celda 43 sí escribe
  `resultados/bundle_c_multiseed.csv` desde el notebook.
- **Ojo:** el `bundle_c_multiseed.csv` del notebook y
  `scripts/operativo/evaluate_bundle_stability.py` son dos escritores del mismo tipo de
  evidencia; no los mezcles en la misma corrida sin decidir cuál manda.

### 07 — SHAP del bundle C

- **Módulos directos:** `ds02_rul.shap_c.ejecutar_shap_c`; dentro, `data`,
  `persistence`, `inference` y `metrics`.
- **Qué no hace:** no entrena ni reescribe `models/`; solo carga el bundle con
  SHA verificado y escribe la explicación.
- **Salida:** `resultados/shap_bundle_C/` (tres CSV, tres PNG y `metadata.json`).

## Orden de ejecución

```text
01 → 02 → 03 → 04 → 05 → 06 → 07
```

- **04 antes de 05** por `notebooks/artifacts_c/`.
- **06 después de 03/04/05** si quieres que las tablas comparativas encuentren
  los CSV/artefactos que esos notebooks dejan.
- **07 es independiente** del resto, pero necesita el bundle C y los parquet
  adaptados.

## Reglas para reejecutar

1. Trabaja desde la raíz del repo; los notebooks hacen `os.chdir(_ROOT)`.
2. No borres `notebooks/artifacts_c/` ni `resultados/` antes de terminar: NB05 y
   NB06 leen artefactos de NB04.
3. No ejecutes `bundle_c.entrenar()` desde un notebook: escribe `models/`.
4. Si reejecutas para regenerar evidencia, haz una copia de `mlruns/` antes; los
   runs live se añaden, no sustituyen a los históricos.
5. Si un import falla, revisa primero `tests/test_architecture.py` y este mapa;
   no vuelvas a mover módulos a `clase/` para “arreglarlo”.
