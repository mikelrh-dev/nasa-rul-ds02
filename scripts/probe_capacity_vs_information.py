"""Capacity vs information: is the high-RUL error the model class, the objective, or the data?

Four questions, one cheap experiment, `dev` only, grouped out-of-fold by engine so
no scored engine ever contributes to the preprocessing or the weights:

* **A0** current tabular branch (LightGBM, quantile 0.35, `cyc_norm` = cycle/100).
* **A1** same, quantile 0.50 - isolates the *objective's* downward bias.
* **A2** XGBoost, quantile 0.35 - isolates the *library*.
* **A3** LightGBM with `cycle / L` (the true life fraction) replacing `cyc_norm`.
  `L` is the engine's total life, so this arm is an **oracle**: it is not
  deployable and exists only to measure how much of the error is information
  that the current features do not carry.
* **A4** XGBoost with the same life fraction - best available class *and*
  information.
* **A5** LightGBM with both `cyc_norm` and the life fraction.
* **A6** linear model over `[cycle, L]`: `RUL = L - cycle` is exactly linear, so a
  model with the right inductive bias can represent it while a tree can only
  clamp at the edges of the life values it saw. This arm separates "the
  information is unusable by trees" from "the information is absent".
* **A7** LightGBM with raw `L` appended - the same oracle through a tree.
* **A8** LightGBM q0.50 with the life fraction - objective and information together.

Decision rule, declared before looking: if A3/A4 close most of the gap at
`y > 65`, the tabular features *can* use life information and the blocker is
estimating `L` from early data (a data/estimator-of-L problem, not a ceiling).
If they do not, the ceiling is in the representation itself.

Run:  python scripts/probe_capacity_vs_information.py
"""
from __future__ import annotations

import numpy as np
from lightgbm import LGBMRegressor
from sklearn.linear_model import RidgeCV
from xgboost import XGBRegressor

from ds02_rul.data import load_ds02
from ds02_rul.features import build_windows, fit_preprocessing
from ds02_rul.metrics import calculate_nasa_score

# Same grouped folds as the OOF gate, so the numbers are comparable with
# INFORME_p0_p1_prior_de_vida.md (units 16/20, 2/10, 5/18).
FOLDS = ((2.0, 10.0), (5.0, 18.0), (16.0, 20.0))
WINDOW = 50
STEP = 3


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def lgb_maker(alpha: float):
    return lambda: LGBMRegressor(
        objective="quantile", alpha=alpha, n_estimators=300, learning_rate=0.02,
        num_leaves=15, max_depth=4, min_child_samples=50, reg_alpha=1.0,
        reg_lambda=5.0, colsample_bytree=0.8, subsample=0.8, verbose=-1,
        random_state=42,
    )


def xgb_maker(alpha: float):
    return lambda: XGBRegressor(
        objective="reg:quantileerror", quantile_alpha=alpha, n_estimators=300,
        learning_rate=0.02, max_depth=4, min_child_weight=50, reg_alpha=1.0,
        reg_lambda=5.0, colsample_bytree=0.8, subsample=0.8, random_state=42,
        tree_method="hist", n_jobs=4,
    )


def ridge_maker():
    return lambda: RidgeCV(alphas=np.logspace(-2, 3, 20))


ARMS = {
    "A0 LGB q0.35 cyc_norm": ("cyc", lgb_maker(0.35)),
    "A1 LGB q0.50 cyc_norm": ("cyc", lgb_maker(0.50)),
    "A2 XGB q0.35 cyc_norm": ("cyc", xgb_maker(0.35)),
    "A3 LGB q0.35 life_frac": ("frac", lgb_maker(0.35)),
    "A4 XGB q0.35 life_frac": ("frac", xgb_maker(0.35)),
    "A5 LGB q0.35 cyc+frac": ("both", lgb_maker(0.35)),
    "A6 Ridge [cycle,L] (oraculo)": ("cycL", ridge_maker()),
    "A7 LGB q0.35 +L (oraculo)": ("plusL", lgb_maker(0.35)),
    "A8 LGB q0.50 life_frac": ("frac", lgb_maker(0.50)),
}


def main():
    raw = load_ds02(stride=100)
    A, W, Xs, Y = raw["A_train"], raw["W_train"], raw["Xs_train"], raw["y_train"]
    units_raw, cyc_raw = A[:, 0], A[:, 1]
    life = {
        float(u): float(cyc_raw[units_raw == u].max()) for u in np.unique(units_raw)
    }
    print("vida total por motor:", {k: v for k, v in sorted(life.items())})

    preds = {name: {} for name in ARMS}
    for fold_id, held in enumerate(FOLDS):
        train_units = np.setdiff1d(np.unique(units_raw), np.asarray(held))
        mask = np.isin(units_raw, train_units)
        prep = fit_preprocessing(W[mask], Xs[mask])
        dev = build_windows(
            W, Xs, Y, units_raw, cyc_raw, prep,
            window_size=WINDOW, step=STEP, use_cycle=True,
        )
        wu = dev["meta"]["unit"].values
        wc = dev["meta"]["cycle"].values
        y = dev["y"].astype(np.float64)
        X_base = dev["X_tab"].astype(np.float64)   # column 0 is cycle/100
        frac = np.array([wc[i] / life[float(wu[i])] for i in range(len(wu))])

        L_col = np.array([life[float(u)] for u in wu])
        variants = {
            "cyc": X_base,
            "frac": np.column_stack([frac, X_base[:, 1:]]),
            "both": np.column_stack([X_base, frac]),
            "cycL": np.column_stack([wc, L_col]),
            "plusL": np.column_stack([X_base, L_col]),
        }
        tr = np.isin(wu, train_units)
        te = ~tr
        for name, (kind, maker) in ARMS.items():
            model = maker().fit(variants[kind][tr], y[tr])
            preds[name][fold_id] = (
                np.where(te)[0], model.predict(variants[kind][te]), y[te], wu[te]
            )

        print(f"fold {fold_id}: held-out {sorted(held)}, {te.sum()} ventanas")

    # every arm scores the same rows: concatenate each arm's own held-out blocks
    y_all = np.concatenate([preds["A0 LGB q0.35 cyc_norm"][f][2] for f in range(len(FOLDS))])
    units_all = np.concatenate(
        [preds["A0 LGB q0.35 cyc_norm"][f][3] for f in range(len(FOLDS))]
    )
    assert len(y_all) == len(units_all) and len(y_all) == sum(
        len(preds["A0 LGB q0.35 cyc_norm"][f][2]) for f in range(len(FOLDS))
    )
    rows = []
    for name in ARMS:
        p = np.concatenate([preds[name][f][1] for f in range(len(FOLDS))])
        hi, lo = y_all > 65, y_all <= 62
        macro = float(
            np.mean([rmse(p[units_all == u], y_all[units_all == u]) for u in np.unique(units_all)])
        )
        rows.append(
            {
                "arm": name,
                "macro": macro,
                "rmse": rmse(p, y_all),
                "rmse_hi": rmse(p[hi], y_all[hi]),
                "bias_hi": float(np.mean(p[hi] - y_all[hi])),
                "rmse_lo": rmse(p[lo], y_all[lo]),
                "bias_lo": float(np.mean(p[lo] - y_all[lo])),
                "nasa": calculate_nasa_score(y_all, p),
            }
        )

    header = (f"{'arm':30s} {'macro':>6} {'RMSE':>6} {'RMSE>65':>8} {'bias>65':>8} "
              f"{'RMSE<=62':>9} {'bias<=62':>9} {'NASA':>9}")
    print("\n" + header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['arm']:30s} {r['macro']:6.2f} {r['rmse']:6.2f} {r['rmse_hi']:8.2f} "
            f"{r['bias_hi']:+8.2f} {r['rmse_lo']:9.2f} {r['bias_lo']:+9.2f} {r['nasa']:9.1f}"
        )


if __name__ == "__main__":
    main()
