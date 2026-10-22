# Especificación de Desarrollo: Centro de Control y Mantenimiento Predictivo en Streamlit (NASA N-CMAPSS DS02)

## 1. Contexto y Objetivo para el Agente
El repositorio actual ya cuenta con un sistema de Machine Learning híbrido (BiLSTM + LightGBM cuantílico + Meta-aprendiz Ridge/Stacking) completamente entrenado, validado y empaquetado para el dataset **NASA N-CMAPSS DS02**, además de una versión básica en `app/dashboard.py` (basada en FD001).

**Objetivo:** Desarrollar o actualizar la interfaz gráfica en Streamlit (`app/dashboard_ds02.py` o evolucionando `app/dashboard.py`) para convertirla en un **Sistema de Soporte a la Decisión (DSS) y Derivación a Hangar** enfocado en **DS02**, pensado para una defensa/presentación académica e industrial en vivo.

### 🚨 REGLA DE ORO (Restricción Estricta)
* **PROHIBIDO modificar, reentrenar o alterar la lógica algorítmica** en `src/ds02_rul/` ni sobreescribir los artefactos en `models/`.
* La aplicación debe ser **100% de lectura e inferencia/visualización**, consumiendo los artefactos congelados ya existentes.

---

## 2. Inventario de Artefactos y Módulos a Consumir
El agente debe basar toda la carga de datos y predicciones en los siguientes recursos existentes en el repositorio:

1. **Artefactos de Evaluación y Resultados (Carga rápida para UI):**
   * `models/test_eval_ultima_ventana.csv`: Contiene el resumen de la última ventana de evaluación por motor.
   * `models/ds02_manifest.json`: Manifiesto con las métricas globales y por unidad (RMSE global `4.315`, MAE `<25` de `1.126`, desglose de Motores 11, 14 y 15), hiperparámetros y configuración conformal.
   * `models/alarm_policy.json`: Política de alarmas y umbrales operativos.
   * `models/ablation_meta_cycle.json`: Datos de ablación y comparativa del meta-modelo.
2. **Modelos y Pipeline de Inferencia (Solo lectura via `@st.cache_resource`):**
   * Librería interna: `src/ds02_rul/persistence.py`, `src/ds02_rul/inference.py`, `src/ds02_rul/conformal.py`.
   * Pesos: `models/bilstm_ds02.keras`, `models/ensemble.joblib`, `models/scaler.joblib`.

---

## 3. Arquitectura de la Interfaz de Usuario (UI/UX)

La aplicación debe configurarse en modo panorámico (`st.set_page_config(layout="wide")`) y estructurarse en una **Barra Lateral de Simulación** y **4 Pestañas Principales**.

### Barra Lateral (Sidebar): Controles de Guardia Operativa
* **Selector de Unidad (Test Set DS02):** Desplegable para filtrar o inspeccionar en detalle los motores de prueba:
  * `Motor 15` (Etiqueta UI: *"Unidad 15 - Degradación Nominal / Alta Precisión"*).
  * `Motor 11` (Etiqueta UI: *"Unidad 11 - Degradación Estándar"*).
  * `Motor 14` (Etiqueta UI: *"Unidad 14 - Caso Atípico / Régimen Compuesto"*).
* **Simulador de Ciclo de Vuelo (Slider temporal):** Un control deslizable (`Ciclo actual: 1 a N`) que permita "viajar en el tiempo" a lo largo de la vida del motor seleccionado para ver en vivo cómo cae la RUL, cómo se estrecha la banda conformal y en qué ciclo exacto salta la alarma de envío al hangar.
* **Configuración de Umbral de Hangar:** Slider numérico (por defecto `25` ciclos, alineado con el tramo crítico de evaluación de la NASA) que define cuándo un avión pasa a estado *AOG (Aircraft on Ground / En Hangar)*.

---

### Pestaña 1: 🏭 Hangar Virtual y Estado de Flota (Vista Ejecutiva)
**Propósito:** Simular la pantalla de un Jefe de Mantenimiento que necesita saber en 5 segundos qué aviones pueden volar hoy y cuáles se bloquean automáticamente.

* **Fila Superior de KPIs (`st.metric`):**
  1. `Flota Monitorizada (Test DS02)`: 3 Unidades activas (6.196 ventanas evaluadas).
  2. `Precisión en Zona Crítica (RUL < 25)`: Mostrar el MAE oficial del manifiesto (`1.13 ciclos`).
  3. `Unidades en Hangar (Inmovilizadas)`: Conteo dinámico según el ciclo simulado.
* **Regla de Negocio Automatizada (El "Hangar"):**
  * La decisión **NO** se toma solo con la predicción puntual ($\hat{y}$), sino con el **Límite Inferior de la Banda Conformal** ($L_{\text{inf}}$) para garantizar seguridad aeroespacial:
    * 🟢 **APTO PARA VUELO:** $L_{\text{inf}} \ge 50$ ciclos.
    * 🟡 **INSPECCIÓN PROGRAMADA:** $25 \le L_{\text{inf}} < 50$ ciclos.
    * 🔴 **DERIVACIÓN AUTOMÁTICA A HANGAR (BLOQUEADO):** $L_{\text{inf}} < 25$ ciclos.
* **Tabla Interactiva de Cola de Mantenimiento:**
  * Mostrar una tabla estilizada con Pandas `Styler` (colores semafóricos) con las columnas: `ID Motor`, `Ciclo Actual`, `RUL Real (Ground Truth)`, `RUL Predicha`, `Límite Conformal Inferior (Riesgo)`, `Estado Operativo` y `Acción Automática Asignada` (ej. *"Orden de desmontaje HPT/LPT enviada a taller"*).

---

### Pestaña 2: 📈 Telemetría RUL y Bandas Conformales (Inspección en Tiempo Real)
**Propósito:** Mostrar visualmente la potencia del ensamble híbrido y la cuantificación de incertidumbre sobre la unidad seleccionada en el Sidebar.

* **Gráfico Principal Interactivo (Plotly):**
  * Eje X: `Ciclo de Vuelo` (hasta el ciclo seleccionado en el slider, o vista completa con una línea vertical marcando el ciclo actual).
  * Eje Y: `RUL (Ciclos restantes)`.
  * Trazas a dibujar:
    1. **RUL Real** (línea punteada gris/verde).
    2. **Predicción del Ensamble** (línea sólida azul fuerte).
    3. **Banda de Incertidumbre Conformal** (`fill='tonexty'` sombreado suave entre el límite inferior y superior conformal asimétrico).
    4. **Zona de Entrada a Hangar:** Franja horizontal sombreada en rojo tenue por debajo de `Y = 25` ciclos.
* **Tarjetas de Desempeño de la Unidad:**
  * Mostrar debajo del gráfico el RMSE, MAE y Sesgo específicos de ese motor en el conjunto de prueba (extraídos de `ds02_manifest.json`).

---

### Pestaña 3: 🔍 Radiografía Física de Sensores y Condiciones Operativas
**Propósito:** Dar explicabilidad física al modelo demostrando que no es una "caja negra", sino que lee presiones, temperaturas y velocidades de rotor reales tras limpiar el ruido de vuelo.

* **Diccionario Semántico en la UI:**
  * El agente debe mapear los nombres técnicos de las columnas del dataset a etiquetas comprensibles en el selector de gráficas (ej. mostrar temperaturas de turbina HPT/LPT, presiones totales como `s7`, velocidades de giro del fan y núcleo, y condiciones de vuelo como Altitud, Mach y TRA).
* **Visualización Dual (2 columnas):**
  * **Gráfico A (Condiciones Operativas):** Evolución de Altitud / Mach / Acelerador en las ventanas del motor.
  * **Gráfico B (Deriva de Sensores Residualizados):** Evolución de los sensores seleccionados donde se aprecie claramente cómo la tendencia térmica o de presión se dispara a medida que el motor se acerca al fallo ($RUL < 25$).

---

### Pestaña 4: ⚠️ Auditoría de Ingeniería: El Caso "Motor 14" y Honestidad Diagnóstica
**Propósito:** Transformar la debilidad estadística del Motor 14 en el punto más fuerte de la presentación académica, demostrando madurez analítica.

* **Comparativa Visual de Error por Unidad:**
  * Gráfico de barras (Plotly) comparando el RMSE y MAE de los tres motores de test:
    * `Motor 15`: RMSE `2.88` (Excelente)
    * `Motor 11`: RMSE `3.72` (Muy bueno)
    * `Motor 14`: RMSE `8.04` (Outlier / Anomalía)
* **Gráfico de Precisión por Tramos de Vida (MAE por RUL Bin):**
  * Mostrar los datos del manifiesto: cómo en vida alta `[50, 75)` el MAE es `5.35`, en `[25, 50)` es `4.17`, pero en el tramo crítico **`[0, 25)` cae a `1.12` ciclos**.
* **Panel Explicativo Estructurado (Cajas de información técnicas):**
  * Incluir tres tarjetas visuales explicando las causas raíz descubiertas en los informes del repositorio (`docs/informes/informe-2026-10-21-p0-p1-prior-de-vida.md`):
    1. **Complejidad Física:** Modo de fallo compuesto (degradación simultánea más agresiva).
    2. **Densidad de Muestreo (Hallazgo P0):** Menor cantidad de observaciones por ciclo de vuelo (~20 filas/ciclo frente a >110 en entrenamiento).
    3. **Sesgo del Prior de Vida y Mitigación Conformal:** Cómo la menor duración total del motor (75 ciclos) engaña al prior medio, y cómo el uso del **límite conformal inferior** en el Hangar Virtual actúa como red de seguridad para absorber este desfase.

---

## 4. Plan de Ejecución Paso a Paso para el Agente

1. **Fase 1 - Capa de Datos para la UI (`app/ui_data_loader.py`):**
   * Crear funciones cacheadas (`@st.cache_data` y `@st.cache_resource`) que lean `models/ds02_manifest.json`, `models/alarm_policy.json` y las predicciones por ventana de los motores 11, 14 y 15 (cargando los arrays precalculados en `scripts/` o ejecutando una pasada limpia de inferencia con `src/ds02_rul/inference.py` si los datos de test están disponibles localmente; en caso de no estar el `.h5` pesado de la NASA en la máquina de presentación, **generar/exportar un archivo ligero `.parquet` o `.csv` en `models/ds02_ui_telemetry_cache.csv`** con las curvas de los motores 11, 14 y 15 para que la app cargue de forma instantánea en clase sin depender de gigabytes de RAM).
2. **Fase 2 - Construcción de la Interfaz (`app/dashboard_ds02.py`):**
   * Implementar el layout con las 4 pestañas descritas, gráficos en `plotly.graph_objects` con tema oscuro o corporativo limpio, y la lógica de derivación automática al hangar.
3. **Fase 3 - Generador de Orden de Trabajo (Cierre del Caso de Uso):**
   * Añadir un botón `📥 Descargar Orden de Mantenimiento (JSON/CSV)` en la Pestaña 1 para los motores que estén en estado rojo, generando un reporte listo para entregar a los mecánicos.
4. **Fase 4 - Verificación:**
   * Comprobar que la aplicación arranca sin errores con `streamlit run app/dashboard_ds02.py` y que ningún test existente en `pytest` se ha roto.