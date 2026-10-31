# Descomposición ejecutable: pulido de la demo DS02

> **Para quien ejecute este documento.** Lee antes `planStreamlit.md` (misma carpeta `docs/plans/`): este
> fichero lo descompone en tareas con diseño cerrado. Ejecuta las tareas en el
> orden de la sección 2 y no te saltes los gates de la sección 8.
>
> **Para el orquestador.** El plan tenía un bloqueante de diseño en C1: el tablero
> no lee ninguna flota de `st.session_state`, así que "guarda en session_state y
> redirige a la pestaña de flota" no hacía nada. La sección 6 lo resuelve con un
> diseño concreto y verificable.

---

## 1. Reglas que no se negocian

Iguales a las del plan (`planStreamlit.md` §2). Repetidas aquí porque un ejecutor
con cero contexto no debe tener que saltar de fichero para no romper nada.

- **G1** `models/` y `src/ds02_rul/` son de solo lectura. Lo vigila
  `tests/test_dss_ui.py:216`.
- **G2** El tema vive en `.streamlit/config.toml`. **Prohibido `unsafe_allow_html`
  y `<style`.** Lo vigila `tests/test_dss_ui.py:292`. Un solo `st.markdown(..., unsafe_allow_html=True)` rompe el build.
- **G3** Cada gráfico y tabla lleva un `alt` no vacío. Lo vigila
  `tests/test_dss_ui.py:260`.
- **G4** Ninguna métrica se hardcodea: se recalculan de la caché.
- **G5** Los umbrales por defecto son 30 / 25 (ADR-008). No se cambian.
- **G6** El motor de reglas es el de `mia/reglas.py`. No se inventan reglas.
- **G7** No se fabrica telemetría ni se inyectan offsets en sensores. La
  "perturbación" es elegir un ciclo de la caché, nunca tocar los datos.

Comando de verificación de todas las tareas:

```bash
pytest tests -q
```

---

## 2. Orden y dependencias

    Tarea 0  Recortes de Clase A (OPCIONAL, fuera del plan)   sin dependencias
    Tarea 1  C2 · Modo demo en un clic                        sin dependencias
    Tarea 2  C3 · Panel de primera lectura                    sin dependencias
    Tarea 3  C1 · Formulario de alta en el sidebar             sin dependencias*
    Tarea 4  C4 · Traducción de terminología (OPCIONAL)       tras la 3

*La Tarea 3 es la única con diseño nuevo. Está resuelta en la sección 6. Las
Tareas 1 y 2 son paralelizables entre sí: tocan zonas distintas del tablero.

Orden recomendado: **0 (opcional) → 1 y 2 en paralelo → 3 → 4 (opcional).**

No se ejecuta la Tarea 4 si la 3 no está verificada, porque comparten
`UNIT_LABELS`.

---

## 3. Tarea 0 — Recortes de Clase A (OPCIONAL)

**Aviso:** esta tarea **no forma parte de `planStreamlit.md`**. Es el recorte de
código muerto identificado en el análisis previo. Es seguro y reversible, pero es
una decisión tuya, no del plan. Si la omites, pasa directamente a la Tarea 1.

**Qué se borra y por qué está verificado:**

| Fichero | Líneas | Evidencia de que sobra |
|---|---|---|
| `app/api.py` | 123 | Ningún test lo importa. Ninguna referencia en código. |
| `app/dashboard.py` | 131 | Ningún test lo importa. Duplicado de `dashboard_ds02.py`. |

**Paso 0.1 — borrar `app/api.py`**

```bash
git rm app/api.py
```

**Paso 0.2 — borrar `app/dashboard.py`**

```bash
git rm app/dashboard.py
```

**Paso 0.3 — arreglar `docker-compose.yml` (obligatorio si haces 0.1 y 0.2)**

`docker-compose.yml` tiene dos servicios que rompen al borrar esos ficheros:

- el servicio `api` (líneas 6-20) arranca `app.api:app` a través del `CMD` del
  `Dockerfile:35`;
- el servicio `dashboard` (líneas 22-36) ejecuta `streamlit run app/dashboard.py`.

Deja el fichero con un solo servicio, el del dashboard nuevo:

```yaml
# docker compose up --build
#
# La app DS02 lee app/cache/, no el HDF5: hace falta el dataset solo para
# regenerar la caché (scripts/build_ui_cache.py), no para levantar la UI.
services:
  dashboard:
    build: .
    image: ds02-rul:4.1.0
    ports:
      - "8501:8501"
    volumes:
      - ./app/cache:/app/app/cache:ro
    command: >
      streamlit run app/dashboard_ds02.py
      --server.address 0.0.0.0 --server.port 8501 --server.headless true
```

Y cambia el `CMD` del `Dockerfile:35`, que hoy arranca uvicorn:

```dockerfile
CMD ["streamlit", "run", "app/dashboard_ds02.py",
     "--server.address", "0.0.0.0", "--server.port", "8501",
     "--server.headless", "true"]
```

**Paso 0.4 — verificar**

```bash
pytest tests -q
docker compose config >/dev/null && echo "compose OK"
grep -rn "app/api\|app/dashboard\.py" --include=*.md --include=*.toml --include=*.yml . | grep -v ".venv"
```

El último comando devolverá referencias históricas en `docs/` y en
`openspec/changes/2026-10-20-ds02-honest-deployable/tasks.md`. **Es correcto que
aparezcan**: son el registro de requisitos ya cerrados, no dependencias vivas.
No se editan.

**Deuda que queda, no la pagues aquí:** `requirements.txt:21-22` fija `fastapi` y
`uvicorn`, que ya no tendrían consumidor. Quitarlos es una decisión aparte (afecta
al Dockerfile y a `pyproject.toml`) y no aporta nada a la demo. Déjalos y
anótalo en el informe.

**Gate 0:** `pytest tests -q` en verde y `docker compose config` válido.

---

## 4. Tarea 1 — C2 · Modo demo en un clic

**Objetivo.** Un botón que deja la app en el estado desde el que se cuenta la
historia, sin que el presentador recuerde tres ajustes.

**Ficheros.** Crear `app/ui_alta.py`; modificar `app/dashboard_ds02.py`.

### Paso 1.1 — crear `app/ui_alta.py` con el estado de demo

```python
"""Estado de la demo y alta rápida de aeronaves (presentacional, sin inferencia).

Nada de lo que hay aquí llama al modelo ni toca `models/`: el modo demo solo
pone widgets y el alta toma ventanas ya puntuadas de la caché. Ver la sección 6
de este documento para el diseño completo del alta.
"""
from __future__ import annotations

# ADR-008: los umbrales por defecto.
UMBRAL_DEMO = (30.0, 25.0)
# U14 cruza a HANGAR en el ciclo 29 (L_inf 23,29) con 47 ciclos de RUL real
# restantes. Es el mejor argumento de la demo: no es un número al azar.
CICLO_DEMO = 29
UNIDAD_DEMO = 14


def estado_demo() -> dict:
    """Umbrales, ciclo y unidad del escenario de demo, con su porqué."""
    return {
        "umbrales": UMBRAL_DEMO,
        "ciclo": CICLO_DEMO,
        "unidad": UNIDAD_DEMO,
        "porque": (
            f"U{UNIDAD_DEMO} entra en HANGAR en el ciclo {CICLO_DEMO} con 47 ciclos "
            "de RUL real por delante: muestra la alarma conservadora y su coste."
        ),
    }
```

### Paso 1.2 — dar clave al slider de ciclo

El slider de ciclo (`app/dashboard_ds02.py:197-207`) no tiene `key=`, así que no
se puede fijar desde `session_state`. Añádela:

```python
    cycle = st.slider(
        "Ciclo de vuelo simulado",
        min_value=1,
        max_value=max_life,
        value=1,
        step=1,
        key="cycle",          # <-- nuevo: permite fijarlo desde session_state
        help=(...),
    )
```

### Paso 1.3 — botón de demo en el sidebar

Justo después del bloque de umbrales (`app/dashboard_ds02.py:240`), antes del
toggle de corrección:

```python
    st.subheader("Demo en vivo", icon=":material/movie:")
    st.caption(
        "Deja la app en el estado desde el que se cuenta la historia: umbrales "
        "30/25, ciclo 29 y la unidad 14, que es la que entra en hangar."
    )
    if st.button("Cargar escenario de demo", icon=":material/play_circle:",
                 key="demo_cargar", type="primary"):
        demo = A.estado_demo()
        st.session_state["preset"] = "Normal"
        st.session_state["th_apto_Normal"] = demo["umbrales"][0]
        st.session_state["th_aog_Normal"] = demo["umbrales"][1]
        st.session_state["unit"] = demo["unidad"]
        st.session_state["cycle"] = demo["ciclo"]
        st.rerun()
```

El import: `import ui_alta as A  # noqa: E402`, junto a los otros imports del
tablero (`app/dashboard_ds02.py:35-39`).

**Ojo con las claves.** Los `number_input` de umbrales usan
`key=f"th_apto_{preset}"` (`app/dashboard_ds02.py:227,232`). Esas son las claves
exactas que hay que escribir. El `selectbox` de preset usa `key="preset"`.

### Paso 1.4 — verificar

```bash
pytest tests -q
```

Test nuevo en `tests/test_ui_alta.py`:

```python
def test_el_estado_de_demo_es_el_medido():
    demo = A.estado_demo()
    assert demo["umbrales"] == (30.0, 25.0)
    assert demo["ciclo"] == 29
    assert demo["unidad"] == 14
```

Y un `AppTest` que compruebe que el botón fija los tres valores (sigue el patrón
de `tests/test_dss_ui.py:299`).

**Gate 1:** el botón deja umbrales 30/25, ciclo 29 y unidad 14, y el KPI de
unidades en hangar pasa a 1.

---

## 5. Tarea 2 — C3 · Panel de primera lectura

**Objetivo.** Que un visitante se lleve el mensaje antes de leer ingeniería.

**Ficheros.** Solo `app/dashboard_ds02.py`.

### Paso 2.1 — panel tras la cabecera

Insertar entre el bloque de badges (`app/dashboard_ds02.py:376-389`) y el
`st.tabs` (línea 391):

```python
with st.container(border=True):
    st.subheader("Primera lectura", icon=":material/visibility:")
    with st.container(horizontal=True):
        st.metric("Unidades monitorizadas", f"{global_metrics['units']}",
                  f"{global_metrics['windows']:,} ventanas evaluadas",
                  border=True, icon=":material/groups:", delta_color="off")
        st.metric("MAE en zona crítica", f"{critical_mae:.2f} ciclos",
                  f"RUL real < {threshold_aog:.0f}", border=True,
                  icon=":material/target:", delta_color="off")
        st.metric("Unidades en hangar", f"{grounded} / {len(snapshot)}",
                  f"en el ciclo {cycle}", border=True,
                  icon=":material/local_shipping:", delta_color="off")
    st.caption(
        "La decisión de inmovilizar no la toma la predicción del modelo: la toma "
        "el peor caso de su banda. Por eso un motor puede quedar en hangar con "
        "vida útil estimada por encima del umbral."
    )
```

**No dupliques la métrica de zona crítica.** El panel de la pestaña 1
(`app/dashboard_ds02.py:411-418`) ya la muestra con su `help` completo. El panel
nuevo la resume y la pestaña la desarrolla.

### Paso 2.2 — verificar

```bash
pytest tests -q
```

Test nuevo: las tres cifras del panel coinciden con las de la pestaña 1. Toma los
valores de `global_metrics`, `critical_mae` y `grounded` (ya calculados en
`app/dashboard_ds02.py:348-365`) y comprueba que el panel los reproduce.

**Gate 2:** el panel renderiza y sus tres cifras son las mismas que las de la
pestaña 1. `test_every_chart_and_grid_has_an_accessible_name` sigue en verde (el
panel no añade gráficos ni tablas).

---

## 6. Tarea 3 — C1 · Formulario de alta (DISEÑO RESUELTO)

Esta es la tarea con diseño nuevo. El plan la dejaba bloqueada; aquí está la
decisión tomada, con su justificación.

### 6.1 Por qué el plan no funcionaba

Tres hechos comprobados:

1. **El tablero no lee ninguna flota de `session_state`.** La pestaña de flota
   calcula `snapshot = L.fleet_snapshot(frame, cycle, ...)` (`app/dashboard_ds02.py:352`)
   y `frame` sale de la caché. Las claves de sesión que existen son `twins`,
   `hangar`, `live_*` y `twin_flash`.
2. **`fleet_snapshot` solo ve las unidades de la caché.**
   `app/ui_data_loader.py:229` recorre `windows["unit"].unique()`: solo 11, 14 y 15.
3. **No hay `unit_id` libre.** Caché = 11/14/15, evaluación en vivo = −1
   (`app/ui_inference.py:29`), gemelos = 0 (`app/twin.py:153`).

El plan decía "reutiliza la ruta de entrada existente", pero la ruta existente
(`app/dashboard_ds02.py:1432`) son tres modos de datos del **usuario** (ejemplo,
pegar, CSV) y el selector de perfil lee de la **caché**. No es la misma ruta.

### 6.2 El diseño

**Una aeronave de alta es una lectura de la caché ya puntuada, con un id
sintético.** Se toman las ventanas ya evaluadas de una unidad del test hasta un
ciclo elegido y se les asigna un `unit_id` del rango negativo reservado. No se
fabrica telemetría, no se vuelve a llamar al modelo, no se toca `models/`.

**Qué es el "ciclo elegido" y qué no.** La **historia** de la aeronave es el
prefijo (`cycle <= elegido`), pero su **estado** es el de **ese ciclo concreto**:
el mínimo `lower` de las ventanas de ese ciclo, que es lo que hace `fleet_snapshot`.
No es el peor valor de todo el prefijo. La diferencia es real y se ve en los datos:
U11 hasta el ciclo 20 tiene un mínimo de prefijo de **25,53**, pero su estado en el
ciclo 20 es **29,28**. Caen en la misma banda (INSPECCIÓN), así que el perfil sigue
siendo válido, pero si verificas con el mínimo del prefijo saldrá 25,53 y pensarás
que el documento miente. El comando de la sección 6.8 usa `cycle == ciclo`, que es
la lectura correcta.

**Regla de honestidad que lo sostiene:** las métricas globales siguen saliendo
**solo** de la caché. Contar dos veces las mismas ventanas inflaría el RMSE. Así
que hay dos frames: `frame_cache` (caché, para métricas y telemetría) y `frame`
(caché + altas, para la flota y las órdenes).

### 6.3 Paso 3.1 — `app/ui_alta.py` (ampliación)

Añade a `app/ui_alta.py`:

```python
# Rango negativo reservado: nunca colisiona con la caché (11/14/15), con la
# evaluación en vivo (-1) ni con los gemelos (0).
PREFIJO_ALTA = -1000

# Perfil -> (unidad cacheada, ciclo hasta el que se toma la historia).
#
# OJO, medido el 2026-10-22: U11 empieza en el ciclo 1, U14 en el 3 y U15 en el 2.
# Pedir un ciclo anterior al primero de una unidad no devuelve NaN: devuelve un
# recorte vacío, que `ventanas_de_alta` rechaza con ValueError. Aun así, no pongas
# un ciclo que no exista.
#
# VERIFICA la banda de cada perfil con el comando de la sección 6.8: el valor que
# aparece aquí es una referencia, no una constante de la que fiarse a ciegas.
PERFILES = {
    "Recién salido de revisión":       (11, 1),
    "Recién salido de revisión (U15)": (15, 2),
    "Desgaste operativo medio":        (11, 20),
    "Desgaste operativo medio (U14)":  (14, 20),
    "Fin de vida / crítico":           (14, 29),
    "Fin de vida / crítico (U11)":     (11, 22),
    "Caso atípico (U14)":              (14, 3),
}


def unidad_alta(indice: int) -> float:
    """Id de una aeronave de alta. Negativo y reservado: no colisiona."""
    return float(PREFIJO_ALTA - int(indice))


def ventanas_de_alta(windows: pd.DataFrame, unidad: int, ciclo_hasta: int,
                     unit_id: float) -> pd.DataFrame:
    """Ventanas ya puntuadas de `unidad` hasta `ciclo_hasta`, con id sintético.

    Se conservan `pred`/`lower`/`upper`/`y_true` tal cual están en la caché: no
    se repuntúa nada. Solo cambia `unit`, la clave de agrupación que usan
    `unit_curve` y `fleet_snapshot`.
    """
    recorte = windows[(windows["unit"] == int(unidad))
                      & (windows["cycle"] <= int(ciclo_hasta))].copy()
    if recorte.empty:
        # No es un NaN silencioso: es un recorte vacío, y se dice por qué.
        del_cache = windows[windows["unit"] == int(unidad)]
        primero = (int(del_cache["cycle"].min()) if not del_cache.empty
                  else "¿unidad inexistente?")
        raise ValueError(
            f"la unidad {unidad} no tiene ventanas hasta el ciclo {ciclo_hasta}; "
            f"su primer ciclo puntuado es el {primero}")
    recorte["unit"] = float(unit_id)
    return recorte


def frame_con_altas(frame_cache: pd.DataFrame, windows: pd.DataFrame,
                    altas: list[dict], aplicar_reglas: bool,
                    umbrales: dict) -> pd.DataFrame:
    """`frame_cache` más las aeronaves de alta, con su decisión aplicada.

    Función **pura**: no lee `session_state`, recibe `altas` como parámetro, para
    poder probarse sin levantar la app (misma convención que `twin.py` y
    `hangar.py`).

    Las métricas y la telemetría no pasan por aquí: usar `frame_cache` para
    ellas es lo que evita contar dos veces las mismas ventanas.
    """
    if not altas:
        return frame_cache
    extras = pd.concat(
        [ventanas_de_alta(windows, alta["unidad"], alta["ciclo"], alta["unit_id"])
         for alta in altas],
        ignore_index=True,
    )
    if aplicar_reglas:
        extras = UR.corregir_ventanas(extras)
    extras = UR.decidir_ventanas(extras, umbrales)
    return pd.concat([frame_cache, extras], ignore_index=True)
```

Necesitarás `import pandas as pd` y `import ui_rules as UR` en el módulo. Ambos
son puros: ninguno importa Streamlit.

### 6.4 Paso 3.2 — helpers en `app/dashboard_ds02.py`

Junto a `_cargar_registros` (`app/dashboard_ds02.py:47`):

```python
ALTA_KEY = "flota_alta"


def _altas() -> list[dict]:
    """Aeronaves de alta de esta sesión. Clave de `session_state`, sin disco."""
    return list(st.session_state.get(ALTA_KEY) or [])


def _etiqueta_unidad(unit: float) -> str:
    """Matrícula de una aeronave de alta, o la etiqueta de la caché."""
    for alta in _altas():
        if float(alta["unit_id"]) == float(unit):
            return str(alta["matricula"])
    return L.UNIT_LABELS.get(int(unit), f"Unidad {int(unit)}")
```

La lógica de composición del frame vive en `ui_alta.frame_con_altas` (pura, en el
paso 3.1); aquí solo se lee la sesión y se pone la etiqueta.

### 6.5 Paso 3.3 — preparar los dos frames

En el bloque de preparación de datos (`app/dashboard_ds02.py:342-366`), separa
la caché de la flota:

```python
umbrales = {"apto": float(threshold_apto), "hangar": float(threshold_aog)}

# `frame_cache` es solo la caché: de aquí salen las métricas y la telemetría.
# `frame` incluye las aeronaves de alta: de aquí sale la flota y las órdenes.
frame_cache = UR.corregir_ventanas(windows) if aplicar_reglas else windows
frame_cache = UR.decidir_ventanas(frame_cache, umbrales)
frame = A.frame_con_altas(frame_cache, windows, _altas(), aplicar_reglas, umbrales)

global_metrics = L.global_metrics(frame_cache)          # antes: frame
curves = {u: L.unit_curve(frame, u) for u in unidades_vistas}
alarms = {u: L.first_alarm_cycle(curves[u], threshold_aog) for u in unidades_vistas}
correccion = UR.resumen_correccion(windows, frame_cache) if aplicar_reglas else None
snapshot = L.fleet_snapshot(frame, cycle, threshold_apto, threshold_aog)
curve = curves[int(unit)]
per_unit = L.per_unit_metrics(frame_cache)
unit_metrics = per_unit[per_unit["unit"] == unit].iloc[0]
alarm_cycle, truth_cycle = alarms[int(unit)]
```

Y donde hoy se calcula `units` (`app/dashboard_ds02.py:180`):

```python
units = sorted(int(u) for u in windows["unit"].unique())
unidades_vistas = sorted(int(u) for u in frame["unit"].unique())
```

**Cuidado con `unit_metrics`.** `per_unit` se calcula sobre `frame_cache` (3
unidades). Si el usuario selecciona en el sidebar una aeronave de alta, esa fila
no existe y `per_unit[per_unit["unit"] == unit].iloc[0]` lanza `IndexError`.
Resuélvelo antes de esa línea:

```python
unit_metrics = (per_unit[per_unit["unit"] == unit].iloc[0]
                if (per_unit["unit"] == unit).any()
                else None)
```

y pinta las tarjetas de la pestaña 2 solo si `unit_metrics is not None`, con un
`st.caption` que diga que esa unidad no tiene verdad en la caché.

### 6.6 Paso 3.4 — formulario en el sidebar

Antes del bloque de umbrales (`app/dashboard_ds02.py:209`):

```python
    st.subheader("Alta rápida", icon=":material/library_add:")
    st.caption(
        "Incorpora una aeronave usando telemetría ya evaluada de la caché. No se "
        "llama al modelo: es una lectura distinta de los mismos datos."
    )
    with st.form("alta_avion"):
        matricula = st.text_input(
            "Matrícula", key="alta_matricula", value="",
            help="Etiqueta de visualización. Mínimo 3 caracteres.",
        )
        perfil = st.selectbox("Perfil de desgaste", list(A.PERFILES), key="alta_perfil")
        enviar = st.form_submit_button("Incorporar unidad",
                                       icon=":material/add_circle:", type="primary")
    if enviar:
        try:
            limpia = T.normalizar_id(matricula)
        except ValueError as exc:
            st.error(str(exc), title="Matrícula no válida", icon=":material/rule:")
        else:
            unidad, ciclo = A.PERFILES[perfil]
            altas = _altas()
            altas.append({
                "matricula": limpia,
                "unidad": unidad,
                "ciclo": ciclo,
                "unit_id": A.unidad_alta(len(altas)),
            })
            st.session_state[ALTA_KEY] = altas
            st.session_state["unit"] = int(A.unidad_alta(len(altas) - 1))
            st.session_state["twin_flash"] = (
                f"Aeronave `{limpia}` incorporada (U{unidad} hasta el ciclo {ciclo}).")
            st.rerun()

    with st.expander("Quitar aeronaves de alta", icon=":material/remove_circle:"):
        altas = _altas()
        if not altas:
            st.caption("Ninguna aeronave de alta en esta sesión.")
        else:
            a_quitar = st.selectbox(
                "Aeronave", [alta["matricula"] for alta in altas], key="alta_quitar")
            if st.button("Quitar", icon=":material/delete:", key="alta_quitar_btn"):
                st.session_state[ALTA_KEY] = [
                    alta for alta in altas if alta["matricula"] != a_quitar]
                st.rerun()
```

**Nota sobre persistencia.** El alta vive en `session_state`: recargar la página
lo pierde. Eso es deliberado (la demo no necesita que sobreviva) y **no** es un
bug. Persistirlo significaría extender `app/twin.py` y
`app/registros_flota.json`, que es otra tarea.

### 6.7 Paso 3.5 — que se vea en la flota

Tres sitios necesitan la etiqueta en vez del id:

1. **Cola de mantenimiento** (`app/dashboard_ds02.py:505-508`): la columna `"Motor"`
   hoy es `f"U{int(u)}"`. Cámbiala por `_etiqueta_unidad(u)`.
2. **Selector de unidad del sidebar** (`app/dashboard_ds02.py:186-195`): ofrece
   `unidades_vistas` en vez de `units`, y usa un `format_func` que devuelva
   `_etiqueta_unidad(u)`.
3. **Cronología de flota** (`app/dashboard_ds02.py:451-453`): la columna `"unidad"`
   es `f"U{u}"`. Usa `_etiqueta_unidad(u)` para que el eje muestre la matrícula.

### 6.8 Paso 3.6 — verificar

```bash
pytest tests -q
```

Test nuevo en `tests/test_ui_alta.py`. Ojo: **no importes `dashboard_ds02`** en un
test unitario — importarlo ejecuta la app. Prueba la función pura:

```python
import ui_alta as A
import ui_data_loader as L


def test_una_aeronave_de_alta_entra_en_la_flota():
    windows = L.get_windows()
    altas = [{"matricula": "EC-MKR", "unidad": 11, "ciclo": 22,
              "unit_id": A.unidad_alta(0)}]
    frame = A.frame_con_altas(windows, windows, altas, False,
                              {"apto": 30.0, "hangar": 25.0})
    snapshot = L.fleet_snapshot(frame, 22, 30.0, 25.0)
    assert int(A.unidad_alta(0)) in set(snapshot["unit"])
    # La aeronave de alta está en HANGAR: U11 cruza a 25 en el ciclo 22.
    fila = snapshot[snapshot["unit"] == int(A.unidad_alta(0))].iloc[0]
    assert fila["state"] == L.AOG
```

El comportamiento de la UI (que la matrícula se vea en la cola) se comprueba con
`AppTest`, como en `tests/test_dss_ui.py:299`. La clave de sesión es la literal
`"flota_alta"` (constante `ALTA_KEY` del tablero); al usar `AppTest` se inyecta en
`app.session_state`.

Y la comprobación de bandas de los perfiles:

```bash
./.venv/Scripts/python.exe -c "
import pandas as pd
w = pd.read_parquet('app/cache/ds02_windows.parquet')
print('primer ciclo por unidad:')
for u in (11, 14, 15):
    print(f'  U{u}: ciclo {int(w[w.unit==u].cycle.min())}')
print()
for nombre,(u,ciclo) in {
  'Recien salido de revision':(11,1),
  'Desgaste operativo medio':(11,20),
  'Fin de vida / critico':(14,29),
  'Caso atipico (U14)':(14,3)}.items():
    sub = w[(w.unit==u)&(w.cycle==ciclo)]
    lo = float(sub['lower'].min())
    estado = 'APTO' if lo>=30 else ('INSPECCION' if lo>=25 else 'HANGAR')
    print(f'{nombre:28s} U{u} ciclo {ciclo:3d}  L_inf={lo:6.2f}  -> {estado}')
"
```

Salida esperada (verificada el 2026-10-22):

```
primer ciclo por unidad:
  U11: ciclo 1
  U14: ciclo 3
  U15: ciclo 2

Recien salido de revision     U11 ciclo   1  L_inf= 35.41  -> APTO
Desgaste operativo medio      U11 ciclo  20  L_inf= 29.28  -> INSPECCION
Fin de vida / critico         U14 ciclo  29  L_inf= 23.29  -> HANGAR
Caso atipico (U14)            U14 ciclo   3  L_inf= 32.43  -> APTO
```

**Este comando cazó un error del plan original.** La primera versión ponía
`Caso atípico (U14)` en el ciclo 1 con `L_inf` 32,43. Ese valor es real, pero
pertenece al **ciclo 3**: U14 no tiene ventanas en los ciclos 1 ni 2. Corregido
en el plan y en el `PERFILES` de arriba.

**Gate 3:** una aeronave de alta aparece en la cola de mantenimiento con su
matrícula, con el estado que le corresponde, y las métricas globales de la
pestaña 1 **no** cambian al añadirla.

---

## 7. Tarea 4 — C4 · Traducción de terminología (OPCIONAL)

**Aviso:** es cosmética y es la única tarea con riesgo de credibilidad. El repo es
deliberado al no inventar entidades: la caché tiene **tres motores**, no aviones.

**Regla de aceptación.** Se permite un **alias de visualización**
(`Motor DS02-11`). **No** se permite: un modelo de avión por motor, una matrícula
inventada como identidad, ni cifras económicas.

**Ficheros.** `app/ui_data_loader.py:101-105` (`UNIT_LABELS`) y las cadenas de
`app/dashboard_ds02.py`. No toca las columnas de la caché ni `mia/`.

**Paso 4.1.** Cambia `UNIT_LABELS` por etiquetas de una sola línea:

```python
UNIT_LABELS = {
    11: "Motor DS02-11 · degradación estándar",
    14: "Motor DS02-14 · caso atípico",
    15: "Motor DS02-15 · degradación nominal",
}
```

**Paso 4.2 — verificar.**

```bash
pytest tests -q
```

Test: el recuento de unidades y los `unit_id` de la caché no cambian.

**Gate 4:** las métricas y los ids de la caché son idénticos; solo cambian las
etiquetas.

---

## 8. Gates de revisión

Entre tareas, para. Un gate en rojo detiene la cadena.

| Gate |Tras la tarea | Comprobación |
|---|---|---|
| 0 | Tarea 0 | `pytest tests -q` y `docker compose config` válido |
| 1 | Tarea 1 | el botón deja 30/25, ciclo 29, unidad 14 |
| 2 | Tarea 2 | las tres cifras coinciden con la pestaña 1 |
| 3 | Tarea 3 | la aeronave entra en la flota y las métricas no cambian |
| 4 | Tarea 4 | los ids de la caché no cambian |

**Tras cada gate, reportar:** ficheros tocados, tests nuevos, salida de
`pytest tests -q`, y cualquier desviación del diseño. No seguir si un gate falla.

---

## 9. Notas para el ejecutor

**Lo que NO encontrarás en el plan y sí importa:**

- El plan decía que C1 "reutiliza la ruta de entrada existente". No es cierto: la
  ruta existente pide datos al usuario y el alta lee de la caché. La sección 6.2
  es el diseño correcto.
- El plan dejaba abierta la persistencia del alta. Decisión: `session_state`, sin
  persistir. Recargar pierde las altas y eso es correcto.
- Los valores de `PERFILES` son una referencia. **Verifícalos** con el comando de
  la sección 6.8 antes de confiar en ellos: si la caché se regenera, cambian.

**Riesgos:**

1. **`IndexError` al seleccionar una aeronave de alta en el sidebar.** Resuelto en
   el paso 3.3; si se te olvida, la app revienta al cambiar de unidad.
2. **Inflar las métricas.** Si usas `frame` en vez de `frame_cache` para
   `global_metrics`, el RMSE cambia al añadir aeronaves. Es el error más fácil de
   cometer y el más caro.
3. **El `alt` de los gráficos.** Los gráficos de la cronología y del RUL ya llevan
   `alt`; si los regeneras, mantenlo o rompe el test de accesibilidad.
4. **Claves de widgets.** `st.session_state["cycle"]` solo funciona si el slider
   tiene `key="cycle"`. Sin eso, el modo demo no hace nada y parece que el botón
   está roto.

**Fuera de alcance:** tocar `app/ui_inference.py`, `app/ui_data_loader.py` (salvo
`UNIT_LABELS` en la Tarea 4), `app/cache/`, `models/`, `src/` o `mia/`.
