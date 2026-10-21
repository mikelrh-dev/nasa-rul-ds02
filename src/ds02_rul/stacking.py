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

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.linear_model import RidgeCV
from sklearn.model_selection import GroupKFold

from .metrics import calculate_nasa_score
from .smoothing import causal_ema_by_unit

BETA_GRID = np.linspace(0.0, 1.0, 21)
RIDGE_ALPHAS = np.logspace(-2, 3, 20)


@dataclass(frozen=True)
class MetaSpec:
    """How the stacking layer is built and applied.

    The shipped protocol (`MetaSpec()`) is the 50/50 average of a free
    `RidgeCV` and a shallow `LGBMRegressor` over `[p_lstm, p_lgb]`. The fields
    below exist so the alternatives are measurable instead of argued about.

    level_mode : "free" | "sum_to_one" | "convex"
        `free` keeps the fitted coefficients, which shrink (their sum was
        0.894 on the shipped artifact). That shrink is optimal *inside* the
        meta's support and a bias outside it, so `sum_to_one` rescales the
        ridge coefficients to sum to 1 and refits the intercept, removing the
        attenuation while keeping the learned split between the branches.
        `convex` goes further and removes the intercept: the meta becomes a
        learned convex mix of the two branches, so it *cannot* shift the level.
        That matters because the shipped meta carries an intercept fitted on
        unit 16's own bias, and a level shift learned on one engine does not
        transfer (the same failure mode as the rejected OOF-pooled meta).
    use_discrepancy : bool
        Add `relu(p_lgb - p_lstm)` as a third meta-feature, so the meta can see
        *how far* the asymmetric quantile branch diverges from the BiLSTM.
    support_gate : float
        Ramp width, in cycles, over which the meta prediction is handed back to
        `max(p_lstm, p_lgb)` as `max(p_lstm, p_lgb)` exceeds the largest target
        the meta was fitted on. `0.0` disables the gate.
    blend_lgb : float
        Weight of the tree meta in the 50/50 reconciliation. `0.0` uses the
        (level-restored) ridge alone.
    """

    level_mode: str = "free"
    use_discrepancy: bool = False
    support_gate: float = 0.0
    blend_lgb: float = 0.5

    def __post_init__(self):
        if self.level_mode not in ("free", "sum_to_one", "convex"):
            raise ValueError(f"unknown level_mode {self.level_mode!r}")
        if not 0.0 <= self.blend_lgb <= 1.0:
            raise ValueError("blend_lgb must be in [0, 1]")
        if self.support_gate < 0.0:
            raise ValueError("support_gate must be >= 0")


def meta_design(p_lstm, p_lgb, spec: MetaSpec = MetaSpec()) -> np.ndarray:
    """Build the meta design matrix for one spec."""
    p_lstm = np.asarray(p_lstm, dtype=np.float64).ravel()
    p_lgb = np.asarray(p_lgb, dtype=np.float64).ravel()
    cols = [p_lstm, p_lgb]
    if spec.use_discrepancy:
        cols.append(np.maximum(p_lgb - p_lstm, 0.0))
    return np.column_stack(cols)


def fit_meta(Z, y, spec: MetaSpec = MetaSpec(), seed: int = 42) -> dict:
    """Fit the meta-learners under `spec`, recording the support they saw.

    `support` is the largest target in the fitting rows: above it the meta is
    extrapolating, and the support gate (when enabled) hands the prediction back
    to the base branches there.
    """
    from lightgbm import LGBMRegressor

    Z = np.asarray(Z, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).ravel()
    ridge = RidgeCV(alphas=RIDGE_ALPHAS).fit(Z, y)
    if spec.level_mode == "sum_to_one":
        coef = np.asarray(ridge.coef_, dtype=np.float64).copy()
        total = float(coef.sum())
        if abs(total) > 1e-9:
            coef = coef / total
            ridge.coef_ = coef
            ridge.intercept_ = float(np.mean(y - Z @ coef))
    elif spec.level_mode == "convex":
        from scipy.optimize import nnls

        raw_coef, _ = nnls(Z, y)
        total = float(raw_coef.sum())
        coef = (
            raw_coef / total
            if total > 1e-9
            else np.full(Z.shape[1], 1.0 / Z.shape[1])
        )
        ridge.coef_ = coef
        ridge.intercept_ = 0.0
    lgbm = LGBMRegressor(
        max_depth=3, num_leaves=7, n_estimators=120, learning_rate=0.03,
        min_child_samples=20, random_state=seed, verbose=-1,
    ).fit(Z, y)
    return {
        "ridge": ridge,
        "lgbm": lgbm,
        "spec": spec,
        "support": float(y.max()),
        "n_fit": int(y.size),
    }


def predict_meta(meta: dict, p_lstm, p_lgb) -> np.ndarray:
    """Apply a fitted meta to two base predictions, honouring its spec."""
    spec: MetaSpec = meta["spec"]
    Z = meta_design(p_lstm, p_lgb, spec)
    p_meta = (1.0 - spec.blend_lgb) * np.asarray(meta["ridge"].predict(Z)).ravel()
    if spec.blend_lgb > 0.0:
        p_meta = p_meta + spec.blend_lgb * np.asarray(meta["lgbm"].predict(Z)).ravel()

    if spec.support_gate > 0.0:
        anchor = np.maximum(
            np.asarray(p_lstm, dtype=np.float64).ravel(),
            np.asarray(p_lgb, dtype=np.float64).ravel(),
        )
        w = np.clip((anchor - meta["support"]) / spec.support_gate, 0.0, 1.0)
        p_meta = (1.0 - w) * p_meta + w * anchor
    return p_meta


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


def fit_meta_learners(Z, y, seed: int = 42):
    """Fit the two meta-learners on a `[p_lstm, p_lgb]` design.

    Used by the pipeline with the unit-16 rows. Pooling the five fit engines'
    out-of-fold vector into this same function was measured and **rejected**: the
    pooled fit learns a level prior from the long-lived dev engines (RUL up to 88)
    that does not transfer to the shorter test engines. On unit 16 it predicts a
    mean of 39.9 against a true 31.5 and RMSE grows monotonically with `beta`
    (4.04 at 0, 10.17 at 1). Kept because it is the instrument that made that
    negative result reproducible — see `INFORME_motor16_vs_oof.md`.
    """
    from lightgbm import LGBMRegressor

    Z = np.asarray(Z, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64).ravel()
    ridge = RidgeCV(alphas=RIDGE_ALPHAS).fit(Z, y)
    lgbm = LGBMRegressor(
        max_depth=3, num_leaves=7, n_estimators=120, learning_rate=0.03,
        min_child_samples=20, random_state=seed, verbose=-1,
    ).fit(Z, y)
    return ridge, lgbm


def meta_predict(ridge, lgbm, Z) -> np.ndarray:
    """The fixed 50/50 reconciliation of the two meta-learners."""
    Z = np.asarray(Z, dtype=np.float64)
    return 0.5 * np.asarray(ridge.predict(Z)).ravel() + 0.5 * np.asarray(
        lgbm.predict(Z)
    ).ravel()


def score_beta_holdout(p_meta, p_lstm, y, units, cycles, beta_grid=BETA_GRID,
                       span: int = 5) -> dict:
    """Score the `beta` grid on rows that the meta-learner did not train on.

    This is the scorer for the rejected OOF-pooled design: the pooled meta never
    saw unit 16, so unit 16 was the honest place to score it. With the shipped
    protocol the meta is fitted on unit 16 itself, so the grid is scored by
    grouped out-of-fold folds instead (`select_beta_grouped`).
    """
    p_meta = np.asarray(p_meta, dtype=np.float64).ravel()
    p_lstm = np.asarray(p_lstm, dtype=np.float64).ravel()
    y = np.asarray(y, dtype=np.float64).ravel()
    units = np.asarray(units)
    cycles = np.asarray(cycles, dtype=np.float64)

    rmse_ref = float(np.sqrt(np.mean((y - p_lstm) ** 2)))
    nasa_ref = max(calculate_nasa_score(y, p_lstm), 1e-9)

    rows = []
    for beta in beta_grid:
        blend = p_lstm + float(beta) * (p_meta - p_lstm)
        smoothed = causal_ema_by_unit(blend, units, cycles, span=span)
        rmse = float(np.sqrt(np.mean((y - smoothed) ** 2)))
        nasa = calculate_nasa_score(y, smoothed)
        rows.append({
            "beta": round(float(beta), 2), "rmse": rmse, "nasa": nasa,
            "criterion": rmse / rmse_ref + nasa / nasa_ref,
        })
    frame = pd.DataFrame(rows)
    best = frame.loc[frame["criterion"].idxmin()]
    return {
        "beta": float(best["beta"]),
        "rmse": float(best["rmse"]),
        "nasa": float(best["nasa"]),
        "rmse_lstm_ref": rmse_ref,
        "nasa_lstm_ref": nasa_ref,
        "table": frame,
        "scored_units": sorted(float(u) for u in np.unique(units)),
        "n_rows": int(len(y)),
    }


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
    meta_spec: MetaSpec | None = None,
) -> dict:
    """Select `beta` out-of-fold and report the per-fold spread.

    The meta-learners that score a fold are fitted on the *other* folds only, so
    the criterion is never evaluated on rows that fitted the meta-learner. When
    `meta_spec` is given, each fold fits and applies exactly that spec, so the
    `beta` that is selected is the one implied by the meta actually shipped.
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
    oof_idx, oof_pl, oof_pm = [], [], []
    for fold_id, (fit_idx, score_idx) in enumerate(folds):
        if len(score_idx) == 0 or len(fit_idx) == 0:
            continue
        if np.intersect1d(units[fit_idx], units[score_idx]).size:
            raise AssertionError(
                "grouped split leaked a unit between fit and score: "
                f"{np.intersect1d(units[fit_idx], units[score_idx])}"
            )

        if meta_spec is not None:
            Z_fit = meta_design(pred_lstm[fit_idx], pred_lgb[fit_idx], meta_spec)
            fold_meta = fit_meta(Z_fit, y[fit_idx], spec=meta_spec)
            p_meta = predict_meta(
                fold_meta, pred_lstm[score_idx], pred_lgb[score_idx]
            )
        else:
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
        oof_idx.append(score_idx)
        oof_pl.append(pred_lstm[score_idx])
        oof_pm.append(p_meta)

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
    # Out-of-fold predictions under the selected beta, ready to calibrate a
    # prediction band. Every row here was scored by a meta-learner fitted on the
    # other engines, so the residuals are not the meta's own fit.
    calib = None
    if oof_idx:
        idx = np.concatenate(oof_idx)
        pl = np.concatenate(oof_pl)
        pm = np.concatenate(oof_pm)
        blend = pl + beta_hat * (pm - pl)
        calib = {
            "units": units[idx],
            "cycles": cycles[idx],
            "y": y[idx],
            "pred_lstm": pl,
            "pred_meta": pm,
            "pred_ema": causal_ema_by_unit(blend, units[idx], cycles[idx], span=span),
            "beta": beta_hat,
            "n_rows": int(idx.size),
        }

    return {"beta": beta_hat, "folds": records, "spread": spread,
            "beta_grid": beta_grid.tolist(), "oof_calib": calib}


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
