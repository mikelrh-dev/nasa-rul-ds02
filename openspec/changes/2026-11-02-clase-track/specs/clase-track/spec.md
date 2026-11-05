# Spec delta: Track de clase — `clase-track` (nueva capacidad)

**Change:** `2026-11-02-clase-track`
**Status:** Proposed
**Capability:** `clase-track` (new; no modifica `rul-prediction-ds02`, `ds02-dss-ui`, `ds02-live-evaluation`, `ds02-rules-engine`)

---

## ADDED

### Requirement: Dataset de clase con nulos auditados y categórica

La capacidad SHALL producir `data/processed/{train_con_nulos,train,test,X_train,X_test,y_train,y_test}.parquet` desde filas downsampleadas con: inyección MAR SOLO en T30 cuando `alt>27_000 & Mach>0.68` (`tasa_elegible=0.10 ~= 2.1% global, seed=7`, mask guardada; el 30k/0.8 teórico no existe en DS02: Mach máx 0.74); auditoría con tasa global/en elegibles, 100% en crucero alto, rachas por unidad y conteo >3 seguidos (R1); análisis de si los nulos son al azar o con patrón (MAR) antes de imputar; imputación `groupby(unit).ffill()` tras ordenar por ciclo + `fillna(mediana_train)` (mediana SOLO de train, solo primer NaN); categórica `fase_vuelo` derivada SOLO de `alt`/`Mach` con umbrales publicados y justificación de la variable nueva (`fase_vuelo`); split por `unit` (nunca aleatorio). Test de robustez AC 20-170 (degradación <5% RMSE, R1 si >3 ciclos) en Fase 2.

#### Scenario: Imputación causal sin fuga
- GIVEN ventanas ordenadas por ciclo con nulos inyectados
- WHEN `imputar_ffill` corre
- THEN ningún valor de ciclo futuro ni de otra unidad entra en el relleno
- AND la primera fila de cada unidad usa la mediana de train

#### Scenario: Split por motor
- GIVEN unidades DS02
- WHEN se particiona train/test
- THEN ninguna `unit` aparece en ambos lados
- AND el test se evalúa una sola vez, con el modelo elegido

### Requirement: EDA con tabla y 5 gráficos comentados

`notebooks/01_eda.ipynb` SHALL incluir tabla de campos (nombre, qué significa, tipo, %nulos antes/después, descarte y porqué), chequeo de duplicados/imposibles, análisis de patrón de nulos, y AL MENOS 5 figuras matplotlib: barras, histograma, boxplot (misma numérica), dispersión (2 vars), heatmap correlación. Cada figura SHALL llevar "qué veo / conclusión" y 1-2 figuras SHALL citarse en el README.

### Requirement: Pipeline sklearn compartido

`src/clase/pipeline_clase.py` SHALL exponer un `ColumnTransformer` (`StandardScaler` numéricas + `OneHot(handle_unknown=ignore)` para `fase_vuelo`) usado por LOS 5 clásicos y el MLP, y `predict_caso_nuevo(modelo, dict)` que puntúa 1 fila. El `models/mejor_modelo.joblib` SHALL guardar el `Pipeline` completo.

#### Scenario: Un solo preprocesado
- GIVEN los 6 entrenamientos de clase
- WHEN se inspecciona cada `Pipeline`
- THEN todos comparten el mismo `pre` (mismo transformador, refitado solo en train)

### Requirement: Cinco clásicos con GridSearchCV y tiempos

La capacidad SHALL entrenar Ridge, KNN, RF, XGBoost y SVR sobre `X_tab`, cada uno como `Pipeline(pre, reg)` con `GridSearchCV(cv=GroupKFold(3, groups=unit))` y grids mínimos publicados. En regresión los 5 de la rúbrica se adaptan a Ridge, KNN, RF, XGBoost y SVR con GridSearchCV y validación cruzada; SMOTE no aplica en regresión y SHALL documentarse como N/A. SHALL registrar `resultados/comparativa.csv` (modelo, RMSE/MAE/R² train/val, tiempo_s) y citar el híbrido congelado como "extra no visto en clase".

### Requirement: MLP base + 3 experimentos con hipótesis

La capacidad SHALL entrenar `MLPRegressor` base + E1 capacidad / E2 regularización-lr / E3 batch-early, cada uno con hipótesis escrita ANTES del resultado en `notebooks/03_modelos_B.ipynb`.

### Requirement: Métricas, elección por negocio y SHAP

La capacidad SHALL reportar MAE/RMSE/R² en train/val + gráfico real-vs-predicho en test (1 sola vez, modelo elegido), explicar qué significan para la empresa (coste hangar vs inspección), elegir por métrica de negocio (no por RMSE ciego, desempate al más simple) y mostrar qué variables pesan más con SHAP calculado con validación —nunca con test— sobre el modelo elegido (200 filas), en `resultados/shap_*.png/csv` (rúbrica v5, SAA-9 10 pts). La permutación solo vale como lectura complementaria, no como sustituto para el 10.

#### Scenario: SHAP sobre validación
- GIVEN el modelo elegido
- WHEN se calculan las atribuciones SHAP
- THEN se usan filas de validación, nunca de test
- AND se publica el top-k de variables en `resultados/shap_*.png/csv`

### Requirement: README de clase, app fina y respuesta individual

El README SHALL traer los 6 apartados obligatorios (título+frase, captura app arriba, negocio con dato+objetivo+quién+€, esquema Mermaid + IA débil/supervisado con comparación razonada con una IA fuerte, datos+hallazgo+figs, resultados con tabla pandas+tiempos+elección+test+real-vs-predicho), apartados propios además de los 6 obligatorios, y captura MLflow en `resultados/`. `app/streamlit_app.py` SHALL mostrar métricas de test con matriz de confusión —o gráfico real-vs-predicho en regresión— y predecir 1 caso nuevo con la decisión de las reglas (`src/reglas.py`); SHALL mostrar la `p`/valor predicho del caso nuevo junto a la decisión de las reglas. Cada alumno SHALL entregar un artefacto individual de respuesta (documento o presentación) defendiendo su parte (SAA-10, PIA-6, MIA-4); los guiones de `docs/defensa/` son apoyo, no el artefacto.

### Requirement: MLflow tracking de modelos y experimentos

Todos los modelos y experimentos SHALL registrarse en MLflow con hiperparámetros y métricas (train/val/tiempo), con capturas en `resultados/`; `mlflow` SHALL estar en `requirements.txt`. `src/clase/train_*.py` SHALL importar `mlflow` y usar su tracking para registrar cada entrenamiento.

### Requirement: n8n por webhook según decisión (MIA-3)

`src/n8n.py` SHALL enviar la decisión por webhook a `n8n/flujo.json` y el flujo SHALL tener una rama por decisión con una acción distinta a las vistas en clase según la decisión (Sheets/Postgres/Calendar/correo). `n8n/flujo.json` SHALL contener el flujo real, no un placeholder.

### Requirement: Ventaneo honesto de la base adaptada (NB04)

La capacidad SHALL mapear el parquet MAR-imputado a W/Xs/y/units/cycles, re-imputar con medianas SOLO de fit-units `[2,5,10,18,20]` y ventanear con `fit_preprocessing`/`build_windows` sin cambios (93 features, sin `fase_vuelo`; holdout 16 y test `[11,14,15]` intactos). La LGBM cuantil 0.35 resultante SHALL compararse con el B-histórico en las mismas ventanas y SHALL llevar columna `grano=ventana` (prohibido el ranking mixto con el E1-fila 7.70).

#### Scenario: Sin fuga del holdout en la re-imputación
- GIVEN la base adaptada
- WHEN se calculan las medianas de respaldo
- THEN solo intervienen fit-units
- AND ninguna estadística de 16/11/14/15 entra en el preprocesado

### Requirement: Bundle C versionado con puerta de adopción (NB05, pendiente)

El ensemble reentrenado SHALL vivir en `src/clase/models/` con manifest y banda propios (nunca en `models/`), seed 42 primero (7/123 solo si queda cerca de 4.25). La adopción (re-freeze caché + banda + reglas + ADR) SHALL exigir `RMSE_C ≤ 4.25 − spread` Y `NASA_C ≤ NASA_B` en las mismas 6.196 ventanas; si no se cumple, C SHALL quedar como experimento y B SHALL seguir en producción. SIN re-freeze en este change.

## MODIFIED

None (capacidad nueva; las 4 desplegadas quedan intactas).

## REMOVED

None.

## Related capabilities

Cita (no modifica) `rul-prediction-ds02` (híbrido como extra y como producción), `ds02-rules-engine` (re-export en `src/reglas.py`), `ds02-dss-ui`/`ds02-live-evaluation` (validadores reutilizados).
