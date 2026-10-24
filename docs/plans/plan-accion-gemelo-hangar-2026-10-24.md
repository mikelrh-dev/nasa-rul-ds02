# Plan de acción DS02 · gemelo digital y hangar

Origen: análisis de funcionamiento básico y de las propuestas del informe
`docs/informe_estrat_gico_y_arquitectura_mro_ds02.md`.

Restricciones de este plan, aceptadas de antemano:

1. **No se toca el modelo de ML.** Ningún cambio en `models/`, ningún reentrenamiento,
   ningún peso nuevo. Lo que se lea del modelo se lee.
2. **Todo tiene que funcionar correctamente.** Cada ítem termina con una prueba
   ejecutada que lo respalda. Sin eso, no se da por hecho.
3. **Se proponen mejoras implantables**, no deseos: cada una dice dónde se toca,
   cuánto cuesta y cómo se verifica.

Estado de partida: `81187ef` en `origin/master`, 200 tests en verde.

---

## VEREDICTO

**La app funciona. El defecto no es del modelo, y el modelo no hay que tocarlo.**

Tres conclusiones, en orden de importancia:

1. **Hay dos cosas llamadas "gemelo" y se pisan.** El gemelo registrado (la serie
   guardada en `twins`) y la sección "El gemelo" de la pestaña Motor son dos
   objetos distintos. La sección muestra la unidad de caché, no el gemelo
   registrado: `app/dashboard_ds02.py:1813` hace
   `_fila_g = snapshot[snapshot["unit"] == unit].iloc[0]`, y `unit` sale del
   selector de la barra lateral, que solo lista unidades de caché.

2. **El gemelo registrado no se puede abrir.** Su serie (cycle, pred, lower,
   upper, start_row) no se dibuja en ningún sitio. Lo que se ve es una fila en la
   tabla "Gemelos registrados" y una sparkline de `lower` en el muro. La banda no
   se pinta, no hay curva, no hay "ciclos hasta el fallo", no hay ventana que
   decidió.

3. **El gemelo y el hangar están desconectados del modelo, y eso está bien que
   lo estén.** El modelo solo se carga en el sandbox, la evaluación en vivo y el
   lote (`app/dashboard_ds02.py:832, 2587, 2467`). El hangar, el gemelo y la
   simulación repasan la caché, y `app/simulacion.py` lo dice en su cabecera.
   No hay que unirlos a la fuerza: hay que dar al gemelo el panel que le falta,
   que es un problema de `app/`, no de `models/`.

**Riesgo del plan completo: bajo.** Ningún ítem toca el modelo. La mayoría son
aditivos (paneles nuevos, columnas nuevas en la caché, documentos). Lo único que
renombra es el título de una sección.

---

## CÓMO USAR ESTE FICHERO (instrucciones para el agente)

Este documento es la lista única de trabajo. Quien lo lea tiene que hacer tres
cosas, en este orden:

1. **Verificar, no confiar.** Cada cifra de este plan salió de ejecutar el código.
   Si un agente encuentra algo distinto, lo corrige aquí y dice por qué.
2. **Rellenar el registro de fase.** Cada ítem tiene una tabla de estado con
   `Commit` y `Prueba ejecutada`. Se rellena al terminar, nunca antes.
3. **Dejar rastro del "no".** Si un ítem se descarta, se anota con el motivo.

Regla que no se negocia: **nadie marca un ítem como hecho sin salida de terminal
que lo pruebe.** "Lo he leído y parece bien" no es evidencia.

Restricción operativa: **no tocar `models/` ni `src/ds02_rul/`.** Los cambios van
en `app/`, `docs/`, `scripts/build_ui_cache.py` y `tests/`. Si un ítem parece
necesitar tocar el modelo, se detiene y se pregunta.

---

## FASE 0 · El defecto central (bloqueante)

Sin esto, nada de lo demás se entiende: el usuario registra un gemelo y no lo ve.

### 0.1 · Renombrar la sección que no es el gemelo

| | |
| :--- | :--- |
| Qué | La sección "El gemelo" de la pestaña Motor pasa a llamarse por lo que es: la vista consolidada del **motor de caché** seleccionado. |
| Por qué | Hoy promete el gemelo y muestra otra cosa. Es la misma clase de error que el informe de Gemini: un nombre que miente. |
| Dónde | `app/dashboard_ds02.py:1819` (subtítulo) y el comentario de la línea 1810. |
| Verificación | AppTest: el subtítulo nuevo aparece; el contenido no cambia. |
| Esfuerzo | 5 min. Riesgo 1. |

### 0.2 · Panel de detalle del gemelo registrado

| | |
| :--- | :--- |
| Qué | Un panel nuevo, propio, que muestre el gemelo seleccionado: su curva de RUL, su **banda** (`lower` y `upper`), su estado y su regla. |
| Por qué | Es la pieza que falta. La serie ya está guardada con todo lo necesario; es leer, no calcular. |
| Dónde | `app/dashboard_ds02.py`, nuevo contenedor junto a "Gemelos registrados". Usa `T.ciclo_a_ciclo(gemelo, umbrales)`, que ya devuelve cycle, pred, lower_media, lower_min y upper. |
| Verificación | AppTest: seleccionar un gemelo y comprobar que el panel existe y dibuja la banda. Añadir un test que fije que la banda dibujada es `lower` y `upper`, no solo `lower`. |
| Esfuerzo | Medio. Riesgo 3. |

### 0.3 · "Ciclos hasta el fallo" y ventana que decidió, en ese panel

| | |
| :--- | :--- |
| Qué | El número que ya tienen las unidades de caché (`S.ciclos_hasta_fallo`) y la ventana que sostuvo la decisión (`T.vista_resultado` ya la elige). |
| Por qué | Son las dos preguntas básicas de un gemelo digital: "¿cuánto le queda?" y "¿en qué dato te basas?". |
| Dónde | `app/simulacion.py:ciclos_hasta_fallo` sobre la serie del gemelo; `app/twin.py:vista_resultado` para la ventana. |
| Verificación | Test que compruebe que el número de ciclos coincide con el cruce de `lower` en la serie guardada. |
| Esfuerzo | Bajo. Riesgo 2. |

---

## FASE 1 · Funcionamiento básico del gemelo

### 1.1 · Guardar los sensores crudos en el gemelo

| | |
| :--- | :--- |
| Qué | `T.make_twin` solo guarda cycle, pred, lower, upper y start_row. Sin las filas crudas no se puede volver a puntuar el gemelo. |
| Por qué | Es el requisito para estresar un gemelo en el sandbox y para re-puntuarlo. Sin esto, el gemelo es de solo lectura. |
| Dónde | `app/twin.py:make_twin`. Añadir las filas de telemetría (50 filas × 19 canales por ventana, o una referencia a la caché cuando el gemelo sale del alta). |
| Ojo | No toca el modelo: guarda la **entrada**, no el modelo. |
| Verificación | Test que reconstruya la tabla desde el gemelo guardado y compruebe que `INF.preflight` la acepta. |
| Esfuerzo | Medio. Riesgo 4 (crece el JSON de registros). |

### 1.2 · Dejar que el sandbox acepte un gemelo

| | |
| :--- | :--- |
| Qué | `_sandbox_estres` trabaja sobre unidades de caché. Con 1.1, puede aceptar la tabla de un gemelo registrado. |
| Por qué | El sandbox es la única pieza que llama al modelo. Si el gemelo no puede entrar, el modelo y el gemelo siguen sin hablarse. |
| Dónde | `app/dashboard_ds02.py:_sandbox_estres` y `app/ui_inference.py:score_table`. |
| Verificación | Test que puntúe un gemelo guardado y compruebe que la banda y el estado se recalculan. |
| Esfuerzo | Medio. Riesgo 4. |

### 1.3 · Documentar que el hangar no toca al modelo

| | |
| :--- | :--- |
| Qué | `S.reiniciar_vida` ya lo dice en su módulo ("la caché no tiene datos de un motor reparado"), pero nadie lo lee. Que lo diga la UI en el panel del gemelo. |
| Por qué | No es un defecto: es una decisión honesta. Pero si no se declara, parece un fallo. |
| Dónde | `app/dashboard_ds02.py`, panel del gemelo. |
| Verificación | AppTest: el aviso aparece cuando el gemelo tiene registro de hangar. |
| Esfuerzo | Bajo. Riesgo 1. |

---

## FASE 2 · Coherencia documental (cero riesgo, se puede hacer ya)

### 2.1 · Corregir el 31,8 del guion

| | |
| :--- | :--- |
| Qué | El informe dice "Unidad 15 en el ciclo 6 con L_inf = 31.8". La realidad: `lower` (media) = 31,93 y `lower_min` = 31,30. Y el preset de U15 es el ciclo 2, donde vale 35,76. |
| Por qué | Es el único número del guion que se puede comprobar en directo y no cuadra. |
| Dónde | `docs/informe_estrat_gico_y_arquitectura_mro_ds02.md` y el guion de defensa. |
| Verificación | Ejecutar `L.unit_curve` sobre U15 y citar el valor que devuelve. |
| Esfuerzo | 5 min. Riesgo 1. |

### 2.2 · Documentar los 13/23/18 de anticipación

| | |
| :--- | :--- |
| Qué | Verificados con `L.first_alarm_cycle`: U11 alarma 22 → verdad 35 (13), U14 29 → 52 (23), U15 25 → 43 (18). Hoy solo existen en el informe de Gemini. |
| Por qué | Es la mejor cifra del proyecto y un tribunal preguntará de dónde sale. |
| Ojo | Declararlos como "alarma menos verdad", nunca como backtest: no hay protocolo de backtest. |
| Dónde | `docs/informes/`, con el comando que los reproduce. |
| Verificación | El comando está en el documento y se puede re-ejecutar. |
| Esfuerzo | 15 min. Riesgo 2. |

### 2.3 · Alinear el vocabulario

| | |
| :--- | :--- |
| Qué | El informe usa `operativo`, `pendiente_revision`, `parada_inmediata`, `en_reparacion`. La app usa `EN_SERVICIO`, `INSPECCION_PROGRAMADA`, `AOG_DERIVADO`, `EN_TALLER`, `PRUEBA_EN_BANCO` (`app/hangar.py:18-22`). |
| Por qué | Dos idiomas en una defensa se nota. |
| Dónde | El informe y el guion. |
| Esfuerzo | 10 min. Riesgo 1. |

### 2.4 · Reescribir el guion contra lo que hay

| | |
| :--- | :--- |
| Qué | El informe promete seis funciones que no existen: bloqueo de unidades, calculadora de despacho, jittering, "Avanzar Turno", la máquina de estados con otros nombres, un inspector de telemetría. |
| Por qué | Decirlas en el tribunal es lo único que puede hundir la defensa. |
| Dónde | El guion de defensa. |
| Esfuerzo | 30 min. Riesgo 1. |

---

## FASE 3 · Mejora honesta (el único "wow" que no es teatro)

### 3.1 · Enseñar los residuos Ridge reales

| | |
| :--- | :--- |
| Qué | El modelo consume `SensorResidualizer` (`src/ds02_rul/residualizer.py`): una regresión Ridge por sensor sobre las condiciones de vuelo (`alt`, `Mach`, `TRA`, `T2`). La app no lo usa: su "Radiografía de sensores" (`app/dashboard_ds02.py:265`) calcula un porcentaje contra los 5 primeros ciclos. |
| Por qué | Cierra la pregunta "¿y si el modelo mira al piloto?". Es la explicación física real, no una deriva de referencia. |
| Dónde | Precomputar los residuos en `scripts/build_ui_cache.py:209`, que ya escribe `ds02_rows.parquet`. La app lee, no calcula. |
| Ojo con el modelo | **Lee** los parámetros del residualizer; no modifica nada. `models/ensemble.joblib` pesa 468 KB, pero cargarlo arrastra TensorFlow (entra `src/ds02_rul/__init__.py` → `ensemble.py` → Keras). Por eso se precomputa: la app no paga ese coste. |
| Ojo con la unidad | Los residuos están **estandarizados** (`res_scaler.transform`). Están en σ, no en grados. El eje se llama "residuo (σ)". |
| Verificación previa obligatoria | Los residuos tienen que acompañar la caída del RUL. Si no acompañan, la fase se cancela y se anota el motivo. |
| Verificación final | Test que compare el residuo con la caída del RUL en las tres unidades. |
| Esfuerzo | Medio. Riesgo 5. |

---

## FUERA DE ESTE PLAN

| Propuesta | Motivo |
| :--- | :--- |
| Voz de cabina + bot de Telegram | Necesita red y un token en el repo. Falla en directo si el aula no tiene internet. No avanza la tesis. |
| Bloquear unidades retenidas en la UI | Quita recorrido libre en la demo. Es una decisión de producto, no una mejora técnica. |
| Desfases de ciclo por unidad | Rompe el reloj compartido y obliga a tocar el muro, la cronología y el comparador a la vez. |
| Calculadora de despacho de misión | Narrativa potente, pero prometer una tasa de degradación es arriesgado. Solo si sobra tiempo. |
| Jittering OOD | Mientras no puedas decir "la banda sigue siendo 90 %", es un agujero en tu propia tesis. |
| Tocar `models/` o `src/ds02_rul/` | Prohibido por las restricciones de este plan. |

---

## ORDEN Y CRITERIO

1. **Fase 0** (esta semana): el defecto central. Sin esto, el gemelo sigue sin verse.
2. **Fase 2** (esta tarde, en paralelo): todo documento. Cero riesgo.
3. **Fase 1** (después de la 0): el gemelo deja de ser de solo lectura.
4. **Fase 3** (si sobra tiempo): la mejora honesta.
5. **Fuera de este plan**: nunca antes de la defensa.

Criterio de decisión para cada ítem: ¿arregla algo que el usuario ve o que el
tribunal puede comprobar? Si sí, entra. Si solo suena bien, no.

---

## REGISTRO DE ESTADO

### Fase 0

| Ítem | Estado | Commit | Prueba ejecutada |
| :--- | :--- | :--- | :--- |
| 0.1 renombrar la sección | PENDIENTE | — | — |
| 0.2 panel de detalle del gemelo | PENDIENTE | — | — |
| 0.3 ciclos hasta el fallo + ventana | PENDIENTE | — | — |

### Fase 1

| Ítem | Estado | Commit | Prueba ejecutada |
| :--- | :--- | :--- | :--- |
| 1.1 sensores crudos en el gemelo | PENDIENTE | — | — |
| 1.2 sandbox acepta gemelos | PENDIENTE | — | — |
| 1.3 declarar que el hangar no toca el modelo | PENDIENTE | — | — |

### Fase 2

| Ítem | Estado | Commit | Prueba ejecutada |
| :--- | :--- | :--- | :--- |
| 2.1 corregir el 31,8 | PENDIENTE | — | — |
| 2.2 documentar 13/23/18 | PENDIENTE | — | — |
| 2.3 alinear vocabulario | PENDIENTE | — | — |
| 2.4 reescribir el guion | PENDIENTE | — | — |

### Fase 3

| Ítem | Estado | Commit | Prueba ejecutada |
| :--- | :--- | :--- | :--- |
| 3.1 residuos Ridge | PENDIENTE | — | — |

### Línea base (ya hecho)

| Ítem | Estado | Commit | Prueba ejecutada |
| :--- | :--- | :--- | :--- |
| Suite verde | HECHO | `81187ef` | `pytest tests -q` → 200 passed |
| Muro muestra gemelos registrados | HECHO | `7f64606` | AppTest: 4 tarjetas |
| El fixture no borra el registro del usuario | HECHO | `81187ef` | Centinela restaurado |

---

## VERIFICADO EN LA SESIÓN QUE ORIGINÓ ESTE PLAN

- La sección "El gemelo" usa `snapshot[snapshot["unit"] == unit]`: es la caché.
- En la pestaña Motor, la palabra "gemelo" solo aparece en el comentario de la
  línea 1810 y en el subtítulo de la 1819.
- La serie de un gemelo registrado solo se usa en `app/dashboard_ds02.py:1599`,
  para un valor por defecto de un input.
- `T.make_twin` guarda cycle, pred, lower, upper y start_row. **No guarda los
  sensores crudos**, así que el gemelo no se puede repuntuar.
- El modelo se carga en `app/dashboard_ds02.py:832, 2587, 2467` (sandbox,
  evaluación en vivo y lote). En ningún otro sitio.
- `app/simulacion.py` declara que nunca llama al modelo.
- `S.ciclos_hasta_fallo` se calcula sobre la caché y solo se pinta para unidades
  de caché (`app/dashboard_ds02.py:1131, 1152`).
