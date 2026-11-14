"""Sala «Casos nuevos»: traer motores que no están en la caché.

Cuatro caminos hacia el mismo validador: el lote de CSV, el ejemplo de un clic,
el explorador por ciclo y el formulario con datos propios. El resultado se pinta
en una tarjeta común y desde ahí se registra el gemelo.

`_tab_casos` es un preámbulo de alias y ocho llamadas con nombre. El formulario
individual (`_unidad_nueva`) conserva su estado en variables locales porque las
tres rutas de entrada desembocan en la misma puntuación. Recibe el `AppCtx` y no
importa el dashboard.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.lib import twin as T
from app.lib import alta as A
from app.lib import batch as B
from app.lib import ui_data_loader as L
from app.lib import ui_inference as INF
from app.lib import n8n_payload as UN
from app.lib import rules as UR
from src import n8n as N8N

from app.lib.theme import (
    CHART_CONFIG, ROSE, ROSE_SOFT, SKY, chart_layout, style_axes,
)

from app.ui._sandbox_estres import _sandbox_estres
from app.lib.context import AppCtx


# Quinto elemento del desplegable «Dataset demo»: no es un preset, es la
# puerta a elegir motor y rango de ciclos a mano.
DEMO_MANUAL = "Manual (motor y rango de ciclos)"


@st.fragment
def _tab_casos(ctx: AppCtx) -> None:
    """Cuatro rutas de entrada al mismo validador, en orden de pantalla.

    Preámbulo de alias y ocho llamadas; cada bloque es una `def` anidada que lee
    el `AppCtx` por clausura. El formulario (`_unidad_nueva`) guarda su estado en
    locales porque las tres rutas desembocan en la misma puntuación. Ver «Cómo se
    lee una pestaña» en `app/README.md`.
    """
    _guardar_registros = ctx.guardar_registros
    _log = ctx.log
    _preflight_panel = ctx.preflight_panel
    _vista_tribunal = ctx.vista_tribunal
    shap_panel = ctx.shap_panel
    threshold_aog = ctx.threshold_aog
    threshold_apto = ctx.threshold_apto
    umbrales = ctx.umbrales
    windows = ctx.windows

    def _lote_de_motores() -> None:
        """Carga de un lote de motores y su triage."""
        with st.container(border=True):
            st.subheader("Incorporar en lote · trae uno o doce", icon=":material/library_add:")
            st.caption(
                "Puntúa N motores de una vez y devuelve una fila por motor: predicción, "
                "banda y estado. No reentrena, no toca la caché y no inventa ground truth: "
                "los datos los aportas tú, así que no hay RMSE ni MAE que reportar."
            )
            _lote_mode = st.segmented_control(
                "Fuente del lote",
                ["Subir CSV (uno por motor)", "Pegar CSV por bloques"],
                default="Subir CSV (uno por motor)",
                key="lote_mode",
                help="Cada CSV es un motor. En la segunda opción, una columna `unit_id` "
                     "separa los motores dentro del mismo CSV.",
            )
            _bloques: list[dict] = []
            if _lote_mode == "Subir CSV (uno por motor)":
                _archivos = st.file_uploader(
                    f"CSV de motores (máximo {B.MAX_MOTORES_LOTE})",
                    type=["csv"], accept_multiple_files=True, key="lote_archivos",
                )
                if _archivos:
                    try:
                        # P1: `bloques_de_archivos` rechaza el lote antes de
                        # parsear todo si hay > MAX_MOTORES_LOTE archivos y
                        # valida tamaño en bytes + nrows=MAX_FILAS+1 por archivo.
                        _bloques = B.bloques_de_archivos(_archivos)
                    except Exception as exc:  # noqa: BLE001 - el mensaje se muestra
                        st.error(f"No se pudieron leer los CSV: {exc}",
                                 icon=":material/error:")
            else:
                _texto_lote = st.text_area(
                    "CSV con columna `unit_id`", height=160, key="lote_texto",
                    placeholder="unit_id,cycle,alt,Mach,TRA,T2,T24,…",
                    help="Una columna `unit_id` por motor y los 18 canales del dataset.",
                )
                if _texto_lote.strip():
                    try:
                        _bloques = B.bloques_de_csv(_texto_lote)
                    except Exception as exc:  # noqa: BLE001
                        st.error(f"No se pudo leer el CSV por bloques: {exc}",
                                 icon=":material/error:")

            if B.excede_limite(len(_bloques)):
                st.error(
                    f"Traes {len(_bloques)} motores y el tope es {B.MAX_MOTORES_LOTE}. "
                    "Quita algunos: por encima del tope el lote deja de ser interactivo "
                    "en un portátil.",
                    icon=":material/rule:",
                )
                _bloques = []
            elif _bloques:
                _aviso_lote = B.validar_lote(_bloques)
                if not _aviso_lote["ok"]:
                    for _mat, _error in _aviso_lote["errores"].items():
                        st.error(f"`{_mat}`: {_error}", icon=":material/rule:")
                else:
                    with st.form("lote_evaluar"):
                        _enviar_lote = st.form_submit_button(
                            f"Puntuar {_aviso_lote['bloques']} motor(es)",
                            type="primary", icon=":material/play_arrow:",
                        )
                    if _enviar_lote:
                        _barra = st.progress(0.0, text="Puntuando 0 de …")

                        def _progreso(i, n, mat):
                            """Actualiza la barra de progreso al puntuar el lote."""
                            _barra.progress(i / n, text=f"Puntuando {i} de {n} · {mat}")

                        try:
                            _resultado_lote = B.puntuar_lote(
                                _bloques, umbrales, INF.get_ensemble(), _progreso)
                        except ValueError as exc:
                            st.session_state["lote_resultado"] = None
                            st.error(str(exc), title="No se pudo puntuar el lote",
                                     icon=":material/rule:")
                        else:
                            st.session_state["lote_resultado"] = _resultado_lote
                            st.session_state["lote_bloques"] = _bloques
                            _log(f"Lote puntuado: {len(_bloques)} motor(es).")
                            st.rerun()

        _lote = st.session_state.get("lote_resultado")
        if _lote is not None:
            _resumen = B.resumen_lote(_lote)
            with st.container(horizontal=True):
                st.metric("Motores puntuados", f"{_resumen['total']}", border=True,
                          delta_color="off", icon=":material/groups:")
                st.metric("En hangar", f"{_resumen['por_estado'][L.AOG]}", border=True,
                          delta_color="off", icon=":material/local_shipping:")
                st.metric("En inspección", f"{_resumen['por_estado'][L.PREVENTIVE]}",
                          border=True, delta_color="off", icon=":material/schedule:")
                st.metric("Aptos", f"{_resumen['por_estado'][L.AIRWORTHY]}", border=True,
                          delta_color="off", icon=":material/check_circle:")
            _ver = _lote.rename(columns={
                "matricula": "Matrícula", "ciclo": "Ciclo", "pred": "RUL p35",
                "lower": "L_inf (decide)", "upper": "L_sup", "estado": "Estado",
                "regla": "Regla",
            })
            st.dataframe(
                _ver, hide_index=True,
                column_config={
                    "Ciclo": st.column_config.NumberColumn("Ciclo", format="%d"),
                    "RUL p35": st.column_config.NumberColumn(
                        "RUL p35", format="%.1f"),
                    "L_inf (decide)": st.column_config.NumberColumn(
                        "L_inf (decide)", format="%.1f",
                        help="Límite inferior de la banda: es lo que decide el estado."),
                    "L_sup": st.column_config.NumberColumn("L_sup", format="%.1f"),
                },
                alt="Triage del lote: una fila por motor con su predicción, su banda y "
                    "su estado.",
            )
            st.caption(
                "Predicción del artefacto congelado (`models/ds02_manifest.json`) sobre los "
                "datos aportados. **Sin ground truth**: no hay error que reportar."
            )
            with st.container(horizontal=True):
                st.download_button(
                    "Descargar triage (CSV)",
                    data=_ver.to_csv(index=False),
                    file_name="triage_lote_ds02.csv",
                    mime="text/csv",
                    icon=":material/download:",
                )
                if st.button(
                    "Registrar gemelos", icon=":material/library_add:",
                    key="lote_registrar",
                    help="Guarda los motores del lote en la flota registrada.",
                ):
                    _barra_g = st.progress(0.0, text="Registrando 0 de …")

                    def _progreso_g(i, n, mat):
                        """Actualiza la barra de progreso al registrar los gemelos."""
                        _barra_g.progress(i / n, text=f"Registrando {i} de {n} · {mat}")

                    try:
                        _gemelos_nuevos = B.registrar_gemelos(
                            st.session_state.get("lote_bloques") or [],
                            INF.get_ensemble(), umbrales,
                            st.session_state.get("twins", {}), _progreso_g)
                    except ValueError as exc:
                        st.error(str(exc), title="No se pudieron registrar",
                                 icon=":material/rule:")
                    else:
                        st.session_state["twins"] = _gemelos_nuevos
                        _guardar_registros()
                        st.session_state["lote_resultado"] = None
                        _log(f"{len(_gemelos_nuevos)} gemelo(s) registrados desde el lote.")
                        st.session_state["twin_flash"] = (
                            f"{len(_gemelos_nuevos)} gemelo(s) en la flota registrada. "
                            "Míralos en la primera pestaña, en «Gemelos registrados»."
                        )
                        st.rerun()

    def _demo_un_clic() -> None:
        """Onboarding: puntua un tramo real de la cache en un clic."""
        with st.container(border=True):
            st.subheader("Puntúa un ejemplo en 1 clic", icon=":material/rocket_launch:")
            st.caption(
                "El onboarding del tablero está en la primera pestaña. Esto puntúa un tramo "
                "real de la caché y deja el resultado listo para registrar: no pega nada ni "
                "sube CSV."
            )
            c1, c2, c3 = st.columns(3)
            for _col, _nombre in zip((c1, c2, c3), list(DEMO_PRESETS)[:3]):
                with _col:
                    if st.button(_nombre, key=f"live_demo_{_nombre}", type="primary" if "Crítico" in _nombre else "secondary", icon=":material/play_arrow:"):
                        _u, _p, _ciclo, _did = DEMO_PRESETS[_nombre]
                        try:
                            if _ciclo is None:
                                _tab, _meta = INF.example_window(
                                    _u, _p, rows=INF.DEMO_ROWS)
                            else:
                                _tab, _meta = INF.window_ending_at(
                                    _u, _ciclo, rows=INF.DEMO_ROWS)
                            _pf = INF.preflight(_tab)
                            if not _pf["ok"]:
                                raise ValueError(_pf["error"])
                            st.session_state["live_engine_id"] = _did
                            # El selectbox «Dataset demo» es la fuente de la tabla del
                            # modo por defecto («Ejemplo del test set»): sin sincronizarlo,
                            # el botón cambiaba la matrícula y el resultado, pero la rejilla,
                            # el pie «Ventana real de U…» y el form «Evaluar unidad» seguían
                            # con el preset anterior y machacaban el resultado del botón.
                            st.session_state["live_demo_preset"] = _nombre
                            st.session_state["_editor_value"] = _tab
                            st.session_state["live_result"] = INF.score_table(_tab, engine_id=_did)
                            st.session_state["live_meta"] = _meta
                            st.session_state["live_warnings"] = _pf["avisos"]
                            st.session_state["live_error"] = None
                            st.session_state["live_flash"] = f"{_nombre} puntuado abajo (ciclos {_meta['start_cycle']}→{_meta['end_cycle']}). Puedes cambiar a Editar tabla para modificar valores y reevaluar, o pulsar Registrar gemelo."
                        except ValueError as exc:
                            st.session_state["live_result"] = None
                            st.session_state["live_error"] = str(exc)
                        st.rerun()
            # Nota de honestidad: el límite inferior no es monótono y el tribunal lo va a
            # ver. Los tres números salen de la caché, no están escritos a mano.
            _fila_hangar = windows[(windows["unit"] == _u_hangar) & (windows["cycle"] == _c_hangar)]
            _lo_min = float(_fila_hangar["lower"].min())
            _lo_max = float(_fila_hangar["lower"].max())
            _y_real = float(_fila_hangar["y_true"].mean())
            _curva_h = L.unit_curve(windows, _u_hangar).sort_values("cycle")
            _caida = _curva_h[_curva_h["lower_min"] < umbrales["apto"]]
            _ciclo_caida = int(_caida["cycle"].min()) if not _caida.empty else None
            _repunte = (
                _curva_h[(_curva_h["cycle"] > _ciclo_caida)
                         & (_curva_h["lower_min"] >= umbrales["apto"])]
                if _ciclo_caida is not None else _curva_h.iloc[0:0]
            )
            _ciclo_repunte = int(_repunte["cycle"].min()) if not _repunte.empty else None
            _nota_mono = (
                f" La trayectoria no es monótona — cae a inspección en el ciclo "
                f"{_ciclo_caida} y vuelve a apto en el {_ciclo_repunte} — porque el EMA "
                "causal (ADR-006) reduce pero no elimina los saltos de un predictor por "
                "ventanas. Se muestra tal cual."
                if _ciclo_caida is not None and _ciclo_repunte is not None else ""
            )
            st.caption(
                f"El caso crítico termina en el ciclo {_c_hangar}, donde el límite inferior "
                f"cruza el umbral de hangar ({umbrales['hangar']:.0f}) con {_y_real:.0f} ciclos "
                f"reales restantes: dentro del propio ciclo baja de {_lo_max:.1f} a {_lo_min:.1f}."
                + _nota_mono
            )

    def _explorar_por_ciclo() -> None:
        """Explorador por ciclo: genera un tramo y su estado."""
        with st.container(border=True):
            st.subheader("Explora por ciclo", icon=":material/timeline:")
            st.caption(
                "Elige un motor y un punto de su vida: se genera el tramo y se muestra "
                "el estado calculado. No se puntúa hasta pulsar \"Evaluar este tramo\"."
            )
            _exp_cols = st.columns(4)
            with _exp_cols[0]:
                _exp_unit = st.selectbox(
                    "Motor",
                    [11, 14, 15],
                    key="explorar_unit",
                    help="Unidad de la caché (11, 14 o 15).",
                )
            with _exp_cols[1]:
                _exp_len = st.selectbox(
                    "Largo del tramo",
                    [50, 300],
                    index=1,
                    key="explorar_len",
                    help="50 = una ventana; 300 = trayectoria con EMA suavizada.",
                )
            with _exp_cols[2]:
                _exp_mode = st.selectbox(
                    "Modo",
                    ["Posición relativa", "Ciclo final"],
                    key="explorar_mode",
                    help="Posición relativa: fracción de la vida (0-1). "
                         "Ciclo final: elige el ciclo exacto en que termina el tramo.",
                )
            with _exp_cols[3]:
                if _exp_mode == "Posición relativa":
                    _exp_pos = st.slider(
                        "Punto final (posición en la vida del motor)",
                        0.0, 1.0, 0.5, 0.01,
                        key="explorar_pos",
                        help="0.0 = inicio, 1.0 = final. El tramo termina en ese punto.",
                    )
                else:
                    _ciclos_disp = sorted(
                        int(c) for c in windows[windows["unit"] == _exp_unit]["cycle"].unique()
                    )
                    _exp_cycle = st.selectbox(
                        "Ciclo final",
                        _ciclos_disp,
                        key="explorar_cycle",
                        help="Ciclo exacto en que termina el tramo. "
                             "El tramo abarca los ciclos anteriores según el largo elegido.",
                    )
            try:
                if _exp_mode == "Posición relativa":
                    _exp_tab, _exp_meta = INF.example_window(
                        _exp_unit, _exp_pos, rows=_exp_len)
                else:
                    _exp_tab, _exp_meta = INF.window_ending_at(
                        _exp_unit, _exp_cycle, rows=_exp_len)
                _exp_pf = INF.preflight(_exp_tab)
                _exp_ok = bool(_exp_pf["ok"])
                st.session_state["explorar_table"] = _exp_tab
                st.session_state["explorar_meta"] = _exp_meta
                st.session_state["explorar_ok"] = _exp_ok
                st.session_state["explorar_avisos"] = _exp_pf["avisos"]
                _exp_end_cycle = int(_exp_meta["end_cycle"])
                _cached = windows[(windows["unit"] == _exp_unit)
                                  & (windows["cycle"] == _exp_end_cycle)]
                if not _cached.empty:
                    _exp_lower = float(_cached["lower"].iloc[-1])
                    _exp_state = L.classify(
                        _exp_lower, umbrales["apto"], umbrales["hangar"])
                else:
                    _exp_state = "sin referencia en caché"
                st.session_state["explorar_state"] = _exp_state
                _exp_err = None if _exp_ok else _exp_pf["error"]
            except ValueError as _exc:
                _exp_tab = None
                _exp_meta = None
                st.session_state["explorar_table"] = None
                st.session_state["explorar_meta"] = None
                st.session_state["explorar_ok"] = False
                st.session_state["explorar_state"] = "—"
                _exp_err = str(_exc)
            if _exp_err:
                st.error(_exp_err, icon=":material/error:")
            else:
                st.caption(
                    f"Tramo: ciclos {_exp_meta['start_cycle']}→{_exp_meta['end_cycle']} · "
                    f"{len(_exp_tab)} filas · estado estimado: **{_exp_state}**"
                )
                for _av in st.session_state.get("explorar_avisos", []) or []:
                    st.warning(_av, icon=":material/warning:")
                with st.expander("Ver tramo generado", expanded=False):
                    st.dataframe(
                        _exp_tab,
                        hide_index=True,
                        alt="Tramo generado para explorar por ciclo: ciclos y sensores.",
                    )
            if st.button(
                "Evaluar este tramo",
                key="explorar_evaluar",
                type="primary",
                icon=":material/play_arrow:",
                disabled=not st.session_state.get("explorar_ok", False),
            ):
                _tab = st.session_state.get("explorar_table")
                _meta = st.session_state.get("explorar_meta")
                if _tab is not None:
                    try:
                        st.session_state["live_engine_id"] = (
                            f"ESN-EXPLORAR-{_exp_unit}")
                        st.session_state["_editor_value"] = _tab
                        st.session_state["live_result"] = INF.score_table(
                            _tab, engine_id=f"ESN-EXPLORAR-{_exp_unit}")
                        st.session_state["live_meta"] = _meta
                        st.session_state["live_warnings"] = (
                            st.session_state.get("explorar_avisos", []) or [])
                        st.session_state["live_error"] = None
                        st.session_state["live_flash"] = (
                            f"Tramo explorado puntuado (ciclos "
                            f"{_meta['start_cycle']}→{_meta['end_cycle']}).")
                    except ValueError as _exc:
                        st.session_state["live_result"] = None
                        st.session_state["live_error"] = str(_exc)
                    st.rerun()

    def _unidad_nueva() -> None:
        """Tres rutas de entrada (ejemplo, tabla, CSV) y la puntuacion."""
        st.subheader("Puntúa un motor con datos que aportes tú", icon=":material/science:")
        st.caption(
            "Las tres rutas desembocan en el mismo validador y en la misma llamada al "
            "artefacto congelado. Una ventana son **50 muestras remuestreadas** (1 de cada "
            "100 registros), lo que son **~0,4 ciclos de vuelo**, no 50 lecturas seguidas "
            "ni 50 ciclos. Teclear 900 celdas no es "
            "viable: usa el ejemplo, pega un bloque desde Excel o sube el CSV."
        )

        mode = st.segmented_control(
            "Entrada de datos",
            ["Ejemplo del test set", "Editar tabla (pegar)", "Subir CSV"],
            default="Ejemplo del test set",
            key="live_mode",
            help="El ejemplo usa una ventana real de la caché; las otras dos aceptan tus datos.",
        )

        st.session_state.setdefault("live_engine_id", "ESN-DEMO-01")
        identidad = st.text_input(
            "Id del motor",
            key="live_engine_id",
            help="Se escribe en la orden y en el gemelo. Mínimo 3 caracteres.",
        )
        id_ok = len(str(identidad or "").strip()) >= T.MIN_ID
        if not id_ok:
            st.error(
                f"El id necesita al menos {T.MIN_ID} caracteres: se valida ahora, "
                "no al registrar.",
                icon=":material/rule:",
            )
        # ¿Está ya en la flota? Se responde aquí, antes de evaluar, para que la duda
        # «¿esto se ha añadido?» no obligue a bajar hasta la tarjeta de registro.
        try:
            _id_norm = T.normalizar_id(identidad) if id_ok else ""
        except ValueError:
            _id_norm = ""
        _en_flota = bool(_id_norm) and _id_norm in (st.session_state.get("twins") or {})
        if _id_norm:
            st.badge(
                "EN LA FLOTA" if _en_flota else "SIN REGISTRAR",
                icon=":material/check_circle:" if _en_flota else ":material/add_circle:",
                color="green" if _en_flota else "gray",
            )
        st.caption(
            "Paso 1 · trae los datos · Paso 2 · revisa el pre-vuelo de abajo · "
            "Paso 3 · evalúa · Paso 4 · regístralo en la tarjeta que sale bajo el "
            "resultado. El botón de evaluar solo se activa con los pasos 1 y 2 en verde."
        )
        # La plantilla se descarga desde el expander «Qué es cada columna», que ya
        # reutiliza `INF.template_csv()` (cabecera + 50 filas vacías) y ya esta
        # probado. Un segundo boton con la cabecera escrita a mano era un segundo
        # sitio donde arreglar el mismo contrato.

        def _on_preset_change():
            """Actualiza el motor demo al cambiar el preset de ejemplo."""
            _nuevo = st.session_state.get("live_demo_preset")
            if _nuevo in DEMO_PRESETS:
                st.session_state["live_engine_id"] = DEMO_PRESETS[_nuevo][3]
        if mode == "Ejemplo del test set":
            demo_nombre = st.selectbox(
                "Dataset demo", [*DEMO_PRESETS, DEMO_MANUAL], key="live_demo_preset",
                on_change=_on_preset_change,
                help=f"Cuatro casos reales o un tramo manual. Los presets cargan {INF.DEMO_ROWS} muestras; el manual carga el rango de ciclos que elijas.",
            )
            if demo_nombre == DEMO_MANUAL:
                _man_cols = st.columns(3)
                with _man_cols[0]:
                    _man_unit = st.selectbox(
                        "Motor", [11, 14, 15], key="manual_unit",
                        help="Unidad de la caché (11, 14 o 15).",
                    )
                _man_ciclos = INF.cycles_of_unit(_man_unit)
                with _man_cols[1]:
                    _man_start = st.selectbox(
                        "Ciclo inicial", _man_ciclos, index=0,
                        key=f"manual_start_{_man_unit}",
                        help="Primer ciclo del tramo manual.",
                    )
                with _man_cols[2]:
                    _man_end = st.selectbox(
                        "Ciclo final", _man_ciclos,
                        index=min(len(_man_ciclos) - 1, 5),
                        key=f"manual_end_{_man_unit}",
                        help="Último ciclo del tramo manual.",
                    )
                st.caption(
                    "Se cargan todas las filas de la caché entre ambos ciclos, "
                    "incluidos los extremos. Ajusta el rango hasta ver las muestras "
                    "que quieras; el pre-vuelo de abajo te dirá si llega al mínimo."
                )
        example_table, example_meta = INF.example_window(14, 0.55)
        if mode == "Ejemplo del test set" and "demo_nombre" in locals():
            if demo_nombre == DEMO_MANUAL:
                _man_ini, _man_fin = sorted((_man_start, _man_end))
                if (_man_ini, _man_fin) != (_man_start, _man_end):
                    st.caption(f"Rango invertido: se usa {_man_ini}→{_man_fin}.")
                example_table, example_meta = INF.window_between_cycles(
                    _man_unit, _man_ini, _man_fin)
            else:
                _du2, _dp2, _ciclo2, _ = DEMO_PRESETS[demo_nombre]
                if _ciclo2 is None:
                    example_table, example_meta = INF.example_window(
                        _du2, _dp2, rows=INF.DEMO_ROWS)
                else:
                    example_table, example_meta = INF.window_ending_at(
                        _du2, _ciclo2, rows=INF.DEMO_ROWS)
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
                         icon=":material/menu_book:", expanded=False):
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
                "accidente: la ventana toma 1 de cada 100 registros, así que varias "
                "muestras comparten ciclo y 50 muestras cubren ~0,4 vuelos."
            )
            st.download_button(
                "Descargar plantilla CSV (50 muestras remuestreadas vacías)",
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
                    f"`{example_meta['source']}`. Desmarca filas para excluirlas (mínimo 50 para puntuar)."
                )
                _edit = example_table.copy()
                _edit.insert(0, "usar", True)
                _cols_cfg = dict(number_columns)
                _cols_cfg["usar"] = st.column_config.CheckboxColumn("usar", help="Desmarca para no predecir esa fila.")
                _edited = st.data_editor(
                    _edit, hide_index=True, height=260, key="live_demo_grid",
                    column_config=_cols_cfg,
                    alt="Ventana demo seleccionable: marca qué filas se puntúan.",
                )
                _sel = pd.DataFrame(_edited)
                _usar = _sel["usar"].fillna(False).to_numpy(dtype=bool) if "usar" in _sel.columns else [True] * len(_sel)
                _filtrada = _sel.loc[_usar].drop(columns=[c for c in ["usar"] if c in _sel.columns], errors="ignore")
                st.caption(f"{int(_usar.sum())} de {len(_sel)} muestras seleccionadas → {max(0, int(_usar.sum()) - INF.window_size() + 1)} ventana(s).")
            preflight_ejemplo = INF.preflight(_filtrada)
            _preflight_panel(preflight_ejemplo)
            with st.form("live_eval_example"):
                submitted = st.form_submit_button(
                    "Evaluar unidad", type="primary", icon=":material/play_arrow:",
                    disabled=not id_ok,
                )
            if submitted:
                table_to_score = _filtrada
                data_meta = example_meta
        elif mode == "Editar tabla (pegar)":
            # `live_editor` es un `st.data_editor`: Streamlit declara su clave de
            # solo lectura y no se puede escribir desde un handler. La tabla se
            # guarda en `_editor_value` y se pasa como `data`; se mantiene entre
            # pasadas para que la rejilla no revierta al tocar una celda.
            _tabla_editor = st.session_state.get("_editor_value")
            if _tabla_editor is None:
                _tabla_editor = example_table
            edited = st.data_editor(
                _tabla_editor,
                num_rows="dynamic",
                hide_index=True,
                height=420,
                key="live_editor",
                column_config=number_columns,
            )
            draft = pd.DataFrame(edited) if edited is not None else example_table
            if "usar" in draft.columns:
                draft = draft[draft["usar"].fillna(False).astype(bool)].drop(columns=["usar"])
            state_rows = len(draft)
            state_windows = max(0, state_rows - INF.window_size() + 1)
            if state_rows > INF.UMBRAL_RECORTE_EDITOR:
                st.warning(
                    f"La rejilla va lenta con {L.fmt_miles(state_rows)} filas. Puedes recortar a las "
                    f"primeras {L.fmt_miles(INF.UMBRAL_RECORTE_EDITOR)} para editar con fluidez: "
                    "se puntuará lo visible y el recorte queda a la vista.",
                    icon=":material/speed:",
                )
                if st.button(
                    f"Recortar a {L.fmt_miles(INF.UMBRAL_RECORTE_EDITOR)} primeras filas",
                    icon=":material/content_cut:", key="recortar_editor",
                ):
                    cortada, _ = INF.limitar_filas(draft)
                    # Igual que arriba: la clave del `data_editor` es de solo lectura.
                    # Se guarda la tabla recortada y la rejilla la dibuja en la
                    # siguiente pasada.
                    st.session_state["_editor_value"] = cortada
                    st.session_state.pop("live_edit_fixed", None)
                    st.rerun()
            st.caption(
                f"**{state_rows} muestras** → {state_windows} ventana(s). Pega el bloque "
                "desde Excel/Sheets sobre la primera celda: la rejilla acepta una "
                "matriz de 50×19, y con más muestras puntúa todas las ventanas "
                "deslizantes. No cambies los encabezados."
            )
            _fija = st.session_state.get("live_edit_fixed")
            if (_fija is not None and list(_fija.get("cols", [])) == list(draft.columns)
                    and _fija.get("len") == len(draft)):
                draft = _fija["table"]
            pf_edit = INF.preflight(draft)
            if (not pf_edit["ok"] and "Orden de canales" in (pf_edit["error"] or "")
                    and set(draft.columns) == set(INF.required_columns())):
                if st.button("Reordenar al orden del dataset",
                             icon=":material/sort:", key="reorder_edit"):
                    st.session_state["live_edit_fixed"] = {
                        "cols": list(draft.columns), "len": len(draft),
                        "table": INF.reordenar_columnas(draft),
                    }
                    st.rerun()
            _preflight_panel(pf_edit)
            submitted = st.button(
                "Evaluar unidad", type="primary", icon=":material/play_arrow:",
                disabled=not (id_ok and pf_edit["ok"]), key="eval_editor",
            )
            if submitted:
                table_to_score = draft
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
                    # P1: valida el tamaño en bytes antes de parsear y acota la
                    # lectura con nrows=MAX_FILAS+1; si hay más filas, preflight
                    # lo rechaza con el mensaje de límite ya existente.
                    _n_bytes = B._size_bytes(upload)
                    if _n_bytes is not None:
                        B._check_bytes(_n_bytes, str(getattr(upload, "name", "CSV")))
                    uploaded_table = pd.read_csv(upload, nrows=INF.MAX_FILAS + 1)
                except Exception as exc:  # noqa: BLE001 - the message is shown to the user
                    st.error(f"No se pudo leer el CSV: {exc}", icon=":material/error:")
                if uploaded_table is not None:
                    st.caption(
                        f"{len(uploaded_table)} filas y {len(uploaded_table.columns)} columnas."
                    )
                    _fija_csv = st.session_state.get("live_csv_fixed")
                    if (_fija_csv is not None
                            and _fija_csv.get("name") == getattr(upload, "name", None)):
                        uploaded_table = _fija_csv["table"]
                    preflight_csv = INF.preflight(uploaded_table)
                    if (not preflight_csv["ok"]
                            and "Orden de canales" in (preflight_csv["error"] or "")
                            and set(uploaded_table.columns) == set(INF.required_columns())):
                        if st.button("Reordenar al orden del dataset",
                                     icon=":material/sort:", key="reorder_csv"):
                            st.session_state["live_csv_fixed"] = {
                                "name": getattr(upload, "name", None),
                                "table": INF.reordenar_columnas(uploaded_table),
                            }
                            st.rerun()
                        preflight_csv = INF.preflight(
                            st.session_state["live_csv_fixed"]["table"])
                        _preflight_panel(preflight_csv)
                        uploaded_table = st.session_state["live_csv_fixed"]["table"]
                    else:
                        _preflight_panel(preflight_csv)
                    submitted = st.button(
                        "Evaluar unidad", type="primary", icon=":material/play_arrow:",
                        disabled=not (id_ok and preflight_csv["ok"]), key="eval_csv",
                    )
                    if submitted:
                        table_to_score = uploaded_table
                        data_meta = {"source": upload.name}

        if submitted and table_to_score is not None:
            try:
                preflight = INF.preflight(table_to_score)
                if not preflight["ok"]:
                    raise ValueError(preflight["error"])
                st.session_state["live_result"] = INF.score_table(
                    table_to_score, engine_id=identidad)
                st.session_state["live_meta"] = data_meta
                st.session_state["live_warnings"] = preflight["avisos"]
                st.session_state["live_error"] = None
            except ValueError as exc:
                st.session_state["live_result"] = None
                st.session_state["live_warnings"] = []
                st.session_state["live_error"] = str(exc)

    def _resultado_en_vivo() -> None:
        """Tarjeta del resultado: banda, decision y registro del gemelo."""
        live_error = st.session_state.get("live_error")
        if live_error:
            st.error(live_error, title="No se pudo evaluar", icon=":material/rule:")
        for note in st.session_state.get("live_warnings") or []:
            st.warning(note, icon=":material/find_in_page:")

        live = st.session_state.get("live_result")
        if live:
            last = live["windows"].iloc[-1]
            # La pasada A se toma de `decision_en_vivo`, que decide con la invalidez
            # real de la banda y no con las cautelas de plausibilidad: esas se pintan
            # arriba como aviso al operador (2782), pero no son un dato imposible.
            _decision = UR.decision_en_vivo(live, umbrales)
            alertas_live = _decision["alertas"]
            traza_live = _decision["traza"]
            # MIA-3: notificacion n8n, punto de llamada unico. Solo si la
            # decision no es SIN_DECISION, deduplicado por fingerprint en la
            # sesion (cada rerun sin cambio de fingerprint no re-envia).
            # Notifican HANGAR, INSPECCION y APTO (APTO llega a Set log);
            # SIN_DECISION no hace nada. Dedupe solo si el POST fue ok.
            _fp_n8n = str(live["contract"].get("fingerprint") or "")
            _enviadas_n8n = set(st.session_state.get("n8n_enviadas") or set())
            # MIA-3: unidad real para n8n (no -1 de scoring en vivo).
            # live_meta trae `unit` de la caché (ej. 14 en Critico U14 ciclo 34);
            # unidad_simulada=-1 solo evita mezclar EMA y no es la unidad real.
            _meta_n8n = st.session_state.get("live_meta") or {}
            _unidad_real = (
                _meta_n8n.get("unit")
                if isinstance(_meta_n8n, dict) and _meta_n8n.get("unit") is not None
                else live["contract"].get("unidad_simulada")
            )
            if UN.debe_notificar(traza_live["decision"], _fp_n8n, _enviadas_n8n):
                _payload_n8n = UN.payload_desde_traza(
                    _decision, umbrales,
                    str(live["contract"].get("artefacto_sha256") or ""), _fp_n8n,
                    unidad=_unidad_real)
                _res_n8n = N8N.enviar_decision(traza_live["decision"], _payload_n8n)
                st.session_state["n8n_ultimo"] = {
                    "decision": str(traza_live["decision"]),
                    "ok": bool(isinstance(_res_n8n, dict) and _res_n8n.get("ok") is True),
                    "status": (_res_n8n.get("status") if isinstance(_res_n8n, dict) else None),
                    "en": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
                if isinstance(_res_n8n, dict) and _res_n8n.get("ok") is True:
                    _enviadas_n8n.add(_fp_n8n)
                    st.session_state["n8n_enviadas"] = _enviadas_n8n
            live_state = (traza_live["decision"] if traza_live["decision"] in L.STATE_LABELS
                          else L.NO_DATA)
            tone = {
                L.AIRWORTHY: "green",
                L.PREVENTIVE: "orange",
                L.AOG: "red",
                L.SIN_DECISION: "gray",
            }.get(live_state, "gray")
            with st.container(horizontal=True):
                st.metric("RUL p35 (conservadora)", f"{last['pred']:.1f}", "cuantil 0.35", border=True,
                          icon=":material/speed:", delta_color="off")
                st.metric("Límite inferior", f"{last['lower']:.1f}", "decide el estado",
                          border=True, icon=":material/trending_down:", delta_color="off")
                st.metric("Límite superior", f"{last['upper']:.1f}", "banda 90 %",
                          border=True, icon=":material/trending_up:", delta_color="off")
                st.metric("Ventanas puntuadas", f"{live['contract']['ventanas']}",
                          f"{live['contract']['filas']} filas", border=True,
                          icon=":material/layers:", delta_color="off")
                st.metric("SHA-256 del artefacto",
                          str(live["contract"]["artefacto_sha256"])[:12], "reproducibilidad",
                          border=True, icon=":material/fingerprint:", delta_color="off",
                          help="Huella del artefacto congelado que produjo esta "
                               "predicción. El contrato completo está en el expander "
                               "«Contrato y procedencia de esta evaluación».")
                st.metric("Contrato",
                          f"w{live['contract']['window']}/s{live['contract']['step']}",
                          "ventana/step", border=True,
                          icon=":material/description:", delta_color="off",
                          help="Ventana de filas remuestreadas y step usados en esta "
                               "evaluación. Fuera de este contrato la predicción no es "
                               "reproducible.")
            reglas_live = " → ".join(traza_live["usadas"])
            st.markdown(
                f"Con los umbrales en vigor ({threshold_apto:.0f} / {threshold_aog:.0f}): "
                f":{tone}-badge[{L.STATE_LABELS[live_state]}]"
                + (f" · reglas: `{reglas_live}`" if reglas_live else "")
            )
            if traza_live["porque"]:
                st.caption(" · ".join(traza_live["porque"]))
            # El registro va pegado al resultado: es el paso que se busca justo después
            # de evaluar. Antes vivía en un expander plegado al final de la sección.
            gemelos_previos = st.session_state.get("twins", {})
            motor_live = str(live["contract"].get("motor") or "").strip().upper()
            ya_existe = motor_live in gemelos_previos
            reemplazar = False
            with st.container(border=True):
                if ya_existe:
                    previo = gemelos_previos[motor_live]
                    verdad_previa = T.metricas_verdad(previo)
                    st.markdown(
                        f":green-badge[:material/check_circle: EN LA FLOTA] "
                        f"`{motor_live}` · {len(previo['serie'])} ventana(s) guardada(s)"
                        + (f" · RUL real {verdad_previa['rul_real']:.0f} ciclos"
                           if verdad_previa else "")
                    )
                    st.caption(
                        "Puntuar otra ventana del mismo motor no lo sobrescribe solo: "
                        "marca la casilla para sustituir la serie."
                    )
                    reemplazar = st.checkbox(
                        "Reemplazar la serie guardada (la RUL real se conserva)",
                        key="twin_replace",
                        help="Se sustituyen la serie, la huella y el contrato. La RUL real "
                             "es un hecho del motor, no de la ventana: no se borra.",
                    )
                else:
                    st.markdown(
                        f":gray-badge[:material/add_circle: SIN REGISTRAR] "
                        f"`{motor_live}` no está en la flota."
                    )
                    st.caption(
                        "Regístralo para que aparezca en el muro y en «Gemelos "
                        "registrados». Su estado se recalcula con los umbrales en vigor; "
                        "la serie no se vuelve a puntuar."
                    )
                if st.button(
                    f"Reemplazar gemelo `{motor_live}`" if ya_existe else "Registrar en la flota",
                    icon=":material/sync:" if ya_existe else ":material/add_circle:",
                    key="twin_add", type="primary",
                ):
                    try:
                        gemelo = T.make_twin(
                            live["contract"].get("motor") or "",
                            live,
                            source=str((st.session_state.get("live_meta") or {}).get(
                                "source", "entrada manual")),
                            banda=INF.BANDA_ARTEFACTO,
                            correccion=INF.CORRECCION_NINGUNA,
                            umbrales=umbrales,
                            fingerprint_value=live["contract"].get("fingerprint", ""),
                        )
                        st.session_state["twins"] = T.registrar(
                            st.session_state.get("twins", {}), gemelo,
                            reemplazar=reemplazar)
                        _guardar_registros()
                        _log(f"Gemelo {gemelo['id']} registrado.")
                    except ValueError as exc:
                        st.error(str(exc), title="No se pudo registrar", icon=":material/rule:")
                    else:
                        st.session_state["twin_flash"] = (
                            f"Gemelo `{gemelo['id']}` actualizado en la flota."
                            if reemplazar else
                            f"Gemelo `{gemelo['id']}` registrado en la flota.")
                        st.rerun()


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
                    annotation_font_color=ROSE_SOFT,
                )
                fig_live.update_layout(**chart_layout(height=340, hovermode="x unified"))
                style_axes(fig_live, x_title="Ciclo de vuelo", y_title="RUL (ciclos)")
                st.plotly_chart(
                    fig_live, theme=None, config=CHART_CONFIG,
                    alt="Estimación de RUL y banda conformal para la unidad aportada por el usuario.",
                )

            with st.expander(
                "Contrato y procedencia de esta evaluación", icon=":material/receipt_long:"
            ):
                contract = live["contract"]
                st.markdown(
                    f"**artefacto** `{contract['artefacto']}` · "
                    f"**SHA-256** `{contract['artefacto_sha256']}`"
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
                    "Las 50 muestras son la rejilla remuestreada (1 de cada 100 registros del "
                    "dataset), lo que son ~0,4 ciclos de vuelo, no 50 lecturas de 1 Hz. Con otro "
                    "muestreo la predicción queda "
                    "fuera de contrato aunque los números sean válidos."
                )

            st.caption(
                "**Sin ground truth**: esta unidad no trae RUL real, así que no se declara "
                "RMSE ni MAE. La banda es una cota conservadora calibrada sobre los motores "
                "de desarrollo; el sesgo de vida alta (`RUL ≈ 63 − ciclo`) también aplica aquí."
            )

            if live_state == L.AOG:
                order_live = INF.live_work_order(
                    live, st.session_state.get("live_meta"), threshold_apto, threshold_aog,
                    alertas=alertas_live,
                )
                st.download_button(
                    "Descargar orden de esta unidad (JSON)",
                    data=json.dumps(order_live, ensure_ascii=False, indent=2),
                    file_name="orden_mantenimiento_unidad_externa.json",
                    mime="application/json",
                    icon=":material/download:",
                    type="primary",
                )

    def _sandbox_de_estres() -> None:
        """Sandbox de estres en vivo."""
        with st.expander("Sandbox de estrés · perturba el motor y mira el pipeline reaccionar",
                         icon=":material/tune:", expanded=_vista_tribunal):
            st.caption(
                "El tribunal mueve el deslizador y la app re-puntúa el tramo con el "
                "artefacto congelado y re-decide con el motor oficial. No se reentrena "
                "nada: lo que cambia es la entrada."
            )
            _sandbox_estres(ctx)

    def _shap_waterfall() -> None:
        """Explicabilidad local con SHAP waterfall."""
        with st.container(border=True):
            st.subheader("Explicabilidad local · SHAP waterfall",
                         icon=":material/psychology:")
            st.caption(
                "Por qué el modelo predice este RUL para el motor seleccionado. "
                "TreeExplainer exacto sobre el LightGBM del híbrido (no reentrena). "
                "El waterfall muestra la contribución de cada feature a la predicción. "
                "El SHAP explica solo la rama árbol (LightGBM), no el BiLSTM, el stacking "
                "ni la EMA causal."
            )
            _wf_unit = int(st.session_state.get("unit", 14))
            shap_panel(_wf_unit, suffix="casos")

    _lote_de_motores()

    _demo_crit = A.estado_demo()

    _u_hangar = int(_demo_crit["unidad"])

    _c_hangar = int(_demo_crit["ciclo"])

    DEMO_PRESETS = INF.demo_presets(_u_hangar, _c_hangar)

    _demo_un_clic()

    _explorar_por_ciclo()

    _unidad_nueva()

    _resultado_en_vivo()

    _sandbox_de_estres()

    _shap_waterfall()
