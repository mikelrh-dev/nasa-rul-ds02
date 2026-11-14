"""Pestaña Motor: qué le pasa a un motor concreto.

La sala va de lo general a lo concreto: la curva de vida con su banda conformal,
las alarmas y el ciclo en que se disparan, la telemetría física del motor
elegido, el SHAP que explica la predicción y, al final, la orden de trabajo con
su parte en PDF.

Los datos y los helpers llegan en el `AppCtx` que construye
`app/entrypoints/dashboard_ds02.py`; el módulo no importa el dashboard ni
TensorFlow. Procede de la extracción del monolito y no cambia métricas, umbrales
ni cachés.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.lib import flota as F
from app.lib import dashboard_helpers as DH
from app.lib import hangar as HGR
from app.lib import ui_data_loader as L
from app.lib import rules as UR
from src.mia import reglas as R_REGLAS

# Design tokens: dueno `theme.py` (el dashboard tambien los importa de ahi).
from app.lib.theme import (
    CHART_CONFIG, INK, MUTED, MUTED_LINE, GRID, SURFACE, SKY, ROSE, ROSE_SOFT,
)

from app.lib.context import AppCtx

__all__ = ["_tab_motor"]


@st.fragment
def _tab_motor(ctx: AppCtx) -> None:
    """Cuerpo de la pestaña Motor; recibe el contexto de la app."""
    snapshot = ctx.snapshot
    unit = ctx.unit
    etiqueta_unidad = ctx.etiqueta_unidad
    registro = ctx.registro
    telemetry = ctx.telemetry
    order = ctx.order
    registros = ctx.registros
    threshold_apto = ctx.threshold_apto
    threshold_aog = ctx.threshold_aog
    umbrales = ctx.umbrales
    aplicar_reglas = ctx.aplicar_reglas
    curve = ctx.curve
    unit_metrics = ctx.unit_metrics
    alarm_cycle = ctx.alarm_cycle
    truth_cycle = ctx.truth_cycle
    current = ctx.current
    wu = ctx.wu
    coverage = ctx.coverage
    critical_start = ctx.critical_start
    max_life = ctx.max_life
    chart_layout = ctx.chart_layout
    style_axes = ctx.style_axes
    shap_panel = ctx.shap_panel
    fig_deriva = ctx.fig_deriva
    st_badge_estado = ctx.st_badge_estado
    _etiqueta_unidad = etiqueta_unidad
    _registro = registro
    _wu = wu

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
                _gauge, theme=None, config=CHART_CONFIG,
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
                _r9 = R_REGLAS.si_R9_HANGAR({"limite_inferior": float(_lo_g), "alertas_datos": [], "umbrales": {"apto": float(umbrales["apto"]), "hangar": float(umbrales["hangar"])}})
                if _r9:
                    st.caption(f"R9 evaluada: Sí (L_inf {_lo_g:.1f} < {float(umbrales['hangar']):.0f}): dispara y gana")
                else:
                    st.caption(f"R9 evaluada: No (L_inf {_lo_g:.1f} >= {float(umbrales['hangar']):.0f}): evaluada, no dispara")
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
                theme=None, config=CHART_CONFIG,
                alt=f"Radiografía de sensores de {_etiqueta_g}: deriva porcentual de las "
                    "presiones frente a su línea base sana.",
            )
            st.caption(
                "Radiografía de sensores (presiones) respecto a la línea base sana del "
                "propio motor: la señal física bruta, antes de que el modelo la lea."
            )
        # app-ux-bundle-fix: radiografía de temperaturas T24 · T2 · T50.
        _temp_clave = ["T24", "T2", "T50"]
        _per_cycle_t = (
            telemetry[telemetry["unit"] == unit]
            .groupby("cycle", as_index=False)[_temp_clave]
            .mean(numeric_only=True)
        )
        if not _per_cycle_t.empty:
            st.plotly_chart(
                fig_deriva(_per_cycle_t, _temp_clave,
                           int(_per_cycle_t["cycle"].max()),
                           critical_start, threshold_aog, height=220),
                theme=None, config=CHART_CONFIG,
                alt=f"Radiografía de temperaturas T24, T2 y T50 de {_etiqueta_g}: "
                    "deriva porcentual frente a la línea base sana.",
            )
            st.caption(
                "Radiografía de temperaturas T24 (salida LPC) · T2 (entrada del fan) · "
                "T50 (salida LPT): estaciones físicas del dataset N-CMAPSS."
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
                name="Banda 90 %",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=curve["cycle"], y=curve["pred"], mode="lines",
                line=dict(color=SKY, width=3), name="RUL predicha",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=curve["cycle"], y=curve["y_true"], mode="lines",
                line=dict(color=MUTED_LINE, width=1.6, dash="dot"), name="RUL real",
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
            annotation_font_color=ROSE_SOFT,
        )
        fig.add_vline(
            x=current, line_dash="dot", line_color=INK, line_width=1.5,
            annotation_text=f"ciclo {current}", annotation_position="top",
            annotation_font=dict(color=INK, size=11),
        )
        fig.update_layout(**chart_layout(height=430, hovermode="x unified"))
        style_axes(fig, x_title="Ciclo de vuelo", y_title="RUL (ciclos restantes)")
        st.plotly_chart(
            fig, theme=None, config=CHART_CONFIG,
            alt="RUL real y predicha a lo largo de la vida del motor, con la banda conformal y la zona de hangar sombreada.",
        )
        st.download_button(
            "Descargar trayectoria (CSV)",
            data=DH.trayectoria_csv(curve),
            file_name=f"trayectoria_{_etiqueta_g.replace(' ', '_')}.csv",
            mime="text/csv",
            icon=":material/table_view:",
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

    with st.container(border=True):
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

    # ------------------------------------------------------------- SHAP
    with st.container(border=True):
        st.subheader("Explicabilidad · SHAP (LightGBM del híbrido)",
                     icon=":material/psychology:")
        st.caption(
            "Qué features del LightGBM pesan más en la predicción de este motor. "
            "TreeExplainer exacto sobre el modelo congelado (no reentrena). "
            "El SHAP explica el componente tabular del híbrido, no el BiLSTM ni el "
            "stacking."
        )
        shap_panel(int(unit), suffix="motor")
