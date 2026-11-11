"""Pestaña Flota extraída de `dashboard_ds02` (dashboard-split-monolito, PR3 task 2.2).

Pure structural move: the body of `_tab_flota` (including the nested
`_muro_del_hangar` fragment and `_panel_gemelo`) is byte-identical to the
pre-split dashboard version except for the parameter list and the
dashboard-globals resolution below. No behavior, metric or threshold change.

Dashboard-owned globals (`frame`/`frame_cache`/`snapshot`/`curves`/
`unidades_vistas`/`tarjetas_*`/`gemelos`/`registros`/`order`/`correccion`/
`windows`/`provenance`/`unit`/`cycle`/thresholds/`umbrales`/preset state/
`banda_en_uso`/`correccion_en_uso`/`_vista_tribunal` and the helpers
`_etiqueta_unidad`/`_registro`/`_slug_motor`/`_guardar_registros`/
`chart_layout`/`style_axes`) are passed by the dashboard, which keeps the
module-level `windows`/`telemetry`/`frame_cache` hot path (ttl=3600,
corregir+decidir) byte-identical. The fallback import of `dashboard_ds02`
is lazy, inside the fragment, and only fills in what a standalone caller
omitted (never at import time, so there is no circular import, and no
TensorFlow import: every import here is pandas/numpy/plotly + the rules
layer via `ui_*`/`flota`/`hangar`/`twin`/`simulacion`/`pdf_partes`).

`frame_cache` (ttl=3600), the ola-2 SHAP cache and the PDF
`artefacto_sha256` signature are untouched: this module only reads the
already-decided `frame_cache`/`frame` it is handed, exactly as the inline
fragment did.
"""
from __future__ import annotations

import json

import numpy as np
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
    import dashboard_helpers as DH  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import dashboard_helpers as DH  # type: ignore[no-redef]

try:
    import pdf_partes as PP  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import pdf_partes as PP  # type: ignore[no-redef]

try:
    import simulacion as S  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import simulacion as S  # type: ignore[no-redef]

try:
    import twin as T  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import twin as T  # type: ignore[no-redef]

try:
    import ui_data_loader as L  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import ui_data_loader as L  # type: ignore[no-redef]

try:
    import ui_inference as INF  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import ui_inference as INF  # type: ignore[no-redef]

try:
    import ui_rules as UR  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import ui_rules as UR  # type: ignore[no-redef]

try:
    import ui_alta as A  # noqa: E402
except ImportError:  # pragma: no cover
    from app import ui_alta as A  # type: ignore[no-redef]

# Design tokens: dueno `theme.py` (el dashboard tambien los importa de ahi).
# Aliases con prefijo para conservar los nombres historicos del modulo.
try:  # noqa: E402
    from theme import (  # noqa: E402
        INK, SKY, ROSE,
        SLATE as _SLATE, GREEN as _GREEN, AMBER as _AMBER,
        STATE_COLORS, STATE_BG, STATE_WORD, RANGO_ESTADO,
        BADGE_COLOR, BADGE_ICON,
    )
except ImportError:  # pragma: no cover - import-style fallback
    from app.theme import (  # type: ignore[no-redef]
        INK, SKY, ROSE,
        SLATE as _SLATE, GREEN as _GREEN, AMBER as _AMBER,
        STATE_COLORS, STATE_BG, STATE_WORD, RANGO_ESTADO,
        BADGE_COLOR, BADGE_ICON,
    )

__all__ = ["_tab_flota"]


def _rerun_app() -> None:
    """Callback full-scope: este fragmento re-ejecuta con argumentos congelados
    de `dashboard:1142-1156`, asi que un `st.rerun()` local dejaria banda y
    triaje stale. `scope="app"` re-ejecuta el dashboard y recalcula banda.
    No se quita el `@st.fragment` (romperia la paginacion del muro).
    """
    st.rerun(scope="app")


@st.fragment
def _tab_flota(ctx=None) -> None:
    """Cuerpo de la pestaña Flota; recibe el contexto de la app."""
    if ctx is None:
        try:
            from context import ctx_from_dashboard
        except ImportError:
            from app.context import ctx_from_dashboard
        ctx = ctx_from_dashboard()
    frame = ctx.frame
    frame_cache = ctx.frame_cache
    snapshot = ctx.snapshot
    curves = ctx.curves
    unidades_vistas = ctx.unidades_vistas
    tarjetas_cache = ctx.tarjetas_cache
    tarjetas_gemelos = ctx.tarjetas_gemelos
    gemelos = ctx.gemelos
    registros = ctx.registros
    order = ctx.order
    correccion = ctx.correccion
    windows = ctx.windows
    provenance = ctx.provenance
    unit = ctx.unit
    cycle = ctx.cycle
    threshold_apto = ctx.threshold_apto
    threshold_aog = ctx.threshold_aog
    umbrales = ctx.umbrales
    preset = ctx.preset
    presets = ctx.presets
    preset_vals = ctx.preset_vals
    banda_en_uso = ctx.banda_en_uso
    correccion_en_uso = ctx.correccion_en_uso
    vista_tribunal = ctx.vista_tribunal
    etiqueta_unidad = ctx.etiqueta_unidad
    registro = ctx.registro
    slug_motor = ctx.slug_motor
    guardar_registros = ctx.guardar_registros
    chart_layout = ctx.chart_layout
    style_axes = ctx.style_axes
    _PRESETS = presets
    _preset_vals = preset_vals
    _vista_tribunal = vista_tribunal
    _etiqueta_unidad = etiqueta_unidad
    _registro = registro
    _slug_motor = slug_motor
    _guardar_registros = guardar_registros

    with st.container(border=True):
        st.subheader("Muro del hangar", icon=":material/grid_view:")
        st.caption(
            "Una tarjeta por motor, con la sparkline de su límite inferior. El color y el "
            "estado los dicta `L_inf`; pulsa «Ver gemelo» para abrir su ficha completa. "
            "La flota de la caché y los motores registrados en esta sesión comparten muro."
        )

        @st.fragment
        def _muro_del_hangar() -> None:
            orden = st.pills(
                "Orden del muro",
                ["Por urgencia", "Por unidad"],
                default="Por urgencia",
                key="muro_orden",
                help="Por urgencia adelanta las unidades en hangar; por unidad respeta "
                     "el orden de la caché y deja los motores registrados al final.",
            )
            tarjetas = tarjetas_cache + tarjetas_gemelos
            if orden == "Por unidad":
                tarjetas = sorted(tarjetas, key=lambda t: t["orden_unidad"])
            else:
                tarjetas = sorted(
                    tarjetas,
                    key=lambda t: (RANGO_ESTADO.get(t["estado"], 9), t["orden_unidad"]),
                )
            columnas = st.columns(3)
            for i, tarjeta in enumerate(tarjetas):
                etiqueta = tarjeta["etiqueta"]
                estado = tarjeta["estado"]
                curva = tarjeta["curva"]
                _pred = "—" if pd.isna(tarjeta["pred"]) else f"{tarjeta['pred']:.1f}"
                _lo = "—" if pd.isna(tarjeta["lower"]) else f"{tarjeta['lower']:.1f}"
                with columnas[i % 3]:
                    with st.container(border=True):
                        st.markdown(f"**{etiqueta}**")
                        st.badge(
                            L.STATE_LABELS.get(estado, str(estado)),
                            icon=BADGE_ICON.get(estado, ":material/circle:"),
                            color=BADGE_COLOR.get(estado, "gray"),
                        )
                        st.metric("L_inf (decide)", _lo, "ciclos",
                                  border=True, delta_color="off",
                                  icon=":material/trending_down:")
                        # app-ux-bundle-fix: sparkline del muro (serie L_inf del motor).
                        if "cycle" in curva.columns and "lower" in curva.columns:
                            _sp = curva.sort_values("cycle")
                            st.plotly_chart(
                                go.Figure(go.Scatter(
                                    x=_sp["cycle"], y=_sp["lower"],
                                    mode="lines",
                                    line=dict(width=1.5),
                                    showlegend=False, hoverinfo="skip",
                                    name="L_inf",
                                )).update_layout(
                                    height=60, margin=dict(l=0, r=0, t=0, b=0),
                                    xaxis=dict(visible=False),
                                    yaxis=dict(visible=False),
                                    paper_bgcolor="rgba(0,0,0,0)",
                                    plot_bgcolor="rgba(0,0,0,0)",
                                ),
                                theme=None,
                                alt=f"Sparkline de L_inf de {etiqueta} a lo largo de los ciclos.",
                            )
                        if pd.isna(tarjeta["lower"]):
                            _primer_ciclo_u = int(curva["cycle"].min())
                            st.caption(
                                f"Sin telemetría en este ciclo: esta unidad vuela desde "
                                f"el ciclo {_primer_ciclo_u}. Avanza el reloj de flota o "
                                f"incorpórala con ese ciclo."
                            )
                        if st.button(
                            "Ver gemelo", key=tarjeta["clave_boton"],
                            icon=":material/visibility:", type="secondary",
                        ):
                            if tarjeta["gemelo"]:
                                # Un gemelo no tiene ficha en la pestaña del motor: su
                                # registro es la tabla de debajo. Decirlo es mejor que
                                # prometer una ficha que no existe.
                                st.session_state["_gemelo_pendiente"] = tarjeta["gemelo"]
                                st.session_state["_toast_pendiente"] = (
                                    f"{etiqueta}: su estado se recalcula con los umbrales "
                                    "en vigor en «Gemelos registrados», bajo el muro."
                                )
                            else:
                                # app-ux-bundle-fix: «Ver gemelo» apunta al tab Motor
                                # con `selected_unit`; el dashboard lo consume con
                                # escritura diferida (clave `unit` del sidebar).
                                st.session_state["selected_unit"] = int(tarjeta["unidad"])
                                st.session_state["_ver_gemelo_pendiente"] = int(tarjeta["unidad"])
                                st.session_state["_escenario_pendiente"] = (
                                    tarjeta["unidad"], tarjeta["ciclo_tarjeta"])
                                st.session_state["_toast_pendiente"] = (
                                    f"{etiqueta} seleccionada (selected_unit="
                                    f"{int(tarjeta['unidad'])}). Abre su ficha en la "
                                    "pestaña «Motor · qué le pasa a este»."
                                )
                            st.rerun()

        _muro_del_hangar()

    with st.expander("Cronología de estado de flota", icon=":material/timeline:",
                     expanded=False):
        st.caption(
            "**Leyenda:** ● verde → Apto · ■ naranja → Inspección · ✕ rojo → Hangar. "
            "Solo `L_inf` (límite inferior de la banda) decide el color; la línea "
            "vertical punteada es el reloj de flota."
        )
        ribbon_rows = []
        por_ciclo = UR.estado_por_ciclo(frame)
        for u in unidades_vistas:
            curva = curves[u]
            sub = por_ciclo[por_ciclo["unit"] == u].sort_values("cycle")
            ribbon_rows.append(
                pd.DataFrame(
                    {
                        "unidad": _etiqueta_unidad(float(u)),
                        "ciclo": curva["cycle"],
                        "estado": sub["decision"].to_numpy(),
                        "L_inf": curva["lower"],
                    }
                )
            )
        ribbon = pd.concat(ribbon_rows, ignore_index=True)
        ribbon["color"] = ribbon["estado"].map(STATE_COLORS)
        ribbon["etiqueta"] = ribbon["estado"].map(STATE_WORD)
        ribbon["simbolo"] = ribbon["estado"].map(L.STATE_SYMBOLS).fillna("circle")

        fig_fleet = go.Figure(
            go.Scatter(
                x=ribbon["ciclo"],
                y=ribbon["unidad"],
                mode="markers",                            marker=dict(color=ribbon["color"], size=11, symbol=ribbon["simbolo"],
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
                categoryorder="array", categoryarray=[_etiqueta_unidad(float(u)) for u in reversed(unidades_vistas)],
            ),
        )
        style_axes(fig_fleet)
        st.plotly_chart(
            fig_fleet, theme=None,
            alt="Cronología de estado por unidad: verde apto, ámbar inspección y rojo hangar a lo largo de los ciclos.",
        )

    # -------------------- sala 3: el taller (¿qué pasa si cambio la política?)
    with st.container(border=True):
        st.subheader("El taller · qué pasa si cambio la política",
                     icon=":material/tune:")
        _taller_a, _taller_b = st.columns([2, 1])
        with _taller_a:
            st.selectbox(
                "Preset de umbrales",
                list(_PRESETS),
                key="preset",
                on_change=_rerun_app,
                help="Rellena los dos umbrales de abajo. Después puedes ajustarlos a mano.",
            )
            with st.container(horizontal=True):
                st.number_input(
                    "Apto si L_inf ≥ (ciclos)", min_value=1.0, max_value=100.0,
                    value=_preset_vals[0], step=1.0, key=f"th_apto_{preset}",
                    on_change=_rerun_app,
                    help="Estado verde gobernado por el límite inferior conformal, no "
                         "por la predicción puntual.",
                )
                st.number_input(
                    "Hangar si L_inf < (ciclos)", min_value=0.0, max_value=99.0,
                    value=_preset_vals[1], step=1.0, key=f"th_aog_{preset}",
                    on_change=_rerun_app,
                    help="Por debajo de este límite inferior la unidad se inmoviliza y "
                         "se emite orden de trabajo.",
                )
            st.caption(f"Banda en uso: {banda_en_uso}. Corrección: {correccion_en_uso}.")
        with _taller_b:
            st.toggle(
                "Aplicar corrección de reglas",
                value=False,
                key="aplicar_reglas",
                on_change=_rerun_app,
                help=(
                    "Pasada B del motor de reglas (paquete src/mia/): R2b ajuste isotonico "
                    "causal y R6 banda conformal recalibrada sobre el punto corregido. "
                    "Apagado, la UI muestra la lectura cruda de la caché, que es la que "
                    "reproduce el contrato congelado del artefacto."
                ),
            )
        st.caption(
            "La decisión sigue siendo por límite inferior: mover estos controles no "
            "cambia esa agregación, solo los números que la disparan. El reloj de "
            "flota vive en la barra lateral, junto a la unidad."
        )

    # -------------------- avance de flota: el reloj se mueve, los retenidos no
    with st.container(border=True):
        st.subheader("Avanzar la flota", icon=":material/fast_forward:")
        st.caption(
            "Mueve el reloj compartido. El motor que ya cruzó el umbral deja de "
            "volar: se queda donde está en vez de extrapolarle. Los números salen "
            "de la caché ya puntuada; no se recalcula nada."
        )
        # P1.1 · reusa `frame_cache` (ya decidido arriba): la 2ª pasada
        # sobre `windows` cruda era redundante con aplicar_reglas=False
        # (idéntica) y divergente con aplicar_reglas=True. `retenidos`/
        # `ciclos_hasta_fallo` solo leen unit/cycle/lower, así que el
        # frame fusionado vale íntegro para este bloque.
        _decidido = frame_cache
        _retenidos = S.retenidos(_decidido, cycle, umbrales)
        _faltan = S.ciclos_hasta_fallo(_decidido, cycle, umbrales)
        _fila_av = st.columns([1, 2])
        with _fila_av[0]:
            if st.button("Avanzar 10 ciclos de flota",
                         icon=":material/fast_forward:", key="avanzar_flota",
                         type="primary"):
                # No se escribe `cycle` aqui: el widget ya se instancio en esta
                # pasada y Streamlit lo prohibe
                # (`StreamlitWidgetAlreadyInstantiatedError`): la pagina revienta.
                # Se deja la bandera y el bloque de escrituras diferidas la aplica
                # antes de que el widget nazca.
                st.session_state["_avance_flota"] = int(min(
                    cycle + 10, int(windows["cycle"].max())))
                st.rerun()
        with _fila_av[1]:
            if _retenidos:
                st.caption(
                    "No vuelan: " + ", ".join(
                        F.etiqueta(F.clave_de(float(u), _registro()))
                        for u in sorted(_retenidos)))
            else:
                st.caption("Toda la flota puede volar en este ciclo.")
        _faltan_txt = " · ".join(
            f"{F.etiqueta(F.clave_de(float(u), _registro()))}: "
            + ("nunca en la vida registrada" if v is None else f"{v} ciclos")
            for u, v in sorted(_faltan.items()))
        st.caption(f"Ciclos hasta el umbral de hangar · {_faltan_txt}")

    # -------------------- modo historia: la narrativa en cuatro pasos
    if _vista_tribunal:
        with st.container(border=True):
            st.subheader("Modo historia · la narrativa en cuatro pasos", icon=":material/auto_stories:")
            st.caption("Cuatro estados que cuentan la historia, derivados de la caché. Cada paso deja la app donde dice; el cuarto cambia la política para ver el efecto.")
            # Base del preset, no los umbrales en vigor: tras el paso 4 (35/20)
            # los umbrales en vigor ya están contaminados y los pasos 1-3
            # derivarían su base de ellos en vez de restaurar el preset.
            _pasos_historia = A.estado_historia(windows, {"apto": float(_preset_vals[0]), "hangar": float(_preset_vals[1])})
            _cols_h = st.columns(len(_pasos_historia))
            for _col, _paso in zip(_cols_h, _pasos_historia):
                with _col:
                    if st.button(f"{_paso['paso']}. {_paso['titulo']}", key=f"historia_{_paso['paso']}", icon=":material/play_circle:"):
                        st.session_state["_escenario_pendiente"] = (int(_paso["unidad"]), int(_paso["ciclo"]))
                        st.session_state["_umbrales_pendientes"] = (_paso["umbrales"]["apto"], _paso["umbrales"]["hangar"])
                        _log_sesion = st.session_state.get("_sesion_log") or []
                        _log_sesion.append({"at": pd.Timestamp.now(tz="UTC").isoformat(), "que": f"Modo historia, paso {_paso['paso']}: {_paso['titulo']}."})
                        st.session_state["_sesion_log"] = _log_sesion
                        st.session_state["_toast_pendiente"] = (f"Paso {_paso['paso']}: {_paso['titulo']}. {_paso['cuenta']}")
                        st.rerun()
                    st.caption(_paso["cuenta"])

    # -------------------- registro de sesión
    # Plegado: es un log de auditoría de la sesión, no algo que se mire en directo.
    if _vista_tribunal:
        with st.expander("Registro de sesión · qué se ha hecho en esta sesión",
                         icon=":material/receipt_long:"):
            _log_sesion = st.session_state.get("_sesion_log") or []
            if not _log_sesion:
                st.caption(
                    "Todavía no has hecho nada en esta sesión. El registro se llena con "
                    "cada acción discreta: altas, escenarios, lotes y gemelos."
                )
            else:
                st.dataframe(
                    pd.DataFrame(_log_sesion),
                    hide_index=True,
                    column_config={
                        "at": st.column_config.TextColumn("Cuándo"),
                        "que": st.column_config.TextColumn("Qué"),
                    },
                    alt="Registro de sesión: las acciones hechas, con su fecha.",
                )
                with st.container(horizontal=True):
                    st.download_button(
                        "Descargar registro (CSV)",
                        data=pd.DataFrame(_log_sesion).to_csv(index=False),
                        file_name="registro_sesion_ds02.csv",
                        mime="text/csv",
                        icon=":material/download:",
                    )
                    if st.button("Vaciar registro", icon=":material/delete:",
                                 key="sesion_vaciar"):
                        st.session_state["_sesion_log"] = []
                        st.rerun()

    if correccion:
        st.caption(
            f"**Corrección de reglas activa** (pasada B del motor `src/mia/`): "
            f"{L.fmt_miles(correccion['ventanas_corregidas'])} de {L.fmt_miles(correccion['ventanas'])} "
            f"ventanas movidas ({correccion['porcentaje']} %) · "
            f"Δ punto medio {correccion['delta_medio_punto']:+.2f} ciclos · "
            f"Δ L_inf medio {correccion['delta_medio_l_inf']:+.2f}. "
            "La lectura cruda de la caché sigue disponible en la pestaña de auditoría."
        )


    # Plegada la tabla; la tarjeta «Regla de negocio» se queda fuera, a la vista.
    with st.expander("Cola de mantenimiento · tabla por unidad",
                     icon=":material/assignment:", expanded=False):
        display = pd.DataFrame(
            {
                "Motor": [_etiqueta_unidad(float(u)) for u in snapshot["unit"]],
                "Ciclo": snapshot["cycle"],
                "RUL real": snapshot["y_true"],
                "RUL p35": snapshot["pred"],
                "L_inf (riesgo)": snapshot["lower"],
                "L_sup": snapshot["upper"],
                "Estado": snapshot["state_label"],
                "Regla": snapshot["rule"],
                "Por qué decide así": [
                    (
                        f"L_inf {lo:.1f} ≥ {threshold_apto:.0f}: vuela"
                        if estado == L.AIRWORTHY else
                        f"L_inf {lo:.1f} < {threshold_aog:.0f}: al hangar"
                        if estado == L.AOG else
                        (f"L_inf {lo:.1f} entre {threshold_aog:.0f} y "
                         f"{threshold_apto:.0f}: vigilar"
                         if pd.notna(lo) else "sin telemetría en este ciclo")
                    )
                    for lo, estado in zip(snapshot["lower"], snapshot["state"])
                ],
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
                "RUL p35": st.column_config.NumberColumn("RUL p35", format="%.1f",
                                                help="Cuantil 0.35 de la RUL (ADR-003)."),
                "L_inf (riesgo)": st.column_config.NumberColumn(
                    "L_inf (riesgo)", format="%.1f",
                    help="Límite inferior de la banda conformal: es lo que decide el estado.",
                ),
                "L_sup": st.column_config.NumberColumn("L_sup", format="%.1f"),
                "Regla": st.column_config.TextColumn(
                    "Regla",
                    help="Regla de la pasada A que firmó el estado (mia.motor).",
                ),
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

    with st.expander("Comparar con otros umbrales", icon=":material/compare:"):
        st.caption(
            "Recalcula la flota con un segundo juego de umbrales (sin re-puntuar) y "
            "muestra qué cambiaría respecto a los en vigor."
        )
        comp_a = st.number_input("Apto alternativo", min_value=1.0, max_value=100.0,
                                  value=threshold_apto + 5.0, step=1.0, key="comp_apto")
        comp_h = st.number_input("Hangar alternativo", min_value=0.0, max_value=99.0,
                                  value=threshold_aog + 5.0, step=1.0, key="comp_aog")
        if comp_h >= comp_a:
            st.error("El hangar alternativo debe ser menor que el apto alternativo.",
                      icon=":material/rule:")
        else:
            snap_b = L.fleet_snapshot(frame, cycle, comp_a, comp_h)
            cuenta_a = snapshot["state"].value_counts()
            cuenta_b = snap_b["state"].value_counts()
            comp = pd.DataFrame({
                "Estado": [L.STATE_LABELS.get(s, s) for s in L.STATE_LABELS],
                "En vigor": [int(cuenta_a.get(s, 0)) for s in L.STATE_LABELS],
                "Alternativo": [int(cuenta_b.get(s, 0)) for s in L.STATE_LABELS],
            })
            st.dataframe(comp, hide_index=True,
                         alt="Comparativa de estados de flota entre umbrales en vigor y alternativos.")
            merged = snapshot[["unit", "state"]].merge(
                snap_b[["unit", "state"]], on="unit", suffixes=("", "_alt"))
            cambian = merged[merged["state"] != merged["state_alt"]]
            if cambian.empty:
                st.caption("Nada cambiaría: los mismos estados con los otros umbrales.")
            else:
                st.dataframe(
                    pd.DataFrame({
                        "Motor": [f"U{int(u)}" for u in cambian["unit"]],
                        "Ahora": [L.STATE_LABELS.get(s, s) for s in cambian["state"]],
                        "Con alternativos": [L.STATE_LABELS.get(s, s)
                                              for s in cambian["state_alt"]],
                    }),
                    hide_index=True,
                    alt="Unidades que cambiarían de estado con los umbrales alternativos.",
                )

    with st.expander("Historial de la unidad: cómo llegó a este estado",
                      icon=":material/history:"):
        hist = UR.estado_por_ciclo(frame)
        hu = hist[hist["unit"] == unit].sort_values("cycle").reset_index(drop=True)
        if hu.empty:
            st.caption("Sin ciclos evaluados para esta unidad.")
        else:
            rachas, inicio = [], hu.iloc[0]
            previo = None
            for _, fila_h in hu.iterrows():
                if previo is not None and fila_h["decision"] != previo["decision"]:
                    rachas.append({"Desde": int(previo["cycle"]),
                                   "Hasta": int(fila_h["cycle"] - 1),
                                   "Estado": L.STATE_LABELS.get(previo["decision"],
                                                                  str(previo["decision"])),
                                   "L_inf mín": round(float(hu[(hu["cycle"] >= previo["cycle"]) &
                                                                 (hu["cycle"] < fila_h["cycle"])]
                                                              ["lower"].min()), 1)})
                    previo = fila_h
                elif previo is None:
                    previo = fila_h
            if previo is not None:
                rachas.append({"Desde": int(previo["cycle"]),
                               "Hasta": int(hu["cycle"].max()),
                               "Estado": L.STATE_LABELS.get(previo["decision"],
                                                              str(previo["decision"])),
                               "L_inf mín": round(float(hu[hu["cycle"] >= previo["cycle"]]
                                                          ["lower"].min()), 1)})
            st.dataframe(pd.DataFrame(rachas), hide_index=True,
                         alt="Rachas de estado de la unidad seleccionada a lo largo de los ciclos.")

    if _vista_tribunal:
        with st.container(border=True):
            st.subheader("Motor de reglas · traza del caso", icon=":material/rule:")
            fila = snapshot[snapshot["unit"] == unit].iloc[0]
            st.caption(
                "Pasada A de `mia.motor` sobre la unidad seleccionada: la misma función del "
                "cuaderno de práctica, no una reclasificación paralela. Gana la regla de "
                "mayor prioridad que se cumpla."
            )
            if bool(fila["reached"]):
                traza = UR.traza_decision(float(fila["lower"]), umbrales)
                st.markdown(
                    f"**U{int(unit)} · ciclo {cycle}** · `L_inf = {fila['lower']:.1f}` → "
                    f"**{traza['decision'] or 'sin decisión'}** · reglas: "
                    + (" → ".join(traza["usadas"]) or "(ninguna)")
                )
                for linea in traza["porque"]:
                    st.caption(linea)
            else:
                st.caption(
                    "La unidad todavía no tiene ventanas evaluadas en este ciclo: el motor no "
                    "emite una decisión que no pueda sostener."
                )
            catalogo = pd.DataFrame(UR.catalogo_decision()).rename(
                columns={"regla": "Regla", "prioridad": "Prioridad", "porque": "Porqué"}
            )
            st.dataframe(
                catalogo,
                hide_index=True,
                column_config={
                    "Prioridad": st.column_config.NumberColumn("Prioridad", format="%d"),
                },
                alt="Reglas de la pasada A, con su prioridad y su justificación.",
            )

    blocked = order["unidades"]
    with st.container(border=True):
        st.subheader("Orden de trabajo", icon=":material/description:")
        if blocked:
            st.caption(
                f"{len(blocked)} unidad(es) bloqueada(s) en el ciclo {cycle}. El documento lleva "
                "el hash del artefacto y los umbrales en vigor."
            )
            # app-ux-bundle-fix: vista previa de la orden antes de descargar.
            st.dataframe(
                pd.DataFrame(blocked),
                hide_index=True,
                column_config={
                    "limite_inferior": st.column_config.NumberColumn(
                        "L_inf", format="%.2f"),
                },
                alt="Vista previa de la orden de trabajo: unidades bloqueadas con su límite inferior y acción.",
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
                st.download_button(
                    "Descargar orden (PDF)",
                    data=PP.parte_trabajo_pdf(order),
                    file_name=f"orden_mantenimiento_ds02_ciclo{cycle}.pdf",
                    mime="application/pdf",
                    icon=":material/picture_as_pdf:",
                )
        else:
            st.success(
                f"Ninguna unidad en hangar en el ciclo {cycle}. No se emite orden de trabajo.",
                title="Flota disponible",
                icon=":material/check_circle:",
            )
            parte = L.parte_disponibilidad(snapshot, provenance, threshold_apto,
                                            threshold_aog)
            with st.container(horizontal=True):
                st.download_button(
                    "Descargar parte de disponibilidad (JSON)",
                    data=json.dumps(parte, ensure_ascii=False, indent=2),
                    file_name=f"parte_disponibilidad_ds02_ciclo{cycle}.json",
                    mime="application/json",
                    icon=":material/download:",
                    help="Deja constancia firmable de que se miró la flota y no había nada que derivar.",
                )
                st.download_button(
                    "Descargar parte de flota (CSV)",
                    data=snapshot[["unit", "cycle", "state", "rule"]].to_csv(index=False),
                    file_name=f"parte_flota_ds02_ciclo{cycle}.csv",
                    mime="text/csv",
                    icon=":material/table_view:",
                )

    # app-ux-bundle-fix: contraste crudo vs corregido (CSV por ventana).
    with st.container(border=True):
        st.subheader("Contraste crudo vs corregido", icon=":material/compare_arrows:")
        st.caption(
            "Por ventana: límite inferior de la caché (crudo) frente al de la capa "
            "de reglas (corregido), con la decisión final."
        )
        st.download_button(
            "Descargar contraste (CSV)",
            data=DH.contraste_csv(windows, frame_cache),
            file_name=f"contraste_crudo_corregido_ciclo{cycle}.csv",
            mime="text/csv",
            icon=":material/table_view:",
        )


    # ------------------------------------------------------ gemelos y hangar
    with st.container(border=True):
        st.subheader("Gemelos registrados", icon=":material/precision_manufacturing:")
        aviso_gemelo = st.session_state.get("twin_flash")
        if aviso_gemelo:
            del st.session_state["twin_flash"]
            st.toast(aviso_gemelo, icon=":material/check_circle:")
        # El muro manda: una tarjeta de gemelo apunta aqui. Se consume en cuanto se
        # lee, para que no vuelva a salir en el siguiente render.
        gemelo_pendiente = st.session_state.pop("_gemelo_pendiente", None)
        if gemelo_pendiente:
            if gemelo_pendiente in gemelos:
                _estado_pendiente = T.estado_actual(gemelos[gemelo_pendiente], umbrales)
                st.caption(
                    f"**{gemelo_pendiente}**: "
                    f"{L.STATE_LABELS.get(_estado_pendiente['decision'])} "
                    f"con los umbrales en vigor, L_inf {_estado_pendiente['lower_min']:.1f} ciclos."
                )
            else:
                st.caption(f"El motor `{gemelo_pendiente}` ya no está registrado.")
        if not gemelos:
            st.caption(
                "Ningún motor externo registrado todavía. Puntúa uno en «Evaluar unidad "
                "nueva» y añádelo: la serie queda guardada y su estado se recalcula con "
                "los umbrales en vigor, sin volver a llamar al modelo."
            )
        else:
            filas_gemelos = []
            for gemelo_id, gemelo in gemelos.items():
                estado_g = T.estado_actual(gemelo, umbrales)
                metricas_g = T.metricas_verdad(gemelo)
                filas_gemelos.append({
                    "Motor": gemelo_id,
                    "Ciclo": estado_g["cycle"],
                    "L_inf": estado_g["lower_min"],
                    "Estado": L.STATE_LABELS.get(estado_g["decision"],
                                                 str(estado_g["decision"])),
                    "Regla": estado_g["regla"],
                    "Banda": gemelo["banda"],
                    "Verdad": ("sin reportar" if not metricas_g else
                               f"{metricas_g['rul_real']:.0f} · "
                               f"{'dentro' if metricas_g['cubierta'] else 'fuera'}"),
                    "Huella": gemelo["fingerprint"][:8],
                })
            st.dataframe(
                pd.DataFrame(filas_gemelos),
                hide_index=True,
                column_config={
                    "Ciclo": st.column_config.NumberColumn("Ciclo", format="%d"),
                    "L_inf": st.column_config.NumberColumn("L_inf", format="%.2f"),
                    "Huella": st.column_config.TextColumn("Huella", help="SHA-256 de la tabla puntuada."),
                },
                alt="Motores externos registrados con su estado recalculado, la regla aplicada y la banda usada.",
            )
            resumen_gemelos = T.resumen(gemelos)
            if resumen_gemelos["con_verdad"]:
                st.caption(
                    f"{resumen_gemelos['con_verdad']} gemelo(s) con verdad reportada · "
                    f"cobertura {resumen_gemelos['cubiertos']}/{resumen_gemelos['con_verdad']} · "
                    f"MAE {resumen_gemelos['mae']:.2f} ciclos"
                )
            st.markdown("**Gestión de los gemelos registrados**")
            with st.expander("Reportar la RUL real de un gemelo", icon=":material/fact_check:"):
                elegido_v = st.selectbox(
                    "Motor", list(gemelos), key="truth_engine",
                    help="Gemelo registrado sobre el que se declara la RUL real conocida.",
                )
                ciclo_v = st.number_input(
                    "Ciclo en que se conoció", min_value=0.0, step=1.0,
                    value=float(gemelos[elegido_v]["serie"][-1]["cycle"]),
                    key=f"truth_cycle_{elegido_v}",
                )
                rul_v = st.number_input(
                    "RUL real (ciclos)", min_value=0.0, step=1.0, value=0.0,
                    key=f"truth_rul_{elegido_v}",
                )
                st.caption(
                    "La cobertura se mide contra la ventana más pesimista de ese ciclo: "
                    "si esa banda cubre la verdad, la decisión que la acompañó era defendible."
                )
                if st.button("Guardar verdad", icon=":material/save:", key="truth_save"):
                    try:
                        actualizado = T.con_verdad(gemelos[elegido_v], rul_v, ciclo_v)
                    except ValueError as exc:
                        st.error(str(exc), title="Valor no válido", icon=":material/rule:")
                    else:
                        st.session_state["twins"] = {**gemelos, elegido_v: actualizado}
                        _guardar_registros()
                        st.rerun()

            with st.expander("Documentar un gemelo", icon=":material/description:"):
                motor_doc = st.selectbox(
                    "Motor", list(gemelos), key="twin_doc",
                    help="Gemelo registrado a documentar (orden de trabajo JSON).",
                )
                gemelo_doc = gemelos[motor_doc]
                estado_doc = T.estado_actual(gemelo_doc, umbrales)
                orden_gemelo = INF.live_work_order(
                    T.vista_resultado(gemelo_doc),
                    {"source": gemelo_doc["source"],
                     "registrado_en": gemelo_doc["created_at"],
                     "huella": gemelo_doc["fingerprint"]},
                    threshold_apto, threshold_aog,
                    banda=gemelo_doc["banda"], correccion=gemelo_doc["correccion"],
                )
                # El documento describe un gemelo guardado, no una evaluación recién hecha.
                orden_gemelo["documento"] = f"Orden de mantenimiento — gemelo {motor_doc}"
                orden_gemelo["modo"] = "gemelo registrado (serie guardada, sin repuntuar)"
                ciclo_doc = estado_doc["cycle"]
                # El id lo escribe el usuario: un `/` en el nombre del fichero rompe la descarga.
                slug_doc = _slug_motor(motor_doc.lower())
                etiqueta_doc = L.STATE_LABELS.get(estado_doc["decision"],
                                                 str(estado_doc["decision"]))
                st.caption(
                    f"Estado con los umbrales en vigor: **{etiqueta_doc}**"
                    + (f" en el ciclo {ciclo_doc:.0f}" if ciclo_doc is not None else "")
                    + ". El documento describe la peor ventana de ese ciclo, con la huella y "
                    "la banda que se guardaron al puntuar: no se llama al modelo."
                )
                with st.container(horizontal=True):
                    st.download_button(
                        "Descargar ficha del gemelo (JSON)",
                        data=json.dumps(orden_gemelo, ensure_ascii=False, indent=2),
                        file_name=f"orden_mantenimiento_{slug_doc}.json",
                        mime="application/json",
                        icon=":material/download:",
                        key="twin_doc_json",
                    )
                    st.download_button(
                        "Descargar ficha del gemelo (CSV)",
                        data=L.work_order_csv(orden_gemelo),
                        file_name=f"orden_mantenimiento_{slug_doc}.csv",
                        mime="text/csv",
                        icon=":material/table_view:",
                        key="twin_doc_csv",
                    )

            with st.expander("Eliminar un gemelo", icon=":material/delete:"):
                borrar = st.selectbox(
                    "Motor", list(gemelos), key="twin_del",
                    help="Gemelo registrado a eliminar de la flota de la sesión.",
                )
                st.caption(
                    "Borrar un gemelo no toca su registro de hangar: el gemelo es lo que el "
                    "modelo dijo, el registro es lo que pasó después."
                )
                if st.button("Eliminar gemelo", icon=":material/delete_forever:",
                             key="twin_del_btn"):
                    st.session_state["twins"] = T.eliminar(gemelos, borrar)
                    _guardar_registros()
                    st.session_state["twin_flash"] = f"Gemelo `{borrar}` eliminado."
                    st.rerun()


    def _panel_gemelo() -> None:
        """Detalle del gemelo registrado: su curva, su banda y su ventana.

        Antes no existía. La serie del gemelo (cycle, pred, lower, upper, start_row)
        ya estaba guardada en `twins`; el muro la dibujaba y nada más. Aquí se ve
        completa, con la banda y con las dos preguntas que un gemelo digital tiene
        que responder: cuánto le queda y en qué ventana se basó la decisión.

        Se alimenta de `st.session_state`, nunca de un global de módulo: es un
        contenedor de primer nivel y se re-ejecuta completo en cada pasada.
        """
        with st.container(border=True):
            st.subheader("Gemelo digital · detalle",
                         icon=":material/precision_manufacturing:")
            st.caption(
                "El gemelo es lo que el modelo dijo, guardado una vez. Su estado se "
                "recalcula con los umbrales en vigor sin volver a llamar al modelo: "
                "la serie no cambia, la lectura sí."
            )
            _gemelos = st.session_state.get("twins") or {}
            if not _gemelos:
                st.caption(
                    "Ningún gemelo registrado todavía. Puntúa un motor en «Evaluar "
                    "unidad nueva» y aparece aquí con su curva completa."
                )
                return
            _elegido = st.selectbox(
                "Gemelo", list(_gemelos), key="gemelo_detalle_sel",
                help="Motores registrados en esta sesión, con su serie guardada.",
            )
            _gemelo = _gemelos[_elegido]
            _curva = T.ciclo_a_ciclo(_gemelo, umbrales)
            if _curva.empty:
                st.caption(f"`{_elegido}` no tiene serie que dibujar.")
                return

            _ultima = _curva.iloc[-1]
            _decision = str(_ultima["decision"])
            _pred = float(_ultima["pred"])
            _lo = float(_ultima["lower_min"])
            _ciclo_ult = int(_ultima["cycle"])

            # Ciclos hasta el umbral: la misma pregunta que la flota le hace a la
            # caché, hecha aquí sobre la serie guardada.
            _cruce = _curva[_curva["lower_min"] < umbrales["hangar"]]
            _falta = (None if _cruce.empty
                      else int(_cruce["cycle"].min()) - _ciclo_ult)
            _falta_txt = ("no cruza el umbral en la vida registrada" if _falta is None
                          else ("ya está por debajo del umbral" if _falta <= 0
                                else f"{_falta} ciclos"))

            st.metric("RUL p35 (conservadora)", f"{_pred:.1f}", "cuantil 0.35",
                      border=True, delta_color="off", icon=":material/speed:",
                      help="Cuantil 0.35 de la RUL (ADR-003). El estado no lo decide "
                           "este número: lo decide L_inf.")
            st.metric("L_inf (decide)", f"{_lo:.1f}", "ciclos",
                      border=True, delta_color="off", icon=":material/trending_down:",
                      help="Límite inferior de la banda al 90 %. Es el número que gobierna "
                           "la decisión de hangar (ADR-008).")
            st.metric("Estado", L.STATE_LABELS.get(_decision, _decision),
                      str(_ultima["regla"] or "(sin regla)"),
                      border=True, delta_color="off", icon=":material/rule:")
            st.metric("Ciclos hasta el umbral", _falta_txt, f"ciclo {_ciclo_ult}",
                      border=True, delta_color="off", icon=":material/hourglass_bottom:",
                      help="Primer ciclo de la serie guardada en que L_inf cae por debajo "
                           "del umbral de hangar, menos el último ciclo registrado.")

            # La ventana que decidió: `vista_resultado` ya la elige; aquí se cita.
            _vista = T.vista_resultado(_gemelo)
            _vent = _vista["windows"].iloc[0]
            st.caption(
                f"La ventana que decide es la posición **{int(_vent['window'])}** de la "
                f"serie guardada, del ciclo **{int(_vent['cycle'])}**, que empieza en la fila "
                f"**{int(_vent['start_row'])}** de la tabla puntuada: la más pesimista "
                "de ese ciclo. Es el dato que sostiene el estado."
            )

            _fig = go.Figure()
            _fig.add_trace(go.Scatter(
                x=_curva["cycle"], y=_curva["upper"], mode="lines",
                line=dict(width=0), showlegend=False, hoverinfo="skip",
            ))
            _fig.add_trace(go.Scatter(
                x=_curva["cycle"], y=_curva["lower_media"], mode="lines",
                line=dict(width=0), name="objetivo 90 % · cobertura medida", fill="tonexty",
                fillcolor="rgba(56,189,248,0.18)", hoverinfo="skip",
            ))
            _fig.add_trace(go.Scatter(
                x=_curva["cycle"], y=_curva["pred"], mode="lines", name="RUL p35",
                line=dict(width=2, color=SKY),
                hovertemplate="ciclo %{x}<br>RUL %{y:.1f}<extra></extra>",
            ))
            _fig.add_trace(go.Scatter(
                x=_curva["cycle"], y=_curva["lower_min"], mode="lines",
                name="L_inf (decide)", line=dict(width=2, color=ROSE),
                hovertemplate="ciclo %{x}<br>L_inf %{y:.1f}<extra></extra>",
            ))
            _fig.add_hline(
                y=umbrales["hangar"], line_color=ROSE, line_dash="dash", line_width=1.5,
                annotation_text=f"hangar ({umbrales['hangar']:.0f})",
                annotation_position="top right",
                annotation_font=dict(color=ROSE, size=11),
            )
            _fig.update_layout(**chart_layout(height=340, hovermode="closest"))
            style_axes(_fig, x_title="Ciclo de vuelo", y_title="RUL (ciclos)")
            st.plotly_chart(
                _fig, theme=None,
                alt=f"Curva de RUL del gemelo {_elegido} con su banda conformal al 90 %, "
                    "el límite inferior que decide y el umbral de hangar.",
            )
            st.warning(
                "La banda es la de la serie guardada: **no se recalibra** al mover los "
                "umbrales, porque la calibración es parte del artefacto congelado. "
                "Mover el umbral cambia la lectura, no la banda.",
                icon=":material/info:",
            )


    _panel_gemelo()

    with st.container(border=True):
        st.subheader("Hangar · ciclo de vida", icon=":material/warehouse:")
        resumen_h = HGR.resumen(registros)
        with st.container(horizontal=True):
            st.metric("Registros", resumen_h["total"], border=True, delta_color="off",
                      icon=":material/inventory_2:")
            st.metric("Abiertos", resumen_h["abiertos"], border=True, delta_color="off",
                      icon=":material/pending_actions:")
            st.metric("En taller", resumen_h["por_estado"][HGR.TALLER], border=True,
                      delta_color="off", icon=":material/build:")
        if not registros:
            st.caption(
                "Ningún registro abierto. Al derivar una unidad se congela aquí la decisión "
                "de entrada, con sus umbrales: mover los sliders después no reescribe la "
                "historia."
            )
        else:
            # app-ux-bundle-fix: filtro de estado sobre la cola del hangar.
            _filtro_cola = st.multiselect(
                "Filtrar cola por estado",
                [HGR.ETIQUETAS[e] for e in HGR.ESTADOS],
                default=[HGR.ETIQUETAS[e] for e in HGR.ESTADOS],
                key="cola_filtro_estado",
                help="Restringe la tabla a los estados elegidos.",
            )
            _estados_filtro = {e for e in HGR.ESTADOS
                               if HGR.ETIQUETAS[e] in _filtro_cola}
            filas_hangar = []
            for registro in DH.cola_filtrada(registros, _estados_filtro):
                decision_hoy = UR.traza_decision(registro["entrada"]["lower"], umbrales)["decision"]
                revision = HGR.revision(registro, umbrales, decision_hoy)
                filas_hangar.append({
                    "Unidad": registro["unidad"],
                    "Estado": HGR.ETIQUETAS.get(registro["estado"], registro["estado"]),
                    "L_inf de entrada": registro["entrada"]["lower"],
                    "Umbral de entrada": registro["entrada"]["umbrales"]["hangar"],
                    "Regla": registro["entrada"]["regla"],
                    "Hoy": "coincide" if not revision["cambia"] else revision["hoy"],
                })
            st.dataframe(
                pd.DataFrame(filas_hangar),
                hide_index=True,
                column_config={
                    "L_inf de entrada": st.column_config.NumberColumn(
                        "L_inf de entrada", format="%.2f"),
                    "Umbral de entrada": st.column_config.NumberColumn(
                        "Umbral de entrada", format="%.0f"),
                },
                alt="Cola de hangar ordenada por urgencia, con la decisión congelada y la de hoy.",
            )

        candidatos = {}
        for _, fila in snapshot[snapshot["state"] == L.AOG].iterrows():
            # La clave sale del registro: una alta responde a su matricula, un motor
            # de caché a U<int>. Antes se montaba a mano con f"U{int(unit)}" y las
            # altas entraban al hangar como U-1000.
            candidatos[F.clave_de(float(fila["unit"]), _registro())] = {
                "ciclo": int(fila["cycle"]),
                "lower": float(fila["lower"]),
                "regla": str(fila["rule"]),
            }
        for gemelo_id, gemelo in gemelos.items():
            estado_g = T.estado_actual(gemelo, umbrales)
            if estado_g["decision"] == L.AOG:
                candidatos[gemelo_id] = {
                    "ciclo": int(estado_g["cycle"] or 0),
                    "lower": float(estado_g["lower_min"]),
                    "regla": estado_g["regla"],
                }
        disponibles = [clave for clave in candidatos if clave not in registros]
        if disponibles:
            with st.form("hangar_abrir"):
                elegido_h = st.selectbox(
                    "Unidad a derivar", disponibles,
                    help="Unidad en hangar sin registro abierto en este ciclo.",
                )
                nota_alta = st.text_input("Nota de entrada", value="")
                if st.form_submit_button("Abrir registro", icon=":material/login:"):
                    datos = candidatos[elegido_h]
                    st.session_state["hangar"] = {
                        **registros,
                        elegido_h: HGR.abrir(elegido_h, datos["ciclo"], datos["lower"],
                                             umbrales, datos["regla"], nota=nota_alta),
                    }
                    _guardar_registros()
                    st.rerun()
        else:
            st.caption(
                "No hay unidades en hangar sin registro en este ciclo, ni gemelos "
                "derivados pendientes de abrir."
            )

        if registros:
            with st.container(border=True):
                unidad_sel = st.selectbox("Registro", list(registros), key="hangar_sel")
                actual = registros[unidad_sel]["estado"]
                destino = st.selectbox(
                    "Nuevo estado",
                    HGR.permitidas(actual),
                    format_func=lambda estado: HGR.ETIQUETAS.get(estado, estado),
                    key="hangar_destino",
                    help="Solo se ofrecen los estados alcanzables desde el actual.",
                )
                nota_mov = st.text_input("Nota del evento", key="hangar_nota")
                if st.button("Registrar movimiento", icon=":material/logout:", key="hangar_mover"):
                    try:
                        movido = HGR.avanzar(registros[unidad_sel], destino,
                                             int(cycle), nota=nota_mov)
                    except ValueError as exc:
                        st.error(str(exc), title="Movimiento no permitido",
                                 icon=":material/rule:")
                    else:
                        st.session_state["hangar"] = {**registros, unidad_sel: movido}
                        _guardar_registros()
                        st.rerun()
