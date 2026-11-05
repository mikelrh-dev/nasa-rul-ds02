"""Pestaña Motor extraída de `dashboard_ds02` (dashboard-split-monolito, PR4 task 2.3).

Pure structural move: the body of `_tab_motor` is byte-identical to the
pre-split dashboard version except for the parameter list and the
dashboard-globals resolution below. No behavior, metric or threshold change.

Dashboard-owned globals (`snapshot`/`unit`/`curves`/`telemetry`/`order`/
`registros`/`unidades_vistas`/thresholds/`umbrales`/`aplicar_reglas`/
`curve`/`per_unit`/`unit_metrics`/`alarm_cycle`/`truth_cycle`/`current`/
`_wu`/`coverage`/`critical_start`/`max_life` and the helpers
`_etiqueta_unidad`/`_registro`/`chart_layout`/`style_axes`/`shap_panel`/
`fig_deriva`/`st_badge_estado`) are passed by the dashboard, which keeps the
module-level `windows`/`telemetry`/`frame_cache` hot path (ttl=3600,
corregir+decidir) byte-identical. The fallback import of `dashboard_ds02`
is lazy, inside the fragment, and only fills in what a standalone caller
omitted (never at import time, so there is no circular import, and no
TensorFlow import: every import here is pandas/plotly + the rules layer
via `ui_*`/`flota`/`hangar`).

`frame_cache` (ttl=3600), the ola-2 SHAP cache and the PDF
`artefacto_sha256` signature are untouched: this module only reads the
already-decided data it is handed, exactly as the inline fragment did.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    import flota as F  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import flota as F  # type: ignore[no-redef]

try:
    import hangar as HGR  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import hangar as HGR  # type: ignore[no-redef]

try:
    import ui_data_loader as L  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import ui_data_loader as L  # type: ignore[no-redef]

try:
    import ui_rules as UR  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import ui_rules as UR  # type: ignore[no-redef]

# Design tokens: same hex values as `dashboard_ds02` (see its design-tokens
# section). Kept as literals here so this module needs no dashboard import
# for colors; chart/badge helpers are still dashboard-owned (passed in).
INK = "#e8eef7"
MUTED = "#93a4bd"
GRID = "#22304a"
SURFACE = "#141d2e"
SKY = "#38bdf8"
ROSE = "#f87171"

__all__ = ["_tab_motor"]


@st.fragment
def _tab_motor(snapshot=None, unit=None, etiqueta_unidad=None, registro=None,
               curves=None, telemetry=None, order=None, registros=None,
               unidades_vistas=None, threshold_apto=None, threshold_aog=None,
               umbrales=None, aplicar_reglas=None, curve=None, per_unit=None,
               unit_metrics=None, alarm_cycle=None, truth_cycle=None,
               current=None, wu=None, coverage=None, critical_start=None,
               max_life=None, chart_layout=None, style_axes=None,
               shap_panel=None, fig_deriva=None, st_badge_estado=None) -> None:
    if (snapshot is None or unit is None or etiqueta_unidad is None
            or registro is None or curves is None or telemetry is None
            or order is None or registros is None or unidades_vistas is None
            or threshold_apto is None or threshold_aog is None
            or umbrales is None or aplicar_reglas is None or curve is None
            or per_unit is None or unit_metrics is None
            or alarm_cycle is None or truth_cycle is None
            or current is None or wu is None or coverage is None
            or critical_start is None or max_life is None
            or chart_layout is None or style_axes is None
            or shap_panel is None or fig_deriva is None
            or st_badge_estado is None):
        # Fallback import (PR4): dashboard_ds02 owns the frame/snapshot/curve
        # globals, the per-unit metrics (coverage/curve/alarm_cycle/...),
        # the threshold/rule state and the chart/SHAP helpers. Lazy, inside
        # the fragment, to avoid a circular top-level import: the dashboard
        # imports this module, so this module must not import the dashboard
        # at import time. `unit_metrics`/`alarm_cycle`/`truth_cycle`/
        # `critical_start` are deliberately also filled from the dashboard:
        # None is their legitimate value there too (e.g. a unit without
        # metrics), so filling is a no-op in that state, not a behavior
        # change.
        import sys as _sys
        _dash = _sys.modules.get("dashboard_ds02") or _sys.modules.get("app.dashboard_ds02")
        _main = _sys.modules.get("__main__")
        if _dash is None and _main is not None and hasattr(_main, "snapshot"):
            _dash = _main
        if _dash is None:
            try:
                import dashboard_ds02 as _dash  # type: ignore
            except ImportError:  # pragma: no cover - import-style fallback
                from app import dashboard_ds02 as _dash  # type: ignore
        if snapshot is None:
            snapshot = _dash.snapshot
        if unit is None:
            unit = _dash.unit
        if etiqueta_unidad is None:
            etiqueta_unidad = _dash._etiqueta_unidad
        if registro is None:
            registro = _dash._registro
        if curves is None:
            curves = _dash.curves
        if telemetry is None:
            telemetry = _dash.telemetry
        if order is None:
            order = _dash.order
        if registros is None:
            registros = _dash.registros
        if unidades_vistas is None:
            unidades_vistas = _dash.unidades_vistas
        if threshold_apto is None:
            threshold_apto = _dash.threshold_apto
        if threshold_aog is None:
            threshold_aog = _dash.threshold_aog
        if umbrales is None:
            umbrales = _dash.umbrales
        if aplicar_reglas is None:
            aplicar_reglas = _dash.aplicar_reglas
        if curve is None:
            curve = _dash.curve
        if per_unit is None:
            per_unit = _dash.per_unit
        if unit_metrics is None:
            unit_metrics = _dash.unit_metrics
        if alarm_cycle is None:
            alarm_cycle = _dash.alarm_cycle
        if truth_cycle is None:
            truth_cycle = _dash.truth_cycle
        if current is None:
            current = _dash.current
        if wu is None:
            wu = _dash._wu
        if coverage is None:
            coverage = _dash.coverage
        if critical_start is None:
            critical_start = _dash.critical_start
        if max_life is None:
            max_life = _dash.max_life
        if chart_layout is None:
            chart_layout = _dash.chart_layout
        if style_axes is None:
            style_axes = _dash.style_axes
        if shap_panel is None:
            shap_panel = _dash.shap_panel
        if fig_deriva is None:
            fig_deriva = _dash.fig_deriva
        if st_badge_estado is None:
            st_badge_estado = _dash.st_badge_estado
    _etiqueta_unidad = etiqueta_unidad
    _registro = registro
    _wu = wu
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
                "propio motor: la señal física bruta, antes de que el modelo la lea."
            )
            with st.expander("Mapa de calor · degradación sensorial (z-score)",
                             expanded=False):
                st.caption(
                    "z-score por canal sobre la historia completa del motor: "
                    "rojo = por encima de su media histórica, azul = por debajo. "
                    "Colapsado por defecto para no saturar la vista."
                )
                _sensor_cols = [c for g in L.CHANNEL_GROUPS.values() for c in g]
                _sensor_cols = list(dict.fromkeys(_sensor_cols))
                _tel_u = telemetry[telemetry["unit"] == unit]
                if not _tel_u.empty and all(c in _tel_u.columns for c in _sensor_cols):
                    _heat = _tel_u.groupby("cycle", as_index=False)[_sensor_cols].mean(
                        numeric_only=True)
                    _mat = _heat[_sensor_cols].astype(float)
                    _z = (_mat - _mat.mean(axis=0)) / _mat.std(axis=0).replace(0, 1)
                    import plotly.express as px
                    _fig_heat = px.imshow(
                        _z.T,
                        x=_heat["cycle"].astype(str).tolist(),
                        y=_sensor_cols,
                        color_continuous_scale="RdBu_r",
                        aspect="auto",
                        labels={"x": "ciclo", "y": "sensor", "color": "z"},
                    )
                    _fig_heat.update_layout(
                        height=360, margin=dict(l=10, r=10, t=10, b=10))
                    st.plotly_chart(_fig_heat, theme=None,
                                    alt=f"Mapa de calor z-score de los sensores "
                                        f"del motor {unit} a lo largo de su vida.")

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

    # -------------------- perfil de vuelo: alt vs Mach (canales reales)
    # Vive aquí y no en «Casos nuevos»: dibuja el motor seleccionado en la barra
    # lateral, así que es una vista del motor, no una forma de traer casos.
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
