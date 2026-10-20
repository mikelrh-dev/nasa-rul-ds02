"""Leakage-free preprocessing and window extraction.

Two things changed relative to the original notebook:

1. `fit_preprocessing` is only ever called on the *fit units*. The scalers, the
   degree-2 polynomial basis and the 14 residual ridges never see the holdout
   unit, so the holdout is clean end to end and not merely clean for the model
   weights.
2. The cycle counter is optional (`use_cycle`) and there is a per-engine
   healthy-baseline offset (`use_baseline_delta`), so the honest ablation can be
   measured rather than asserted.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

from .residualizer import SensorResidualizer

BASE_CYCLES = 3  # "first three cycles of life" define the healthy baseline


def fit_preprocessing(W_raw: np.ndarray, Xs_raw: np.ndarray) -> dict:
    """Fit the scalers and the per-sensor residual ridges on ONE split only.

    Parameters
    ----------
    W_raw, Xs_raw : np.ndarray
        Regime and sensor matrices of the fit units (never the holdout/test).

    Returns
    -------
    dict with `scaler`, `scaler_w`, `poly`, `ridges`, `res_scaler`, `residualizer`.
    """
    X_full = np.hstack([W_raw, Xs_raw])
    scaler = StandardScaler().fit(X_full)
    scaler_w = StandardScaler().fit(W_raw)

    W_scaled = scaler_w.transform(W_raw)
    poly = PolynomialFeatures(degree=2, include_bias=False).fit(W_scaled)
    P = poly.transform(W_scaled)

    ridges = []
    res = np.zeros_like(Xs_raw, dtype=np.float64)
    for j in range(Xs_raw.shape[1]):
        ridge = Ridge(alpha=1.0).fit(P, Xs_raw[:, j])
        ridges.append(ridge)
        res[:, j] = Xs_raw[:, j] - ridge.predict(P)

    res_scaler = StandardScaler().fit(res)
    return {
        "scaler": scaler,
        "scaler_w": scaler_w,
        "poly": poly,
        "ridges": ridges,
        "res_scaler": res_scaler,
        "residualizer": SensorResidualizer(poly, ridges, res_scaler),
    }


def per_unit_baseline(res: np.ndarray, units: np.ndarray, cycles: np.ndarray) -> dict:
    """Mean residualised sensor vector over each unit's first `BASE_CYCLES` cycles.

    Causal by construction: it reads only that engine's own early life, which in
    a real deployment is exactly the healthy-state calibration we would record.
    """
    out = {}
    for unit in np.unique(units):
        mask = units == unit
        early = mask & (cycles <= BASE_CYCLES)
        if not early.any():
            early = mask & (cycles <= np.min(cycles[mask]))
        out[unit] = res[early].mean(axis=0)
    return out


def build_windows(
    W_raw: np.ndarray,
    Xs_raw: np.ndarray,
    y: np.ndarray,
    units: np.ndarray,
    cycles: np.ndarray,
    prep: dict,
    window_size: int = 50,
    step: int = 1,
    use_cycle: bool = True,
    use_baseline_delta: bool = False,
    baselines: dict | None = None,
) -> dict:
    """Cut `(window, channels)` sequences and the tabular window summary.

    Returns a dict with `X_seq`, `X_tab`, `y`, `meta`, `X_raw`, `baselines`.
    `X_raw` keeps the 18 raw channels so a reloaded artifact can be exercised
    through its public `predict` contract.
    """
    n_op = W_raw.shape[1]
    scaler = prep["scaler"]
    scaler_w = prep["scaler_w"]

    X_full = np.hstack([W_raw, Xs_raw])
    X_scaled = scaler.transform(X_full)
    W_scaled = scaler_w.transform(W_raw)
    res = prep["residualizer"].transform(W_scaled, Xs_raw)

    if use_baseline_delta:
        if baselines is None:
            baselines = per_unit_baseline(res, units, cycles)
        res = res.copy()
        for unit, baseline in baselines.items():
            mask = units == unit
            if mask.any():
                res[mask] = res[mask] - baseline

    seq_list, tab_list, raw_list, y_list, meta_list = [], [], [], [], []

    for unit in np.unique(units):
        mask = units == unit
        S = X_scaled[mask]
        R = res[mask]
        Wm = W_scaled[mask]
        Raw = X_full[mask]
        y_u = y[mask]
        c_u = cycles[mask]
        n = len(S)
        if n < window_size:
            continue

        for i in range(0, n - window_size + 1, step):
            win = S[i : i + window_size]
            if use_cycle:
                cyc = np.full((window_size, 1), c_u[i + window_size - 1] / 100.0)
                seq = np.hstack([win, cyc])
            else:
                seq = win

            op = Wm[i : i + window_size]
            xs = R[i : i + window_size]
            blocks = [
                op.mean(axis=0),
                op[-1],
                xs.mean(axis=0),
                xs[-1],
                xs.std(axis=0),
                xs[-10:].mean(axis=0),
                xs[-1] - xs[0],
                xs[-5:].mean(axis=0) - xs[:5].mean(axis=0),
            ]
            if use_cycle:
                blocks.insert(0, np.array([c_u[i + window_size - 1] / 100.0]))

            seq_list.append(seq.astype(np.float32))
            tab_list.append(np.hstack(blocks).astype(np.float32))
            raw_list.append(Raw[i : i + window_size].astype(np.float32))
            y_list.append(float(y_u[i + window_size - 1]))
            meta_list.append((unit, float(c_u[i + window_size - 1])))

    meta = pd.DataFrame(meta_list, columns=["unit", "cycle"])
    return {
        "X_seq": np.asarray(seq_list, dtype=np.float32),
        "X_tab": np.asarray(tab_list, dtype=np.float32),
        "y": np.asarray(y_list, dtype=np.float32),
        "meta": meta,
        "X_raw": np.asarray(raw_list, dtype=np.float32),
        "baselines": baselines if use_baseline_delta else None,
        "n_op": n_op,
        "use_cycle": use_cycle,
    }
