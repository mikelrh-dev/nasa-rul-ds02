"""DS02 maintenance decision-support surface.

    streamlit run app/dashboard_ds02.py

Four tabs over one cached frame: fleet hangar, RUL with its conformal band,
physical sensor radiography, and the engine-14 audit. Everything is read from
`app/cache/` (see `scripts/build_ui_cache.py`) and `models/ds02_manifest.json`;
the frozen bundle is never loaded, so no TensorFlow import is needed and the app
runs from a laptop without the 2.3 GB HDF5.

The maintenance state is decided by the conformal LOWER bound, not by the point
estimate. Thresholds are ADR-008's 30 / 25 and are adjustable in the sidebar.

Colors, fonts and radii live in `.streamlit/config.toml`; the Plotly figures use
the same tokens so the charts sit on the same surface as the widgets.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ui_data_loader as L  # noqa: E402
import ui_inference as INF  # noqa: E402

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
}
STATE_BG = {
    L.AIRWORTHY: "background-color: rgba(52, 211, 153, 0.14)",
    L.PREVENTIVE: "background-color: rgba(245, 158, 11, 0.14)",
    L.AOG: "background-color: rgba(248, 113, 113, 0.14)",
    L.NO_DATA: "background-color: rgba(100, 116, 139, 0.14)",
}
STATE_WORD = {
    L.AIRWORTHY: "apto",
    L.PREVENTIVE: "inspección",
    L.AOG: "hangar",
    L.NO_DATA: "sin datos",
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
global_metrics = L.global_metrics(windows)
curves = {u: L.unit_curve(windows, u) for u in units}
alarms = {u: L.first_alarm_cycle(curves[u], 25.0) for u in units}

# ------------------------------------------------------------------- sidebar
with st.sidebar:
    st.header("Guardia operativa", icon=":material/radar:")
    unit = st.segmented_control(
        "Unidad de test",
        units,
        default=units[0],
        required=True,
        format_func=lambda u: f"U{int(u)}",
        key="unit",
        help="Motores del conjunto de test DS02 (partición fija [11, 14, 15]).",
    )
    st.caption(L.UNIT_LABELS.get(int(unit), f"Unidad {int(unit)}"))

    cycle = st.slider(
        "Ciclo de vuelo simulado",
        min_value=1,
        max_value=max_life,
        value=1,
        step=1,
        help=(
            "Reloj de flota: se aplica a las tres unidades. Las que terminaron su vida "
            f"registrada se muestran en su último ciclo evaluado (vida máxima: {max_life})."
        ),
    )

    st.subheader("Umbrales de derivación", icon=":material/tune:")
    threshold_apto = st.number_input(
        "Apto si L_inf ≥ (ciclos)", min_value=1.0, max_value=100.0,
        value=float(provenance["defaults"]["threshold_airworthy"]), step=1.0,
        help="Estado verde gobernado por el límite inferior conformal, no por la predicción puntual.",
    )
    threshold_aog = st.number_input(
        "Hangar si L_inf < (ciclos)", min_value=0.0, max_value=99.0,
        value=float(provenance["defaults"]["threshold_aog"]), step=1.0,
        help="Por debajo de este límite inferior la unidad se inmoviliza y se emite orden de trabajo.",
    )
    if threshold_aog >= threshold_apto:
        st.error(
            "El umbral de hangar debe ser estrictamente menor que el de apto.",
            icon=":material/rule:",
        )
        st.stop()

    st.caption(
        f"Caché con {provenance['counts']['windows']:,} ventanas y "
        f"{provenance['counts']['rows']:,} filas de telemetría · "
        f"generada {provenance['generated_at'][:16].replace('T', ' ')}"
    )

    with st.expander("Cómo leer esta pantalla", icon=":material/help:"):
        st.markdown(
            "- **RUL** (*remaining useful life*): ciclos de vuelo que le quedan al motor "
            "según el modelo. Es una estimación, no una medida.\n"
            "- **L_inf**: extremo inferior de la banda conformal al 90 %. Es el número que "
            "gobierna la decisión, no la predicción puntual: equivocarse por pesimismo "
            "cuesta una inspección, por optimismo cuesta un motor.\n"
            "- **Banda 90 %**: intervalo calibrado sobre los motores de desarrollo. Si el "
            "motor se comporta como ellos, su vida real cae dentro 9 de cada 10 veces.\n"
            "- **Estados**: APTO (`L_inf ≥ apto`) · INSPECCIÓN (entre umbrales) · "
            "HANGAR/AOG (`L_inf < hangar`: la unidad no vuela y se emite orden).\n"
            "- **Ciclo de vuelo**: un despegue–aterrizaje. El reloj de la barra lateral "
            "simula el paso del tiempo sobre el conjunto de test congelado.\n"
            "- **Ventana**: las 50 filas remuestreadas que el modelo consume de una vez. "
            "Se puntúa una ventana cada 2 filas, así que un ciclo acumula varias "
            "predicciones.\n"
            "- **Orden de trabajo**: documento JSON/CSV con las unidades bloqueadas, su "
            "banda y la acción de mantenimiento."
        )

    with st.expander("Contrato de artefacto congelado", icon=":material/lock:"):
        shape = manifest.get("model_shape", {})
        conformal = manifest.get("conformal", {}) or {}
        st.caption(
            "Registrado en `models/ds02_manifest.json`. **No** es un cálculo de esta "
            "caché: es el contrato del artefacto que se está consumiendo."
        )
        st.markdown(
            f"**dataset** `{manifest.get('dataset')}` · "
            f"**code_version** `{manifest.get('code_version')}` · "
            f"**seed** `{manifest.get('seed')}`"
        )
        st.markdown(
            f"**test** `{manifest.get('unit_partition', {}).get('test')}` · "
            f"**ventana** `{shape.get('bilstm_input_shape')}` · "
            f"**meta** `{shape.get('meta_features')} features`"
        )
        st.markdown(
            f"**banda** objetivo `{conformal.get('target_coverage')}` · "
            f"*{conformal.get('method')}* · calibración "
            f"`{conformal.get('n_calibration')}` filas"
        )
        recorded = manifest.get("macro_rmse", {}).get("per_unit_rmse", {})
        if recorded:
            st.markdown(
                "**macro-RMSE por motor (registrado)** "
                + " · ".join(f"U{int(float(k))}: `{v:.3f}`" for k, v in recorded.items())
            )
        st.json(
            {
                "artefactos": manifest.get("artifacts", {}),
                "inference_contract": manifest.get("inference_contract", {}),
                "lgb_objective": manifest.get("lgb_objective", {}),
            },
            expanded=False,
        )

snapshot = L.fleet_snapshot(windows, cycle, threshold_apto, threshold_aog)
curve = curves[int(unit)]
per_unit = L.per_unit_metrics(windows)
unit_metrics = per_unit[per_unit["unit"] == unit].iloc[0]
alarm_cycle, truth_cycle = alarms[int(unit)]
current = int(min(cycle, int(curve["cycle"].max())))
coverage = float(
    np.mean((curve["y_true"] >= curve["lower"]) & (curve["y_true"] <= curve["upper"]))
)
critical_mae = L.critical_zone_mae(windows, 25.0)
grounded = int((snapshot["state"] == L.AOG).sum())
critical_start = truth_cycle

# ---------------------------------------------------------------------- header
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
            f"Artefacto {provenance['artifact']['ensemble_sha256'][:8]}",
            icon=":material/lock:", color="gray",
        )
        st.badge(
            f"{global_metrics['windows']:,} ventanas",
            icon=":material/table_rows:", color="blue",
        )
        st.badge(
            f"Banda {provenance['artifact']['conformal_target_coverage']:.0%}",
            icon=":material/verified:", color="green",
        )

tab_fleet, tab_rul, tab_sensors, tab_audit, tab_live = st.tabs(
    [
        ":material/factory: Hangar virtual y estado de flota",
        ":material/monitoring: Telemetría RUL y bandas conformales",
        ":material/thermostat: Radiografía física de sensores",
        ":material/warning: Auditoría: el caso Motor 14",
        ":material/rocket_launch: Evaluar unidad nueva",
    ]
)


# ------------------------------------------------------------------- tab 1
with tab_fleet:
    with st.container(horizontal=True):
        st.metric(
            "Flota monitorizada",
            f"{global_metrics['units']} unidades",
            f"{global_metrics['windows']:,} ventanas evaluadas",
            border=True, icon=":material/groups:", delta_color="off",
        )
        st.metric(
            "MAE en zona crítica",
            f"{critical_mae:.2f} ciclos",
            "RUL real < 25 · calculado de la caché",
            border=True, icon=":material/target:", delta_color="off",
            help="Error absoluto medio donde de verdad se decide el mantenimiento.",
        )
        st.metric(
            "Macro-RMSE",
            f"{global_metrics['macro_rmse']:.2f} ciclos",
            f"ponderado {global_metrics['rmse']:.2f}",
            border=True, icon=":material/balance:", delta_color="off",
            help="El macro-RMSE da el mismo peso a cada motor; el ponderado lo da a cada ventana.",
        )
        st.metric(
            "Unidades en hangar",
            f"{grounded} / {len(snapshot)}",
            f"en el ciclo {cycle}",
            border=True, icon=":material/local_shipping:", delta_color="off",
        )

    with st.container(border=True):
        st.subheader("Cronología de estado de flota", icon=":material/timeline:")
        st.caption(
            "Cada punto es un ciclo evaluado y su color es el estado que dicta el límite "
            "inferior. La línea vertical es el reloj de la simulación."
        )
        ribbon_rows = []
        for u in units:
            frame = curves[u]
            states = L.classify_series(frame["lower"], threshold_apto, threshold_aog)
            ribbon_rows.append(
                pd.DataFrame(
                    {
                        "unidad": f"U{u}",
                        "ciclo": frame["cycle"],
                        "estado": states.to_numpy(),
                        "L_inf": frame["lower"],
                    }
                )
            )
        ribbon = pd.concat(ribbon_rows, ignore_index=True)
        ribbon["color"] = ribbon["estado"].map(STATE_COLORS)
        ribbon["etiqueta"] = ribbon["estado"].map(STATE_WORD)

        fig_fleet = go.Figure(
            go.Scatter(
                x=ribbon["ciclo"],
                y=ribbon["unidad"],
                mode="markers",
                marker=dict(color=ribbon["color"], size=11, symbol="square",
                            line=dict(width=0)),
                customdata=np.column_stack([ribbon["etiqueta"], ribbon["L_inf"]]),
                hovertemplate=(
                    "U%{y} · ciclo %{x}<br>estado: %{customdata[0]}"
                    "<br>L_inf: %{customdata[1]:.1f} ciclos<extra></extra>"
                ),
                name="Estado por ciclo",
            )
        )
        fig_fleet.add_vline(
            x=cycle, line_color=INK, line_width=1.5, line_dash="dot",
            annotation_text=f"ciclo {cycle}", annotation_position="top",
            annotation_font=dict(color=INK, size=11),
        )
        fig_fleet.update_layout(
            **chart_layout(height=240, showlegend=False,
                           hovermode="closest"),
            xaxis_title="Ciclo de vuelo",
            yaxis=dict(
                categoryorder="array", categoryarray=[f"U{u}" for u in reversed(units)],
            ),
        )
        style_axes(fig_fleet)
        st.plotly_chart(
            fig_fleet, theme=None,
            alt="Cronología de estado por unidad: verde apto, ámbar inspección y rojo hangar a lo largo de los ciclos.",
        )

    with st.container(border=True):
        st.subheader("Cola de mantenimiento", icon=":material/assignment:")
        st.caption("Decisión por límite inferior conformal, no por la predicción puntual.")
        display = pd.DataFrame(
            {
                "Motor": [f"U{int(u)}" for u in snapshot["unit"]],
                "Ciclo": snapshot["cycle"],
                "RUL real": snapshot["y_true"],
                "RUL predicha": snapshot["pred"],
                "L_inf (riesgo)": snapshot["lower"],
                "L_sup": snapshot["upper"],
                "Estado": snapshot["state_label"],
                "Acción automática asignada": snapshot["action"],
            }
        )

        def _row_style(row: pd.Series) -> list[str]:
            label = row["Estado"]
            state = next((s for s, name in L.STATE_LABELS.items() if name == label), L.NO_DATA)
            return [STATE_BG[state]] * len(row)

        styled = display.style.apply(_row_style, axis=1)
        st.dataframe(
            styled,
            hide_index=True,
            column_config={
                "Ciclo": st.column_config.NumberColumn("Ciclo", format="%d"),
                "RUL real": st.column_config.NumberColumn("RUL real", format="%.1f"),
                "RUL predicha": st.column_config.NumberColumn("RUL predicha", format="%.1f"),
                "L_inf (riesgo)": st.column_config.NumberColumn(
                    "L_inf (riesgo)", format="%.1f",
                    help="Límite inferior de la banda conformal: es lo que decide el estado.",
                ),
                "L_sup": st.column_config.NumberColumn("L_sup", format="%.1f"),
            },
            alt="Cola de mantenimiento: estado y acción por unidad en el ciclo simulado.",
        )

        clamped = snapshot[snapshot["clamped"]]
        if not clamped.empty:
            st.caption(
                "Limitadas a su último ciclo evaluado: "
                + ", ".join(
                    f"U{int(r.unit)} en {int(r.scored_cycle)}" for r in clamped.itertuples()
                )
                + ". No se extrapola más allá de la vida registrada."
            )

        st.info(
            f"**Apto** si `L_inf ≥ {threshold_apto:.0f}` · "
            f"**inspección** si `{threshold_aog:.0f} ≤ L_inf < {threshold_apto:.0f}` · "
            f"**hangar** si `L_inf < {threshold_aog:.0f}`. El estado se decide con el límite "
            "inferior de la banda: la predicción puntual puede estar por encima del umbral y la "
            "unidad aun así quedar inmovilizada. Es deliberado (ADR-008): el error del modelo no "
            "es simétrico entre motores.",
            title="Regla de negocio",
            icon=":material/shield:",
        )

    order = L.work_order(snapshot, provenance, threshold_apto, threshold_aog)
    blocked = order["unidades"]
    with st.container(border=True):
        st.subheader("Orden de trabajo", icon=":material/description:")
        if blocked:
            st.caption(
                f"{len(blocked)} unidad(es) bloqueada(s) en el ciclo {cycle}. El documento lleva "
                "el hash del artefacto y los umbrales en vigor."
            )
            with st.container(horizontal=True):
                st.download_button(
                    "Descargar orden (JSON)",
                    data=json.dumps(order, ensure_ascii=False, indent=2),
                    file_name=f"orden_mantenimiento_ds02_ciclo{cycle}.json",
                    mime="application/json",
                    type="primary",
                    icon=":material/download:",
                )
                st.download_button(
                    "Descargar orden (CSV)",
                    data=L.work_order_csv(order),
                    file_name=f"orden_mantenimiento_ds02_ciclo{cycle}.csv",
                    mime="text/csv",
                    icon=":material/table_view:",
                )
        else:
            st.success(
                f"Ninguna unidad en hangar en el ciclo {cycle}. No se emite orden de trabajo.",
                title="Flota disponible",
                icon=":material/check_circle:",
            )
            st.button(
                "Descargar orden (JSON)",
                disabled=True,
                icon=":material/download:",
                help="No hay unidades bloqueadas en este ciclo.",
            )


# ------------------------------------------------------------------- tab 2
with tab_rul:
    with st.container(border=True):
        st.subheader("Trayectoria de RUL y banda conformal", icon=":material/ssid_chart:")
        st.caption(
            f"Unidad {int(unit)} · {len(curve)} ciclos evaluados · cobertura realizada "
            f"{coverage:.0%} (objetivo 90 %)."
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
        st.metric("RMSE", f"{unit_metrics['rmse']:.2f}", f"U{int(unit)}", border=True,
                  icon=":material/analytics:", delta_color="off")
        st.metric("MAE", f"{unit_metrics['mae']:.2f}", f"U{int(unit)}", border=True,
                  icon=":material/straighten:", delta_color="off")
        st.metric("Sesgo (pred − real)", f"{unit_metrics['bias']:+.2f}", "ciclos", border=True,
                  icon=":material/swap_vert:", delta_color="off")
        st.metric("Cobertura de banda", f"{coverage * 100:.0f} %", "objetivo 90 %", border=True,
                  icon=":material/verified:", delta_color="off")
        st.metric("Vida registrada", f"{int(unit_metrics['life'])}", "ciclos", border=True,
                  icon=":material/schedule:", delta_color="off")

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


# ------------------------------------------------------------------- tab 3
with tab_sensors:
    group = st.selectbox("Grupo de canales", list(L.CHANNEL_GROUPS), index=0)
    channels = st.multiselect(
        "Canales a dibujar",
        L.CHANNEL_GROUPS[group],
        default=L.CHANNEL_GROUPS[group][:2],
        format_func=lambda c: L.CHANNEL_LABELS.get(c, c),
    )

    # "Condiciones de vuelo" already contains alt/Mach: dedupe before selecting,
    # or the groupby receives duplicate column names.
    needed = list(dict.fromkeys(L.CHANNEL_GROUPS[group] + ["alt", "Mach"]))
    per_cycle = (
        telemetry[telemetry["unit"] == unit]
        .groupby("cycle", as_index=False)[needed]
        .mean(numeric_only=True)
    )
    last_cycle = int(per_cycle["cycle"].max())

    left, right = st.columns(2)
    with left:
        with st.container(border=True, height="stretch"):
            st.subheader("Condiciones operativas", icon=":material/air:")
            ops = [c for c in ("alt", "Mach", "TRA", "T2") if c in per_cycle.columns]
            fig_a = make_subplots(
                rows=len(ops), cols=1, shared_xaxes=True, vertical_spacing=0.07
            )
            for i, ch in enumerate(ops, start=1):
                fig_a.add_trace(
                    go.Scatter(
                        x=per_cycle["cycle"], y=per_cycle[ch], mode="lines",
                        name=L.CHANNEL_LABELS.get(ch, ch), line=dict(width=1.8, color=SKY),
                    ),
                    row=i, col=1,
                )
                fig_a.update_yaxes(title_text=ch, row=i, col=1)
            fig_a.update_layout(**chart_layout(height=360, showlegend=False,
                                               hovermode="x unified"))
            style_axes(fig_a, x_title="Ciclo de vuelo")
            st.plotly_chart(
                fig_a, theme=None,
                alt="Altitud, Mach, acelerador y T2 a lo largo de los ciclos del motor seleccionado.",
            )
            st.caption(
                "El régimen de vuelo es lo que el residualizador descarta antes de que el "
                "modelo lea los sensores."
            )

    with right:
        with st.container(border=True, height="stretch"):
            st.subheader("Deriva física respecto al motor sano", icon=":material/monitor_heart:")
            if not channels:
                st.info(
                    "Selecciona al menos un canal para dibujar la deriva.",
                    icon=":material/touch_app:",
                )
            else:
                baseline_cycles = 5
                baseline = per_cycle.head(baseline_cycles)[channels].mean()
                drift = (per_cycle[channels] / baseline - 1.0) * 100.0
                fig_b = go.Figure()
                for ch in channels:
                    fig_b.add_trace(
                        go.Scatter(
                            x=per_cycle["cycle"], y=drift[ch], mode="lines",
                            name=L.CHANNEL_LABELS.get(ch, ch), line=dict(width=2),
                        )
                    )
                fig_b.add_hline(y=0, line_color=MUTED, line_width=1)
                if critical_start is not None:
                    fig_b.add_vrect(
                        x0=critical_start, x1=last_cycle, fillcolor=ROSE, opacity=0.12,
                        line_width=0,
                        annotation_text=f"RUL real < {threshold_aog:.0f}",
                        annotation_position="top right", annotation_font_size=11,
                        annotation_font_color="#fca5a5",
                    )
                fig_b.update_layout(**chart_layout(height=360, hovermode="x unified"))
                style_axes(
                    fig_b,
                    x_title="Ciclo de vuelo",
                    y_title="variación % vs. media de los 5 primeros ciclos",
                )
                st.plotly_chart(
                    fig_b, theme=None,
                    alt="Deriva porcentual de los sensores seleccionados frente a la línea base sana del propio motor.",
                )
                st.caption(
                    f"Media por ciclo frente a la línea base sana del propio motor (U{unit}, "
                    f"primeros {baseline_cycles} ciclos). No es la residualización del modelo: "
                    "es la señal física bruta, para poder discutirla."
                )

    st.caption(
        "Nomenclatura tomada del propio HDF5 (`X_s_var`, `W_var`): "
        + ", ".join(
            L.CHANNEL_LABELS[c].split(" · ")[0]
            for c in (
                L.CHANNEL_GROUPS["Temperaturas"]
                + L.CHANNEL_GROUPS["Presiones"]
                + L.CHANNEL_GROUPS["Velocidades de rotor"]
                + L.CHANNEL_GROUPS["Combustible"]
            )
        )
        + ". Nada de etiquetas `s1…s21`, que son de FD001."
    )


# ------------------------------------------------------------------- tab 4
with tab_audit:
    st.subheader(
        "El motor 14 concentra el error y también la evidencia",
        icon=":material/insights:",
    )

    with st.container(border=True):
        bars = go.Figure()
        bars.add_trace(
            go.Bar(
                x=[f"U{int(u)}" for u in per_unit["unit"]], y=per_unit["rmse"],
                name="RMSE",
                marker_color=[ROSE if int(u) == 14 else SKY for u in per_unit["unit"]],
                text=[f"{v:.2f}" for v in per_unit["rmse"]],
                textposition="outside", textfont=dict(color=INK),
            )
        )
        bars.add_trace(
            go.Bar(
                x=[f"U{int(u)}" for u in per_unit["unit"]], y=per_unit["mae"],
                name="MAE",
                marker_color=[("#fca5a5" if int(u) == 14 else "#7dd3fc") for u in per_unit["unit"]],
                text=[f"{v:.2f}" for v in per_unit["mae"]],
                textposition="outside", textfont=dict(color=INK),
            )
        )
        bars.update_layout(**chart_layout(height=340, barmode="group", hovermode="closest"))
        style_axes(bars, y_title="ciclos")
        st.plotly_chart(
            bars, theme=None,
            alt="RMSE y MAE por unidad; el motor 14 concentra el error con 760 ventanas.",
        )
        st.caption("Calculado de la caché, no de una tabla fija. Rojo = motor 14.")

    u14 = per_unit[per_unit["unit"] == 14].iloc[0]
    u14_prov = provenance["counts"]["units"]["14"]
    fit_density = provenance["counts"]["fit_engine_rows_per_cycle"]

    card_a, card_b, card_c = st.columns(3, border=True)
    with card_a:
        st.markdown("**Complejidad física**")
        st.markdown(
            f"Régimen compuesto: degradación simultánea más agresiva. Medido, no supuesto: "
            f"RMSE **{u14['rmse']:.2f}** y sesgo **{u14['bias']:+.2f}** ciclos sobre "
            f"**{int(u14['windows'])}** ventanas."
        )
        st.caption(
            "El sesgo es negativo: el modelo se queda corto. Es el error caro, porque "
            "sobreestimar vida es lo que la NASA penaliza más."
        )
    with card_b:
        st.markdown("**Densidad de muestreo — medida y descartada**")
        st.markdown(
            f"U14 trae **{u14_prov['rows_per_cycle']:.1f} filas/ciclo** frente a "
            f"**{fit_density:.1f}** de media en los motores de ajuste "
            f"({u14_prov['density_vs_fit']:.2f}×). La hipótesis se probó re-ventaneando dos "
            "motores a esa misma densidad, con todo lo demás fijo."
        )
        st.caption(
            "`INFORME_p0_p1_prior_de_vida.md`: el sesgo del meta cambió −0.93 / −0.03 / "
            "+0.34 ciclos. La densidad no explica el error; se reporta como hipótesis refutada."
        )
    with card_c:
        st.markdown("**Prior de vida y mitigación conformal**")
        st.markdown(
            "El sesgo en vida alta es ≈ **−0,87 ciclos por ciclo de vida** del motor: el "
            "conjunto implementa, sin declararlo, `RUL ≈ 63 − ciclo` (63 = vida del motor 16, "
            "el del *early stopping* y el ajuste del meta)."
        )
        st.caption(
            "La mitigación no es otro meta: es decidir con el límite inferior. La alarma llega "
            "antes en U14 precisamente porque su sesgo es el peor."
        )

    band_col, lead_col = st.columns([1, 1])
    with band_col:
        with st.container(border=True, height="stretch"):
            st.subheader("Precisión por tramo de vida", icon=":material/steps:")
            band_df = L.mae_by_band(windows)
            populated = band_df[band_df["windows"] > 0]
            band_fig = go.Figure(
                go.Bar(
                    x=populated["band"], y=populated["mae"],
                    marker_color=[GREEN if b.startswith("[0") else "#475569" for b in populated["band"]],
                    text=[f"{v:.2f}" for v in populated["mae"]],
                    textposition="outside", textfont=dict(color=INK),
                )
            )
            band_fig.update_layout(**chart_layout(height=300, hovermode="closest"))
            style_axes(band_fig, x_title="tramo de RUL real", y_title="MAE (ciclos)")
            st.plotly_chart(
                band_fig, theme=None,
                alt="MAE por tramo de RUL real: mínimo en el tramo crítico 0-25 y máximo en vida alta.",
            )
            st.dataframe(
                populated.assign(Tramo=populated["band"]),
                hide_index=True,
                column_config={
                    "Tramo": st.column_config.TextColumn("Tramo"),
                    "windows": st.column_config.NumberColumn("Ventanas", format="%d"),
                    "mae": st.column_config.NumberColumn("MAE", format="%.3f"),
                    "bias": st.column_config.NumberColumn("Sesgo", format="%+.3f"),
                },
                alt="MAE y sesgo por tramo de RUL real.",
            )
            if len(populated) < len(band_df):
                st.caption(
                    "Ningún motor de test supera los 75 ciclos de RUL real, así que el tramo "
                    "más alto no tiene filas: no se dibuja una barra vacía ni se inventa un valor."
                )

    with lead_col:
        with st.container(border=True, height="stretch"):
            st.subheader("Alarma vs. verdad", icon=":material/av_timer:")
            rows = []
            for u in units:
                a, t = L.first_alarm_cycle(curves[u], threshold_aog)
                rows.append({
                    "Motor": f"U{u}",
                    "Alarma": a,
                    "RUL real < umbral": t,
                    "Adelanto": (t - a) if (a is not None and t is not None) else None,
                    "RUL real al alarmar": (
                        float(curves[u].loc[curves[u]["cycle"] == a, "y_true"].iloc[0])
                        if a is not None else None
                    ),
                })
            st.dataframe(
                pd.DataFrame(rows),
                hide_index=True,
                column_config={
                    "Motor": st.column_config.TextColumn("Motor"),
                    "Alarma": st.column_config.NumberColumn("Ciclo de alarma", format="%d"),
                    "RUL real < umbral": st.column_config.NumberColumn(
                        "Ciclo con RUL real < umbral", format="%d"
                    ),
                    "Adelanto": st.column_config.NumberColumn(
                        "Adelanto (ciclos)", format="%d"
                    ),
                    "RUL real al alarmar": st.column_config.NumberColumn(
                        "RUL real al alarmar", format="%.1f"
                    ),
                },
                alt="Ciclo de alarma frente al ciclo en que la RUL real cruza el umbral, por unidad.",
            )
            st.caption(
                "El adelanto es el coste en disponibilidad de una cota conservadora: la flota "
                f"se inmoviliza antes de que la RUL real llegue a {threshold_aog:.0f}. Es "
                "ajustable desde la barra lateral."
            )

    with st.container(border=True):
        st.subheader("Contrato congelado vs. cálculo en vivo", icon=":material/difference:")
        recorded = manifest.get("macro_rmse", {}).get("per_unit_rmse", {})
        compare = pd.DataFrame(
            {
                "Motor": [f"U{int(u)}" for u in per_unit["unit"]],
                "En vivo (caché)": per_unit["rmse"].to_numpy(),
                "Registrado (manifest)": [
                    float(recorded.get(str(float(u)), np.nan)) for u in per_unit["unit"]
                ],
            }
        )
        compare["Δ"] = compare["En vivo (caché)"] - compare["Registrado (manifest)"]
        st.dataframe(
            compare,
            hide_index=True,
            column_config={
                "Motor": st.column_config.TextColumn("Motor"),
                "En vivo (caché)": st.column_config.NumberColumn(
                    "RMSE en vivo (caché)", format="%.4f"
                ),
                "Registrado (manifest)": st.column_config.NumberColumn(
                    "RMSE registrado (manifest)", format="%.4f"
                ),
                "Δ": st.column_config.NumberColumn("Δ", format="%+.4f"),
            },
            alt="Comparación entre el RMSE recalculado de la caché y el registrado en el manifiesto.",
        )
        st.caption(
            "Ambas columnas describen las mismas ventanas. Una diferencia distinta de cero "
            "sería deriva de regeneración del artefacto, y se publica tal cual: no se ajusta "
            "ninguna de las dos. El score NASA es una **suma** asimétrica sobre las mismas "
            "6 196 ventanas y no aplica el recorte de 125 ciclos del camino FD001."
        )



# ------------------------------------------------------------------- tab 5
with tab_live:
    st.subheader("Puntúa un motor con datos que aportes tú", icon=":material/science:")
    st.caption(
        "Las tres rutas desembocan en el mismo validador y en la misma llamada al "
        "artefacto congelado. Una ventana son **50 filas remuestreadas** (1 de cada 100 "
        "registros), no 50 lecturas seguidas ni 50 ciclos. Teclear 900 celdas no es "
        "viable: usa el ejemplo, pega un bloque desde Excel o sube el CSV."
    )

    mode = st.segmented_control(
        "Entrada de datos",
        ["Ejemplo del test set", "Editar tabla (pegar)", "Subir CSV"],
        default="Ejemplo del test set",
        key="live_mode",
        help="El ejemplo usa una ventana real de la caché; las otras dos aceptan tus datos.",
    )

    example_table, example_meta = INF.example_window(14, 0.55)
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
                     icon=":material/menu_book:"):
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
            "accidente: la ventana toma 1 de cada 100 registros, así que varias filas "
            "comparten ciclo y 50 filas cubren pocos vuelos."
        )
        st.download_button(
            "Descargar plantilla CSV (50 filas vacías)",
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
                f"`{example_meta['source']}`."
            )
            st.dataframe(
                example_table,
                hide_index=True,
                height=260,
                column_config=number_columns,
                alt="Ventana de ejemplo: 50 filas de telemetría remuestreada listas para puntuar.",
            )
        with st.form("live_eval_example"):
            submitted = st.form_submit_button(
                "Evaluar unidad", type="primary", icon=":material/play_arrow:"
            )
        if submitted:
            table_to_score = example_table
    elif mode == "Editar tabla (pegar)":
        with st.form("live_eval_editor"):
            edited = st.data_editor(
                example_table,
                num_rows="dynamic",
                hide_index=True,
                height=420,
                key="live_editor",
                column_config=number_columns,
            )
            state_rows = len(edited)
            state_windows = max(0, state_rows - INF.window_size() + 1)
            st.caption(
                f"**{state_rows} filas** → {state_windows} ventana(s). Pega el bloque "
                "desde Excel/Sheets sobre la primera celda: la rejilla acepta una "
                "matriz de 50×19, y con más filas puntúa todas las ventanas "
                "deslizantes. Las columnas y su orden deben ser los del dataset; no "
                "cambies los encabezados."
            )
            if state_rows < INF.window_size():
                st.caption(
                    f"Faltan {INF.window_size() - state_rows} filas para llegar al "
                    "mínimo del contrato.",
                    icon=":material/info:",
                )
            submitted = st.form_submit_button(
                "Evaluar unidad", type="primary", icon=":material/play_arrow:"
            )
        if submitted:
            table_to_score = edited
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
                uploaded_table = pd.read_csv(upload)
            except Exception as exc:  # noqa: BLE001 - the message is shown to the user
                st.error(f"No se pudo leer el CSV: {exc}", icon=":material/error:")
            if uploaded_table is not None:
                st.caption(
                    f"{len(uploaded_table)} filas y {len(uploaded_table.columns)} columnas."
                )
                with st.form("live_eval_csv"):
                    submitted = st.form_submit_button(
                        "Evaluar unidad", type="primary", icon=":material/play_arrow:"
                    )
                if submitted:
                    table_to_score = uploaded_table
                    data_meta = {"source": upload.name}

    if submitted and table_to_score is not None:
        try:
            st.session_state["live_result"] = INF.score_table(table_to_score)
            st.session_state["live_meta"] = data_meta
            st.session_state["live_warnings"] = INF.plausibility_warnings(table_to_score)
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
        live_state = L.classify(float(last["lower"]), threshold_apto, threshold_aog)
        tone = (
            "green" if live_state == L.AIRWORTHY
            else "orange" if live_state == L.PREVENTIVE
            else "red"
        )
        with st.container(horizontal=True):
            st.metric("RUL estimada", f"{last['pred']:.1f}", "ciclos", border=True,
                      icon=":material/speed:", delta_color="off")
            st.metric("Límite inferior", f"{last['lower']:.1f}", "decide el estado",
                      border=True, icon=":material/trending_down:", delta_color="off")
            st.metric("Límite superior", f"{last['upper']:.1f}", "banda 90 %",
                      border=True, icon=":material/trending_up:", delta_color="off")
            st.metric("Ventanas puntuadas", f"{live['contract']['ventanas']}",
                      f"{live['contract']['filas']} filas", border=True,
                      icon=":material/layers:", delta_color="off")
        st.markdown(
            f"Con los umbrales en vigor ({threshold_apto:.0f} / {threshold_aog:.0f}): "
            f":{tone}-badge[{L.STATE_LABELS[live_state]}]"
        )

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
                f"sha256 `{contract['artefacto_sha256'][:16]}…`"
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
                "Las 50 filas son la rejilla remuestreada (1 de cada 100 registros del "
                "dataset), no 50 lecturas de 1 Hz. Con otro muestreo la predicción queda "
                "fuera de contrato aunque los números sean válidos."
            )

        st.caption(
            "**Sin ground truth**: esta unidad no trae RUL real, así que no se declara "
            "RMSE ni MAE. La banda es una cota conservadora calibrada sobre los motores "
            "de desarrollo; el sesgo de vida alta (`RUL ≈ 63 − ciclo`) también aplica aquí."
        )

        if live_state == L.AOG:
            order_live = INF.live_work_order(
                live, st.session_state.get("live_meta"), threshold_apto, threshold_aog
            )
            st.download_button(
                "Descargar orden de esta unidad (JSON)",
                data=json.dumps(order_live, ensure_ascii=False, indent=2),
                file_name="orden_mantenimiento_unidad_externa.json",
                mime="application/json",
                icon=":material/download:",
                type="primary",
            )
