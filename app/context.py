"""Contexto compartido de la app.

Antes cada pestana recibia entre 18 y 29 parametros y, si faltaba uno, lo
buscaba en `dashboard_ds02` con `sys.modules`. Ahora el dashboard construye
un `AppCtx` una sola vez y las pestanas leen de ahi. Los campos con prefijo
`_` en el dashboard se exponen sin prefijo (`etiqueta_unidad`, `registro`,
`sha256_cached`, ...).

Este modulo no importa Streamlit ni el dashboard: solo transporta valores.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class AppCtx:
    # ---------------------------------------------------------------- datos
    frame: Any = None
    frame_cache: Any = None
    snapshot: Any = None
    curves: Any = None
    telemetry: Any = None
    windows: Any = None
    provenance: Any = None
    manifest: Any = None
    units: Any = None
    per_unit: Any = None
    unit_metrics: Any = None
    global_metrics: Any = None
    critical_mae: Any = None
    alarm_cycle: Any = None
    truth_cycle: Any = None
    current: Any = None
    wu: Any = None
    coverage: Any = None
    critical_start: Any = None
    max_life: Any = None
    curve: Any = None
    alarms: Any = None

    # ------------------------------------------------- estado y seleccion
    unit: Any = None
    cycle: Any = None
    umbrales: Any = None
    preset: Any = None
    presets: Any = None
    preset_vals: Any = None
    threshold_apto: Any = None
    threshold_aog: Any = None
    aplicar_reglas: Any = None
    banda_en_uso: Any = None
    correccion_en_uso: Any = None
    correccion: Any = None
    order: Any = None
    registros: Any = None
    unidades_vistas: Any = None
    gemelos: Any = None
    tarjetas_cache: Any = None
    tarjetas_gemelos: Any = None
    vista_tribunal: Any = None

    # ------------------------------------------------------- helpers de UI
    etiqueta_unidad: Any = None
    registro: Any = None
    slug_motor: Any = None
    guardar_registros: Any = None
    chart_layout: Any = None
    style_axes: Any = None
    fig_deriva: Any = None
    shap_panel: Any = None
    st_badge_estado: Any = None
    sha256_cached: Any = None
    informe_pdf_cached: Any = None
    log: Any = None
    preflight_panel: Any = None
    sandbox_puntua_cached: Any = None
    cache_sha: Any = None


# Campos cuyo nombre en `dashboard_ds02` lleva prefijo o mayusculas.
_DASHBOARD_NAMES = {
    "etiqueta_unidad": "_etiqueta_unidad",
    "registro": "_registro",
    "slug_motor": "_slug_motor",
    "guardar_registros": "_guardar_registros",
    "sha256_cached": "_sha256_cached",
    "informe_pdf_cached": "_informe_pdf_cached",
    "log": "_log",
    "preflight_panel": "_preflight_panel",
    "sandbox_puntua_cached": "_sandbox_puntua_cached",
    "cache_sha": "_cache_sha",
    "presets": "_PRESETS",
    "preset_vals": "_preset_vals",
    "vista_tribunal": "_vista_tribunal",
}


def ctx_from_dashboard() -> AppCtx:
    """Reconstruye el contexto leyendo el dashboard ya cargado.

    Solo se usa cuando una pestana se invoca sin `ctx` (tests o uso suelto).
    """
    import sys

    dash = (sys.modules.get("dashboard_ds02")
            or sys.modules.get("app.dashboard_ds02")
            or sys.modules.get("__main__"))
    if dash is None:  # pragma: no cover - defensivo
        try:
            import dashboard_ds02 as dash  # type: ignore
        except ImportError:
            from app import dashboard_ds02 as dash  # type: ignore

    valores = {}
    for campo in AppCtx.__dataclass_fields__:
        nombre = _DASHBOARD_NAMES.get(campo, campo)
        valores[campo] = getattr(dash, nombre, None)
    return AppCtx(**valores)
