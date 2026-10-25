# Planificación DS02 · prioridad, riesgo y registro de fases

Origen: análisis del informe `docs/informe_estrat_gico_y_arquitectura_mro_ds02.md`
(elaborado por Gemini) y auditoría de sus afirmaciones contra el código real.

Estado del árbol cuando se escribió esto: `81187ef` en `origin/master`, 200 tests
en verde, el muro ya muestra los motores registrados.

Escala usada:

- **Impacto (0-10)**: cuánto mejora la defensa (lo que ve y cree el tribunal) más
  cuánto reduce el riesgo de contradecirte en directo.
- **Riesgo (0-10)**: probabilidad × coste de que rompa algo o falle en directo.
  Incluye el riesgo de contradecir tu propia tesis.

---

## CÓMO USAR ESTE FICHERO (leer antes de tocar nada)

Este documento es la única lista de prioridades del proyecto. Un agente que
cualquier sesión lo lea tiene que hacer tres cosas, en este orden:

1. **Verificar, no confiar.** Las cifras de este plan salieron de ejecutar el
   código. Lo que un agente encuentre distinto, se corrige aquí y se dice por
   qué. Un plan que nadie verifica es un plan que miente.
2. **Completar el registro de fase.** Cada fase tiene una tabla de estado. Al
   terminar una fase, el agente la rellena con: fecha, commit, y la prueba
   ejecutada que la respalda. Nunca se marca una fase sin prueba ejecutada.
3. **Dejar rastro del "no".** Si una propuesta se descarta, se anota en la fase
   con el motivo. Las cosas que no se hacen son parte del proyecto: el informe
   de Gemini propone seis funciones que no existen y hay que saber por qué no.

Regla que no se negocia: **un agente no puede marcar una fase como hecha sin
salida de terminal que lo pruebe.** "Lo he leído y parece bien" no es evidencia.

---

## A · EFECTO WOW (lo que el tribunal recuerda)

| # | Propuesta | Impacto | Riesgo | Fase |
| :--- | :--- | :--- | :--- | :--- |
| A1 | Residuos Ridge reales (`SensorResidualizer`) | 9 | 4 | Aplazada |
| A2 | Documentar los 13/23/18 de anticipación | 8 | 2 | Fase 1 |
| A3 | Calculadora de despacho de misión | 7 | 8 | Fase 4 |
| A4 | Jittering OOD (±0,5 % de ruido) | 7 | 7 | Fase 4 |
| A5 | Voz de cabina + bot de Telegram | 5 | 10 | Fase 5 |
| A6 | Bloquear unidades retenidas | 4 | 6 | Fase 5 |

**A1 · Residuos Ridge reales.** Enseña la razón física por la que el modelo baja
el RUL. Responde al ataque "¿y si está mirando al piloto?". Es el único "wow"
honesto de la lista: no es teatro, es la explicación física real.

**Verificado el 24 de octubre de 2026.** Calculado sobre la caché (12 538 filas ×
14 sensores) y **acompaña la caída del RUL**: el residuo de T48 correlaciona
−0,88 / −0,82 / −0,87 con la RUL real en U11 / U14 / U15, y va de −0,61 σ
(ciclo 11, RUL 65) a +3,19 σ (ciclo 76, RUL 0) en U14. La presión del fan (P2)
no correlaciona (−0,04 en U14), lo que es la prueba de que el panel no miente:
se ve qué sensor manda y cuál no.

Coste medido: caché de 1,9 a 3,6 MB (×1,88); medio día de trabajo. Riesgo 4: el
modelo no se toca, pero el eje va en σ y el builder de la caché necesita el
artefacto. **Aplazada hasta después de la defensa** por timing, no por peligro:
añade una señal nueva que explicar en directo. Detalle completo en
`plan-accion-gemelo-hangar-2026-10-24.md`, Fase 3.

Hallazgo que lo sostiene: el modelo consume `SensorResidualizer`
(`src/ds02_rul/residualizer.py`, usado en `src/ds02_rul/ensemble.py:202`), que
resta de cada uno de los 14 sensores una regresión Ridge (alpha=1,0) sobre una
base polinómica de grado 2 de las condiciones de vuelo (`alt`, `Mach`, `TRA`,
`T2`). La app **no lo usa**: su "Radiografía de sensores"
(`app/dashboard_ds02.py:265`) calcula `(valor / media de los 5 primeros ciclos -
1) * 100`, una deriva de referencia, no el residuo del modelo. El informe de
Gemini lo promete (apartado 2, punto 4) y no existe.

**A2 · Los 13/23/18.** Verificados ejecutando `L.first_alarm_cycle`: U11 alarma
en 22 y verdad en 35 (13), U14 29 → 52 (23), U15 25 → 43 (18). Hoy solo existen
en el informe de Gemini. Declararlos como "alarma menos verdad", nunca como
backtest: un backtest implica un protocolo que no hay.

**A5 · Voz + Telegram.** Es el peor cociente de la lista (5/10). No avanza la
tesis, añade dependencias que no están en `requirements.txt`, necesita un token
en el repo y mete una llamada de red en el minuto en que el tribunal mira.

---

## B · COHERENCIA (evita que te contradigan)

| # | Propuesta | Impacto | Riesgo | Fase |
| :--- | :--- | :--- | :--- | :--- |
| B1 | Reescribir el guion contra lo que hay | 8 | 1 | Fase 1 |
| B2 | Corregir el 31,8 del guion | 6 | 1 | Fase 1 |
| B3 | Alinear el vocabulario de estados | 5 | 1 | Fase 1 |
| B4 | Inspector de ventana de telemetría | 6 | 5 | Fase 3 |
| B5 | Renombrar "Avanzar Turno" | 4 | 2 | Fase 1 |

**B1.** El informe de Gemini promete seis funciones que no existen en el código:

| Lo que promete el informe | Realidad verificada |
| :--- | :--- |
| Máquina de estados `operativo`, `pendiente_revision`, `parada_inmediata`, `en_reparacion` | `app/hangar.py:18-22`: `EN_SERVICIO`, `INSPECCION_PROGRAMADA`, `AOG_DERIVADO`, `EN_TALLER`, `PRUEBA_EN_BANCO`. Ninguno de los nombres del informe existe. |
| Botón "Avanzar Turno (+N ciclos)" | `app/dashboard_ds02.py:1134`: "Avanzar 10 ciclos de flota". No avanza motores: mueve el reloj compartido. `S.avanzar()` existe pero solo lo llaman los tests. |
| Calculadora de Despacho de Misión | No existe. |
| "La interfaz bloquea su selección para nuevas misiones" | No existe bloqueo. `S.retenidos()` detecta retenidos y los pinta en un caption. |
| "Jittering operativo (±0,5 % de ruido blanco gaussiano)" | No existe. No hay una línea de jittering en `app/` ni en `src/`. |
| Inspector de Ventana de Telemetría | No existe. El 300/251 sale de `DEMO_ROWS=300` en `app/ui_inference.py:160`, que es el largo del tramo de demo. |
| `L_inf = 31,8` para U15 en ciclo 6 | No reproducible: `lower` (media) = 31,93 y `lower_min` = 31,30. Y el preset de U15 es el ciclo 2, donde vale 35,76. |
| Nombres de pestaña "Flota y Hangar", "Motor (Gemelo Digital)", "Evidencia y Sandbox OOD" | `app/dashboard_ds02.py:930-932`: "Flota · qué pasa hoy", "Motor · qué le pasa a este", "Evidencia · cómo se calculó". |

**B2.** Es el único número del guion que se puede comprobar en directo y no
cuadra. Cambiarlo por 31,93 (o decir "unos 32 ciclos").

**B3.** El informe dice "operativo, parada_inmediata"; la app dice `EN_SERVICIO`,
`AOG_DERIVADO`. Dos idiomas en una defensa se nota.

---

## C · TÉCNICO INTERNO (no se ve, sostiene lo demás)

| # | Propuesta | Impacto | Riesgo | Fase |
| :--- | :--- | :--- | :--- | :--- |
| C1 | Pulido visual de la jerarquía | 5 | 2 | Fase 3 |
| C2 | Disparador de eventos al entrar en AOG | 5 | 6 | Fase 4 |
| C3 | pytest al 100 % | 2 | 0 | Fase 1 |
| C4 | Desfases de ciclo por unidad | 4 | 8 | Fase 5 |

**C3.** Ya está: 200 tests en verde. No es trabajo pendiente, es el estado de
salida de cada fase.

---

## FASES Y REGISTRO DE ESTADO

### Fase 1 · Cierre de coherencia (documento, cero riesgo)

Cubre: A2, B1, B2, B3, B5, C3.

| Item | Estado | Commit | Prueba ejecutada |
| :--- | :--- | :--- | :--- |
| A2 documentar 13/23/18 | PENDIENTE | — | — |
| B1 reescribir el guion | PENDIENTE | — | — |
| B2 corregir el 31,8 | PENDIENTE | — | — |
| B3 alinear vocabulario | PENDIENTE | — | — |
| B5 renombrar "Avanzar Turno" | PENDIENTE | — | — |
| C3 pytest 100 % (línea base) | HECHO | `81187ef` | `pytest tests -q` → 200 passed |

### Fase 2 · Residuos Ridge en la radiografía

Cubre: A1.

| Item | Estado | Commit | Prueba ejecutada |
| :--- | :--- | :--- | :--- |
| A1 precomputar residuos en la caché | PENDIENTE | — | — |
| A1 panel con eje en σ | PENDIENTE | — | — |

**Advertencias de esta fase:**

- Cargar el residualizer arrastra TensorFlow: al deserializarlo entra
  `src/ds02_rul/__init__.py`, que importa `ensemble.py` y con él Keras. Por eso
  la app no carga el artefacto nunca. Un panel que costara TensorFlow en cada
  render es inaceptable.
- `models/ensemble.joblib` pesa 468 KB (no 2,3 GB; ese peso es el HDF5 de
  `bilstm_ds02.keras`, 1,9 MB, dentro de `models/`).
- Los residuos están **estandarizados** (`res_scaler.transform`). Están en
  desviaciones típicas, no en grados ni bares. El eje tiene que llamarse
  "residuo (σ)".
- `scripts/build_ui_cache.py:209` ya escribe `ds02_rows.parquet` con los canales
  crudos. Ahí es donde entran las columnas de residuo: la app lee datos ya
  calculados y no carga el modelo.
- Verificar antes de construir: los residuos tienen que acompañar la caída del
  RUL. Si no acompañan, la fase se cancela y se anota el motivo.

### Fase 3 · Auditoría y lectura

Cubre: B4, C1.

| Item | Estado | Commit | Prueba ejecutada |
| :--- | :--- | :--- | :--- |
| B4 inspector de ventana de telemetría | PENDIENTE | — | — |
| C1 pulido visual | PENDIENTE | — | — |

### Fase 4 · Solo si sobra tiempo

Cubre: A3, A4, C2.

| Item | Estado | Commit | Prueba ejecutada |
| :--- | :--- | :--- | :--- |
| A3 calculadora de despacho | PENDIENTE | — | — |
| A4 jittering OOD | PENDIENTE | — | — |
| C2 disparador de eventos AOG | PENDIENTE | — | — |

### Fase 5 · No antes de la defensa

Cubre: A5, A6, C4.

| Item | Estado | Motivo del orden |
| :--- | :--- | :--- |
| A5 voz + Telegram | DESCARTADO POR AHORA | Necesita red y un token en el repo. Falla en directo si el aula no tiene internet. |
| A6 bloquear unidades retenidas | DESCARTADO POR AHORA | Quita recorrido libre en la demo. Es una decisión de producto, no una mejora técnica. |
| C4 desfases de ciclo por unidad | DESCARTADO POR AHORA | Rompe el reloj compartido y obliga a tocar el muro, la cronología y el comparador a la vez. |

---

## ORDEN Y CRITERIO

1. Fase 1 (esta tarde): todo documento. Deja la defensa sin contradicciones.
2. Fase 2 (esta semana): el único "wow" honesto.
3. Fase 3, solo si sobra tiempo.
4. Fase 5, nunca antes de la defensa.

La frontera está en A1, A2, B1, B2, B3, C1: alto impacto, riesgo bajo.

## VERIFICADO EN ESTA SESIÓN

- Partición del dataset: fit `[2, 5, 10, 18, 20]`, holdout `[16]`, test
  `[11, 14, 15]`. Coincide con `models/ds02_manifest.json` y
  `src/ds02_rul/persistence.py:65`.
- Anticipación 13/23/18: ejecutado con `L.first_alarm_cycle` sobre
  `app/cache/ds02_windows.parquet`.
- Los presets de demo están fijados por un test que comprueba que dan el estado
  que promete su nombre: `tests/test_live_eval.py:632`.
- La app no se contradice a sí misma: no hay cifras escritas a mano en los textos
  de la UI que puedan desmentir lo dibujado.
- El residualizer aparece en `src/ds02_rul/*` y en ningún archivo de `app/`.

---

## 2026-10-24 (noche) · Tres botones arreglados y dos incidentes de registro

### Los tres botones

Continuación de la auditoría de las escrituras `st.session_state[...] = ...` que
caen sobre claves de widget. Verificado ejecutando y arreglado:

| Botón | Dónde | Qué pasaba | Arreglo |
| :--- | :--- | :--- | :--- |
| Avanzar 10 ciclos de flota | `app/dashboard_ds02.py:1144` | Escribía `cycle` desde su propio handler: `StreamlitWidgetAlreadyInstantiatedError` | Bandera `_avance_flota`, aplicada en el bloque diferido (`:364`) |
| Recortar a 1.500 primeras filas | `app/dashboard_ds02.py:2925` | Escribía en la clave de un `st.data_editor`, que Streamlit declara de solo lectura | La tabla se guarda en `_editor_value` (`:2931`) |
| Presets de demo («Puntúa un ejemplo en 1 clic») | `app/dashboard_ds02.py:2714` | Igual: solo reventaba al pulsar con el modo «Editar tabla (pegar)» | Igual (`:2900` es donde se dibuja) |

Los tres tests de regresión (`test_avanzar_la_flota_mueve_el_reloj_sin_romper_la_app`,
`test_recortar_la_rejilla_no_rompe_la_app` y
`test_el_preset_demo_funciona_tambien_en_modo_editar`) **fallan sin el arreglo y
pasan con él**: se comprobó restaurando el código sin arreglar. Ninguno de los
tres botones estaba cubierto, así que los 206 tests en verde no los cazaban. Ahora
son 209.

El `data_editor` no admite el patrón diferido que arregla los otros dos: su clave
es de solo lectura y da igual que la escritura sea antes o después de instanciar
el widget. Ahí la tabla tiene que vivir en otra clave y pasarse como `data`.

**Dos falsos positivos** que la auditoría marcó y no lo eran:

- `app/dashboard_ds02.py:2795` escribe en `live_engine_id`. Es un `on_change`, que
  corre antes de instanciar el widget: es legal y es la forma correcta.
- Las escrituras de las líneas 352-365 y 387-388 son el propio mecanismo diferido
  de la app, aplicado antes de que los widgets nazcan.

### Incidente 1 · el registro de flota quedó vacío

`app/registros_flota.json` amaneció en `{"twins": {}, "hangar": {}, "altas": {}}`.
La sonda del agente anterior pulsó `reset_demo` (`app/dashboard_ds02.py:1915`),
que sí borra gemelos y hangar y los guarda en disco. Corría como script suelto, no
bajo pytest, así que el fixture de `tests/conftest.py` no actuó.

No hay copia en disco ni en git (el archivo está en `.gitignore`). La única vía de
recuperación es una sesión de navegador que siga viva con los gemelos en
`session_state`.

### Incidente 2 · las sondas fuera de pytest ensucian el registro

El mismo fixture que no protegió el incidente 1 no protege ninguna sonda ad-hoc:
al arrancar el tablero con `AppTest` desde un script, `_guardar_registros()`
escribe en el archivo de producción. Durante esta sesión tres sondas dejaron en el
archivo dos altas (`ESN-AUDITORIA`, `ESN-AVISO`) y dos registros de hangar. Se
restauró a mano a `{"twins": {}, "hangar": {}, "altas": {}}`.

**Conclusión para el futuro:** cualquier sonda que arranque el tablero tiene que
correr bajo pytest (donde el fixture aparta y restaura el archivo) o restaurar
`app/registros_flota.json` al terminar. Ojo: `sesion_vaciar`
(`app/dashboard_ds02.py:1216`) **no** borra la flota; solo vacía el log de sesión.
