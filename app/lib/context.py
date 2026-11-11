"""Contexto compartido de la app.

Antes cada pestana recibia entre 18 y 29 parametros y, si faltaba uno, lo
buscaba en `dashboard_ds02` con `sys.modules`. Ahora el dashboard construye
un `AppCtx` una sola vez y las pestanas leen de ahi. Los campos con prefijo
`_` en el dashboard se exponen sin prefijo (`etiqueta_unidad`, `registro`,
`sha256_cached`, ...).

Los campos de datos y de estado van tipados para que se lea que transportan;
los helpers de UI se quedan en `Any` porque son callables de firmas distintas
y el contexto solo los pasa de largo. `pandas` se importa solo para tipos.

Este modulo no importa Streamlit ni el dashboard: solo transporta valores.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - solo para el chequeo de tipos
    import pandas as pd


@dataclass
class AppCtx:
    # ---------------------------------------------------------------- datos
    frame: pd.DataFrame | None = None
    frame_cache: pd.DataFrame | None = None
    snapshot: pd.DataFrame | None = None
    curves: dict[int, pd.DataFrame] | None = None
    telemetry: pd.DataFrame | None = None
    windows: pd.DataFrame | None = None
    provenance: dict[str, Any] | None = None
    manifest: dict[str, Any] | None = None
    units: list[int] | None = None
    per_unit: pd.DataFrame | None = None
    unit_metrics: pd.Series | None = None
    global_metrics: dict[str, Any] | None = None
    critical_mae: float | None = None
    alarm_cycle: int | None = None
    truth_cycle: int | None = None
    current: int | None = None
    wu: pd.DataFrame | None = None
    coverage: float | None = None
    critical_start: int | None = None
    max_life: int | None = None
    curve: pd.DataFrame | None = None
    alarms: dict[int, tuple[int | None, int | None]] | None = None

    # ------------------------------------------------- estado y seleccion
    unit: int | None = None
    cycle: int | None = None
    umbrales: dict[str, float] | None = None
    preset: str | None = None
    presets: dict[str, tuple[float, float]] | None = None
    preset_vals: tuple[float, float] | None = None
    threshold_apto: float | None = None
    threshold_aog: float | None = None
    aplicar_reglas: bool | None = None
    banda_en_uso: str | None = None
    correccion_en_uso: str | None = None
    correccion: dict[str, Any] | None = None
    order: dict[str, Any] | None = None
    registros: dict[str, Any] | None = None
    unidades_vistas: list[int] | None = None
    gemelos: dict[str, Any] | None = None
    tarjetas_cache: list[dict[str, Any]] | None = None
    tarjetas_gemelos: list[dict[str, Any]] | None = None
    vista_tribunal: bool | None = None

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
