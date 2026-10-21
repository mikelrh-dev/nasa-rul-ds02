"""Split-conformal prediction intervals for the RUL ensemble.

A point prediction is not deployable on its own: maintenance decides on a range.
The intervals here are *asymmetric* on purpose. The NASA penalty is asymmetric
too (over-estimating RUL costs `exp(d/10)`, under-estimating `exp(-d/13)`), so a
symmetric band would spend half its width on the cheap side.

Calibration is split-conformal: the band comes from residual quantiles measured
on rows the meta-learner never saw, grouped by predicted RUL so the width can
grow where the error grows. Coverage is then *reported*, not assumed — with only
three test engines a global coverage figure is a weak claim, so the caller is
expected to publish it per engine.
"""
from __future__ import annotations

import numpy as np

DEFAULT_EDGES = (0.0, 25.0, 50.0, 75.0, np.inf)


def _bin_index(pred: np.ndarray, edges) -> np.ndarray:
    edges = np.asarray(edges, dtype=np.float64)
    # `searchsorted(side='right') - 1` puts a value exactly on an edge in the
    # bin that starts there, which is what a reader expects from "[25, 50)".
    return np.clip(np.searchsorted(edges, pred, side="right") - 1, 0, len(edges) - 2)


def fit_conformal(y_true, pred, target: float = 0.90, edges=DEFAULT_EDGES,
                  min_rows: int = 100, debias: bool = False) -> dict:
    """Fit a per-bin asymmetric band from signed residuals `y_true - pred`.

    Bins with fewer than `min_rows` observations fall back to the global
    quantiles, so a sparse tail does not produce a band drawn from a handful of
    points.

    `debias=True` subtracts the per-bin median residual before taking the
    quantiles, so the band measures *dispersion* instead of absorbing the point
    estimate's level bias. On this project the split models under-predict at high
    RUL, which makes both residual quantiles negative there and collapses the
    band to one side; the de-biased variant keeps it two-sided. It is a
    diagnostic, not the shipped calibration: a de-biased band stops covering
    exactly where the model is biased, which is information, not a defect.
    """
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    pred = np.asarray(pred, dtype=np.float64).ravel()
    if y_true.shape != pred.shape:
        raise ValueError(f"shape mismatch: y {y_true.shape} vs pred {pred.shape}")

    alpha = (1.0 - float(target)) / 2.0
    resid = y_true - pred
    global_shift = float(np.median(resid)) if debias else 0.0
    global_lo, global_hi = np.quantile(resid - global_shift, [alpha, 1.0 - alpha])
    idx = _bin_index(pred, edges)

    bins = []
    for b in range(len(np.asarray(edges)) - 1):
        mask = idx == b
        n = int(mask.sum())
        if n >= min_rows:
            shift = float(np.median(resid[mask])) if debias else 0.0
            lo, hi = np.quantile(resid[mask] - shift, [alpha, 1.0 - alpha])
            source = "bin"
        else:
            lo, hi = global_lo, global_hi
            source = "global"
        lo_edge, hi_edge = float(edges[b]), float(edges[b + 1])
        bins.append({
            "index": b,
            # `inf` is not valid JSON; the open upper bound is written as null.
            "pred_range": [lo_edge, None if np.isinf(hi_edge) else hi_edge],
            "n": n,
            "q_low": round(float(lo), 4),
            "q_high": round(float(hi), 4),
            "source": source,
        })

    return {
        "method": "split-conformal, per predicted-RUL bin, asymmetric"
                  + (", level-debiased" if debias else ""),
        "debias": bool(debias),
        "target_coverage": float(target),
        "alpha_each_side": round(float(alpha), 4),
        "edges": [None if np.isinf(float(e)) else float(e) for e in edges],
        "bins": bins,
        "global_quantiles": [round(float(global_lo), 4), round(float(global_hi), 4)],
        "n_calibration": int(len(y_true)),
    }


def apply_conformal(pred, calib: dict):
    """Turn point predictions into `(lower, upper)` bounds.

    The bounds never cross the point estimate: a quantile band that excludes its
    own centre would be a bug, not a caveat.
    """
    pred = np.asarray(pred, dtype=np.float64).ravel()
    edges = np.asarray(calib["edges"], dtype=np.float64)
    idx = _bin_index(pred, edges)
    lower = np.empty_like(pred)
    upper = np.empty_like(pred)
    for b, spec in enumerate(calib["bins"]):
        mask = idx == b
        if not mask.any():
            continue
        lower[mask] = pred[mask] + spec["q_low"]
        upper[mask] = pred[mask] + spec["q_high"]
    lower = np.minimum(lower, pred)
    upper = np.maximum(upper, pred)
    # RUL is non-negative, so the lower bound is clipped at zero — but only where
    # the point estimate is itself non-negative, otherwise the clip would put the
    # bound above its own centre and break `lower <= pred <= upper`.
    lower = np.where(pred >= 0.0, np.clip(lower, 0.0, None), lower)
    return lower, upper


def empirical_coverage(y_true, lower, upper) -> float:
    """Fraction of rows whose truth falls inside the band."""
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    return float(np.mean((y_true >= lower) & (y_true <= upper)))
