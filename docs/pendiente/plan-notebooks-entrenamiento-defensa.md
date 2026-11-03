# Plan de reestructuración de notebooks 01–05: entrenamiento + explicaciones para la defensa

> **Para el agente ejecutor:** este plan se implementa tarea por tarea, en orden. Cada tarea termina con una verificación ejecutable y un commit. No avances a la tarea siguiente con la verificación en rojo.

**Objetivo:** que la secuencia `notebooks/01_eda.ipynb` → `05_ensemble_adaptado.ipynb` sea autosuficiente para montar la defensa completa: datos, entrenamiento real, decisiones y explicaciones, sin abrir `notebooks/ds02_ensemble/` ni depender de CSVs o bundles pre-generados.

**Arquitectura:** los notebooks orquestan y explican; la lógica de dominio permanece en `src/ds02_rul/` y `track_clase/` (fuente única). Cada notebook entrena en vivo lo que su capítulo necesita, muestra las ecuaciones de cada pieza y enlaza narrativamente con el anterior y el siguiente. `notebooks/ds02_ensemble/` queda intacto como referencia de storytelling.

**Stack:** Python 3.12 (`.venv`), kernel Jupyter `ds02-venv`, pandas 3.0.6, scikit-learn 1.9.1, LightGBM 4.7.0, XGBoost 3.4.1, TensorFlow 2.21.0 / Keras 3.15.1, SHAP 0.54.1, nbconvert 7.17.2.

**Specs de referencia (leer antes de empezar):**
- `docs/pendiente/planificacion-clase-5notebooks.md` — intención original del track de clase.
- `docs/pendiente/plan-reestructuracion-notebooks.md` — plan previo; su mapeo contiene errores estructurales que este plan corrige (ver §1.3).
- `notebooks/ds02_ensemble/01-03` — referencia de storytelling y de ecuaciones; **no se copia código, se copia el ritmo**.
- `notebooks/ds02_ensemble/EVALUACION_EJECUCION.md` — no-determinismo de TensorFlow y cifras publicadas vs rerun.
- `docs/decisions/ADR-001..ADR-008` — decisión de diseño detrás de cada ecuación.

---

## 0. Restricciones globales (no negociables)

| # | Regla |
|---|---|
| R1 | Solo se editan estos cinco archivos: `notebooks/01_eda.ipynb`, `02_modelos_A.ipynb`, `03_modelos_B.ipynb`, `04_lgbm_adaptada.ipynb`, `05_ensemble_adaptado.ipynb`. |
| R2 | Prohibido modificar `src/`, `app/`, `mia/`, `models/`, `requirements.txt`, `tests/`, `track_clase/`. Si algo falta en esos módulos, se resuelve dentro del notebook con las piezas que ya existen. |
| R3 | Prohibido escribir en disco durante la ejecución: ni `models/`, ni `resultados/`, ni `track_clase/models/`. Las figuras se muestran con `IPython.display.Image` desde un buffer en memoria. |
| R4 | Prohibido llamar funciones que persisten: `entrenar_todo`, `entrenar_mlp`, `importancia_mejor_clasico`, `ejecutar_shap`, `entrenar` (de `train_lgbm_adaptada` y de `train_ensemble_adaptado`), `save_ensemble`, `write_manifest`, `tabla_final.main`, `build_ui_cache`. Se usan sus constantes y funciones puras, y se re-orquesta el bucle en el notebook. |
| R5 | Prohibido marcar, mover o modificar `notebooks/ds02_ensemble/` (incluidos sus artefactos). |
| R6 | Los cinco notebooks deben declarar `metadata.kernelspec.name = "ds02-venv"` y `display_name = "Python (ds02-venv)"`. Hoy los cinco declaran `python3` (Python 3.10 del sistema, sin las dependencias). |
| R7 | Prohibido hardcodear métricas publicadas como ancla. Las celdas `assert` solo verifican **invariantes estructurales** (formas, particiones, ausencia de fuga, rangos), nunca valores de RMSE/NASA. |
| R8 | Los artefactos técnicos (código, comentarios, títulos de tablas) van en español neutro, igual que el resto del repositorio. Sin voseo ni slang. |
| R9 | Cada notebook se re-ejecuta completo con `nbconvert --execute` antes de darlo por terminado. No se entrega un notebook con celdas sin ejecutar. |
| R10 | Después de cada tarea: `pytest tests -q` y comparación contra la línea base documentada en §5.2. |

---

## 1. Diagnóstico: qué está mal hoy

### 1.1 Estado actual por notebook

| NB | Celdas | Qué hace hoy | Tiempo | Problema |
|---|---|---|---|---|
| 01 | 14 | EDA + nulos + `fase_vuelo` | 7 s | No presenta el pipeline honesto (residualización, ventanas) que usan 04 y 05. No hay puente al modelado. |
| 02 | 11 | Lee `resultados/comparativa.csv` y `models/mejor_modelo_clase.joblib` | 33 s | No entrena. Una demo de 2.000 filas y 2 folds no es entrenamiento. Ancla contra CSV. |
| 03 | 17 | Lee `resultados/mlp_comparativa.csv` y `resultados/shap_importancia.csv` | 423 s | No entrena el modelo que presenta; re-entrena solo para "anclar". Depende de `models/` y de un CSV de SHAP. |
| 04 | 12 | Lee `resultados/comparativa_ventanas.csv` y `track_clase/models/lgbm_adaptada.joblib` | 18 s | No entrena. Ancla contra joblib versionado. |
| 05 | 26 | Lee 4 CSVs + bundle de `track_clase/models/` | 216 s | Solo el multiseed entrena. Todo el resto es lectura de artefactos. 17 celdas sin `id`. |

### 1.2 Defectos transversales

1. **Kernel incorrecto en los cinco.** `python3` apunta a `C:\Users\mikel\AppData\Local\Programs\Python\Python310`. Sin `pyarrow`, `tensorflow`, `lightgbm` ni `shap`.
2. **Los notebooks no son la fuente de verdad.** La defensa tendría que abrir `resultados/` y `track_clase/models/` para justificar cifras. El tribunal no debe ver dos carpetas.
3. **Celdas `ANCLA`.** Verifican que un CSV coincide con un artefacto persistido. Eso demuestra que el CSV es fresco, no que el modelo se entrenó en el notebook.
4. **Escritura de PNG en `resultados/`.** 01, 03 y 05 guardan figuras con `fig.savefig('../resultados/...')` y luego las muestran con `Image(filename=...)`.
5. **Sin ecuaciones.** No hay residualización, meta-learner, beta, EMA, conformal, `cyc_norm`, BiLSTM ni LightGBM cuantílico explicados formalmente.
6. **Sin hilo narrativo.** Cada notebook es una isla: no dice de dónde viene ni qué deja al siguiente.

### 1.3 Correcciones al plan previo

El plan anterior (`plan-reestructuracion-notebooks.md`) asignaba mal cuatro temas. Este plan fija el contrato correcto:

| Tema | Plan previo | Correcto | Por qué |
|---|---|---|---|
| Conformal | NB04 | **NB05** | Es propiedad de `HybridStackingEnsemble.predict_interval`, no del LGBM. |
| Beta / meta / EMA | NB03 | **NB05** | Mezclan `p_lstm` y `p_meta`; sin BiLSTM no existen. |
| Multisemilla / diagnósticos | NB04 y NB05 (duplicado) | **NB05** | Una sola vez, donde vive el híbrido. |
| `cyc_norm` | NB03 | **NB01 (contrato) + NB04/NB05 (uso)** | Es una feature de `build_windows` (canal 19), no un tema de MLP. |

### 1.4 Decisión de reparto: T2 (adoptada)

- **NB04** entrena **solo** el especialista tabular (LightGBM cuantílico) sobre ventanas.
- **NB05** entrena **BiLSTM + meta + beta + EMA + conformal + multiseed**, reutilizando el LGBM que ya entrenó NB04 mediante el mismo `run_seed` (mismo seed, mismas ventanas, mismas predicciones).

**Por qué T2 y no T1** (T1 = NB04 entrena ambos especialistas): T1 obliga a un puente de artefactos entre notebooks (zona gris respecto a R3) o a reentrenar la semilla 42 en NB05 (duplica el coste más caro del proyecto). T2 no necesita puente y no duplica: NB05 obtiene su LGBM llamando a `run_seed`, que es la función que ya usa NB04 conceptualmente. La igualdad de predicciones se verifica con un `assert` de consistencia (§3.5), lo que convierte el solapamiento en una prueba de que no hay fuga ni desalineación.

---

## 2. Arquitectura objetivo

### 2.1 Arco narrativo 01 → 05

| NB | Pregunta que responde | Entrena | Deja al siguiente | Tiempo objetivo |
|---|---|---|---|---|
| 01 | ¿Qué datos hay, cómo se parten y qué contrato los hace honestos? | Nada | Partición, imputación, residualización, ventanas, las dos ligas | ~15 s |
| 02 | ¿Qué logra un modelo tabular barato sobre una fila? | 5 clásicos + GridSearch | "El techo de la liga de fila y su mejor modelo" | ~2 min |
| 03 | ¿Aporta no-linealidad? ¿Qué mira el modelo? | 4 MLP + XGB para SHAP | "La no-linealidad ayuda; la importancia coincide; falta el tiempo" | ~6–8 min |
| 04 | ¿Qué logra el especialista tabular sobre una ventana honesta? | LightGBM cuantílico | "7,07 RMSE en la liga de ventana; falta medir cuánto aporta la secuencia sobre estas mismas ventanas" | ~1 min |
| 05 | ¿Cuánto aporta leer la película completa? | BiLSTM + meta + beta + EMA + conformal + 3 semillas | Veredicto D11 y tabla final | ~6 min |

**Total de la pasada completa: 15–18 min.** No se corre en vivo en la defensa; los notebooks se presentan pre-ejecutados y el entrenamiento se muestra en código + outputs.

### 2.2 Las dos ligas (declararlo explícitamente en NB01 y NB05)

| Liga | Grano | Train | Test | Predictores | Modelos |
|---|---|---|---|---|---|
| Fila | 1 ciclo de vuelo | 52.635 filas | 12.538 filas | 19 numéricas + `fase_vuelo` = 20 predictores (el frame trae 21 columnas porque incluye `unit`, que solo se usa como grupo) | 02, 03 |
| Ventana | 50 ciclos terminando en el ciclo objetivo | 17.450 ventanas (14.915 fit + 2.535 holdout-16) | 6.196 ventanas (11: 3.293 / 14: 760 / 15: 2.143) | secuencia `(50, 19)` y resumen tabular de 93 columnas | 04, 05 |

**Las dos ligas no son comparables entre sí** (distinto grano, distinta unidad de error). Por eso el cierre es "dos ligas, dos campeones", nunca un ranking mixto. Esta frase debe aparecer literalmente en NB01 y en el cierre de NB05.

### 2.3 Mapa DRY: un solo punto de verdad por tema

| Concepto | Fuente única (no se reimplementa) | Notebook que lo explica |
|---|---|---|
| Partición por motor | `track_clase.ventanas_adaptadas.FIT_UNITS / HOLDOUT_UNITS / TEST_UNITS`; `dataset_clase.TRAIN_UNITS / TEST_UNITS` | 01 |
| Inyección MAR | `dataset_clase.inyectar_nulos_mar`; auditoría en `data/processed/auditoria_nulos.json` | 01 |
| Imputación | `dataset_clase.imputar_ffill`, `medianas_train` | 01 |
| Residualización | `ds02_rul.features.fit_preprocessing` (`SensorResidualizer`) | 01 (contrato), 04 (uso) |
| Ventanas + resumen 93 | `ds02_rul.features.build_windows` | 01 (contrato), 04 (uso) |
| Pipeline tabular de fila | `track_clase.pipeline_clase.make_pipeline`, `FEATURE_COLS` | 02 |
| Grids de clásicos | `track_clase.train_clasicos.ESPEC` | 02 |
| MLP | `track_clase.train_mlp.EXPS`, `BASE_KW` | 03 |
| LGBM cuantílico | `ds02_rul.pipeline.make_lgbm`, `LGB_PARAMS` | 04 |
| BiLSTM | `ds02_rul.model.build_champion_bilstm` | 05 |
| Meta-learner | `ds02_rul.stacking.fit_meta_learners`, `meta_predict` | 05 |
| Beta | `ds02_rul.stacking.select_beta_grouped`, `BETA_GRID` | 05 |
| EMA | `ds02_rul.smoothing.causal_ema_by_unit` | 05 |
| Conformal | `ds02_rul.conformal.fit_conformal`, `apply_conformal`, `empirical_coverage` | 05 |
| Métricas | `ds02_rul.metrics.evaluate_predictions`, `macro_rmse`, `calculate_nasa_score` | 02 (definición), 04 y 05 (uso) |

**Duplicación permitida y acotada:** el bucle de orquestación (10–15 líneas) que recorre `ESPEC` o `EXPS` y llama a `make_pipeline`. Es inevitable porque las funciones de módulo que harían ese bucle (`entrenar_todo`, `entrenar_mlp`) persisten resultados y R2 prohíbe modificarlas. La **lógica** (grids, pipeline, preprocesado) no se duplica: se importa.

### 2.4 Convenciones de celda

Cada notebook sigue este esqueleto, en este orden:

1. **Título** (`# NN — ...`).
2. **Dónde estamos** (markdown): 1–2 líneas con el resultado del notebook anterior y qué añade este.
3. **Setup** (código): imports, `sys.path`, `TF_CPP_MIN_LOG_LEVEL`, `warnings`, helper `mostrar(fig)`.
4. **Cuerpo** por secciones `## N · ...`, cada una con markdown que dice qué se va a medir y por qué, seguida de la celda de código y de una celda de lectura ("**Qué vemos.** ...").
5. **Cierre → siguiente** (markdown): el resultado y la pregunta que abre el siguiente notebook.

**Helper de figura (una vez por notebook, en el setup):**

```python
import io
from IPython.display import Image, display

def mostrar(fig, dpi=120):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    display(Image(data=buf.getvalue()))
```

Esto cumple R3 (cero escrituras a disco) y reemplaza el patrón `savefig('../resultados/...') + Image(filename=...)`.

---

## 3. Especificación por notebook

### 3.1 NB01 — `01_eda.ipynb`: datos y contrato

**Objetivo:** que el tribunal entienda el dataset, la partición por motor, el mecanismo de nulos, la residualización y el contrato de ventanas **antes** de ver un solo modelo.

**Contrato de celdas:**

| # | Tipo | Contenido | Fuente |
|---|---|---|---|
| 1 | md | Título + "Dónde estamos" (es el primer capítulo) | — |
| 2 | md | Qué es DS02, qué se predice, por qué es IA débil y supervisada (conservar el texto actual) | — |
| 3 | co | Setup: imports, `matplotlib.use('Agg')`, `mostrar`, carga de `train.parquet`, `test.parquet`, `train_con_nulos.parquet`, `auditoria_nulos.json` | — |
| 4 | md | **Las dos ligas**: tabla de §2.2 con las cifras reales | §2.2 |
| 5 | co | Imprime formas, unidades, RUL media, fase; imprime la tabla de ligas calculada | — |
| 6 | md | Tabla de campos + calidad (conservar la actual, es buena) | — |
| 7 | co | Duplicados, RUL<0, cycle<=0, Mach fuera de rango, nulos por columna | — |
| 8 | md | **La partición es por motor, no por fila** + ecuación de GroupKFold | — |
| 9 | co | Tabla de unidades: fit `[2,5,10,18,20]`, holdout `[16]`, test `[11,14,15]`; cuenta de filas por unidad; `assert` de que fit ∩ test = ∅ | `ventanas_adaptadas` |
| 10 | md | **Nulos MAR**: definición y ecuación | — |
| 11 | co | Recalcula la tasa MAR sobre `train_con_nulos` (elegibles, nulos, tasa global) y compara con `auditoria_nulos.json`; `assert` de que `RUL` no tiene nulos | `dataset_clase.elegibles_mar` |
| 12 | md | **Imputación**: ffill causal + mediana de fit-units; ecuación | — |
| 13 | co | Aplica `imputar_ffill` a `train_con_nulos` con `medianas_train`; muestra antes/después; `assert` 0 nulos. **No** escribe parquet. | `dataset_clase` |
| 14 | md | Fig.1 reparto de `fase_vuelo`; Fig.2 histograma RUL; Fig.3 boxplot T48 por fase | — |
| 15 | co | Genera las tres figuras y las muestra con `mostrar` | — |
| 16 | md | Fig.4 dispersión alt-Mach por fase | — |
| 17 | co | Figura + lectura | — |
| 18 | md | Fig.5 heatmap de correlación | — |
| 19 | co | Figura + lectura (RUL no sale de una fila → hace falta historia) | — |
| 20 | md | **Residualización**: el problema (el régimen manda en el sensor crudo) y la ecuación | ADR-002 |
| 21 | co | `fit_preprocessing` sobre las filas de fit-units; muestra la caída de correlación sensor–régimen antes/después en 3 sensores; `assert` de formas | `ds02_rul.features` |
| 22 | md | **Contrato de ventanas**: W=50, stride 3/2, resumen de 93 columnas, `cyc_norm` | ADR-002, ADR-003 |
| 23 | co | `ventanas_adaptadas()`; imprime `dev X_seq`, `dev X_tab`, `test X_seq`, `test X_tab`; `assert` de `(·,50,19)` y `(·,93)`; `assert` de que test tiene 6.196 ventanas y 3 unidades | `track_clase.ventanas_adaptadas` |
| 24 | md | **Cierre → NB02**: "sabemos partir y transformar; la pregunta ahora es cuánto explica una sola fila" | — |

**Ecuaciones obligatorias (celdas markdown):**

- **RUL.** `$y_{u,c} = N_u - c$`: ciclos restantes del motor `u` en el ciclo `c`, tal como los provee DS02. No se recorta a 125 (eso es FD001).
- **Partición.** `$U_{fit} \cap U_{hold} = \emptyset$, $U_{fit} \cap U_{test} = \emptyset$`: ninguna ventana del mismo motor cae en dos lados.
- **MAR.** `$M_{u,c} \sim \mathrm{Bernoulli}(\pi)$` si `alt > 27.000` y `Mach > 0.68`, con `$\pi = 0.10$` sobre `T30` y semilla 7. Resultado auditado: 12.499 filas elegibles, 1.185 nulos inyectados sobre train+test, 9,48 % dentro de las elegibles y 1,82 % global. En `train_con_nulos` quedan 1.056 nulos.
- **Imputación.** `$\hat{x}_{u,c,j} = x_{u,c-1,j}$` si falta (ffill dentro del motor, ordenado por ciclo); si no hay valor previo, `$\hat{x}_{u,c,j} = m_j$` con `$m_j = \mathrm{median}\{x_{u,c,j} : u \in U_{fit}\}$`.
- **Residualización.** Para cada sensor `j`, `$f_j(w) = \beta_{j,0} + \sum_{k=1}^{14} \beta_{j,k}\,\phi_k(w)$`, donde `$\phi$` es la expansión polinómica de grado 2 de `(alt, Mach, TRA, T2)` estandarizados (4 lineales + 4 cuadrados + 6 interacciones) y `$\beta_j$` se ajusta con ridge `$\alpha=1$`. El residuo es `$r_{u,c,j} = x_{u,c,j} - f_j(w_{u,c})$`, luego estandarizado.
- **Ventana.** `$W_i = \{(u,c) : c_i \le c < c_i + 50\}$`, objetivo `$y_i = y_{u,\,c_i+49}$`; stride 3 en dev y 2 en test.
- **Resumen tabular (93).** `$[c/100,\ \overline{w}_{1:4},\ w_{last,1:4},\ \overline{r}_{1:14},\ r_{last,1:14},\ \sigma_r{}_{1:14},\ \overline{r}_{last10,1:14},\ (r_{last}-r_{first})_{1:14},\ (\overline{r}_{last5}-\overline{r}_{first5})_{1:14}]$` → `1 + 8 + 84 = 93`.
- **`cyc_norm`.** `$\tilde{c} = c/100$` repetido en los 50 pasos como canal 19 de la secuencia. Sin él, el BiLSTM pierde 1,094 RMSE (5,419 → 6,513, medido en el bundle B).

**Salidas esperadas:** `train (52635, 23)`, `test (12538, 23)`, 1.056 nulos en `train_con_nulos`, `dev (17450, 50, 19)`, `dev X_tab (17450, 93)`, `test (6196, 50, 19)`, `test X_tab (6196, 93)`.

**Tiempo:** ~15 s.

---

### 3.2 NB02 — `02_modelos_A.ipynb`: los cinco clásicos, entrenados

**Objetivo:** establecer el techo de la liga de fila con entrenamiento real y mostrar que la elección de familia importa menos que la representación.

**Contrato de celdas:**

| # | Tipo | Contenido |
|---|---|---|
| 1 | md | Título + "Dónde estamos": NB01 fijó la partición y la liga de fila |
| 2 | co | Setup: `sys.path`, imports, `mostrar`, carga de `train_con_nulos.parquet` y `test_con_nulos.parquet` |
| 3 | md | **Reconstrucción del frame tabular**: por qué se deriva en el notebook y no se lee un parquet mágico |
| 4 | co | `imputar_ffill` con medianas de train → `X_tr`, `y_tr`, `X_te`, `y_te`; `assert` de 21 columnas, 0 nulos, `unit` presente |
| 5 | md | **GroupKFold**: ecuación y por qué no `KFold` |
| 6 | co | `ESPEC` de `train_clasicos`; entrena los 5 con `GridSearchCV(GroupKFold(3))`; SVM sobre submuestra de 5.000 con `default_rng(42)`; tabla de resultados con `mejores_params`, `tiempo_s`, métricas train/test |
| 7 | md | **Qué es cada familia** + ecuación de cada una (Ridge, KNN, RF, XGB, SVR) |
| 8 | co | Imprime la tabla ordenada y elige el mejor por `rmse_test` con desempate por simplicidad (`ORDEN_SIMPLE`) |
| 9 | md | **Métricas**: RMSE, MAE, R² y por qué RMSE manda (fallos gordos) |
| 10 | co | Real vs predicho del mejor (muestra de 4.000 filas test) |
| 11 | md | **Análisis por motor**: el promedio global esconde al motor difícil |
| 12 | co | `macro_rmse` por unidad en test (11/14/15) |
| 13 | md | **Lectura honesta**: el mejor clásico ronda 9 RMSE; una fila no alcanza |
| 14 | md | **Cierre → NB03**: "¿mejora una red no lineal sobre la misma tabla?" |

**Ecuaciones obligatorias:**

- **Ridge.** `$\hat{\beta} = \arg\min_\beta \|y - X\beta\|_2^2 + \alpha\|\beta\|_2^2$`, `$\alpha \in \{0.1, 1, 10\}$`.
- **KNN.** `$\hat{y}(x) = \frac{1}{k}\sum_{i \in N_k(x)} y_i$`, `$k \in \{5, 15, 31\}$`.
- **Random Forest.** `$\hat{y} = \frac{1}{B}\sum_{b=1}^{B} T_b(x)$` con `B=200` y `max_depth ∈ {8, 15, None}`; cada árbol minimiza varianza en los cortes.
- **XGBoost.** `$\mathcal{L} = \sum_i \ell(y_i, \hat{y}_i) + \sum_k \Omega(f_k)$`, `$\Omega(f) = \gamma T + \frac{1}{2}\lambda\|w\|^2$`, boosting aditivo con `lr=0.05`.
- **SVR.** `$\hat{y}(x) = \sum_i (\alpha_i - \alpha_i^*) K(x_i, x) + b$` con `$K$` RBF y pérdida `$\epsilon$`-insensible; `$C \in \{1, 10\}$`, `$\epsilon \in \{0.5, 1\}$`.
- **GroupKFold.** Los folds particionan `$U$`, no las filas: `$\bigcup_f V_f = U$` y `$V_f \cap V_{f'} = \emptyset$`.

**Salidas esperadas:** 5 filas; el mejor debe rondar RMSE test 9,06 (SVM sobre 5k). No se asserta el valor: se imprime.

**Tiempo:** ~2 min.

---

### 3.3 NB03 — `03_modelos_B.ipynb`: no-linealidad e interpretabilidad

**Objetivo:** medir si una red no lineal mejora la liga de fila y explicar **qué mira** el modelo. Cierra la liga de fila y justifica pasar a la ventana.

**Contrato de celdas:**

| # | Tipo | Contenido |
|---|---|---|
| 1 | md | Título + "Dónde estamos": NB02 dejó el techo de la liga de fila en ~9 RMSE |
| 2 | co | Setup: `sys.path`, imports, `mostrar`, carga del frame tabular (misma reconstrucción que NB02) |
| 3 | md | **Los cuatro experimentos**: `EXPS` y la hipótesis de cada uno |
| 4 | co | Imprime `BASE_KW` y `EXPS` (nombre, kwargs, hipótesis) |
| 5 | md | **MLP**: ecuación de la capa y de la pérdida |
| 6 | co | Entrena los 4 con `make_pipeline(MLPRegressor(**{**BASE_KW, **kw}))`; tabla con `rmse_train/test`, `mae_test`, `r2_test`, `n_iter_`, `tiempo_s` |
| 7 | co | Elige el mejor por `rmse_test`; real vs predicho (4.000 filas) |
| 8 | md | **CV del mejor** (GroupKFold 3 por motor): ¿generaliza o fue suerte? |
| 9 | co | `cross_val_score` con `GroupKFold(3)` y `n_jobs=1`; media ± std; compara con el test |
| 10 | md | **Importancia por permutación**: definición y ecuación |
| 11 | co | `permutation_importance` sobre el mejor MLP ya entrenado (200 filas test, 5 repeticiones, seed 7); top 15; `assert` de que los nombres coinciden con las 21 columnas de entrada |
| 12 | md | **SHAP**: qué añade sobre permutación y ecuación de Shapley |
| 13 | co | Entrena **un** XGB con la configuración de `ESPEC["xgb"][0]` (sin re-buscar grid); `make_pre()`; `TreeExplainer` con fondo explícito de 200 filas; `shap_values` sobre 200 filas test; top 10 por `mean |SHAP|` |
| 14 | md | **Comparación**: qué variables coinciden entre permutación y SHAP, y qué significa |
| 15 | co | Tabla cruzada top-10 de ambos métodos; lectura |
| 16 | md | **Cierre → NB04**: "la red no lineal mejora poco; el límite no es la familia, es el grano. Una fila no tiene historia." |

**Ecuaciones obligatorias:**

- **MLP.** `$h^{(1)} = \sigma(W_1 x + b_1)$`, `$h^{(2)} = \sigma(W_2 h^{(1)} + b_2)$`, `$\hat{y} = W_3 h^{(2)} + b_3$`, `$\sigma = \mathrm{ReLU}$`.
- **Pérdida y regularización.** `$\mathcal{L} = \frac{1}{2n}\|y - \hat{y}\|_2^2 + \frac{\alpha}{2}\sum_l \|W_l\|_F^2$`, `$\alpha \in \{10^{-3}, 10^{-2}\}$`; Adam con `lr = 10^{-3}`, early stopping sobre 10 % de validación.
- **Permutación.** `$I_j = \frac{1}{R}\sum_{r=1}^{R}\left[\mathcal{L}\left(y, X^{(j,\pi_r)}\right) - \mathcal{L}(y, X)\right]$, $R=5$`.
- **SHAP.** `$\phi_j = \sum_{S \subseteq F\setminus\{j\}} \frac{|S|!\,(|F|-|S|-1)!}{|F|!}\left[f(S\cup\{j\}) - f(S)\right]$`; `TreeExplainer` lo calcula exacto para árboles.

**Salidas esperadas:** 4 filas; el mejor ronda RMSE test 7,70 (`E1_capacidad`). La CV debe quedar en el mismo orden de magnitud que el test; si se separa mucho, **se reporta**, no se oculta.

**Tiempo:** ~6–8 min (la CV de 3 folds sobre 52k filas es el tramo caro).

---

### 3.4 NB04 — `04_lgbm_adaptada.ipynb`: el especialista tabular sobre ventanas

**Objetivo:** introducir el grano ventana con el modelo más barato y fuerte de la rama tabular, y dejar el especialista que NB05 reutilizará.

**Contrato de celdas:**

| # | Tipo | Contenido |
|---|---|---|
| 1 | md | Título + "Dónde estamos": la liga de fila se agotó en ~7,7 RMSE; el límite es el grano |
| 2 | md | Glosario: ventana, grano, GroupKFold (conservar, es bueno) |
| 3 | co | Setup: `sys.path`, `TF_CPP_MIN_LOG_LEVEL`, `warnings`, `mostrar`, `ventanas_adaptadas()` |
| 4 | co | Imprime fit/holdout/test, formas de `dev` y `test`, y el desglose 93 = 1 + 8 + 84 |
| 5 | md | **LightGBM cuantílico**: por qué cuantil 0,35 y no mediana |
| 6 | co | Entrena `make_lgbm(42)` sobre las ventanas de fit-units; evalúa en holdout-16 y test (RMSE, MAE, R², NASA) |
| 7 | md | **CV diagnóstica** (GroupKFold 3, solo fit-units) |
| 8 | co | 3 folds; media ± std; lectura: el fold difícil concentra los motores largos |
| 9 | md | **La ablación del objetivo**: 0,35 vs 0,50, medido en holdout y test |
| 10 | co | Entrena `make_lgbm(42)` con `objective="quantile", alpha=0.5` sobre las mismas ventanas; tabla comparativa holdout/test |
| 11 | md | **Lectura honesta**: el gate de dev no arbitra entre 0,35 y 0,50; se mantiene 0,35 por pre-registro (ADR-007), no por conveniencia |
| 12 | md | **Importancia de variables** del LGBM |
| 13 | co | Top 10 por ganancia; lectura (qué domina el resumen de 93 columnas) |
| 14 | md | Real vs predicho + análisis por motor |
| 15 | co | Figura real vs predicho (test) y `macro_rmse` por unidad |
| 16 | md | **Cierre → NB05**: "7,07 RMSE con una foto de la ventana. ¿Cuánto cuesta leer la película?" |

**Ecuaciones obligatorias:**

- **Pérdida cuantílica (pinball).** `$L_\alpha(y, \hat{y}) = \alpha\,(y - \hat{y})$` si `$y > \hat{y}$`, `$(1-\alpha)(\hat{y} - y)$` si no; `$\alpha = 0.35$`.
- **LightGBM.** Crecimiento leaf-wise por histogramas; `$\mathcal{L} = \sum_i L_\alpha(y_i, \hat{y}_i) + \sum_k \Omega(f_k)$`, `$\Omega(f) = \gamma T + \frac{\lambda}{2}\|w\|^2 + \alpha_{L1}\|w\|_1$`; `num_leaves=15`, `max_depth=4`, `min_child_samples=50`, `$\alpha_{L1}=1$`, `$\lambda=5$`.
- **NASA score.** `$S = \sum_i \left[\exp(-d_i/13) - 1\right]$` si `$d_i < 0$`, `$\left[\exp(d_i/10) - 1\right]$` si `$d_i \ge 0$`, con `$d_i = \hat{y}_i - y_i$`. Sobre-predecir cuesta más.
- **macro-RMSE.** `$\mathrm{RMSE}_{macro} = \frac{1}{|U|}\sum_{u \in U} \sqrt{\frac{1}{n_u}\sum_{i \in u}(y_i - \hat{y}_i)^2}$`.

**Salidas esperadas:** CV media ≈ 12,3; test ≈ 7,07 RMSE / ≈ 7,4k NASA. El `assert` permitido es de forma (`X_tab.shape[1] == 93`) y de partición, no de métrica.

**Tiempo:** ~1 min.

---

### 3.5 NB05 — `05_ensemble_adaptado.ipynb`: el híbrido completo

**Objetivo:** entrenar el modelo que gana, explicar cada pieza con su ecuación, medir el veredicto D11 y cerrar con la tabla final. Es el notebook más largo y el que sostiene la defensa.

**Contrato de celdas:**

| # | Tipo | Contenido |
|---|---|---|
| 1 | md | Título + "Dónde estamos": NB04 dejó el especialista tabular en 7,07 |
| 2 | md | **El reparto**: qué aporta cada motor (BiLSTM lee la secuencia; LGBM lee la foto; el meta reconcilia) |
| 3 | md | **`cyc_norm` está en la base pero no en el meta**: por qué (el meta no debe leer un contador) |
| 4 | co | Setup: `sys.path`, `TF_CPP_MIN_LOG_LEVEL`, `warnings`, `mostrar`, imports de `run_seed`, `oof_base_predictions`, `select_beta_grouped`, `fit_meta_learners`, `HybridStackingEnsemble`, `fit_conformal`, `empirical_coverage`, `causal_ema_by_unit` |
| 5 | md | **Paso 1 — los dos especialistas**: `run_seed` entrena LGBM + BiLSTM con el protocolo honesto |
| 6 | co | `construir_raw_adaptado()` inline (misma lógica que el módulo, sin persistir); `run_seed(raw, seed=42, ...)`; imprime tiempos, parámetros, épocas ejecutadas |
| 7 | md | **BiLSTM**: arquitectura y ecuaciones |
| 8 | co | `out["bilstm"].summary()`; curva de entrenamiento con `mostrar`; lectura de la mejor época |
| 9 | md | **Paso 2 — calibración de `beta` fuera de fold** |
| 10 | co | `oof_base_predictions(raw, unidades_dev, n_splits=3, epochs=15)`; `select_beta_grouped(..., span=5, use_cycle_feature=False)`; imprime `beta`, `spread` y la curva por fold; `assert` de que cada fold no comparte motor entre fit y score |
| 11 | md | **Beta**: ecuación de la mezcla y del criterio |
| 12 | co | Figura `beta` vs criterio por fold |
| 13 | md | **Paso 3 — meta-learner** |
| 14 | co | `fit_meta_learners(Z_hold, y_hold)` sobre las ventanas de holdout-16; `assert` de `Z_hold.shape[1] == 2` |
| 15 | md | **Meta**: ecuación del diseño y de la reconciliación 50/50 |
| 16 | co | Pesos del ridge; importancia del LGBM meta; lectura |
| 17 | md | **Paso 4 — EMA causal** |
| 18 | co | Aplica `causal_ema_by_unit` a las predicciones del híbrido; tabla con y sin EMA |
| 19 | md | **EMA**: ecuación recursiva y `span=5` |
| 20 | md | **Paso 5 — banda conformal** |
| 21 | co | `fit_conformal(oof_calib["y"], oof_calib["pred_ema"], target=0.90)`; asigna `ensemble.conformal`; `predict_interval` en test; cobertura empírica global y por motor |
| 22 | md | **Conformal**: ecuación de los cuantiles por bin |
| 23 | md | **No-determinismo de TensorFlow** (obligatorio, antes de la tabla) |
| 24 | co | Tabla de test: LGBM-C, BiLSTM-C, BiLSTM-C+EMA5, Híbrido-C+EMA5, + fila histórica B (4.251 / 2305,1, etiquetada "bundle congelado, no reentrenado aquí") |
| 25 | co | `assert` de consistencia: el RMSE del LGBM de `run_seed` coincide con el de NB04 (tolerancia 1e-6); si no, hay fuga o desalineación |
| 26 | md | **macro-RMSE por motor**: el motor 14 se lleva el error |
| 27 | co | Tabla por unidad + lectura |
| 28 | md | **Diagnóstico**: real vs predicho, residuos, error por tramo de RUL |
| 29 | co | Tres figuras con `mostrar` + lecturas |
| 30 | md | **Paso 6 — estabilidad entre semillas** |
| 31 | co | Para seeds `(7, 123)`: `run_seed` + `fit_meta_learners` + ensemble con el `beta` seleccionado en 42; tabla por semilla; media ± std con `ddof=1`; incluye la semilla 42 |
| 32 | md | **Veredicto D11**: criterio pre-registrado y su lectura |
| 33 | co | `RMSE_C <= 4.251` y `NASA_C <= 2305.1` sobre la media multiseed; imprime ADOPTAR o "C queda como experimento, B sigue" |
| 34 | md | **Dos ligas, dos campeones**: tabla cruzada con las cifras de NB02/NB03 **citadas con procedencia** ("cifras de NB02/NB03, no recalculadas aquí") |
| 35 | md | **Cierre — qué se lleva la defensa**: 5 frases, una por notebook |

**Ecuaciones obligatorias:**

- **BiLSTM.** Entrada `$(50, 19)$` → BatchNorm → 2 capas `Bidirectional(LSTM(64))` con dropout 0,2 → concatenación de *last step*, *average pool* y *max pool* → `Dense(32, ReLU)` → `Dense(1)`. Pérdida `Huber($\delta=10$)`; Adam `lr=10^{-3}`; early stopping sobre holdout-16 con `patience=5`.
- **Meta.** `$Z = [p_{lstm}, p_{lgb}]$` (dos columnas, sin ciclo); `$p_{meta} = \frac{1}{2}\,\mathrm{Ridge}(Z) + \frac{1}{2}\,\mathrm{LGBM}(Z)$`; el ridge usa `RidgeCV` sobre `$\alpha \in \mathrm{logspace}(-2, 3, 20)$`; el LGBM meta usa `max_depth=3`, `num_leaves=7`, `n_estimators=120`, `lr=0.03`.
- **Beta.** `$p(\beta) = p_{lstm} + \beta\,(p_{meta} - p_{lstm})$`, `$\beta \in \{0, 0.05, \ldots, 1\}$`; criterio `$J(\beta) = \frac{\mathrm{RMSE}(\beta)}{\mathrm{RMSE}_{lstm}} + \frac{\mathrm{NASA}(\beta)}{\mathrm{NASA}_{lstm}}$`; `$\hat{\beta} = \mathrm{median}_f(\arg\min_\beta J_f)$` sobre folds agrupados por motor.
- **EMA.** `$s_t = \alpha\,p_t + (1-\alpha)\,s_{t-1}$`, `$\alpha = 2/(\mathrm{span}+1) = 1/3$` para `span=5`; causal dentro de cada motor, ordenado por ciclo.
- **Conformal.** `$e_i = y_i - \hat{y}_i$`; bins de `$\hat{y}$` en `$[0,25), [25,50), [50,75), [75,\infty)$`; `$\alpha = (1-0.90)/2 = 0.05$`; `$q_{lo} = Q_{\alpha}(e)$`, `$q_{hi} = Q_{1-\alpha}(e)$`; intervalo `$[\hat{y} + q_{lo},\ \hat{y} + q_{hi}]$`; bins con menos de 100 filas usan los cuantiles globales. Se calibra sobre residuos **fuera de fold**, nunca sobre las filas que entrenaron al meta.
- **Cobertura.** `$\mathrm{cov} = \frac{1}{n}\sum_i \mathbf{1}[\,lo_i \le y_i \le hi_i\,]$`.

**Celda obligatoria de no-determinismo (markdown, antes de la tabla):**

> Las cifras de esta tabla pueden diferir en ±0,02 RMSE de las publicadas en `models/` y en el README. La causa no es un error: TensorFlow no garantiza reproducibilidad bit a bit entre ejecuciones (reducciones en paralelo, oneDNN). La fila "Híbrido-B histórico" es el bundle congelado y se cita como referencia, no se reentrena aquí. Documentado en `notebooks/ds02_ensemble/EVALUACION_EJECUCION.md`.

**Salidas esperadas:** `beta` en `{0.0, …, 1.0}` (esperado 1,00); tabla de test con el híbrido en ~4,3–4,4 RMSE; cobertura ≈ 0,88–0,92; multiseed `4,35 ± 0,02`; veredicto D11 impreso.

**Tiempo:** ~6 min (seed 42: ~80 s BiLSTM + ~90 s OOF; seeds 7 y 123: ~80 s cada una).

---

## 4. Tareas

### Tarea 0 — Infraestructura y línea base

**Archivos:** los cinco notebooks (solo `metadata.kernelspec`).

**Pasos:**

- [ ] Comprobar el árbol limpio: `git status --porcelain` debe estar vacío.
- [ ] En los cinco notebooks, fijar `metadata.kernelspec = {"display_name": "Python (ds02-venv)", "language": "python", "name": "ds02-venv"}`.
- [ ] Verificar: `.venv\Scripts\python.exe -c "import json; [print(p, json.load(open(p, encoding='utf-8'))['metadata']['kernelspec']['name']) for p in [...]]"` → cinco veces `ds02-venv`.
- [ ] Capturar la línea base de tests: `.venv\Scripts\python.exe -m pytest tests -q` → anotar el resultado exacto (ver §5.2).
- [ ] Commit: `chore(notebooks): pin ds02-venv kernel in 01-05`.

**Criterio de aceptación:** los cinco declaran `ds02-venv`; ningún otro cambio en el repo.

---

### Tarea 1 — NB01: datos y contrato

**Archivos:** `notebooks/01_eda.ipynb`.

**Consume:** `data/processed/train.parquet`, `test.parquet`, `train_con_nulos.parquet`, `auditoria_nulos.json`.

**Produce:** el contrato (partición, imputación, residualización, ventanas) que citan 02–05.

**Pasos:**

- [ ] Reescribir el notebook según §3.1, conservando las cinco figuras y su lectura actual.
- [ ] Reemplazar todos los `savefig('../resultados/...')` por el helper `mostrar`.
- [ ] Añadir las ecuaciones de §3.1 en celdas markdown.
- [ ] Asignar `id` estable a cada celda (`nb01-c01`, …).
- [ ] Ejecutar: `nbconvert --execute` (comando en §5.1).
- [ ] Verificar salidas: 17.450 / 6.196 ventanas, formas `(·,50,19)` y `(·,93)`, 1.056 nulos.
- [ ] `pytest` contra la línea base.
- [ ] Commit: `docs(notebooks): rewrite 01 as data contract with residualization and window spec`.

---

### Tarea 2 — NB02: cinco clásicos entrenados

**Archivos:** `notebooks/02_modelos_A.ipynb`.

**Consume:** contrato de NB01; `track_clase.pipeline_clase.make_pipeline`; `track_clase.train_clasicos.ESPEC`, `ORDEN_SIMPLE`.

**Produce:** el mejor clásico y su RMSE test (cifra que cita el cierre de NB03).

**Pasos:**

- [ ] Eliminar la celda `ANCLA` y la lectura de `resultados/comparativa.csv`.
- [ ] Reconstruir `X_tr/X_te` desde `train_con_nulos.parquet` / `test_con_nulos.parquet` con `imputar_ffill` + `medianas_train`.
- [ ] Implementar el bucle de entrenamiento sobre `ESPEC` (GridSearchCV + GroupKFold(3), SVM en submuestra 5k).
- [ ] Añadir ecuaciones de §3.2 y la celda de análisis por motor con `macro_rmse`.
- [ ] Ejecutar y verificar las 5 filas.
- [ ] `pytest` contra la línea base.
- [ ] Commit: `feat(notebooks): train the five classic models inside 02`.

---

### Tarea 3 — NB03: MLP e interpretabilidad

**Archivos:** `notebooks/03_modelos_B.ipynb`.

**Consume:** mismo frame tabular que NB02; `track_clase.train_mlp.EXPS`, `BASE_KW`.

**Produce:** el mejor MLP, la importancia por permutación y el top-10 SHAP.

**Pasos:**

- [ ] Eliminar la lectura de `resultados/mlp_comparativa.csv`, `resultados/importancia_permutacion.csv` y `resultados/shap_importancia.csv`.
- [ ] Eliminar la carga de `models/mejor_modelo_clase.joblib`.
- [ ] Entrenar los 4 `EXPS` con `make_pipeline`.
- [ ] Implementar permutación sobre el mejor MLP entrenado (no sobre un clásico cargado).
- [ ] Implementar SHAP inline: un XGB con la config de `ESPEC["xgb"][0]` + `TreeExplainer` con fondo explícito (mismo patrón que `shap_clase.ejecutar_shap`, sin escribir CSV/PNG).
- [ ] Mantener la CV del mejor (3 folds) y su lectura.
- [ ] Ejecutar y verificar las 4 filas y los dos rankings.
- [ ] `pytest` contra la línea base.
- [ ] Commit: `feat(notebooks): train MLPs and compute permutation + SHAP inside 03`.

---

### Tarea 4 — NB04: LightGBM sobre ventanas

**Archivos:** `notebooks/04_lgbm_adaptada.ipynb`.

**Consume:** `ventanas_adaptadas`, `ds02_rul.pipeline.make_lgbm`.

**Produce:** el especialista tabular y su RMSE, que NB05 verificará por igualdad.

**Pasos:**

- [ ] Eliminar la lectura de `resultados/comparativa_ventanas.csv` y de `track_clase/models/lgbm_adaptada.joblib`.
- [ ] Entrenar `make_lgbm(42)` sobre las ventanas de fit-units.
- [ ] Mantener la CV diagnóstica sobre fit-units.
- [ ] Añadir la ablación 0,35 vs 0,50 en holdout y test, con la lectura de ADR-007.
- [ ] Añadir importancia de variables y análisis por motor.
- [ ] Ejecutar y verificar.
- [ ] `pytest` contra la línea base.
- [ ] Commit: `feat(notebooks): train the quantile LightGBM inside 04`.

---

### Tarea 5 — NB05: híbrido completo

**Archivos:** `notebooks/05_ensemble_adaptado.ipynb`.

**Consume:** `run_seed`, `oof_base_predictions`, `select_beta_grouped`, `fit_meta_learners`, `HybridStackingEnsemble`, `fit_conformal`, `causal_ema_by_unit`, `evaluate_predictions`, `macro_rmse`.

**Produce:** la tabla de test, la cobertura conformal, el multiseed y el veredicto D11.

**Pasos:**

- [ ] Eliminar las lecturas de los cuatro CSVs y del bundle en `track_clase/models/`.
- [ ] Implementar `construir_raw_adaptado` inline (copiar la lógica del módulo, sin `save_ensemble`).
- [ ] Entrenar seed 42 con `run_seed`; mostrar `summary()` y curva.
- [ ] Calibrar `beta` con OOF y `select_beta_grouped`; graficar la curva por fold.
- [ ] Entrenar el meta sobre holdout-16; mostrar pesos e importancia.
- [ ] Aplicar EMA y tabla con/sin EMA.
- [ ] Calibrar conformal y medir cobertura global y por motor.
- [ ] Añadir la celda de no-determinismo **antes** de la tabla de métricas.
- [ ] Añadir el `assert` de consistencia LGBM NB04 ↔ NB05.
- [ ] Multiseed con `beta` fijo; media ± std con la semilla 42 incluida.
- [ ] Calcular y **reportar** el veredicto D11 (no assertar que se adopta).
- [ ] Cerrar con "dos ligas, dos campeones" citando NB02/NB03.
- [ ] Asignar `id` a las 26 celdas y validar con `nbformat.validate`.
- [ ] Ejecutar y verificar.
- [ ] `pytest` contra la línea base.
- [ ] Commit: `feat(notebooks): train the full hybrid ensemble inside 05`.

---

### Tarea 6 — Pasada completa y cierre

**Pasos:**

- [ ] Ejecutar 01 → 05 en orden, sin `--inplace` en un directorio temporal primero, y después `--inplace` para dejar los outputs.
- [ ] Confirmar tiempos: total ≤ 20 min.
- [ ] Confirmar que `git status` solo muestra los cinco notebooks.
- [ ] Confirmar que `notebooks/ds02_ensemble/` no aparece en `git status`.
- [ ] Confirmar que no se creó ni modificó nada en `resultados/`, `models/` ni `track_clase/models/` (comparar `git status --ignored` antes/después si hace falta).
- [ ] Revisar el hilo narrativo: cada notebook cita al anterior en su primera celda y al siguiente en su cierre.
- [ ] `pytest` final contra la línea base.
- [ ] Commit: `docs(notebooks): complete the 01-05 training narrative`.

---

## 5. Protocolo de verificación

### 5.1 Ejecución de un notebook

```powershell
.venv\Scripts\python.exe -m jupyter nbconvert --to notebook --execute --inplace `
  --ExecutePreprocessor.kernel_name=ds02-venv `
  --ExecutePreprocessor.timeout=1800 `
  notebooks\01_eda.ipynb
```

Cambiar el nombre del archivo por el del notebook en curso. `--inplace` deja los outputs en el archivo; sin `--inplace` escribe un `.nbconvert.ipynb` al lado, que hay que borrar.

**Señal de éxito:** exit code 0 y ninguna celda con `output_type: error`. Verificación rápida:

```powershell
.venv\Scripts\python.exe -c "import json,sys; nb=json.load(open(r'notebooks\05_ensemble_adaptado.ipynb',encoding='utf-8')); errs=[(i,o.get('ename')) for i,c in enumerate(nb['cells']) for o in c.get('outputs',[]) if o.get('output_type')=='error']; print('ERRORES:',errs or 'ninguno')"
```

### 5.2 Tests

```powershell
.venv\Scripts\python.exe -m pytest tests -q
```

**Línea base medida en este repo (antes de tocar nada):** `3 failed, 232 passed, 6 skipped in ~185 s`.

Los 3 fallos son **preexistentes** y ajenos a este trabajo:

- `tests/test_clase_bundle_c.py::{test_raw_adaptado_alineado_sin_nulos, test_raw_adaptado_particiones_congeladas, test_raw_adaptado_medianas_solo_fit_units}`.
- Causa: `tests/test_audit_fixes.py:237` y `tests/test_ui_rules.py:166` instalan un paquete falso `sys.modules["ds02_rul"]` que nunca retiran; cuando `test_clase_bundle_c` corre después, importa el stub y falla con `ImportError: cannot import name 'HybridStackingEnsemble' from 'ds02_rul' (unknown location)`.
- En aislamiento pasan: `.venv\Scripts\python.exe -m pytest tests/test_clase_bundle_c.py -q` → `3 passed`.

**Criterio:** ninguna tarea introduce fallos nuevos. Se acepta la misma línea base (`3 failed, 232 passed, 6 skipped`) y se documenta en el commit. **No se arreglan los tests**: R2 lo prohíbe.

### 5.3 Verificación de no-escritura

Antes y después de ejecutar la pasada completa:

```powershell
git status --porcelain
git status --porcelain --ignored | Select-String 'resultados/|models/'
```

El primer comando solo debe listar los cinco notebooks. El segundo no debe mostrar archivos nuevos con fecha posterior al inicio de la tarea.

---

## 6. Riesgos y trampas

| # | Riesgo | Prob. | Mitigación |
|---|---|---|---|
| 1 | Llamar sin querer `entrenar_todo()`/`entrenar_mlp()`/`entrenar()` y escribir en `models/` o `resultados/` | Alta | Lista negra de R4; revisar cada import antes de ejecutar; §5.3 |
| 2 | Kernel `python3` por defecto al abrir el notebook | Alta | Tarea 0 + `--ExecutePreprocessor.kernel_name=ds02-venv` explícito |
| 3 | `nbconvert --inplace` tarda 6 min en NB05 y se itera muchas veces | Media | Desarrollar NB05 con `SEEDS = (42,)` y restaurar `(42, 7, 123)` antes de la pasada final; la tabla multiseed debe mostrar 3 semillas |
| 4 | TF no determinista → el executor cree que rompió algo | Alta | Celda de no-determinismo obligatoria en NB05; comparar contra ±0,02, nunca con igualdad exacta |
| 5 | `assert` de métricas hardcodeadas | Media | R7: solo invariantes estructurales |
| 6 | `matplotlib.use('Agg')` + `plt.show()` no renderiza inline | Alta | Helper `mostrar(fig)` con `BytesIO` + `Image(data=...)`; nunca `savefig` a disco |
| 7 | Duplicar lógica de dominio en el notebook | Media | §2.3: se importan constantes y funciones puras; solo se duplica el bucle de orquestación |
| 8 | NB05 reentrena el LGBM y difiere de NB04 por orden de filas | Media | `assert` de consistencia con tolerancia 1e-6; si falla, revisar el orden de `build_windows` antes de seguir |
| 9 | `pytest` rojo por los 3 fallos preexistentes | Alta | §5.2: línea base documentada; no se tocan tests |
| 10 | Celdas sin `id` (`MissingIDFieldWarning`) en NB05 | Alta | Asignar `id` estable y validar con `nbformat.validate` |
| 11 | `data/processed/*.parquet` no existe en un clon limpio (`data/` está en `.gitignore:91`) | Media | Es una dependencia preexistente de todo el track; documentarla en NB01 como requisito de ejecución, no intentar regenerarla aquí |
| 12 | El tribunal pregunta por la diferencia 4,25 vs 4,35 | Alta | La fila "B histórico" está etiquetada como bundle congelado; la celda de no-determinismo lo explica antes de la tabla |

---

## 7. Criterios de aceptación

- [ ] Los cinco notebooks declaran kernel `ds02-venv` y se ejecutan de punta a punta con exit code 0.
- [ ] Ningún notebook lee `resultados/*.csv`, `models/*.joblib` ni `track_clase/models/*`.
- [ ] Ningún notebook escribe en disco durante la ejecución (figuras en memoria).
- [ ] NB02 entrena los 5 clásicos; NB03 entrena los 4 MLP + el XGB de SHAP; NB04 entrena el LGBM; NB05 entrena BiLSTM, meta, beta, EMA, conformal y 3 semillas.
- [ ] Cada notebook contiene las ecuaciones de su capítulo (§3).
- [ ] Cada notebook abre citando al anterior y cierra citando al siguiente.
- [ ] NB05 imprime el veredicto D11 y la tabla "dos ligas, dos campeones" con procedencia explícita.
- [ ] `pytest tests -q` no introduce fallos nuevos respecto de la línea base.
- [ ] `git status` solo muestra los cinco notebooks (y este plan).
- [ ] `notebooks/ds02_ensemble/` permanece intacto.
- [ ] Pasada completa 01 → 05 en ≤ 20 min.

---

## 8. Fuera de alcance y decisiones abiertas

**Fuera de alcance (no hacer):**
- Refactorizar `track_clase/` para separar cálculo de persistencia. Sería la solución limpia a la duplicación del bucle, pero R2 lo prohíbe y abriría un cambio en `src`/`track_clase` que este plan no cubre.
- Arreglar los 3 tests preexistentes de `test_clase_bundle_c.py`.
- Regenerar `data/processed/*.parquet`.
- Re-freeze de artefactos en `models/`.

**Decisiones que el ejecutor puede ajustar, con consecuencia declarada:**

1. **CV de NB03 (3 folds, ~4 min).** Si el presupuesto de tiempo aprieta, se puede reducir a 2 folds o quitar. Consecuencia: se pierde la comprobación "el test no fue suerte". Si se quita, hay que decirlo en el cierre de NB03.
2. **Ablación 0,35 vs 0,50 en NB04.** Si se quita, se pierde la evidencia de ADR-007 y el cierre de NB04 queda como afirmación, no como medida. Recomendado mantener: cuesta ~6 s.
3. **Tabla cruzada de NB05.** Se implementa como markdown con cifras citadas de NB02/NB03, no recalculadas. Si el usuario prefiere una tabla viva, la alternativa es reentrenar en NB05 los dos campeones de la liga de fila (~1 min extra) a cambio de duplicar entrenamiento. Recomendado: markdown con procedencia.

**Decisiones ya cerradas (no reabrir sin autorización):**
- Reparto T2 (§1.4).
- Prohibición de escribir en `models/` y `resultados/` (R3).
- Prohibición de tocar `src/`, `track_clase/`, `app/`, `mia/` (R2).
- `notebooks/ds02_ensemble/` intacto (R5).
