"""SHAP explainability for the frozen DS02 bundle (model B).

Computes TreeExplainer attributions over the LightGBM tabular branch of the
hybrid ensemble.  The 93 tabular features are derived from raw cached rows
using the same preprocessing that produced the bundle, so the explanation is
consistent with what the model actually consumed.

Nothing is written: the model is read from ``models/``, the data from
``app/cache/``.  Results are held by ``st.cache_data`` so repeated renders
do not recompute.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(APP_DIR)
SRC = os.path.join(ROOT, "src")

if SRC not in sys.path:
    sys.path.insert(0, SRC)

import ui_data_loader as L  # noqa: E402
import ui_inference as INF  # noqa: E402


def _derive_tabular_features(table: pd.DataFrame, ensemble) -> np.ndarray:
    """Derive the 93 tabular features from a raw input table.

    Replicates ``src/ds02_rul.features.build_windows`` for a single window
    ending at the last row of ``table``.  Returns shape (1, 93).
    """
    frame = INF.validate_table(table)
    order = INF.channel_order()
    n_op = len(L.get_provenance()["source"]["op_names"])

    W_raw = frame[order[:n_op]].to_numpy(dtype=np.float64)
    Xs_raw = frame[order[n_op:]].to_numpy(dtype=np.float64)
    cycles = frame["cycle"].to_numpy(dtype=np.float64)

    window_size = ensemble.window_size
    if len(frame) < window_size:
        raise ValueError(
            f"Se necesitan al menos {window_size} filas y llegaron {len(frame)}."
        )

    # Preprocessing (same as build_windows)
    X_full = np.hstack([W_raw, Xs_raw])
    X_scaled = ensemble.scaler.transform(X_full)
    W_scaled = ensemble.scaler_w.transform(W_raw)
    res = ensemble.residualizer.transform(W_scaled, Xs_raw)

    # Last window
    i = len(frame) - window_size
    op = W_scaled[i : i + window_size]
    xs = res[i : i + window_size]
    cyc = cycles[i + window_size - 1] / 100.0

    blocks = [
        np.array([cyc]),
        op.mean(axis=0),
        op[-1],
        xs.mean(axis=0),
        xs[-1],
        xs.std(axis=0),
        xs[-10:].mean(axis=0),
        xs[-1] - xs[0],
        xs[-5:].mean(axis=0) - xs[:5].mean(axis=0),
    ]
    X_tab = np.hstack(blocks).astype(np.float32).reshape(1, -1)
    return X_tab


@st.cache_data(show_spinner="Calculando SHAP (una sola vez)…", ttl=3600)
def shap_top_features(unit: int, top_k: int = 10) -> pd.DataFrame:
    """Top-k features by mean |SHAP| for the given unit's last window.

    Returns a DataFrame with columns ``feature`` and ``mean_abs_shap``.
    """
    import shap

    ensemble = INF.get_ensemble()
    lgb = ensemble.lgb_standalone

    # Build a single window from cached rows
    rows_frame = L.get_rows()
    frame = rows_frame[rows_frame["unit"] == int(unit)].reset_index(drop=True)
    if len(frame) < ensemble.window_size:
        raise ValueError(f"Unidad {unit} no tiene suficientes filas.")

    # Use the last window_size rows
    chunk = frame.iloc[-ensemble.window_size :].copy()
    table = chunk[["cycle"] + INF.channel_order()].reset_index(drop=True)

    X_tab = _derive_tabular_features(table, ensemble)

    # Feature names from block structure (93 features total)
    op_names = L.get_provenance()["source"]["op_names"]
    sensor_names = L.get_provenance()["source"]["sensor_names"]
    feature_names = ["cyc_norm"]
    for name in op_names:
        feature_names.append(f"op_mean_{name}")
    for name in op_names:
        feature_names.append(f"op_last_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_mean_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_last_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_std_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_last10_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_delta_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_trend_{name}")

    assert len(feature_names) == X_tab.shape[1], (
        f"Expected {X_tab.shape[1]} names, got {len(feature_names)}"
    )

    # TreeExplainer (exact for LightGBM)
    explainer = shap.TreeExplainer(lgb)
    sv = explainer.shap_values(X_tab)
    sv = np.asarray(sv).reshape(-1)

    # Top-k by mean |SHAP|
    media = np.abs(sv)
    order_idx = np.argsort(media)[::-1][:top_k]
    result = pd.DataFrame({
        "feature": [feature_names[i] for i in order_idx],
        "shap_value": [float(sv[i]) for i in order_idx],
        "abs_shap": [float(media[i]) for i in order_idx],
    })
    return result


def _shap_claves() -> tuple[str, str]:
    """(solver_sha, rows_sha) que sellan la clave del waterfall cacheado.

    `solver` es la huella del artefacto (rama LightGBM) y `rows` la del
    parquet de filas: si el bundle o la caché se regeneran, la clave cambia
    y el TreeExplainer se re-ejecuta en vez de servir un waterfall viejo.
    """
    prov = L.get_provenance()
    solver = str(prov.get("artifact", {}).get("ensemble_sha256", ""))
    rows = str(prov.get("counts", {}).get("rows_sha256", ""))
    return solver, rows


def _con_claves(solver_sha: str, rows_sha: str) -> tuple[str, str]:
    """Rellena los shas que falten desde provenance (para la clave de caché)."""
    if solver_sha and rows_sha:
        return solver_sha, rows_sha
    _s, _r = _shap_claves()
    return solver_sha or _s, rows_sha or _r


def shap_waterfall_data(
    unit: int, solver_sha: str = "", rows_sha: str = ""
) -> tuple[np.ndarray, np.ndarray, float, list[str]]:
    """Return SHAP values, feature values, base value, and feature names for a waterfall.

    Used for per-prediction explanation in the dashboard. Envuelve al
    `_shap_waterfall_data_cached` (ttl 3600), así que la clave es siempre
    (unit, solver_sha, rows_sha) aunque el llamador no pase los shas.
    """
    solver_sha, rows_sha = _con_claves(solver_sha, rows_sha)
    return _shap_waterfall_data_cached(unit, solver_sha, rows_sha)


@st.cache_data(
    show_spinner="Calculando SHAP waterfall…", ttl=3600
)
def _shap_waterfall_data_cached(
    unit: int, solver_sha: str, rows_sha: str
) -> tuple[np.ndarray, np.ndarray, float, list[str]]:
    """Cuerpo cacheado: evita el 2º TreeExplainer (~1,7 s) si `shap_top_features`
    ya explicó la ventana (misma `unit`/solver/rows)."""
    import shap

    ensemble = INF.get_ensemble()
    lgb = ensemble.lgb_standalone

    rows_frame = L.get_rows()
    frame = rows_frame[rows_frame["unit"] == int(unit)].reset_index(drop=True)
    chunk = frame.iloc[-ensemble.window_size :].copy()
    table = chunk[["cycle"] + INF.channel_order()].reset_index(drop=True)

    X_tab = _derive_tabular_features(table, ensemble)
    op_names = L.get_provenance()["source"]["op_names"]
    sensor_names = L.get_provenance()["source"]["sensor_names"]
    feature_names = ["cyc_norm"]
    for name in op_names:
        feature_names.append(f"op_mean_{name}")
    for name in op_names:
        feature_names.append(f"op_last_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_mean_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_last_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_std_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_last10_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_delta_{name}")
    for name in sensor_names:
        feature_names.append(f"xs_trend_{name}")

    explainer = shap.TreeExplainer(lgb)
    sv = explainer.shap_values(X_tab)
    sv = np.asarray(sv).reshape(-1)
    base = float(np.asarray(explainer.expected_value).reshape(-1)[0])

    return sv, X_tab.reshape(-1), base, feature_names


def shap_waterfall_fig(
    unit: int, max_display: int = 12, solver_sha: str = "", rows_sha: str = ""
):
    """Plotly waterfall figure for the given unit's last window.

    The dashboard renders this figure directly: no file on disk, no fixed temp
    path, and the chart inherits the app's dark theme via `chart_layout`.
    Envuelve al `_shap_waterfall_fig_cached` (ttl 3600): la clave es
    (unit, max_display, solver_sha, rows_sha).
    """
    solver_sha, rows_sha = _con_claves(solver_sha, rows_sha)
    return _shap_waterfall_fig_cached(
        unit, max_display, solver_sha, rows_sha
    )


@st.cache_data(show_spinner="Calculando SHAP waterfall…", ttl=3600)
def _shap_waterfall_fig_cached(
    unit: int, max_display: int, solver_sha: str, rows_sha: str
):
    """Cuerpo cacheado del waterfall (misma clave, sin TreeExplainer extra)."""
    import plotly.graph_objects as go

    sv, values, base, names = shap_waterfall_data(unit, solver_sha, rows_sha)
    order_idx = np.argsort(np.abs(sv))[::-1][:max_display]
    feats = [names[i] for i in order_idx]
    contribs = [float(sv[i]) for i in order_idx]
    fig = go.Figure(
        go.Waterfall(
            name=f"SHAP waterfall · motor {int(unit)}",
            orientation="v",
            measure=["relative"] * len(contribs),
            x=feats,
            y=contribs,
            totals=[float(base)],
            waterfallgap=0.25,
            hovertemplate="%{x}<br>contribución %{y:.2f}<extra></extra>",
        )
    )
    return fig


def shap_waterfall_png(unit: int, out_path: str | None = None) -> str:
    """Generate a SHAP waterfall plot PNG for the given unit's last window.

    Returns the path to the saved PNG.  Uses matplotlib Agg backend. When no
    `out_path` is given, a private temp file is created with `tempfile`
    (never a fixed shared path).
    """
    import tempfile

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import shap

    if out_path is None:
        fd, out_path = tempfile.mkstemp(suffix=".png", prefix="shap_waterfall_")
        import os as _os

        _os.close(fd)
    sv, values, base, names = shap_waterfall_data(unit)

    explanation = shap.Explanation(
        values=sv,
        base_values=base,
        data=values,
        feature_names=names,
    )

    shap.plots.waterfall(explanation, max_display=12, show=False)
    fig = plt.gcf()
    fig.tight_layout()
    fig.savefig(out_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return out_path
