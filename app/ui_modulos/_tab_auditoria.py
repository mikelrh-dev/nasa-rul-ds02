"""Pestaña Auditoría extraída de `dashboard_ds02` (dashboard-split-monolito, PR5 task 2.4).

Pure structural move: the body of `_tab_auditoria` is byte-identical to the
pre-split dashboard version except for the parameter list and the
dashboard-globals resolution below. No behavior, metric or threshold change.

Dashboard-owned globals (`per_unit`/`provenance`/`windows`/`units`/`curves`/
`alarms`/`unidades_vistas`/`global_metrics`/`critical_mae`/`manifest`/`cycle`/
thresholds/`aplicar_reglas` and the helpers `chart_layout`/`style_axes`/
`_sha256_cached`/`_informe_pdf_cached`) are passed by the dashboard, which
keeps the module-level `windows`/`telemetry`/`frame_cache` hot path (ttl=3600,
corregir+decidir) byte-identical. The fallback import of `dashboard_ds02`
is lazy, inside the fragment, and only fills in what a standalone caller
omitted (never at import time, so there is no circular import, and no
TensorFlow import: every import here is pandas/numpy/plotly + the rules layer
via `ui_*`).

`frame_cache` (ttl=3600), the ola-2 SHAP cache and the PDF
`artefacto_sha256` signature are untouched: this module only reads the
already-decided data it is handed, exactly as the inline fragment did.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

try:
    import ui_data_loader as L  # noqa: E402
except ImportError:  # pragma: no cover - import-style fallback
    from app import ui_data_loader as L  # type: ignore[no-redef]

# Design tokens: same hex values as `dashboard_ds02` (see its design-tokens
# section). Kept as literals here so this module needs no dashboard import
# for colors; chart/badge helpers are still dashboard-owned (passed in).
INK = "#e8eef7"
SKY = "#38bdf8"
GREEN = "#34d399"
ROSE = "#f87171"

__all__ = ["_tab_auditoria"]


@st.fragment
def _tab_auditoria(per_unit=None, provenance=None, chart_layout=None,
                   style_axes=None, windows=None, units=None, curves=None,
                   threshold_aog=None, global_metrics=None, critical_mae=None,
                   manifest=None, cycle=None, alarms=None,
                   unidades_vistas=None, threshold_apto=None,
                   aplicar_reglas=None, sha256_cached=None,
                   informe_pdf_cached=None) -> None:
    if (per_unit is None or provenance is None or chart_layout is None
            or style_axes is None or windows is None or units is None
            or curves is None or threshold_aog is None
            or global_metrics is None or critical_mae is None
            or manifest is None or cycle is None or alarms is None
            or unidades_vistas is None or threshold_apto is None
            or aplicar_reglas is None or sha256_cached is None
            or informe_pdf_cached is None):
        # Fallback import (PR5): dashboard_ds02 owns the frame/cache globals,
        # the per-unit metrics (per_unit/alarms/curves/...), the threshold/
        # rule state and the chart/PDF helpers. Lazy, inside the fragment,
        # to avoid a circular top-level import: the dashboard imports this
        # module, so this module must not import the dashboard at import
        # time.
        try:
            import dashboard_ds02 as _dash  # type: ignore
        except ImportError:  # pragma: no cover - import-style fallback
            from app import dashboard_ds02 as _dash  # type: ignore
        if per_unit is None:
            per_unit = _dash.per_unit
        if provenance is None:
            provenance = _dash.provenance
        if chart_layout is None:
            chart_layout = _dash.chart_layout
        if style_axes is None:
            style_axes = _dash.style_axes
        if windows is None:
            windows = _dash.windows
        if units is None:
            units = _dash.units
        if curves is None:
            curves = _dash.curves
        if threshold_aog is None:
            threshold_aog = _dash.threshold_aog
        if global_metrics is None:
            global_metrics = _dash.global_metrics
        if critical_mae is None:
            critical_mae = _dash.critical_mae
        if manifest is None:
            manifest = _dash.manifest
        if cycle is None:
            cycle = _dash.cycle
        if alarms is None:
            alarms = _dash.alarms
        if unidades_vistas is None:
            unidades_vistas = _dash.unidades_vistas
        if threshold_apto is None:
            threshold_apto = _dash.threshold_apto
        if aplicar_reglas is None:
            aplicar_reglas = _dash.aplicar_reglas
        if sha256_cached is None:
            sha256_cached = _dash._sha256_cached
        if informe_pdf_cached is None:
            informe_pdf_cached = _dash._informe_pdf_cached
    # Aliases preserving the original body identifiers: the inline fragment
    # used `_sha256_cached` and `_informe_pdf_cached` unqualified.
    _sha256_cached = sha256_cached
    _informe_pdf_cached = informe_pdf_cached
    # ------------------------------------------------------------------- tab 4

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

    # Las tres hipótesis van plegadas: el tribunal ve primero la métrica limpia
    # (la barra del motor 14) y abre la justificación solo si la pregunta llega.
    with st.expander(
        "¿Por qué el motor 14? Hipótesis probadas y descartadas",
        icon=":material/help_center:",
    ):
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
                "`docs/informes/informe-2026-10-21-p0-p1-prior-de-vida.md`: el sesgo del meta cambió −0.93 / −0.03 / "
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
        st.subheader("Calidad del modelo", icon=":material/insights:")
        st.caption(
            "Métricas de calidad, no de decisión: cuánto se equivoca el modelo, no "
            "lo que decide. Viven aquí porque son para el tribunal, no para el "
            "operador de taller."
        )
        with st.container(horizontal=True):
            st.metric(
                "Macro-RMSE", f"{global_metrics['macro_rmse']:.2f} ciclos",
                f"ponderado {global_metrics['rmse']:.2f}", border=True,
                delta_color="off", icon=":material/balance:",
                help="El macro-RMSE da el mismo peso a cada motor; el ponderado lo da a cada ventana.")
            st.metric(
                "MAE en zona crítica", f"{critical_mae:.2f} ciclos",
                f"RUL real < {threshold_aog:.0f}", border=True,
                delta_color="off", icon=":material/target:",
                help="Error absoluto medio donde de verdad se decide el mantenimiento.")

    with st.expander("Procedencia verificable", icon=":material/fingerprint:"):
        st.caption(
            "Huella SHA-256 del ensemble congelado, copiada del manifiesto que acompaña a "
            "la caché. La UI no recalcula el artefacto: lo identifica."
        )
        st.code(provenance["artifact"]["ensemble_sha256"], language=None)
        st.markdown(
            f"**ensemble** `{provenance['artifact'].get('ensemble', 'models/ensemble.joblib')}` · "
            f"**manifest** `{provenance['artifact'].get('manifest', 'models/ds02_manifest.json')}`"
        )
        st.caption(
            "Para verificarlo en local: `python -c \"import hashlib;print(hashlib.sha256"
            "(open('models/ensemble.joblib','rb').read()).hexdigest())\"`."
        )
        with st.container(horizontal=True):
            st.metric(
                "Ventanas en caché",
                f"{provenance['counts']['windows']:,}",
                f"generada {provenance['generated_at'][:10]}",
                border=True, delta_color="off", icon=":material/dataset:")
        st.caption(
            f"Contrato: ventana de {provenance['source']['window']} muestras, "
            f"step={provenance['source']['step']}. La caché va a step=2 y la vía "
            f"en vivo a step=1, así que no coinciden bit a bit, y el punto está "
            f"suavizado con un EMA causal por motor. Documentado, no reconciliado."
        )

    with st.expander("Contrato congelado vs. cálculo en vivo", icon=":material/difference:"):
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
        st.markdown("**SHA-256 del ensemble**")
        st.code(provenance["artifact"]["ensemble_sha256"], language=None)
        st.caption(
            "64 caracteres hexadecimales. Es la huella del artefacto congelado, no la de "
            "la caché."
        )
        # Auditoria criptografica on-demand: hashea el .keras en disco y lo
        # compara con el sello registrado. El hash va por `@st.cache_data`
        # (clave path/tamaño/mtime): re-pulsar sin cambio en disco no relee.
        if st.button("Auditar hashes del artefacto", icon=":material/verified:",
                     key="btn_audit_hashes"):
            _path_keras = os.path.join(L.ROOT, "models", "bilstm_ds02.keras")
            try:
                _st_keras = os.stat(_path_keras)
                _digest_keras = _sha256_cached(
                    _path_keras, int(_st_keras.st_size), int(_st_keras.st_mtime_ns)
                )
            except OSError:
                _digest_keras = None
            st.session_state["audit_hashes"] = {"bilstm_ds02.keras": _digest_keras}
        _audit = st.session_state.get("audit_hashes")
        if _audit:
            _esp_bilstm = (provenance.get("artifact") or {}).get("bilstm_sha256")
            _leido_bilstm = _audit.get("bilstm_ds02.keras")
            if _leido_bilstm is not None and _esp_bilstm and _leido_bilstm == _esp_bilstm:
                st.success("bilstm_ds02.keras: hash coincide con el manifest.",
                           icon=":material/check_circle:")
            elif _leido_bilstm is not None:
                st.error(f"bilstm_ds02.keras: discrepancia "
                         f"({_leido_bilstm[:12]} vs {_esp_bilstm[:12]})",
                         icon=":material/cancel:")
            else:
                st.warning("No se pudo hashear bilstm_ds02.keras.",
                           icon=":material/warning:")
        # El sello estaba en pantalla y nadie lo comprobaba: si el bundle se
        # reentrena y se sustituye sin reconstruir `app/cache/`, la superficie
        # sigue pintando predicciones bajo el sello viejo. Se mira en cada
        # render y **solo** se avisa cuando discrepan: con el sello en regla no
        # aparece nada, de modo que el camino verde no mueve ni un widget.
        _sello = L.artifact_hash_check(provenance)
        if _sello["checked"] and not _sello["ok"]:
            st.warning(
                f"La caché no corresponde al artefacto que hay en disco: el sello "
                f"registrado es `{_sello['esperado'][:12]}` y el leído es "
                f"`{_sello['leido'][:12]}`. Las cifras salen de `app/cache/`; "
                f"reconstrúyela con `python scripts/build_ui_cache.py`.",
                icon=":material/warning:",
            )
        elif not _sello["checked"]:
            st.caption(
                "No se pudo comprobar el sello del artefacto contra "
                "`models/ensemble.joblib`."
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

    with st.container(border=True):
        st.subheader("Informe de auditoría", icon=":material/picture_as_pdf:")
        st.caption(
            "Un PDF con las dos tablas de arriba —precisión por tramo y alarma vs. "
            "verdad— más la huella del artefacto congelado y los umbrales en vigor. "
            "Es la constancia firmable de cómo se calculó lo que se decide hoy."
        )
        # El PDF solo se genera al pulsar: no se paga en cada render. La
        # construcción va por `@st.cache_data` (umbrales + SHA + firma de caché).
        # La firma es por HASH de contenido (h5 + windows + rows), no por
        # conteos: dos cachés con 6196 ventanas pero distinto contenido no
        # comparten PDF.
        _source = provenance.get("source") or {}
        _counts = provenance.get("counts") or {}
        _curves_sig = ";".join(
            f"{int(u)}:{alarms[u][0]}:{alarms[u][1]}" for u in unidades_vistas
        )
        _manifest_sig = (
            f"{manifest.get('format_version', '')}:"
            f"{manifest.get('code_version', '')}:"
            f"{provenance.get('format_version', '')}:"
            f"{provenance.get('generated_at', '')}"
        )
        _windows_sig = (
            f"{provenance['artifact']['ensemble_sha256']}:"
            f"{_source.get('h5_sha256', '')}:"
            f"{_counts.get('windows_sha256', '')}:"
            f"{_counts.get('rows_sha256', '')}:"
            f"{critical_mae:.6f}:{cycle}:{_curves_sig}:{_manifest_sig}"
        )
        if st.button(
            "Generar informe (PDF)",
            icon=":material/picture_as_pdf:",
            key="btn_gen_pdf",
            help="Genera el PDF de auditoría con los umbrales en vigor. Solo se "
                 "genera al pulsar; luego queda cacheado para la descarga.",
        ):
            st.session_state["_pdf_generado"] = True
        if st.session_state.get("_pdf_generado"):
            try:
                _pdf_auditoria = _informe_pdf_cached(
                    float(threshold_apto), float(threshold_aog),
                    float(critical_mae),
                    str(provenance["artifact"]["ensemble_sha256"]),
                    _windows_sig,
                    bool(aplicar_reglas),
                    _manifest_sig,
                )
            except Exception as exc:  # pragma: no cover - defensa ante fpdf ausente
                st.warning(
                    f"No se pudo generar el informe PDF ({type(exc).__name__}). "
                    "Las tablas de arriba siguen siendo la fuente.",
                    icon=":material/error:",
                )
                st.session_state.pop("_pdf_generado", None)
            else:
                st.download_button(
                    "Descargar informe de auditoría (PDF)",
                    data=_pdf_auditoria,
                    file_name=f"informe_auditoria_ds02_ciclo{cycle}.pdf",
                    mime="application/pdf",
                    icon=":material/download:",
                    help="Congela las tablas de auditoría y la huella del artefacto.",
                )
