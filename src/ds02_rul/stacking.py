"""Grouped out-of-fold selection of the shrinkage factor `beta`.

The original notebook fitted the meta-learners on the unit-16 rows and then
scored the `beta` grid on those same rows, which is why it reported a validation
RMSE of 0.308 against the BiLSTM's 4.221 and drove `beta` to the grid maximum.
Here every scored unit is scored by meta-learners that were fitted on the other
units only.

Phase A is expensive (one base-model fit per held-out group) and is supplied by
the caller: `select_beta_grouped` consumes already-computed out-of-fold
predictions. That keeps the compute budget explicit and avoids a hidden refit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GroupKFold

from .metrics import calculate_nasa_score
from .smoothing import causal_ema_by_unit

BETA_GRID = np.linspace(0.0, 1.0, 21)
RIDGE_ALPHAS = np.logspace(-2, 3, 20)


def grouped_folds(units, n_splits: int = 3, seed: int = 42):
    """Balanced grouped folds over unique units, deterministic for a seed."""
    units = np.asarray(units)
    unique = np.unique(units)
    rng = np.random.RandomState(seed)
    shuffled = unique.copy()
    rng.shuffle(shuffled)
    folds = [shuffled[i::n_splits] for i in range(n_splits)]
    out = []
    for held in folds:
        val = np.isin(units, held)
        out.append((np.where(~val)[0], np.where(val)[0]))
    return out


def select_beta_grouped(
    units,
    cycles,
    y,
    pred_lstm,
    pred_lgb,
    folds=None,
    beta_grid=BETA_GRID,
    span: int = 5,
    use_cycle_feature: bool = True,
) -> dict:
    """Select `beta` out-of-fold and report the per-fold spread.

    The meta-learners that score a fold are fitted on the *other* folds only, so
    the criterion is never evaluated on rows that fitted the meta-learner.
    """
    from lightgbm import LGBMRegressor

    units = np.asarray(units)
    cycles = np.asarray(cycles, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    pred_lstm = np.asarray(pred_lstm, dtype=np.float64)
    pred_lgb = np.asarray(pred_lgb, dtype=np.float64)

    if folds is None:
        folds = grouped_folds(units, n_splits=3)

    def design(idx):
        cols = [pred_lstm[idx], pred_lgb[idx]]
        if use_cycle_feature:
            cols.append(cycles[idx] / 100.0)
        return np.column_stack(cols)

    records = []
    for fold_id, (fit_idx, score_idx) in enumerate(folds):
        if len(score_idx) == 0 or len(fit_idx) == 0:
            continue
        if np.intersect1d(units[fit_idx], units[score_idx]).size:
            raise AssertionError(
                "grouped split leaked a unit between fit and score: "
                f"{np.intersect1d(units[fit_idx], units[score_idx])}"
            )

        Z_fit, Z_score = design(fit_idx), design(score_idx)
        ridge = RidgeCV(alphas=RIDGE_ALPHAS).fit(Z_fit, y[fit_idx])
        lgbm = LGBMRegressor(
            max_depth=3,
            num_leaves=7,
            n_estimators=120,
            learning_rate=0.03,
            min_child_samples=20,
            random_state=42,
            verbose=-1,
        ).fit(Z_fit, y[fit_idx])

        p_meta = 0.5 * ridge.predict(Z_score) + 0.5 * lgbm.predict(Z_score)

        base = pred_lstm[score_idx]
        rmse_ref = float(np.sqrt(np.mean((y[score_idx] - base) ** 2)))
        nasa_ref = max(calculate_nasa_score(y[score_idx], base), 1e-9)

        best = {"beta": 0.0, "criterion": np.inf, "rmse": np.inf, "nasa": np.inf}
        curve = []
        for beta in beta_grid:
            blend = base + beta * (p_meta - base)
            smoothed = causal_ema_by_unit(
                blend, units[score_idx], cycles[score_idx], span=span
            )
            rmse = float(np.sqrt(np.mean((y[score_idx] - smoothed) ** 2)))
            nasa = calculate_nasa_score(y[score_idx], smoothed)
            crit = rmse / rmse_ref + nasa / nasa_ref
            curve.append({"beta": round(float(beta), 2), "rmse": rmse, "nasa": nasa, "criterion": crit})
            if crit < best["criterion"]:
                best = {"beta": float(beta), "criterion": crit, "rmse": rmse, "nasa": nasa}

        records.append(
            {
                "fold": fold_id,
                "scored_units": sorted(float(u) for u in np.unique(units[score_idx])),
                "fit_units": sorted(float(u) for u in np.unique(units[fit_idx])),
                "beta": best["beta"],
                "rmse_val": round(best["rmse"], 4),
                "nasa_val": round(best["nasa"], 2),
                "rmse_lstm_ref": round(rmse_ref, 4),
                "nasa_lstm_ref": round(nasa_ref, 2),
                "curve": curve,
            }
        )

    betas = np.array([r["beta"] for r in records])
    beta_hat = float(np.median(betas)) if betas.size else 1.0
    spread = {
        "min": float(betas.min()) if betas.size else None,
        "max": float(betas.max()) if betas.size else None,
        "iqr": float(np.subtract(*np.percentile(betas, [75, 25]))) if betas.size else None,
        "n_folds": int(betas.size),
    }
    return {"beta": beta_hat, "folds": records, "spread": spread, "beta_grid": beta_grid.tolist()}


def in_sample_beta_diagnostic(
    units, cycles, y, pred_lstm, pred_lgb, beta_grid=BETA_GRID, span: int = 5,
    use_cycle_feature: bool = True,
) -> dict:
    """Reproduce the legacy protocol on ONE unit to expose its in-sample bias.

    Diagnostic only: it fits the meta-learners and scores the grid on the same
    rows. Kept so the defect stays reproducible instead of living in prose.
    """
    from lightgbm import LGBMRegressor

    units = np.asarray(units)
    cycles = np.asarray(cycles, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    pred_lstm = np.asarray(pred_lstm, dtype=np.float64)
    pred_lgb = np.asarray(pred_lgb, dtype=np.float64)

    cols = [pred_lstm, pred_lgb]
    if use_cycle_feature:
        cols.append(cycles / 100.0)
    Z = np.column_stack(cols)

    ridge = RidgeCV(alphas=RIDGE_ALPHAS).fit(Z, y)
    lgbm = LGBMRegressor(
        max_depth=3, num_leaves=7, n_estimators=120, learning_rate=0.03,
        min_child_samples=20, random_state=42, verbose=-1,
    ).fit(Z, y)
    p_meta = 0.5 * ridge.predict(Z) + 0.5 * lgbm.predict(Z)

    rmse_ref = float(np.sqrt(np.mean((y - pred_lstm) ** 2)))
    nasa_ref = max(calculate_nasa_score(y, pred_lstm), 1e-9)
    rows = []
    for beta in beta_grid:
        smoothed = causal_ema_by_unit(pred_lstm + beta * (p_meta - pred_lstm), units, cycles, span=span)
        rmse = float(np.sqrt(np.mean((y - smoothed) ** 2)))
        nasa = calculate_nasa_score(y, smoothed)
        rows.append({"beta": round(float(beta), 2), "rmse_val": rmse, "nasa_val": nasa,
                     "criterion": rmse / rmse_ref + nasa / nasa_ref})
    frame = pd.DataFrame(rows)
    best = frame.loc[frame["criterion"].idxmin()]
    return {"beta": float(best["beta"]), "rmse_val": float(best["rmse_val"]),
            "nasa_val": float(best["nasa_val"]), "rmse_lstm_ref": rmse_ref,
            "nasa_lstm_ref": nasa_ref, "table": frame}
