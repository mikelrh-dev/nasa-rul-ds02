"""P0 - is the high-RUL bias caused by sampling density, or by engine life?

Controlled experiment on `dev`, no model is refit and no test row is read.

Two engines (2 and 5) are re-windowed at two densities:

* **natural** - every 100th raw row, i.e. the density the shipped models were
  trained and scaled on (~114-125 rows/cycle);
* **distorted** - a stride chosen so the engine shows ~20.6 rows/cycle, which is
  unit 14's density. A 50-row window then spans ~2.4 flight cycles instead of
  ~0.43.

Everything else is held fixed: same scaler (fitted on the fit units at stride
100), same BiLSTM, same LightGBM, same meta-learners. So any change in the bias
at `y > 65` is attributable to the row spacing alone. What survives at natural
density is attributable to the engine's life length.

Run:  python scripts/p0_density_control.py
"""
from __future__ import annotations

import h5py
import numpy as np

from ds02_rul.data import resolve_ds02
from ds02_rul.persistence import load_ensemble

WINDOW = 50
STEP = 2
TARGET_DENSITY = 20.6  # rows/cycle, unit 14 at stride 100
UNITS = (2.0, 5.0, 10.0)


def engine_rows(fh, unit: float):
    """Return (row_slice, cycles) for one engine, read from the raw HDF5."""
    A = fh["A_dev"][:]
    masks = A[:, 0] == unit
    idx = np.where(masks)[0]
    if idx.size == 0:
        raise KeyError(f"unit {unit} not in A_dev")
    if idx[-1] - idx[0] + 1 != idx.size:
        raise AssertionError(f"unit {unit} is not stored contiguously")
    cycles = A[idx, 1]
    if np.any(np.diff(cycles) < 0):
        raise AssertionError(f"unit {unit} cycles are not monotone")
    return idx[0], idx[-1] + 1, cycles


def build(fh, unit, step_raw, ens):
    """Windows for one engine sampled every `step_raw` rows."""
    start, stop, cycles = engine_rows(fh, unit)
    rows = np.arange(start, stop, step_raw)
    cyc = cycles[rows - start]
    W = fh["W_dev"][rows]
    Xs = fh["X_s_dev"][rows]
    y = fh["Y_dev"][rows].ravel()

    X, yw, cw = [], [], []
    for i in range(0, len(rows) - WINDOW + 1, STEP):
        X.append(np.hstack([W[i : i + WINDOW], Xs[i : i + WINDOW]]))
        yw.append(float(y[i + WINDOW - 1]))
        cw.append(float(cyc[i + WINDOW - 1]))
    X = np.asarray(X, dtype=np.float32)
    yw = np.asarray(yw)
    cw = np.asarray(cw)

    Xs_scaled = ens.scaler.transform(
        X.reshape(-1, X.shape[2]).astype(np.float64)
    ).reshape(X.shape).astype(np.float32)
    p_lstm = np.asarray(
        ens._resolve_model().predict(
            ens._sequence(Xs_scaled, cw, ens.bilstm_model.input_shape), verbose=0
        )
    ).ravel()
    p_lgb = np.asarray(ens.lgb_standalone.predict(ens._tabular(Xs_scaled, cw))).ravel()
    Z = np.column_stack([p_lstm, p_lgb])
    p_meta = 0.5 * np.asarray(ens.ridge_meta.predict(Z)).ravel() + 0.5 * np.asarray(
        ens.lgb_meta.predict(Z)
    ).ravel()
    return {
        "n": len(yw),
        "cycles_span": WINDOW * step_raw / np.mean(np.diff(np.unique(cyc)))
        if len(np.unique(cyc)) > 1
        else np.nan,
        "y": yw,
        "p_lstm": p_lstm,
        "p_lgb": p_lgb,
        "p_meta": p_meta,
    }


def report(tag, res):
    y, hi = res["y"], res["y"] > 65
    lo = ~hi
    rmse = lambda a, b: float(np.sqrt(np.mean((a - b) ** 2)))  # noqa: E731
    print(
        f"{tag:26s} n={res['n']:5d}  "
        f"| y>65 n={hi.sum():4d} y={y[hi].mean():5.1f} "
        f"b_lstm={res['p_lstm'][hi].mean() - y[hi].mean():+6.2f} "
        f"b_lgb={res['p_lgb'][hi].mean() - y[hi].mean():+6.2f} "
        f"b_meta={res['p_meta'][hi].mean() - y[hi].mean():+6.2f} "
        f"rmse_meta={rmse(res['p_meta'][hi], y[hi]):5.2f} "
        f"| y<=62 n={lo.sum():5d} rmse_meta={rmse(res['p_meta'][lo], y[lo]):5.2f}"
    )


def main():
    ens = load_ensemble("models/ensemble.joblib")
    with h5py.File(resolve_ds02(), "r") as fh:
        for unit in UNITS:
            start, stop, cycles = engine_rows(fh, unit)
            raw_per_cycle = (stop - start) / cycles.max()
            print(
                f"\nunit {unit:.0f}: {stop - start} filas, {cycles.max():.0f} ciclos, "
                f"{raw_per_cycle:.1f} filas/ciclo en bruto"
            )
            print("-" * 118)
            natural = build(fh, unit, 100, ens)
            report(f"u{unit:.0f} natural (~{raw_per_cycle / 100:.0f}/ciclo)", natural)
            step = max(1, int(round(raw_per_cycle / TARGET_DENSITY)))
            dist = build(fh, unit, step, ens)
            report(f"u{unit:.0f} distorsionado (step={step}, ~{raw_per_cycle / step:.1f}/ciclo)", dist)


if __name__ == "__main__":
    main()
