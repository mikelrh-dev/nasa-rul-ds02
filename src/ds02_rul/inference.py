"""Raw window extraction for inference.

`HybridStackingEnsemble.predict` takes *raw* `(n, window, 18)` windows and does
its own scaling and residualisation internally, using the objects stored in the
artifact. That means inference never needs the training-time preprocessing
bundle — only the raw channels, which is exactly what a live feed provides.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def raw_windows(W, Xs, units, cycles, window: int = 50, step: int = 1):
    """Cut raw `(n, window, n_channels)` windows aligned to each unit's cycles.

    Returns `(X_raw, cycles_end, units_end, meta)` where the last three describe
    the window's final row, matching the training-time target convention.
    """
    W = np.asarray(W, dtype=np.float32)
    Xs = np.asarray(Xs, dtype=np.float32)
    units = np.asarray(units)
    cycles = np.asarray(cycles, dtype=np.float64)
    X_full = np.hstack([W, Xs])

    out, out_units, out_cycles, meta = [], [], [], []
    for unit in np.unique(units):
        mask = units == unit
        Xu = X_full[mask]
        cu = cycles[mask]
        # Sort stable por (unit, cycle): si la entrada viene desordenada, las
        # ventanas se cortan en orden temporal y no con el orden de llegada.
        order = np.argsort(cu, kind="stable")
        Xu = Xu[order]
        cu = cu[order]
        n = len(Xu)
        if n < window:
            continue
        for i in range(0, n - window + 1, step):
            out.append(Xu[i : i + window])
            out_units.append(float(unit))
            out_cycles.append(float(cu[i + window - 1]))
            meta.append((float(unit), float(cu[i + window - 1]), int(i)))

    frame = pd.DataFrame(meta, columns=["unit", "cycle", "start_index"])
    return (
        np.asarray(out, dtype=np.float32),
        np.asarray(out_cycles, dtype=np.float64),
        np.asarray(out_units, dtype=np.float64),
        frame,
    )


def windows_for_unit(W, Xs, units, cycles, unit: float, window: int = 50, step: int = 1):
    """Raw windows belonging to a single engine, ordered by cycle."""
    X, cyc, uni, meta = raw_windows(W, Xs, units, cycles, window, step)
    mask = uni == float(unit)
    if not mask.any():
        raise ValueError(
            f"unit {unit} has no {window}-row window; available units: "
            f"{sorted(set(uni.tolist()))}"
        )
    order = np.argsort(cyc[mask], kind="stable")
    return X[mask][order], cyc[mask][order], uni[mask][order], meta[mask].reset_index(drop=True)

