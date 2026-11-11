"""Sandbox de estres extracted from `dashboard_ds02` (dashboard-split-monolito, PR2 task 2.1).

Pure structural move: the body of `_sandbox_estres` is byte-identical to the
pre-split dashboard version except for the parameter list and the
dashboard-globals resolution below. No behavior, metric or threshold change.

Receives the single `AppCtx` built by the dashboard: `windows`, `telemetry`,
`units`, `cache_sha`, `sandbox_puntua_cached`, `chart_layout`, `style_axes`
and `st_badge_estado` are read from it. `_sandbox_puntua_cached` is owned by
`app/lib/sandbox.py`; this module only reuses it through the context, so the
scoring/preflight logic is not duplicated here and the module never imports
the dashboard.

`frame_cache` (ttl=3600), the SHAP cache and the PDF `artefacto_sha256`
signature are untouched.
"""
from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from app.lib import ui_data_loader as L

from app.lib.context import AppCtx

# Design tokens: dueno `theme.py` (el dashboard tambien los importa de ahi).
# `theme` no importa el dashboard: no hay ciclo en el import.
from app.lib.theme import SKY, AMBER, GREEN, ROSE

__all__ = ["_sandbox_estres"]


@st.fragment
def _sandbox_estres(ctx: AppCtx) -> None:
    windows = ctx.windows
    telemetry = ctx.telemetry
    units = ctx.units
    _cache_sha = ctx.cache_sha
    _sandbox_puntua_cached = ctx.sandbox_puntua_cached
    chart_layout = ctx.chart_layout
    style_axes = ctx.style_axes
    st_badge_estado = ctx.st_badge_estado
    """Sandbox de estrés: perturbar la caché y ver el pipeline reaccionar en vivo.

    El tribunal mueve el deslizador y la app re-puntúa el tramo con el artefacto
    congelado (`ui_inference.score_table`) y re-decide con el motor oficial
    (`mia/reglas.py` vía `ui_rules.decidir_ventanas`). No se reentrena nada y no
    se escribe en `models/` ni en `src/`.

    La perturbación es sintética y se declara: el split-conformal se calibró sobre
    datos reales, así que romper la intercambiabilidad quita la garantía del 90 %.
    La banda se sigue dibujando — el límite inferior sigue gobernando la decisión
    (ADR-008) — pero con la leyenda degradada y el aviso visible.

    Con la deriva a 0 % el tramo se dibuja desde la caché y el modelo no se carga:
    la app está documentada y testeada para arrancar sin el artefacto de 2,3 GB.
    Solo una deriva distinta de cero paga la carga (una sola vez, `@st.cache_resource`).

    Los umbrales se leen de `session_state` y no del global del módulo: el fragment
    se re-ejecuta solo, y un valor congelado en la pasada anterior quedaría obsoleto
    si el tribunal cambiara la política en la pestaña del taller.
    """
    _preset_sbx = str(st.session_state.get("preset", "Normal"))
    _umb_sbx = {
        "apto": float(st.session_state.get(f"th_apto_{_preset_sbx}", L.DEFAULT_AIRWORTHY)),
        "hangar": float(st.session_state.get(f"th_aog_{_preset_sbx}", L.DEFAULT_AOG)),
    }
    _u_sbx = st.segmented_control(
        "Unidad del tramo", units, default=14, key="sbx_unit",
        help="Motores del conjunto de test DS02 (partición fija [11, 14, 15]).",
    )
    _sensor_sbx = st.selectbox(
        "Sensor a perturbar",
        ["T48", "T24"],
        index=0,
        key="sbx_sensor",
        help="T48 (salida HPT) por defecto; T24 (salida LPC) es el segundo sensor "
             "del sandbox (app-ux-bundle-fix).",
    )
    _deriva_pct = st.slider(
        f"Deriva térmica acumulada en {_sensor_sbx}", min_value=0, max_value=30, value=0,
        step=1, format="%d%%", key="sbx_deriva",
        help=f"Porcentaje que {_sensor_sbx} (canal N-CMAPSS) gana "
             "al final del tramo respecto a su valor en caché. Con 0 % el tramo es "
             "la caché tal cual; cualquier otro valor es una intervención sintética.",
    )
    _deriva = _deriva_pct / 100.0
    _perturbado = _deriva > 0.0

    # El tramo va del primer ciclo puntuado al primero en que la caché ya manda al
    # hangar: es el mismo recorrido que cuenta el modo historia. Sale de la caché,
    # no de una constante.
    _cur_sbx = L.unit_curve(windows, int(_u_sbx))
    _c_inicio = int(_cur_sbx["cycle"].min())
    _bajo_hangar = _cur_sbx[_cur_sbx["lower_min"] < _umb_sbx["hangar"]]
    _c_fin = (int(_bajo_hangar["cycle"].min()) if not _bajo_hangar.empty
              else int(_cur_sbx["cycle"].max()))
    if _c_fin <= _c_inicio:
        st.caption(
            "Este motor no cruza el umbral de hangar en la caché: no hay transición "
            "que enseñar en el tramo."
        )
        return
    _tramo = telemetry[(telemetry["unit"] == int(_u_sbx))
                       & (telemetry["cycle"] >= _c_inicio)
                       & (telemetry["cycle"] <= _c_fin)].reset_index(drop=True)
    _muestras = len(_tramo)

    if not _perturbado:
        # Con 0 % el tramo es la caché tal cual y se dibuja sin cargar el modelo: la
        # app está documentada y testeada para arrancar sin el artefacto (2,3 GB).
        # El estado se clasifica con el mismo `L.classify` que usa el cargador.
        _cur = (_cur_sbx[["cycle", "pred", "lower", "upper", "lower_min"]]
                .sort_values("cycle").reset_index(drop=True))
        # `unit_curve` devuelve toda la vida del motor; el sandbox enseña el tramo.
        _cur = _cur[_cur["cycle"] <= _c_fin].reset_index(drop=True)
        _cruce = _cur[_cur["lower_min"] < _umb_sbx["hangar"]]
        _cruce_ciclo = int(_cruce["cycle"].min()) if not _cruce.empty else None
        _ultima = _cur.iloc[-1]
        _estado = L.classify(float(_ultima["lower"]), _umb_sbx["apto"], _umb_sbx["hangar"])
        _ventanas = int(((windows["unit"] == int(_u_sbx))
                         & (windows["cycle"] >= _c_inicio)
                         & (windows["cycle"] <= _c_fin)).sum())
    else:
        # P1.4 · la inferencia sale del helper cacheado (`_sandbox_puntua_cached`):
        # mismo (unit, deriva, umbrales) → caché, sin repetir preflight/puntuación.
        _ok, _error, _avisos, _dec, _ventanas = _sandbox_puntua_cached(
            int(_u_sbx), int(_deriva_pct),
            float(_umb_sbx["apto"]), float(_umb_sbx["hangar"]), _cache_sha,
            _sensor_sbx, windows=windows, telemetry=telemetry,
        )
        if not _ok:
            st.error(_error, icon=":material/rule:")
            return
        _pf = {"avisos": list(_avisos)}
        _cur = (_dec.groupby("cycle", as_index=False)
                .agg(pred=("pred", "mean"), lower=("lower", "mean"),
                     upper=("upper", "mean"), lower_min=("lower", "min"))
                .sort_values("cycle").reset_index(drop=True))
        _cruce = _cur[_cur["lower_min"] < _umb_sbx["hangar"]]
        _cruce_ciclo = int(_cruce["cycle"].min()) if not _cruce.empty else None
        _fin_dec = _dec[_dec["cycle"] == _c_fin]
        _ultima = (_fin_dec.loc[_fin_dec["lower"].idxmin()] if not _fin_dec.empty
                   else _dec.iloc[-1])
        _estado = str(_ultima["decision"])

    _band_name = ("Banda proyectada (fuera de garantía conformal 90 %)"
                  if _perturbado else "Banda conformal (90 %)")
    _dash = "dot" if _perturbado else "solid"
    _band_color = ROSE if _perturbado else SKY
    _fill = "rgba(248,113,113,0.10)" if _perturbado else "rgba(56,189,248,0.10)"

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=_cur["cycle"], y=_cur["upper"], mode="lines", name=_band_name,
        line=dict(width=1, color=_band_color, dash=_dash),
        hovertemplate="ciclo %{x}<br>superior %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_cur["cycle"], y=_cur["lower"], mode="lines", name=" ",
        line=dict(width=1, color=_band_color, dash=_dash),
        fill="tonexty", fillcolor=_fill,
        hovertemplate="ciclo %{x}<br>inferior %{y:.1f}<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=_cur["cycle"], y=_cur["pred"], mode="lines", name="RUL predicha",
        line=dict(width=2, color=SKY),
        hovertemplate="ciclo %{x}<br>RUL %{y:.1f}<extra></extra>",
    ))
    fig.add_hline(y=_umb_sbx["apto"], line_color=GREEN, line_width=1, line_dash="dash",
                  annotation_text=f"apto ≥ {_umb_sbx['apto']:.0f}",
                  annotation_font_color=GREEN, annotation_font_size=11)
    fig.add_hline(y=_umb_sbx["hangar"], line_color=ROSE, line_width=1, line_dash="dash",
                  annotation_text=f"hangar < {_umb_sbx['hangar']:.0f}",
                  annotation_font_color=ROSE, annotation_font_size=11)
    if _cruce_ciclo is not None:
        fig.add_vline(x=_cruce_ciclo, line_color=AMBER, line_width=1, line_dash="dot",
                      annotation_text=f"hangar en {_cruce_ciclo}",
                      annotation_font_color=AMBER, annotation_font_size=11)
    fig.update_layout(**chart_layout(height=360))
    style_axes(fig, x_title="Ciclo de vuelo", y_title="ciclos de RUL")
    _alt = (f"Curva de RUL de la unidad {int(_u_sbx)} entre los ciclos {_c_inicio} y "
            f"{_c_fin}, con una deriva sintética del {_deriva_pct:.0f} % en {_sensor_sbx}: el "
            f"límite inferior cruza el umbral de hangar en el ciclo {_cruce_ciclo} y el "
            f"estado al final del tramo es {L.STATE_LABELS.get(_estado, _estado)}."
            if _cruce_ciclo is not None and _perturbado else
            f"Curva de RUL de la unidad {int(_u_sbx)} entre los ciclos {_c_inicio} y "
            f"{_c_fin} sin cruce al umbral de hangar; el estado al final del tramo es "
            f"{L.STATE_LABELS.get(_estado, _estado)}."
            if _cruce_ciclo is None else
            f"Curva de RUL de la unidad {int(_u_sbx)} entre los ciclos {_c_inicio} y "
            f"{_c_fin} leída de la caché: el límite inferior cruza el umbral de hangar "
            f"en el ciclo {_cruce_ciclo} y el estado al final del tramo es "
            f"{L.STATE_LABELS.get(_estado, _estado)}.")
    st.plotly_chart(fig, use_container_width=True, alt=_alt)

    _m1, _m2 = st.columns(2)
    _m1.metric("RUL p35 al final del tramo", f"{_ultima['pred']:.1f} ciclos",
               border=True, icon=":material/schedule:")
    _m2.metric("Cruce a hangar",
               f"ciclo {_cruce_ciclo}" if _cruce_ciclo else "no cruza en el tramo",
               border=True, icon=":material/warning:")
    st_badge_estado(_estado)
    st.caption(
        f"Tramo de caché ciclos {_c_inicio}→{_c_fin}: {_muestras} muestras "
        f"remuestreadas, {_ventanas} ventanas. "
        + ("Leído de la caché, sin cargar el modelo: al mover el deslizador el "
           "pipeline corre en vivo y la banda pierde la garantía conformal."
           if not _perturbado else
           "Puntuado en vivo con el artefacto congelado; la banda se degrada a "
           "proyectada porque el split-conformal perdió la intercambiabilidad.")
    )
    if _perturbado:
        for _aviso in _pf["avisos"]:
            st.warning(_aviso, icon=":material/find_in_page:")
        st.warning(
            f"Deriva sintética del {_deriva_pct:.0f} % sobre {_sensor_sbx}: la banda pierde la "
            "garantía conformal del 90 % — el split-conformal se calibró sobre datos "
            "reales y una intervención sintética rompe la intercambiabilidad. El "
            "límite inferior sigue gobernando la decisión (ADR-008), pero su cobertura "
            "ya no está garantizada.",
            icon=":material/warning:",
        )
