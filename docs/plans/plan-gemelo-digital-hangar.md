# Plan: gemelo digital del hangar (DS02)

> **Para quien ejecute este plan:** usa la skill `plan` para validar el alcance y
> `test-driven-development` para cada tarea. Este documento no ejecuta nada.
>
> **Para quien lo revise:** cada cifra es reproducible con los comandos de la
> sección 8. Si una afirmación no se puede reproducir, es un error del plan.

**Objetivo:** que un usuario sin contexto entre en la app, entienda en menos de 10
segundos qué decide el sistema, y pueda incorporar **uno o varios** motores y ver su
estado sin leer documentación.

**Arquitectura:** no se toca inferencia, ni `models/`, ni `src/ds02_rul/`, ni
`mia/`, ni `app/cache/`. Todo el trabajo es presentacional sobre
`app/dashboard_ds02.py` y módulos de apoyo nuevos o existentes.

**Stack:** Streamlit 1.66.0 · Plotly 7.1.0 · pandas · PyArrow. Sin TensorFlow en
tiempo de render. Sin dependencias nuevas.

---

## 0. Veredicto ejecutivo

Tres conclusiones, en este orden:

1. **El encuadre honesto es "hangar de motores", no "hangar de aviones".** El
   dataset tiene **tres motores turbofán**, no aviones. Un hangar de motores es
   además lo que de verdad hace un taller MRO: los motores se bajan del ala y
   entran al taller. La intuición que pide el usuario se satisface igual, y sin
   el riesgo de credibilidad que el repo ya rechazó una vez (sección 7, R1).

2. **La capacidad que falta es la incorporación en lote.** La individual ya
   existe y funciona (C1 en el sidebar + pestaña "Evaluar unidad nueva"). No hay
   ninguna ruta para "traigo doce motores y los triaje de una vez". Esa es la
   feature nueva, y es la que el usuario pidió explícitamente.

3. **El resto es reordenar, no rehacer.** La app ya tiene 1.995 líneas, 5
   pestañas, 7 gráficos Plotly, ciclo de vida de hangar, motor de reglas, gemelos,
   órdenes de trabajo y 152 tests verdes. El problema diagnosticado es de
   **entrada y encuadre**, no de fondo.

**Orden propuesto:** Fase 0 (cerrar lo que está a medias) → Fase 1 (el tablero,
que es lo que la hace intuitiva) → Fase 2 (el lote, que es lo pedido) →
Fase 3 (el gemelo) → Fase 4 (el taller) → Fase 5 (mejoras de experiencia).

---

## 1. Diagnóstico: qué hay y qué falta

### 1.1 Lo que ya está construido y verificado

Medido sobre el repo en este momento. **No es trabajo pendiente.**

| Pieza | Estado | Fuente |
|---|---|---|
| `app/dashboard_ds02.py` — 1.995 líneas, 5 pestañas, sidebar de simulación | Hecho | `app/dashboard_ds02.py:480` |
| Gráficos interactivos | Hecho — 7 `st.plotly_chart`, cero matplotlib en `app/` | verificado por `tests/test_dss_ui.py:260` |
| Caché offline (6.196 ventanas / 12.538 filas / 3 unidades) | Hecho | `app/cache/ds02_windows.parquet` |
| Cargadores cacheados sin TensorFlow | Hecho | `app/ui_data_loader.py:109-143` |
| Política de triage por límite inferior | Hecho | `app/ui_data_loader.py:145`, `app/ui_rules.py:96` |
| Motor de reglas (R1/R9/R8/R7) | Hecho | `mia/reglas.py:195-204` |
| Gemelos registrados y persistidos | Hecho | `app/twin.py`, `app/registros_flota.json` |
| Ciclo de vida del hangar con decisión congelada | Hecho | `app/hangar.py:56`, `:116` |
| Alta individual en el sidebar (C1) | Hecho, **sin commitear** | `app/ui_alta.py`, `app/dashboard_ds02.py:227-271` |
| Modo demo en un clic (C2) | Hecho, **sin commitear** | `app/dashboard_ds02.py:1077` |
| Panel de primera lectura (C3) | Hecho, **sin commitear** | `app/dashboard_ds02.py:463` |
| Tema oscuro en configuración, sin CSS | Hecho | `.streamlit/config.toml` |
| `alt=` accesible en cada gráfico y tabla | Hecho | `tests/test_dss_ui.py:260` |
| Suite de pruebas | **152 tests verdes** | `pytest tests -q` |

**Estado del árbol de trabajo:** hay 204 líneas insertadas y 34 borradas en
`app/dashboard_ds02.py` sin commitear, más `app/ui_alta.py` y
`tests/test_ui_alta.py` sin seguimiento. La app arranca headless sin excepción y
los 5 tabs renderizan (verificado con `AppTest`).

### 1.2 Lo que falta

| Hueco | Evidencia |
|---|---|
| **Incorporación en lote** | No existe ningún módulo ni UI que puntúe N unidades a la vez. `app/ui_alta.py` da de alta **una** por formulario; `app/ui_inference.py` puntúa **una** por formulario. |
| **Muro de tarjetas** | La flota se muestra como un scatter de ciclos y una tabla. No hay una tarjeta por motor en la que se pueda pulsar. |
| **Onboarding como estado inicial** | Existe ("¿Primera vez aquí? Empieza en 1 clic") pero vive en la **quinta** pestaña (`app/dashboard_ds02.py:1538`). El usuario que entra no lo ve. |
| **Vista consolidada por motor** | La verdad de un motor está repartida: estado en la pestaña 1, curva RUL en la 2, sensores en la 3, ciclo de vida en la 1, orden de trabajo en la 1. Hay que cambiar de pestaña cuatro veces para entender **un** motor. |
| **Modo historia** | El modo demo (C2) deja un estado fijo. No hay una secuencia que cuente la narrativa. |
| **Feedback no intrusivo** | Los avisos usan `st.success` en bloque, que empuja el contenido hacia abajo. |

### 1.3 La restricción que condiciona todo

El repo tiene siete reglas de oro (G1–G7 en `planStreamlit.md` §2). Las que
importan para este plan:

- **G2** — el tema vive en `.streamlit/config.toml`. **Prohibido
  `unsafe_allow_html` y `<style`.** Lo vigila `tests/test_dss_ui.py:292`.
- **G3** — cada gráfico y tabla lleva un `alt` no vacío.
- **G4** — ninguna métrica se hardcodea: se recalcula de la caché.
- **G5** — umbrales 30 / 25, decisión por límite inferior.
- **G7** — la integridad metodológica es el activo principal. No se fabrica
  telemetría, no se inventan cifras, no se inventan entidades.

---

## 2. Decisión de encuadre: motores, no aviones

### 2.1 Qué dice el dataset

Medido sobre la caché real:

```
U11: ciclos puntuados   1..59   ventanas=3293
U14: ciclos puntuados   3..76   ventanas=760
U15: ciclos puntuados   2..67   ventanas=2143
```

Tres unidades. **Motores turbofán del dataset N-CMAPSS DS02.** No hay aviones,
no hay flota de aeronaves, no hay modelos de avión.

### 2.2 Por qué "hangar de motores" y no "hangar de aviones"

El usuario pide "un gemelo digital de un hangar" y habla de "aviones". La
intuición es correcta — un hangar con activos etiquetados, cada uno con un estado
de salud — pero la palabra "avión" es una afirmación que el dataset no sostiene.

**La buena noticia: "hangar de motores" es más realista, no menos.** Un taller
MRO (Maintenance, Repair and Overhaul) trabaja **motores**: se bajan del ala,
entran al taller, se prueban en banco y vuelven. Eso es exactamente el ciclo de
vida que ya implementa `app/hangar.py`:

```
EN_SERVICIO → INSPECCION → AOG → TALLER → BANCO → EN_SERVICIO
```

Así que el encuadre honesto **ya es** el que el usuario imagina, solo que con la
entidad correcta. El gemelo digital es de **motores**, y el hangar es un hangar de
motores.

### 2.3 Qué se permite y qué no

**Se permite:**

- Una **matrícula como etiqueta de visualización.** El usuario teclea `EC-MKR` y
  la app la muestra. Ya existe en C1 (`app/ui_alta.py`, `app/dashboard_ds02.py:232`).
- Un alias descriptivo por motor, claramente una etiqueta
  (`UNIT_LABELS` en `app/ui_data_loader.py:101`).

**No se permite** (y cualquier tarea que lo proponga está mal):

- Un modelo de avión por motor (A320neo, 737 MAX 8, A350-900).
- Una matrícula como **identidad** que implique una entidad nueva en los datos.
- Cifras económicas (150.000 € AOG / 18.000 € preventivo).
- Reglas R3, R4 o R5: no existen.

### 2.4 Cómo se dice en pantalla

Una sola línea, visible, que evita la confusión sin ser pedante:

> Cada unidad es un **motor turbofán** del dataset N-CMAPSS DS02. La matrícula es
> una etiqueta de visualización; los datos son los de la caché congelada.

---

## 3. La experiencia: cinco salas

El usuario no recorre cinco pestañas de ingeniería. Recorre **cinco salas de un
hangar**, en el orden en que le vienen las preguntas.

```
   entra
     │
     ▼
 ┌─────────────┐   pulsa una tarjeta   ┌─────────────┐
 │ 1 El tablero │ ────────────────────► │ 2 El gemelo  │
 │  ¿qué pasa?  │ ◄──────────────────── │  ¿por qué?   │
 └──────┬──────┘      vuelve             └─────────────┘
        │
        │ trae motores
        ▼
 ┌─────────────┐   mueve la política   ┌─────────────┐
 │ 4 Incorporar │ ◄─────────────────── │ 3 El taller  │
 │  uno o doce  │ ───────────────────► │ ¿y si...?    │
 └─────────────┘                       └─────────────┘
        │
        ▼
 ┌─────────────┐
 │ 5 Auditoría  │  (si pregunta un tribunal)
 └─────────────┘
```

### 3.1 Sala 1 — El tablero

**Pregunta que responde:** ¿qué está pasando en el hangar?

Es el estado de aterrizaje. Lo primero que ve un usuario nuevo.

- **Cabecera:** 3 métricas (unidades monitorizadas, unidades en hangar, MAE en zona
  crítica) y la frase del límite inferior. Ya existe (C3, `app/dashboard_ds02.py:463`).
- **Muro de tarjetas:** una tarjeta por motor. Cada tarjeta es
  `st.container(border=True)` dentro de una rejilla de 3 columnas:
  - Matrícula / etiqueta.
  - Estado (verde / ámbar / rojo, con los colores del tema).
  - RUL predicha y `L_inf`.
  - Sparkline de la trayectoria (Plotly pequeño, un `go.Scatter` por tarjeta).
  - Botón **"Ver gemelo"** → selecciona la unidad y lleva a la Sala 2.
- **Reloj de flota:** el slider de ciclo, envuelto en un `st.fragment` para que al
  moverlo solo se re-dibuje el tablero y no la app entera.
- **Modo demo** y **Borrar**: ya existen, se quedan.

**Por qué un muro de tarjetas y no un scatter:** un scatter de ciclos vs. estado
es una visualización **de ingeniero**. Una tarjeta por activo es lo que un
operador de un hangar reconoce al instante. Además da **pulsabilidad real**: un
botón por tarjeta es un botón Streamlit, no un evento de Plotly que no vuelve al
script.

### 3.2 Sala 2 — El gemelo

**Pregunta que responde:** ¿por qué está así este motor?

Es la consolidación de lo que hoy está repartido. Un motor, toda su verdad, sin
cambiar de pestaña.

- Gauge de RUL restante (`go.Indicator`, nativo de Plotly, sin HTML).
- Trayectoria RUL + banda conformal (hoy en la pestaña 2).
- La decisión y **qué regla la produjo** (hoy en la pestaña 1).
- Radiografía de sensores (hoy en la pestaña 3).
- Ciclo de vida del hangar y orden de trabajo (hoy en la pestaña 1).
- Cronología de estado por ciclo.

### 3.3 Sala 3 — El taller

**Pregunta que responde:** ¿qué pasa si cambio la política?

Los controles que hoy están en el sidebar pasan a una sala con **explicación**:

- Umbrales (30 / 25 por defecto).
- Interruptor del motor de reglas.
- Reloj de flota.
- Y el efecto, visible, sobre el muro y sobre la cola de mantenimiento.

El mensaje central de esta sala, que es el argumento de ADR-008:

> La decisión de inmovilizar **no** la toma la predicción. Toma el peor caso de
> la banda.

### 3.4 Sala 4 — Incorporar

**Pregunta que responde:** traigo un motor, o traigo doce.

- **Alta individual** (ya existe, C1).
- **Alta en lote** (nuevo, sección 5).
- Las tres rutas de datos ya existentes: preset de caché, pegar, CSV.

### 3.5 Sala 5 — Auditoría

Ya existe (pestaña 4). El caso Motor 14, las hipótesis refutadas, el contrato
congelado. Se queda tal cual, y gana protagonismo al ser la sala a la que se envía
a un tribunal que pregunta.

### 3.6 El principio de interacción

**Una acción, una consecuencia, visible al instante.** Ningún control puede
dejar al usuario preguntando qué acaba de pasar.

Todo control nuevo lleva un `caption` que dice **lo que hará y lo que no hará**.
El repo ya lo hace bien:

> "Decisión por límite inferior conformal, no por la predicción puntual."

Ese es el estándar.

---

## 4. Cómo se adapta a Streamlit

### 4.1 Las cuatro restricciones

| Restricción | Consecuencia | Cómo se esquiva |
|---|---|---|
| Streamlit re-ejecuta el script entero en cada interacción | Todo trabajo caro debe estar cacheado | El modelo ya vive en `st.cache_resource`; la caché parquet en `st.cache_data`. `st.fragment` aísla las zonas que cambian mucho. |
| Los gráficos de Plotly **no devuelven clics** al script | "Pulsar en el gráfico" no existe | El muro de tarjetas usa **botones reales** (`st.button`), no clics en el chart. |
| El layout es vertical por defecto | Hay que componer con columnas | `st.columns` + `st.container(border=True)`. Sin CSS (G2). |
| Todo gráfico y tabla necesita `alt=` | No es opcional | Es un test, no una convención: `tests/test_dss_ui.py:260`. |

### 4.2 Primitivas disponibles y verificadas

Comprobado en Streamlit 1.66.0 instalado en el repo:

```
st.fragment       st.pills        st.popover      st.dialog
st.toast          st.status       st.progress     st.metric
st.container      st.data_editor  st.file_uploader st.download_button
```

Todas están. No hace falta subir de versión ni añadir dependencias.

### 4.3 Qué aporta cada una a este plan

| Primitiva | Uso en este plan |
|---|---|
| `st.fragment` | El reloj de flota y el muro se re-dibujan sin re-ejecutar la app entera. Es la mejora de sensación más grande y barata. |
| `st.pills` | El selector de "sala" o de motor, más legible que un `selectbox`. |
| `st.progress` | El lote muestra progreso real en vez de un spinner. |
| `st.status` | El estado del lote ("puntuando 3 de 12") sin bloques de texto. |
| `st.toast` | Feedback que no empuja el contenido. Sustituye a varios `st.success`. |
| `st.popover` | Controles secundarios sin ensuciar la sala. |
| `st.dialog` | Confirmaciones ("¿borrar los gemelos?") sin navegación. |
| `st.container(border=True)` | La tarjeta nativa. Es la **única** forma de tarjeta compatible con G2. |

### 4.4 Lo que **no** se hace

- **No se inyecta CSS.** Las tarjetas son `st.container(border=True)` + `st.metric`.
  Un solo `unsafe_allow_html` rompe `tests/test_dss_ui.py:292`.
- **No se reordenan las pestañas a capricho.** El test existente
  (`tests/test_dss_ui.py:252`) exige 5 tabs y que haya etiquetas con "Hangar",
  "Motor 14" y "Evaluar". El reordenamiento de este plan las conserva.
- **No se carga el modelo para dibujar la UI.** Todo lo que sale de la caché se
  dibuja sin TensorFlow.

---

## 5. La capacidad nueva: incorporar en lote

Esta es la feature que el usuario pidió y que no existe.

### 5.1 Qué es

Un operador trae **N motores** (los que sean), la app los puntúa todos de una
vez, y devuelve una tabla de triaje: uno por motor, con su predicción, su banda,
su estado y su orden de trabajo. Nada más.

### 5.2 Qué **no** es

No reentrena. No toca la caché. No inventa ground truth. No inventa un RMSE para
unos datos que no lo tienen.

### 5.3 Módulo nuevo: `app/ui_batch.py` (puro, sin Streamlit)

Misma convención que `app/twin.py`, `app/hangar.py` y `app/ui_alta.py`: no
importa Streamlit, para poder probarlo sin levantar la app.

```
MAX_MOTORES_LOTE = 25          # tope duro, por memoria del portátil

def bloques_de_csv(texto) -> list[dict]
    """CSV con columna `unit_id` que separa bloques. Cada bloque >= 50 filas."""

def bloques_de_archivos(archivos) -> list[dict]
    """Varios CSV subidos a la vez, cada uno un motor."""

def validar_bloque(bloque) -> dict
    """Preflight reutilizando ui_inference.preflight: un solo validador."""

def puntuar_bloque(bloque, motor) -> pd.DataFrame
    """Una fila: matrícula, ciclo final, pred, lower, upper."""

def puntuar_lote(bloques, umbrales, motor) -> pd.DataFrame
    """N motores -> N filas con su estado decidido."""

def resumen_lote(resultado) -> dict
    """Cuántos por estado, para los KPIs del lote."""

def excede_limite(n) -> bool
    """True si n > MAX_MOTORES_LOTE."""
```

**Regla dura: el lote reutiliza el validador de `app/ui_inference.py`, no crea un
segundo.** Si crea un segundo validador, el cambio está mal (mismo argumento que
el plan de pulido usó para C1).

### 5.4 La interfaz

En la Sala 4:

1. **Entrada:** `st.file_uploader` (CSV múltiple) o un área de texto con N bloques.
   La plantilla CSV ya existe y se descarga desde `app/ui_inference.py`.
2. **Progreso:** `st.progress` + `st.status` con el conteo real
   ("puntuando 3 de 12").
3. **Resultado:** `st.dataframe` ordenable y filtrable, con `alt=` no vacío.
   Columnas: matrícula, ciclo, RUL predicha, `L_inf`, estado.
4. **Exportación:** `st.download_button` con la orden de trabajo, misma forma que
   la que ya existe en `app/ui_data_loader.py`.
5. **Registro:** botón "Registrar gemelos" que guarda los N gemelos de una vez y
   lleva al tablero.

### 5.5 Honestidad del lote

Los datos los aporta el usuario: **no hay ground truth**. La tabla del lote
declara eso explícitamente y **no muestra** RMSE, MAE ni "RUL real". Muestra
predicción y banda, y dice de dónde sale:

> Predicción del artefacto congelado (`models/ds02_manifest.json`) sobre los
> datos aportados. Sin ground truth: no hay error que reportar.

### 5.6 Tope de motores

`MAX_MOTORES_LOTE = 25`. Cada motor son ~50 filas y una llamada al modelo; 25 es
interactivo en un portátil, 250 no lo es. El tope se aplica con un aviso claro, no
con un fallo silencioso.

---

## 6. Fases y tareas

### Fase 0 — Cerrar lo que está a medias

**Prerrequisito de todo lo demás.** Hay 204 líneas sin commitear.

- Revisar el diff de `app/dashboard_ds02.py`.
- Revisar `app/ui_alta.py` y `tests/test_ui_alta.py`.
- Confirmar que los 8 guards siguen verdes.
- Commitar.

**Por qué primero:** no se construye sobre arena. Si el diff tiene un error, es
mejor encontrarlo ahora, con 152 tests, que después de añadir tres fases encima.

**Riesgo:** nulo, es trabajo ya verificado.

### Fase 1 — El tablero

- Muro de tarjetas con botón por tarjeta.
- Onboarding movido aquí como estado inicial.
- `st.fragment` para el reloj y el muro.
- Feedback con `st.toast` donde hoy hay `st.success` en bloque.

**Ficheros:** `app/dashboard_ds02.py`.

**Verificación:** test de que el muro tiene una tarjeta por unidad; test de que
pulsar una tarjeta cambia la unidad seleccionada; el test de tabs sigue verde.

**Riesgo:** bajo.

### Fase 2 — Incorporar en lote

- `app/ui_batch.py` (puro).
- UI en la Sala 4 con progreso, tabla ordenable y exportación.
- Testeos del módulo puro y de la UI con `AppTest`.

**Ficheros:** `app/ui_batch.py` (nuevo), `app/dashboard_ds02.py`,
`tests/test_ui_batch.py` (nuevo).

**Verificación:** test de que N bloques producen N filas; test de que un bloque
con menos de 50 filas se rechaza; test de que el tope se aplica con aviso; test de
que el lote no muestra ground truth; `pytest tests -q`.

**Riesgo:** medio. Es la única fase que llama al modelo en un bucle.

### Fase 3 — El gemelo

- Consolidar la vista por motor (RUL + banda + decisión + regla + sensores +
  ciclo de vida).
- Gauge con `go.Indicator`.

**Ficheros:** `app/dashboard_ds02.py`.

**Verificación:** test de que la sala muestra la regla que produjo la decisión;
test de que el gauge tiene `alt`; `pytest tests -q`.

**Riesgo:** bajo. Es mover código que ya existe.

### Fase 4 — El taller

- Subir los controles de política a una sala con explicación.
- Conectar el efecto sobre el muro y la cola.

**Ficheros:** `app/dashboard_ds02.py`.

**Verificación:** test de que mover un umbral cambia la cola; test de que la
decisión no cambia de agregación; `pytest tests -q`.

**Riesgo:** bajo.

### Fase 5 — Mejoras de experiencia

- **Modo historia:** una secuencia de estados que cuenta la narrativa. Es la
  extensión natural de C2 y la mejora de mayor valor para una demo en directo:

  | Paso | Estado que deja | Qué se cuenta |
  |---|---|---|
  | 1. El hangar esta mañana | ciclo 1, umbrales 30/25 | Toda la flota en verde. |
  | 2. El motor problemático | U14, ciclo 8 | Primera inspección. |
  | 3. La decisión difícil | U14, ciclo 29 | HANGAR con 47 ciclos de vida real restante. |
  | 4. ¿Y si aflojamos la política? | umbrales 35/20 | Cómo cambia la flota. |

- **Comparador:** seleccionar 2–3 motores y superponer sus trayectorias.
- **Registro de sesión:** un log de lo que el usuario ha hecho, visible y exportable.

**Ficheros:** `app/dashboard_ds02.py`, `app/ui_alta.py` (para el modo historia).

**Verificación:** test de que cada paso del modo historia deja el estado que
declara; `pytest tests -q`.

**Riesgo:** bajo.

---

## 7. Rechazado explícitamente

Cada rechazo tiene su medición o su regla que lo sostiene.

### R1 — "Hangar de aviones" con modelo de avión por motor

**Rechazado.** El dataset tiene **tres motores turbofán**. Un A320neo, un 737 MAX 8
y un A350-900 son tres variantes de un mismo motor; este dataset tiene **un solo
turbofán**. Presentar cada motor como un modelo de avión distinto es una afirmación
que el dataset no sostiene, y es exactamente lo que un tribunal técnico detecta en
un minuto. Ya rechazado en `planStreamlit.md` §4 R9 y R8.

### R2 — Métricas del lote inventadas

**Rechazado.** Los datos los aporta el usuario: no hay ground truth. Mostrar un
RMSE o un MAE para el lote sería inventar un número. El lote muestra predicción y
banda, y dice que no hay error que reportar.

### R3 — Un validador nuevo para el lote

**Rechazado.** `app/ui_inference.py` ya tiene el validador. Un segundo validador
para el lote es un segundo sitio donde arreglar el mismo bug, y el plan de pulido
ya marcó ese error como "el cambio está mal si ocurre".

### R4 — Perturbación de sensores para forzar la salida

**Rechazado de plano.** Fabricar datos para controlar la salida del modelo es lo
único que ataca directamente el activo principal del proyecto ante un tribunal
(G7). La perturbación se hace **eligiendo el ciclo de la caché**, nunca tocando
los sensores.

### R5 — Slider de avance por avión

**Rechazado.** Existe un único reloj de flota y es deliberado: es el calendario
compartido, lo usan las órdenes de trabajo y `app/hangar.py`, y clampa las unidades
cortas en vez de extrapolarlas. Ya rechazado en `planStreamlit.md` §4 R6.

### R6 — SVG del motor dentro de `app/twin.py`

**Rechazado.** `app/twin.py` es el modelo de datos de los gemelos, no un
renderizador. Ya rechazado en `planStreamlit.md` §4 R7. Si se quiere un esquema,
va en un módulo nuevo y como imagen (`st.image`), nunca como HTML crudo.

---

## 8. Verificación

### 8.1 Comandos

```bash
# suite completa
pytest tests -q

# solo lo nuevo
pytest tests/test_ui_batch.py -v
pytest tests/test_ui_alta.py -v
pytest tests/test_dss_ui.py -v

# la app arranca sin excepción y los 5 tabs están
./.venv/Scripts/python.exe -c "
from streamlit.testing.v1 import AppTest
app = AppTest.from_file('app/dashboard_ds02.py', default_timeout=180)
app.run()
print('excepcion:', app.exception)
print('tabs:', len(app.tabs))
"
```

### 8.2 Guards que deben seguir verdes

| Test | Qué impide |
|---|---|
| `tests/test_dss_ui.py:292` `test_no_css_is_injected_into_the_app` | cualquier tarjeta con CSS crudo (G2) |
| `tests/test_dss_ui.py:260` `test_every_chart_and_grid_has_an_accessible_name` | gráficos nuevos sin `alt` (G3) |
| `tests/test_dss_ui.py:216` `test_reading_the_ui_leaves_the_frozen_artifacts_untouched` | escribir en `models/` (G1) |
| `tests/test_dss_ui.py:51` `test_airworthy_state_is_reachable_on_this_band` | cambiar los umbrales (G5) |
| `tests/test_dss_ui.py:114` `test_metrics_are_recomputed_from_the_cache` | hardcodear métricas (G4) |
| `tests/test_dss_ui.py:252` `test_app_renders_headless_without_exception` | perder un tab o su etiqueta |
| `tests/test_dss_ui.py:299` `test_the_cycle_slider_drives_the_grounded_kpi` | romper el reloj de flota (R5) |

### 8.3 Cómo reproducir las cifras de este plan

```bash
# Conteos y ciclos puntuados por unidad
./.venv/Scripts/python.exe -c "
import pandas as pd
w = pd.read_parquet('app/cache/ds02_windows.parquet')
for u,g in w.groupby('unit'):
    print(f'U{u}: ciclos {int(g.cycle.min())}..{int(g.cycle.max())}  ventanas={len(g)}')
"

# Transiciones de estado con umbrales 30/25
./.venv/Scripts/python.exe -c "
import pandas as pd
w = pd.read_parquet('app/cache/ds02_windows.parquet')
idx = w.groupby(['unit','cycle'])['lower'].idxmin()
pc = w.loc[idx,['unit','cycle','lower']].sort_values(['unit','cycle'])
def banda(v): return 'APTO' if v>=30 else ('INSPECCION' if v>=25 else 'HANGAR')
for u,g in pc.groupby('unit'):
    g=g.reset_index(drop=True); b=g['lower'].map(banda)
    s=g[b!=b.shift()].assign(s=b)
    print(f'U{u}:', [f'c{int(r.cycle)}->{r.s}' for r in s.itertuples()])
"
```

Resultado esperado:

```
U11: ciclos 1..59  ventanas=3293
U14: ciclos 3..76  ventanas=760
U15: ciclos 2..67  ventanas=2143

U11: ['c1->APTO','c6->INSPECCION','c8->APTO','c9->INSPECCION','c17->APTO','c20->INSPECCION','c22->HANGAR']
U14: ['c3->APTO','c8->INSPECCION','c14->APTO','c20->INSPECCION','c29->HANGAR']
U15: ['c2->APTO','c9->INSPECCION','c16->APTO','c18->INSPECCION','c25->HANGAR']
```

Si cualquiera de estos números sale distinto, el repo ha cambiado y este plan
queda desactualizado: **no se ejecuta hasta recalcularlo.**

---

## 9. Riesgos y preguntas abiertas

**Riesgos.**

1. **Fase 2 es la única con riesgo real.** Puntuar N motores en un bucle puede
   saturar un portátil. Mitigación: el tope de 25, la barra de progreso y el
   modelo en `st.cache_resource` (ya está).
2. **El muro de tarjetas no escala a flotas grandes.** Si el usuario incorpora
   25 motores, un muro de 25 tarjetas es un muro de 25 tarjetas: ilegible.
   Mitigación: el muro muestra las unidades de caché y las de alta **ordenadas
   por estado** (primero las rojas), y el resto queda en la tabla.
3. **`st.fragment` es una primitiva moderna.** Si `AppTest` no lo exercise bien,
   los tests de interacción del reloj pueden quedar cojos. Mitigación: probarlo
   en la Fase 1, que es la primera, y desecharlo si el harness no lo soporta.
4. **El modo historia fija estados por medición concreta.** Igual que C2 con el
   ciclo 29, si la caché se regenera, el paso 3 deja de ser cierto. Mitigación:
   los pasos se derivan con una función pura (`estado_historia()` en
   `app/ui_alta.py`), no de constantes esparcidas.

**Preguntas abiertas.**

1. **¿La audiencia es tribunal académico, mixto, o cliente MRO?** Cambia cuánto
   interesa la Sala 5 y si el encuadre "hangar de motores" necesita más o menos
   explicación.
2. **¿Quieres que el lote puntúe contra el modelo de verdad o que sea una
   simulación sobre caché?** El plan asume lo primero (el usuario trae datos). Si
   prefieres lo segundo (el usuario elige perfiles y la app simula), es más
   barato y no necesita `st.progress` real.
3. **¿El modo historia debe ser visible para el usuario final o solo para el
   presentador?** Si es solo para el presentador, puede vivir en el sidebar
   plegado; si es para todos, merece su propia sala.
4. **¿Hay que persistir la flota de alta entre recargas?** Hoy C1 la guarda en
   `session_state` y se pierde al recargar. Si debe sobrevivir, toca
   `app/twin.py` y `app/registros_flota.json`, y hay que revisar
   `tests/test_twin.py` y `tests/conftest.py`.
