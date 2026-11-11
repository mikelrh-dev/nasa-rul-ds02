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
