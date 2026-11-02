# Tasks: Track de clase DS02

**Change:** `2026-11-02-clase-track`
**Status:** Proposed

Cada tarea cierra con su acceptance check. `tdd: true` donde haya lógica. Comandos desde la raíz del repo. Nada escribe en `models/`, `src/ds02_rul/`, `mia/`, `app/cache/`, `archive/`.

## Review workload guard

```
Decision needed before apply: No (ya autorizado: 4 fases sin MLflow/n8n, en clase-experimental)
Chained PRs recommended: No (1 commit por fase, <400 líneas cada uno)
400-line budget risk: Low (Fase 2 es la mayor, se parte en 2.1/2.2/2.3)
```

---

## Fase 0 — Esqueleto (1 commit)

### [x] 0.1 Verificar rama y crear esqueleto
**Crea** `clase/`, `data/raw|processed/` (+ `data/raw/README.md` con fingerprint HDF5, sin commitear el .h5), `notebooks/`, `resultados/`, `n8n/flujo.json` (placeholder `{"pendiente":"MIA3"}`), `src/reglas.py` (re-export de `mia/reglas.py`), `src/n8n.py` (stub documentado, sin llamada).
Acceptance: `git status --porcelain models/ src/ds02_rul/ mia/ app/cache/` vacío; `python -c "import src.reglas"` ok.

## Fase 1 — Dataset + EDA

### [x] 1.1 `clase/dataset_clase.py` (inyección + imputación + fase_vuelo + split)
**Crea** funciones puras: `inyectar_nulos_mar(df, sensor=T30, alt>27k, Mach>0.68, tasa_elegible=0.10, seed=7)`, `elegibles_mar`, `rachas_nulos`, `imputar_ffill(df, med_train)`, `fase_vuelo(alt, mach)`, `split_por_unidad(df)`. RED test primero en `tests/test_clase_dataset.py`: MAR solo T30+elegibles; ffill no mira futuro ni otras unidades; medianas solo de train; `fase_vuelo` solo usa alt/Mach.
Acceptance: `pytest tests/test_clase_dataset.py -q` verde + `data/processed/{train_con_nulos,train,test,X_train,X_test,y_train,y_test}.parquet` + `auditoria_nulos.json` (MAR, tasa global/en elegibles, rachas) generados.

### [x] 1.2 `notebooks/01_eda.ipynb` (tabla + calidad + 5 gráficos)
Tabla campos (nombre, qué significa, tipo, %nulos antes/después, descarte), duplicados/imposibles, patrón nulos (heatmap por sensor/fase), variable nueva justificada. 6 figuras: barras (fase_vuelo o unidades), hist + box (1 numérica, ej. T48 o RUL), scatter (2 vars, ej. alt vs Mach coloreado por fase), heatmap correlación. Cada figura con "qué veo / conclusión".
Acceptance: notebook ejecuta sin error; `resultados/eda_*.png` (≥5) existen; 1-2 figs citadas para README.

## Fase 2 — Pipeline + modelos

### [x] 2.1 `clase/pipeline_clase.py` (ColumnTransformer compartido)
`NUM_COLS` + `["fase_vuelo"]`, `ColumnTransformer([StandardScaler, OneHot(handle_unknown=ignore)])`, `make_pipeline(pre, reg)`, `predict_caso_nuevo(modelo, dict)` (1 fila → RUL). Test: el mismo `pre` en los 5+MLP; `predict_caso_nuevo` redondea a 2 decimales.
Acceptance: `pytest tests/test_clase_pipeline.py -q` verde.

### [x] 2.2 `clase/train_clasicos.py` + `notebooks/02_modelos_A.ipynb`
Ridge/KNN/RF/XGB/SVR + GridSearchCV(`GroupKFold(3, groups=unit)`), grids mínimos del design, tiempos por modelo, `resultados/comparativa.csv` (modelo, RMSE/MAE/R² train/val, tiempo_s), gráfico real-vs-predicho del mejor, frase negocio por métrica elegida.
Acceptance: 5 modelos entrenan; CSV con 5 filas + tiempos; `models/mejor_modelo_clase.joblib` guarda pipeline completo.

### [x] 2.3 `clase/train_mlp.py` + `notebooks/03_modelos_B.ipynb` + SHAP
MLP base + E1/E2/E3 con hipótesis escrita antes del resultado. SHAP (200 filas) o permutación + `resultados/shap_*.png` + top-10 variables en README.
Acceptance: base + 3 exps con métricas; figura SHAP/permutación existe.

## Fase 3 — README + app

### [x] 3.1 README 6 apartados
Título+frase+resultado, captura app arriba, necesidad negocio (dato+objetivo+quién+€), esquema Mermaid (modelo→reglas→(n8n pendiente)→acción) + párrafo IA débil/supervisado/herramientas, datos (tabla+hallazgo+1-2 figs), resultados (tabla pandas+tiempos, elección por negocio, test 1 vez, real-vs-predicho, captura app; declarar "MLflow pendiente" explícitamente), estructura `clase/`, cómo ejecutar clase, autoría.
Acceptance: checklist 6 apartados ok; sin afirmar MLflow/n8n hechos.

### [x] 3.2 `clase/app_clase.py` (fina, reutiliza)
Métricas test del mejor clásico + predecir caso nuevo (formulario 1 fila) + decisión `mia/motor` + controles vacíos/erróneos (reusar `validate_table`). Sin POST n8n.
Acceptance: `streamlit run clase/app_clase.py` predice 1 caso y muestra decisión; tabla vacía/inf rechazada con mensaje.

## Fase 4 — Verificación (sin MLflow/n8n)

### [x] 4.1 Gate clase
`pytest tests/ -q` verde, `freeze_rules_evidence.py` exit 0, `git status models/ src/ds02_rul/ mia/ app/cache/` vacío, conteo tests registrado.
Acceptance: todo verde + informe de qué techos quedan (SAA9→7 formal, PIA4→0, PIA5→7, MIA3→0) para el change siguiente.

## Fase 5 — NB04 LGBM adaptada (AUTORIZADA)

### [ ] 5.1 `clase/ventanas_adaptadas.py` (ventaneo honesto de la adaptada)
Mapea parquet MAR-imputado → W/Xs/y/units/cycles; re-imputa con medianas SOLO fit-units `[2,5,10,18,20]`; `fit_preprocessing` + `build_windows` sin cambios (93, sin `fase_vuelo`). RED test: preprocesado fit solo en fit-units; split fit/holdout16/test11-14-15 sin solape.
Acceptance: `pytest tests/test_clase_ventanas.py -q` verde.

### [ ] 5.2 `notebooks/04_lightgbm_adaptada.ipynb` (LGBM cuantil 0.35 + GridSearch)
GroupKFold por motor, métricas RMSE/MAE/R²/NASA + por motor + real-vs-predicho + tabla con columna `grano=ventana` (prohibido ranking mixto con E1-7.70). Guarda `clase/models/lgbm_adaptada.joblib` + `resultados/comparativa_ventanas.csv`.
Acceptance: notebook ejecuta; comparativa honesta B-histórico vs LGBM-adaptada en mismas ventanas.

## Fase 6 — NB05 bundle C (PENDIENTE, solo si B-plumbing ok)

### [x] 6.1 `clase/train_ensemble_adaptado.py` + `notebooks/05_ensemble_adaptado.ipynb` (seed 42)
Mismo protocolo que B sobre ventanas adaptadas (adaptador `construir_raw_adaptado` + `run_seed`/`oof`/`select_beta`/meta/holdout-16 sin cambios); manifest + banda propios en `clase/models/`.
Evidencia 2026-11-02: Híbrido-C RMSE 4.338 / NASA 2336.2 vs B 4.251/2305.1 (6.196 ventanas); beta_hat=1.00; puerta D11 NO superada → C experimento, B sigue. Multiseed en NB05 (7: 4.338/2350.9, 123: 4.266/2330.3): C 4.314±0.042 / 2339.1±10.6 vs B 4.251/2305.1 — hueco real, fuera de ruido. Test `tests/test_clase_bundle_c.py` verde. B-bajo-dropout 2026-11-02 (solo inferencia del bundle congelado, mismo grid 6.196, `tests/test_clase_b_robusto.py` verde): RMSE 4.247 / NASA 2290.0, indistinguible de B-limpio → B insensible al régimen; B sigue con evidencia.
Acceptance: bundle C versionado + tabla B vs C (RMSE y NASA, 6.196 ventanas); decisión contra la puerta D11; SIN re-freeze (requiere otra autorización).

## Fase 7 — Consolidación entrega (AUTORIZADA 2026-11-02)

### [x] 7.1 Renombrar `clase/` → `track_clase/` (+ re-ejecutar 02/03/04)
`clase/` era andamio de aislamiento; el aislamiento sigue siendo necesario (protege `src/ds02_rul/` congelado), pero el nombre no era profesional. `mv` + sed (`from clase.` → `from track_clase.`, paths `../clase/` → `../track_clase/`, `scripts/build_05_notebook.py` incluido); `clase/models/` NO se mueve a `models/` (colisión `ensemble.joblib` B vs C: la separación campeón/challenger es intencionada). 22 tests track verdes + 02/03/04 re-ejecutados con kernel `ds02-venv` (0 errores) + smoke de imports del 05 (sin reentrenar).
Acceptance: `grep from clase.` vacío en py/ipynb (solo prosa histórica en docs); tests verdes; notebooks sin `error` ni `InconsistentVersionWarning`.

### [x] 7.2 SHAP real + tabla de grano único + puente README (SAA-9 → 10)
`track_clase/shap_clase.py` (TreeExplainer XGB, fondo 200 train, `resultados/shap_importancia.*`, `shap==0.54.1` + `xgboost==3.4.1` pinneados en requirements) + `track_clase/tabla_final.py` (`resultados/tabla_final_clase.csv`, columna `grano`, campeones fila=MLP-E1 7.70 / ventana=B 4.251, sin ranking mixto) + bloque de entrada en `README.md` raíz → `track_clase/README.md`. Supera el techo SAA9→7 de la Fase 4.1: SAA-9 queda en 10.
Acceptance: `resultados/shap_importancia.png` + `tabla_final_clase.csv` existen; celda SHAP del 03 con output; tests `test_clase_shap`/`test_clase_tabla` verdes.
