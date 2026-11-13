"""DS02 maintenance decision-support surface.

    streamlit run app/entrypoints/dashboard_ds02.py

Four tabs over one cached frame: the fleet hangar, one engine in detail (RUL
with its conformal band, alarms, physics and SHAP), the engines you bring, and
the audit of how it was all computed. Everything is read from `app/cache/` (see
`scripts/build/build_ui_cache.py`) and `models/ds02_manifest.json`; the frozen bundle is
never loaded, so no TensorFlow import is needed and the app runs from a laptop
without the 2.3 GB HDF5.

Both rule passes run through `src/mia/`: the correction pass (R2b + R6) behind the
opt-in toggle, and the decision pass (R1, R9, R8, R7) on every render.The maintenance state is therefore the engine's answer, decided on the conformal
LOWER bound and not on the point estimate. Thresholds are ADR-013's 25 / 20 and
are adjustable in the sidebar.

Colors, fonts and radii live in `.streamlit/config.toml`; the Plotly figures use
the same tokens so the charts sit on the same surface as the widgets.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# Bootstrap de paquete: este entrypoint vive en app/entrypoints/, asi que
# parents[2] es la raiz del repo. Es el UNICO sys.path.insert de app/ y el
# unico `__file__` admitido: sirve solo para poder importar `app`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app import _paths  # noqa: E402

# El ROOT que usa la app sale de `_paths`, no de la aritmetica de `__file__`.
ROOT = _paths.ROOT

from app.lib import flota as F  # noqa: E402
from app.lib import hangar as HGR  # noqa: E402
from app.lib import alta as A  # noqa: E402
from app.lib import ui_data_loader as L  # noqa: E402
from app.lib import rules as UR  # noqa: E402
from app.lib.informe_auditoria import _informe_pdf_cached  # noqa: E402
from app.lib.sandbox import _sandbox_puntua_cached  # noqa: E402
from app.ui import _sha256_cached  # noqa: E402
from app.ui._paneles import (  # noqa: E402
    preflight_panel, shap_panel,
    tarjetas_cache as _tarjetas_cache_fn,
    tarjetas_gemelos as _tarjetas_gemelos_fn,
)

# Estado de sesión en un solo sitio: gemelos y registros de hangar.
# Se cargan de disco una sola vez: recargar la página ya no borra la flota.
# Cada sesión tiene su fichero en `registros_sesiones/`; los huérfanos se
# conservan (no hay borrado automático). El legacy `registros_flota.json` se
# copia una vez por sesión y no se mueve ni se toca después.
_LEGACY_PATH = str(_paths.REGISTROS_PATH)
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


# Design tokens y helpers de Plotly: dueno `theme.py`.
from app.lib.theme import (  # noqa: E402
    BADGE_COLOR, BADGE_ICON, chart_layout, style_axes, fig_deriva,
)


def st_badge_estado(estado: str) -> None:
    """Insignia de estado con color e icono: el color nunca viaja solo."""
    st.badge(
        L.STATE_LABELS.get(estado, str(estado)),
        icon=BADGE_ICON.get(estado, ":material/circle:"),
        color=BADGE_COLOR.get(estado, "gray"),
    )


# Helper único de SHA-256: dueño `app.lib.ui_data_loader` (único `def` en `app/`);
# re-exportado desde `app.ui` e importado arriba para compat. Digest y
# `OSError -> None` intactos.

# Flota (PR3, dashboard-split-monolito 2.2): dueño
# `app.ui._tab_flota`; aquí se delega desde el wrapper `_tab_flota`.
# La caché de marco (`frame_cache`, ttl=3600) sigue aquí; los paneles y el
# PDF viven en `app/ui/` y `app/lib/`.
from app.ui._tab_flota import _tab_flota as _tab_flota_impl

# Motor (PR4, dashboard-split-monolito 2.3): dueno
# `app.ui._tab_motor`; aqui se delega desde el wrapper `_tab_motor`.
# La caché de marco (`frame_cache`, ttl=3600) sigue aquí; los paneles y el
# PDF viven en `app/ui/` y `app/lib/`.
from app.ui._tab_motor import _tab_motor as _tab_motor_impl

# Auditoria (PR5, dashboard-split-monolito 2.4): dueno
# `app.ui._tab_auditoria`; aqui se delega desde el wrapper
# `_tab_auditoria`. La caché de marco (`frame_cache`, ttl=3600) sigue aquí;
# el informe PDF vive en `app/lib/informe_auditoria.py`.
from app.ui._tab_auditoria import _tab_auditoria as _tab_auditoria_impl


# Casos nuevos (B1): dueno `app.ui._tab_casos`; el dashboard solo
# construye el contexto y lo pasa.
from app.ui._tab_casos import _tab_casos as _tab_casos_impl

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

# ------------------------------------------------------- escrituras diferidas
# Un handler no puede escribir en la clave de un widget que ya se instanció:
# Streamlit lo prohíbe (`StreamlitWidgetAlreadyInstantiatedError`) y la app
# revienta en pantalla. La solución es dejar una bandera y aplicarla aquí, antes
# de crear los widgets: en la siguiente pasada el widget nace con el valor ya en
# `session_state`. Sin esto, «Incorporar unidad» y «Cargar escenario de demo»
# rompían la app aunque su lógica fuera correcta.
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
    "Conservador (+10)": (10.0, 10.0),
}
preset = str(st.session_state.get("preset", "Normal"))
_base_apto = float(provenance["defaults"]["threshold_airworthy"])
_base_aog = float(provenance["defaults"]["threshold_aog"])
_d_apto, _d_aog = _PRESETS.get(preset, _PRESETS["Normal"])
_preset_vals = (max(1.0, _base_apto + _d_apto), max(0.0, _base_aog + _d_aog))
# Sincroniza spinbuttons con el preset al cambiar: Streamlit ignora `value=`
# si la clave ya existe y la historia deja valores persistentes (20/15).
# Al cambiar se sobrescriben las claves del preset vigente con `_preset_vals`
# para que Prudente→Normal restaure 25/20. Ediciones manuales del mismo
# preset se descartan por diseño (D3).
_prev_preset = st.session_state.get("_preset_prev")
if _prev_preset is not None and _prev_preset != preset:
    st.session_state[f"th_apto_{preset}"] = float(_preset_vals[0])
    st.session_state[f"th_aog_{preset}"] = float(_preset_vals[1])
st.session_state["_preset_prev"] = preset
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
# Barra lateral (B3): dueno `app.ui._sidebar`; devuelve el estado.
from app.ui._sidebar import _sidebar

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


tarjetas_gemelos = _tarjetas_gemelos_fn(
    gemelos, unidades_vistas, umbrales, _altas, _slug_motor)
derivados_gemelos = sum(1 for t in tarjetas_gemelos if t["estado"] == L.AOG)

tarjetas_cache = _tarjetas_cache_fn(
    snapshot, curves, unidades_vistas, cycle, _etiqueta_unidad, _slug_motor)
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

# P1.4 · La inferencia del sandbox cacheada vive en `app/lib/sandbox.py`
# (`_sandbox_puntua_cached`): el entrypoint la importa y la pasa por `AppCtx`.

# El informe de auditoría en PDF vive en `app/lib/informe_auditoria.py`
# (`_informe_auditoria_pdf` + `_informe_pdf_cached`): el entrypoint importa el
# constructor cacheado y lo pasa por `AppCtx`.

# La vista la escribe el widget de la barra lateral; aquí solo se lee. Turno
# esconde en Flota el material de demo y de auditoría.
_vista_tribunal = str(st.session_state.get("vista_modo", "Tribunal")) == "Tribunal"

# Contexto unico de la app: las pestanas reciben un objeto en vez de 18-29
# parametros. Se construye una sola vez, tras calcular todos los globales.
from app.lib.context import AppCtx  # noqa: E402

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
    preflight_panel=preflight_panel,
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
