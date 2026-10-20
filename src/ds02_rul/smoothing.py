"""Causal per-unit exponential moving average.

Wear is monotone in cycle, but a window-by-window prediction is not. The EMA
removes that discontinuity noise without looking forward: `adjust=False` makes
the recursion depend only on the current and past samples, and the per-unit
grouping keeps two engines from bleeding into each other.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def causal_ema_by_unit(pred, units, cycles, span: int = 5) -> np.ndarray:
    """Smooth `pred` within each unit, over rows ordered by cycle.

    Parameters
    ----------
    pred : array-like of shape (n,)
    units : array-like of shape (n,)
    cycles : array-like of shape (n,)
    span : int
        Pandas `ewm` span. `span=5` corresponds to alpha = 2 / (5 + 1).

    Returns
    -------
    np.ndarray of shape (n,), same ordering as the input.
    """
    pred = np.asarray(pred, dtype=np.float64)
    units = np.asarray(units)
    cycles = np.asarray(cycles)
    out = np.zeros_like(pred)
    for unit in np.unique(units):
        idx = np.where(units == unit)[0]
        idx = idx[np.argsort(cycles[idx], kind="stable")]
        out[idx] = pd.Series(pred[idx]).ewm(span=span, adjust=False).mean().values
    return out
