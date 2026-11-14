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

# ---------------------------------------------------------------- channel identity
# Medido en `app/cache/ds02_rows.parquet`: P15 y P21 tienen correlacion 1.000 en las
# tres unidades test (maxima diferencia absoluta 0.25 psia) y Ps30/P40 igual. Se
# muestran como una sola traza para no repetir informacion.
CANALES_DUPLICADOS: dict[str, str] = {"P21": "P15", "P40": "Ps30"}

# Un color por codigo de canal, compartido por la vista por ciclo y la alineada: la
# misma serie debe poder seguirse sin volver a leer la leyenda.
COLOR_CANAL: dict[str, str] = {
    "T2": "#a78bfa",
    "T24": SKY,
    "T30": SKY_SOFT,
    "T48": "#fb923c",
    "T50": AMBER,
    "P15": GREEN,
    "P2": "#2dd4bf",
    "P24": SLATE,
    "Ps30": "#f472b6",
    "P50": "#c084fc",
    "Nf": "#4ade80",
    "Nc": "#a3e635",
    "Wf": "#e879f9",
    "alt": MUTED,
    "Mach": "#fbbf24",
    "TRA": "#cbd5e1",
}


def canales_unicos(channels: list[str]) -> tuple[list[str], dict[str, str]]:
    """Colapsa los canales duplicados y devuelve (bases en orden, etiquetas).

    La etiqueta acumula los codigos fusionados: ["P15", "P21"] sale como una sola
    traza llamada "P15 · P21", igual si la entrada va al reves.
    """
    orden: list[str] = []
    etiquetas: dict[str, str] = {}
    for canal in channels:
        base = CANALES_DUPLICADOS.get(canal, canal)
        if base not in etiquetas:
            orden.append(base)
            etiquetas[base] = base
        if canal != base:
            etiquetas[base] = f"{etiquetas[base]} \u00b7 {canal}"
    return orden, etiquetas

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

# Margenes base: con 8 px Plotly dibujaba ticks y titulos fuera del viewport del
# SVG y el texto quedaba recortado. El margen inferior debe ademas dejar sitio
# para la leyenda, que cuelga bajo el titulo del eje X.
_MARGEN_L, _MARGEN_R, _MARGEN_T, _MARGEN_B = 56, 16, 44, 120
# Lo que la leyenda inferior deja libre bajo el area de trazado: ticks (~20 px),
# salto, titulo del eje X (~18 px) y holgura. Medido en DOM vivo.
_LEYENDA_DESPEJE_PX = 65.0


def chart_layout(**overrides) -> dict:
    """Shared Plotly layout: transparent surface, themed axes, legend below."""
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color=INK, size=13),
        margin=dict(l=_MARGEN_L, r=_MARGEN_R, t=_MARGEN_T, b=_MARGEN_B),
        # Sin automargin en ningun eje: `automargin` reserva sitio para la leyenda
        # encogiendo el area de trazado, y como la posicion de la leyenda es una
        # fraccion de esa altura, el despeje se retroalimentaba y volvia a chocar
        # con el titulo del eje X. Con margenes explicitos el alto del area de
        # trazado es exactamente height - t - b.
        xaxis=dict(automargin=False),
        yaxis=dict(automargin=False),
        hoverlabel=dict(bgcolor=SURFACE, bordercolor=GRID, font=dict(color=INK)),
        legend=dict(
            orientation="h", yanchor="top", y=-0.16, x=0,
            bgcolor="rgba(0,0,0,0)", font=dict(color=MUTED, size=12),
        ),
        hovermode="x unified",
    )
    layout.update(overrides)

    # La leyenda cuelga bajo el titulo del eje X. Su `y` es una fraccion de la
    # altura del area de trazado, asi que se recalcula con los margenes y la
    # altura DEFINITIVOS: algunos graficos sobreescriben `margin` y `height`.
    if "legend" not in overrides:
        margen = layout["margin"]
        altura = layout.get("height")
        if isinstance(altura, (int, float)) and altura > 0:
            alto_plot = max(float(altura) - margen["t"] - margen["b"], 40.0)
            layout["legend"]["y"] = round(-_LEYENDA_DESPEJE_PX / alto_plot, 3)
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
    fig = go.Figure()
    canales_base, etiquetas = canales_unicos(
        [c for c in channels if c in per_cycle.columns]
    )
    if not canales_base:
        return fig
    baseline_cycles = 5
    baseline = per_cycle.head(baseline_cycles)[canales_base].mean()
    drift = (per_cycle[canales_base] / baseline - 1.0) * 100.0
    for ch in canales_base:
        fig.add_trace(
            go.Scatter(
                x=per_cycle["cycle"], y=drift[ch], mode="lines",
                # Solo el codigo en la leyenda: con las descripciones largas
                # el pressures chart envolvia 5 filas y el propio Plotly
                # encogia el area de trazado para hacerles sitio.
                name=etiquetas[ch], line=dict(width=2, color=COLOR_CANAL.get(ch, MUTED_LINE)),
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
    # Mas aire arriba: con la leyenda larga el area de trazado se encoge y el
    # titulo Y rotado necesita margen para no salirse del SVG.
    fig.update_layout(**chart_layout(
        height=height, hovermode="x unified",
        margin=dict(l=_MARGEN_L, r=_MARGEN_R, t=72, b=_MARGEN_B),
    ))
    style_axes(
        fig, x_title="Ciclo de vuelo",
        y_title="% vs. baseline (5 ciclos)",
    )
    return fig


def fig_deriva_vida(frame: pd.DataFrame, resumen: pd.DataFrame,
                    channels: list[str], threshold_aog: float,
                    height: int = 280) -> go.Figure:
    """Deriva media por tramo de RUL real, agregada sobre las unidades de la cache.

    La x va en RUL real invertido (vida alta a la izquierda, fallo a la derecha) para
    que la zona critica quede donde termina la vida del motor.
    """
    fig = go.Figure()
    if frame is None or frame.empty or resumen is None or resumen.empty:
        return fig
    canales_base, etiquetas = canales_unicos(
        [c for c in channels if c in frame["canal"].unique()]
    )
    if not canales_base:
        return fig
    sub = frame[frame["canal"].isin(canales_base)]
    destacados = set(resumen.index[resumen["resaltar"]]) \
        if "resaltar" in resumen.columns else set()
    for canal in canales_base:
        serie = (
            sub[sub["canal"] == canal]
            .groupby("rul_centro", as_index=False)["deriva"].mean()
            .sort_values("rul_centro")
        )
        if serie.empty:
            continue
        es_destacado = canal in destacados
        fig.add_trace(go.Scatter(
            x=serie["rul_centro"], y=serie["deriva"], mode="lines",
            name=etiquetas[canal],
            line=dict(width=2.5 if es_destacado else 1.2,
                      color=COLOR_CANAL.get(canal, MUTED_LINE)),
        ))
    fig.add_hline(y=0, line_color=MUTED, line_width=1)
    fig.add_vrect(
        x0=0, x1=threshold_aog, fillcolor=ROSE, opacity=0.12, line_width=0,
        annotation_text=f"RUL real < {threshold_aog:.0f}",
        annotation_position="top right", annotation_font_size=11,
        annotation_font_color=ROSE_SOFT,
    )
    # Mismo margen superior amplio que la vista por ciclo: el titulo Y rotado es
    # largo y con 44 px se sale del viewport del SVG.
    fig.update_layout(**chart_layout(
        height=height, hovermode="x unified",
        margin=dict(l=_MARGEN_L, r=_MARGEN_R, t=72, b=_MARGEN_B),
    ))
    style_axes(fig, x_title="RUL real (ciclos)",
               y_title="% vs. baseline (5 ciclos)")
    fig.update_xaxes(autorange="reversed")
    return fig


def caption_deriva_vida(resumen: pd.DataFrame, channels: list[str] | None = None) -> str:
    """Frase del caption con las cifras medidas; ningun numero va escrito a mano."""
    metodo = ("Método: valor del ciclo dividido por la media de los 5 primeros ciclos "
              "del propio motor, menos 1, en %. Fuente: app/cache (ds02_rows y "
              "ds02_windows).")
    if resumen is None or resumen.empty:
        return ("Deriva media de las unidades test alineada por RUL real. " + metodo)
    if channels:
        bases, _ = canales_unicos(list(channels))
        vista = resumen.loc[resumen.index.intersection(bases)]
    else:
        vista = resumen
    if vista.empty:
        return "No hay datos para estos canales. " + metodo
    destacados = vista.index[vista["resaltar"]].tolist()
    criterio = "(|corr con el RUL| >= 0,3 y salto >= 0,5 ppt)"
    if not destacados:
        mayor = float(vista["salto"].abs().max())
        if "monotono" in vista.columns and len(vista):
            forma = ("la forma es monótona" if bool(vista["monotono"].all())
                     else "la forma no es monótona")
        else:
            forma = "la forma no es monótona"
        return (f"Deriva media de las unidades test alineada por RUL real. Ninguno de "
                f"estos canales supera el criterio de deriva {criterio}: el mayor cambio "
                f"entre tramos es de {mayor:.1f} ppt y {forma}. " + metodo)
    cifras = ", ".join(
        f"{canal} {vista.loc[canal, 'salto']:+.2f} ppt" for canal in destacados
    )
    return (f"Deriva media de las unidades test alineada por RUL real. Solo {cifras} "
            f"supera el criterio de deriva {criterio}; el resto queda por debajo. "
            + metodo)
