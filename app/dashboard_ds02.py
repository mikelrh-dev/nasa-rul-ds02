"""DS02 maintenance decision-support surface.

    streamlit run app/dashboard_ds02.py

Five tabs over one cached frame: fleet hangar, RUL with its conformal band,
physical sensor radiography, the engine-14 audit, and the live evaluation of a
unit you bring. Everything is read from `app/cache/` (see
`scripts/build_ui_cache.py`) and `models/ds02_manifest.json`; the frozen bundle is
never loaded, so no TensorFlow import is needed and the app runs from a laptop
without the 2.3 GB HDF5.

Both rule passes run through `src/mia/`: the correction pass (R2b + R6) behind the
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
import pdf_partes as PP  # noqa: E402
import ui_inference as INF  # noqa: E402
import ui_rules as UR  # noqa: E402
import flota as F  # noqa: E402
import dashboard_helpers as DH  # noqa: E402
import simulacion as S  # noqa: E402
import ui_modulos as UM  # noqa: E402
import ui_n8n as UN  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import n8n as N8N  # noqa: E402

# Estado de sesión en un solo sitio: gemelos y registros de hangar.
# Se cargan de disco una sola vez: recargar la página ya no borra la flota.
# Cada sesión tiene su fichero en `registros_sesiones/`; los huérfanos se
# conservan (no hay borrado automático). El legacy `registros_flota.json` se
# copia una vez por sesión y no se mueve ni se toca después.
_LEGACY_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "registros_flota.json")
_REGISTROS_PATH = _LEGACY_PATH  # alias legacy
_DEFAULT_SESSION_ID = "default"


def _candidate_session_id():
    """`session_id` por query_params -> session_state -> script ctx -> default."""
    try:
        valor = st.query_params.get("session_id")
    except Exception:
        valor = None
    if isinstance(valor, (list, tuple)):
        valor = valor[0] if valor else None
    if valor:
        return valor, "query_params"
    valor = st.session_state.get("session_id")
    if valor:
        return valor, "session_state"
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        ctx = get_script_run_ctx()
        if ctx is not None:
            valor = getattr(ctx, "session_id", None)
            if valor:
                return valor, "script ctx"
    except Exception:
        pass
    return _DEFAULT_SESSION_ID, "default"


def _active_registry_path():
    """Ruta de la sesión activa; inválida -> error visible y memoria (sin fichero)."""
    if "_registry_path_resuelta" in st.session_state:
        return st.session_state["_registry_path"]
    candidato, fuente = _candidate_session_id()
    try:
        ruta = HGR.session_registry_path(candidato)
    except ValueError as exc:
        st.error(f"session_id inválido ({exc}); registro en memoria, sin fichero")
        st.session_state["_registry_path_resuelta"] = True
        st.session_state["_registry_path"] = None
        return None
    # Fallback válido (session_state/script ctx/default): silencioso a propósito.
    # Es diagnóstico interno, no aviso de usuario: un warning en grande aquí
    # domina la primera pantalla y rompe la lectura de "Primera lectura".
    # Solo se pinta si el id es inválido (rama anterior).
    st.session_state["_registry_path_resuelta"] = True
    st.session_state["_registry_path"] = ruta
    st.session_state["session_id"] = candidato
    return ruta


def _cargar_registros() -> None:
    """Carga el registro de la sesión (twins/hangar/altas) desde disco."""
    if not st.session_state.get("_registros_cargados"):
        disco: dict = HGR.empty_registry()
        ruta = _active_registry_path()
        if ruta is not None:
            if not os.path.exists(ruta):
                try:
                    HGR.migrate_legacy_registry(_LEGACY_PATH, ruta)
                except (OSError, ValueError) as exc:
                    st.error(f"no se pudo migrar el registro legacy: {exc}")
            disco, aviso = HGR.load_session_registry_with_status(ruta)
            if aviso:
                st.error(aviso)
        st.session_state.setdefault("twins", dict(disco.get("twins", {})))
        st.session_state.setdefault("hangar", dict(disco.get("hangar", {})))
        # El alta viaja en el mismo JSON. Antes vivia solo en `session_state`
        # y desaparecia al recargar: el motor se perdia y el usuario creia
        # haber hecho algo mal.
        st.session_state.setdefault(F.ALTAS_KEY, dict(disco.get(F.ALTAS_KEY, {})))
        st.session_state["_registros_cargados"] = True


def _guardar_registros() -> None:
    """Guarda el registro de la sesión (twins/hangar/altas) en disco."""
    ruta = _active_registry_path()
    if ruta is None:
        return
    try:
        HGR.save_session_registry(
            ruta, {"twins": st.session_state.get("twins", {}),
                   "hangar": st.session_state.get("hangar", {}),
                   F.ALTAS_KEY: st.session_state.get(F.ALTAS_KEY, {})})
    except (OSError, ValueError) as exc:
        st.error(f"no se pudo guardar el registro de la sesión: {exc}")


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

    Se consume a nivel de módulo, antes de los tabs/fragmentos, no dentro de
    un fragmento: un fragmento solo se re-ejecuta con sus propios widgets, así
    que un `pop` dentro de él no corre en cada pasada completa (y un `get`
    sin consumir repite el toast en cada rerun del fragmento). Todos los
    handlers que piden estos avisos terminan en `st.rerun()` completo, así
    que la pasada siguiente los pinta una sola vez aquí.
    """
    mensaje = st.session_state.pop("_toast_pendiente", None)
    if mensaje:
        st.toast(mensaje, icon=":material/info:")
    for _clave in ("live_flash", "twin_flash"):
        _aviso = st.session_state.pop(_clave, None)
        if _aviso:
            st.toast(_aviso, icon=":material/check_circle:")


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
        st.metric("Filas", L.fmt_miles(pf['filas']), border=True, delta_color="off",
                  icon=":material/table_rows:")
        st.metric("Ventanas", L.fmt_miles(pf['ventanas']), border=True, delta_color="off",
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
    L.NO_DATA: "en espera",
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
    """Applies the shared themed axes style to a figure."""
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


# Helper único de SHA-256: dueño `ui_data_loader` (único `def` en `app/`);
# aquí se re-exporta para compat. Digest y `OSError -> None` intactos.
_sha256_cached = UM._sha256_cached

# Sandbox de estrés (PR2, dashboard-split-monolito 2.1): dueño
# `ui_modulos._sandbox_estres`; aquí se re-exporta para compat y se llama
# con los globales del dashboard. `_sandbox_puntua_cached` sigue siendo
# dueño único en este fichero (una sola `def` en `app/`) y se pasa como
# helper, sin duplicar su lógica en el módulo extraído.
try:
    from ui_modulos._sandbox_estres import _sandbox_estres as _sandbox_estres
except ImportError:  # pragma: no cover - import-style fallback
    from app.ui_modulos._sandbox_estres import _sandbox_estres as _sandbox_estres  # type: ignore[no-redef]

# Flota (PR3, dashboard-split-monolito 2.2): dueño
# `ui_modulos._tab_flota`; aquí se delega desde el wrapper `_tab_flota`
# (la pestaña sigue llamándose `_tab_flota()` con los globales del
# dashboard: `frame_cache` ttl=3600, SHAP cache y PDF
# `artefacto_sha256` intactos en este fichero).
try:
    from ui_modulos._tab_flota import _tab_flota as _tab_flota_impl
except ImportError:  # pragma: no cover - import-style fallback
    from app.ui_modulos._tab_flota import _tab_flota as _tab_flota_impl  # type: ignore[no-redef]

# Motor (PR4, dashboard-split-monolito 2.3): dueno
# `ui_modulos._tab_motor`; aqui se delega desde el wrapper `_tab_motor`
# (la pestana sigue llamandose `_tab_motor()` con los globales del
# dashboard: `frame_cache` ttl=3600, SHAP cache y PDF
# `artefacto_sha256` intactos en este fichero).
try:
    from ui_modulos._tab_motor import _tab_motor as _tab_motor_impl
except ImportError:  # pragma: no cover - import-style fallback
    from app.ui_modulos._tab_motor import _tab_motor as _tab_motor_impl  # type: ignore[no-redef]

# Auditoria (PR5, dashboard-split-monolito 2.4): dueno
# `ui_modulos._tab_auditoria`; aqui se delega desde el wrapper
# `_tab_auditoria` (la pestana sigue llamandose `_tab_auditoria()` con los
# globales del dashboard: `frame_cache` ttl=3600, SHAP cache y PDF
# `artefacto_sha256` intactos en este fichero).
try:
    from ui_modulos._tab_auditoria import _tab_auditoria as _tab_auditoria_impl
except ImportError:  # pragma: no cover - import-style fallback
    from app.ui_modulos._tab_auditoria import _tab_auditoria as _tab_auditoria_impl  # type: ignore[no-redef]


def shap_panel(unit: int, suffix: str = "motor") -> None:
    """Panel SHAP unificado: top features + waterfall Plotly.

    Sustituye a los dos bloques SHAP duplicados (Motor y Casos nuevos): una
    sola definición, dos call sites con claves de botón distintas.
    """
    try:
        import ui_shap as USH
    except ImportError:
        st.info(
            "SHAP no instalado: `ui_shap` no está en el entorno. Instala el "
            "paquete con `pip install shap` y recarga. El resto de la app "
            "sigue funcionando sin explicabilidad.",
            icon=":material/info:",
        )
        return

    if st.button(
        "Calcular SHAP para este motor",
        icon=":material/psychology:",
        key=f"btn_shap_{suffix}",
        help="Calcula las contribuciones exactas del LightGBM del híbrido "
             "(TreeExplainer) para la última ventana del motor.",
    ):
        try:
            _shap_df = USH.shap_top_features(int(unit), top_k=10)
        except ImportError:
            st.info(
                "SHAP no instalado: falta el paquete `shap` (`pip install shap`). "
                "Sin él no se puede explicar la predicción.",
                icon=":material/info:",
            )
            return
        except Exception as _e:
            st.warning(f"No se pudo calcular SHAP: {_e}", icon=":material/warning:")
            return
        if _shap_df is not None and not _shap_df.empty:
            import plotly.express as px

            _fig_shap = px.bar(
                _shap_df.sort_values("abs_shap"),
                x="abs_shap", y="feature", orientation="h",
                labels={"abs_shap": "mean |SHAP| (ciclos RUL)",
                        "feature": "feature"},
                title=f"Top-10 features · motor {int(unit)}",
            )
            _fig_shap.update_layout(**chart_layout(height=360))
            st.plotly_chart(
                _fig_shap, use_container_width=True,
                alt=f"Top-10 contribuciones SHAP del motor {int(unit)}.",
            )
            st.dataframe(_shap_df, use_container_width=True, hide_index=True)
            try:
                _wf_fig = USH.shap_waterfall_fig(int(unit), max_display=12)
            except ImportError:
                st.info(
                    "SHAP no instalado: falta el paquete `shap` (`pip install shap`).",
                    icon=":material/info:",
                )
                return
            except Exception as _e2:
                st.warning(f"No se pudo generar el waterfall: {_e2}",
                           icon=":material/warning:")
                return
            _wf_fig.update_layout(**chart_layout(height=420))
            style_axes(_wf_fig, x_title="feature", y_title="contribución")
            st.plotly_chart(
                _wf_fig, use_container_width=True,
                alt=f"SHAP waterfall del motor {int(unit)}.",
            )
        else:
            st.info("Sin datos suficientes para calcular SHAP.",
                    icon=":material/info:")


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
# «Ver gemelo» del muro apunta al tab Motor con `selected_unit` (app-ux-bundle-fix):
# la clave del widget del sidebar es `unit`, así que la selección se consume aquí,
# antes de que los widgets se instancien. `selected_unit` queda como huella visible.
if st.session_state.pop("_ver_gemelo_pendiente", None) is not None:
    _sel = st.session_state.get("selected_unit")
    if _sel is not None:
        try:
            st.session_state["unit"] = int(_sel)
        except (TypeError, ValueError):
            pass
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
    "Conservador (+10)": (10.0, 10.0),
    "Agresivo (−10)": (-10.0, -10.0),
}
preset = str(st.session_state.get("preset", "Normal"))
_base_apto = float(provenance["defaults"]["threshold_airworthy"])
_base_aog = float(provenance["defaults"]["threshold_aog"])
_d_apto, _d_aog = _PRESETS.get(preset, _PRESETS["Normal"])
_preset_vals = (max(1.0, _base_apto + _d_apto), max(0.0, _base_aog + _d_aog))
# Sincroniza spinbuttons con el preset al cambiar: Streamlit ignora `value=`
# si la clave ya existe y la historia deja valores persistentes (35/20).
# Al cambiar se sobrescriben las claves del preset vigente con `_preset_vals`
# para que Prudente→Normal restaure 30/25. Ediciones manuales del mismo
# preset se descartan por diseño (D3).
_prev_preset = st.session_state.get("_preset_prev")
if _prev_preset is not None and _prev_preset != preset:
    st.session_state[f"th_apto_{preset}"] = float(_preset_vals[0])
    st.session_state[f"th_aog_{preset}"] = float(_preset_vals[1])
st.session_state["_preset_prev"] = preset
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
    "R6 recalibrada (src/mia/calibracion_banda.json, 14 915 filas OOF puras)"
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
    # Qué ve cada audiencia: el tribunal necesita todo; el operario, solo su turno.
    st.segmented_control(
        "Vista",
        ["Tribunal", "Turno"],
        default="Tribunal",
        key="vista_modo",
        help="Tribunal muestra todo (evidencia, demo, sandbox). Turno deja solo lo "
             "que un operario usa en su guardia.",
    )
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

    # El reloj de flota va aquí, junto a la unidad: son los dos controles que se
    # usan juntos. El «ciclo del alta» de más abajo es otro concepto.
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
    st.divider()

    # Sin `st.form`: la matrícula se deriva de la unidad y tiene que refrescarse
    # al cambiarla. En un form el valor no viaja hasta enviar y quedaría obsoleto.
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
    matricula = st.text_input(
        "Matrícula (etiqueta de visualización, auto-generada)",
        value=f"MTTT{int(unidad_libre)}", disabled=True,
        help="No es un identificador real de aeronave: es la etiqueta con la que "
             "el motor aparece en el muro y en el hangar.",
    )
    enviar = st.button("Incorporar unidad",
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
    with st.expander("Reset de flota (quitar unidades de alta)",
                     icon=":material/restart_alt:"):
        st.caption(
            "Deshace las altas de esta sesión. La flota de la caché no se toca."
        )
        altas = _altas()
        if not altas:
            st.caption("Ninguna aeronave de alta en esta sesión.")
        else:
            a_quitar = st.selectbox(
                "Aeronave", [a["matricula"] for a in altas], key="alta_quitar",
                help="Aeronave de alta a quitar de esta sesión. La flota de la caché no se toca.",
            )
            if st.button("Quitar", icon=":material/delete:", key="alta_quitar_btn"):
                registro = _registro()
                registro = F.quitar_alta(registro, a_quitar)
                st.session_state[F.ALTAS_KEY] = registro[F.ALTAS_KEY]
                st.session_state["twins"] = registro.get("twins") or {}
                st.session_state["hangar"] = registro.get("hangar") or {}
                _guardar_registros()
                st.rerun()
    st.caption(
        f"Caché con {L.fmt_miles(provenance['counts']['windows'])} ventanas y "
        f"{L.fmt_miles(provenance['counts']['rows'])} filas de telemetría · "
        f"generada {provenance['generated_at'][:16].replace('T', ' ')}"
    )

    with st.expander("Cómo leer esta pantalla", icon=":material/help:"):
        st.markdown(
            """- **RUL**: ciclos que le quedan al motor (estimación, no medida).
- **L_inf / objetivo nominal 90 % · cobertura medida empíricamente**: cota inferior conformal; gobierna la decisión (APTO · INSPECCIÓN · HANGAR/AOG).
- **Ciclo de vuelo / Ventana**: reloj simulado; 50 muestras remuestreadas (~0,4 ciclos) por ventana.
- **Orden de trabajo**: JSON/CSV de las unidades bloqueadas con banda y acción."""
        )

    # Panel n8n visible (app-ux-bundle-fix): estado del webhook, último envío y
    # botón de prueba. Nunca rompe la app si falta la URL (ver src/n8n.py).
    with st.expander("n8n · webhook de decisión", icon=":material/webhook:"):
        _url_n8n = os.environ.get("N8N_WEBHOOK_URL", "")
        if _url_n8n:
            st.caption(f"Webhook configurado: `{_url_n8n}`")
        else:
            st.caption(
                "Webhook no configurado (`N8N_WEBHOOK_URL` vacío): los envíos "
                "quedan en log local y el test devuelve ok=False."
            )
        _ult_n8n = st.session_state.get("n8n_ultimo") or {}
        if _ult_n8n:
            st.caption(
                f"Último envío: {_ult_n8n.get('decision', '?')} · "
                f"ok={_ult_n8n.get('ok')} · status={_ult_n8n.get('status')} · "
                f"en {_ult_n8n.get('en', '?')}"
            )
        else:
            st.caption("Último envío: ninguno en esta sesión.")
        if st.button("Probar envío n8n", key="n8n_prueba", icon=":material/send:"):
            _res_prueba = DH.probar_n8n()
            st.session_state["n8n_ultimo"] = {
                "decision": "APTO (test)",
                "ok": bool(isinstance(_res_prueba, dict) and _res_prueba.get("ok") is True),
                "status": (_res_prueba.get("status") if isinstance(_res_prueba, dict) else None),
                "en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }


# La capa de reglas (src/mia/) es opcional y arranca apagada: con ella apagada la UI
# muestra la lectura cruda de la caché, que es la que reproduce el contrato
# congelado en models/ds02_manifest.json.
umbrales = {"apto": float(threshold_apto), "hangar": float(threshold_aog)}
# P1.1 · Frame decidido fusionado: antes «Avanzar la flota» volvía a ejecutar
# `decidir_ventanas` sobre `windows` cruda en cada rerun (6196 filas, 2ª pasada
# redundante). Ahora una sola pasada corregida+decidida, cacheada por
# (umbrales, aplicar_reglas, sha de caché): el segundo llamador reutiliza este
# mismo frame (solo lee unit/cycle/lower). La clave lleva el sha de provenance
# para que una caché regenerada no sirva el frame viejo (ttl 3600).
_cache_sha = (
    f"{provenance['artifact']['ensemble_sha256']}:"
    f"{provenance['counts'].get('windows_sha256', '')}:"
    f"{provenance.get('generated_at', '')}"
)


@st.cache_data(ttl=3600, show_spinner=False)
def _frame_cache_cached(
    apto: float, hangar: float, aplicar: bool, cache_sha: str
) -> pd.DataFrame:
    """Corrección (opcional) + pasada A sobre la caché, una sola vez por clave.

    Lee los globales `windows` (cargados con `L.get_windows()`, ya cacheados):
    la clave son escalares + sha, así que no hay que hashear el DataFrame en
    cada render. No muta `windows` (`corregir`/`decidir` copian dentro).
    """
    base = UR.corregir_ventanas(windows) if aplicar else windows.copy()
    # Pasada A del motor `src/mia/`: R1/R9/R8/R7 deciden sobre el límite inferior.
    return UR.decidir_ventanas(base, {"apto": float(apto), "hangar": float(hangar)})


# `frame_cache` es solo la caché: de aquí salen las métricas y la telemetría.
# `frame` incluye las aeronaves de alta: de aquí sale la flota y las órdenes.
frame_cache = _frame_cache_cached(
    float(threshold_apto), float(threshold_aog), bool(aplicar_reglas), _cache_sha
)
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
    _matriculas_altas = {a["matricula"] for a in _altas()}
    for gemelo_id, gemelo in gemelos.items():
        # El alta ya aparece en `tarjetas_cache` via `frame_con_altas`: no se
        # duplica en el muro (sigue en Gemelos registrados). Sin este filtro,
        # 1 Incorporar = 2 tarjetas (3->5).
        if gemelo_id in _matriculas_altas:
            continue
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

# Orden compartido entre pestañas: Flota la pinta y Motor la consulta para el
# «Orden de trabajo» del motor. Se calcula a nivel módulo (antes de los tabs)
# para que los fragmentos `_tab_flota` y `_tab_motor` lean el mismo global.
order = L.work_order(snapshot, provenance, threshold_apto, threshold_aog,
                     banda=banda_en_uso, correccion=correccion_en_uso)

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
            f"{L.fmt_miles(global_metrics['windows'])} ventanas",
            icon=":material/table_rows:", color="blue",
        )
        st.badge(
            f"Banda {provenance['artifact']['conformal_target_coverage']:.0%}",
            icon=":material/verified:", color="green",
        )
        st.badge(
            "Lectura corregida (R2b+R6)" if aplicar_reglas else "Lectura cruda de caché",
            icon=":material/tune:", color="blue",
        )

with st.container(border=True):
    st.subheader("Primera lectura", icon=":material/visibility:")
    _total_muro = len(tarjetas_cache) + len(tarjetas_gemelos)
    hangar_en_muro = grounded + derivados_gemelos
    with st.container(horizontal=True):
        st.metric("Unidades monitorizadas", f"{global_metrics['units']}",
                  f"{L.fmt_miles(global_metrics['windows'])} ventanas evaluadas",
                  border=True, icon=":material/groups:", delta_color="off")
        st.metric("Unidades en hangar", f"{hangar_en_muro} / {_total_muro}",
                  f"en el ciclo {cycle}", border=True,
                  icon=":material/local_shipping:", delta_color="off")
    st.caption(
        "La decisión de inmovilizar no la toma la predicción del modelo: la toma "
        "el peor caso de su banda. Por eso un motor puede quedar en hangar con "
        "vida útil estimada por encima del umbral."
    )
    st.caption(
        f"El contador incluye la flota de la caché y los motores registrados: "
        f"{grounded} de caché + {derivados_gemelos} registrados = {hangar_en_muro} "
        f"en el muro, sobre {_total_muro} tarjetas."
    )

# P1.4 · Inferencia del sandbox cacheada por (unit, deriva, umbrales). Antes
# cada movimiento del deslizador re-ejecutaba preflight + score_table (~5,89 s)
# aunque el estado fuera el mismo que la vez anterior. `tramo_sig` es el sha
# de provenance (`_cache_sha`): si la caché se regenera, la clave cambia y el
# tramo se re-puntúa. Devuelve el resultado ya decidido, sin tocar `st`.


@st.cache_data(ttl=3600, show_spinner="Re-puntuando tramo con el artefacto…")
def _sandbox_puntua_cached(
    unit: int, deriva_pct: int, apto: float, hangar: float, tramo_sig: str,
    sensor: str = "T48",
) -> tuple:
    """Preflight + puntuación + decisión del tramo perturbado (una vez por clave).

    Devuelve `(ok, error, avisos, dec, ventas)`: `dec` es el frame decidido por
    ventana (o `None` si no puntuó). Los errores de validación/puntuación se
    devuelven como valores, no se lanzan, para que el fragment los pinte igual
    que antes.
    """
    _umb = {"apto": float(apto), "hangar": float(hangar)}
    _cur_sbx = L.unit_curve(windows, int(unit))
    _c_inicio = int(_cur_sbx["cycle"].min())
    _bajo = _cur_sbx[_cur_sbx["lower_min"] < _umb["hangar"]]
    _c_fin = (int(_bajo["cycle"].min()) if not _bajo.empty
              else int(_cur_sbx["cycle"].max()))
    _tramo = telemetry[(telemetry["unit"] == int(unit))
                       & (telemetry["cycle"] >= _c_inicio)
                       & (telemetry["cycle"] <= _c_fin)].reset_index(drop=True)
    _tab = _tramo[["cycle"] + INF.channel_order()].copy()
    _deriva = float(int(deriva_pct)) / 100.0
    _tab[sensor] = _tab[sensor].astype(float) * (
        1.0 + _deriva * np.linspace(0.0, 1.0, len(_tab)))
    _pf = INF.preflight(_tab)
    if not _pf["ok"]:
        return (False, _pf["error"], tuple(_pf["avisos"]), None, 0)
    try:
        _win = INF.score_table(_tab, engine_id=f"ESN-SBX-{int(unit)}")["windows"]
    except ValueError as exc:
        return (False, str(exc), tuple(_pf["avisos"]), None, 0)
    return (True, None, tuple(_pf["avisos"]),
            UR.decidir_ventanas(_win, _umb), int(len(_win)))




def _informe_auditoria_pdf(
    windows: pd.DataFrame,
    curves: dict,
    unidades: list,
    threshold_apto: float,
    threshold_aog: float,
    provenance: dict,
    critical_mae: float,
) -> bytes:
    """Informe de auditoría en PDF: las dos tablas que un tribunal pide.

    Congela la huella del artefacto y las tablas de Evidencia, para que el papel
    y la pantalla digan lo mismo. No recalcula el modelo: reusa las series ya
    puntuadas de la caché.
    """
    from fpdf import FPDF

    def _latin1(txt: str) -> str:
        """fpdf2 con fuentes core solo codifica latin-1: traduce lo que no entra."""
        for _a, _b in (("∞", "inf"), ("≥", ">="), ("≤", "<="), ("—", "-"),
                       ("–", "-"), ("×", "x"), ("≈", "~"), ("→", "->"),
                       ("·", "-"), ("…", "...")):
            txt = str(txt).replace(_a, _b)
        return txt.encode("latin-1", "replace").decode("latin-1")

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, "Informe de auditoria - RUL DS02", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=10)
    pdf.cell(0, 6,
             f"Politica en vigor: apto si L_inf >= {threshold_apto:.0f} | "
             f"inspeccion si {threshold_aog:.0f} <= L_inf < {threshold_apto:.0f} | "
             f"hangar si L_inf < {threshold_aog:.0f}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6,
             f"Artefacto congelado SHA-256: {provenance['artifact']['ensemble_sha256']}",
             new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6,
             f"MAE en zona critica (RUL real < {threshold_aog:.0f}): "
             f"{critical_mae:.2f} ciclos",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Precision por tramo de vida (MAE sobre RUL real)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 10)
    for ancho, txt in ((35, "Tramo"), (30, "Ventanas"), (30, "MAE"), (30, "Sesgo")):
        pdf.cell(ancho, 7, txt, border=1, align="C")
    pdf.ln()
    pdf.set_font("helvetica", size=10)
    for r in L.mae_by_band(windows).itertuples():
        pdf.cell(35, 7, _latin1(r.band), border=1)
        pdf.cell(30, 7, f"{int(r.windows)}", border=1, align="R")
        pdf.cell(30, 7, "n/a" if pd.isna(r.mae) else f"{r.mae:.3f}", border=1, align="R")
        pdf.cell(30, 7, "n/a" if pd.isna(r.bias) else f"{r.bias:+.3f}", border=1, align="R")
        pdf.ln()
    pdf.ln(4)

    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "Alarma vs. verdad (adelanto por motor)",
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", "B", 10)
    for ancho, txt in ((30, "Motor"), (40, "Alarma"), (40, "RUL real < umbral"),
                       (35, "Adelanto")):
        pdf.cell(ancho, 7, txt, border=1, align="C")
    pdf.ln()
    pdf.set_font("helvetica", size=10)
    for u in unidades:
        a, t = L.first_alarm_cycle(curves[u], threshold_aog)
        pdf.cell(30, 7, f"U{int(u)}", border=1)
        pdf.cell(40, 7, "-" if a is None else str(int(a)), border=1, align="R")
        pdf.cell(40, 7, "-" if t is None else str(int(t)), border=1, align="R")
        pdf.cell(35, 7, "-" if (a is None or t is None) else str(int(t - a)),
                 border=1, align="R")
        pdf.ln()
    pdf.ln(4)

    pdf.set_font("helvetica", "I", 8)
    pdf.multi_cell(
        0, 5,
        "La banda conformal es la de la serie guardada: no se recalibra al mover los "
        "umbrales, porque la calibracion es parte del artefacto congelado. La decision "
        "la toma el limite inferior de la banda, no la prediccion puntual (ADR-008).")
    return bytes(pdf.output())


@st.cache_data(ttl=3600, show_spinner="Generando informe de auditoría…")
def _informe_pdf_cached(
    threshold_apto: float,
    threshold_aog: float,
    critical_mae: float,
    ensemble_sha256: str,
    windows_sig: str,
    aplicar_reglas: bool = False,
    pdf_version: str = "",
) -> bytes:
    """Constructor cacheado del PDF de auditoría.

    Lee los globales de la app (`windows`, `curves`, `unidades_vistas`,
    `provenance`): la clave son escalares (umbrales, SHA, firma de caché,
    aplicar_reglas y versión de manifest), así que no hay que hashear
    DataFrames en cada render. P1.3: `aplicar_reglas` y `pdf_version`
    (curvas/alarmas vía `windows_sig` + versión del manifest) cierran el
    PDF stale al mover umbrales o activar la corrección.
    """
    return _informe_auditoria_pdf(
        windows, curves, unidades_vistas,
        threshold_apto, threshold_aog, provenance, critical_mae,
    )


# La vista la escribe el widget de la barra lateral; aquí solo se lee. Turno
# esconde en Flota el material de demo y de auditoría.
_vista_tribunal = str(st.session_state.get("vista_modo", "Tribunal")) == "Tribunal"

tab_flota, tab_motor, tab_casos, tab_auditoria = st.tabs(
    [
        ":material/factory: Flota · qué pasa hoy",
        ":material/precision_manufacturing: Motor · qué le pasa a este",
        ":material/library_add: Casos nuevos · trae un motor",
        ":material/science: Auditoría · cómo se calculó",
    ]
)


with tab_flota:
    def _tab_flota() -> None:
        """Flota (PR3): delega en `ui_modulos._tab_flota` con los globales.

        Wrapper fino: el cuerpo vive en el módulo extraído (byte-idéntico
        al fragmento inline, incluido `_muro_del_hangar`). El dashboard
        sigue dueño de `windows`/`telemetry`/`frame_cache` (ttl=3600),
        la caché SHAP y la firma PDF `artefacto_sha256`.
        """
        _tab_flota_impl(
            frame=frame, frame_cache=frame_cache, snapshot=snapshot,
            curves=curves, unidades_vistas=unidades_vistas,
            tarjetas_cache=tarjetas_cache, tarjetas_gemelos=tarjetas_gemelos,
            gemelos=gemelos, registros=registros, order=order,
            correccion=correccion, windows=windows, provenance=provenance,
            unit=unit, cycle=cycle, threshold_apto=threshold_apto,
            threshold_aog=threshold_aog, umbrales=umbrales, preset=preset,
            presets=_PRESETS, preset_vals=_preset_vals,
            banda_en_uso=banda_en_uso, correccion_en_uso=correccion_en_uso,
            vista_tribunal=_vista_tribunal, etiqueta_unidad=_etiqueta_unidad,
            registro=_registro, slug_motor=_slug_motor,
            guardar_registros=_guardar_registros, chart_layout=chart_layout,
            style_axes=style_axes,
        )

    _tab_flota()
with tab_motor:
    def _tab_motor() -> None:
        """Motor (PR4): delega en `ui_modulos._tab_motor` con los globales.

        Wrapper fino: el cuerpo vive en el modulo extraido (byte-identico
        al fragmento inline). El dashboard sigue dueno de `windows`/
        `telemetry`/`frame_cache` (ttl=3600), la cache SHAP y la firma
        PDF `artefacto_sha256`.
        """
        _tab_motor_impl(
            snapshot=snapshot, unit=unit, etiqueta_unidad=_etiqueta_unidad,
            registro=_registro, curves=curves, telemetry=telemetry,
            order=order, registros=registros, unidades_vistas=unidades_vistas,
            threshold_apto=threshold_apto, threshold_aog=threshold_aog,
            umbrales=umbrales, aplicar_reglas=aplicar_reglas, curve=curve,
            per_unit=per_unit, unit_metrics=unit_metrics,
            alarm_cycle=alarm_cycle, truth_cycle=truth_cycle, current=current,
            wu=_wu, coverage=coverage, critical_start=critical_start,
            max_life=max_life, chart_layout=chart_layout,
            style_axes=style_axes, shap_panel=shap_panel,
            fig_deriva=fig_deriva, st_badge_estado=st_badge_estado,
        )

    # ------------------------------------------------------- auditoria: el como
    _tab_motor()
with tab_auditoria:
    def _tab_auditoria() -> None:
        """Auditoria (PR5): delega en `ui_modulos._tab_auditoria` con los globales.

        Wrapper fino: el cuerpo vive en el modulo extraido (byte-identico
        al fragmento inline). El dashboard sigue dueno de `windows`/
        `telemetry`/`frame_cache` (ttl=3600), la cache SHAP y la firma
        PDF `artefacto_sha256`.
        """
        _tab_auditoria_impl(
            per_unit=per_unit, provenance=provenance,
            chart_layout=chart_layout, style_axes=style_axes,
            windows=windows, units=units, curves=curves,
            threshold_aog=threshold_aog, global_metrics=global_metrics,
            critical_mae=critical_mae, manifest=manifest, cycle=cycle,
            alarms=alarms, unidades_vistas=unidades_vistas,
            threshold_apto=threshold_apto, aplicar_reglas=aplicar_reglas,
            sha256_cached=_sha256_cached,
            informe_pdf_cached=_informe_pdf_cached,
        )

    # ------------------------------------------- casos nuevos: trae un motor
    _tab_auditoria()

with tab_casos:
    @st.fragment
    def _tab_casos() -> None:
        """Sala «Casos nuevos»: incorporar motores en lote y registrarlos."""
        # Los avisos `live_flash`/`twin_flash` se consumen a nivel de módulo
        # en `_mostrar_toast_pendiente()` (antes de los tabs): aquí solo se
        # lee `session_state` para el resto, sin mutarlo dentro del fragmento.

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
                        # P1: `bloques_de_archivos` rechaza el lote antes de
                        # parsear todo si hay > MAX_MOTORES_LOTE archivos y
                        # valida tamaño en bytes + nrows=MAX_FILAS+1 por archivo.
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
                            """Actualiza la barra de progreso al puntuar el lote."""
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
                        """Actualiza la barra de progreso al registrar los gemelos."""
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

        # El caso crítico usa el ciclo del estado demo (29): es el primer ciclo
        # cuyo tramo en vivo (ultima ventana) cae en HANGAR con el bundle C
        # (L_inf 21.4 en vivo). El paso 3 del modo historia (25) es la primera
        # derivación por peor ventana de la flota: otra agregación, no el tramo.
        _demo_crit = A.estado_demo()
        _u_hangar = int(_demo_crit["unidad"])
        _c_hangar = int(_demo_crit["ciclo"])
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
        with st.container(border=True):
            st.subheader("Explora por ciclo", icon=":material/timeline:")
            st.caption(
                "Elige un motor y un punto de su vida: se genera el tramo y se muestra "
                "el estado calculado. No se puntúa hasta pulsar \"Evaluar este tramo\"."
            )
            _exp_cols = st.columns(4)
            with _exp_cols[0]:
                _exp_unit = st.selectbox(
                    "Motor",
                    [11, 14, 15],
                    key="explorar_unit",
                    help="Unidad de la caché (11, 14 o 15).",
                )
            with _exp_cols[1]:
                _exp_len = st.selectbox(
                    "Largo del tramo",
                    [50, 300],
                    index=1,
                    key="explorar_len",
                    help="50 = una ventana; 300 = trayectoria con EMA suavizada.",
                )
            with _exp_cols[2]:
                _exp_mode = st.selectbox(
                    "Modo",
                    ["Posición relativa", "Ciclo final"],
                    key="explorar_mode",
                    help="Posición relativa: fracción de la vida (0-1). "
                         "Ciclo final: elige el ciclo exacto en que termina el tramo.",
                )
            with _exp_cols[3]:
                if _exp_mode == "Posición relativa":
                    _exp_pos = st.slider(
                        "Punto final (posición en la vida del motor)",
                        0.0, 1.0, 0.5, 0.01,
                        key="explorar_pos",
                        help="0.0 = inicio, 1.0 = final. El tramo termina en ese punto.",
                    )
                else:
                    _ciclos_disp = sorted(
                        int(c) for c in windows[windows["unit"] == _exp_unit]["cycle"].unique()
                    )
                    _exp_cycle = st.selectbox(
                        "Ciclo final",
                        _ciclos_disp,
                        key="explorar_cycle",
                        help="Ciclo exacto en que termina el tramo. "
                             "El tramo abarca los ciclos anteriores según el largo elegido.",
                    )
            try:
                if _exp_mode == "Posición relativa":
                    _exp_tab, _exp_meta = INF.example_window(
                        _exp_unit, _exp_pos, rows=_exp_len)
                else:
                    _exp_tab, _exp_meta = INF.window_ending_at(
                        _exp_unit, _exp_cycle, rows=_exp_len)
                _exp_pf = INF.preflight(_exp_tab)
                _exp_ok = bool(_exp_pf["ok"])
                st.session_state["explorar_table"] = _exp_tab
                st.session_state["explorar_meta"] = _exp_meta
                st.session_state["explorar_ok"] = _exp_ok
                st.session_state["explorar_avisos"] = _exp_pf["avisos"]
                _exp_end_cycle = int(_exp_meta["end_cycle"])
                _cached = windows[(windows["unit"] == _exp_unit)
                                  & (windows["cycle"] == _exp_end_cycle)]
                if not _cached.empty:
                    _exp_lower = float(_cached["lower"].iloc[-1])
                    _exp_state = L.classify(
                        _exp_lower, umbrales["apto"], umbrales["hangar"])
                else:
                    _exp_state = "sin referencia en caché"
                st.session_state["explorar_state"] = _exp_state
                _exp_err = None if _exp_ok else _exp_pf["error"]
            except ValueError as _exc:
                _exp_tab = None
                _exp_meta = None
                st.session_state["explorar_table"] = None
                st.session_state["explorar_meta"] = None
                st.session_state["explorar_ok"] = False
                st.session_state["explorar_state"] = "—"
                _exp_err = str(_exc)
            if _exp_err:
                st.error(_exp_err, icon=":material/error:")
            else:
                st.caption(
                    f"Tramo: ciclos {_exp_meta['start_cycle']}→{_exp_meta['end_cycle']} · "
                    f"{len(_exp_tab)} filas · estado estimado: **{_exp_state}**"
                )
                for _av in st.session_state.get("explorar_avisos", []) or []:
                    st.warning(_av, icon=":material/warning:")
                with st.expander("Ver tramo generado", expanded=False):
                    st.dataframe(
                        _exp_tab,
                        hide_index=True,
                        alt="Tramo generado para explorar por ciclo: ciclos y sensores.",
                    )
            if st.button(
                "Evaluar este tramo",
                key="explorar_evaluar",
                type="primary",
                icon=":material/play_arrow:",
                disabled=not st.session_state.get("explorar_ok", False),
            ):
                _tab = st.session_state.get("explorar_table")
                _meta = st.session_state.get("explorar_meta")
                if _tab is not None:
                    try:
                        st.session_state["live_engine_id"] = (
                            f"ESN-EXPLORAR-{_exp_unit}")
                        st.session_state["_editor_value"] = _tab
                        st.session_state["live_result"] = INF.score_table(
                            _tab, engine_id=f"ESN-EXPLORAR-{_exp_unit}")
                        st.session_state["live_meta"] = _meta
                        st.session_state["live_warnings"] = (
                            st.session_state.get("explorar_avisos", []) or [])
                        st.session_state["live_error"] = None
                        st.session_state["live_flash"] = (
                            f"Tramo explorado puntuado (ciclos "
                            f"{_meta['start_cycle']}→{_meta['end_cycle']}).")
                    except ValueError as _exc:
                        st.session_state["live_result"] = None
                        st.session_state["live_error"] = str(_exc)
                    st.rerun()

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
        # ¿Está ya en la flota? Se responde aquí, antes de evaluar, para que la duda
        # «¿esto se ha añadido?» no obligue a bajar hasta la tarjeta de registro.
        try:
            _id_norm = T.normalizar_id(identidad) if id_ok else ""
        except ValueError:
            _id_norm = ""
        _en_flota = bool(_id_norm) and _id_norm in (st.session_state.get("twins") or {})
        if _id_norm:
            st.badge(
                "EN LA FLOTA" if _en_flota else "SIN REGISTRAR",
                icon=":material/check_circle:" if _en_flota else ":material/add_circle:",
                color="green" if _en_flota else "gray",
            )
        st.caption(
            "Paso 1 · trae los datos · Paso 2 · revisa el pre-vuelo de abajo · "
            "Paso 3 · evalúa · Paso 4 · regístralo en la tarjeta que sale bajo el "
            "resultado. El botón de evaluar solo se activa con los pasos 1 y 2 en verde."
        )
        # La plantilla se descarga desde el expander «Qué es cada columna», que ya
        # reutiliza `INF.template_csv()` (cabecera + 50 filas vacías) y ya esta
        # probado. Un segundo boton con la cabecera escrita a mano era un segundo
        # sitio donde arreglar el mismo contrato.

        def _on_preset_change():
            """Actualiza el motor demo al cambiar el preset de ejemplo."""
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
                         icon=":material/menu_book:", expanded=False):
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
                    f"La rejilla va lenta con {L.fmt_miles(state_rows)} filas. Puedes recortar a las "
                    f"primeras {L.fmt_miles(INF.UMBRAL_RECORTE_EDITOR)} para editar con fluidez: "
                    "se puntuará lo visible y el recorte queda a la vista.",
                    icon=":material/speed:",
                )
                if st.button(
                    f"Recortar a {L.fmt_miles(INF.UMBRAL_RECORTE_EDITOR)} primeras filas",
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
                    # P1: valida el tamaño en bytes antes de parsear y acota la
                    # lectura con nrows=MAX_FILAS+1; si hay más filas, preflight
                    # lo rechaza con el mensaje de límite ya existente.
                    _n_bytes = B._size_bytes(upload)
                    if _n_bytes is not None:
                        B._check_bytes(_n_bytes, str(getattr(upload, "name", "CSV")))
                    uploaded_table = pd.read_csv(upload, nrows=INF.MAX_FILAS + 1)
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
            # MIA-3: notificacion n8n, punto de llamada unico. Solo si la
            # decision no es SIN_DECISION, deduplicado por fingerprint en la
            # sesion (cada rerun sin cambio de fingerprint no re-envia).
            # Notifican HANGAR, INSPECCION y APTO (APTO llega a Set log);
            # SIN_DECISION no hace nada. Dedupe solo si el POST fue ok.
            _fp_n8n = str(live["contract"].get("fingerprint") or "")
            _enviadas_n8n = set(st.session_state.get("n8n_enviadas") or set())
            # MIA-3: unidad real para n8n (no -1 de scoring en vivo).
            # live_meta trae `unit` de la caché (ej. 14 en Critico U14 ciclo 29);
            # unidad_simulada=-1 solo evita mezclar EMA y no es la unidad real.
            _meta_n8n = st.session_state.get("live_meta") or {}
            _unidad_real = (
                _meta_n8n.get("unit")
                if isinstance(_meta_n8n, dict) and _meta_n8n.get("unit") is not None
                else live["contract"].get("unidad_simulada")
            )
            if UN.debe_notificar(traza_live["decision"], _fp_n8n, _enviadas_n8n):
                _payload_n8n = UN.payload_desde_traza(
                    _decision, umbrales,
                    str(live["contract"].get("artefacto_sha256") or ""), _fp_n8n,
                    unidad=_unidad_real)
                _res_n8n = N8N.enviar_decision(traza_live["decision"], _payload_n8n)
                st.session_state["n8n_ultimo"] = {
                    "decision": str(traza_live["decision"]),
                    "ok": bool(isinstance(_res_n8n, dict) and _res_n8n.get("ok") is True),
                    "status": (_res_n8n.get("status") if isinstance(_res_n8n, dict) else None),
                    "en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
                if isinstance(_res_n8n, dict) and _res_n8n.get("ok") is True:
                    _enviadas_n8n.add(_fp_n8n)
                    st.session_state["n8n_enviadas"] = _enviadas_n8n
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
                st.metric("SHA-256 del artefacto",
                          str(live["contract"]["artefacto_sha256"])[:12], "reproducibilidad",
                          border=True, icon=":material/fingerprint:", delta_color="off",
                          help="Huella del artefacto congelado que produjo esta "
                               "predicción. El contrato completo está en el expander "
                               "«Contrato y procedencia de esta evaluación».")
                st.metric("Contrato",
                          f"w{live['contract']['window']}/s{live['contract']['step']}",
                          "ventana/step", border=True,
                          icon=":material/description:", delta_color="off",
                          help="Ventana de filas remuestreadas y step usados en esta "
                               "evaluación. Fuera de este contrato la predicción no es "
                               "reproducible.")
            reglas_live = " → ".join(traza_live["usadas"])
            st.markdown(
                f"Con los umbrales en vigor ({threshold_apto:.0f} / {threshold_aog:.0f}): "
                f":{tone}-badge[{L.STATE_LABELS[live_state]}]"
                + (f" · reglas: `{reglas_live}`" if reglas_live else "")
            )
            if traza_live["porque"]:
                st.caption(" · ".join(traza_live["porque"]))
            # El registro va pegado al resultado: es el paso que se busca justo después
            # de evaluar. Antes vivía en un expander plegado al final de la sección.
            gemelos_previos = st.session_state.get("twins", {})
            motor_live = str(live["contract"].get("motor") or "").strip().upper()
            ya_existe = motor_live in gemelos_previos
            reemplazar = False
            with st.container(border=True):
                if ya_existe:
                    previo = gemelos_previos[motor_live]
                    verdad_previa = T.metricas_verdad(previo)
                    st.markdown(
                        f":green-badge[:material/check_circle: EN LA FLOTA] "
                        f"`{motor_live}` · {len(previo['serie'])} ventana(s) guardada(s)"
                        + (f" · RUL real {verdad_previa['rul_real']:.0f} ciclos"
                           if verdad_previa else "")
                    )
                    st.caption(
                        "Puntuar otra ventana del mismo motor no lo sobrescribe solo: "
                        "marca la casilla para sustituir la serie."
                    )
                    reemplazar = st.checkbox(
                        "Reemplazar la serie guardada (la RUL real se conserva)",
                        key="twin_replace",
                        help="Se sustituyen la serie, la huella y el contrato. La RUL real "
                             "es un hecho del motor, no de la ventana: no se borra.",
                    )
                else:
                    st.markdown(
                        f":gray-badge[:material/add_circle: SIN REGISTRAR] "
                        f"`{motor_live}` no está en la flota."
                    )
                    st.caption(
                        "Regístralo para que aparezca en el muro y en «Gemelos "
                        "registrados». Su estado se recalcula con los umbrales en vigor; "
                        "la serie no se vuelve a puntuar."
                    )
                if st.button(
                    f"Reemplazar gemelo `{motor_live}`" if ya_existe else "Registrar en la flota",
                    icon=":material/sync:" if ya_existe else ":material/add_circle:",
                    key="twin_add", type="primary",
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
        with st.expander("Sandbox de estrés · perturba el motor y mira el pipeline reaccionar",
                         icon=":material/tune:", expanded=_vista_tribunal):
            st.caption(
                "El tribunal mueve el deslizador y la app re-puntúa el tramo con el "
                "artefacto congelado y re-decide con el motor oficial. No se reentrena "
                "nada: lo que cambia es la entrada."
            )
            _sandbox_estres(windows, telemetry, units, _cache_sha,
                            _sandbox_puntua_cached, chart_layout, style_axes,
                            st_badge_estado)


        with st.expander("Demo en vivo", icon=":material/movie:", expanded=_vista_tribunal):
            st.caption(
                "Deja la app en el estado desde el que se cuenta la historia: umbrales "
                "30/25, ciclo 29 y la unidad 14, que es la que entra en hangar."
            )
            if st.button("Cargar escenario de demo", icon=":material/play_circle:",
                         key="demo_cargar", type="primary"):
                st.session_state["_demo_pendiente"] = True
                _log("Escenario de demo cargado (umbrales 30/25, ciclo 29, U14).")
                st.rerun()
            with st.expander("Restablecer demo", icon=":material/restart_alt:"):
                st.caption(
                    "Borra la flota registrada —gemelos y registros de hangar— de la "
                    "sesión y del disco. La caché y el artefacto no se tocan."
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


        # ------------------------------------------------------------- SHAP waterfall
        with st.container(border=True):
            st.subheader("Explicabilidad local · SHAP waterfall",
                         icon=":material/psychology:")
            st.caption(
                "Por qué el modelo predice este RUL para el motor seleccionado. "
                "TreeExplainer exacto sobre el LightGBM del híbrido (no reentrena). "
                "El waterfall muestra la contribución de cada feature a la predicción. "
                "El SHAP explica solo la rama árbol (LightGBM), no el BiLSTM, el stacking "
                "ni la EMA causal."
            )
            _wf_unit = int(st.session_state.get("unit", 14))
            shap_panel(_wf_unit, suffix="casos")
    _tab_casos()
