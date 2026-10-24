# Informe de Auditoría, Arquitectura y Hoja de Ruta: Gemelo Digital MRO (NASA N-CMAPSS DS02-006)

**Proyecto:** Sistema de Soporte a la Decisión (DSS) y Gemelo Digital de Hangar para Predicción de RUL en Turbofanes  
**Arquitectura ML:** Stacking Híbrido (BiLSTM Triple Pooling + LightGBM Cuantil 0.35) + Bandas Conformales Asimétricas (90%)  
**Principio Rector:** *Protocolo Honesto* — Cero datos inventados, cero *data leakage*, trazabilidad criptográfica (SHA-256) y decisiones gobernadas por aversión al riesgo ($L_{inf}$).

---

## 1. Auditoría de Integridad de Datos y Particionado (El Manifiesto Manda)

Tras auditar de forma cruzada el manifiesto congelado (`models/ds02_manifest.json`), el fichero fuente `N-CMAPSS_DS02-006.h5` y el código del pipeline (`src/ds02_rul/pipeline.py`), se establece la única verdad operativa sobre las 9 unidades existentes en el dataset:

| Partición | Unidades (Motores) | Rol en el Pipeline | Estado de Contaminación (*Leakage*) | Uso Permitido en la Defensa / Demo |
| :--- | :--- | :--- | :--- | :--- |
| **Fit (Train)** | `2, 5, 10, 18, 20` | Ajuste de pesos de BiLSTM, árboles de LightGBM, escaladores y regresores Ridge. | **100% Visto** (Datos de aprendizaje directo). | Prohibido para evaluar rendimiento. Solo válido como referencia de distribución base. |
| **Holdout (Selección)** | `16` (7.653 filas) | Elección de hiperparámetros ($\beta$), calibración del meta-modelo y de la banda conformal. | **Contaminación de 2º Orden** (Sesgo optimista por selección). | Chequeo técnico secundario (*sanity check*) con asterisco explícito. **Nunca como métrica titular.** |
| **Test (Evaluación)** | `11, 14, 15` | Evaluación final congelada. | **0% Visto en aprendizaje** (Ciego para los pesos del modelo). | **Evidencia Nº 1 (Validación Ciega).** Base del backtest de anticipación al fallo (13, 23 y 18 ciclos). |

### Regla de Oro para el Tribunal
* **No existen motores "libres" ocultos en DS02-006** (las unidades 12 y 13 no forman parte de este archivo).
* Los motores **11, 14 y 15** no deben denominarse coloquialmente *"datos de test"*, sino **"Unidades de Validación Ciega apartadas del entrenamiento"**. La red neuronal jamás ajustó un solo parámetro con ellos.
* Para pruebas *Out-of-Distribution* (OOD) puras en directo sin violar las leyes de la termodinámica, se utiliza el **Sandbox de Estrés** (perturbación controlada sobre sensores reales como $T48$) o la inyección de ventanas con *Jittering Operativo* ($\pm 0.5\%$ de ruido blanco gaussiano sobre telemetría real).

---

## 2. Evaluación de Viabilidad y Descarte de "Humo" (Decisiones de Diseño)

Para mantener una credibilidad académica e industrial inatacable, se han filtrado las propuestas bajo el criterio estricto de **no inventar variables que no existan en la física del dataset ni en el pipeline entrenado**:

1. **Mapa Geográfico GPS $\rightarrow$ DESCARTADO:**
   * *Motivo:* N-CMAPSS no contiene coordenadas de latitud ni longitud. Inventar rutas sobre un mapa destruye el rigor científico del proyecto.
   * *Sustituto Honesto:* **Envolvente de Vuelo Real (Flight Envelope)** usando exclusivamente las tres variables operativas reales del dataset: Altitud (`alt`), Número de Mach (`Mach`) y ángulo de palanca de empuje (`TRA`).
2. **KPIs Financieros en Euros $\rightarrow$ DESCARTADOS:**
   * *Motivo:* El dataset no incluye costes de taller, precios de combustible ni penalizaciones contractuales de aerolíneas. Mostrar ahorros en euros inventados expone al proyecto a críticas severas del tribunal.
   * *Sustituto Honesto:* **KPIs de Ingeniería de Fiabilidad y Seguridad Operativa**: Ciclos de anticipación antes del cruce crítico (*Lead Time* de 13, 23 y 18 ciclos), Cobertura Empírica de la Banda Conformal (90%), Macro-RMSE y anchura de incertidumbre ($\Delta \text{Banda} = L_{sup} - L_{inf}$).
3. **Simulación del Paso del Tiempo y Hangar $\rightarrow$ APROBADO (100% Basado en el Modelo):**
   * *Cómo funciona sin inventar datos:* El botón **"Avanzar Turno"** (`app/simulacion.py`) no genera números aleatorios; extrae secuencialmente las ventanas reales de los motores `11, 14, 15` desde `app/cache/ds02_windows.parquet` y `ds02_rows.parquet`, ejecutando la inferencia real del modelo híbrido ciclo a ciclo.
4. **Diagnóstico por Estaciones del Motor $\rightarrow$ APROBADO (100% Basado en el Modelo):**
   * *Cómo funciona sin inventar datos:* El modelo ya calcula en su preprocesamiento los **residuos Ridge** (diferencia entre el valor real del sensor y el valor esperado para esa altitud y Mach, según `ADR-002`). Mostrar qué sensores presentan mayor deriva residual explica físicamente por qué el modelo está reduciendo el RUL.

---

## 3. Arquitectura Funcional del Gemelo Digital MRO (Core ML + Streamlit)

El objetivo inmediato es consolidar una experiencia de usuario (*Task-First UX*) impecable, dividida en tres vistas conectadas por un estado persistente (`app/flota.py`, `app/hangar.py`, `app/simulacion.py`).

### A. Máquina de Estados de los Motores en el Hangar
Cada motor registrado en el sistema atraviesa un ciclo de vida determinista gobernado por la inferencia del modelo:

$$\text{EN VUELO (Operativo)} \xrightarrow{L_{inf} \le \text{Umbral}} \text{AOG (Parada Inmediata / Bloqueado)} \xrightarrow{\text{Acción Operario}} \text{EN REVISIÓN (Taller)} \xrightarrow{\text{Certificación}} \text{REPARADO (Alta)}$$

* **Regla de Bloqueo de Seguridad:** Cuando el **Límite Inferior ($L_{inf}$)** de la banda conformal cruza el umbral crítico de seguridad, el motor entra en estado `AOG`. La interfaz **bloquea su selección para nuevas misiones de vuelo** en la zona de pruebas hasta que el operario gestione su paso por el taller y certifique su reparación.
* **Asincronía de Flota:** Los motores precargados (ej. Unidades 11, 14 y 15) pueden encontrarse en fases distintas de su vida útil (uno recién revisado en el ciclo 6, otro a mitad de vida en el ciclo 45, y otro acercándose a la degradación crítica).

### B. Estructura de las 3 Pestañas en Streamlit (`app/dashboard_ds02.py`)

#### 1. Pestaña `Flota y Hangar` (Macrogestión y Simulación por Turnos)
* **Control de Turnos (`app/simulacion.py`):** Botón maestro **"Avanzar Turno (+N ciclos)"**. Al pulsarlo, todos los motores en estado `Operativo` avanzan en su línea temporal real dentro de la caché Parquet y actualizan su predicción.
* **Tarjetas Visuales de Bahías (Bays):** Visualización clara de qué motores están:
  * 🟢 **Aptos para volar** ($L_{inf}$ holgado).
  * 🟡 **Pendientes de revisión programada** ($L_{inf}$ acercándose al umbral).
  * 🔴 **Parada Inmediata / AOG** ($L_{inf}$ por debajo del umbral, bloqueados).
* **Panel de Gestión del Operario:** Botones de acción directa sobre cada motor en el hangar: *"Ingresar en Taller"* y *"Certificar Reparación / Overhaul"* (que desbloquea el motor y reinicia su contador operativo).

#### 2. Pestaña `Motor (Gemelo Digital)` (Inspección Profunda y Triage)
* **Métricas de Cabecera con Jerarquía Clara:**
  * **Límite Inferior Conformal ($L_{inf}$):** Destacado como el indicador que **decide el estado**.
  * **RUL p35 (Conservadora):** Predicción puntual asimétrica.
  * **Límite Superior ($L_{sup}$):** Techo de la banda al 90%.
  * **Trazabilidad:** Ciclos evaluados, número de ventanas puntuadas (mínimo 50 muestras para 1 ventana válida) y huella criptográfica `SHA-256` de la tabla de entrada.
* **Curva de Degradación y Banda de Incertidumbre:** Gráfico interactivo con la evolución histórica del RUL predicho, la sombra de la banda conformal al 90% y la línea horizontal roja del umbral de parada.
* **Explicabilidad Física (Sensores Residualizados):** Visualización de los sensores termodinámicos (`T24`, `T30`, `T48`, `T50`, `Ps30`, `Wf`, etc.) agrupados por sección del turbofán (Fan, LPC, HPC, HPT, LPT), destacando cuáles están empujando la predicción hacia el fallo.
* **Calculadora de Despacho de Misión:** Verificación rápida que responde a la pregunta: *¿Puede este motor asumir un próximo vuelo de $X$ ciclos según su tasa actual de degradación ($\Delta L_{inf} / \Delta \text{ciclo}$)?*

#### 3. Pestaña `Evidencia y Sandbox OOD` (Auditoría para el Tribunal)
* **Inspector de Ventana de Telemetría:** Tabla interactiva (como la vista del ciclo $1 \rightarrow 6$, 300 filas = 251 ventanas) donde se puede auditar fila a fila qué lecturas exactas (`alt`, `Mach`, `TRA`, temperaturas y presiones) están alimentando al modelo.
* **Sandbox de Estrés Termodinámico:** Deslizadores para inyectar anomalías físicas controladas en vivo (ej. simular un sobrecalentamiento progresivo en la turbina de alta presión $T48$) y demostrar ante el jurado que la red neuronal y la banda conformal reaccionan en tiempo real a la física, sin leer resultados precalculados.
* **Carga de CSV Externo (Sonda Inédita):** Subida de ficheros con *jittering* para certificar la robustez matemática fuera del archivo original.

---

## 4. El Guion de Defensa en Directo (El Loop de 4 Minutos)

Con esta estructura, tu demostración ante el jurado sigue una narrativa blindada:

1. **Minuto 1 (El Criterio de Seguridad):** Abres la vista de **Hangar**. Explicas que en aviación no se decide con la media, sino con el cuantil 0.35 y el límite inferior de la banda conformal ($L_{inf}$). Muestras tus 3 motores en distintas fases de ciclo (por ejemplo, la Unidad 15 en el ciclo 6 recién salida de revisión con $L_{inf} = 31.8$ ciclos, totalmente sana).
2. **Minuto 2 (El Paso del Tiempo y el Bloqueo):** Pulsas **"Avanzar Turno"**. El jurado ve cómo los ciclos avanzan con telemetría real. La Unidad 14 entra en zona crítica; el sistema la clasifica automáticamente en **Parada Inmediata (AOG)** y **bloquea su uso** en la zona de vuelo.
3. **Minuto 3 (La Prueba Ciega y la Física):** Entras al detalle del motor bloqueado. Dices: *"Esta es una unidad de validación ciega; el modelo jamás vio estos datos al entrenarse"*. Muestras cómo la caída del RUL coincide con la desviación física en los residuos de temperatura de la turbina ($T48$/$T30$). Acto seguido, como operario, pulsas **"Certificar Reparación"** para devolver el motor al servicio activo.
4. **Minuto 4 (El Golpe de Gracia en el Sandbox):** Si un miembro del jurado duda de si los datos estaban en caché, abres el **Sandbox**, invitas al profesor a alterar un sensor en directo o cargas tu CSV con ruido blanco, y demuestras cómo la inferencia recalcula instantáneamente el RUL y ensancha la banda de incertidumbre.

---

## 5. Plan de Implementación Escalonado (Prioridades)

### Fase 1: Cierre y Pulido del Core ML + Streamlit (FOCO ACTUAL)
* [ ] **Paso 1.1:** Verificar y blindar la máquina de estados en `app/hangar.py` y `app/flota.py` (estados `operativo`, `pendiente_revision`, `parada_inmediata`, `en_reparacion`) asegurando que un motor en `parada_inmediata` quede bloqueado para volar hasta que el operario lo repare manualmente.
* [ ] **Paso 1.2:** Conectar de extremo a extremo el avance de ciclos en `app/simulacion.py` con las 3 unidades de validación ciega (`11, 14, 15`) precargadas en caché con desfases de ciclo inicial distintos para aportar realismo asíncrono.
* [ ] **Paso 1.3:** Pulir la jerarquía visual de `app/dashboard_ds02.py` (tarjetas de estado en el hangar, claridad en la explicación de *Filas vs. Ventanas* y visualización de los residuos de sensores que justifican la caída del RUL).
* [ ] **Paso 1.4:** Pasar la batería completa de `pytest` (`test_flota.py`, `test_hangar.py`, `test_simulacion.py`, `test_dss_ui.py`) al 100% en verde.

### Fase 2: Automatización y Alertas Críticas (POST-CORE, cuando Fase 1 esté lista)
* [ ] **Paso 2.1:** Implementar el disparador de eventos cuando un motor transicione a `parada_inmediata` (AOG).
* [ ] **Paso 2.2:** Integrar síntesis de voz gratuita (`gTTS` / `edge-tts`) para reproducir un aviso sonoro de cabina en la propia interfaz de Streamlit y enviar en paralelo una **Nota de Voz de Emergencia + Ficha Técnica (con hash SHA-256)** al bot de **Telegram** del jefe de mantenimiento.