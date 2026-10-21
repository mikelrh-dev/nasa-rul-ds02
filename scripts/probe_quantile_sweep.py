"""Sweep the tabular objective's quantile, with and without the life oracle.

`probe_capacity_vs_information.py` shows that moving from quantile 0.35 to the
median buys ~0.9 RMSE and ~3.4 cycles of high-RUL bias, and that the life
fraction buys more. This script tests whether 0.50 is a lucky point and whether
the two effects add up, so the recommendation does not rest on one number.

Grouped out-of-fold by engine, `dev` only.

Run:  python scripts/probe_quantile_sweep.py
"""
from __future__ import annotations

import numpy as np
from lightgbm import LGBMRegressor

from ds02_rul.data import load_ds02
from ds02_rul.features import build_windows, fit_preprocessing
from ds02_rul.metrics import calculate_nasa_score

FOLDS = ((2.0, 10.0), (5.0, 18.0), (16.0, 20.0))
ALPHAS = (0.35, 0.40, 0.45, 0.50, 0.55, 0.60)


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def main():
    raw = load_ds02(stride=100)
    A, W, Xs, Y = raw["A_train"], raw["W_train"], raw["Xs_train"], raw["y_train"]
    units_raw, cyc_raw = A[:, 0], A[:, 1]
    life = {float(u): float(cyc_raw[units_raw == u].max()) for u in np.unique(units_raw)}

    collected = {f"{a:.2f}|{k}": [] for a in ALPHAS for k in ("cyc", "plusL")}
    y_all, u_all = [], []
    for held in FOLDS:
        train_units = np.setdiff1d(np.unique(units_raw), np.asarray(held))
        mask = np.isin(units_raw, train_units)
        prep = fit_preprocessing(W[mask], Xs[mask])
        dev = build_windows(
            W, Xs, Y, units_raw, cyc_raw, prep, window_size=50, step=3, use_cycle=True
        )
        wu, y = dev["meta"]["unit"].values, dev["y"].astype(np.float64)
        X = dev["X_tab"].astype(np.float64)
        L_col = np.array([life[float(u)] for u in wu])
        tr = np.isin(wu, train_units)
        te = ~tr
        y_all.append(y[te])
        u_all.append(wu[te])

        for alpha in ALPHAS:
            for kind, design in (("cyc", X), ("plusL", np.column_stack([X, L_col]))):
                model = LGBMRegressor(
                    objective="quantile", alpha=alpha, n_estimators=300,
                    learning_rate=0.02, num_leaves=15, max_depth=4,
                    min_child_samples=50, reg_alpha=1.0, reg_lambda=5.0,
                    colsample_bytree=0.8, subsample=0.8, verbose=-1, random_state=42,
                ).fit(design[tr], y[tr])
                collected[f"{alpha:.2f}|{kind}"].append(model.predict(design[te]))

    y_all = np.concatenate(y_all)
    u_all = np.concatenate(u_all)
    hi, lo = y_all > 65, y_all <= 62
    print(f"{'alpha':>6} {'oraculo':>8} {'macro':>6} {'RMSE':>6} {'RMSE>65':>8} "
          f"{'bias>65':>8} {'RMSE<=62':>9} {'bias<=62':>9} {'NASA':>9}")
    for key, chunks in collected.items():
        alpha, kind = key.split("|")
        p = np.concatenate(chunks)
        macro = float(np.mean([rmse(p[u_all == u], y_all[u_all == u]) for u in np.unique(u_all)]))
        print(
            f"{alpha:>6} {kind:>8} {macro:6.2f} {rmse(p, y_all):6.2f} "
            f"{rmse(p[hi], y_all[hi]):8.2f} {np.mean(p[hi] - y_all[hi]):+8.2f} "
            f"{rmse(p[lo], y_all[lo]):9.2f} {np.mean(p[lo] - y_all[lo]):+9.2f} "
            f"{calculate_nasa_score(y_all, p):9.1f}"
        )


if __name__ == "__main__":
    main()
