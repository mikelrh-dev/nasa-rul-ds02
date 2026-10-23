# Informe de Auditoría: UX, Conexión Modelo-Streamlit, Misconceptions y Riesgos Potenciales (`nasa-rul-ds02`)

> **INSTRUCCIÓN ESTRICTA PARA EL AGENTE REVISOR (PRIMERA PASADA - SOLO LECTURA):**
> **NO MODIFIQUES NINGÚN ARCHIVO.** Tu único objetivo en esta primera pasada es actuar como **Auditor Verificador**. Debes recorrer el código fuente del repositorio siguiendo los **Patrones de Exploración** provistos en cada sección, contrastar las hipótesis de este informe contra la implementación real y emitir un reporte de estado clasificando cada punto como:
> - `[CONFIRMADO]`: El riesgo, bug o problema de UX existe tal como se describe (citar archivo y líneas exactas).
> - `[PARCIAL / MITIGADO]`: El código contempla el caso pero de forma incompleta o solo en una parte del flujo (ej. mitigado en caché pero vulnerable en inferencia en vivo).
> - `[REFUTADO / YA RESUELTO]`: El código ya implementa una defensa robusta contra este punto (citar dónde se resuelve).

---

## 0. Mapa de Superficie a Auditar

El agente debe centrar su inspección estática en los siguientes módulos del repositorio:

1. **Capa UI / Streamlit (`app/`):**
   - `app/dashboard_ds02.py` y `app/dashboard.py` (Puntos de entrada y layout global)
   - `app/ui_inference.py` (Puente entre la interfaz y el pipeline de predicción)
   - `app/ui_data_loader.py` (Ingesta de datos, lectura de Parquet y validación de CSVs)
   - `app/twin.py` (Gemelo digital / Sandbox de estrés interactivo)
   - `app/hangar.py` (Vista de flota / selección de unidades)
   - `app/ui_alta.py` y `app/ui_batch.py` (Alta de nuevos motores y procesamiento por lotes)
   - `app/ui_rules.py` (Integración visual de la capa de reglas de negocio)
   - `app/cache/cache_manifest.json`, `ds02_rows.parquet`, `ds02_windows.parquet`
2. **Capa Core ML (`src/ds02_rul/`):**
   - `inference.py`, `pipeline.py`, `persistence.py`, `residualizer.py`, `features.py`, `pooling.py`, `stacking.py`, `smoothing.py`, `conformal.py`
3. **Capa Motor de Reglas / Dominio (`mia/`):**
   - `mia/modelo.py`, `mia/motor.py`, `mia/reglas.py`, `mia/casos.py`, `mia/calibracion_banda.json`
4. **Artefactos y Manifiestos (`models/` y raíz):**
   - `models/ds02_manifest.json`, `models/alarm_policy.json`, `models/psi_reference.json`, `models/ablation_meta_cycle.json`
   - Binarios: `/ensemble.joblib`, `/scaler.joblib` vs `models/ensemble.joblib`, `models/scaler.joblib`, `models/v3_bundle.joblib`, `models/bilstm_ds02.keras`

---

## 1. Auditoría de la Conexión Modelo $\leftrightarrow$ Streamlit

### 1.1. Gestión de Caché de Recursos Pesados vs. Datos (`@st.cache_resource` vs `@st.cache_data`)
* **Hipótesis de Riesgo:** En Streamlit, cada interacción de usuario dispara un *rerun* completo. Si la carga de `bilstm_ds02.keras`, `v3_bundle.joblib` o `ensemble.joblib` no está decorada con `@st.cache_resource`, o si se pasan objetos mutables/modelos dentro de funciones con `@st.cache_data` sin prefijo `_`, se producirán fugas de memoria (TensorFlow graph retracing) o penalizaciones graves de latencia.
* **Patrón de Exploración para el Agente:**
  - Buscar decoradores de caché y cargas de modelos en `app/` y `mia/`:
    ```bash
    rg -n "cache_resource|cache_data|load_model|joblib\.load|pickle\.load" app/ mia/ src/
    ```
  - Verificar en `app/ui_inference.py`, `app/ui_data_loader.py` y `mia/modelo.py` si `load_model` de Keras o el cargador de `src/ds02_rul/persistence.py` se invoca fuera de un bloque cacheado por sesión/proceso.
* **Criterio de Verificación:** Confirmar que los modelos tengan exactamente una instancia en memoria compartida y que los DataFrames Parquet (`ds02_rows.parquet`, `ds02_windows.parquet`) no se re-lean del disco en cada cambio de pestaña o slider.

### 1.2. Paridad entre Pipeline de Entrenamiento/Caché e Inferencia en Vivo (`twin.py`, `ui_batch.py`, `ui_alta.py`)
* **Hipótesis de Riesgo (Train-Serve Skew):** El pipeline oficial de DS02 consta de varios pasos secuenciales muy específicos documentados en los ADRs:
  1. Residualización de sensores sobre condiciones operativas (`residualizer.py` - ADR-002).
  2. Escalado Ajustado solo en Train (`scaler.joblib`).
  3. Construcción de ventanas temporales + extracción de features / triple pooling (`features.py`, `pooling.py`) + `cyc_norm` (o su exclusión en el meta-modelo según `ablation_meta_cycle.json`).
  4. Predicción base: LightGBM cuantil ($\tau = 0.35$, ADR-003/007) + BiLSTM (`bilstm_ds02.keras`).
  5. Meta-learner de Stacking Híbrido (`stacking.py` - ADR-001).
  6. Suavizado Causal EMA (`smoothing.py` - ADR-006).
  7. Banda de incertidumbre Conformal (`conformal.py` - ADR-008) y Regla Isotónica R2b (`mia/reglas.py` - ADR-009).
  * **El fallo potencial:** Cuando el usuario usa el Gemelo Digital (`app/twin.py`) o sube un lote (`app/ui_batch.py`), `app/ui_inference.py` podría estar saltándose la residualización por régimen operativo, aplicando mal el escalador (ej. sobre valores crudos en vez de residualizados o viceversa), o ejecutando el suavizado EMA sobre una ventana aislada de 1 solo paso temporal (donde el EMA causal pierde su inercia histórica).
* **Patrón de Exploración para el Agente:**
  - Rastrear el flujo exacto desde `app/twin.py` y `app/ui_batch.py` hacia `app/ui_inference.py` y `src/ds02_rul/inference.py`:
    ```bash
    rg -n "residual|scaler|transform|ema|smooth|conformal|predict" app/ src/ds02_rul/ mia/
    ```
  - Comparar la función que genera `app/cache/ds02_windows.parquet` en `scripts/build_ui_cache.py` contra la función de inferencia en vivo llamada desde `app/twin.py` y `app/ui_batch.py`.
* **Criterio de Verificación:** ¿Producen exactamente el mismo número (hasta precisión de punto flotante `1e-5`) una unidad evaluada desde la caché precalculada (`ds02_windows.parquet`) y esa misma unidad pasada sin perturbaciones por la función de inferencia en vivo de `ui_inference.py`?

### 1.3. Desambiguación de Artefactos Duplicados y Rutas Relativas
* **Hipótesis de Riesgo:** Existen archivos homónimos en la raíz del proyecto (`/ensemble.joblib`, `/scaler.joblib`) y en el directorio `/models/` (`models/ensemble.joblib`, `models/scaler.joblib`, `models/v3_bundle.joblib`), además de `models/legacy/`. Si distintos módulos (`mia/modelo.py` vs `src/ds02_rul/persistence.py` vs `app/ui_inference.py`) resuelven rutas relativas dependiendo del `cwd` desde donde se lance `streamlit run`, pueden cargar versiones distintas del modelo o fallar según el directorio de trabajo.
* **Patrón de Exploración para el Agente:**
  - Buscar todas las referencias a archivos `.joblib`, `.keras`, `.json` y `.parquet`:
    ```bash
    rg -n "\.(joblib|keras|json|parquet|npz|npy)" app/ src/ mia/ scripts/
    ```
  - Comprobar hashes SHA256 o tamaños entre `/ensemble.joblib` y `models/ensemble.joblib`, y entre `/scaler.joblib` y `models/scaler.joblib`.
  - Revisar `models/ds02_manifest.json` y `app/cache/cache_manifest.json` para verificar si se validan los checksums al iniciar la app.

### 1.4. Latencia de Inferencia Keras en Interacciones de UI (`twin.py`)
* **Hipótesis de Riesgo:** `model.predict()` de Keras tiene un sobrecoste fijo por llamada (~100-300 ms) pensado para lotes grandes. En `app/twin.py`, si al mover un slider de estrés se invoca `model.predict()` para una sola ventana (o peor, en un bucle fila por fila para reconstruir la curva EMA del motor), la interfaz sufrirá congelamientos notables.
* **Patrón de Exploración para el Agente:**
  - Inspeccionar cómo se invoca el modelo Keras en `src/ds02_rul/model.py`, `src/ds02_rul/inference.py` y `app/ui_inference.py`:
    ```bash
    rg -n "\.predict\(" app/ src/ mia/
    ```
  - Verificar si existe algún bucle `for` en `app/twin.py` o `app/ui_inference.py` que llame a la inferencia ventana por ventana en lugar de vectorizar el tensor 3D `(N_windows, W, N_features)`.

---

## 2. Misconceptions de Uso y Trampas Cognitivas (UX / Dominio)

### 2.1. Misconception 1: Perturbación Estática vs. Ventana Temporal + EMA Causal en el Gemelo Digital (`app/twin.py`)
* **Descripción del Problema:** El usuario de un "Gemelo Digital" o "Sandbox de Estrés" suele pensar que al mover el slider de un sensor (ej. subir la temperatura de salida de turbina) está evaluando "¿qué pasa si en este ciclo el sensor marca $X$?". Sin embargo:
  1. El modelo consume una **ventana deslizante** de longitud $W$ (donde el BiLSTM aplica *triple pooling*: media, desviación estándar, último valor, etc.).
  2. La salida final pasa por un **filtro EMA causal** ($\hat{y}_t = \alpha y_t + (1-\alpha)\hat{y}_{t-1}$) y potencialmente por el ajuste isotónico/monótono (`ADR-006`, `ADR-009`).
* **Trampa de Uso:**
  - Si la perturbación de `twin.py` solo modifica el último ciclo $t$ de la ventana, las estadísticas agregadas de la ventana (media, pendiente, std) apenas cambian y el suavizado EMA amortigua el cambio, haciendo parecer que el modelo es "insensible" a fallos graves.
  - Por el contrario, si la perturbación aplica un *offset* plano a toda la ventana histórica o a toda la vida del motor, la desviación estándar intra-ventana y la derivada temporal no cambian (solo cambia la media), lo cual no simula una degradación progresiva real sino un sesgo de calibración del sensor.
* **Patrón de Exploración para el Agente:**
  - Analizar en `app/twin.py` y `tests/test_twin.py` cómo se aplican exactamente los deltas/sliders de los sensores sobre el tensor de entrada o DataFrame de la ventana, y si el EMA causal se recalcula sobre la trayectoria o se omite.
  - Revisar `docs/plans/estado-sandbox-estres-2026-10-23.md` y `docs/informes/informe-2026-10-23-fallos-y-usabilidad-app.md` para contrastar el comportamiento esperado frente al actual.

### 2.2. Misconception 2: Violación Física por Perturbación Univariante (Colinealidad y OOD)
* **Descripción del Problema:** En un motor turbofán N-CMAPSS DS02, las variables termodinámicas están fuertemente acopladas por las leyes de conservación de masa y energía (un deterioro en HPT o HPC altera simultáneamente temperaturas `T30`/`T48`/`T50`, presiones `P30` y velocidades `Nc`/`Nf`).
* **Trampa de Uso:** Si la UI permite mover un único sensor a valores extremos manteniendo los demás constantes (o si el usuario introduce valores manuales en `ui_alta.py`), se genera un punto **Out-of-Distribution (OOD)** que viola la física del motor. En regiones OOD, LightGBM y la capa de stacking pueden presentar respuestas no monótonas (por ejemplo, predecir que el RUL *aumenta* al incrementar una temperatura crítica).
* **Patrón de Exploración para el Agente:**
  - Verificar en `app/twin.py`, `app/ui_alta.py` y `app/ui_inference.py` si se utiliza `models/psi_reference.json` o alguna métrica de distancia/rango para advertir al usuario cuando su configuración manual de sensores rompe la correlación física o sale del soporte de entrenamiento.
  - Comprobar si existen *presets* de degradación física acoplada (modos de fallo) o solo sliders independientes por sensor.

### 2.3. Misconception 3: Interpretación del RUL Cuantil ($\tau = 0.35$) y la Banda Conformal como "Esperanza Matemática"
* **Descripción del Problema:** Según `ADR-003`, `ADR-007` y `ADR-008`, el sistema no predice la media condicional $\mathbb{E}[\text{RUL}|X]$ ni la mediana ($P_{50}$), sino que emplea una función de pérdida asimétrica orientada al cuantil $\tau = 0.35$ para proteger el *NASA Score*, combinada con un límite inferior conformal (`conformal.py`, `calibracion_banda.json`) para el triaje de alarmas (`alarm_policy.json`).
* **Trampa de Uso:** Un operador o auditor externo que compare la predicción puntual mostrada en la UI contra el `RUL_real` observará un sesgo sistemático hacia abajo (subestimación intencional) y puede diagnosticar erróneamente que el modelo "está mal calibrado o subestima siempre", o no entender qué métrica exacta (predicción puntual EMA vs. límite inferior conformal) está disparando el estado de alarma o las reglas de `mia/reglas.py`.
* **Patrón de Exploración para el Agente:**
  - Revisar los textos, métricas (`st.metric`), tooltips (`help=...`) y leyendas de gráficos en `app/dashboard_ds02.py`, `app/hangar.py`, `app/twin.py` y `app/ui_rules.py`:
    ```bash
    rg -n "st\.metric|RUL|conformal|cuantil|0\.35|banda|alarma|umbral" app/
    ```
  - Verificar en `docs/informes/informe-2026-10-21-alarma-y-confusion.md` y `app/ui_rules.py` si existe ambigüedad visual entre la alarma por umbral conformal y las reglas heurísticas/isotónicas (como `R2b` descrita en `ADR-009`).

### 2.4. Misconception 4: El Rol de la Edad Cronológica (`cycle` / `cyc_norm`) en Motores Subidos por el Usuario (`ui_batch.py` / `ui_alta.py`)
* **Descripción del Problema:** Históricamente documentado en `docs/informes/informe-2026-10-20-meta-cycle-fix.md` y `docs/informes/informe-2026-10-21-p0-p1-prior-de-vida.md`, el uso de la edad del motor (`cycle` o `cyc_norm`) tiene dos riesgos graves de interpretación y de fuga de datos:
  1. **Fuga de fin de vida en Test/Batch:** Si `cyc_norm` se calcula como `cycle / max(cycle_del_motor_actual)`, al subir un archivo CSV truncado en `ui_batch.py` (ej. un motor sano inspeccionado en el ciclo 120), `cyc_norm` valdrá $1.0$ en el ciclo 120, haciéndole creer al modelo que el motor está al $100\%$ de su vida útil solo porque ahí termina el CSV.
  2. **Dominancia del Prior de Edad:** Si `cyc_norm` se normaliza por una constante fija de entrenamiento, un usuario que pruebe en `ui_alta.py` o `twin.py` los mismos valores de sensores en el ciclo 50 vs. el ciclo 250 verá predicciones distintas y debe comprender cuánto peso tiene la edad cronológica frente al estado real de los sensores.
* **Patrón de Exploración para el Agente:**
  - Inspeccionar cómo se calcula `cyc_norm` (o cualquier feature derivada de `cycle`) en `src/ds02_rul/features.py`, `app/ui_data_loader.py` y `app/ui_inference.py`:
    ```bash
    rg -n "cyc_norm|cycle" src/ds02_rul/ app/ mia/
    ```
  - Verificar con extrema atención si algún cálculo agrupa por unidad y divide por `.max()` del propio DataFrame de entrada en inferencia.

### 2.5. Misconception 5: Regla `R2b` (Ajuste Isotónico Offline vs. Regla Causal en Tiempo Real)
* **Descripción del Problema:** El documento `ADR-009-r2b-is-an-isotonic-fit-not-a-monotonicity-rule.md` y `docs/informes/auditoria-2026-10-21-reglas.md` advierten sobre la naturaleza de la regla `R2b`. Una regresión isotónica ajustada sobre toda la curva de un motor utiliza información futura de la serie para forzar monotonía decreciente (no es estrictamente causal si se recalcula sobre toda la ventana completa mirando hacia adelante), o si se aplica en la UI, el usuario puede confundir un *post-procesado de suavizado monótono* con una regla de decisión de mantenimiento.
* **Patrón de Exploración para el Agente:**
  - Revisar `mia/reglas.py`, `app/ui_rules.py` y `tests/test_ui_rules.py` para verificar cómo se ejecuta y cómo se explica `R2b` (y el resto de reglas del motor MIA) en la interfaz de Streamlit.

---

## 3. Errores Potenciales en Tiempo de Ejecución (Edge Cases y Bugs Técnicos)

### 3.1. Motores con Historial Corto ($N_{\text{ciclos}} < W$) en `ui_alta.py` y `ui_batch.py`
* **Descripción del Error Potencial:** La red BiLSTM requiere secuencias de longitud fija $W$ (ej. $W=30$ o $W=50$). Si un usuario da de alta un motor en `ui_alta.py` con una sola lectura puntual o sube en `ui_batch.py` un motor con menos de $W$ ciclos registrados:
  - Si no hay *left-padding* (replicando el primer ciclo o rellenando con ceros) explícito y documentado, el generador de ventanas devolverá 0 ventanas para esa unidad (`shape=(0, W, F)`), provocando un `ValueError` o `IndexError` en Keras/LightGBM, o descartando silenciosamente el motor del informe batch sin avisar al usuario.
  - Si sí hace *padding* silencioso en `ui_alta.py` (ej. repetir 30 veces una única fila introducida en un formulario), las features de ventana como `std` o `slope` valdrán exactamente $0.0$, alterando artificialmente la predicción de LightGBM y BiLSTM.
* **Patrón de Exploración para el Agente:**
  - Inspeccionar `app/ui_alta.py`, `app/ui_batch.py`, `app/ui_data_loader.py` y `src/ds02_rul/data.py`:
    ```bash
    rg -n "window|pad|len\(|shape" app/ui_alta.py app/ui_batch.py app/ui_data_loader.py src/ds02_rul/
    ```
  - Revisar `tests/test_ui_alta.py` y `tests/test_ui_batch.py` para ver qué longitud mínima de ciclos exigen o cómo sintetizan la ventana.

### 3.2. Contaminación Cruzada de `st.session_state` al Cambiar de Motor o Pestaña
* **Descripción del Error Potencial:** En aplicaciones multipágina o con pestañas (`Hangar` $\rightarrow$ `Gemelo Digital` $\rightarrow$ `Reglas` $\rightarrow$ `Batch`), es habitual guardar en `st.session_state` los valores de los sliders de perturbación, la unidad seleccionada o el resultado de la última inferencia.
  - **Bug clásico:** El usuario selecciona el "Motor 14", aplica una perturbación de estrés en `twin.py`, y luego cambia el selector global al "Motor 11". Si las claves (`key=...`) de los sliders de sensores no están vinculadas al ID de la unidad o no se resetean mediante un callback `on_change` al cambiar de motor, el "Motor 11" heredará silenciosamente los offsets o valores absolutos de los sensores del "Motor 14".
* **Patrón de Exploración para el Agente:**
  - Buscar todos los accesos y mutaciones a `session_state` y el uso de `key=` y `on_change=` en `app/`:
    ```bash
    rg -n "session_state|on_change|key=" app/
    ```
  - Verificar en `tests/test_dss_interaction.py` y `tests/test_ux_round3.py` si este flujo de cambio de unidad está cubierto.

### 3.3. Desorden Temporal, Ciclos Duplicados o Huecos (`gaps`) en CSVs de Usuario (`ui_data_loader.py` / `ui_batch.py`)
* **Descripción del Error Potencial:** Al cargar un archivo externo en `ui_batch.py`:
  1. Si el CSV no viene ordenado por `(unit, cycle)` de forma estrictamente ascendente y el cargador no fuerza `.sort_values(["unit", "cycle"])`, las ventanas temporales y el EMA causal mezclarán el futuro con el pasado.
  2. Si existen ciclos duplicados para una misma unidad o valores `NaN`/`inf` en algún sensor o condición operativa, el `residualizer` o la red neuronal propagarán `NaN` a toda la predicción subsiguiente debido a la recurrencia del filtro EMA ($\hat{y}_t = \alpha \cdot \text{NaN} + (1-\alpha)\hat{y}_{t-1} = \text{NaN}$).
* **Patrón de Exploración para el Agente:**
  - Inspeccionar las validaciones de esquema y limpieza en `app/ui_data_loader.py` y `app/ui_batch.py`:
    ```bash
    rg -n "sort_values|isna|isnull|dropna|duplicated|inf" app/ src/ds02_rul/
    ```

### 3.4. Fragilidad en el Desacoplamiento `app/api.py` vs. Llamada Directa en Streamlit
* **Descripción del Error Potencial:** El repositorio incluye `app/api.py` (además de los módulos `app/ui_*.py`). A menudo existe una divergencia entre lo que expone la API (ej. FastAPI/Flask o interfaz programática) y lo que ejecuta directamente el dashboard de Streamlit (`dashboard_ds02.py`), quedando uno de los dos caminos desactualizado respecto a las últimas correcciones de auditoría (`2026-10-21-ds02-audit-fixes`).
* **Patrón de Exploración para el Agente:**
  - Inspeccionar `app/api.py`, `app/dashboard.py` y `app/dashboard_ds02.py` para determinar cuál es el *entrypoint* activo (verificando también `Dockerfile` y `docker-compose.yml`) y si existen módulos huérfanos o desincronizados:
    ```bash
    rg -n "dashboard|api" Dockerfile docker-compose.yml pyproject.toml app/
    ```

---

## 4. Protocolo de Ejecución para el Agente (Checklist de Primera Pasada)

El agente que revise este documento debe ejecutar los siguientes pasos **sin alterar ningún archivo del repositorio**:

1. **Fase 1 - Lectura de Documentación Reciente del Proyecto:**
   - Leer `docs/informes/informe-2026-10-23-fallos-y-usabilidad-app.md`, `docs/plans/estado-sandbox-estres-2026-10-23.md`, `docs/plans/spec-pulido-demo-ds02.md` y `docs/informes/auditoria-2026-10-21-reglas.md` para conocer qué problemas ya fueron detectados previamente por el equipo.
2. **Fase 2 - Inspección del Código de `app/`, `mia/` y `src/ds02_rul/`:**
   - Leer íntegramente `app/dashboard_ds02.py`, `app/ui_inference.py`, `app/ui_data_loader.py`, `app/twin.py`, `app/hangar.py`, `app/ui_alta.py`, `app/ui_batch.py` y `app/ui_rules.py`.
   - Cruzar las llamadas con `src/ds02_rul/inference.py`, `src/ds02_rul/pipeline.py` y `mia/modelo.py`.
3. **Fase 3 - Ejecución de Tests Existentes (Solo lectura/diagnóstico):**
   - Ejecutar `pytest` en modo consulta para comprobar el estado base de la suite (`tests/test_dss_ui.py`, `tests/test_dss_interaction.py`, `tests/test_twin.py`, `tests/test_ui_alta.py`, `tests/test_ui_batch.py`, `tests/test_ui_rules.py`, `tests/test_ux_round3.py`).
4. **Fase 4 - Emisión del Informe de Verificación:**
   - Responder con una tabla resumen que evalúe los puntos **1.1 a 1.4**, **2.1 a 2.5** y **3.1 a 3.4**, indicando:
     - **Estado** (`[CONFIRMADO]`, `[PARCIAL / MITIGADO]`, `[REFUTADO / YA RESUELTO]`).
     - **Evidencia en Código** (`archivo.py:línea` y breve extracto).
     - **Severidad Real** (`Crítica`, `Alta`, `Media`, `Baja`).
     - **Propuesta de Acción** (sin implementarla aún) para la segunda pasada.

---

## 5. Resultado de la verificación (2026-10-23, solo lectura, sin modificar código)

> Leyenda: `[CONFIRMADO]` el riesgo existe tal como se describe · `[PARCIAL / MITIGADO]` contemplado solo en parte · `[REFUTADO / YA RESUELTO]` el código ya lo neutraliza. Severidad: Crítica / Alta / Media / Baja.

### 1.1. Caché de recursos pesados vs. datos — `[REFUTADO / YA RESUELTO]` (Baja)

- El bundle se carga una sola vez por proceso: `app/ui_inference.py:330-337` (`@st.cache_resource` sobre `get_ensemble` → `load_ensemble(ARTIFACT)`); `mia/modelo.py:35-45` singleton perezoso de módulo (`_cargar`); `app/api.py:27-31` carga única en `lifespan`.
- Los Parquet van por `@st.cache_data`: `app/ui_data_loader.py:109,118,127,133` (`get_windows`, `get_rows`, `get_provenance`, `get_manifest`) y `app/ui_inference.py:155` (`observed_envelope`). Los DataFrames no se re-leen por rerun.
- Ningún objeto modelo entra en funciones con `@st.cache_data`: la ruta batch recibe el ensemble ya cargado como parámetro (`app/ui_batch.py:93-100`, docstring "para no recargar el artefacto una vez por motor").
- Acción: ninguna. Opcional: verificar SHA del bundle al cargarlo (ver 1.3).

### 1.2. Paridad caché-entrenamiento vs inferencia en vivo — `[PARCIAL / MITIGADO]` (Media)

- Mismo pipeline, imposible el skew manual: tanto `scripts/build_ui_cache.py:98-104` como `app/ui_inference.py:score_table` llaman a `raw_windows` + `ensemble.predict_interval`; escalado, residualización, `cyc_norm`, EMA y conformal viven **dentro** del bundle (`src/ds02_rul/ensemble.py:101-179`, `_tabular:193-223` deshace el escalado y aplica `residualizer.transform`). Nadie reimplementa el preproceso en `app/`.
- Diferencias reales que rompen la paridad bit a bit: (a) la caché se construyó con `step=2` (`build_ui_cache.py:87-100`) y el vivo puntúa con `step=1` (`ui_inference.py:388-396`); (b) el EMA es causal sobre la serie puntuada (`smoothing.py:causal_ema_by_unit`), así que el tramo del sandbox (frío en `c_inicio`, `dashboard_ds02.py:638-676`) no reproduce los valores de la caché completa aunque la deriva sea 0 % — a 0 % el sandbox evita el problema **no repuntuando** (lee la caché).
- Acción: documentar que caché (step 2) y vivo (step 1) difieren en densidad; si se necesita igualdad 1e-5, puntuar con `step=2` y con historia previa para el EMA.

### 1.3. Artefactos duplicados y rutas relativas — `[PARCIAL / MITIGADO]` (Media-Baja)

- `/ensemble.joblib` y `models/ensemble.joblib` son el **mismo bytes** (SHA-256 `0acd795b…e6d502` en ambos; igual para `scaler.joblib`, `027b0f8f…114b02`). No hay divergencia de versiones hoy.
- Todo el código activo apunta a `models/`: `ui_inference.py:23` (absoluto vía `ROOT`), `mia/modelo.py:21` (absoluto vía `RAIZ`), `api.py:23`, `dashboard.py:26`, `build_ui_cache.py:42`.
- Huecos: (a) los hashes se **registran pero no se verifican** al arrancar (`cache_manifest.json: "ensemble_sha256"` coincide con el medido, pero nada lo comprueba); (b) `api.py`/`dashboard.py` usan ruta relativa `models/...` (depende de `cwd`; en Docker funciona por `WORKDIR /app`); (c) `persistence.py:20` trae por defecto `ENSEMBLE_FILE = "ensemble.joblib"` relativo — ningún llamador lo usa sin argumento, pero invita al error.
- Acción: validar SHA contra el manifiesto en `get_ensemble`; ignorar o eliminar las copias de raíz para que nadie las cargue por defecto.

### 1.4. Latencia Keras en interacciones — `[REFUTADO / YA RESUELTO]` (Baja)

- Una sola llamada `model.predict` por interacción sobre el tensor completo `(N, ventana, 19)`: `ensemble.py:137` dentro de `predict`, que a su vez es llamado una vez por `predict_interval`; el sandbox puntúa el tramo entero en un único `score_table` (`dashboard_ds02.py:660`). Sin bucles fila a fila en `app/`.
- El grafo queda en memoria vía `@st.cache_resource`; a deriva 0 % ni siquiera se carga (rama de caché, `dashboard_ds02.py:638-652`).
- Matiz: `app/api.py:106-115` puntúa ventana individual por request (paga el overhead fijo por llamada, correcto para una API).
- Acción: ninguna.

### 2.1. Perturbación estática vs ventana + EMA — `[REFUTADO]` el fallo descrito; `[PARCIAL]` efecto borde (Media)

- El sandbox NO perturba un solo ciclo: rampa progresiva `0→deriva` sobre todo el tramo (`dashboard_ds02.py:655-656` `T48 *= 1+deriva·linspace(0,1,N)`) y re-puntuación de **todas** las ventanas + EMA causal por unidad (`ensemble.py:158`, `units` constante por tramo en `ui_inference.py:388-396`, sin mezcla entre motores). La hipótesis de sliders en `twin.py` está desactualizada: `twin.py` hoy es solo almacén de gemelos, sin sliders.
- Efecto borde real: el EMA arranca en frío en `c_inicio` del tramo, sin la historia previa del motor.
- Acción: burn-in del EMA o nota en el caption del tramo. El aviso conformal degradado ya existe (`dashboard:745-751`).

### 2.2. Violación física univariante / OOD — `[PARCIAL / MITIGADO]` (Alta)

- Mitigado a nivel univariante: `ui_inference.py:156-224` (`observed_envelope` ±5 % + `plausibility_warnings`, aviso de ciclo único plano); el sandbox los pinta (`dashboard_ds02.py:745-751`).
- No mitigado a nivel multivariante: cero usos de `psi_reference` en `app/ mia/ src/`; sin presets de degradación acoplada; único control = slider de T48 (`dashboard:610-614`). Una combinación termodinámicamente imposible pero canal-por-canal "en rango" no avisa, y LightGBM/stacking pueden responder no-monótonos en OOD.
- Acción: presets de fallo acoplado o distancia multivariante como warning no bloqueante; etiquetar el slider como intervención sintética univariante.

### 2.3. RUL cuantil τ=0.35 leído como esperanza — `[PARCIAL / MITIGADO]` (Media)

- Decisión por `L_inf` explícita y consistente: `dashboard:1101`, help en `1143`, `ui_rules.py:96-130` decide sobre `lower`, `mia/motor.py` R9/R8/R7 sobre `limite_inferior`; `ui_rules.py:37-65` conserva `pred_enviada/lower_enviada` para no esconder la lectura cruda. El sesgo conservador se explica en auditoría (`dashboard:2009-2037`).
- Pero en el punto de uso la métrica dice "RUL predicha" (`dashboard:729-731`) sin etiqueta τ=0.35; "cuantílico" aparece una sola vez (`dashboard:542`), lejos del badge.
- Acción: rotular "RUL p35 (conservadora)" + `help=` de una línea junto al badge.

### 2.4. `cycle`/`cyc_norm` en altas y lotes — `[REFUTADO]` la fuga; `[PARCIAL]` la dominancia del prior (Media)

- Fuga por máx-local refutada: `features.py:133` y `ensemble.py:147` usan `cycle/100.0` absoluto (constante 100), sin `groupby.max()` en inferencia; `inference.py:raw_windows` no renormaliza por el largo del CSV. Un CSV truncado en ciclo 120 da `cyc_norm=1.2`, nunca `1.0` falso. El batch usa el mismo `INF.score_table` que el individual (`ui_batch.py:100,145`).
- Dominancia del prior existe por diseño (el meta incluye `cycles/100` si `n_meta>=3`, `ensemble:143-147`; medida en `scripts/build_02_notebook.py:555+`) pero la UI no muestra cuánto pesa edad vs sensores.
- Acción: nota en `ui_alta`/plantilla CSV ("`cycle` es edad absoluta, no fracción del archivo"); opcional, mostrar sensibilidad edad-vs-sensores.

### 2.5. R2b isotónica offline vs causal — `[REFUTADO / YA RESUELTO]` (Baja)

- Causal y documentado: `mia/reglas.py:52-75` (`pava_causal_no_creciente`, "depende solo de ≤t", "la secuencia devuelta NO es estrictamente no creciente"), `efecto_R2b:135-139` extremo del prefijo; `app/ui_rules.py:5-18,59-63` ordena por `(cycle, start_index)` por unidad y cita la secc. 13 del informe de reglas. R6 recalibra la banda sobre el punto corregido (`ui_rules:64-65`).
- Acción: ninguna de lógica; mantener el rótulo completo "ajuste isotónico causal (no monotonía estricta)" donde se muestre R2b.

### 3.1. Historial corto (N < W) — `[REFUTADO / YA RESUELTO]` (Baja)

- Rechazo explícito antes del modelo, sin padding silencioso: `ui_inference.py:271-277` exige ≥50 muestras (mensaje con conteos), `preflight` lo replica sin cargar el modelo; `ui_batch.validar_bloque` reutiliza `preflight` (`ui_batch.py:77-91`). Tests que lo fijan: `test_ui_batch.py:87-93`, `test_live_eval.py:61-64`.
- La vía `ui_alta` no puntúa nada nuevo: recorta ventanas ya puntuadas de la caché (`ui_alta.py:35-55` `ventanas_de_alta`), así que un alta con 1 lectura ni llega al modelo. Grep de `pad` en `app/` vacío.
- Acción: ninguna.

### 3.2. Contaminación de `session_state` entre motores — `[PARCIAL / MITIGADO]` (Baja)

- La clase de bug descrita no puede darse por construcción: no hay offsets por sensor guardados; la única perturbación es `%` global (`sbx_deriva`) aplicada a la unidad seleccionada en el render; los umbrales se leen de `session_state` dentro del fragment (`dashboard_ds02.py:600-603`), los twins/hangar van claveados por id (`twin.registrar` + `normalizar_id`).
- Sin test de "cambiar de unidad con deriva activa" (`test_dss_interaction.py` / `test_ux_round3.py` no cubren el sandbox); el patrón de acciones pendientes (`_demo/_alta/_escenario/_umbrales_pendientes`, `dashboard:301-339`) es correcto pero frágil ante futuras claves globales.
- Acción: añadir un test de cambio de unidad con deriva ≠ 0; prefijar futuras claves de perturbación por unidad si aparecen sliders por sensor.

### 3.3. CSVs desordenados, duplicados, NaN/inf — `[PARCIAL / MITIGADO]` (Media)

- Cubierto: no-numérico y NaN rechazados (`ui_inference.py:279-300`, `to_numeric(coerce)→isna`, con pista de coma decimal europea), `cycle` decreciente rechazado (`302-309`), tablas cortas rechazadas (3.1), orden de canales exigido (`264-269`), columnas extrañas rechazadas (`258-263`). Gaps entre ciclos aceptados por diseño (filas remuestreadas, el EMA opera sobre lo disponible).
- Huecos reales: (a) `inf` **pasa** la validación (`isna()` no caza `±inf`) y propagaría al residualizador/red/EMA; (b) duplicados exactos no se detectan (`duplicated` ausente en `app/`); (c) el vivo no reordena (solo rechaza decrementos) mientras `build_ui_cache.py:120` sí ordena — un CSV no-decreciente pero desordenado entre unidades queda en orden de llegada.
- Acción: rechazar `±inf` en `validate_table` (una línea con `np.isinf`); decidir política de duplicados exactos.

### 3.4. Desacople `api.py` vs Streamlit — `[CONFIRMADO]` (Alta para la demo, Media para la API)

- `docker-compose.yml` (servicio `dashboard`) arranca `streamlit run app/dashboard.py`, el tablero legacy que **falla al renderizar** (`ValueError: cannot reindex on an axis with duplicate labels`, `dashboard.py:100`, verificado por render headless el 2026-10-23). El flujo vigente es `dashboard_ds02.py` (cache, sin HDF5 de 2,3 GB; `dashboard.py:37-42` exige el HDF5).
- `app/api.py:82-119` puntúa desde el HDF5 crudo con `step=2`, devuelve solo punto (`ensemble.predict`, sin banda conformal ni reglas `mia/`): puede responder distinto número que la UI (`step=1` + intervalo + R2b/R6 + pasada A) para la misma unidad.
- Acción: apuntar compose a `dashboard_ds02.py`; documentar la API como "punto sin banda ni reglas" o alinearla al contrato `score_table`+`decidir_ventanas`.