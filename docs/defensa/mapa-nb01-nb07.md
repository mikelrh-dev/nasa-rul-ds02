# Mapa celda → .py → frase de 20 s (NB01–07)

> Cómo leer este mapa: **celda = índice 0-based** (`0idx`, como en
> `exploracion_cero_nb01-07.json`). En Jupyter el contador visible es 1-based
> (`1idx = 0idx + 1`); si alguien dice «celda N» sin aclarar, pregunta si es
> 0idx o 1idx. **Frase de 20 s** = lo que un junior puede decir en vivo sin
> contradecirse. Todo sale de código con `path:línea` o de `resultados/`;
> ninguna frase inventa números.
>
> Regla de defensa: si te preguntan *«¿dónde se entrena?»*, la respuesta es
> siempre **en el `.py` indicado en la columna `.py` oficial** (columna
> «entreno oficial» en cada tabla). Los notebooks **no invocan** esos
> entrenos oficiales salvo que la tabla diga explícitamente «sí lo invoca»;
> en NB02 c5/c20 y NB05 c30 lo *duplican sin escribir* (ver filas marcadas
> con «DUPLICA, no invoca»).

#### Numeración 0idx/1idx + ruta de `models` (corregida 2026-11-10)

- **0idx vs 1idx:** este mapa cita `0idx` (índice literal en el `.ipynb`).
  En Jupyter el contador visible es `1idx = 0idx + 1`. Si alguien dice
  «celda N» sin aclarar, pide 0idx/1idx antes de saltar. Casos que muerden:
  NB05 c29 es Markdown de procedencia y c30 (0idx) / c31 (1idx) es el code
  de LGBM; NB02 c5 0idx / c6 1idx y c20 0idx / c21 1idx son los entrenos
  en vivo. Los pies Markdown junto a cada code (NB02 c5/c20, NB05 c30)
  repiten esta numeración en el punto de error.
- **Ruta de `lgbm_adaptada.joblib` (corregida 2026-11-10):**
  `src/clase/train_lgbm_adaptada.py:61` ya escribe en
  `src/clase/models/lgbm_adaptada.joblib` (con `/`, no `src.clase`). No queda
  carpeta fantasma; NB05 c38 carga el joblib real. La misma nota vive en el pie
  de NB05 c30.

## 0 · Escritores oficiales (la enciclopedia de procedencia)

| Artefacto | Escritor `.py` oficial (función:líneas) | Escribe | Quién lo lee |
|---|---|---|---|
| `resultados/comparativa.csv` + `models/mejor_modelo_clase.joblib` | `src/clase/train_clasicos.py:108` `entrenar_todo()` (escribe `to_csv:157`, `joblib.dump:158`) | CSV + joblib | NB02 c3 (ancla), c11/c15/c32 (carga) |
| `resultados/mlp_comparativa.csv` + `models/mejor_modelo_clase_E2.joblib` (E2) | `src/clase/train_mlp.py:107` `entrenar_mlp()` (escribe `to_csv:137`, `joblib.dump E2:142`, `E2_MODEL_PATH:50`) | CSV + joblib | NB02 c17 (ancla), c25 (re-fit, no carga) |
| `resultados/comparativa_ventanas.csv` + `src/clase/models/lgbm_adaptada.joblib` | `src/clase/train_lgbm_adaptada.py:34` `entrenar()` (escribe `to_csv:60`, `joblib.dump:61` en `src/clase/models` ) | CSV + joblib | NB05 c28 (ancla), c38 (carga joblib oficial) |
| **Bundle C** `models/ensemble.joblib` + `bilstm_ds02.keras` + `scaler.joblib` + `models/ds02_manifest.json` + `resultados/comparativa_bundle_c.csv` + `bundle_c_por_motor.csv` + `real_vs_predicho_bundle_c.png` | **`src/ds02_rul/bundle_c.py:entrenar`** → **`src/ds02_rul/persistence.py:202` `save_ensemble()`** (`OUT_DIR = _ROOT/models:64`; también escribe CSV:188-189 y PNG:202) | 7 artefactos | NB03–NB07 vía `puente_c()` / `load_ensemble` (NB06 c19/c53/c56, NB07 c3 vía `shap_c`) |
| `resultados/tabla_final_clase.csv` | `src/clase/tabla_final.py:22` `construir_tabla()` + `:68` `main()` (`to_csv:76`) | CSV | NB06 c49 (lee), c52 (reconstruye y exige igualdad, **no** escribe) |
| `resultados/shap_bundle_C/` (3 CSV + 3 PNG + `metadata.json`) | `src/ds02_rul/shap_c.py` `ejecutar_shap_c` (llamada única desde NB07 c3) | Explicación, no modelo | NB07 c4/c5 |
| `notebooks/artifacts_c/nb2_*` (3 joblib + 3 npy) | **NB04 c31** (`joblib.dump`/`np.save` propios) | Estado intermedio ignorado por git | NB05 c6 (recarga, sin re-entrenar NB04) |

> `models/mejor_modelo.joblib` **no tiene escritor**: es copia manual idéntica
> de `models/mejor_modelo_clase.joblib` (mismo tamaño 526049 bytes). Ver
> `models/README.md`. Ningún notebook ni script hace la copia.
>
> Cita corta para el bundle C (defender en 20 s):
> «El bundle C no se entrena en notebooks: lo escribe
> `bundle_c.entrenar()` 183-222 en `models/` vía
> `save_ensemble` `persistence.py:202` y los notebooks solo lo leen.»

---

## NB01 · `01_eda_y_contexto.ipynb` — EDA, no entrena (34 celdas, 13 code)

**En 20 s:** «Esto es EDA de datos, no entrena ningún modelo; las figuras son
solo presentación.» `execution_count` 1-13 en todo el code (ejecutado).

| Celda (0idx) | Hace (1 línea) | `.py` / función real | Frase de 20 s |
|---|---|---|---|
| c0 (`exec=1`) | Bootstrap `_ROOT`/`cwd`/`sys.path` | — (entorno) | «La celda 0 no es lógica del modelo: fija raíz, cwd y sys.path.» |
| c5 (`exec=2`) | Carga `train/test.parquet` + auditoría, imprime formas/fase/RUL | Duplica lista `SENSORES` inline vs `dataset_clase.SENSOR_COLS` | «Cargo los parquet ya procesados; la lista de sensores inline duplica `SENSOR_COLS` pero no entrena.» |
| c8 (`exec=3`) | Calidad: duplicados, `RUL<0`, Mach fuera, nulos por sensor, RUL por fase | Lee `auditoria_nulos.json`; escritor: `dataset_clase` (no invocado aquí) | «Reviso calidad sobre la auditoría ya calculada; no recalculé el MAR aquí.» |
| c11 (`exec=4`) | Fig.1 barras `fase_vuelo` → `eda_barras_fase.png` | Ninguna (display) | «Solo presentación: barras de fase desde el parquet.» |
| c13 (`exec=5`) | Fig.2 hist RUL + Fig.3 box T48 por fase → 2 PNG | Ninguna (display) | «Solo presentación: dos figuras, sin lógica.» |
| c15 (`exec=6`) | Fig.4 scatter alt vs Mach por fase → `eda_scatter_alt_mach.png` | Lee `fase_vuelo` del parquet (no llama `asignar_fase_vuelo`) | «El scatter usa la fase ya venida en el parquet; los umbrales 18k/26k+0.65 viven en `dataset_clase.asignar_fase_vuelo`.» |
| c17 (`exec=7`) | Fig.5 heatmap correlación → `eda_heatmap_corr.png` | Ninguna (display) | «Solo presentación: heatmap con columnas inline.» |
| c21 (`exec=8`) | Dos ligas fila vs ventana + unidades fit/hold/test | Literales que duplican `FIT_UNITS` de `data.py` / `ventanas_adaptadas` | «Explico las dos ligas con literales que copian `FIT_UNITS`; el contrato oficial vive en `data.py`.» |
| c23 (`exec=9`) | Recalcula MAR en vivo con `elegibles_mar` | **Sí usa** `dataset_clase.elegibles_mar` | «Recalculo el MAR con la función oficial `elegibles_mar`, no a mano.» |
| c25 (`exec=10`) | Imputación en vivo (medianas fit-units + ffill) | **Sí usa** `dataset_clase.imputar_ffill` + `SENSOR_COLS` | «Imputo con la función oficial `imputar_ffill`; las medianas inline anticipan `medianas_train` del `.py`.» |
| c27 (`exec=11`) | Residualización en vivo (14 Ridge por sensor) | **Sí usa** `ds02_rul/features.fit_preprocessing` (Ridge **físico**) | «Residualizo con la función oficial `fit_preprocessing`; este Ridge limpia sensores, no predice RUL.» |
| c29 (`exec=12`) | Fig.6 T48 residualizado por fase → `eda_t48_resid_fase.png` | Usa `prep` de c27 | «Solo presentación, pero depende de la variable `prep` de la celda anterior.» |
| c31 (`exec=13`) | Ventanas en vivo assert (50,19) `X_tab` 93, test 6196 | **Sí usa** `ventanas_adaptadas` | «Verifico el contrato de ventanas con la función oficial `ventanas_adaptadas` (93 cols, 6196 test).» |

**Entreno oficial:** NB01 **no tiene** entrenador externo que invocar; es el
escritor de sus 6 PNG de EDA. La frase completa: «NB01 no invoca ningún
`train_*.py`; las funciones oficiales que usa son `elegibles_mar`,
`imputar_ffill`, `fit_preprocessing` y `ventanas_adaptadas`».

---

## NB02 · `02_modelos_clasicos_y_mlp.ipynb` — Clásicos + MLP (40 celdas, 14 code)

**En 20 s:** «NB02 no escribe CSV/joblib: repite en vivo los loops oficiales
para anclarlos contra el CSV archivado; el entreno oficial vive en el `.py`.»

| Celda (0idx) | Hace (1 línea) | `.py` / función real | Frase de 20 s |
|---|---|---|---|
| c3 (`exec=2`) | Lee `comparativa.csv`, elige menor `rmse_val` | Solo lectura (escritor: `train_clasicos.entrenar_todo`) | «Leo la comparativa archivada y elijo por `rmse_val`; el CSV lo escribió el `.py`.» |
| **c5 (`exec=None`)** | **ENTRENO VIVO clásicos:** GridSearch `GroupKFold(3)` sobre `ESPEC`, SVM submuestra 5k; assert `<0.01` vs CSV; **no escribe** | **DUPLICA, no invoca** `train_clasicos.entrenar_todo:108` (importa `ESPEC`/`CV`/`SCORING`/`_metricas_*` privadas + `make_pipeline` de `src.clase.pipeline_clase`) | «Entreno en vivo ancla: mismo loop que `train_clasicos.py:108`, sin escribir, y exige que coincida con el CSV.» + follow-up: «No llamo a `entrenar_todo()` porque reescribiría CSV/joblib y cambiaría `tiempo_s`; eso es Grupo ALTO, no demo de hoy.» |
| c7 (`exec=4`) | CV XGB `cross_val_score` | Duplica params XGB inline + `make_pipeline` | «Mido el CV del ya elegido XGB; los params inline copian `ESPEC`.» |
| c11 (`exec=5`) | Real vs predicho clásico test (2000 filas) → `clasicos_real_vs_pred.png` | Carga `models/mejor_modelo.joblib` (**copia manual**, sin escritor) | «Pinto el mejor clásico desde el joblib ya guardado; `mejor_modelo.joblib` es copia manual, no regenerable.» |
| c15 (`exec=6`) | Por motor `groupby unit` | Usa `pipeline_clase.FEATURE_COLS` vía `src.clase.*` | «Desgloso por motor con las `FEATURE_COLS` oficiales.» |
| c17 (`exec=7`) | Ancla `mlp_comparativa.csv` | Solo lectura (escritor: `train_mlp.entrenar_mlp`) | «Leo la comparativa MLP archivada; el ganador E2 salió de ahí.» |
| **c20 (`exec=8`)** | **ENTRENO VIVO MLP:** loop `EXPS` (base/E1/E2/E3) `fit` + `cross_val_predict`; assert ganador E2; **no escribe** | **DUPLICA, no invoca** `train_mlp.entrenar_mlp:107` (importa `EXPS`/`BASE_KW`/`_m_train`/`_m_oof` privados) | «MLP en vivo: mismo loop que `train_mlp.py:107`, sin escribir, y verifica que E2 gana contra el CSV.» + follow-up: «No llamo a `entrenar_mlp()` por la misma razón: reescribiría `mlp_comparativa.csv` y el joblib E2:142.» |
| c21 (`exec=9`) | Imprime `BASE_KW`/`EXPS` (hipótesis) | **Sí usa** `train_mlp.EXPS`/`BASE_KW` bien citados | «Muestro las hipótesis E1/E2/E3 desde la fuente oficial `train_mlp.EXPS`.» |
| c24 (`exec=None`) | CV de E1 (~4 min, justifica descarte) | Duplica `_base` inline vs `BASE_KW` | «CV de E1 en vivo con base inline; si se separa del test, confirma que el test fue de una sola lectura.» |
| c25 (`exec=11`) | Real vs predicho MLP: **re-fit E2 en vivo** desde params del CSV → `mlp_real_vs_pred.png` | **Re-fit en vivo, NO carga** `mejor_modelo_clase_E2.joblib` | «Repito el fit de E2 desde los params del CSV para pintar; no cargo el joblib E2 guardado.» |
| c29 (`exec=12`) | Lee `importancia_permutacion.csv` | Lectura (escritor: `train_mlp.importancia_mejor_clasico`) | «Leo la tabla de permutación ya guardada; el PNG no se re-escribe aquí.» |
| c32 (`exec=13`) | **ANCLA:** recomputa permutación (200 val, exige top-3) | Usa `grupos_validacion` de `train_clasicos` + joblib XGB | «Anclo la permutación: recomputo 200 filas de validación y exijo el mismo top-3.» |
| c35 (`exec=14`) | **SHAP VIVO XGB:** TreeExplainer top_shap + assert orden → `shap_importancia.png` | Usa `shap_clase.top_shap` pero **re-fit XGB, NO llama** `ejecutar_shap` | «SHAP solo de XGB con la función `top_shap`; reentreno el XGB aquí, no cargo el joblib.» |

**Entreno oficial (frase de cierre):** «El entreno oficial de clásicos vive en
`train_clasicos.entrenar_todo:108` y el del MLP en `train_mlp.entrenar_mlp:107`;
NB02 c5/c20 **no los invoca**: copian el loop en vivo sin escribir y hacen
assert contra el CSV. La razón (reescribiría CSV/joblib, cambiaría `tiempo_s`,
invalidaría el manifiesto) es Grupo ALTO y no se demuestra en vivo.»

> `exec=None` en c5 y c24 = celdas **no ejecutadas en el estado guardado**;
> no lo confundas con «no deben ejecutarse».

---

## NB03 · `03_feature_engineering_secuencial.ipynb` — Ablación cyc_norm (15 celdas, 5 code)

**En 20 s:** «Pregunto si el reloj (`cyc_norm`) ayuda con una ablación en vivo;
el bundle C solo se lee, no se entrena aquí.» `c9 exec=None` (no ejecutada).

| Celda (0idx) | Hace (1 línea) | `.py` / función real | Frase de 20 s |
|---|---|---|---|
| c4 (`exec=1`) | Print alias «listos» sin importar | Menciona `viz.evaluar_clase` sin uso | «La celda 4 solo menciona los alias en un print; no los importa ni los usa.» |
| c6 (`exec=3`) | Puente C `raw/dev/test/prep` + bundle preentrenado | **Sí usa** `puente_c` (`src/ds02_rul/puente_c.py`; `dev/test` se construyen dentro, no aquí) | «Cargo base adaptada y bundle con `puente_c`; `dev/test` vienen de dentro del puente, no los construyo yo.» |
| c9 (`exec=None`) | Ablación en vivo `ablation_table` 4 variantes × 3 modelos, semilla 42 | **Sí usa** `ds02_rul/pipeline.py` `ablation_table` (bien delegado) | «Mido la ablación en vivo con la función oficial `ablation_table`; `abl` queda en memoria, no en CSV.» |
| **c14 (`exec=4`)** | **Figura barras RMSE; si `abl` no está en memoria, dibuja con 12 literales copiados** | **Literales duplicados (12 filas)** | «Si `abl` está en memoria, pinto la tabla calculada; si no —p. ej. kernel limpio— pinto 12 literales copiados a mano de la salida impresa: 6.563, 6.499, 6.297, 6.394, 6.324, 8.765, 5.796, 5.771, 7.067, 5.512, 5.490, 8.547 (BiLSTM/BiLSTM+EMA/LGBM × OFF/Baseline/ON/ON+delta). Es la única figura indefendible sin `abl`.» |

**Entreno oficial:** «El bundle C vive en
`bundle_c.entrenar`; NB03 **no lo invoca**: la ablación
c9 se mide en vivo y la figura c14 reutiliza `abl` (o literales si falta). La
corrección (leer `resultados/ablacion_cycnorm.csv` + assert) es Grupo MEDIO,
no tocada aquí.»

---

## NB04 · `04_arquitectura_bilstm_oof.ipynb` — BiLSTM OOF + ensamble (33 celdas, 15 code)

**En 20 s:** «Mido OOF, beta y meta en vivo para auditar, pero no re-escribo el
bundle desplegado; mi único `joblib.dump` es el estado para NB05.»

| Celda (0idx) | Hace (1 línea) | `.py` / función real | Frase de 20 s |
|---|---|---|---|
| c4 (`exec=2`) | Imports protocolo `SEEDS`/`WINDOW`/`STEP` | `ds02_rul` `metrics`/`conformal`/`smoothing`/`stacking` | «Declaro el protocolo 50/3/2; las constantes están en tres sitios, aquí las junto.» |
| c6 (`exec=3`) | Puente C | `puente_c` | «Cargo el bundle con `puente_c` en lectura.» |
| c7 (`exec=4`) | Alias `evaluar_clase` | `viz.evaluar_clase` (alias de `evaluate_predictions`) | «`evaluar_clase` es alias de solo lectura, no entrena.» |
| c8 (`exec=5`) | OOF en vivo `oof_base_predictions` step1, epochs15 | `ds02_rul/pipeline.oof_base_predictions` | «Genero OOF en vivo con la función oficial; ojo, hoy uso step1 y la celda 4 dice step3.» |
| c12 (`exec=6`) | Beta `select_beta_grouped` | `stacking.select_beta_grouped` | «Eligo beta fuera de fold con la función oficial.» |
| c15 (`exec=7`) | Meta `fit_meta_learners` sobre Z (2 cols), holdout-16 | `stacking.fit_meta_learners` (Ridge **meta**) | «Ajusto el meta solo en holdout-16 con la función oficial; este Ridge mezcla 2 predicciones, no mira sensores.» |
| c17 (`exec=8`) | Fig. pesos `ridge_meta` → `ridge_meta_pesos_04.png` | Display (vivo, no instalado 28/72) | «Solo presentación: pesos del meta vivo.» |
| c19 (`exec=9`) | `HybridStackingEnsemble.predict` tabla 4 filas | `ensemble.HybridStackingEnsemble` + `evaluate_predictions` + `causal_ema` | «Ensamblo en vivo y evalúo con las funciones oficiales; no es el bundle desplegado.» |
| c20 (`exec=10`) | Baseline media train 20.022 | Alias `evaluar_clase` | «La media train 20.022 es el listón, no un modelo.» |
| c23 (`exec=11`) | Sensibilidad EMA 3/5/10 + cascada | `causal_ema_by_unit` | «EMA10 gana en esta lectura pero no se reelige aquí.» |
| c25 (`exec=12`) | Macro RMSE por motor | `metrics.macro_rmse` | «El macro 5.0153 no es el global 4.338: es otra agregación.» |
| c28 (`exec=13`) | Banda `fit_conformal` (3 variantes) | `conformal.fit_conformal` | «Calibro la banda solo con residuales fuera de fold.» |
| c29 (`exec=14`) | Evalúa banda `predict_interval`/`coverage` | `ensemble.conformal` / `predict_interval` | «La cobertura es 100 % con ancho 27: cota conservadora, no probabilidad.» |
| c31 (`exec=15`) | **Guarda `artifacts_c/nb2_*`** (3 joblib + 3 npy) | Escritor propio NB04 | «Mi único `dump` es `notebooks/artifacts_c/` para NB05; el bundle de `models/` no lo toco.» |

**Entreno oficial:** «El bundle C vive en
`bundle_c.entrenar` vía `save_ensemble`
`persistence.py:202`; **NB04 no lo invoca**: mide OOF/meta en vivo y solo
escribe `notebooks/artifacts_c/` (ignorado por git, cadena NB04→NB05).»

---

## NB05 · `05_meta_ensemble_y_conformal.ipynb` — Multisemilla + conformal + LGBM adaptada (40 celdas, 14 code)

**En 20 s:** «Dejo `artifacts_c/` en disco y multiseed con `run_seed`; la LGBM
adaptada de la celda 30 es entreno en vivo sin escribir, el joblib oficial lo
escribe el `.py`.»

| Celda (0idx) | Hace (1 línea) | `.py` / función real | Frase de 20 s |
|---|---|---|---|
| c4 (`exec=2`) | Imports `run_seed`/`seed_summary` | `ds02_rul.pipeline` | «Declaro imports y `SEEDS`; las constantes duplican al puente.» |
| c6 (`exec=3`) | Puente + recarga `artifacts_c/` NB04, reconstruye ensemble `BETA` | `puente_c` + `nb2_*` | «Recargo lo que dejó NB04; sin NB04 no arranca el assert.» |
| c7 (`exec=4`) | Print alias sin importar | Mención | «Como NB03: menciono alias, no los importo.» |
| c8 (`exec=5`) | Multisemilla loop `SEEDS` `run_seed` + `fit_meta` + `Ensemble.predict` | `run_seed` / `fit_meta_learners` / `HybridStackingEnsemble` | «Corro 3 semillas con las funciones oficiales; la beta compartida cuesta el doble y es silenciosa.» |
| c9 (`exec=6`) | `seed_summary` media ± std | `seed_summary` | «La media ± std sale de `seed_summary`, no a mano.» |
| c10 (`exec=7`) | Trayectoria banda `plt.show` | Display | «Solo presentación: trayectoria con banda, sin `savefig`.» |
| c11 (`exec=8`) | Cobertura por motor `empirical_coverage` | `conformal` | «Repito la cobertura de NB04 por motor; duplica, no contradice.» |
| c16 (`exec=15`) | Figura dispersión por semilla | `viz.dispersion_por_semilla` | «Pinto media ± std con la función oficial de viz.» |
| c28 (`exec=10`) | Ancla `comparativa_ventanas.csv` filtrada | Lectura (escritor: `train_lgbm_adaptada.entrenar`) | «Leo el CSV oficial de LGBM adaptada; el filtro histórico es inline.» |
| **c30 (`exec=11`, 1idx 31)** | **ENTRENO VIVO LGBM adaptada:** `make_lgbm(42).fit` sobre ventanas fit-units, assert `RMSE<0.01` vs CSV; **no escribe** | **DUPLICA, no invoca** `train_lgbm_adaptada.entrenar:34` (mismo código, sin `to_csv`/`joblib.dump`) | «LGBM adaptada en vivo: mismo código que `train_lgbm_adaptada.py:34-61` pero sin escribir; el modelo vive solo en esta celda y se ancla contra el CSV.» + follow-up: «Si te piden el joblib oficial, vive en `src/clase/models/lgbm_adaptada.joblib` y lo escribió el `.py` en `src/clase/models:61`; aquí no se escribe.» |
| c32 (`exec=12`) | Mecanismo `ventanas_adaptadas` shapes 93 | `src/clase/ventanas_adaptadas` | «Verifico las 93 columnas con la función oficial de ventanas.» |
| c33 (`exec=13`) | CV `GroupKFold` fit-units `make_lgbm` | Duplica parcial `make_lgbm` | «CV diagnóstica en vivo; la media esconde la heterogeneidad entre motores.» |
| c38 (`exec=14`) | Real vs predicho LGBM **joblib oficial** → PNG | Carga `src/clase/models/lgbm_adaptada.joblib` | «Pinto con el joblib oficial escrito por el `.py`; nótese que el vivo de c30 y el oficial de c38 se llaman igual pero son dos objetos.» |

**Entreno oficial (frase de cierre):** «La LGBM adaptada oficial vive en
`train_lgbm_adaptada.entrenar:34` (escribe CSV:60 + joblib:61); **NB05 c30 no
lo invoca**: duplica el `fit` de 0,3 s sin escribir y hace assert contra el
CSV. Ojo con la numeración: tras Grupo SEGURO, c29 es markdown de procedencia
y c30 (0idx) / c31 (1idx) es el código.»

---

## NB06 · `06_evaluacion_produccion_comparativa.ipynb` — Bundle C en producción (62 celdas, 20 code)

**En 20 s:** «Reconstruyo test y tabla desde disco sin reentrenar; el bundle
desplegado solo se lee y la tabla solo se verifica.»

| Celda (0idx) | Hace (1 línea) | `.py` / función real | Frase de 20 s |
|---|---|---|---|
| c10 (`exec=2`) | Curva loss `run_seed` seed42 → `loss_curve_c.png` | `construir_raw_adaptado` + `run_seed` | «Curva de pérdida en vivo con `run_seed`; su `history` no es la del puente.» |
| c12 (`exec=3`) | OOF + beta en vivo step3 EPOCHS_OOF15 | `oof_base_predictions` + `select_beta_grouped` | «Segundo OOF en vivo (step3), distinto del step1 de NB04.» |
| c15 (`exec=4`) | Ensamble vivo `fit_meta` + `HybridStacking` scatter → `real_vs_predicho_bundle_c.png` | `fit_meta_learners` / `HybridStacking` / `evaluate` / `macro` | «Ensamble vivo en memoria; no es el desplegado de 4,338.» |
| c19 (`exec=5`) | Meta instalado `load_ensemble` pesos 28/72 alpha88 | `load_ensemble` + SHA | «Cargo el bundle instalado por el camino oficial `load_ensemble` con SHA.» |
| c21 (`exec=6`) | Fig. pesos instalado → `ridge_meta_pesos_06.png` | Display | «Solo presentación: pesos del artefacto, no del vivo.» |
| c24 (`exec=7`) | Banda `fit_conformal` `oof_calib` | `fit_conformal` | «Re-calibro la banda en vivo; no coincide con la del manifiesto.» |
| c26 (`exec=8`) | Residuos numpy | Ninguna (no usa `viz.residuos`) | «Residuos con numpy a mano.» |
| c30 (`exec=9`) | Lee `comparativa_bundle_c.csv` | Lectura (escritor: `bundle_c.entrenar`) | «Leo la cascada 7.067→4.338 del CSV archivado.» |
| c32 (`exec=19`) | Fig. cascada desde CSV → `bundle_c_cascada_rmse.png` | Display CSV | «Solo presentación: la cascada sale del CSV, no del vivo.» |
| c34 (`exec=10`) | **ANCLA** manifiesto vs CSV assert | `json.load` manifiesto | «Anclo: el manifiesto coincide con la fila Híbrido-C del CSV.» |
| c37 (`exec=11`) | Lee `bundle_c_por_motor.csv` + PNG | Lectura | «Leo la tabla por motor ya guardada.» |
| c39 (`exec=20`) | Fig. RMSE por motor CSV → PNG | Display CSV | «Solo presentación: U14 8.576 n760 se lee del CSV.» |
| c43 (`exec=12`) | Multiseed 7/123 `run_seed`+meta+`Ensemble` → `bundle_c_multiseed.csv` | **Escribe CSV desde el notebook**, NO llama `scripts/evaluate_bundle_stability` | «Multiseed en vivo que sí escribe su CSV; es doble escritor con `scripts/evaluate_bundle_stability.py` (beta 1.00 a mano).» |
| c45 (`exec=13`) | Media multiseed lee base+ms | Agregación | «Mi media 4.322 es agregación manual, distinta de la de NB05.» |
| c49 (`exec=22`) | Lee `tabla_final_clase.csv`, elige campeón por grano | Lectura `tabla_final.py` | «En fila manda MLP-E2 (7.72); en ventana, C (4.338). No los mezclo.» |
| c52 (`exec=16`, 1idx 53) | **TABLA VIVA** `construir_tabla` 4 CSV + `assert_frame_equal` | **Sí usa** `tabla_final.construir_tabla` (bien) | «Reconstruyo la tabla con la función oficial `construir_tabla` y exijo igualdad con el CSV; no escribo.» |
| c53 (`exec=16`) | Autónoma: construye test + `load_ensemble` + viz → `real_vs_predicho_viz_c.png` | `construir_raw` / `load_ensemble` / `build_windows` / `real_vs_predicho` | «Celda autónoma: reconstruye todo desde disco sin reentrenar.» |
| c56 (`exec=17`) | RECARGA ×2 `load_ensemble` + `puente_c` diff bit a bit | `load_ensemble` + `puente_c` | «Dos cargas idénticas coinciden; TF no determinista explica 4.338 vs 4.229 en otra corrida.» |
| c59 (`exec=18`) | Lee manifiesto, imprime versión/seed/dataset | `json.load` | «Leo versión/seed del manifiesto; no verifica SHA de artefactos.» |

**Entreno oficial:** «El bundle C vive en
`bundle_c.entrenar` y la tabla final en
`tabla_final.py:76`; **NB06 no los invoca**: lee en c19/c53/c56, verifica en
c34/c52 y solo escribe el multiseed c43, los PNG y nada de `models/`.»

---

## NB07 · `07_shap_c_bundle_c.ipynb` — SHAP bundle C (7 celdas, 4 code)

**En 20 s:** «No entrena nada: llama a `ejecutar_shap_c` sobre el bundle
congelado en solo lectura y vuelca la explicación.» 8/10, el más defendible.

| Celda (0idx) | Hace (1 línea) | `.py` / función real | Frase de 20 s |
|---|---|---|---|
| c0 (`exec=1`) | Bootstrap + TF 1 hilo antes de Keras | — (entorno; orden crítico) | «La celda 0 fija TF a 1 hilo antes de importar Keras; sin ese orden cambia el paralelismo.» |
| c3 (`exec=2`) | `ejecutar_shap_c(n=200, fondo=200, seed=42)` + tiempo | **Sí llama** `src/ds02_rul/shap_c.py:ejecutar_shap_c` (llamada única, bien delegada) | «Explico con la función oficial `ejecutar_shap_c`; todo el cómputo vive en `shap_c.py`.» |
| c4 (`exec=3`) | Lee 3 CSV + `metadata.json`, imprime top-5 | Lectura `shap_bundle_C/` | «Leo las 3 ramas ya explicadas.» |
| c5 (`exec=4`) | Display 3 barras `bar_*.png` | Display | «Solo presentación: las barras ya calculadas; BiLSTM agrega por canal y pierde los 50 pasos.» |

**Entreno oficial:** «El bundle C vive en
`bundle_c.entrenar` vía `save_ensemble`
`persistence.py:202`; el SHAP vive en `shap_c.ejecutar_shap_c`. **NB07 no
entrena ninguno de los dos**: carga `models/ensemble.joblib` en lectura y
escribe solo `resultados/shap_bundle_C/` (explicación, no modelo).»

---

## Doble import — defiéndelo sin dudar

**Frase de 20 s:** «`ds02_rul.*` es la ruta corta de `src/ds02_rul/`;
`src.*` es la misma carpeta con prefijo `src`, y la celda 0 fija la raíz.»

| Grafía | Ejemplo en notebooks | Cuándo se elige |
|---|---|---|
| Ruta corta `from ds02_rul.*` (resuelve vía `_ROOT/src`) | NB01 c27, NB03 c9, NB04 c4/c8/c15/c19, NB05 c4/c6, NB06 c19/c43 | Celdas de `ds02_rul` paquete |
| Con prefijo `from src.*` (resuelve vía `_ROOT`) | NB02 todo (`src.clase.*`), NB05 c30/c32/c33/c38, NB06 c10/c43/c52/c53, NB07 c3 (`src.ds02_rul.shap_c`) | Celdas de `src/clase` y track de clase |

Si preguntan «¿por qué dos grafías y cuál uso?»: la dualidad viene de
`pyproject.toml` `packages.find where=src` + pickle calificado de
`HybridStackingEnsemble` + `test_artifact_contract` en proceso limpio;
unificar a `src.*` rompe artefactos (Grupo ALTO). No propongas unificar en vivo.

## Tres Ridges — dime qué entrada recibe

**Frase de 20 s:** «Ridge físico limpia sensores, Ridge fila predice RUL de 1
fila, y `ridge_meta` mezcla 2 predicciones ya hechas.»

| Ridge | Dónde vive | Entrada | No es |
|---|---|---|---|
| **Físico** (14 Ridge por sensor, NB01 c27) | `SensorResidualizer` `src/ds02_rul/residualizer.py`, vía `fit_preprocessing` | Telemetría `alt/Mach/TRA/T2` (grado 2) → residuo = degradación | No predice RUL |
| **Fila** (baseline, NB02 c5) | Pipeline fila `src/clase/pipeline_clase.py:38` `make_pipeline`, fila `regresion` de `comparativa.csv` | 1 fila imputada → RUL (val 8.28, compite XGB 8.22) | No limpia sensores ni mezcla predicciones |
| **Meta** (`ridge_meta`/`RidgeCV`, NB04 c15 / NB05 / NB06 c19) | `fit_meta_learners` `src/ds02_rul/stacking.py` | `[p_lstm, p_lgb]` en holdout-16 → 28 % red / 72 % árbol, `alpha=88.6` | No mira sensores ni predice RUL de 1 fila |

## exec=None — dilo sin temblar

`exec=None` significa que la celda **no se ejecutó en el estado guardado**
(NB02 c5/c24, NB03 c9). No significa «prohibida». En vivo, si le das a Run,
c5/c20/c30 hacen assert contra el CSV archivado y **no reescriben** nada;
c9 (NB03) calcula `abl` en memoria (tarda) y c14 dejaría de usar literales.

---

*Verificación de este mapa (sin re-ejecutar entrenos): `nbformat.validate`
en verde en NB01–07, hashes `sha256` de cada celda `code` idénticos antes y
después de añadir las footers Markdown, `git diff` limitado a `docs/defensa/`
y a celdas Markdown de `notebooks/*.ipynb`.*
