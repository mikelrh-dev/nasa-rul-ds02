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
3. **Paso del tiempo $\rightarrow$ APROBADO (basado en la caché, no en el modelo):**
   * *Cómo funciona sin inventar datos:* el botón **«Avanzar 10 ciclos de flota»** sube el reloj compartido. `app/simulacion.py` **nunca llama al modelo**: lee las ventanas ya puntuadas de la caché (`app/cache/ds02_windows.parquet`) y deja quieta la unidad que ya cruzó el umbral. La cabecera de ese módulo lo declara y da la razón: re-puntuar no reproduciría la caché, porque el EMA causal arranca en frío en una ventana aislada y porque la caché se construyó a `step=2` y la puntuación en vivo a `step=1`.
4. **Diagnóstico por sensores $\rightarrow$ PARCIAL:** los residuos Ridge existen y el modelo los consume (`src/ds02_rul/residualizer.py`, aplicado en `src/ds02_rul/ensemble.py:202`). La app **no los muestra**: su «Radiografía de sensores» dibuja una deriva porcentual contra los primeros cinco ciclos (`app/dashboard_ds02.py:265`), que es una señal honesta pero no la que usa el modelo. Mostrar el residuo real es la mejora de mayor impacto pendiente; está fuera del plan de la defensa por ahora.

---

## 3. Arquitectura Funcional del Gemelo Digital MRO (Core ML + Streamlit)

El objetivo inmediato es consolidar una experiencia de usuario (*Task-First UX*) impecable, dividida en tres vistas conectadas por un estado persistente (`app/flota.py`, `app/hangar.py`, `app/simulacion.py`).

### A. Máquina de estados de los motores en el hangar

Cinco estados, definidos en `app/hangar.py:18-22`, con las transiciones en
`app/hangar.py:27-33`. El ciclo de vida **no llama al modelo**: es bookkeeping
operativo, y el gemelo es lo que el modelo dijo (ver `app/twin.py`).

```
EN_SERVICIO ──> INSPECCION_PROGRAMADA ──> AOG_DERIVADO ──> EN_TALLER ──> PRUEBA_EN_BANCO
```

Transiciones permitidas:

- `EN_SERVICIO` → `INSPECCION_PROGRAMADA` o `AOG_DERIVADO`
- `INSPECCION_PROGRAMADA` → `AOG_DERIVADO` o `EN_SERVICIO`
- `AOG_DERIVADO` → `EN_TALLER`
- `EN_TALLER` → `PRUEBA_EN_BANCO`
- `PRUEBA_EN_BANCO` → `EN_SERVICIO` o `AOG_DERIVADO`

* **Qué abre un registro:** una unidad entra al hangar cuando el operario pulsa
  **«Abrir registro»**, y el estado lo dicta la decisión del motor
  (`AOG_DERIVADO` si $L_{inf} < \text{umbral de hangar}$,
  `INSPECCION_PROGRAMADA` en cualquier otro caso). La decisión de entrada queda
  **congelada con los umbrales del momento**: mover el slider después no reescribe
  la historia. `hangar.revision` contrasta lo congelado con lo que diría la
  política de hoy, y la tabla del hangar lo publica como «coincide» o como el
  estado que tomaría ahora.
* **Qué no hay:** la app **no bloquea la selección** de un motor retenido. El
  motor retenido deja de avanzar con el reloj (`S.retenidos`, que se pinta en el
  caption «No vuelan: …»), pero se puede seguir inspeccionando. Prometer bloqueo
  sería prometer una función que no existe.
* **Asincronía de flota:** el reloj es un solo valor compartido (`cycle`), pero
  cada unidad se evalúa contra su propia vida registrada, así que en el mismo ciclo
  pueden verse unidades en fases distintas. La vida registrada es finita: U11
  llega a 59 ciclos, U14 a 74 y U15 a 66. Pasado ese punto, `fleet_snapshot` la
  reporta con el último ciclo puntuado, no extrapolada.

### B. Estructura de las 3 pestañas en Streamlit (`app/dashboard_ds02.py`)

Los nombres reales están en `app/dashboard_ds02.py:930-932`.

#### 1. Pestaña «Flota · qué pasa hoy»
* **Control del reloj (`app/simulacion.py`):** Botón **«Avanzar 10 ciclos de
  flota»**. Sube el reloj compartido; los motores que no cruzaron el umbral
  avanzan con él y los que ya cruzaron se quedan donde están. No llama al modelo:
  lee la caché ya puntuada.
* **Muro del hangar:** Una tarjeta por motor, con la sparkline de su
  $L_{inf}$. El color y el estado los dicta $L_{inf}$:
  * 🟢 **Apto para vuelo** ($L_{inf}$ holgado).
  * 🟡 **Inspección programada** ($L_{inf}$ acercándose al umbral).
  * 🔴 **AOG_DERIVADO** ($L_{inf}$ por debajo del umbral).
  Un motor retenido deja de avanzar, pero **no queda bloqueado**: se puede seguir
  inspeccionando.
* **Gestión del operario:** Para mover un motor por el ciclo de vida hay que abrir
  su registro (**«Abrir registro»**, en «Hangar · ciclo de vida») y luego pulsar
  **«Registrar movimiento»** con el destino permitido. No existen los botones
  «Ingresar en Taller» ni «Certificar Reparación».

#### 2. Pestaña «Motor · qué le pasa a este»
* **Métricas de Cabecera con Jerarquía Clara:**
  * **Límite Inferior Conformal ($L_{inf}$):** Destacado como el indicador que **decide el estado**.
  * **RUL p35 (Conservadora):** Predicción puntual asimétrica.
  * **Límite Superior ($L_{sup}$):** Techo de la banda al 90%.
  * **Trazabilidad:** Ciclos evaluados, número de ventanas puntuadas (mínimo 50 muestras para 1 ventana válida) y huella criptográfica `SHA-256` de la tabla de entrada.
* **Curva de Degradación y Banda de Incertidumbre:** Gráfico interactivo con la evolución histórica del RUL predicho, la sombra de la banda conformal al 90% y la línea horizontal roja del umbral de parada.
* **Explicabilidad Física:** **Radiografía de sensores**: la deriva porcentual de
  las presiones (`P15`, `P2`, `P21`, `P24`, `Ps30`, `P40`, `P50`) y las
  temperaturas (`T2`, `T24`, `T30`, `T48`, `T50`) respecto a la línea base sana de
  los primeros cinco ciclos del propio motor. Es una deriva de referencia, no los
  residuos Ridge que consume el modelo: esa diferencia está en
  `docs/plans/plan-accion-gemelo-hangar-2026-10-24.md`, fuera de plan por ahora.
* **Lo que no hay:** no existe una calculadora de despacho de misión. El número
  que sí existe es «Ciclos hasta el umbral de hangar», en la pestaña de flota,
  calculado sobre la caché.

#### 3. Pestaña «Evidencia · cómo se calculó»
* **Trazabilidad del artefacto:** versiones de TensorFlow, Keras, sklearn y
  LightGBM, huella SHA-256 del artefacto y contrato de inferencia (ventana 50,
  `beta` 1,0, `ema_span` 5).
* **Paridad con el manifiesto:** el RMSE recalculado de la caché se publica junto
  al registrado en `models/ds02_manifest.json`, con la diferencia. No se ajusta
  ninguna de las dos columnas.
* **Sandbox de estrés termodinámico:** un deslizador, **«Deriva térmica acumulada
  en T48»** (0-30 %). Con 0 % el tramo es la caché tal cual; con cualquier otro
  valor la intervención es sintética y la banda pierde la garantía conformal. La
  leyenda lo declara y la app no lo oculta.
* **Carga de CSV externo:** en «Evaluar unidad nueva» se puntúa una tabla que
  aportas tú. No existe *jittering* automático: el ruido va en tu CSV.

---

## 4. El Guion de Defensa en Directo (El Loop de 4 Minutos)

Guion corregido contra lo que la app hace de verdad. Cada afirmación de esta
sección se verificó ejecutando el código; el detalle está en
`docs/plans/plan-accion-gemelo-hangar-2026-10-24.md`. Los nombres de estado son
los de `app/hangar.py`: `EN_SERVICIO`, `INSPECCION_PROGRAMADA`, `AOG_DERIVADO`,
`EN_TALLER`, `PRUEBA_EN_BANCO`.

1. **Minuto 1 (El criterio de seguridad):** Abres la pestaña **«Flota · qué pasa
   hoy»** y bajas al **Muro del hangar**. Explicas que en aviación no se decide
   con la media, sino con el cuantil 0.35 y el límite inferior de la banda
   conformal ($L_{inf}$). Pulsas el archetype **«Recién salido de revisión
   (U15)»**: deja la app en la Unidad 15, ciclo 2, con $L_{inf} = 35.8$ ciclos,
   sana. El número sale de la caché: el comando está en
   `docs/informes/informe-2026-10-24-anticipacion-al-fallo.md`.
2. **Minuto 2 (El paso del tiempo):** Pulsas **«Avanzar 10 ciclos de flota»**.
   El reloj compartido sube y los motores que no cruzaron el umbral avanzan con
   él; el que ya cruzó se queda donde está en vez de extrapolarle. Eso es
   `S.retenidos`, y se pinta en el caption «No vuelan: …». La Unidad 14 entra en
   zona crítica y su tarjeta pasa a **AOG_DERIVADO**. Ojo: la app no bloquea la
   selección; el motor retenido deja de avanzar. Decir «lo bloquea» sería
   prometer una función que no existe.
3. **Minuto 3 (La prueba ciega y la física):** Entras al detalle del motor.
   Dices: *"Esta es una unidad de validación ciega; el modelo jamás vio estos
   datos al entrenarse"*. Muestras la **Radiografía de sensores**: la deriva de
   las presiones frente a la línea base sana del propio motor. Acto seguido, como
   operario, abres **«Hangar · ciclo de vida»**, pulsas **«Abrir registro»** y
   luego **«Registrar movimiento»** para llevarlo a **EN_TALLER**. No existe un
   botón «Certificar Reparación».
4. **Minuto 4 (El golpe de gracia en el Sandbox):** Si un miembro del jurado duda
   de si los datos estaban en caché, abres el **Sandbox de estrés** y subes el
   deslizador **«Deriva térmica acumulada en T48»**: la banda pierde la garantía
   conformal y la leyenda lo declara. Alternativamente, cargas un CSV propio en
   **«Evaluar unidad nueva»**. No existe jittering automático: el ruido lo
   aportas tú en el CSV.

---

## 5. Plan de Implementación Escalonado (revisado contra el código)

El plan original de esta sección proponía cosas que la app ya tiene o que no
conviene construir. Esta es la versión verificada.

### Ya hecho (verificado)

* [x] **Máquina de estados.** `app/hangar.py` con cinco estados, transiciones
      validadas (`permitidas`; `avanzar` rechaza las ilegales con el mensaje de
      qué destinos sí se permiten) y decisión de entrada congelada con sus
      umbrales. Cubierto por `tests/test_hangar.py`.
* [x] **Avance de ciclos.** `app/simulacion.py`: `retenidos`, `avanzar`,
      `ciclos_hasta_fallo` y `reiniciar_vida`, sin llamar al modelo. Cubierto por
      `tests/test_simulacion.py`.
* [x] **Batería de tests.** 200 tests en verde.

### Pendiente, y por qué

* [ ] **Paso 1.1 original** («estados `operativo`, `pendiente_revision`,
      `parada_inmediata`, `en_reparacion`»): esos nombres no existen en el código
      y no hay motivo para cambiarlos. Los reales están en `app/hangar.py:18-22`.
      **Descartado.**
* [ ] **Paso 1.2 original** (desfases de ciclo por unidad): el reloj es
      compartido y `fleet_snapshot` ya hace clamping por unidad. Dar un offset por
      unidad rompe esa invariante y obliga a tocar el muro, la cronología y el
      comparador a la vez. **Descartado** salvo necesidad real.
* [ ] **Paso 1.3 (pulido visual):** pendiente de verdad. La lista concreta está en
      `docs/plans/plan-accion-gemelo-hangar-2026-10-24.md`, fase 0.
* [ ] **Paso 2.1 (disparador de eventos AOG):** es un sistema de eventos nuevo.
      Riesgo medio. No entra en el plan de la defensa.
* [ ] **Paso 2.2 (voz + Telegram):** **descartado.** Necesita red y un token en
      el repo, y falla en directo si el aula no tiene internet. No avanza la tesis.