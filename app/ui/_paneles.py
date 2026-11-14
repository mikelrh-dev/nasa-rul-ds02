"""Paneles y tarjetas compartidas por las pestañas (dueño único de la UI).

Viven aquí, y no en el entrypoint, para que `app/entrypoints/dashboard_ds02.py`
sea un orquestador delgado: construye el `AppCtx` y monta las pestañas. Cada
función recibe lo que necesita como parámetro; ninguna lee globales del
dashboard.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app.lib import twin as T
from app.lib import ui_data_loader as L
from app.lib.theme import CHART_CONFIG, chart_layout, style_axes

__all__ = ["preflight_panel", "shap_panel", "tarjetas_cache", "tarjetas_gemelos"]


def preflight_panel(pf: dict) -> None:
    """Resumen del pre-vuelo: lo que se sabe sin cargar el modelo.

    Se pinta antes de pulsar «Evaluar» para que un CSV mal formado se vea en
    milisegundos y no después de cargar TensorFlow.
    """
    if not pf["ok"]:
        st.error(pf["error"], title="La tabla no se puede puntuar",
                 icon=":material/rule:")
        return
    with st.container(horizontal=True):
        st.metric("Filas", L.fmt_miles(pf['filas']), border=True, delta_color="off",
                  icon=":material/table_rows:")
        st.metric("Ventanas", L.fmt_miles(pf['ventanas']), border=True, delta_color="off",
                  icon=":material/layers:")
        st.metric("Huella", pf["fingerprint"][:8], "SHA-256 de la tabla",
                  border=True, delta_color="off", icon=":material/fingerprint:")
    for aviso in pf["avisos"]:
        st.warning(aviso, icon=":material/find_in_page:")


def shap_panel(unit: int, suffix: str = "motor") -> None:
    """Panel SHAP unificado: top features + waterfall Plotly.

    Sustituye a los dos bloques SHAP duplicados (Motor y Casos nuevos): una
    sola definición, dos call sites con claves de botón distintas.
    """
    try:
        from app.lib import ui_shap as USH
    except ImportError:
        st.info(
            "SHAP no instalado: `app.lib.ui_shap` no está en el entorno. Instala el "
            "paquete con `pip install shap` y recarga. El resto de la app "
            "sigue funcionando sin explicabilidad.",
            icon=":material/info:",
        )
        return

    if st.button(
        "Calcular SHAP para este motor",
        icon=":material/psychology:",
        key=f"btn_shap_{suffix}",
        help="Calcula las contribuciones exactas del LightGBM del híbrido "
             "(TreeExplainer) para la última ventana del motor.",
    ):
        try:
            _shap_df = USH.shap_top_features(int(unit), top_k=10)
        except ImportError:
            st.info(
                "SHAP no instalado: falta el paquete `shap` (`pip install shap`). "
                "Sin él no se puede explicar la predicción.",
                icon=":material/info:",
            )
            return
        except Exception as _e:
            st.warning(f"No se pudo calcular SHAP: {_e}", icon=":material/warning:")
            return
        if _shap_df is not None and not _shap_df.empty:
            import plotly.express as px

            _fig_shap = px.bar(
                _shap_df.sort_values("abs_shap"),
                x="abs_shap", y="feature", orientation="h",
                labels={"abs_shap": "mean |SHAP| (ciclos RUL)",
                        "feature": "feature"},
                title=f"Top-10 features · motor {int(unit)}",
            )
            _fig_shap.update_layout(**chart_layout(height=360))
            st.plotly_chart(
                _fig_shap, config=CHART_CONFIG, use_container_width=True,
                alt=f"Top-10 contribuciones SHAP del motor {int(unit)}.",
            )
            st.dataframe(_shap_df, use_container_width=True, hide_index=True)
            try:
                _wf_fig = USH.shap_waterfall_fig(int(unit), max_display=12)
            except ImportError:
                st.info(
                    "SHAP no instalado: falta el paquete `shap` (`pip install shap`).",
                    icon=":material/info:",
                )
                return
            except Exception as _e2:
                st.warning(f"No se pudo generar el waterfall: {_e2}",
                           icon=":material/warning:")
                return
            _wf_fig.update_layout(**chart_layout(height=420))
            style_axes(_wf_fig, x_title="feature", y_title="contribución")
            st.plotly_chart(
                _wf_fig, config=CHART_CONFIG, use_container_width=True,
                alt=f"SHAP waterfall del motor {int(unit)}.",
            )
        else:
            st.info("Sin datos suficientes para calcular SHAP.",
                    icon=":material/info:")


def tarjetas_gemelos(gemelos: dict, unidades_vistas: list, umbrales: dict,
                     altas_fn, slug_motor) -> list[dict]:
    """Una tarjeta por gemelo registrado, con el estado recalculado hoy.

    El gemelo es flota registrada, pero su clave es el `engine_id` y su serie
    vive en el gemelo, no en la caché: por eso `snapshot` (que sale de `frame`)
    no lo veía. Sin esta lista, registrar un motor y volver al muro no mostraba
    nada nuevo.

    El estado no se guarda: se deriva de la serie guardada con los umbrales en
    vigor (`twin.ciclo_a_ciclo`), igual que la tabla de gemelos.
    """
    tarjetas = []
    usadas = {f"muro_gemelo_{int(u)}" for u in unidades_vistas}
    _matriculas_altas = {a["matricula"] for a in altas_fn()}
    for gemelo_id, gemelo in gemelos.items():
        # El alta ya aparece en `tarjetas_cache` via `frame_con_altas`: no se
        # duplica en el muro (sigue en Gemelos registrados). Sin este filtro,
        # 1 Incorporar = 2 tarjetas (3->5).
        if gemelo_id in _matriculas_altas:
            continue
        curva = T.ciclo_a_ciclo(gemelo, umbrales)
        if curva.empty:
            continue
        # La sparkline del muro dibuja `lower`; la curva del gemelo la llama
        # `lower_media`. Se homogenea aqui para que el muro no pregunte de donde
        # salio la tarjeta.
        curva["lower"] = curva["lower_media"]
        ultima = curva.iloc[-1]
        clave = f"muro_gemelo_{slug_motor(gemelo_id)}"
        # Dos ids que slugen igual ("A B" y "A_B") no pueden compartir boton:
        # Streamlit rechaza la clave duplicada y cae la pagina entera.
        while clave in usadas:
            clave += "_"
        usadas.add(clave)
        tarjetas.append({
            "orden_unidad": (1, str(gemelo_id)),
            "etiqueta": str(gemelo_id),
            "estado": str(ultima["decision"]),
            "pred": float(ultima["pred"]),
            "lower": float(ultima["lower_min"]),
            "curva": curva,
            "ciclo_tarjeta": int(ultima["cycle"]),
            "clave_boton": clave,
            "gemelo": str(gemelo_id),
        })
    return tarjetas


def tarjetas_cache(snapshot: pd.DataFrame, curves: dict, unidades_vistas: list,
                   cycle: int, etiqueta_unidad, slug_motor) -> list[dict]:
    """Una tarjeta por unidad de la flota visible: caché y altas."""
    tarjetas = []
    for u in unidades_vistas:
        fila = snapshot[snapshot["unit"] == u].iloc[0]
        _scored = fila["scored_cycle"]
        tarjetas.append({
            "orden_unidad": (0, int(u)),
            "etiqueta": etiqueta_unidad(float(u)),
            "estado": str(fila["state"]),
            "pred": fila["pred"],
            "lower": fila["lower"],
            "curva": curves[u],
            "ciclo_tarjeta": int(_scored) if pd.notna(_scored) else int(cycle),
            "clave_boton": f"muro_gemelo_{int(u)}",
            "gemelo": None,
            "unidad": int(u),
        })
    return tarjetas
