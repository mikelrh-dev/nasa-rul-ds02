"""Pestaña Flota: cómo está la flota hoy y qué trabajo sale de ella.

Cuatro preguntas en orden de lectura: cómo está cada motor (el muro del hangar),
cómo ha llegado hasta aquí (cronología y avance), qué política se aplica (el
taller) y qué trabajo produce todo eso (cola, orden de trabajo y partes). Los
gemelos registrados y su panel de detalle cierran la sala.

La pestaña se lee como un guion: `_tab_flota` es un preámbulo de alias y once
llamadas con nombre, y cada bloque vive en su propia función anidada. Todas leen
los alias del preámbulo por clausura, así que el orden de las llamadas es el
orden de la pantalla.

Los datos llegan en el `AppCtx` que construye
`app/entrypoints/dashboard_ds02.py`; este módulo no importa el dashboard ni
TensorFlow. Nació como extracción literal del monolito y conserva su
comportamiento: ninguna métrica, umbral ni caché (`frame_cache` ttl=3600, SHAP
ola-2, firma del PDF) cambia aquí.
"""
from __future__ import annotations

import json

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.lib import flota as F
from app.lib import hangar as HGR
from app.lib import dashboard_helpers as DH
from app.lib import pdf_partes as PP
from app.lib import simulacion as S
from app.lib import twin as T
from app.lib import ui_data_loader as L
from app.lib import ui_inference as INF
from app.lib import rules as UR

# Design tokens: dueno `theme.py` (el dashboard tambien los importa de ahi).
from app.lib.theme import (
    SKY, ROSE,
    STATE_BG, RANGO_ESTADO,
    BADGE_COLOR, BADGE_ICON,
)
from app.lib.context import AppCtx

__all__ = ["_tab_flota"]


def _rerun_app() -> None:
    """Callback full-scope: este fragmento re-ejecuta con argumentos congelados
    de `dashboard:1142-1156`, asi que un `st.rerun()` local dejaria banda y
    triaje stale. `scope="app"` re-ejecuta el dashboard y recalcula banda.
    No se quita el `@st.fragment` (romperia la paginacion del muro).
    """
    st.rerun(scope="app")


@st.fragment
def _tab_flota(ctx: AppCtx) -> None:
    """Muro del hangar y el trabajo que sale de él, en orden de pantalla.

    Preámbulo de alias y once llamadas: cada bloque vive en la `def` anidada
    que le sigue y lee el `AppCtx` por clausura, así que este cuerpo es el índice
    visual de la pestaña. Ver «Cómo se lee una pestaña» en `app/README.md`.
    """
    frame = ctx.frame
    frame_cache = ctx.frame_cache
    snapshot = ctx.snapshot
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

    def _muro_del_hangar_ui() -> None:
        """Muro del hangar: una tarjeta por motor con su sparkline."""
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
                                    # «Ver gemelo» apunta al tab Motor: el dashboard consume
                                    # `_escenario_pendiente` con escritura diferida (clave
                                    # `unit` del sidebar).
                                    st.session_state["_escenario_pendiente"] = (
                                        tarjeta["unidad"], tarjeta["ciclo_tarjeta"])
                                    st.session_state["_toast_pendiente"] = (
                                        f"{etiqueta} seleccionada. Abre su ficha en la "
                                        "pestaña «Motor · qué le pasa a este»."
                                    )
                                st.rerun()

            _muro_del_hangar()

    def _taller_politica() -> None:
        """El taller: preset y umbrales en vigor."""
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

    def _avance_de_flota() -> None:
        """Reloj de flota y unidades retenidas."""
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

    def _registro_de_sesion() -> None:
        """Registro de las acciones de la sesion."""
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

    def _cola_de_mantenimiento() -> None:
        """Tabla de la cola con el porque de cada estado."""
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

    def _historial_de_unidad() -> None:
        """Rachas de estado de la unidad seleccionada."""
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

    def _traza_de_reglas() -> None:
        """Traza de la pasada A sobre la unidad seleccionada."""
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
    def _orden_de_trabajo() -> None:
        """Orden de trabajo y partes descargables."""
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

    def _gemelos_registrados() -> None:
        """Tabla y gestion de los gemelos registrados."""
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
                resumen_gemelos = T.resumen_gemelos(gemelos)
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

    def _hangar_ciclo_de_vida() -> None:
        """Cola del hangar, filtro y derivacion."""
        with st.container(border=True):
            st.subheader("Hangar · ciclo de vida", icon=":material/warehouse:")
            resumen_h = HGR.resumen_estados(registros)
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

    _muro_del_hangar_ui()

    _taller_politica()

    _avance_de_flota()

    _registro_de_sesion()

    if correccion:
        st.caption(
            f"**Corrección de reglas activa** (pasada B del motor `src/mia/`): "
            f"{L.fmt_miles(correccion['ventanas_corregidas'])} de {L.fmt_miles(correccion['ventanas'])} "
            f"ventanas movidas ({correccion['porcentaje']} %) · "
            f"Δ punto medio {correccion['delta_medio_punto']:+.2f} ciclos · "
            f"Δ L_inf medio {correccion['delta_medio_l_inf']:+.2f}. "
            "La lectura cruda de la caché sigue disponible en la pestaña de auditoría."
        )

    _cola_de_mantenimiento()

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

    _historial_de_unidad()

    _traza_de_reglas()

    _orden_de_trabajo()

    _gemelos_registrados()

    _panel_gemelo()

    _hangar_ciclo_de_vida()
