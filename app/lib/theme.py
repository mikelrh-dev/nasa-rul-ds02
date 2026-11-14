"""Design tokens y helpers de Plotly de la app.

Extraido de `dashboard_ds02.py` (bloque "design tokens"). Solo presentacion:
ninguna funcion entrena ni cambia metricas. El dueno de `CHANNEL_LABELS` sigue
siendo `ui_data_loader`.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

from app.lib import ui_data_loader as L

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
# Tonos suaves: series secundarias y anotaciones, no estados.
ROSE_SOFT = "#fca5a5"
SKY_SOFT = "#7dd3fc"
SLATE_DARK = "#475569"
MUTED_LINE = "#94a3b8"

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


# Chrome comun de todos los graficos del dashboard. Sin modebar flotante: se
# superponia a la esquina superior derecha y no aporta nada en una superficie
# de solo lectura.
CHART_CONFIG: dict = {"displayModeBar": False}


def chart_layout(**overrides) -> dict:
    """Shared Plotly layout: transparent surface, themed axes, legend below."""
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=INK, size=13),
        # Margenes con aire para ticks y titulos: con 8 px Plotly los dibujaba
        # fuera del viewport del SVG y el texto quedaba recortado.
        margin=dict(l=56, r=16, t=44, b=64),
        xaxis=dict(automargin=True),
        yaxis=dict(automargin=True),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=GRID, font=dict(color=INK)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.16, x=0,
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
            annotation_font_color=ROSE_SOFT,
        )
    fig.update_layout(**chart_layout(height=height, hovermode="x unified"))
    style_axes(
        fig, x_title="Ciclo de vuelo",
        y_title="% vs. baseline (5 ciclos)",
    )
    return fig
