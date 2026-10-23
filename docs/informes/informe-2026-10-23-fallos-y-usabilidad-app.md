# Informe: fallos y usabilidad de la app DS02 (Streamlit)

> **Fecha:** 2026-10-23
> **Estado del repo en el momento del análisis:** `master` en `a28a5af`, con
> `app/dashboard_ds02.py` modificado (204 inserciones, 34 borrados, **sin
> commitear**) y `app/ui_alta.py` + `tests/test_ui_alta.py` sin seguimiento.
> **Suite:** 152 tests verdes.
>
> **Para quien lo lea mañana:** cada afirmación de este informe está reproducida
> con un comando o con una sonda. Si algo no se reproduce, el informe está mal.

---

## 0. Resumen para quien tiene dos minutos

**La app está rota en sus dos funciones estrella, y las dos por la misma razón.**

| Función | Estado | Efecto |
|---|---|---|
| **Incorporar unidad** (sidebar, C1) | **ROTA** | Traceback completo en pantalla y la unidad se pierde |
| **Cargar escenario de demo** (C2) | **ROTA** | Traceback completo en pantalla |
| **Registrar gemelo** (pestaña 5) | Funciona | Pero **no aparece en el tablero del hangar** |

Las dos rotas fallan por el mismo motivo: el código escribe en
`st.session_state["unit"]` y `st.session_state["preset"]` **después** de que el
widget con esa clave ya se creó. Streamlit lo prohíbe y lanza
`StreamlitWidgetAlreadyInstantiatedError`. Es un fallo del 100 %: falla siempre,
en el navegador real, con la app tal como está.

**El arreglo es de una línea en cada sitio**, y está verificado: quité la línea
259 y la app funcionó (la unidad entró en el selector, el contador pasó a
"0 / 6" y los 152 tests siguieron verdes). He restaurado el fichero original para
no tocarte el código sin permiso; el arreglo exacto está en la sección 5.

**Sobre tu sensación de "mucha información y poca usabilidad": es correcta y
medible.** Una sola pantalla tiene 22 métricas, 10 tablas, 140 botones, 14
campos, 4 selectores y 9 extensores. Y hay dos conceptos ("flota" y "gemelos")
que no se hablan entre sí, que es la causa de que "probar uno sí y varios no".

---

## 1. Cómo lo he probado

No he leído solo el código. He levantado la app de verdad y la he usado.

1. **Servidor real** en `http://localhost:8531`, con Chromium dirigiéndola
   (`browser_exec`). Es la única forma de ver un traceback que el usuario ve.
2. **AppTest** (el arnés que ya usa el repo) para reproducir con precisión y
   para medir widgets.
3. **Sondas puras** sobre `ui_alta.py` + `ui_data_loader.py` para separar "la
   lógica está bien" de "la UI la rompe".

Las sondas viven en el directorio scratch de Hermes, no en el repo.

---

## 2. Hallazgos confirmados

### H1 — "Incorporar unidad" rompe la app (CRÍTICO)

**Qué hace el usuario:** rellena "Matrícula" y "Perfil de desgaste" en el
sidebar y pulsa **Incorporar unidad**.

**Qué pasa:** la app muestra un traceback completo en pantalla, en rojo:

```
streamlit.errors.StreamlitWidgetAlreadyInstantiatedError: st.session_state['unit']
cannot be modified after the widget with that key is instantiated. Assign
st.session_state['unit'] before creating the widget, or update it from an
on_change or on_click callback, which runs before the widget is instantiated.

Traceback:
File "C:\Users\mikel\Desktop\Pruebas\nasa\app\dashboard_ds02.py", line 259, in <module>
    st.session_state["unit"] = int(A.unidad_alta(len(altas) - 1))
```

**Causa:** `app/dashboard_ds02.py:212` crea `st.segmented_control(..., key="unit")`.
La línea 259 intenta escribir en esa misma clave cuando el widget ya existe.

**Agravante:** el script muere **antes de confirmar el estado**, así que la unidad
se pierde. Verificado: tras recargar la página, el selector seguía mostrando solo
`Unidad 11`, `Unidad 14` y `Unidad 15`. La alta no sobrevivió.

**Cómo reproducirlo:**

```bash
./.venv/Scripts/python.exe -m streamlit run app/dashboard_ds02.py --server.headless true
# 1. Rellena "Matrícula" con cualquier texto de 3+ caracteres
# 2. Pulsa "Incorporar unidad"
# 3. Aparece el traceback
```

---

### H2 — "Cargar escenario de demo" también rompe (CRÍTICO)

**Qué hace el usuario:** pulsa **Cargar escenario de demo** (la feature C2, el
botón que "deja la app en el estado desde el que se cuenta la historia").

**Qué pasa:** el mismo traceback, en otra línea:

```
streamlit.errors.StreamlitWidgetAlreadyInstantiatedError: st.session_state['preset']
cannot be modified after the widget with that key is instantiated.

Traceback:
File "C:\Users\mikel\Desktop\Pruebas\nasa\app\dashboard_ds02.py", line 1080, in <module>
    st.session_state["preset"] = "Normal"
```

**Causa:** `app/dashboard_ds02.py:280-284` crea `st.selectbox("Preset", ...,
key="preset")`. Las líneas 1080-1084 escriben en `preset`, `unit` y `cycle`.

**Efecto:** el modo demo no funciona. Los umbrales, el ciclo 29 y la unidad 14
que promete el botón nunca se cargan. La propia app dice que deja la app en
"umbrales 30/25, ciclo 29 y la unidad 14", y no llega a hacerlo.

**Importante:** este botón es el protagonista de la defensa en directo. Está roto.

---

### H3 — Los gemelos registrados NO aparecen en el tablero del hangar (CRÍTICO)

Este es el hallazgo que explica tu sensación de "uno sí, varios no".

Hay **dos conceptos que no se hablan**:

| Concepto | De dónde sale | Quién lo muestra |
|---|---|---|
| **Flota** | caché (`U11/U14/U15`) + altas del sidebar | tablero, cronología, cola de mantenimiento, órdenes |
| **Gemelos** | "Registrar gemelo" en la pestaña 5 | solo la tabla "Gemelos registrados" |

**Evidencia.** Registré dos gemelos por la ruta de la pestaña 5. Los dos
persistieron en disco:

```
twins: ['ESN-CRIT-01', 'ESN-SANO-01']
```

Pero el tablero del hangar seguía diciendo:

```
Unidades monitorizadas   3
Unidades en hangar       0 / 3
```

y el selector de unidad seguía mostrando solo `Unidad 11`, `Unidad 14` y
`Unidad 15`. **Los gemelos registrados son invisibles para el hangar.**

**Consecuencia para el usuario:**
- La forma **rápida** de añadir motores (sidebar) → **revienta** (H1).
- La forma que **funciona** (pestaña 5) → **no se ve en el tablero**.

Así que "probar varios" es imposible hoy, y "probar uno" no se refleja donde
esperas verlo.

---

### H4 — El botón y el selector de la pestaña 5 no se hablan

En la pestaña 5 hay dos mecanismos que controlan cosas distintas:

- Los **botones** de arriba ("Sano U15 inicio", "Medio U11 desgaste", "Crítico
  U14 hangar") puntúan y guardan en `st.session_state["live_result"]`.
- El **selector** "Dataset demo" controla la tabla de ejemplo y el
  `st.caption` de "Ventana real de…".

**Evidencia.** Pulsé "Crítico U14 hangar". La app respondió correctamente:

> Crítico U14 hangar puntuado abajo (ciclos 28→30).

Y las métricas mostradas eran de U14:

```
RUL estimada     36.4      (U14 @ 0.40 → 36.4, medido)
Límite inferior  22.9
Límite superior  53.4
```

Pero el rótulo de la tabla seguía diciendo:

> Ventana real de U15 · ciclos 4→4 · filas 167–217

**El usuario ve U15 en un sitio y U14 en otro.** Los dos números son correctos
por separado; juntos son una contradicción en pantalla.

**Causa:** el botón escribe `live_result` pero no `example_meta`; el caption se
deriva del selector, no del botón.

---

### H5 — El botón de registrar el gemelo está plegado

El botón "Registrar gemelo" vive dentro de un `st.expander` ("Añadir este motor
a la flota") que llega **cerrado**. El usuario tiene que:

1. puntuar la unidad,
2. **encontrar** el extensor entre los 9 que hay en la página,
3. abrirlo,
4. y solo entonces registrar.

Verificado en el DOM: el botón no existe en el árbol hasta que el extensor se
abre.

**No es un fallo, es una decisión que cuesta.** Y está en el camino crítico de
la única ruta que funciona.

---

### H6 — Los presets dan ventanas de un solo ciclo

La propia app lo avisa, con honestidad:

> Todas las filas pertenecen al mismo ciclo de vuelo: la ventana cubre un único
> ciclo, así que la tendencia que ve el modelo es casi plana.

Medido sobre la caché:

| Unidad | Filas/ciclo | Ventana de 50 filas cubre |
|---|---|---|
| U11 | 112,5 | ~0,45 ciclos |
| U14 | 20,6 | ~2,4 ciclos |
| U15 | 64,7 | ~0,77 ciclos |

Resultado: los presets de U11 y U15 devuelven ventanas de **un solo ciclo**
(`ciclos 4→4`, `ciclos 21→21`). El modelo ve una línea plana y la app lo dice,
pero la predicción se presenta igual como si fuera informativa.

**No es un bug: es una limitación del remuestreo (`STRIDE = 100` con ventana de
50).** Pero es un problema de experiencia: el usuario ve una predicción sobre
una línea plana.

---

### H7 — Densidad de información (tu sensación, medida)

Medido en el DOM de la pantalla principal:

| Elemento | Cantidad |
|---|---|
| Métricas (`st.metric`) | 22 |
| Tablas (`st.dataframe`) | 10 |
| Botones | 140 |
| Campos de entrada | 14 |
| Selectores | 4 |
| Extensores (`st.expander`) | 9 |
| Caracteres de texto | 4.819 |

Y todo eso con solo 3 motores reales en la caché. El 90 % de la pantalla es
infraestructura, no decisión.

---

## 3. Diagnóstico: la causa raíz

Los fallos H1 y H2 son **la misma clase de error**: escribir en el estado de un
widget después de instanciarlo.

```
streamlit.errors.StreamlitWidgetAlreadyInstantiatedError
```

Hay 4 sitios que lo hacen. Los he buscado todos de forma sistemática
(`st.session_state[...] =` contra la lista de `key="..."` de los widgets):

| Línea | Escritura | Colisiona con | Efecto |
|---|---|---|---|
| 259 | `st.session_state["unit"]` | `key="unit"` (línea 212) | **Revienta** |
| 1080 | `st.session_state["preset"]` | `key="preset"` (línea 280) | **Revienta** |
| 1083 | `st.session_state["unit"]` | `key="unit"` (línea 212) | **Revienta** |
| 1084 | `st.session_state["cycle"]` | sin key | No revienta |

Nota: el slider de ciclo (línea 212-226) **no tiene `key=`**, así que la línea
1084 no es un problema. Pero `preset` sí lo tiene, y por eso el botón de demo
revienta antes de llegar a `unit`.

**Por qué los tests no lo pillan:** `AppTest` lanza la excepción, pero
`tests/test_ui_alta.py` solo comprueba la lógica pura de `ui_alta.py`, y
`tests/test_dss_ui.py` arranca la app **sin pulsar el botón**. No hay ningún
test que ejecute el botón "Incorporar unidad" ni el de demo. El hueco es de
cobertura de interacción, no de lógica.

**La lógica subyacente está bien.** Verificado directamente, sin la UI:

```
unidades en el snapshot: [-1000, 11, 14, 15]
 unit  cycle     lower  state
-1000     29 23.289735 HANGAR
   11     29 20.473962 HANGAR
   14     29 23.289735 HANGAR
   15     29 19.675633 HANGAR
```

La unidad de alta entra con su estado correcto. El fallo es exclusivamente la
escritura de estado.

---

## 4. El arreglo mínimo, verificado

### 4.1 Alta (línea 259)

Basta **borrar una línea**:

```diff
                 st.session_state[ALTA_KEY] = altas
-                st.session_state["unit"] = int(A.unidad_alta(len(altas) - 1))
                 st.session_state["twin_flash"] = (
```

La intención era "seleccionar la unidad recién añadida". Pero el widget ya
gestiona su propio estado: al recargar, el selector muestra la nueva unidad
porque `_vistas` la incluye. No hace falta escribir en la clave.

**Verificado en el navegador real tras el cambio:**

```
excepcion tras el alta: (ninguna)
success: ['Aeronave `EC-AAA` incorporada (U11 hasta el ciclo 1). ...']
opciones del selector: EC-AAA, EC-BBB, EC-CCC, Unidad 11, Unidad 14, Unidad 15
Unidades en hangar: 0 / 6
```

Tres altas seguidas, sin error. Y **152 tests verdes** con el cambio aplicado.

### 4.2 Demo (líneas 1080-1084)

Aquí no basta con borrar: el botón tiene que cambiar los widgets. El patrón
correcto en Streamlit es escribir en el estado **antes** de que el widget se
cree. Dos opciones:

- Mover las escrituras al principio del script, condicionadas a una bandera:
  ```python
  # al principio, antes de cualquier widget
  if st.session_state.get("_demo_pendiente"):
      st.session_state["preset"] = "Normal"
      st.session_state["unit"] = 14
      st.session_state["cycle"] = 29
      st.session_state.pop("_demo_pendiente", None)
  ```
  y el botón solo hace `st.session_state["_demo_pendiente"] = True; st.rerun()`.
- O usar `on_click` para escribir antes de que el widget se instancie.

**No he aplicado esta segunda** porque quiero enseñarte el diagnóstico, no
decidir por ti. La primera opción es la más simple y encaja con el código actual.

### 4.3 Qué NO es el arreglo

- No hay que tocar `app/ui_alta.py`: su lógica es correcta.
- No hay que tocar `app/ui_data_loader.py`.
- No hay que tocar `models/`, `src/` ni `mia/`.

---

## 5. Lo que esto significa para el plan de usabilidad

El plan de usabilidad que escribí ayer (`docs/plans/plan-gemelo-digital-hangar.md`)
está construido sobre la premisa de que la app funciona. **Esa premisa es falsa
hoy**, y cambia la prioridad:

### La prioridad no es la usabilidad: es que funcione

| Orden | Qué | Por qué primero |
|---|---|---|
| **1** | **Arreglar el alta (1 línea)** | Sin esto, la feature estrella no existe |
| **2** | **Arreglar el modo demo** | Es el protagonista de la defensa en directo |
| **3** | **Unir flota y gemelos** | Ahora mismo son dos mundos que no se hablan |
| **4** | **Añadir tests de interacción** | Ningún test pulsa esos botones; el fallo era invisible |
| 5 | El tablero de tarjetas | Mejora la entrada, pero sobre una app rota no se nota |
| 6 | El modo historia | Es la guinda |

Los pasos 1 y 2 son **minutos**. Los pasos 3 y 4 son lo que evita que vuelva a
pasar.

### Lo de los tests de interacción (paso 4) merece énfasis

El fallo llevaba ahí desde que se escribió C1/C2, y **152 tests no lo vieron**.
La razón es que `AppTest` arranca la app pero no pulsa los botones. Añadir un
test que haga `app.button[...].click().run()` y **afirme que no hay excepción**
habría detectado esto en el momento.

Es el tipo de test más barato y más valioso que se puede añadir: una sola línea
de acción por botón.

---

## 6. Pendiente: he contaminado un fichero de estado

**`app/registros_flota.json`** es estado de ejecución (está en `.gitignore`, no es
código). Mis pruebas de la pestaña 5 escribieron en él dos gemelos:

```
twins: ['ESN-CRIT-01', 'ESN-SANO-01']
```

El fichero existía antes de mis pruebas (1.700 bytes, del 22 de octubre), así que
**no sé exactamente qué contenia antes**. Ahora tiene 2.555 bytes con mis dos
gemelos.

Si te molesta ver esos dos gemelos en la tabla "Gemelos registrados", se borran:

```bash
rm app/registros_flota.json
```

La app lo recrea vacío. **No lo he borrado yo** porque no sé si el contenido
anterior era tuyo y querías conservarlo. Dímelo y lo dejo como estaba.

**Lo demás está intacto.** He restaurado `app/dashboard_ds02.py` a su estado
original (verificado: `git diff --stat` sigue mostrando las mismas 204
inserciones y 34 borrados) y he parado el servidor de pruebas.

---

## 7. Cómo reproducirlo todo

```bash
# 1. Servidor real
./.venv/Scripts/python.exe -m streamlit run app/dashboard_ds02.py --server.headless true --server.port 8531

# 2. En el navegador: rellena "Matrícula" y pulsa "Incorporar unidad" -> traceback
# 3. En el navegador: pulsa "Cargar escenario de demo" -> traceback (linea 1080)
# 4. Recarga la pagina: la unidad del paso 2 ha desaparecido

# Suite (debe seguir en 152)
pytest tests -q
```

Las sondas que he usado viven en el directorio scratch:

| Sonda | Qué comprueba |
|---|---|
| `probe_alta_multi.py` | El flujo de alta de varios motores |
| `probe_alta_debug.py` | Que el fallo es la línea 259 y no el formulario |
| `probe_alta_fix.py` | Que la app funciona tras quitar esa línea |

---

## 8. Una nota sobre la honestidad del aviso de un solo ciclo

Hay algo que quiero destacar porque es lo mejor de la app y está en un rincón.

Cuando el usuario puntúa una ventana que cubre un solo ciclo, la app **lo dice**:

> Todas las filas pertenecen al mismo ciclo de vuelo: la ventana cubre un único
> ciclo, así que la tendencia que ve el modelo es casi plana.

Y también dice, en la evaluación en vivo:

> **Sin ground truth**: esta unidad no trae RUL real, así que no se declara RMSE
> ni MAE.

Eso es exactamente el estándar de honestidad que el repo mantiene en los informes
y en los ADR. **La app miente en los fallos (H1, H2) pero no en los números.**
Cuando se arreglen los dos botones, la base sobre la que construir es sólida.

---

## 9. Cifras de referencia (para no perderlas)

Todas verificadas sobre `app/cache/ds02_windows.parquet`:

```
U11: ciclos 1..59  ventanas=3293
U14: ciclos 3..76  ventanas=760
U15: ciclos 2..67  ventanas=2143

U11: c1->APTO, c6->INSPECCION, c8->APTO, c9->INSPECCION, c17->APTO, c20->INSPECCION, c22->HANGAR
U14: c3->APTO, c8->INSPECCION, c14->APTO, c20->INSPECCION, c29->HANGAR
U15: c2->APTO, c9->INSPECCION, c16->APTO, c18->INSPECCION, c25->HANGAR
```

Umbrales 30 / 25 · RMSE 4,2892 · MAE 3,1792 · macro-RMSE 4,9026 · MAE zona
crítica 1,13.

Si mañana alguno de estos números sale distinto, el repo ha cambiado y este
informe queda desactualizado.
