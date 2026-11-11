"""DS02 maintenance decision-support surface.

    streamlit run app/dashboard_ds02.py

Five tabs over one cached frame: fleet hangar, RUL with its conformal band,
physical sensor radiography, the engine-14 audit, and the live evaluation of a
unit you bring. Everything is read from `app/cache/` (see
`scripts/build/build_ui_cache.py`) and `models/ds02_manifest.json`; the frozen bundle is
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

# Design tokens y helpers de Plotly: dueno `theme.py`.
from theme import (  # noqa: E402
    INK, MUTED, GRID, SURFACE, SKY, AMBER, GREEN, ROSE, SLATE,
    STATE_COLORS, STATE_BG, STATE_WORD, RANGO_ESTADO,
    BADGE_COLOR, BADGE_ICON, chart_layout, style_axes, fig_deriva,
)


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


# Casos nuevos (B1): dueno `ui_modulos._tab_casos`; el dashboard solo
# construye el contexto y lo pasa.
try:
    from ui_modulos._tab_casos import _tab_casos as _tab_casos_impl
except ImportError:  # pragma: no cover - import-style fallback
    from app.ui_modulos._tab_casos import _tab_casos as _tab_casos_impl  # type: ignore[no-redef]

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
        "`python scripts/build/build_ui_cache.py`.",
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
# Barra lateral (B3): dueno `ui_modulos._sidebar`; devuelve el estado.
try:
    from ui_modulos._sidebar import _sidebar
except ImportError:  # pragma: no cover - import-style fallback
    from app.ui_modulos._sidebar import _sidebar  # type: ignore

_sb = _sidebar(
    windows=windows, provenance=provenance, units=units, max_life=max_life,
    altas_fn=_altas, etiqueta_unidad=_etiqueta_unidad, registro=_registro,
    guardar_registros=_guardar_registros, log=_log,
)
unit = _sb.unit


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

# Contexto unico de la app: las pestanas reciben un objeto en vez de 18-29
# parametros. Se construye una sola vez, tras calcular todos los globales.
from context import AppCtx  # noqa: E402

ctx = AppCtx(
    frame=frame, frame_cache=frame_cache, snapshot=snapshot, curves=curves,
    telemetry=telemetry, windows=windows, provenance=provenance,
    manifest=manifest, units=units, per_unit=per_unit,
    unit_metrics=unit_metrics, global_metrics=global_metrics,
    critical_mae=critical_mae, alarm_cycle=alarm_cycle,
    truth_cycle=truth_cycle, current=current, wu=_wu, coverage=coverage,
    critical_start=critical_start, max_life=max_life, curve=curve,
    alarms=alarms, unit=unit, cycle=cycle, umbrales=umbrales, preset=preset,
    presets=_PRESETS, preset_vals=_preset_vals, threshold_apto=threshold_apto,
    threshold_aog=threshold_aog, aplicar_reglas=aplicar_reglas,
    banda_en_uso=banda_en_uso, correccion_en_uso=correccion_en_uso,
    correccion=correccion, order=order, registros=registros,
    unidades_vistas=unidades_vistas, gemelos=gemelos,
    tarjetas_cache=tarjetas_cache, tarjetas_gemelos=tarjetas_gemelos,
    vista_tribunal=_vista_tribunal, etiqueta_unidad=_etiqueta_unidad,
    registro=_registro, slug_motor=_slug_motor,
    guardar_registros=_guardar_registros, chart_layout=chart_layout,
    style_axes=style_axes, fig_deriva=fig_deriva, shap_panel=shap_panel,
    st_badge_estado=st_badge_estado, sha256_cached=_sha256_cached,
    informe_pdf_cached=_informe_pdf_cached, log=_log,
    preflight_panel=_preflight_panel,
    sandbox_puntua_cached=_sandbox_puntua_cached, cache_sha=_cache_sha,
)

tab_flota, tab_motor, tab_casos, tab_auditoria = st.tabs(
    [
        ":material/factory: Flota · qué pasa hoy",
        ":material/precision_manufacturing: Motor · qué le pasa a este",
        ":material/library_add: Casos nuevos · trae un motor",
        ":material/science: Auditoría · cómo se calculó",
    ]
)


with tab_flota:
    _tab_flota_impl(ctx)

with tab_motor:
    _tab_motor_impl(ctx)

with tab_auditoria:
    _tab_auditoria_impl(ctx)

with tab_casos:
    _tab_casos_impl(ctx)
