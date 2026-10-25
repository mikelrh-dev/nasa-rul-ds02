"""DS02 maintenance decision-support surface.

    streamlit run app/dashboard_ds02.py

Five tabs over one cached frame: fleet hangar, RUL with its conformal band,
physical sensor radiography, the engine-14 audit, and the live evaluation of a
unit you bring. Everything is read from `app/cache/` (see
`scripts/build_ui_cache.py`) and `models/ds02_manifest.json`; the frozen bundle is
never loaded, so no TensorFlow import is needed and the app runs from a laptop
without the 2.3 GB HDF5.

Both rule passes run through `mia/`: the correction pass (R2b + R6) behind the
opt-in toggle, and the decision pass (R1, R9, R8, R7) on every render. The
maintenance state is therefore the engine's answer, decided on the conformal
LOWER bound and not on the point estimate. Thresholds are ADR-008's 30 / 25 and
are adjustable in the sidebar.

Colors, fonts and radii live in `.streamlit/config.toml`; the Plotly figures use
the same tokens so the charts sit on the same surface as the widgets.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import hangar as HGR  # noqa: E402
import twin as T  # noqa: E402
import ui_alta as A  # noqa: E402
import ui_batch as B  # noqa: E402
import ui_data_loader as L  # noqa: E402
import ui_inference as INF  # noqa: E402
import ui_rules as UR  # noqa: E402
import flota as F  # noqa: E402
import simulacion as S  # noqa: E402

# Estado de sesión en un solo sitio: gemelos y registros de hangar.
# Se cargan de disco una sola vez: recargar la página ya no borra la flota.
_REGISTROS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "registros_flota.json")


def _cargar_registros() -> None:
    if not st.session_state.get("_registros_cargados"):
        disco: dict = {}
        try:
            if os.path.exists(_REGISTROS_PATH):
                with open(_REGISTROS_PATH, encoding="utf-8") as _fh:
                    disco = json.load(_fh)
        except (OSError, ValueError):
            disco = {}
        st.session_state.setdefault("twins", dict(disco.get("twins", {})))
        st.session_state.setdefault("hangar", dict(disco.get("hangar", {})))
        # El alta viaja en el mismo JSON. Antes vivia solo en `session_state`
        # y desaparecia al recargar: el motor se perdia y el usuario creia
        # haber hecho algo mal.
        st.session_state.setdefault(F.ALTAS_KEY, dict(disco.get(F.ALTAS_KEY, {})))
        st.session_state["_registros_cargados"] = True


def _guardar_registros() -> None:
    try:
        with open(_REGISTROS_PATH, "w", encoding="utf-8") as _fh:
            json.dump({"twins": st.session_state.get("twins", {}),
                       "hangar": st.session_state.get("hangar", {}),
                       F.ALTAS_KEY: st.session_state.get(F.ALTAS_KEY, {})},
                      _fh, ensure_ascii=False, indent=1)
    except OSError:
        pass


_cargar_registros()


def _altas() -> list[dict]:
    """Aeronaves de alta del registro persistido, en la forma que consume la app.

    El registro guarda el motor de origen como `unidad_cache` (la palabra
    `unidad` sola se presta a confundirla con el unit_id). `frame_con_altas`
    espera `unidad`, asi que el nombre se traduce aqui, en la frontera, y no en
    cada llamador.
    """
    altas = st.session_state.get(F.ALTAS_KEY) or {}
    return [
        {"matricula": clave,
         "unidad": alta.get("unidad_cache", 0),
         "ciclo": alta.get("ciclo", 0),
         "unit_id": alta.get("unit_id", 0.0),
         "indice": alta.get("indice", 0)}
        for clave, alta in altas.items()
    ]


def _registro() -> dict:
    """Registro completo de la sesion: gemelos, hangar y altas.

    Se pasa entero a las funciones puras de `flota` para que resuelvan la clave
    de un motor sin que el llamador monte el diccionario a mano en cada sitio.
    """
    return {
        "twins": st.session_state.get("twins", {}),
        "hangar": st.session_state.get("hangar", {}),
        F.ALTAS_KEY: st.session_state.get(F.ALTAS_KEY) or {},
    }


def _etiqueta_unidad(unit: float) -> str:
    """Etiqueta de un motor, desde el registro unico."""
    return F.etiqueta(F.clave_de(float(unit), _registro()))


def _slug_motor(nombre) -> str:
    """Clave de widget segura a partir del nombre de un motor.

    El id lo escribe el usuario: un espacio o una barra en el nombre romperia la
    clave de un boton o el nombre de un fichero. Conserva las mayusculas (la
    matricula es lo que el operador reconoce) y solo sustituye lo que no vale.
    """
    return "".join(c if c.isalnum() or c in "-_" else "_" for c in str(nombre))


def _mostrar_toast_pendiente() -> None:
    """Toast diferido: un handler lo pide y se pinta en la siguiente pasada.

    `st.toast` no empuja el contenido hacia abajo como un `st.success` en bloque,
    y se puede pedir desde cualquier handler sin reordenar la página.
    """
    mensaje = st.session_state.pop("_toast_pendiente", None)
    if mensaje:
        st.toast(mensaje, icon=":material/info:")


def _log(mensaje: str) -> None:
    """Registro de sesión: qué ha hecho el usuario, con cuándo.

    Se alimenta en cada acción discreta (alta, escenario, paso de historia, lote,
    gemelos). No registra cada rerender: solo lo que el usuario hizo.
    """
    log = list(st.session_state.get("_sesion_log") or [])
    log.append({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "que": str(mensaje),
    })
    st.session_state["_sesion_log"] = log


def _preflight_panel(pf: dict) -> None:
    """Resumen del pre-vuelo: lo que se sabe sin cargar el modelo.

    Se pinta antes de pulsar «Evaluar» para que un CSV mal formado se vea en
    milisegundos y no después de cargar TensorFlow.
    """
    if not pf["ok"]:
        st.error(pf["error"], title="La tabla no se puede puntuar",
                 icon=":material/rule:")
        return
    with st.container(horizontal=True):
        st.metric("Filas", f"{pf['filas']:,}", border=True, delta_color="off",
                  icon=":material/table_rows:")
        st.metric("Ventanas", f"{pf['ventanas']:,}", border=True, delta_color="off",
                  icon=":material/layers:")
        st.metric("Huella", pf["fingerprint"][:8], "SHA-256 de la tabla",
                  border=True, delta_color="off", icon=":material/fingerprint:")
    for aviso in pf["avisos"]:
        st.warning(aviso, icon=":material/find_in_page:")

# ---------------------------------------------------------------- design tokens
INK = "#e8eef7"
MUTED = "#93a4bd"
GRID = "#22304a"
SURFACE = "#141d2e"
SKY = "#38bdf8"
AMBER = "#f59e0b"
GREEN = "#34d399"
ROSE = "#f87171"
SLATE = "#64748b"

STATE_COLORS = {
    L.AIRWORTHY: GREEN,
    L.PREVENTIVE: AMBER,
    L.AOG: ROSE,
    L.NO_DATA: SLATE,
    L.SIN_DECISION: SLATE,
}
STATE_BG = {
    L.AIRWORTHY: "background-color: rgba(52, 211, 153, 0.14)",
    L.PREVENTIVE: "background-color: rgba(245, 158, 11, 0.14)",
    L.AOG: "background-color: rgba(248, 113, 113, 0.14)",
    L.NO_DATA: "background-color: rgba(100, 116, 139, 0.14)",
    L.SIN_DECISION: "background-color: rgba(148, 163, 184, 0.18)",
}
STATE_WORD = {
    L.AIRWORTHY: "apto",
    L.PREVENTIVE: "inspección",
    L.AOG: "hangar",
    L.NO_DATA: "sin datos",
    L.SIN_DECISION: "sin decisión",
}
# Qué tarjeta manda en el muro: una en hangar se atiende antes que una en
# inspección. Es el orden por defecto del muro y el de las órdenes.
RANGO_ESTADO = {
    L.AOG: 0,
    L.PREVENTIVE: 1,
    L.AIRWORTHY: 2,
    L.NO_DATA: 3,
    L.SIN_DECISION: 4,
}
BADGE_COLOR = {
    L.AIRWORTHY: "green",
    L.PREVENTIVE: "orange",
    L.AOG: "red",
    L.NO_DATA: "gray",
    L.SIN_DECISION: "gray",
}
BADGE_ICON = {
    L.AIRWORTHY: ":material/check_circle:",
    L.PREVENTIVE: ":material/schedule:",
    L.AOG: ":material/warning:",
    L.NO_DATA: ":material/hourglass_empty:",
    L.SIN_DECISION: ":material/block:",
}


def chart_layout(**overrides) -> dict:
    """Shared Plotly layout: transparent surface, themed axes, top legend."""
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=INK, size=13),
        margin=dict(l=8, r=8, t=44, b=8),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=GRID, font=dict(color=INK)),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED, size=12),
        ),
        hovermode="x unified",
    )
    layout.update(overrides)
    return layout


def style_axes(fig, x_title: str | None = None, y_title: str | None = None):
    fig.update_xaxes(
        showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False,
        linecolor=GRID, tickfont=dict(color=MUTED), title_font=dict(color=MUTED),
        title_text=x_title,
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False,
        linecolor=GRID, tickfont=dict(color=MUTED), title_font=dict(color=MUTED),
        title_text=y_title,
    )
    return fig


def fig_deriva(per_cycle: pd.DataFrame, channels: list[str], last_cycle: int,
               critical_start: int | None, threshold_aog: float,
               height: int = 360) -> go.Figure:
    """Deriva porcentual de los sensores frente a la línea base sana del motor.

    Extraída de la pestaña de sensores para que el gemelo la muestre sin duplicar
    el cálculo: la misma señal, el mismo baseline y la misma anotación.
    """
    baseline_cycles = 5
    baseline = per_cycle.head(baseline_cycles)[channels].mean()
    drift = (per_cycle[channels] / baseline - 1.0) * 100.0
    fig = go.Figure()
    for ch in channels:
        fig.add_trace(
            go.Scatter(
                x=per_cycle["cycle"], y=drift[ch], mode="lines",
                name=L.CHANNEL_LABELS.get(ch, ch), line=dict(width=2),
            )
        )
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    if critical_start is not None:
        fig.add_vrect(
            x0=critical_start, x1=last_cycle, fillcolor=ROSE, opacity=0.12,
            line_width=0,
            annotation_text=f"RUL real < {threshold_aog:.0f}",
            annotation_position="top right", annotation_font_size=11,
            annotation_font_color="#fca5a5",
        )
    fig.update_layout(**chart_layout(height=height, hovermode="x unified"))
    style_axes(
        fig, x_title="Ciclo de vuelo",
        y_title="variación % vs. media de los 5 primeros ciclos",
    )
    return fig


def st_badge_estado(estado: str) -> None:
    """Insignia de estado con color e icono: el color nunca viaja solo."""
    st.badge(
        L.STATE_LABELS.get(estado, str(estado)),
        icon=BADGE_ICON.get(estado, ":material/circle:"),
        color=BADGE_COLOR.get(estado, "gray"),
    )


st.set_page_config(
    page_title="DS02 · Soporte a la decisión",
    page_icon=":material/flight:",
    layout="wide",
)

if not L.cache_available():
    st.error(
        "Falta la caché de la UI en `app/cache/`. Genérala una vez con "
        "`python scripts/build_ui_cache.py`.",
        title="Caché no encontrada",
        icon=":material/database_off:",
    )
    st.stop()

windows = L.get_windows()
telemetry = L.get_rows()
provenance = L.get_provenance()
manifest = L.get_manifest()

units = sorted(int(u) for u in windows["unit"].unique())
max_life = int(windows["cycle"].max())

# La app abre con un motor ya cargado: nadie llega a una pantalla vacía.
# Semilla de sesión, nunca de disco — `tests/conftest.py` sigue aislando.
#
# No escribe `unit`: ese widget ya posee la clave y tiene su propio default
# (`_vistas[0]`). Escribirla desde aquí provoca el aviso de Streamlit sobre un
# widget con default y valor por Session State API. La marca dice que la app ya
# se sembró; el selector ya carga un motor.
if not st.session_state.get("_semilla_demo"):
    st.session_state["_semilla_demo"] = True

# ------------------------------------------------------- escrituras diferidas
# Un handler no puede escribir en la clave de un widget que ya se instanció:
# Streamlit lo prohíbe (`StreamlitWidgetAlreadyInstantiatedError`) y la app
# revienta en pantalla. La solución es dejar una bandera y aplicarla aquí, antes
# de crear los widgets: en la siguiente pasada el widget nace con el valor ya en
# `session_state`. Sin esto, «Incorporar unidad» y «Cargar escenario de demo»
# rompían la app aunque su lógica fuera correcta.
if st.session_state.get("_demo_pendiente"):
    _demo = A.estado_demo()
    st.session_state["preset"] = "Normal"
    st.session_state["th_apto_Normal"] = _demo["umbrales"][0]
    st.session_state["th_aog_Normal"] = _demo["umbrales"][1]
    st.session_state["unit"] = _demo["unidad"]
    st.session_state["cycle"] = _demo["ciclo"]
    st.session_state.pop("_demo_pendiente", None)
if st.session_state.get("_alta_pendiente") is not None:
    st.session_state["unit"] = st.session_state.pop("_alta_pendiente")
if st.session_state.get("_escenario_pendiente"):
    _u, _c = st.session_state.pop("_escenario_pendiente")
    st.session_state["unit"] = int(_u)
    st.session_state["cycle"] = int(_c)
if st.session_state.get("_avance_flota") is not None:
    st.session_state["cycle"] = int(st.session_state.pop("_avance_flota"))

# ------------------------------------------------------------- política en uso
# Los controles de política viven en la sala «El taller» (pestaña 1), pero el
# resto de la app los necesita ya calculados. Se leen de `session_state`, donde
# el widget los dejó en la pasada anterior: al cambiarlos, Streamlit escribe el
# valor nuevo antes de re-eecutar el script. No hay una segunda fuente de
# verdad: el widget escribe, este bloque lee.
_PRESETS = {
    "Normal": (0.0, 0.0),
    "Prudente (+5)": (5.0, 5.0),
    "Permisivo (−5)": (-5.0, -5.0),
}
preset = str(st.session_state.get("preset", "Normal"))
_base_apto = float(provenance["defaults"]["threshold_airworthy"])
_base_aog = float(provenance["defaults"]["threshold_aog"])
_d_apto, _d_aog = _PRESETS.get(preset, _PRESETS["Normal"])
_preset_vals = (max(1.0, _base_apto + _d_apto), max(0.0, _base_aog + _d_aog))
# El modo historia puede pedir otros umbrales: se dejan en `session_state` antes
# de que el widget exista, igual que las demás escrituras diferidas.
if st.session_state.get("_umbrales_pendientes"):
    _u_p, _h_p = st.session_state.pop("_umbrales_pendientes")
    st.session_state[f"th_apto_{preset}"] = float(_u_p)
    st.session_state[f"th_aog_{preset}"] = float(_h_p)
threshold_apto = float(st.session_state.get(f"th_apto_{preset}", _preset_vals[0]))
threshold_aog = float(st.session_state.get(f"th_aog_{preset}", _preset_vals[1]))
if not threshold_aog < threshold_apto:
    st.error(
        "El umbral de hangar debe ser estrictamente menor que el de apto.",
        icon=":material/rule:",
    )
    st.stop()
aplicar_reglas = bool(st.session_state.get("aplicar_reglas", False))
cycle = int(st.session_state.get("cycle", 1))
banda_en_uso = (
    "R6 recalibrada (mia/calibracion_banda.json, 14 915 filas OOF puras)"
    if aplicar_reglas else
    "artefacto (models/ds02_manifest.json, conformal del bundle)"
)
correccion_en_uso = (
    "R2b isotonico causal + R6 banda recalibrada" if aplicar_reglas
    else "ninguna (lectura cruda de la cache)"
)

# ------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Guardia operativa", icon=":material/radar:")
    _vistas = sorted(set(int(u) for u in units) | {int(a["unit_id"]) for a in _altas()})
    _default = _vistas[0] if int(st.session_state.get("unit", _vistas[0])) not in _vistas else int(st.session_state.get("unit", _vistas[0]))
    unit = st.segmented_control(
        "Unidad de test",
        _vistas,
        default=_default,
        required=True,
        format_func=lambda u: _etiqueta_unidad(float(u)),
        key="unit",
        help="Motores del conjunto de test DS02 (partición fija [11, 14, 15]).",
    )
    st.caption(_etiqueta_unidad(float(unit)))

    st.subheader("Probar con un caso típico (sin datos)", icon=":material/library_add:")
    st.caption(
        "Sin CSV ni pegado: elige matrícula + unidad + ciclo y aparece en flota. Cada ciclo es un estado de degradación distinto. Para telemetría real usa la pestaña Evaluar unidad nueva."
    )
    with st.form("alta_avion"):
        matricula = st.text_input(
            "Matrícula", key="alta_matricula", value="",
            help="Etiqueta de visualización. Mínimo 3 caracteres.",
        )
        unidad_libre = st.selectbox(
            "Unidad base (caché)", sorted(int(u) for u in units), key="alta_unidad",
            format_func=lambda u: L.UNIT_LABELS.get(int(u), f"Unidad {int(u)}"),
            help="Motor del test del que se toma la historia ya puntuada.",
        )
        ciclo_libre = st.number_input(
            "Ciclo hasta el que tomar historia",
            min_value=int(windows["cycle"].min()),
            max_value=int(windows["cycle"].max()),
            value=int(min(max(int(windows["cycle"].min()), 20), int(windows["cycle"].max()))),
            step=1, key="alta_ciclo",
            help="El mismo motor en otro ciclo es otro caso de prueba: cambia su estado de triaje.",
        )
        enviar = st.form_submit_button("Incorporar unidad",
                                       icon=":material/add_circle:", type="primary")
    if enviar:
        try:
            limpia = T.normalizar_id(matricula)
        except ValueError as exc:
            st.error(str(exc), icon=":material/rule:")
        else:
            unidad_p, ciclo_p = int(unidad_libre), int(ciclo_libre)
            registro = {F.ALTAS_KEY: st.session_state.get(F.ALTAS_KEY) or {}}
            try:
                registro = F.registrar_alta(registro, limpia, unidad_p, ciclo_p)
            except ValueError as exc:
                st.error(str(exc), icon=":material/rule:")
            else:
                st.session_state[F.ALTAS_KEY] = registro[F.ALTAS_KEY]
                _guardar_registros()
                _uid = registro[F.ALTAS_KEY][limpia]["unit_id"]
                st.session_state["_alta_pendiente"] = int(_uid)
                # El alta crea su gemelo: el motor aparece en "Gemelos
                # registrados" con su serie guardada. No llama al modelo, toma
                # las ventanas ya puntuadas de la caché.
                _umb = {"apto": float(st.session_state.get("th_apto_Normal", 30.0)),
                        "hangar": float(st.session_state.get("th_aog_Normal", 25.0))}
                _ventanas_alta = A.ventanas_de_alta(windows, unidad_p, ciclo_p, _uid)
                _gemelo = T.make_twin(
                    limpia,
                    {"windows": _ventanas_alta,
                     "contract": {"unidad_simulada": _uid,
                                  "motor": limpia,
                                  "canales": INF.channel_order(),
                                  "window": INF.window_size(),
                                  "step": 2,
                                  "artefacto_sha256": L.get_provenance()["artifact"]["ensemble_sha256"],
                                  "filas": int(len(_ventanas_alta)),
                                  "ventanas": int(len(_ventanas_alta))}},
                    source="alta del sidebar",
                    banda=L.UNIT_LABELS.get(unidad_p, f"U{unidad_p} (caché)"),
                    correccion="ninguna (ventanas ya puntuadas de la caché)",
                    umbrales=_umb,
                )
                st.session_state["twins"] = T.registrar(
                    st.session_state.get("twins", {}), _gemelo)
                _guardar_registros()
                # El aviso dice donde va a aparecer el motor: la matricula, que
                # es la clave del hangar. Antes prometia la matricula y el
                # hangar la claveaba como U-1000.
                st.session_state["twin_flash"] = (
                    f"Aeronave `{limpia}` incorporada (U{unidad_p} hasta el ciclo {ciclo_p}). "
                    f"Aparece en el muro y en «Gemelos registrados» con la matrícula "
                    f"`{limpia}`. Para derivarla, ábrela en «Hangar · ciclo de vida»."
                )
                _log(f"Alta de la unidad {limpia} (U{unidad_p} hasta el ciclo {ciclo_p}).")
                st.rerun()
    with st.expander("Quitar aeronaves de alta", icon=":material/remove_circle:"):
        altas = _altas()
        if not altas:
            st.caption("Ninguna aeronave de alta en esta sesión.")
        else:
            a_quitar = st.selectbox(
                "Aeronave", [a["matricula"] for a in altas], key="alta_quitar")
            if st.button("Quitar", icon=":material/delete:", key="alta_quitar_btn"):
                registro = {F.ALTAS_KEY: st.session_state.get(F.ALTAS_KEY) or {}}
                registro = F.quitar_alta(registro, a_quitar)
                st.session_state[F.ALTAS_KEY] = registro[F.ALTAS_KEY]
                _guardar_registros()
                st.rerun()
    st.subheader("El taller está en la primera pestaña",
                 icon=":material/tune:")
    st.caption(
        "Umbrales, motor de reglas y reloj de flota viven en la sala «El taller», "
        "junto al muro en el que se ve su efecto."
    )
    st.caption(
        f"Caché con {provenance['counts']['windows']:,} ventanas y "
        f"{provenance['counts']['rows']:,} filas de telemetría · "
        f"generada {provenance['generated_at'][:16].replace('T', ' ')}"
    )

    with st.expander("Cómo leer esta pantalla", icon=":material/help:"):
        st.markdown(
            "- **RUL** (*remaining useful life*): ciclos de vuelo que le quedan al motor "
            "según el modelo. Es una estimación, no una medida.\n"
            "- **L_inf**: extremo inferior de la banda conformal al 90 %. Es el número que "
            "gobierna la decisión, no la predicción puntual: equivocarse por pesimismo "
            "cuesta una inspección, por optimismo cuesta un motor.\n"
            "- **Banda 90 %**: intervalo calibrado sobre los motores de desarrollo. Si el "
            "motor se comporta como ellos, su vida real cae dentro 9 de cada 10 veces.\n"
            "- **Estados**: APTO (`L_inf ≥ apto`) · INSPECCIÓN (entre umbrales) · "
            "HANGAR/AOG (`L_inf < hangar`: la unidad no vuela y se emite orden).\n"
            "- **Ciclo de vuelo**: un despegue–aterrizaje. El reloj del taller "
            "simula el paso del tiempo sobre el conjunto de test congelado.\n"
            "- **Ventana**: las 50 muestras remuestreadas (~0,4 ciclos de vuelo) que "
            "el modelo consume de una vez. "
            "Se puntúa una ventana cada 2 filas, así que un ciclo acumula varias "
            "predicciones.\n"
            "- **Orden de trabajo**: documento JSON/CSV con las unidades bloqueadas, su "
            "banda y la acción de mantenimiento."
        )

    with st.expander("Contrato de artefacto congelado", icon=":material/lock:"):
        shape = manifest.get("model_shape", {})
        conformal = manifest.get("conformal", {}) or {}
        st.caption(
            "Registrado en `models/ds02_manifest.json`. **No** es un cálculo de esta "
            "caché: es el contrato del artefacto que se está consumiendo."
        )
        st.markdown(
            f"**dataset** `{manifest.get('dataset')}` · "
            f"**code_version** `{manifest.get('code_version')}` · "
            f"**seed** `{manifest.get('seed')}`"
        )
        st.markdown(
            f"**test** `{manifest.get('unit_partition', {}).get('test')}` · "
            f"**ventana** `{shape.get('bilstm_input_shape')}` · "
            f"**meta** `{shape.get('meta_features')} features`"
        )
        st.markdown(
            f"**banda** objetivo `{conformal.get('target_coverage')}` · "
            f"*{conformal.get('method')}* · calibración "
            f"`{conformal.get('n_calibration')}` filas"
        )
        st.markdown("**SHA-256 del ensemble**")
        st.code(provenance["artifact"]["ensemble_sha256"], language=None)
        st.caption(
            "64 caracteres hexadecimales. Es la huella del artefacto congelado, no la de "
            "la caché."
        )
        recorded = manifest.get("macro_rmse", {}).get("per_unit_rmse", {})
        if recorded:
            st.markdown(
                "**macro-RMSE por motor (registrado)** "
                + " · ".join(f"U{int(float(k))}: `{v:.3f}`" for k, v in recorded.items())
            )
        st.json(
            {
                "artefactos": manifest.get("artifacts", {}),
                "inference_contract": manifest.get("inference_contract", {}),
                "lgb_objective": manifest.get("lgb_objective", {}),
            },
            expanded=False,
        )

# La capa de reglas (mia/) es opcional y arranca apagada: con ella apagada la UI
# muestra la lectura cruda de la caché, que es la que reproduce el contrato
# congelado en models/ds02_manifest.json.
umbrales = {"apto": float(threshold_apto), "hangar": float(threshold_aog)}
# `frame_cache` es solo la caché: de aquí salen las métricas y la telemetría.
# `frame` incluye las aeronaves de alta: de aquí sale la flota y las órdenes.
frame_cache = UR.corregir_ventanas(windows) if aplicar_reglas else windows
# Pasada A del motor `mia/`: R1/R9/R8/R7 deciden el estado sobre el limite inferior.
frame_cache = UR.decidir_ventanas(frame_cache, umbrales)
frame = A.frame_con_altas(frame_cache, windows, _altas(), aplicar_reglas, umbrales)
# Las tarjetas de flota se calculan sobre la lectura en uso: con la corrección
# activa no pueden mostrar el macro-RMSE crudo al lado de un RMSE corregido.
global_metrics = L.global_metrics(frame_cache)
unidades_vistas = sorted(int(u) for u in frame["unit"].unique())
curves = {u: L.unit_curve(frame, u) for u in unidades_vistas}
alarms = {u: L.first_alarm_cycle(curves[u], threshold_aog) for u in unidades_vistas}
correccion = UR.resumen_correccion(windows, frame_cache) if aplicar_reglas else None
snapshot = L.fleet_snapshot(frame, cycle, threshold_apto, threshold_aog)
# Gemelos y registros de hangar: se leen aqui, antes de las pestanas, porque el
# muro los dibuja. Antes vivian despues del muro y el muro no podia verlos.
gemelos = st.session_state.get("twins", {})
registros = st.session_state.get("hangar", {})


def _tarjetas_gemelos() -> list[dict]:
    """Una tarjeta por gemelo registrado, con el estado recalculado hoy.

    El gemelo es flota registrada, pero su clave es el `engine_id` y su serie
    vive en el gemelo, no en la caché: por eso `snapshot` (que sale de `frame`)
    no lo veia. Sin esta lista, registrar un motor y volver al muro no mostraba
    nada nuevo.

    El estado no se guarda: se deriva de la serie guardada con los umbrales en
    vigor (`twin.ciclo_a_ciclo`), igual que la tabla de gemelos.
    """
    tarjetas = []
    usadas = {f"muro_gemelo_{int(u)}" for u in unidades_vistas}
    for gemelo_id, gemelo in gemelos.items():
        curva = T.ciclo_a_ciclo(gemelo, umbrales)
        if curva.empty:
            continue
        # La sparkline del muro dibuja `lower`; la curva del gemelo la llama
        # `lower_media`. Se homogenea aqui para que el muro no pregunte de donde
        # salio la tarjeta.
        curva["lower"] = curva["lower_media"]
        ultima = curva.iloc[-1]
        clave = f"muro_gemelo_{_slug_motor(gemelo_id)}"
        # Dos ids que slugen igual ("A B" y "A_B") no pueden compartir boton:
        # Streamlit rechaza la clave duplicada y cae la pagina entera.
        while clave in usadas:
            clave += "_"
        usadas.add(clave)
        tarjetas.append({
            "orden_unidad": (1, str(gemelo_id)),
            "etiqueta": str(gemelo_id),
            "estado": str(ultima["decision"]),
            "pred": float(ultima["pred"]),
            "lower": float(ultima["lower_min"]),
            "curva": curva,
            "ciclo_tarjeta": int(ultima["cycle"]),
            "clave_boton": clave,
            "gemelo": str(gemelo_id),
        })
    return tarjetas


tarjetas_gemelos = _tarjetas_gemelos()
derivados_gemelos = sum(1 for t in tarjetas_gemelos if t["estado"] == L.AOG)


def _tarjetas_cache() -> list[dict]:
    """Una tarjeta por unidad de la flota visible: caché y altas."""
    tarjetas = []
    for u in unidades_vistas:
        fila = snapshot[snapshot["unit"] == u].iloc[0]
        _scored = fila["scored_cycle"]
        tarjetas.append({
            "orden_unidad": (0, int(u)),
            "etiqueta": _etiqueta_unidad(float(u)),
            "estado": str(fila["state"]),
            "pred": fila["pred"],
            "lower": fila["lower"],
            "curva": curves[u],
            "ciclo_tarjeta": int(_scored) if pd.notna(_scored) else int(cycle),
            "clave_boton": f"muro_gemelo_{int(u)}",
            "gemelo": None,
            "unidad": int(u),
        })
    return tarjetas


tarjetas_cache = _tarjetas_cache()
curve = curves[int(unit)]
per_unit = L.per_unit_metrics(frame_cache)
unit_metrics = (per_unit[per_unit["unit"] == unit].iloc[0]
                if (per_unit["unit"] == unit).any()
                else None)
alarm_cycle, truth_cycle = alarms[int(unit)]
current = int(min(cycle, int(curve["cycle"].max())))
# Cobertura por ventana (la misma base que decide: cada ventana cuenta una vez).
# El gráfico dibuja medias por ciclo, pero este número no promedia: si la peor
# ventana de un ciclo sale de la banda, aquí se cuenta.
_wu = frame[frame["unit"] == int(unit)]
coverage = float(np.mean((_wu["y_true"] >= _wu["lower"]) &
                         (_wu["y_true"] <= _wu["upper"]))) if len(_wu) else float("nan")
critical_mae = L.critical_zone_mae(frame_cache, threshold_aog)
grounded = int((snapshot["state"] == L.AOG).sum())
critical_start = truth_cycle

# ---------------------------------------------------------------------- header
_mostrar_toast_pendiente()
head_left, head_right = st.columns([3, 2], vertical_alignment="center")
with head_left:
    st.title("DS02 · Centro de control de mantenimiento", icon=":material/flight:")
    st.caption(
        "Ensamble híbrido BiLSTM + LightGBM cuantílico · banda conformal asimétrica · "
        "decisión de hangar gobernada por el **límite inferior** de la banda."
    )
with head_right:
    with st.container(horizontal=True, horizontal_alignment="right"):
        st.badge(
            f"SHA-256 {provenance['artifact']['ensemble_sha256'][:8]}",
            icon=":material/lock:", color="gray",
        )
        st.badge(
            f"{global_metrics['windows']:,} ventanas",
            icon=":material/table_rows:", color="blue",
        )
        st.badge(
            f"Banda {provenance['artifact']['conformal_target_coverage']:.0%}",
            icon=":material/verified:", color="green",
        )

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
    if derivados_gemelos:
        # La métrica de arriba cuenta la flota visible en `frame` (caché + altas).
        # Los motores registrados en esta sesión no están en ese recuento, y
        # decirlo es lo único que evita que el número mienta.
        st.caption(
            f"Además, **{derivados_gemelos}** motor(es) de los registrados en esta "
            "sesión están derivados a hangar con los umbrales en vigor: los verás en "
            "el muro y en «Gemelos registrados»."
        )

@st.fragment
def _sandbox_estres() -> None:
    """Sandbox de estrés: perturbar la caché y ver el pipeline reaccionar en vivo.

    El tribunal mueve el deslizador y la app re-puntúa el tramo con el artefacto
    congelado (`ui_inference.score_table`) y re-decide con el motor oficial
    (`mia/reglas.py` vía `ui_rules.decidir_ventanas`). No se reentrena nada y no
    se escribe en `models/` ni en `src/`.

    La perturbación es sintética y se declara: el split-conformal se calibró sobre
    datos reales, así que romper la intercambiabilidad quita la garantía del 90 %.
    La banda se sigue dibujando — el límite inferior sigue gobernando la decisión
    (ADR-008) — pero con la leyenda degradada y el aviso visible.

    Con la deriva a 0 % el tramo se dibuja desde la caché y el modelo no se carga:
    la app está documentada y testeada para arrancar sin el artefacto de 2,3 GB.
    Solo una deriva distinta de cero paga la carga (una sola vez, `@st.cache_resource`).

    Los umbrales se leen de `session_state` y no del global del módulo: el fragment
    se re-ejecuta solo, y un valor congelado en la pasada anterior quedaría obsoleto
    si el tribunal cambiara la política en la pestaña del taller.
    """
    _preset_sbx = str(st.session_state.get("preset", "Normal"))
    _umb_sbx = {
        "apto": float(st.session_state.get(f"th_apto_{_preset_sbx}", 30.0)),
        "hangar": float(st.session_state.get(f"th_aog_{_preset_sbx}", 25.0)),
    }
    _u_sbx = st.segmented_control(
        "Unidad del tramo", units, default=14, key="sbx_unit",
        help="Motores del conjunto de test DS02 (partición fija [11, 14, 15]).",
    )
    _deriva_pct = st.slider(
        "Deriva térmica acumulada en T48", min_value=0, max_value=30, value=0,
        step=1, format="%d%%", key="sbx_deriva",
        help="Porcentaje que T48 (temperatura de salida del compresor de alta) gana "
             "al final del tramo respecto a su valor en caché. Con 0 % el tramo es "
             "la caché tal cual; cualquier otro valor es una intervención sintética.",
    )
    _deriva = _deriva_pct / 100.0
    _perturbado = _deriva > 0.0

    # El tramo va del primer ciclo puntuado al primero en que la caché ya manda al
    # hangar: es el mismo recorrido que cuenta el modo historia. Sale de la caché,
    # no de una constante.
    _cur_sbx = L.unit_curve(windows, int(_u_sbx))
    _c_inicio = int(_cur_sbx["cycle"].min())
    _bajo_hangar = _cur_sbx[_cur_sbx["lower_min"] < _umb_sbx["hangar"]]
    _c_fin = (int(_bajo_hangar["cycle"].min()) if not _bajo_hangar.empty
              else int(_cur_sbx["cycle"].max()))
    if _c_fin <= _c_inicio:
        st.caption(
            "Este motor no cruza el umbral de hangar en la caché: no hay transición "
            "que enseñar en el tramo."
        )
        return
    _tramo = telemetry[(telemetry["unit"] == int(_u_sbx))
                       & (telemetry["cycle"] >= _c_inicio)
                       & (telemetry["cycle"] <= _c_fin)].reset_index(drop=True)
    _muestras = len(_tramo)

    if not _perturbado:
        # Con 0 % el tramo es la caché tal cual y se dibuja sin cargar el modelo: la
        # app está documentada y testeada para arrancar sin el artefacto (2,3 GB).
        # El estado se clasifica con el mismo `L.classify` que usa el cargador.
        _cur = (_cur_sbx[["cycle", "pred", "lower", "upper", "lower_min"]]
                .sort_values("cycle").reset_index(drop=True))
        # `unit_curve` devuelve toda la vida del motor; el sandbox enseña el tramo.
        _cur = _cur[_cur["cycle"] <= _c_fin].reset_index(drop=True)
        _cruce = _cur[_cur["lower_min"] < _umb_sbx["hangar"]]
        _cruce_ciclo = int(_cruce["cycle"].min()) if not _cruce.empty else None
        _ultima = _cur.iloc[-1]
        _estado = L.classify(float(_ultima["lower"]), _umb_sbx["apto"], _umb_sbx["hangar"])
        _ventanas = int(((windows["unit"] == int(_u_sbx))
                         & (windows["cycle"] >= _c_inicio)
                         & (windows["cycle"] <= _c_fin)).sum())
    else:
        _tab = _tramo[["cycle"] + INF.channel_order()].copy()
        _tab["T48"] = _tab["T48"].astype(float) * (
            1.0 + _deriva * np.linspace(0.0, 1.0, len(_tab)))
        _pf = INF.preflight(_tab)
        if not _pf["ok"]:
            st.error(_pf["error"], icon=":material/rule:")
            return
        try:
            _win = INF.score_table(_tab, engine_id=f"ESN-SBX-{int(_u_sbx)}")["windows"]
        except ValueError as exc:
            st.error(str(exc), icon=":material/rule:")
            return
        _dec = UR.decidir_ventanas(_win, _umb_sbx)
        _cur = (_dec.groupby("cycle", as_index=False)
                .agg(pred=("pred", "mean"), lower=("lower", "mean"),
                     upper=("upper", "mean"), lower_min=("lower", "min"))
                .sort_values("cycle").reset_index(drop=True))
        _cruce = _cur[_cur["lower_min"] < _umb_sbx["hangar"]]
        _cruce_ciclo = int(_cruce["cycle"].min()) if not _cruce.empty else None
        _fin_dec = _dec[_dec["cycle"] == _c_fin]
        _ultima = (_fin_dec.loc[_fin_dec["lower"].idxmin()] if not _fin_dec.empty
                   else _dec.iloc[-1])
        _estado = str(_ultima["decision"])
        _ventanas = len(_win)

    _band_name = ("Banda proyectada (fuera de garantía conformal 90 %)"
                  if _perturbado else "Banda conformal (90 %)")
    _dash = "dot" if _perturbado else "solid"
    _band_color = ROSE if _perturbado else SKY
    _fill = "rgba(248,113,113,0.10)" if _perturbado else "rgba(56,189,248,0.10)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_cur["cycle"], y=_cur["upper"], mode="lines", name=_band_name,
        line=dict(width=1, color=_band_color, dash=_dash),
        hovertemplate="ciclo %{x}<br>superior %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_cur["cycle"], y=_cur["lower"], mode="lines", name=" ",
        line=dict(width=1, color=_band_color, dash=_dash),
        fill="tonexty", fillcolor=_fill,
        hovertemplate="ciclo %{x}<br>inferior %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_cur["cycle"], y=_cur["pred"], mode="lines", name="RUL predicha",
        line=dict(width=2, color=SKY),
        hovertemplate="ciclo %{x}<br>RUL %{y:.1f}<extra></extra>",
    ))
    fig.add_hline(y=_umb_sbx["apto"], line_color=GREEN, line_width=1, line_dash="dash",
                  annotation_text=f"apto ≥ {_umb_sbx['apto']:.0f}",
                  annotation_font_color=GREEN, annotation_font_size=11)
    fig.add_hline(y=_umb_sbx["hangar"], line_color=ROSE, line_width=1, line_dash="dash",
                  annotation_text=f"hangar < {_umb_sbx['hangar']:.0f}",
                  annotation_font_color=ROSE, annotation_font_size=11)
    if _cruce_ciclo is not None:
        fig.add_vline(x=_cruce_ciclo, line_color=AMBER, line_width=1, line_dash="dot",
                      annotation_text=f"hangar en {_cruce_ciclo}",
                      annotation_font_color=AMBER, annotation_font_size=11)
    fig.update_layout(**chart_layout(height=360))
    style_axes(fig, x_title="Ciclo de vuelo", y_title="ciclos de RUL")
    _alt = (f"Curva de RUL de la unidad {int(_u_sbx)} entre los ciclos {_c_inicio} y "
            f"{_c_fin}, con una deriva sintética del {_deriva_pct:.0f} % en T48: el "
            f"límite inferior cruza el umbral de hangar en el ciclo {_cruce_ciclo} y el "
            f"estado al final del tramo es {L.STATE_LABELS.get(_estado, _estado)}."
            if _cruce_ciclo is not None and _perturbado else
            f"Curva de RUL de la unidad {int(_u_sbx)} entre los ciclos {_c_inicio} y "
            f"{_c_fin} sin cruce al umbral de hangar; el estado al final del tramo es "
            f"{L.STATE_LABELS.get(_estado, _estado)}."
            if _cruce_ciclo is None else
            f"Curva de RUL de la unidad {int(_u_sbx)} entre los ciclos {_c_inicio} y "
            f"{_c_fin} leída de la caché: el límite inferior cruza el umbral de hangar "
            f"en el ciclo {_cruce_ciclo} y el estado al final del tramo es "
            f"{L.STATE_LABELS.get(_estado, _estado)}.")
    st.plotly_chart(fig, use_container_width=True, alt=_alt)

    _m1, _m2 = st.columns(2)
    _m1.metric("RUL p35 al final del tramo", f"{_ultima['pred']:.1f} ciclos",
               border=True, icon=":material/schedule:")
    _m2.metric("Cruce a hangar",
               f"ciclo {_cruce_ciclo}" if _cruce_ciclo else "no cruza en el tramo",
               border=True, icon=":material/warning:")
    st_badge_estado(_estado)
    st.caption(
        f"Tramo de caché ciclos {_c_inicio}→{_c_fin}: {_muestras} muestras "
        f"remuestreadas, {_ventanas} ventanas. "
        + ("Leído de la caché, sin cargar el modelo: al mover el deslizador el "
           "pipeline corre en vivo y la banda pierde la garantía conformal."
           if not _perturbado else
           "Puntuado en vivo con el artefacto congelado; la banda se degrada a "
           "proyectada porque el split-conformal perdió la intercambiabilidad.")
    )
    if _perturbado:
        for _aviso in _pf["avisos"]:
            st.warning(_aviso, icon=":material/find_in_page:")
        st.warning(
            f"Deriva sintética del {_deriva_pct:.0f} % sobre T48: la banda pierde la "
            "garantía conformal del 90 % — el split-conformal se calibró sobre datos "
            "reales y una intervención sintética rompe la intercambiabilidad. El "
            "límite inferior sigue gobernando la decisión (ADR-008), pero su cobertura "
            "ya no está garantizada.",
            icon=":material/warning:",
        )


tab_flota, tab_motor, tab_evidencia = st.tabs(
    [
        ":material/factory: Flota · qué pasa hoy",
        ":material/precision_manufacturing: Motor · qué le pasa a este",
        ":material/science: Evidencia · cómo se calculó",
    ]
)


with tab_flota:
    # El onboarding es el estado inicial: lo primero que ve quien entra, no la
    # quinta pestaña (donde vivió y nadie lo encontraba).
    with st.container(border=True):
        st.subheader("¿Primera vez aquí? Empieza en 1 clic", icon=":material/rocket_launch:")
        st.caption(
            "Cada unidad es un **motor turbofán** del dataset N-CMAPSS DS02: la matrícula "
            "es una etiqueta de visualización y los datos son los de la caché congelada. "
            "Lo que decide el estado es el **límite inferior** de la banda, no la "
            "predicción puntual. Elige un archetype y mira el muro."
        )
        _arquetipos = [
            ("Recién salido de revisión", "Toda la flota en verde."),
            ("Desgaste operativo medio", "Primera inspección programada."),
            ("Fin de vida / crítico", "Entra en hangar con vida útil estimada alta."),
        ]
        _col_arquetipos = st.columns(3)
        for _col, (_perfil, _que_cuenta) in zip(_col_arquetipos, _arquetipos):
            with _col:
                if st.button(
                    _perfil, key=f"arquetipo_{_perfil}", icon=":material/play_arrow:",
                    type="primary" if "crítico" in _perfil else "secondary",
                ):
                    _u, _c = A.PERFILES[_perfil]
                    st.session_state["_escenario_pendiente"] = (int(_u), int(_c))
                    _log(f"Archetype «{_perfil}» cargado (U{_u}, ciclo {_c}).")
                    st.session_state["_toast_pendiente"] = (
                        f"Escenario «{_perfil}» cargado (U{_u}, ciclo {_c}). "
                        "Pulsa una tarjeta para abrir su gemelo."
                    )
                    st.rerun()
                st.caption(_que_cuenta)

    # El muro: una tarjeta por motor. Es lo que un operador de taller reconoce.
    with st.container(border=True):
        st.subheader("Muro del hangar", icon=":material/grid_view:")
        st.caption(
            "Una tarjeta por motor, con la sparkline de su límite inferior. El color y el "
            "estado los dicta `L_inf`; pulsa «Ver gemelo» para abrir su ficha completa. "
            "La flota de la caché y los motores registrados en esta sesión comparten muro."
        )

        @st.fragment
        def _muro_del_hangar() -> None:
            orden = st.pills(
                "Orden del muro",
                ["Por urgencia", "Por unidad"],
                default="Por urgencia",
                key="muro_orden",
                help="Por urgencia adelanta las unidades en hangar; por unidad respeta "
                     "el orden de la caché y deja los motores registrados al final.",
            )
            tarjetas = tarjetas_cache + tarjetas_gemelos
            if orden == "Por unidad":
                tarjetas = sorted(tarjetas, key=lambda t: t["orden_unidad"])
            else:
                tarjetas = sorted(
                    tarjetas,
                    key=lambda t: (RANGO_ESTADO.get(t["estado"], 9), t["orden_unidad"]),
                )
            columnas = st.columns(3)
            for i, tarjeta in enumerate(tarjetas):
                etiqueta = tarjeta["etiqueta"]
                estado = tarjeta["estado"]
                curva = tarjeta["curva"]
                _pred = "—" if pd.isna(tarjeta["pred"]) else f"{tarjeta['pred']:.1f}"
                _lo = "—" if pd.isna(tarjeta["lower"]) else f"{tarjeta['lower']:.1f}"
                with columnas[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"**{etiqueta}**")
                        st.badge(
                            L.STATE_LABELS.get(estado, str(estado)),
                            icon=BADGE_ICON.get(estado, ":material/circle:"),
                            color=BADGE_COLOR.get(estado, "gray"),
                        )
                        st.metric("RUL p35 (conservadora)", _pred, "cuantil 0.35",
                                  border=True, delta_color="off", icon=":material/speed:",
                                  help="Cuantil 0.35 de la RUL (ADR-003): una estimacion "
                                       "conservadora, no la vida esperada. Lo que decide el "
                                       "estado es el limite inferior de su banda, L_inf.")
                        st.metric("L_inf (decide)", _lo, "ciclos",
                                  border=True, delta_color="off",
                                  icon=":material/trending_down:")
                        fig = go.Figure(
                            go.Scatter(
                                x=curva["cycle"], y=curva["lower"], mode="lines",
                                line=dict(color=SKY, width=2), name="L_inf",
                                hovertemplate="ciclo %{x}<br>L_inf %{y:.1f}<extra></extra>",
                            )
                        )
                        fig.update_layout(**chart_layout(
                            height=110, showlegend=False, hovermode="closest",
                            margin=dict(l=8, r=8, t=6, b=6),
                        ))
                        style_axes(fig)
                        st.plotly_chart(
                            fig, theme=None,
                            alt=f"Sparkline del límite inferior de {etiqueta} "
                                "a lo largo de los ciclos.",
                        )
                        if st.button(
                            "Ver gemelo", key=tarjeta["clave_boton"],
                            icon=":material/visibility:", type="secondary",
                        ):
                            if tarjeta["gemelo"]:
                                # Un gemelo no tiene ficha en la pestaña del motor: su
                                # registro es la tabla de debajo. Decirlo es mejor que
                                # prometer una ficha que no existe.
                                st.session_state["_gemelo_pendiente"] = tarjeta["gemelo"]
                                st.session_state["_toast_pendiente"] = (
                                    f"{etiqueta}: su estado se recalcula con los umbrales "
                                    "en vigor en «Gemelos registrados», bajo el muro."
                                )
                            else:
                                st.session_state["_escenario_pendiente"] = (
                                    tarjeta["unidad"], tarjeta["ciclo_tarjeta"])
                                st.session_state["_toast_pendiente"] = (
                                    f"{etiqueta} seleccionada. Abre su ficha en la "
                                    "pestaña «Motor · qué le pasa a este»."
                                )
                            st.rerun()

        _muro_del_hangar()

    # -------------------- sala 3: el taller (¿qué pasa si cambio la política?)
    with st.container(border=True):
        st.subheader("El taller · qué pasa si cambio la política",
                     icon=":material/tune:")
        st.caption(
            "Los tres controles que gobiernan el triaje, con lo que hacen y lo que no "
            "hacen. Su efecto se ve abajo: en el muro y en la cola de mantenimiento."
        )
        _taller_a, _taller_b = st.columns([2, 1])
        with _taller_a:
            st.selectbox(
                "Preset de umbrales",
                list(_PRESETS),
                key="preset",
                help="Rellena los dos umbrales de abajo. Después puedes ajustarlos a mano.",
            )
            with st.container(horizontal=True):
                st.number_input(
                    "Apto si L_inf ≥ (ciclos)", min_value=1.0, max_value=100.0,
                    value=_preset_vals[0], step=1.0, key=f"th_apto_{preset}",
                    help="Estado verde gobernado por el límite inferior conformal, no "
                         "por la predicción puntual.",
                )
                st.number_input(
                    "Hangar si L_inf < (ciclos)", min_value=0.0, max_value=99.0,
                    value=_preset_vals[1], step=1.0, key=f"th_aog_{preset}",
                    help="Por debajo de este límite inferior la unidad se inmoviliza y "
                         "se emite orden de trabajo.",
                )
            st.caption(f"Banda en uso: {banda_en_uso}. Corrección: {correccion_en_uso}.")
        with _taller_b:
            st.toggle(
                "Aplicar corrección de reglas",
                value=False,
                key="aplicar_reglas",
                help=(
                    "Pasada B del motor de reglas (paquete mia/): R2b ajuste isotonico "
                    "causal y R6 banda conformal recalibrada sobre el punto corregido. "
                    "Apagado, la UI muestra la lectura cruda de la caché, que es la que "
                    "reproduce el contrato congelado del artefacto."
                ),
            )
            st.slider(
                "Ciclo de vuelo simulado",
                min_value=1,
                max_value=max_life,
                value=1,
                step=1,
                key="cycle",
                help=(
                    "Reloj de flota: se aplica a todas las unidades. Las que terminaron "
                    "su vida registrada se muestran en su último ciclo evaluado (vida "
                    f"máxima: {max_life})."
                ),
            )
        st.caption(
            "La decisión sigue siendo por límite inferior: mover estos controles no "
            "cambia esa agregación, solo los números que la disparan."
        )

    # -------------------- avance de flota: el reloj se mueve, los retenidos no
    with st.container(border=True):
        st.subheader("Avanzar la flota", icon=":material/fast_forward:")
        st.caption(
            "Mueve el reloj compartido. El motor que ya cruzó el umbral deja de "
            "volar: se queda donde está en vez de extrapolarle. Los números salen "
            "de la caché ya puntuada; no se recalcula nada."
        )
        _decidido = UR.decidir_ventanas(windows, umbrales)
        _retenidos = S.retenidos(_decidido, cycle, umbrales)
        _faltan = S.ciclos_hasta_fallo(_decidido, cycle, umbrales)
        _fila_av = st.columns([1, 2])
        with _fila_av[0]:
            if st.button("Avanzar 10 ciclos de flota",
                         icon=":material/fast_forward:", key="avanzar_flota",
                         type="primary"):
                # No se escribe `cycle` aqui: el widget ya se instancio en esta
                # pasada y Streamlit lo prohibe
                # (`StreamlitWidgetAlreadyInstantiatedError`): la pagina revienta.
                # Se deja la bandera y el bloque de escrituras diferidas la aplica
                # antes de que el widget nazca.
                st.session_state["_avance_flota"] = int(min(
                    cycle + 10, int(windows["cycle"].max())))
                st.rerun()
        with _fila_av[1]:
            if _retenidos:
                st.caption(
                    "No vuelan: " + ", ".join(
                        F.etiqueta(F.clave_de(float(u), _registro()))
                        for u in sorted(_retenidos)))
            else:
                st.caption("Toda la flota puede volar en este ciclo.")
        _faltan_txt = " · ".join(
            f"{F.etiqueta(F.clave_de(float(u), _registro()))}: "
            + ("nunca en la vida registrada" if v is None else f"{v} ciclos")
            for u, v in sorted(_faltan.items()))
        st.caption(f"Ciclos hasta el umbral de hangar · {_faltan_txt}")

    # -------------------- modo historia: la narrativa en cuatro pasos
    with st.container(border=True):
        st.subheader("Modo historia · la narrativa en cuatro pasos",
                     icon=":material/auto_stories:")
        st.caption(
            "Cuatro estados que cuentan la historia, derivados de la caché. Cada paso "
            "deja la app donde dice; el cuarto cambia la política para ver el efecto."
        )
        _pasos_historia = A.estado_historia(windows, umbrales)
        _cols_h = st.columns(len(_pasos_historia))
        for _col, _paso in zip(_cols_h, _pasos_historia):
            with _col:
                if st.button(
                    f"{_paso['paso']}. {_paso['titulo']}",
                    key=f"historia_{_paso['paso']}", icon=":material/play_circle:",
                ):
                    st.session_state["_escenario_pendiente"] = (
                        int(_paso["unidad"]), int(_paso["ciclo"]))
                    st.session_state["_umbrales_pendientes"] = (
                        _paso["umbrales"]["apto"], _paso["umbrales"]["hangar"])
                    _log(f"Modo historia, paso {_paso['paso']}: {_paso['titulo']}.")
                    st.session_state["_toast_pendiente"] = (
                        f"Paso {_paso['paso']}: {_paso['titulo']}. {_paso['cuenta']}"
                    )
                    st.rerun()
                st.caption(_paso["cuenta"])

    # -------------------- registro de sesión
    with st.container(border=True):
        st.subheader("Registro de sesión", icon=":material/receipt_long:")
        _log_sesion = st.session_state.get("_sesion_log") or []
        if not _log_sesion:
            st.caption(
                "Todavía no has hecho nada en esta sesión. El registro se llena con "
                "cada acción discreta: altas, escenarios, lotes y gemelos."
            )
        else:
            st.dataframe(
                pd.DataFrame(_log_sesion),
                hide_index=True,
                column_config={
                    "at": st.column_config.TextColumn("Cuándo"),
                    "que": st.column_config.TextColumn("Qué"),
                },
                alt="Registro de sesión: las acciones hechas, con su fecha.",
            )
            with st.container(horizontal=True):
                st.download_button(
                    "Descargar registro (CSV)",
                    data=pd.DataFrame(_log_sesion).to_csv(index=False),
                    file_name="registro_sesion_ds02.csv",
                    mime="text/csv",
                    icon=":material/download:",
                )
                if st.button("Vaciar registro", icon=":material/delete:",
                             key="sesion_vaciar"):
                    st.session_state["_sesion_log"] = []
                    st.rerun()

    with st.container(horizontal=True):
        st.metric(
            "Flota monitorizada",
            f"{global_metrics['units']} unidades",
            f"{global_metrics['windows']:,} ventanas evaluadas",
            border=True, icon=":material/groups:", delta_color="off",
        )
        # En la pantalla de decision solo hay una KPI por concepto. Las metricas
        # de calidad del modelo (MAE, Macro-RMSE, sesgo, cobertura) viven en
        # Evidencia: son para el tribunal, no para el operador de taller.
        st.metric(
            "Unidades en hangar",
            f"{grounded} / {len(snapshot)}",
            f"en el ciclo {cycle}",
            border=True, icon=":material/local_shipping:", delta_color="off",
        )

    if correccion:
        st.caption(
            f"**Corrección de reglas activa** (pasada B del motor `mia/`): "
            f"{correccion['ventanas_corregidas']:,} de {correccion['ventanas']:,} "
            f"ventanas movidas ({correccion['porcentaje']} %) · "
            f"Δ punto medio {correccion['delta_medio_punto']:+.2f} ciclos · "
            f"Δ L_inf medio {correccion['delta_medio_l_inf']:+.2f}. "
            "La lectura cruda de la caché sigue disponible en la pestaña de auditoría."
        )

    with st.container(border=True):
        st.subheader("Cronología de estado de flota", icon=":material/timeline:")
        st.caption(
            "Cada punto es un ciclo evaluado y su color es el estado que dicta el límite "
            "inferior. La línea vertical es el reloj de la simulación."
        )
        ribbon_rows = []
        por_ciclo = UR.estado_por_ciclo(frame)
        for u in unidades_vistas:
            curva = curves[u]
            sub = por_ciclo[por_ciclo["unit"] == u].sort_values("cycle")
            ribbon_rows.append(
                pd.DataFrame(
                    {
                        "unidad": _etiqueta_unidad(float(u)),
                        "ciclo": curva["cycle"],
                        "estado": sub["decision"].to_numpy(),
                        "L_inf": curva["lower"],
                    }
                )
            )
        ribbon = pd.concat(ribbon_rows, ignore_index=True)
        ribbon["color"] = ribbon["estado"].map(STATE_COLORS)
        ribbon["etiqueta"] = ribbon["estado"].map(STATE_WORD)
        ribbon["simbolo"] = ribbon["estado"].map(L.STATE_SYMBOLS).fillna("circle")

        fig_fleet = go.Figure(
            go.Scatter(
                x=ribbon["ciclo"],
                y=ribbon["unidad"],
                mode="markers",                            marker=dict(color=ribbon["color"], size=11, symbol=ribbon["simbolo"],
                                        line=dict(width=0)),
                customdata=np.column_stack([ribbon["etiqueta"], ribbon["L_inf"]]),
                hovertemplate=(
                    "U%{y} · ciclo %{x}<br>estado: %{customdata[0]}"
                    "<br>L_inf: %{customdata[1]:.1f} ciclos<extra></extra>"
                ),
                name="Estado por ciclo",
            )
        )
        fig_fleet.add_vline(
            x=cycle, line_color=INK, line_width=1.5, line_dash="dot",
            annotation_text=f"ciclo {cycle}", annotation_position="top",
            annotation_font=dict(color=INK, size=11),
        )
        fig_fleet.update_layout(
            **chart_layout(height=240, showlegend=False,
                           hovermode="closest"),
            xaxis_title="Ciclo de vuelo",
            yaxis=dict(
                categoryorder="array", categoryarray=[_etiqueta_unidad(float(u)) for u in reversed(unidades_vistas)],
            ),
        )
        style_axes(fig_fleet)
        st.plotly_chart(
            fig_fleet, theme=None,
            alt="Cronología de estado por unidad: verde apto, ámbar inspección y rojo hangar a lo largo de los ciclos.",
        )

    with st.container(border=True):
        st.subheader("Cola de mantenimiento", icon=":material/assignment:")
        st.caption("Decisión por límite inferior conformal, no por la predicción puntual.")
        display = pd.DataFrame(
            {
                "Motor": [_etiqueta_unidad(float(u)) for u in snapshot["unit"]],
                "Ciclo": snapshot["cycle"],
                "RUL real": snapshot["y_true"],
                "RUL p35": snapshot["pred"],
                "L_inf (riesgo)": snapshot["lower"],
                "L_sup": snapshot["upper"],
                "Estado": snapshot["state_label"],
                "Regla": snapshot["rule"],
                "Por qué decide así": [
                    (
                        f"L_inf {lo:.1f} ≥ {threshold_apto:.0f}: vuela"
                        if estado == L.AIRWORTHY else
                        f"L_inf {lo:.1f} < {threshold_aog:.0f}: al hangar"
                        if estado == L.AOG else
                        (f"L_inf {lo:.1f} entre {threshold_aog:.0f} y "
                         f"{threshold_apto:.0f}: vigilar"
                         if pd.notna(lo) else "sin telemetría en este ciclo")
                    )
                    for lo, estado in zip(snapshot["lower"], snapshot["state"])
                ],
                "Acción automática asignada": snapshot["action"],
            }
        )

        def _row_style(row: pd.Series) -> list[str]:
            label = row["Estado"]
            state = next((s for s, name in L.STATE_LABELS.items() if name == label), L.NO_DATA)
            return [STATE_BG[state]] * len(row)

        styled = display.style.apply(_row_style, axis=1)
        st.dataframe(
            styled,
            hide_index=True,
            column_config={
                "Ciclo": st.column_config.NumberColumn("Ciclo", format="%d"),
                "RUL real": st.column_config.NumberColumn("RUL real", format="%.1f"),
                "RUL p35": st.column_config.NumberColumn("RUL p35", format="%.1f",
                                                help="Cuantil 0.35 de la RUL (ADR-003)."),
                "L_inf (riesgo)": st.column_config.NumberColumn(
                    "L_inf (riesgo)", format="%.1f",
                    help="Límite inferior de la banda conformal: es lo que decide el estado.",
                ),
                "L_sup": st.column_config.NumberColumn("L_sup", format="%.1f"),
                "Regla": st.column_config.TextColumn(
                    "Regla",
                    help="Regla de la pasada A que firmó el estado (mia.motor).",
                ),
            },
            alt="Cola de mantenimiento: estado y acción por unidad en el ciclo simulado.",
        )

        clamped = snapshot[snapshot["clamped"]]
        if not clamped.empty:
            st.caption(
                "Limitadas a su último ciclo evaluado: "
                + ", ".join(
                    f"U{int(r.unit)} en {int(r.scored_cycle)}" for r in clamped.itertuples()
                )
                + ". No se extrapola más allá de la vida registrada."
            )

        st.info(
            f"**Apto** si `L_inf ≥ {threshold_apto:.0f}` · "
            f"**inspección** si `{threshold_aog:.0f} ≤ L_inf < {threshold_apto:.0f}` · "
            f"**hangar** si `L_inf < {threshold_aog:.0f}`. El estado se decide con el límite "
            "inferior de la banda: la predicción puntual puede estar por encima del umbral y la "
            "unidad aun así quedar inmovilizada. Es deliberado (ADR-008): el error del modelo no "
            "es simétrico entre motores.",
            title="Regla de negocio",
            icon=":material/shield:",
        )

    with st.expander("Comparar con otros umbrales", icon=":material/compare:"):
        st.caption(
            "Recalcula la flota con un segundo juego de umbrales (sin re-puntuar) y "
            "muestra qué cambiaría respecto a los en vigor."
        )
        comp_a = st.number_input("Apto alternativo", min_value=1.0, max_value=100.0,
                                  value=threshold_apto + 5.0, step=1.0, key="comp_apto")
        comp_h = st.number_input("Hangar alternativo", min_value=0.0, max_value=99.0,
                                  value=threshold_aog + 5.0, step=1.0, key="comp_aog")
        if comp_h >= comp_a:
            st.error("El hangar alternativo debe ser menor que el apto alternativo.",
                      icon=":material/rule:")
        else:
            snap_b = L.fleet_snapshot(frame, cycle, comp_a, comp_h)
            cuenta_a = snapshot["state"].value_counts()
            cuenta_b = snap_b["state"].value_counts()
            comp = pd.DataFrame({
                "Estado": [L.STATE_LABELS.get(s, s) for s in L.STATE_LABELS],
                "En vigor": [int(cuenta_a.get(s, 0)) for s in L.STATE_LABELS],
                "Alternativo": [int(cuenta_b.get(s, 0)) for s in L.STATE_LABELS],
            })
            st.dataframe(comp, hide_index=True,
                         alt="Comparativa de estados de flota entre umbrales en vigor y alternativos.")
            merged = snapshot[["unit", "state"]].merge(
                snap_b[["unit", "state"]], on="unit", suffixes=("", "_alt"))
            cambian = merged[merged["state"] != merged["state_alt"]]
            if cambian.empty:
                st.caption("Nada cambiaría: los mismos estados con los otros umbrales.")
            else:
                st.dataframe(
                    pd.DataFrame({
                        "Motor": [f"U{int(u)}" for u in cambian["unit"]],
                        "Ahora": [L.STATE_LABELS.get(s, s) for s in cambian["state"]],
                        "Con alternativos": [L.STATE_LABELS.get(s, s)
                                              for s in cambian["state_alt"]],
                    }),
                    hide_index=True,
                    alt="Unidades que cambiarían de estado con los umbrales alternativos.",
                )

    with st.expander("Historial de la unidad: cómo llegó a este estado",
                      icon=":material/history:"):
        hist = UR.estado_por_ciclo(frame)
        hu = hist[hist["unit"] == unit].sort_values("cycle").reset_index(drop=True)
        if hu.empty:
            st.caption("Sin ciclos evaluados para esta unidad.")
        else:
            rachas, inicio = [], hu.iloc[0]
            previo = None
            for _, fila_h in hu.iterrows():
                if previo is not None and fila_h["decision"] != previo["decision"]:
                    rachas.append({"Desde": int(previo["cycle"]),
                                   "Hasta": int(fila_h["cycle"] - 1),
                                   "Estado": L.STATE_LABELS.get(previo["decision"],
                                                                  str(previo["decision"])),
                                   "L_inf mín": round(float(hu[(hu["cycle"] >= previo["cycle"]) &
                                                                 (hu["cycle"] < fila_h["cycle"])]
                                                              ["lower"].min()), 1)})
                    previo = fila_h
                elif previo is None:
                    previo = fila_h
            if previo is not None:
                rachas.append({"Desde": int(previo["cycle"]),
                               "Hasta": int(hu["cycle"].max()),
                               "Estado": L.STATE_LABELS.get(previo["decision"],
                                                              str(previo["decision"])),
                               "L_inf mín": round(float(hu[hu["cycle"] >= previo["cycle"]]
                                                          ["lower"].min()), 1)})
            st.dataframe(pd.DataFrame(rachas), hide_index=True,
                         alt="Rachas de estado de la unidad seleccionada a lo largo de los ciclos.")

    with st.container(border=True):
        st.subheader("Motor de reglas · traza del caso", icon=":material/rule:")
        fila = snapshot[snapshot["unit"] == unit].iloc[0]
        st.caption(
            "Pasada A de `mia.motor` sobre la unidad seleccionada: la misma función del "
            "cuaderno de práctica, no una reclasificación paralela. Gana la regla de "
            "mayor prioridad que se cumpla."
        )
        if bool(fila["reached"]):
            traza = UR.traza_decision(float(fila["lower"]), umbrales)
            st.markdown(
                f"**U{int(unit)} · ciclo {cycle}** · `L_inf = {fila['lower']:.1f}` → "
                f"**{traza['decision'] or 'sin decisión'}** · reglas: "
                + (" → ".join(traza["usadas"]) or "(ninguna)")
            )
            for linea in traza["porque"]:
                st.caption(linea)
        else:
            st.caption(
                "La unidad todavía no tiene ventanas evaluadas en este ciclo: el motor no "
                "emite una decisión que no pueda sostener."
            )
        catalogo = pd.DataFrame(UR.catalogo_decision()).rename(
            columns={"regla": "Regla", "prioridad": "Prioridad", "porque": "Porqué"}
        )
        st.dataframe(
            catalogo,
            hide_index=True,
            column_config={
                "Prioridad": st.column_config.NumberColumn("Prioridad", format="%d"),
            },
            alt="Reglas de la pasada A, con su prioridad y su justificación.",
        )

    order = L.work_order(snapshot, provenance, threshold_apto, threshold_aog,
                         banda=banda_en_uso, correccion=correccion_en_uso)
    blocked = order["unidades"]
    with st.container(border=True):
        st.subheader("Orden de trabajo", icon=":material/description:")
        if blocked:
            st.caption(
                f"{len(blocked)} unidad(es) bloqueada(s) en el ciclo {cycle}. El documento lleva "
                "el hash del artefacto y los umbrales en vigor."
            )
            with st.container(horizontal=True):
                st.download_button(
                    "Descargar orden (JSON)",
                    data=json.dumps(order, ensure_ascii=False, indent=2),
                    file_name=f"orden_mantenimiento_ds02_ciclo{cycle}.json",
                    mime="application/json",
                    type="primary",
                    icon=":material/download:",
                )
                st.download_button(
                    "Descargar orden (CSV)",
                    data=L.work_order_csv(order),
                    file_name=f"orden_mantenimiento_ds02_ciclo{cycle}.csv",
                    mime="text/csv",
                    icon=":material/table_view:",
                )
        else:
            st.success(
                f"Ninguna unidad en hangar en el ciclo {cycle}. No se emite orden de trabajo.",
                title="Flota disponible",
                icon=":material/check_circle:",
            )
            parte = L.parte_disponibilidad(snapshot, provenance, threshold_apto,
                                            threshold_aog)
            with st.container(horizontal=True):
                st.download_button(
                    "Descargar parte de disponibilidad (JSON)",
                    data=json.dumps(parte, ensure_ascii=False, indent=2),
                    file_name=f"parte_disponibilidad_ds02_ciclo{cycle}.json",
                    mime="application/json",
                    icon=":material/download:",
                    help="Deja constancia firmable de que se miró la flota y no había nada que derivar.",
                )
                st.download_button(
                    "Descargar parte de flota (CSV)",
                    data=snapshot[["unit", "cycle", "state", "rule"]].to_csv(index=False),
                    file_name=f"parte_flota_ds02_ciclo{cycle}.csv",
                    mime="text/csv",
                    icon=":material/table_view:",
                )


# ------------------------------------------------------ gemelos y hangar
with st.container(border=True):
    st.subheader("Gemelos registrados", icon=":material/precision_manufacturing:")
    aviso_gemelo = st.session_state.get("twin_flash")
    if aviso_gemelo:
        del st.session_state["twin_flash"]
        st.toast(aviso_gemelo, icon=":material/check_circle:")
    # El muro manda: una tarjeta de gemelo apunta aqui. Se consume en cuanto se
    # lee, para que no vuelva a salir en el siguiente render.
    gemelo_pendiente = st.session_state.pop("_gemelo_pendiente", None)
    if gemelo_pendiente:
        if gemelo_pendiente in gemelos:
            _estado_pendiente = T.estado_actual(gemelos[gemelo_pendiente], umbrales)
            st.caption(
                f"**{gemelo_pendiente}**: "
                f"{L.STATE_LABELS.get(_estado_pendiente['decision'],
                                      str(_estado_pendiente['decision']))} con los "
                f"umbrales en vigor, L_inf {_estado_pendiente['lower_min']:.1f} ciclos."
            )
        else:
            st.caption(f"El motor `{gemelo_pendiente}` ya no está registrado.")
    if not gemelos:
        st.caption(
            "Ningún motor externo registrado todavía. Puntúa uno en «Evaluar unidad "
            "nueva» y añádelo: la serie queda guardada y su estado se recalcula con "
            "los umbrales en vigor, sin volver a llamar al modelo."
        )
    else:
        filas_gemelos = []
        for gemelo_id, gemelo in gemelos.items():
            estado_g = T.estado_actual(gemelo, umbrales)
            metricas_g = T.metricas_verdad(gemelo)
            filas_gemelos.append({
                "Motor": gemelo_id,
                "Ciclo": estado_g["cycle"],
                "L_inf": estado_g["lower_min"],
                "Estado": L.STATE_LABELS.get(estado_g["decision"],
                                             str(estado_g["decision"])),
                "Regla": estado_g["regla"],
                "Banda": gemelo["banda"],
                "Verdad": ("sin reportar" if not metricas_g else
                           f"{metricas_g['rul_real']:.0f} · "
                           f"{'dentro' if metricas_g['cubierta'] else 'fuera'}"),
                "Huella": gemelo["fingerprint"][:8],
            })
        st.dataframe(
            pd.DataFrame(filas_gemelos),
            hide_index=True,
            column_config={
                "Ciclo": st.column_config.NumberColumn("Ciclo", format="%d"),
                "L_inf": st.column_config.NumberColumn("L_inf", format="%.2f"),
                "Huella": st.column_config.TextColumn("Huella", help="SHA-256 de la tabla puntuada."),
            },
            alt="Motores externos registrados con su estado recalculado, la regla aplicada y la banda usada.",
        )
        resumen_gemelos = T.resumen(gemelos)
        if resumen_gemelos["con_verdad"]:
            st.caption(
                f"{resumen_gemelos['con_verdad']} gemelo(s) con verdad reportada · "
                f"cobertura {resumen_gemelos['cubiertos']}/{resumen_gemelos['con_verdad']} · "
                f"MAE {resumen_gemelos['mae']:.2f} ciclos"
            )
        with st.expander("Reportar la RUL real de un gemelo", icon=":material/fact_check:"):
            elegido_v = st.selectbox("Motor", list(gemelos), key="truth_engine")
            ciclo_v = st.number_input(
                "Ciclo en que se conoció", min_value=0.0, step=1.0,
                value=float(gemelos[elegido_v]["serie"][-1]["cycle"]),
                key=f"truth_cycle_{elegido_v}",
            )
            rul_v = st.number_input(
                "RUL real (ciclos)", min_value=0.0, step=1.0, value=0.0,
                key=f"truth_rul_{elegido_v}",
            )
            st.caption(
                "La cobertura se mide contra la ventana más pesimista de ese ciclo: "
                "si esa banda cubre la verdad, la decisión que la acompañó era defendible."
            )
            if st.button("Guardar verdad", icon=":material/save:", key="truth_save"):
                try:
                    actualizado = T.con_verdad(gemelos[elegido_v], rul_v, ciclo_v)
                except ValueError as exc:
                    st.error(str(exc), title="Valor no válido", icon=":material/rule:")
                else:
                    st.session_state["twins"] = {**gemelos, elegido_v: actualizado}
                    _guardar_registros()
                    st.rerun()

        with st.expander("Documentar un gemelo", icon=":material/description:"):
            motor_doc = st.selectbox("Motor", list(gemelos), key="twin_doc")
            gemelo_doc = gemelos[motor_doc]
            estado_doc = T.estado_actual(gemelo_doc, umbrales)
            orden_gemelo = INF.live_work_order(
                T.vista_resultado(gemelo_doc),
                {"source": gemelo_doc["source"],
                 "registrado_en": gemelo_doc["created_at"],
                 "huella": gemelo_doc["fingerprint"]},
                threshold_apto, threshold_aog,
                banda=gemelo_doc["banda"], correccion=gemelo_doc["correccion"],
            )
            # El documento describe un gemelo guardado, no una evaluación recién hecha.
            orden_gemelo["documento"] = f"Orden de mantenimiento — gemelo {motor_doc}"
            orden_gemelo["modo"] = "gemelo registrado (serie guardada, sin repuntuar)"
            ciclo_doc = estado_doc["cycle"]
            # El id lo escribe el usuario: un `/` en el nombre del fichero rompe la descarga.
            slug_doc = _slug_motor(motor_doc.lower())
            etiqueta_doc = L.STATE_LABELS.get(estado_doc["decision"],
                                             str(estado_doc["decision"]))
            st.caption(
                f"Estado con los umbrales en vigor: **{etiqueta_doc}**"
                + (f" en el ciclo {ciclo_doc:.0f}" if ciclo_doc is not None else "")
                + ". El documento describe la peor ventana de ese ciclo, con la huella y "
                "la banda que se guardaron al puntuar: no se llama al modelo."
            )
            with st.container(horizontal=True):
                st.download_button(
                    "Descargar ficha del gemelo (JSON)",
                    data=json.dumps(orden_gemelo, ensure_ascii=False, indent=2),
                    file_name=f"orden_mantenimiento_{slug_doc}.json",
                    mime="application/json",
                    icon=":material/download:",
                    key="twin_doc_json",
                )
                st.download_button(
                    "Descargar ficha del gemelo (CSV)",
                    data=L.work_order_csv(orden_gemelo),
                    file_name=f"orden_mantenimiento_{slug_doc}.csv",
                    mime="text/csv",
                    icon=":material/table_view:",
                    key="twin_doc_csv",
                )

        with st.expander("Eliminar un gemelo", icon=":material/delete:"):
            borrar = st.selectbox("Motor", list(gemelos), key="twin_del")
            st.caption(
                "Borrar un gemelo no toca su registro de hangar: el gemelo es lo que el "
                "modelo dijo, el registro es lo que pasó después."
            )
            if st.button("Eliminar gemelo", icon=":material/delete_forever:",
                         key="twin_del_btn"):
                st.session_state["twins"] = T.eliminar(gemelos, borrar)
                _guardar_registros()
                st.session_state["twin_flash"] = f"Gemelo `{borrar}` eliminado."
                st.rerun()


def _panel_gemelo() -> None:
    """Detalle del gemelo registrado: su curva, su banda y su ventana.

    Antes no existía. La serie del gemelo (cycle, pred, lower, upper, start_row)
    ya estaba guardada en `twins`; el muro la dibujaba y nada más. Aquí se ve
    completa, con la banda y con las dos preguntas que un gemelo digital tiene
    que responder: cuánto le queda y en qué ventana se basó la decisión.

    Se alimenta de `st.session_state`, nunca de un global de módulo: es un
    contenedor de primer nivel y se re-ejecuta completo en cada pasada.
    """
    with st.container(border=True):
        st.subheader("Gemelo digital · detalle",
                     icon=":material/precision_manufacturing:")
        st.caption(
            "El gemelo es lo que el modelo dijo, guardado una vez. Su estado se "
            "recalcula con los umbrales en vigor sin volver a llamar al modelo: "
            "la serie no cambia, la lectura sí."
        )
        _gemelos = st.session_state.get("twins") or {}
        if not _gemelos:
            st.caption(
                "Ningún gemelo registrado todavía. Puntúa un motor en «Evaluar "
                "unidad nueva» y aparece aquí con su curva completa."
            )
            return
        _elegido = st.selectbox(
            "Gemelo", list(_gemelos), key="gemelo_detalle_sel",
            help="Motores registrados en esta sesión, con su serie guardada.",
        )
        _gemelo = _gemelos[_elegido]
        _curva = T.ciclo_a_ciclo(_gemelo, umbrales)
        if _curva.empty:
            st.caption(f"`{_elegido}` no tiene serie que dibujar.")
            return

        _ultima = _curva.iloc[-1]
        _decision = str(_ultima["decision"])
        _pred = float(_ultima["pred"])
        _lo = float(_ultima["lower_min"])
        _ciclo_ult = int(_ultima["cycle"])

        # Ciclos hasta el umbral: la misma pregunta que la flota le hace a la
        # caché, hecha aquí sobre la serie guardada.
        _cruce = _curva[_curva["lower_min"] < umbrales["hangar"]]
        _falta = (None if _cruce.empty
                  else int(_cruce["cycle"].min()) - _ciclo_ult)
        _falta_txt = ("no cruza el umbral en la vida registrada" if _falta is None
                      else ("ya está por debajo del umbral" if _falta <= 0
                            else f"{_falta} ciclos"))

        st.metric("RUL p35 (conservadora)", f"{_pred:.1f}", "cuantil 0.35",
                  border=True, delta_color="off", icon=":material/speed:",
                  help="Cuantil 0.35 de la RUL (ADR-003). El estado no lo decide "
                       "este número: lo decide L_inf.")
        st.metric("L_inf (decide)", f"{_lo:.1f}", "ciclos",
                  border=True, delta_color="off", icon=":material/trending_down:",
                  help="Límite inferior de la banda al 90 %. Es el número que gobierna "
                       "la decisión de hangar (ADR-008).")
        st.metric("Estado", L.STATE_LABELS.get(_decision, _decision),
                  str(_ultima["regla"] or "(sin regla)"),
                  border=True, delta_color="off", icon=":material/rule:")
        st.metric("Ciclos hasta el umbral", _falta_txt, f"ciclo {_ciclo_ult}",
                  border=True, delta_color="off", icon=":material/hourglass_bottom:",
                  help="Primer ciclo de la serie guardada en que L_inf cae por debajo "
                       "del umbral de hangar, menos el último ciclo registrado.")

        # La ventana que decidió: `vista_resultado` ya la elige; aquí se cita.
        _vista = T.vista_resultado(_gemelo)
        _vent = _vista["windows"].iloc[0]
        st.caption(
            f"La ventana que decide es la **{int(_vent['window'])}** del ciclo "
            f"**{int(_vent['cycle'])}**, que empieza en la fila "
            f"**{int(_vent['start_row'])}** de la tabla puntuada: la más pesimista "
            "de ese ciclo. Es el dato que sostiene el estado."
        )

        _fig = go.Figure()
        _fig.add_trace(go.Scatter(
            x=_curva["cycle"], y=_curva["upper"], mode="lines",
            line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        _fig.add_trace(go.Scatter(
            x=_curva["cycle"], y=_curva["lower_media"], mode="lines",
            line=dict(width=0), name="Banda 90 %", fill="tonexty",
            fillcolor="rgba(56,189,248,0.18)", hoverinfo="skip",
        ))
        _fig.add_trace(go.Scatter(
            x=_curva["cycle"], y=_curva["pred"], mode="lines", name="RUL p35",
            line=dict(width=2, color=SKY),
            hovertemplate="ciclo %{x}<br>RUL %{y:.1f}<extra></extra>",
        ))
        _fig.add_trace(go.Scatter(
            x=_curva["cycle"], y=_curva["lower_min"], mode="lines",
            name="L_inf (decide)", line=dict(width=2, color=ROSE),
            hovertemplate="ciclo %{x}<br>L_inf %{y:.1f}<extra></extra>",
        ))
        _fig.add_hline(
            y=umbrales["hangar"], line_color=ROSE, line_dash="dash", line_width=1.5,
            annotation_text=f"hangar ({umbrales['hangar']:.0f})",
            annotation_position="top right",
            annotation_font=dict(color=ROSE, size=11),
        )
        _fig.update_layout(**chart_layout(height=340, hovermode="closest"))
        style_axes(_fig, x_title="Ciclo de vuelo", y_title="RUL (ciclos)")
        st.plotly_chart(
            _fig, theme=None,
            alt=f"Curva de RUL del gemelo {_elegido} con su banda conformal al 90 %, "
                "el límite inferior que decide y el umbral de hangar.",
        )
        st.caption(
            "La banda es la de la serie guardada: no se recalibra al mover los "
            "umbrales, porque la calibración es parte del artefacto. Mover el "
            "umbral cambia la lectura, no la banda."
        )


_panel_gemelo()

with st.container(border=True):
    st.subheader("Hangar · ciclo de vida", icon=":material/warehouse:")
    resumen_h = HGR.resumen(registros)
    with st.container(horizontal=True):
        st.metric("Registros", resumen_h["total"], border=True, delta_color="off",
                  icon=":material/inventory_2:")
        st.metric("Abiertos", resumen_h["abiertos"], border=True, delta_color="off",
                  icon=":material/pending_actions:")
        st.metric("En taller", resumen_h["por_estado"][HGR.TALLER], border=True,
                  delta_color="off", icon=":material/build:")
    if not registros:
        st.caption(
            "Ningún registro abierto. Al derivar una unidad se congela aquí la decisión "
            "de entrada, con sus umbrales: mover los sliders después no reescribe la "
            "historia."
        )
    else:
        filas_hangar = []
        for registro in HGR.cola(registros):
            decision_hoy = UR.traza_decision(registro["entrada"]["lower"], umbrales)["decision"]
            revision = HGR.revision(registro, umbrales, decision_hoy)
            filas_hangar.append({
                "Unidad": registro["unidad"],
                "Estado": HGR.ETIQUETAS.get(registro["estado"], registro["estado"]),
                "L_inf de entrada": registro["entrada"]["lower"],
                "Umbral de entrada": registro["entrada"]["umbrales"]["hangar"],
                "Regla": registro["entrada"]["regla"],
                "Hoy": "coincide" if not revision["cambia"] else revision["hoy"],
            })
        st.dataframe(
            pd.DataFrame(filas_hangar),
            hide_index=True,
            column_config={
                "L_inf de entrada": st.column_config.NumberColumn(
                    "L_inf de entrada", format="%.2f"),
                "Umbral de entrada": st.column_config.NumberColumn(
                    "Umbral de entrada", format="%.0f"),
            },
            alt="Cola de hangar ordenada por urgencia, con la decisión congelada y la de hoy.",
        )

    candidatos = {}
    for _, fila in snapshot[snapshot["state"] == L.AOG].iterrows():
        # La clave sale del registro: una alta responde a su matricula, un motor
        # de caché a U<int>. Antes se montaba a mano con f"U{int(unit)}" y las
        # altas entraban al hangar como U-1000.
        candidatos[F.clave_de(float(fila["unit"]), _registro())] = {
            "ciclo": int(fila["cycle"]),
            "lower": float(fila["lower"]),
            "regla": str(fila["rule"]),
        }
    for gemelo_id, gemelo in gemelos.items():
        estado_g = T.estado_actual(gemelo, umbrales)
        if estado_g["decision"] == L.AOG:
            candidatos[gemelo_id] = {
                "ciclo": int(estado_g["cycle"] or 0),
                "lower": float(estado_g["lower_min"]),
                "regla": estado_g["regla"],
            }
    disponibles = [clave for clave in candidatos if clave not in registros]
    if disponibles:
        with st.form("hangar_abrir"):
            elegido_h = st.selectbox("Unidad a derivar", disponibles)
            nota_alta = st.text_input("Nota de entrada", value="")
            if st.form_submit_button("Abrir registro", icon=":material/login:"):
                datos = candidatos[elegido_h]
                st.session_state["hangar"] = {
                    **registros,
                    elegido_h: HGR.abrir(elegido_h, datos["ciclo"], datos["lower"],
                                         umbrales, datos["regla"], nota=nota_alta),
                }
                _guardar_registros()
                st.rerun()
    else:
        st.caption(
            "No hay unidades en hangar sin registro en este ciclo, ni gemelos "
            "derivados pendientes de abrir."
        )

    if registros:
        with st.container(border=True):
            unidad_sel = st.selectbox("Registro", list(registros), key="hangar_sel")
            actual = registros[unidad_sel]["estado"]
            destino = st.selectbox(
                "Nuevo estado",
                HGR.permitidas(actual),
                format_func=lambda estado: HGR.ETIQUETAS.get(estado, estado),
                key="hangar_destino",
                help="Solo se ofrecen los estados alcanzables desde el actual.",
            )
            nota_mov = st.text_input("Nota del evento", key="hangar_nota")
            if st.button("Registrar movimiento", icon=":material/logout:", key="hangar_mover"):
                try:
                    movido = HGR.avanzar(registros[unidad_sel], destino,
                                         int(cycle), nota=nota_mov)
                except ValueError as exc:
                    st.error(str(exc), title="Movimiento no permitido",
                             icon=":material/rule:")
                else:
                    st.session_state["hangar"] = {**registros, unidad_sel: movido}
                    _guardar_registros()
                    st.rerun()

    with st.expander("Restablecer demo", icon=":material/restart_alt:"):
        st.caption(
            "Borra los gemelos registrados y los registros de hangar (sesión y disco). "
            "La caché y el artefacto no se tocan."
        )
        confirma = st.checkbox("Confirmo que quiero borrar la flota registrada",
                                key="reset_confirm")
        if st.button("Borrar gemelos y hangar", icon=":material/delete_forever:",
                       disabled=not confirma, key="reset_demo"):
            st.session_state["twins"] = {}
            st.session_state["hangar"] = {}
            _guardar_registros()
            st.session_state["twin_flash"] = "Flota registrada borrada."
            st.rerun()
    st.subheader("Demo en vivo", icon=":material/movie:")
    st.caption(
        "Deja la app en el estado desde el que se cuenta la historia: umbrales "
        "30/25, ciclo 29 y la unidad 14, que es la que entra en hangar."
    )
    if st.button("Cargar escenario de demo", icon=":material/play_circle:",
                 key="demo_cargar", type="primary"):
        st.session_state["_demo_pendiente"] = True
        _log("Escenario de demo cargado (umbrales 30/25, ciclo 29, U14).")
        st.rerun()


# ------------------------------------------------------------------- tab 2


with tab_motor:
    # ------------------------------------------------------------- el gemelo
    # Una sala, una respuesta: ¿por qué está así este motor? Su verdad estaba
    # repartida en cuatro pestañas; aquí está junta.
    _fila_g = snapshot[snapshot["unit"] == unit].iloc[0]
    _etiqueta_g = _etiqueta_unidad(float(unit))
    _pred_g = float(_fila_g["pred"]) if pd.notna(_fila_g["pred"]) else 0.0
    _lo_g = float(_fila_g["lower"]) if pd.notna(_fila_g["lower"]) else float("nan")

    with st.container(border=True):
        st.subheader(f"Vista consolidada · {_etiqueta_g}",
                     icon=":material/precision_manufacturing:")
        st.caption(
            "Lo que dice la caché sobre este motor, junto: la métrica que decide, "
            "la traza de la regla y el ciclo de vida del hangar. El gemelo "
            "registrado tiene su propio panel, arriba."
        )
        _gauge_col, _decision_col = st.columns([1, 2])
        with _gauge_col:
            _gauge = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=round(_pred_g, 1),
                    number={"suffix": " ciclos", "font": {"color": INK, "size": 26}},
                    title={"text": "RUL restante", "font": {"color": MUTED, "size": 13}},
                    gauge={
                        "axis": {"range": [0, max_life], "tickfont": {"color": MUTED}},
                        "bar": {"color": SKY, "thickness": 0.4},
                        "bgcolor": SURFACE,
                        "bordercolor": GRID,
                        "steps": [
                            {"range": [0, threshold_aog],
                             "color": "rgba(248,113,113,0.28)"},
                            {"range": [threshold_aog, threshold_apto],
                             "color": "rgba(245,158,11,0.22)"},
                            {"range": [threshold_apto, max_life],
                             "color": "rgba(52,211,153,0.22)"},
                        ],
                        "threshold": {"line": {"color": ROSE, "width": 3},
                                      "thickness": 0.7, "value": threshold_aog},
                    },
                )
            )
            _gauge.update_layout(**chart_layout(height=240, showlegend=False,
                                                margin=dict(l=18, r=18, t=46, b=8)))
            st.plotly_chart(
                _gauge, theme=None,
                alt=f"Gauge de RUL restante de {_etiqueta_g}: {_pred_g:.1f} ciclos, con "
                    f"la zona de hangar por debajo de {threshold_aog:.0f} sombreada.",
            )
        with _decision_col:
            st_badge_estado(_fila_g["state"])
            with st.container(horizontal=True):
                st.metric("RUL p35 (conservadora)",
                          f"{_pred_g:.1f}" if pd.notna(_fila_g["pred"]) else "—",
                          "cuantil 0.35", border=True, delta_color="off",
                          icon=":material/speed:",
                          help="Cuantil 0.35 de la RUL (ADR-003): conservador. "
                               "El estado lo decide L_inf, el limite inferior de la banda.")
                st.metric("L_inf (decide)",
                          f"{_lo_g:.1f}" if pd.notna(_fila_g["lower"]) else "—",
                          "ciclos", border=True, delta_color="off",
                          icon=":material/trending_down:")
                st.metric("Regla que decide", str(_fila_g["rule"] or "(ninguna)"),
                          "pasada A · mia.motor", border=True, delta_color="off",
                          icon=":material/rule:")
            if pd.notna(_lo_g):
                for linea in UR.traza_decision(_lo_g, umbrales)["porque"]:
                    st.caption(linea)
            _registro_g = registros.get(F.clave_de(float(unit), _registro()))
            if _registro_g:
                st.markdown(
                    f"**Ciclo de vida del hangar**: "
                    f"{HGR.ETIQUETAS.get(_registro_g['estado'], _registro_g['estado'])}"
                    f" · abierto en el ciclo {_registro_g['entrada']['ciclo']} con "
                    f"`L_inf = {_registro_g['entrada']['lower']:.1f}`."
                )
            else:
                st.markdown("**Ciclo de vida del hangar**: sin registro abierto.")
            _bloqueada = next(
                (u for u in order["unidades"] if int(u["unidad"]) == int(unit)), None)
            if _bloqueada:
                st.markdown(
                    f"**Orden de trabajo**: derivación a hangar · "
                    f"`L_inf {_bloqueada['limite_inferior']:.1f}` < {threshold_aog:.0f} · "
                    f"{_bloqueada['accion']}"
                )
            else:
                st.markdown(
                    "**Orden de trabajo**: ninguna para este motor en el ciclo del reloj.")
        # Radiografía de sensores: la misma señal que en su pestaña, sin salir de aquí.
        _presiones = L.CHANNEL_GROUPS["Presiones"]
        _per_cycle_g = (
            telemetry[telemetry["unit"] == unit]
            .groupby("cycle", as_index=False)[_presiones]
            .mean(numeric_only=True)
        )
        if not _per_cycle_g.empty:
            st.plotly_chart(
                fig_deriva(_per_cycle_g, _presiones,
                           int(_per_cycle_g["cycle"].max()),
                           critical_start, threshold_aog, height=220),
                theme=None,
                alt=f"Radiografía de sensores de {_etiqueta_g}: deriva porcentual de las "
                    "presiones frente a su línea base sana.",
            )
            st.caption(
                "Radiografía de sensores (presiones) respecto a la línea base sana del "
                "propio motor. La pestaña 3 la muestra por grupo de canales."
            )

    # -------------------- comparador: 2-3 motores superpuestos
    with st.container(border=True):
        st.subheader("Comparador · superpone trayectorias",
                     icon=":material/compare_arrows:")
        st.caption(
            "Elige 2–3 motores y superpone su límite inferior — lo que decide — y su "
            "predicción puntual, solo para comparar. La línea roja es el umbral de hangar."
        )
        _comparar = st.multiselect(
            "Motores a comparar",
            unidades_vistas,
            default=unidades_vistas[:2],
            format_func=lambda u: _etiqueta_unidad(float(u)),
            key="comparador_unidades",
            help="El límite inferior es lo que decide el estado; la predicción puntual "
                 "se dibuja solo para comparar.",
        )
        if _comparar:
            _fig_c = go.Figure()
            for u in _comparar:
                _curva_c = curves[u]
                _et_c = _etiqueta_unidad(float(u))
                _fig_c.add_trace(go.Scatter(
                    x=_curva_c["cycle"], y=_curva_c["lower"], mode="lines",
                    name=f"L_inf · {_et_c}", line=dict(width=2),
                ))
                _fig_c.add_trace(go.Scatter(
                    x=_curva_c["cycle"], y=_curva_c["pred"], mode="lines",
                    name=f"RUL predicha · {_et_c}", line=dict(width=1.2, dash="dot"),
                ))
            _fig_c.add_hline(
                y=threshold_aog, line_color=ROSE, line_dash="dash", line_width=1.5,
                annotation_text=f"hangar ({threshold_aog:.0f})",
                annotation_position="top right", annotation_font=dict(color=ROSE, size=11),
            )
            _fig_c.update_layout(**chart_layout(height=380))
            style_axes(_fig_c, x_title="Ciclo de vuelo", y_title="RUL (ciclos)")
            st.plotly_chart(
                _fig_c, theme=None,
                alt="Comparador de trayectorias: límite inferior y RUL predicha de los "
                    "motores seleccionados.",
            )

    with st.container(border=True):
        st.subheader("Trayectoria de RUL y banda conformal", icon=":material/ssid_chart:")
        st.caption(
            f"Unidad {int(unit)} · {len(_wu)} ventanas evaluadas · cobertura por ventana "
            f"{coverage:.0%} (objetivo 90 %). El gráfico dibuja medias por ciclo; "
            f"la decisión y este número usan cada ventana."
        )
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=curve["cycle"], y=curve["upper"], mode="lines",
                line=dict(width=0), name="Límite superior", hoverinfo="skip",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=curve["cycle"], y=curve["lower"], mode="lines",
                line=dict(width=0), fill="tonexty",
                fillcolor="rgba(56, 189, 248, 0.18)",
                name="Banda conformal 90 %",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=curve["cycle"], y=curve["pred"], mode="lines",
                line=dict(color=SKY, width=3), name="RUL predicha (ensamble)",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=curve["cycle"], y=curve["y_true"], mode="lines",
                line=dict(color="#94a3b8", width=1.6, dash="dot"), name="RUL real",
            )
        )
        if alarm_cycle is not None:
            at_alarm = curve.loc[curve["cycle"] == alarm_cycle]
            fig.add_trace(
                go.Scatter(
                    x=at_alarm["cycle"], y=at_alarm["pred"], mode="markers",
                    marker=dict(color=ROSE, size=13, symbol="x", line=dict(width=2)),
                    name=f"Alarma AOG (ciclo {alarm_cycle})",
                )
            )
        fig.add_hrect(
            y0=0, y1=threshold_aog, fillcolor=ROSE, opacity=0.10, line_width=0,
            annotation_text=f"zona de hangar (RUL < {threshold_aog:.0f})",
            annotation_position="top left", annotation_font_size=11,
            annotation_font_color="#fca5a5",
        )
        fig.add_vline(
            x=current, line_dash="dot", line_color=INK, line_width=1.5,
            annotation_text=f"ciclo {current}", annotation_position="top",
            annotation_font=dict(color=INK, size=11),
        )
        fig.update_layout(**chart_layout(height=430, hovermode="x unified"))
        style_axes(fig, x_title="Ciclo de vuelo", y_title="RUL (ciclos restantes)")
        st.plotly_chart(
            fig, theme=None,
            alt="RUL real y predicha a lo largo de la vida del motor, con la banda conformal y la zona de hangar sombreada.",
        )

    with st.container(horizontal=True):
        if unit_metrics is not None:
            st.metric("RMSE", f"{unit_metrics['rmse']:.2f}", f"U{int(unit)}", border=True,
                      icon=":material/analytics:", delta_color="off")
            st.metric("MAE", f"{unit_metrics['mae']:.2f}", f"U{int(unit)}", border=True,
                      icon=":material/straighten:", delta_color="off")
            st.metric("Sesgo (pred − real)", f"{unit_metrics['bias']:+.2f}", "ciclos", border=True,
                      icon=":material/swap_vert:", delta_color="off")
        else:
            st.caption(f"Aeronave de alta {_etiqueta_unidad(float(unit))}: sin verdad en caché para RMSE/MAE/sesgo.")
        st.metric("Cobertura de banda", f"{coverage * 100:.0f} %", "objetivo 90 %", border=True,
                  icon=":material/verified:", delta_color="off")
        if unit_metrics is not None:
            st.metric("Vida registrada", f"{int(unit_metrics['life'])}", "ciclos", border=True,
                      icon=":material/schedule:", delta_color="off")
        st.caption(
            f"Métricas sobre la lectura "
            f"{'corregida (R2b + R6)' if aplicar_reglas else 'cruda de la caché'}: "
            "con la capa de reglas activa no se mezclan las dos lecturas."
        )

    read_col, table_col = st.columns([1, 1])
    with read_col:
        with st.container(border=True, height="stretch"):
            st.subheader("Lectura de la decisión", icon=":material/lightbulb:")
            if alarm_cycle is not None:
                lead = (truth_cycle - alarm_cycle) if truth_cycle is not None else None
                st.markdown(
                    f"La alarma de hangar (`L_inf < {threshold_aog:.0f}`) se dispara en el "
                    f"**ciclo {alarm_cycle}**."
                )
                if truth_cycle is not None:
                    st.markdown(
                        f"La RUL real cruza {threshold_aog:.0f} ciclos en el **ciclo "
                        f"{truth_cycle}**: la alarma llega **{lead} ciclos antes**, con una RUL "
                        f"real de {curve.loc[curve['cycle'] == alarm_cycle, 'y_true'].iloc[0]:.1f}."
                    )
            else:
                st.markdown("La unidad no cruza el umbral de hangar en los ciclos evaluados.")
            st.caption(
                "Ese adelanto es el precio de decidir con el límite inferior: la banda es "
                "conservadora (cobertura realizada por encima del 90 % nominal)."
            )
    with table_col:
        with st.container(border=True, height="stretch"):
            st.subheader("Errores por unidad", icon=":material/table_chart:")
            table = per_unit.assign(Motor=[f"U{int(u)}" for u in per_unit["unit"]])
            st.dataframe(
                table[["Motor", "windows", "rmse", "mae", "bias"]],
                hide_index=True,
                column_config={
                    "Motor": st.column_config.TextColumn("Motor"),
                    "windows": st.column_config.NumberColumn("Ventanas", format="%d"),
                    "rmse": st.column_config.NumberColumn("RMSE", format="%.2f"),
                    "mae": st.column_config.NumberColumn("MAE", format="%.2f"),
                    "bias": st.column_config.NumberColumn("Sesgo", format="%+.2f"),
                },
                alt="RMSE, MAE y sesgo por motor, calculados de la caché.",
            )
            st.caption(
                "Los sesgos tienen signo opuesto y se cancelan en el promedio global: U11 "
                "sobreestima, U14 y U15 subestiman."
            )


# ------------------------------------------------------------------- tab 3


with tab_evidencia:
    group = st.selectbox("Grupo de canales", list(L.CHANNEL_GROUPS), index=0)
    channels = st.multiselect(
        "Canales a dibujar",
        L.CHANNEL_GROUPS[group],
        default=L.CHANNEL_GROUPS[group][:2],
        format_func=lambda c: L.CHANNEL_LABELS.get(c, c),
    )

    # "Condiciones de vuelo" already contains alt/Mach: dedupe before selecting,
    # or the groupby receives duplicate column names.
    needed = list(dict.fromkeys(L.CHANNEL_GROUPS[group] + ["alt", "Mach"]))
    per_cycle = (
        telemetry[telemetry["unit"] == unit]
        .groupby("cycle", as_index=False)[needed]
        .mean(numeric_only=True)
    )
    if per_cycle.empty:
        # Una unidad de alta no tiene filas propias en `telemetry`: su serie es la
        # de la unidad de caché de la que se recortó. Se dice en vez de romper.
        st.info(
            f"**{_etiqueta_unidad(float(unit))}** es una unidad de alta: su serie "
            "viene de la caché y no hay telemetría fila a fila que radiografiar "
            "aquí. Su estado y su curva RUL sí están en las pestañas 1 y 2.",
            icon=":material/info:",
        )
    else:
        last_cycle = int(per_cycle["cycle"].max())

        left, right = st.columns(2)
        with left:
            with st.container(border=True, height="stretch"):
                st.subheader("Condiciones operativas", icon=":material/air:")
                ops = [c for c in ("alt", "Mach", "TRA", "T2") if c in per_cycle.columns]
                fig_a = make_subplots(
                    rows=len(ops), cols=1, shared_xaxes=True, vertical_spacing=0.07
                )
                for i, ch in enumerate(ops, start=1):
                    fig_a.add_trace(
                        go.Scatter(
                            x=per_cycle["cycle"], y=per_cycle[ch], mode="lines",
                            name=L.CHANNEL_LABELS.get(ch, ch), line=dict(width=1.8, color=SKY),
                        ),
                        row=i, col=1,
                    )
                    fig_a.update_yaxes(title_text=ch, row=i, col=1)
                fig_a.update_layout(**chart_layout(height=360, showlegend=False,
                                                   hovermode="x unified"))
                style_axes(fig_a, x_title="Ciclo de vuelo")
                st.plotly_chart(
                    fig_a, theme=None,
                    alt="Altitud, Mach, acelerador y T2 a lo largo de los ciclos del motor seleccionado.",
                )
                st.caption(
                    "El régimen de vuelo es lo que el residualizador descarta antes de que el "
                    "modelo lea los sensores."
                )

        with right:
            with st.container(border=True, height="stretch"):
                st.subheader("Deriva física respecto al motor sano", icon=":material/monitor_heart:")
                if not channels:
                    st.caption(
                        ":material/touch_app: Selecciona al menos un canal para dibujar la deriva."
                    )
                else:
                    fig_b = fig_deriva(per_cycle, channels, last_cycle,
                                       critical_start, threshold_aog)
                    st.plotly_chart(
                        fig_b, theme=None,
                        alt="Deriva porcentual de los sensores seleccionados frente a la línea base sana del propio motor.",
                    )
                    st.caption(
                        f"Media por ciclo frente a la línea base sana del propio motor "
                        f"({_etiqueta_unidad(float(unit))}, primeros 5 ciclos). No es la "
                        "residualización del modelo: es la señal física bruta, para "
                        "poder discutirla."
                    )

    st.caption(
        "Nomenclatura tomada del propio HDF5 (`X_s_var`, `W_var`): "
        + ", ".join(
            L.CHANNEL_LABELS[c].split(" · ")[0]
            for c in (
                L.CHANNEL_GROUPS["Temperaturas"]
                + L.CHANNEL_GROUPS["Presiones"]
                + L.CHANNEL_GROUPS["Velocidades de rotor"]
                + L.CHANNEL_GROUPS["Combustible"]
            )
        )
        + ". Nada de etiquetas `s1…s21`, que son de FD001."
    )


# ------------------------------------------------------------------- tab 4

    st.subheader(
        "El motor 14 concentra el error y también la evidencia",
        icon=":material/insights:",
    )

    with st.container(border=True):
        bars = go.Figure()
        bars.add_trace(
            go.Bar(
                x=[f"U{int(u)}" for u in per_unit["unit"]], y=per_unit["rmse"],
                name="RMSE",
                marker_color=[ROSE if int(u) == 14 else SKY for u in per_unit["unit"]],
                text=[f"{v:.2f}" for v in per_unit["rmse"]],
                textposition="outside", textfont=dict(color=INK),
            )
        )
        bars.add_trace(
            go.Bar(
                x=[f"U{int(u)}" for u in per_unit["unit"]], y=per_unit["mae"],
                name="MAE",
                marker_color=[("#fca5a5" if int(u) == 14 else "#7dd3fc") for u in per_unit["unit"]],
                text=[f"{v:.2f}" for v in per_unit["mae"]],
                textposition="outside", textfont=dict(color=INK),
            )
        )
        bars.update_layout(**chart_layout(height=340, barmode="group", hovermode="closest"))
        style_axes(bars, y_title="ciclos")
        st.plotly_chart(
            bars, theme=None,
            alt="RMSE y MAE por unidad; el motor 14 concentra el error con 760 ventanas.",
        )
        st.caption("Calculado de la caché, no de una tabla fija. Rojo = motor 14.")

    u14 = per_unit[per_unit["unit"] == 14].iloc[0]
    u14_prov = provenance["counts"]["units"]["14"]
    fit_density = provenance["counts"]["fit_engine_rows_per_cycle"]

    card_a, card_b, card_c = st.columns(3, border=True)
    with card_a:
        st.markdown("**Complejidad física**")
        st.markdown(
            f"Régimen compuesto: degradación simultánea más agresiva. Medido, no supuesto: "
            f"RMSE **{u14['rmse']:.2f}** y sesgo **{u14['bias']:+.2f}** ciclos sobre "
            f"**{int(u14['windows'])}** ventanas."
        )
        st.caption(
            "El sesgo es negativo: el modelo se queda corto. Es el error caro, porque "
            "sobreestimar vida es lo que la NASA penaliza más."
        )
    with card_b:
        st.markdown("**Densidad de muestreo — medida y descartada**")
        st.markdown(
            f"U14 trae **{u14_prov['rows_per_cycle']:.1f} filas/ciclo** frente a "
            f"**{fit_density:.1f}** de media en los motores de ajuste "
            f"({u14_prov['density_vs_fit']:.2f}×). La hipótesis se probó re-ventaneando dos "
            "motores a esa misma densidad, con todo lo demás fijo."
        )
        st.caption(
            "`docs/informes/informe-2026-10-21-p0-p1-prior-de-vida.md`: el sesgo del meta cambió −0.93 / −0.03 / "
            "+0.34 ciclos. La densidad no explica el error; se reporta como hipótesis refutada."
        )
    with card_c:
        st.markdown("**Prior de vida y mitigación conformal**")
        st.markdown(
            "El sesgo en vida alta es ≈ **−0,87 ciclos por ciclo de vida** del motor: el "
            "conjunto implementa, sin declararlo, `RUL ≈ 63 − ciclo` (63 = vida del motor 16, "
            "el del *early stopping* y el ajuste del meta)."
        )
        st.caption(
            "La mitigación no es otro meta: es decidir con el límite inferior. La alarma llega "
            "antes en U14 precisamente porque su sesgo es el peor."
        )

    band_col, lead_col = st.columns([1, 1])
    with band_col:
        with st.container(border=True, height="stretch"):
            st.subheader("Precisión por tramo de vida", icon=":material/steps:")
            band_df = L.mae_by_band(windows)
            populated = band_df[band_df["windows"] > 0]
            band_fig = go.Figure(
                go.Bar(
                    x=populated["band"], y=populated["mae"],
                    marker_color=[GREEN if b.startswith("[0") else "#475569" for b in populated["band"]],
                    text=[f"{v:.2f}" for v in populated["mae"]],
                    textposition="outside", textfont=dict(color=INK),
                )
            )
            band_fig.update_layout(**chart_layout(height=300, hovermode="closest"))
            style_axes(band_fig, x_title="tramo de RUL real", y_title="MAE (ciclos)")
            st.plotly_chart(
                band_fig, theme=None,
                alt="MAE por tramo de RUL real: mínimo en el tramo crítico 0-25 y máximo en vida alta.",
            )
            st.dataframe(
                populated.assign(Tramo=populated["band"]),
                hide_index=True,
                column_config={
                    "Tramo": st.column_config.TextColumn("Tramo"),
                    "windows": st.column_config.NumberColumn("Ventanas", format="%d"),
                    "mae": st.column_config.NumberColumn("MAE", format="%.3f"),
                    "bias": st.column_config.NumberColumn("Sesgo", format="%+.3f"),
                },
                alt="MAE y sesgo por tramo de RUL real.",
            )
            if len(populated) < len(band_df):
                st.caption(
                    "Ningún motor de test supera los 75 ciclos de RUL real, así que el tramo "
                    "más alto no tiene filas: no se dibuja una barra vacía ni se inventa un valor."
                )

    with lead_col:
        with st.container(border=True, height="stretch"):
            st.subheader("Alarma vs. verdad", icon=":material/av_timer:")
            rows = []
            for u in units:
                a, t = L.first_alarm_cycle(curves[u], threshold_aog)
                rows.append({
                    "Motor": f"U{u}",
                    "Alarma": a,
                    "RUL real < umbral": t,
                    "Adelanto": (t - a) if (a is not None and t is not None) else None,
                    "RUL real al alarmar": (
                        float(curves[u].loc[curves[u]["cycle"] == a, "y_true"].iloc[0])
                        if a is not None else None
                    ),
                })
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                column_config={
                    "Motor": st.column_config.TextColumn("Motor"),
                    "Alarma": st.column_config.NumberColumn("Ciclo de alarma", format="%d"),
                    "RUL real < umbral": st.column_config.NumberColumn(
                        "Ciclo con RUL real < umbral", format="%d"
                    ),
                    "Adelanto": st.column_config.NumberColumn(
                        "Adelanto (ciclos)", format="%d"
                    ),
                    "RUL real al alarmar": st.column_config.NumberColumn(
                        "RUL real al alarmar", format="%.1f"
                    ),
                },
                alt="Ciclo de alarma frente al ciclo en que la RUL real cruza el umbral, por unidad.",
            )
            st.caption(
                "El adelanto es el coste en disponibilidad de una cota conservadora: la flota "
                f"se inmoviliza antes de que la RUL real llegue a {threshold_aog:.0f}. Es "
                "ajustable desde la barra lateral."
            )

    with st.container(border=True):
        st.subheader("Procedencia verificable", icon=":material/fingerprint:")
        st.caption(
            "Huella SHA-256 del ensemble congelado, copiada del manifiesto que acompaña a "
            "la caché. La UI no recalcula el artefacto: lo identifica."
        )
        st.code(provenance["artifact"]["ensemble_sha256"], language=None)
        st.markdown(
            f"**ensemble** `{provenance['artifact'].get('ensemble', 'models/ensemble.joblib')}` · "
            f"**manifest** `{provenance['artifact'].get('manifest', 'models/ds02_manifest.json')}`"
        )
        st.caption(
            "Para verificarlo en local: `python -c \"import hashlib;print(hashlib.sha256"
            "(open('models/ensemble.joblib','rb').read()).hexdigest())\"`."
        )

    with st.container(border=True):
        st.subheader("Contrato congelado vs. cálculo en vivo", icon=":material/difference:")
        recorded = manifest.get("macro_rmse", {}).get("per_unit_rmse", {})
        compare = pd.DataFrame(
            {
                "Motor": [f"U{int(u)}" for u in per_unit["unit"]],
                "En vivo (caché)": per_unit["rmse"].to_numpy(),
                "Registrado (manifest)": [
                    float(recorded.get(str(float(u)), np.nan)) for u in per_unit["unit"]
                ],
            }
        )
        compare["Δ"] = compare["En vivo (caché)"] - compare["Registrado (manifest)"]
        st.dataframe(
            compare,
            hide_index=True,
            column_config={
                "Motor": st.column_config.TextColumn("Motor"),
                "En vivo (caché)": st.column_config.NumberColumn(
                    "RMSE en vivo (caché)", format="%.4f"
                ),
                "Registrado (manifest)": st.column_config.NumberColumn(
                    "RMSE registrado (manifest)", format="%.4f"
                ),
                "Δ": st.column_config.NumberColumn("Δ", format="%+.4f"),
            },
            alt="Comparación entre el RMSE recalculado de la caché y el registrado en el manifiesto.",
        )
        st.caption(
            "Ambas columnas describen las mismas ventanas. Una diferencia distinta de cero "
            "sería deriva de regeneración del artefacto, y se publica tal cual: no se ajusta "
            "ninguna de las dos. El score NASA es una **suma** asimétrica sobre las mismas "
            "6 196 ventanas y no aplica el recorte de 125 ciclos del camino FD001."
        )



# ------------------------------------------------------------------- tab 5

    _flash_live = st.session_state.pop("live_flash", None)
    if _flash_live:
        st.toast(_flash_live, icon=":material/check_circle:")
    _flash_twin_live = st.session_state.get("twin_flash")
    if _flash_twin_live:
        st.toast(_flash_twin_live, icon=":material/check_circle:")

    # -------------------- sala 4: incorporar (individual en el sidebar, lote aquí)
    with st.container(border=True):
        st.subheader("Incorporar en lote · trae uno o doce", icon=":material/library_add:")
        st.caption(
            "Puntúa N motores de una vez y devuelve una fila por motor: predicción, "
            "banda y estado. No reentrena, no toca la caché y no inventa ground truth: "
            "los datos los aportas tú, así que no hay RMSE ni MAE que reportar."
        )
        _lote_mode = st.segmented_control(
            "Fuente del lote",
            ["Subir CSV (uno por motor)", "Pegar CSV por bloques"],
            default="Subir CSV (uno por motor)",
            key="lote_mode",
            help="Cada CSV es un motor. En la segunda opción, una columna `unit_id` "
                 "separa los motores dentro del mismo CSV.",
        )
        _bloques: list[dict] = []
        if _lote_mode == "Subir CSV (uno por motor)":
            _archivos = st.file_uploader(
                f"CSV de motores (máximo {B.MAX_MOTORES_LOTE})",
                type=["csv"], accept_multiple_files=True, key="lote_archivos",
            )
            if _archivos:
                try:
                    _bloques = B.bloques_de_archivos(_archivos)
                except Exception as exc:  # noqa: BLE001 - el mensaje se muestra
                    st.error(f"No se pudieron leer los CSV: {exc}",
                             icon=":material/error:")
        else:
            _texto_lote = st.text_area(
                "CSV con columna `unit_id`", height=160, key="lote_texto",
                placeholder="unit_id,cycle,alt,Mach,TRA,T2,T24,…",
                help="Una columna `unit_id` por motor y los 18 canales del dataset.",
            )
            if _texto_lote.strip():
                try:
                    _bloques = B.bloques_de_csv(_texto_lote)
                except Exception as exc:  # noqa: BLE001
                    st.error(f"No se pudo leer el CSV por bloques: {exc}",
                             icon=":material/error:")

        if B.excede_limite(len(_bloques)):
            st.error(
                f"Traes {len(_bloques)} motores y el tope es {B.MAX_MOTORES_LOTE}. "
                "Quita algunos: por encima del tope el lote deja de ser interactivo "
                "en un portátil.",
                icon=":material/rule:",
            )
            _bloques = []
        elif _bloques:
            _aviso_lote = B.validar_lote(_bloques)
            if not _aviso_lote["ok"]:
                for _mat, _error in _aviso_lote["errores"].items():
                    st.error(f"`{_mat}`: {_error}", icon=":material/rule:")
            else:
                with st.form("lote_evaluar"):
                    _enviar_lote = st.form_submit_button(
                        f"Puntuar {_aviso_lote['bloques']} motor(es)",
                        type="primary", icon=":material/play_arrow:",
                    )
                if _enviar_lote:
                    _barra = st.progress(0.0, text="Puntuando 0 de …")

                    def _progreso(i, n, mat):
                        _barra.progress(i / n, text=f"Puntuando {i} de {n} · {mat}")

                    try:
                        _resultado_lote = B.puntuar_lote(
                            _bloques, umbrales, INF.get_ensemble(), _progreso)
                    except ValueError as exc:
                        st.session_state["lote_resultado"] = None
                        st.error(str(exc), title="No se pudo puntuar el lote",
                                 icon=":material/rule:")
                    else:
                        st.session_state["lote_resultado"] = _resultado_lote
                        st.session_state["lote_bloques"] = _bloques
                        _log(f"Lote puntuado: {len(_bloques)} motor(es).")
                        st.rerun()

    _lote = st.session_state.get("lote_resultado")
    if _lote is not None:
        _resumen = B.resumen_lote(_lote)
        with st.container(horizontal=True):
            st.metric("Motores puntuados", f"{_resumen['total']}", border=True,
                      delta_color="off", icon=":material/groups:")
            st.metric("En hangar", f"{_resumen['por_estado'][L.AOG]}", border=True,
                      delta_color="off", icon=":material/local_shipping:")
            st.metric("En inspección", f"{_resumen['por_estado'][L.PREVENTIVE]}",
                      border=True, delta_color="off", icon=":material/schedule:")
            st.metric("Aptos", f"{_resumen['por_estado'][L.AIRWORTHY]}", border=True,
                      delta_color="off", icon=":material/check_circle:")
        _ver = _lote.rename(columns={
            "matricula": "Matrícula", "ciclo": "Ciclo", "pred": "RUL p35",
            "lower": "L_inf (decide)", "upper": "L_sup", "estado": "Estado",
            "regla": "Regla",
        })
        st.dataframe(
            _ver, hide_index=True,
            column_config={
                "Ciclo": st.column_config.NumberColumn("Ciclo", format="%d"),
                "RUL p35": st.column_config.NumberColumn(
                    "RUL p35", format="%.1f"),
                "L_inf (decide)": st.column_config.NumberColumn(
                    "L_inf (decide)", format="%.1f",
                    help="Límite inferior de la banda: es lo que decide el estado."),
                "L_sup": st.column_config.NumberColumn("L_sup", format="%.1f"),
            },
            alt="Triage del lote: una fila por motor con su predicción, su banda y "
                "su estado.",
        )
        st.caption(
            "Predicción del artefacto congelado (`models/ds02_manifest.json`) sobre los "
            "datos aportados. **Sin ground truth**: no hay error que reportar."
        )
        with st.container(horizontal=True):
            st.download_button(
                "Descargar triage (CSV)",
                data=_ver.to_csv(index=False),
                file_name="triage_lote_ds02.csv",
                mime="text/csv",
                icon=":material/download:",
            )
            if st.button(
                "Registrar gemelos", icon=":material/library_add:",
                key="lote_registrar",
                help="Guarda los motores del lote en la flota registrada.",
            ):
                _barra_g = st.progress(0.0, text="Registrando 0 de …")

                def _progreso_g(i, n, mat):
                    _barra_g.progress(i / n, text=f"Registrando {i} de {n} · {mat}")

                try:
                    _gemelos_nuevos = B.registrar_gemelos(
                        st.session_state.get("lote_bloques") or [],
                        INF.get_ensemble(), umbrales,
                        st.session_state.get("twins", {}), _progreso_g)
                except ValueError as exc:
                    st.error(str(exc), title="No se pudieron registrar",
                             icon=":material/rule:")
                else:
                    st.session_state["twins"] = _gemelos_nuevos
                    _guardar_registros()
                    st.session_state["lote_resultado"] = None
                    _log(f"{len(_gemelos_nuevos)} gemelo(s) registrados desde el lote.")
                    st.session_state["twin_flash"] = (
                        f"{len(_gemelos_nuevos)} gemelo(s) en la flota registrada. "
                        "Míralos en la primera pestaña, en «Gemelos registrados»."
                    )
                    st.rerun()

    # El caso crítico apunta al mismo ciclo que el paso 3 del modo historia: ambos
    # salen de la caché (`estado_historia` elige el primer ciclo en HANGAR del motor
    # de mayor RMSE), así que si la caché cambia, los dos cambian con ella. Ningún
    # ciclo ni ningún límite está esparcido aquí.
    _paso_hangar = A.estado_historia(windows, umbrales)[2]
    _u_hangar = int(_paso_hangar["unidad"])
    _c_hangar = int(_paso_hangar["ciclo"])
    # Los tramos viven en `ui_inference.demo_presets`: son datos y hay un test que
    # los fija. Cada nombre promete un estado y el tramo tiene que darlo a
    # cualquier largo (`DEMO_ROWS`). Antes eran 50 filas (una ventana): el EMA
    # arrancaba en frio y la grafica tenia un punto.
    DEMO_PRESETS = INF.demo_presets(_u_hangar, _c_hangar)

    with st.container(border=True):
        st.subheader("Puntúa un ejemplo en 1 clic", icon=":material/rocket_launch:")
        st.caption(
            "El onboarding del tablero está en la primera pestaña. Esto puntúa un tramo "
            "real de la caché y deja el resultado listo para registrar: no pega nada ni "
            "sube CSV."
        )
        c1, c2, c3 = st.columns(3)
        for _col, _nombre in zip((c1, c2, c3), list(DEMO_PRESETS)[:3]):
            with _col:
                if st.button(_nombre, key=f"live_demo_{_nombre}", type="primary" if "Crítico" in _nombre else "secondary", icon=":material/play_arrow:"):
                    _u, _p, _ciclo, _did = DEMO_PRESETS[_nombre]
                    try:
                        if _ciclo is None:
                            _tab, _meta = INF.example_window(
                                _u, _p, rows=INF.DEMO_ROWS)
                        else:
                            _tab, _meta = INF.window_ending_at(
                                _u, _ciclo, rows=INF.DEMO_ROWS)
                        _pf = INF.preflight(_tab)
                        if not _pf["ok"]:
                            raise ValueError(_pf["error"])
                        st.session_state["live_engine_id"] = _did
                        st.session_state["_editor_value"] = _tab
                        st.session_state["live_result"] = INF.score_table(_tab, engine_id=_did)
                        st.session_state["live_meta"] = _meta
                        st.session_state["live_warnings"] = _pf["avisos"]
                        st.session_state["live_error"] = None
                        st.session_state["live_flash"] = f"{_nombre} puntuado abajo (ciclos {_meta['start_cycle']}→{_meta['end_cycle']}). Puedes cambiar a Editar tabla para modificar valores y reevaluar, o pulsar Registrar gemelo."
                    except ValueError as exc:
                        st.session_state["live_result"] = None
                        st.session_state["live_error"] = str(exc)
                    st.rerun()
        # Nota de honestidad: el límite inferior no es monótono y el tribunal lo va a
        # ver. Los tres números salen de la caché, no están escritos a mano.
        _fila_hangar = windows[(windows["unit"] == _u_hangar) & (windows["cycle"] == _c_hangar)]
        _lo_min = float(_fila_hangar["lower"].min())
        _lo_max = float(_fila_hangar["lower"].max())
        _y_real = float(_fila_hangar["y_true"].mean())
        _curva_h = L.unit_curve(windows, _u_hangar).sort_values("cycle")
        _caida = _curva_h[_curva_h["lower_min"] < umbrales["apto"]]
        _ciclo_caida = int(_caida["cycle"].min()) if not _caida.empty else None
        _repunte = (
            _curva_h[(_curva_h["cycle"] > _ciclo_caida)
                     & (_curva_h["lower_min"] >= umbrales["apto"])]
            if _ciclo_caida is not None else _curva_h.iloc[0:0]
        )
        _ciclo_repunte = int(_repunte["cycle"].min()) if not _repunte.empty else None
        _nota_mono = (
            f" La trayectoria no es monótona — cae a inspección en el ciclo "
            f"{_ciclo_caida} y vuelve a apto en el {_ciclo_repunte} — porque el EMA "
            "causal (ADR-006) reduce pero no elimina los saltos de un predictor por "
            "ventanas. Se muestra tal cual."
            if _ciclo_caida is not None and _ciclo_repunte is not None else ""
        )
        st.caption(
            f"El caso crítico termina en el ciclo {_c_hangar}, donde el límite inferior "
            f"cruza el umbral de hangar ({umbrales['hangar']:.0f}) con {_y_real:.0f} ciclos "
            f"reales restantes: dentro del propio ciclo baja de {_lo_max:.1f} a {_lo_min:.1f}."
            + _nota_mono
        )
    st.subheader("Puntúa un motor con datos que aportes tú", icon=":material/science:")
    st.caption(
        "Las tres rutas desembocan en el mismo validador y en la misma llamada al "
        "artefacto congelado. Una ventana son **50 muestras remuestreadas** (1 de cada "
        "100 registros), lo que son **~0,4 ciclos de vuelo**, no 50 lecturas seguidas "
        "ni 50 ciclos. Teclear 900 celdas no es "
        "viable: usa el ejemplo, pega un bloque desde Excel o sube el CSV."
    )

    mode = st.segmented_control(
        "Entrada de datos",
        ["Ejemplo del test set", "Editar tabla (pegar)", "Subir CSV"],
        default="Ejemplo del test set",
        key="live_mode",
        help="El ejemplo usa una ventana real de la caché; las otras dos aceptan tus datos.",
    )

    st.session_state.setdefault("live_engine_id", "ESN-DEMO-01")
    identidad = st.text_input(
        "Id del motor",
        key="live_engine_id",
        help="Se escribe en la orden y en el gemelo. Mínimo 3 caracteres.",
    )
    id_ok = len(str(identidad or "").strip()) >= T.MIN_ID
    if not id_ok:
        st.error(
            f"El id necesita al menos {T.MIN_ID} caracteres: se valida ahora, "
            "no al registrar.",
            icon=":material/rule:",
        )
    st.caption(
        "Paso 1 · trae los datos · Paso 2 · revisa el pre-vuelo de abajo · "
        "Paso 3 · evalúa y registra el gemelo. El botón solo se activa cuando "
        "los pasos 1 y 2 están en verde."
    )
    # La plantilla se descarga desde el expander «Qué es cada columna», que ya
    # reutiliza `INF.template_csv()` (cabecera + 50 filas vacías) y ya esta
    # probado. Un segundo boton con la cabecera escrita a mano era un segundo
    # sitio donde arreglar el mismo contrato.

    def _on_preset_change():
        _nuevo = st.session_state.get("live_demo_preset")
        if _nuevo in DEMO_PRESETS:
            st.session_state["live_engine_id"] = DEMO_PRESETS[_nuevo][3]
    if mode == "Ejemplo del test set":
        demo_nombre = st.selectbox(
            "Dataset demo", list(DEMO_PRESETS), key="live_demo_preset",
            on_change=_on_preset_change,
            help=f"Tramos reales de caché con ciclos dispares. Al cambiar se proponen sus {INF.DEMO_ROWS} muestras remuestreadas y su matrícula.",
        )
    example_table, example_meta = INF.example_window(14, 0.55)
    if mode == "Ejemplo del test set" and "demo_nombre" in locals():
        _du2, _dp2, _ciclo2, _ = DEMO_PRESETS[demo_nombre]
        if _ciclo2 is None:
            example_table, example_meta = INF.example_window(
                _du2, _dp2, rows=INF.DEMO_ROWS)
        else:
            example_table, example_meta = INF.window_ending_at(
                _du2, _ciclo2, rows=INF.DEMO_ROWS)
    submitted = False
    table_to_score = None
    data_meta = example_meta
    labels = INF.channel_labels()
    number_columns = {
        "cycle": st.column_config.NumberColumn(
            "cycle", format="%d",
            help="Ciclo de vuelo del registro. Se repite en varias filas porque la "
                 "ventana es una rejilla remuestreada, no una lectura por ciclo.",
        )
    }
    number_columns.update({
        c: st.column_config.NumberColumn(c, format="%.3f", help=labels.get(c, c))
        for c in example_table.columns if c != "cycle"
    })

    with st.expander("Qué es cada columna y qué rango es normal",
                     icon=":material/menu_book:"):
        st.caption(
            "Nombres del dataset N-CMAPSS: `T24` es la salida del compresor de baja "
            "presión, `Ps30` la presión estática a la salida del de alta. El rango "
            "está medido sobre `app/cache/ds02_rows.parquet`, no copiado de la "
            "documentación; `aviso` es ese rango con un 5 % de margen, el punto en "
            "que la app te avisa de que estás fuera del dominio de entrenamiento."
        )
        st.dataframe(
            INF.observed_envelope(),
            hide_index=True,
            height=420,
            column_config={
                "canal": st.column_config.TextColumn("canal", width="small"),
                "qué mide": st.column_config.TextColumn("qué mide", width="large"),
                "mínimo": st.column_config.NumberColumn("mínimo DS02", format="%.4g"),
                "máximo": st.column_config.NumberColumn("máximo DS02", format="%.4g"),
                "aviso_desde": st.column_config.NumberColumn("aviso desde", format="%.4g"),
                "aviso_hasta": st.column_config.NumberColumn("aviso hasta", format="%.4g"),
            },
            alt="Glosario de los 18 canales con su significado físico y el rango "
                "observado en DS02.",
        )
        st.caption(
            "**`cycle`** es el ciclo de vuelo del registro y **no** se repite por "
            "accidente: la ventana toma 1 de cada 100 registros, así que varias "
            "muestras comparten ciclo y 50 muestras cubren ~0,4 vuelos."
        )
        st.download_button(
            "Descargar plantilla CSV (50 muestras remuestreadas vacías)",
            data=INF.template_csv(),
            file_name="plantilla_unidad_ds02.csv",
            mime="text/csv",
            icon=":material/file_download:",
        )

    if mode == "Ejemplo del test set":
        with st.container(border=True):
            st.caption(
                f"Ventana real de U{example_meta['unit']} · ciclos "
                f"{example_meta['start_cycle']}→{example_meta['end_cycle']} · filas "
                f"{example_meta['row_slice'][0]}–{example_meta['row_slice'][1]} de "
                f"`{example_meta['source']}`. Desmarca filas para excluirlas (mínimo 50 para puntuar)."
            )
            _edit = example_table.copy()
            _edit.insert(0, "usar", True)
            _cols_cfg = dict(number_columns)
            _cols_cfg["usar"] = st.column_config.CheckboxColumn("usar", help="Desmarca para no predecir esa fila.")
            _edited = st.data_editor(
                _edit, hide_index=True, height=260, key="live_demo_grid",
                column_config=_cols_cfg,
                alt="Ventana demo seleccionable: marca qué filas se puntúan.",
            )
            _sel = pd.DataFrame(_edited)
            _usar = _sel["usar"].fillna(False).to_numpy(dtype=bool) if "usar" in _sel.columns else [True] * len(_sel)
            _filtrada = _sel.loc[_usar].drop(columns=[c for c in ["usar"] if c in _sel.columns], errors="ignore")
            st.caption(f"{int(_usar.sum())} de {len(_sel)} muestras seleccionadas → {max(0, int(_usar.sum()) - INF.window_size() + 1)} ventana(s).")
        preflight_ejemplo = INF.preflight(_filtrada)
        _preflight_panel(preflight_ejemplo)
        with st.form("live_eval_example"):
            submitted = st.form_submit_button(
                "Evaluar unidad", type="primary", icon=":material/play_arrow:",
                disabled=not id_ok,
            )
        if submitted:
            table_to_score = _filtrada
            data_meta = example_meta
    elif mode == "Editar tabla (pegar)":
        # `live_editor` es un `st.data_editor`: Streamlit declara su clave de
        # solo lectura y no se puede escribir desde un handler. La tabla se
        # guarda en `_editor_value` y se pasa como `data`; se mantiene entre
        # pasadas para que la rejilla no revierta al tocar una celda.
        _tabla_editor = st.session_state.get("_editor_value")
        if _tabla_editor is None:
            _tabla_editor = example_table
        edited = st.data_editor(
            _tabla_editor,
            num_rows="dynamic",
            hide_index=True,
            height=420,
            key="live_editor",
            column_config=number_columns,
        )
        draft = pd.DataFrame(edited) if edited is not None else example_table
        if "usar" in draft.columns:
            draft = draft[draft["usar"].fillna(False).astype(bool)].drop(columns=["usar"])
        state_rows = len(draft)
        state_windows = max(0, state_rows - INF.window_size() + 1)
        if state_rows > INF.UMBRAL_RECORTE_EDITOR:
            st.warning(
                f"La rejilla va lenta con {state_rows:,} filas. Puedes recortar a las "
                f"primeras {INF.UMBRAL_RECORTE_EDITOR:,} para editar con fluidez: "
                "se puntuará lo visible y el recorte queda a la vista.",
                icon=":material/speed:",
            )
            if st.button(
                f"Recortar a {INF.UMBRAL_RECORTE_EDITOR:,} primeras filas",
                icon=":material/content_cut:", key="recortar_editor",
            ):
                cortada, _ = INF.limitar_filas(draft)
                # Igual que arriba: la clave del `data_editor` es de solo lectura.
                # Se guarda la tabla recortada y la rejilla la dibuja en la
                # siguiente pasada.
                st.session_state["_editor_value"] = cortada
                st.session_state.pop("live_edit_fixed", None)
                st.rerun()
        st.caption(
            f"**{state_rows} muestras** → {state_windows} ventana(s). Pega el bloque "
            "desde Excel/Sheets sobre la primera celda: la rejilla acepta una "
            "matriz de 50×19, y con más muestras puntúa todas las ventanas "
            "deslizantes. No cambies los encabezados."
        )
        _fija = st.session_state.get("live_edit_fixed")
        if (_fija is not None and list(_fija.get("cols", [])) == list(draft.columns)
                and _fija.get("len") == len(draft)):
            draft = _fija["table"]
        pf_edit = INF.preflight(draft)
        if (not pf_edit["ok"] and "Orden de canales" in (pf_edit["error"] or "")
                and set(draft.columns) == set(INF.required_columns())):
            if st.button("Reordenar al orden del dataset",
                         icon=":material/sort:", key="reorder_edit"):
                st.session_state["live_edit_fixed"] = {
                    "cols": list(draft.columns), "len": len(draft),
                    "table": INF.reordenar_columnas(draft),
                }
                st.rerun()
        _preflight_panel(pf_edit)
        submitted = st.button(
            "Evaluar unidad", type="primary", icon=":material/play_arrow:",
            disabled=not (id_ok and pf_edit["ok"]), key="eval_editor",
        )
        if submitted:
            table_to_score = draft
            data_meta = {"source": "edición manual en la UI"}

    else:
        upload = st.file_uploader(
            "CSV con `cycle` y los 18 canales",
            type=["csv"],
            help="Encabezados en el orden del dataset: alt, Mach, TRA, T2, T24 … Wf.",
        )
        uploaded_table = None
        if upload is None:
            st.info(
                "Sube un CSV, o usa el ejemplo para ver el flujo completo sin datos "
                "propios. Si no tienes el formato, descarga la plantilla en «Qué es "
                "cada columna» y rellénala en Excel.",
                icon=":material/upload_file:",
            )
        else:
            try:
                uploaded_table = pd.read_csv(upload)
            except Exception as exc:  # noqa: BLE001 - the message is shown to the user
                st.error(f"No se pudo leer el CSV: {exc}", icon=":material/error:")
            if uploaded_table is not None:
                st.caption(
                    f"{len(uploaded_table)} filas y {len(uploaded_table.columns)} columnas."
                )
                _fija_csv = st.session_state.get("live_csv_fixed")
                if (_fija_csv is not None
                        and _fija_csv.get("name") == getattr(upload, "name", None)):
                    uploaded_table = _fija_csv["table"]
                preflight_csv = INF.preflight(uploaded_table)
                if (not preflight_csv["ok"]
                        and "Orden de canales" in (preflight_csv["error"] or "")
                        and set(uploaded_table.columns) == set(INF.required_columns())):
                    if st.button("Reordenar al orden del dataset",
                                 icon=":material/sort:", key="reorder_csv"):
                        st.session_state["live_csv_fixed"] = {
                            "name": getattr(upload, "name", None),
                            "table": INF.reordenar_columnas(uploaded_table),
                        }
                        st.rerun()
                    preflight_csv = INF.preflight(
                        st.session_state["live_csv_fixed"]["table"])
                    _preflight_panel(preflight_csv)
                    uploaded_table = st.session_state["live_csv_fixed"]["table"]
                else:
                    _preflight_panel(preflight_csv)
                submitted = st.button(
                    "Evaluar unidad", type="primary", icon=":material/play_arrow:",
                    disabled=not (id_ok and preflight_csv["ok"]), key="eval_csv",
                )
                if submitted:
                    table_to_score = uploaded_table
                    data_meta = {"source": upload.name}

    if submitted and table_to_score is not None:
        try:
            preflight = INF.preflight(table_to_score)
            if not preflight["ok"]:
                raise ValueError(preflight["error"])
            st.session_state["live_result"] = INF.score_table(
                table_to_score, engine_id=identidad)
            st.session_state["live_meta"] = data_meta
            st.session_state["live_warnings"] = preflight["avisos"]
            st.session_state["live_error"] = None
        except ValueError as exc:
            st.session_state["live_result"] = None
            st.session_state["live_warnings"] = []
            st.session_state["live_error"] = str(exc)
    live_error = st.session_state.get("live_error")
    if live_error:
        st.error(live_error, title="No se pudo evaluar", icon=":material/rule:")
    for note in st.session_state.get("live_warnings") or []:
        st.warning(note, icon=":material/find_in_page:")

    live = st.session_state.get("live_result")
    if live:
        last = live["windows"].iloc[-1]
        # La pasada A se toma de `decision_en_vivo`, que decide con la invalidez
        # real de la banda y no con las cautelas de plausibilidad: esas se pintan
        # arriba como aviso al operador (2782), pero no son un dato imposible.
        _decision = UR.decision_en_vivo(live, umbrales)
        alertas_live = _decision["alertas"]
        traza_live = _decision["traza"]
        live_state = (traza_live["decision"] if traza_live["decision"] in L.STATE_LABELS
                      else L.NO_DATA)
        tone = {
            L.AIRWORTHY: "green",
            L.PREVENTIVE: "orange",
            L.AOG: "red",
            L.SIN_DECISION: "gray",
        }.get(live_state, "gray")
        with st.container(horizontal=True):
            st.metric("RUL p35 (conservadora)", f"{last['pred']:.1f}", "cuantil 0.35", border=True,
                      icon=":material/speed:", delta_color="off")
            st.metric("Límite inferior", f"{last['lower']:.1f}", "decide el estado",
                      border=True, icon=":material/trending_down:", delta_color="off")
            st.metric("Límite superior", f"{last['upper']:.1f}", "banda 90 %",
                      border=True, icon=":material/trending_up:", delta_color="off")
            st.metric("Ventanas puntuadas", f"{live['contract']['ventanas']}",
                      f"{live['contract']['filas']} filas", border=True,
                      icon=":material/layers:", delta_color="off")
        reglas_live = " → ".join(traza_live["usadas"])
        st.markdown(
            f"Con los umbrales en vigor ({threshold_apto:.0f} / {threshold_aog:.0f}): "
            f":{tone}-badge[{L.STATE_LABELS[live_state]}]"
            + (f" · reglas: `{reglas_live}`" if reglas_live else "")
        )
        if traza_live["porque"]:
            st.caption(" · ".join(traza_live["porque"]))

        if len(live["windows"]) > 1:
            w = live["windows"]
            fig_live = go.Figure()
            fig_live.add_trace(
                go.Scatter(x=w["cycle"], y=w["upper"], mode="lines", line=dict(width=0),
                           hoverinfo="skip", name="Límite superior")
            )
            fig_live.add_trace(
                go.Scatter(x=w["cycle"], y=w["lower"], mode="lines", line=dict(width=0),
                           fill="tonexty", fillcolor="rgba(56, 189, 248, 0.18)",
                           name="Banda conformal")
            )
            fig_live.add_trace(
                go.Scatter(x=w["cycle"], y=w["pred"], mode="lines",
                           line=dict(color=SKY, width=3), name="RUL estimada")
            )
            fig_live.add_hrect(
                y0=0, y1=threshold_aog, fillcolor=ROSE, opacity=0.10, line_width=0,
                annotation_text=f"hangar ({threshold_aog:.0f})",
                annotation_position="top left", annotation_font_size=11,
                annotation_font_color="#fca5a5",
            )
            fig_live.update_layout(**chart_layout(height=340, hovermode="x unified"))
            style_axes(fig_live, x_title="Ciclo de vuelo", y_title="RUL (ciclos)")
            st.plotly_chart(
                fig_live, theme=None,
                alt="Estimación de RUL y banda conformal para la unidad aportada por el usuario.",
            )

        with st.expander(
            "Contrato y procedencia de esta evaluación", icon=":material/receipt_long:"
        ):
            contract = live["contract"]
            st.markdown(
                f"**artefacto** `{contract['artefacto']}` · "
                f"**SHA-256** `{contract['artefacto_sha256']}`"
            )
            st.markdown(
                f"**ventana** `{contract['window']}` filas remuestreadas · "
                f"**step** `{contract['step']}` · **unidad simulada** "
                f"`{contract['unidad_simulada']:.0f}` (negativa: nunca se mezcla con "
                "las unidades en caché)"
            )
            st.markdown(
                "**canales** `" + ", ".join(contract["canales"]) + "`"
            )
            st.caption(
                "Las 50 muestras son la rejilla remuestreada (1 de cada 100 registros del "
                "dataset), lo que son ~0,4 ciclos de vuelo, no 50 lecturas de 1 Hz. Con otro "
                "muestreo la predicción queda "
                "fuera de contrato aunque los números sean válidos."
            )

        st.caption(
            "**Sin ground truth**: esta unidad no trae RUL real, así que no se declara "
            "RMSE ni MAE. La banda es una cota conservadora calibrada sobre los motores "
            "de desarrollo; el sesgo de vida alta (`RUL ≈ 63 − ciclo`) también aplica aquí."
        )

        with st.expander("Añadir este motor a la flota", icon=":material/library_add:"):
            st.caption(
                "Guarda la serie puntuada como gemelo. Su estado se recalcula con los "
                "umbrales en vigor; la serie no se vuelve a puntuar."
            )
            gemelos_previos = st.session_state.get("twins", {})
            motor_live = str(live["contract"].get("motor") or "").strip().upper()
            ya_existe = motor_live in gemelos_previos
            reemplazar = False
            if ya_existe:
                previo = gemelos_previos[motor_live]
                verdad_previa = T.metricas_verdad(previo)
                st.info(
                    f"Ya hay un gemelo `{motor_live}` con {len(previo['serie'])} "
                    "ventana(s) guardada(s)"
                    + (f" y RUL real reportada ({verdad_previa['rul_real']:.0f} ciclos)"
                       if verdad_previa else "")
                    + ". Puntuar otra ventana del mismo motor no lo sobrescribe solo: "
                    "marca la casilla para sustituir la serie.",
                    icon=":material/info:",
                )
                reemplazar = st.checkbox(
                    "Reemplazar la serie guardada (la RUL real se conserva)",
                    key="twin_replace",
                    help="Se sustituyen la serie, la huella y el contrato. La RUL real "
                         "es un hecho del motor, no de la ventana: no se borra.",
                )
            if st.button(
                f"Reemplazar gemelo `{motor_live}`" if ya_existe else "Registrar gemelo",
                icon=":material/sync:" if ya_existe else ":material/add_circle:",
                key="twin_add",
            ):
                try:
                    gemelo = T.make_twin(
                        live["contract"].get("motor") or "",
                        live,
                        source=str((st.session_state.get("live_meta") or {}).get(
                            "source", "entrada manual")),
                        banda=INF.BANDA_ARTEFACTO,
                        correccion=INF.CORRECCION_NINGUNA,
                        umbrales=umbrales,
                        fingerprint_value=live["contract"].get("fingerprint", ""),
                    )
                    st.session_state["twins"] = T.registrar(
                        st.session_state.get("twins", {}), gemelo,
                        reemplazar=reemplazar)
                    _guardar_registros()
                    _log(f"Gemelo {gemelo['id']} registrado.")
                except ValueError as exc:
                    st.error(str(exc), title="No se pudo registrar", icon=":material/rule:")
                else:
                    st.session_state["twin_flash"] = (
                        f"Gemelo `{gemelo['id']}` actualizado en la flota."
                        if reemplazar else
                        f"Gemelo `{gemelo['id']}` registrado en la flota.")
                    st.rerun()

        if live_state == L.AOG:
            order_live = INF.live_work_order(
                live, st.session_state.get("live_meta"), threshold_apto, threshold_aog,
                alertas=alertas_live,
            )
            st.download_button(
                "Descargar orden de esta unidad (JSON)",
                data=json.dumps(order_live, ensure_ascii=False, indent=2),
                file_name="orden_mantenimiento_unidad_externa.json",
                mime="application/json",
                icon=":material/download:",
                type="primary",
            )

    # -------------------- sala 5: sandbox de estrés en vivo
    with st.container(border=True):
        st.subheader("Sandbox de estrés · perturba el motor y mira el pipeline reaccionar",
                     icon=":material/tune:")
        st.caption(
            "El tribunal mueve el deslizador y la app re-puntúa el tramo con el "
            "artefacto congelado y re-decide con el motor oficial. No se reentrena "
            "nada: lo que cambia es la entrada."
        )
        _sandbox_estres()

    # -------------------- perfil de vuelo: alt vs Mach (canales reales)
    with st.container(border=True):
        st.subheader("Perfil de vuelo · altitud y régimen de vuelo",
                     icon=":material/flight:")
        st.caption(
            "Los dos son canales reales del dataset. No hay mapa: el dataset "
            "N-CMAPSS no trae coordenadas GPS (no hay latitud, longitud ni "
            "posición entre sus 18 canales), así que dibujar rutas exigiría "
            "inventarlas."
        )
        _perfil = telemetry[telemetry["unit"] == int(unit)].copy()
        if not _perfil.empty:
            _fig_vuelo = go.Figure(
                go.Scatter(
                    x=_perfil["Mach"], y=_perfil["alt"], mode="lines",
                    line=dict(color=SKY, width=2), name="Perfil de vuelo",
                    hovertemplate="Mach %{x:.3f}<br>altitud %{y:.0f} ft<extra></extra>",
                )
            )
            _fig_vuelo.update_layout(**chart_layout(
                height=260, showlegend=False, hovermode="closest",
                xaxis_title="Mach", yaxis_title="altitud (ft)",
            ))
            style_axes(_fig_vuelo)
            st.plotly_chart(
                _fig_vuelo, theme=None,
                alt=f"Perfil de vuelo de {_etiqueta_unidad(float(unit))}: altitud "
                    f"frente a número de Mach, los dos canales reales del dataset.",
            )

    # -------------------- calidad del modelo: era de la pantalla de decision
    with st.container(border=True):
        st.subheader("Calidad del modelo", icon=":material/insights:")
        st.caption(
            "Métricas de calidad, no de decisión: cuánto se equivoca el modelo, no "
            "lo que decide. Viven aquí porque son para el tribunal, no para el "
            "operador de taller."
        )
        with st.container(horizontal=True):
            st.metric(
                "Macro-RMSE", f"{global_metrics['macro_rmse']:.2f} ciclos",
                f"ponderado {global_metrics['rmse']:.2f}", border=True,
                delta_color="off", icon=":material/balance:",
                help="El macro-RMSE da el mismo peso a cada motor; el ponderado lo da a cada ventana.")
            st.metric(
                "MAE en zona crítica", f"{critical_mae:.2f} ciclos",
                f"RUL real < {threshold_aog:.0f}", border=True,
                delta_color="off", icon=":material/target:",
                help="Error absoluto medio donde de verdad se decide el mantenimiento.")

    # -------------------- procedencia y contrato (los dos SHA, plegados)
    with st.container(border=True):
        st.subheader("Procedencia y contrato", icon=":material/lock:")
        st.caption(
            "Los dos SHA son datos de procedencia, no el nombre del motor. El "
            "primero identifica el artefacto congelado con el que se calculó; el "
            "segundo, la ventana exacta que se puntuó. El mismo motor en dos "
            "ventanas da dos huellas, y dos motores con los mismos datos dan la "
            "misma: por eso no pueden nombrar un motor."
        )
        with st.container(horizontal=True):
            st.metric(
                "SHA-256 del artefacto",
                provenance["artifact"]["ensemble_sha256"][:12],
                "models/ds02_manifest.json", border=True, delta_color="off",
                icon=":material/deployed_code:")
            st.metric(
                "Ventanas en caché",
                f"{provenance['counts']['windows']:,}",
                f"generada {provenance['generated_at'][:10]}",
                border=True, delta_color="off", icon=":material/dataset:")
        st.caption(
            f"Contrato: ventana de {provenance['source']['window']} muestras, "
            f"step={provenance['source']['step']}. La caché va a step=2 y la vía "
            f"en vivo a step=1, así que no coinciden bit a bit, y el punto está "
            f"suavizado con un EMA causal por motor. Documentado, no reconciliado."
        )
