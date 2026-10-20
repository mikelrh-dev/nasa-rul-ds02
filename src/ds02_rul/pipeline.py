"""Training and evaluation orchestration.

Kept in the package (not in notebook cells) so the notebook stays readable and
the protocol is testable. Two properties matter here:

* preprocessing is fitted on the *fit units only*, and inside each cross-
  validation fold it is fitted again on that fold's training units;
* the Keras model never sees the holdout or the test units, not even through a
  scaler mean.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from .features import build_windows, fit_preprocessing
from .metrics import calculate_nasa_score, evaluate_predictions
from .model import build_champion_bilstm

LGB_PARAMS = dict(
    objective="quantile",
    alpha=0.35,
    n_estimators=300,
    learning_rate=0.02,
    num_leaves=15,
    max_depth=4,
    min_child_samples=50,
    reg_alpha=1.0,
    reg_lambda=5.0,
    colsample_bytree=0.8,
    subsample=0.8,
    verbose=-1,
)


def make_lgbm(seed: int) -> LGBMRegressor:
    return LGBMRegressor(**LGB_PARAMS, random_state=seed)


def fit_bilstm(X_seq, y, fit_idx, val_idx, seed: int, epochs: int = 22, batch_size: int = 128):
    """Train the champion with early stopping on a genuinely held-out unit."""
    import tensorflow as tf
    from keras import callbacks

    model = build_champion_bilstm(input_shape=X_seq.shape[1:], dense_units=32, seed=seed)
    tf.random.set_seed(seed)
    np.random.seed(seed)

    history = model.fit(
        X_seq[fit_idx],
        y[fit_idx],
        validation_data=(X_seq[val_idx], y[val_idx]),
        batch_size=batch_size,
        epochs=epochs,
        verbose=0,
        callbacks=[
            callbacks.EarlyStopping(
                monitor="val_loss", patience=5, restore_best_weights=True, verbose=0
            ),
            callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=2, verbose=0
            ),
        ],
    )
    return model, history


def _row(units, cycles, y, pred, name):
    """Metrics plus the EMA-smoothed variant of the same predictions."""
    from .smoothing import causal_ema_by_unit

    smoothed = causal_ema_by_unit(pred, units, cycles, span=5)
    base = evaluate_predictions(y, pred, name)
    base_sm = evaluate_predictions(y, smoothed, f"{name} + EMA5")
    return base, base_sm, smoothed


def run_seed(raw: dict, seed: int, fit_units, holdout_units, test_units,
             window: int = 50, step_train: int = 3, step_test: int = 2,
             epochs: int = 22, use_cycle: bool = True,
             use_baseline_delta: bool = False) -> dict:
    """Full pipeline for one seed. Returns models, predictions and metrics."""
    A_tr, A_te = raw["A_train"], raw["A_test"]
    W_tr, Xs_tr = raw["W_train"], raw["Xs_train"]
    W_te, Xs_te = raw["W_test"], raw["Xs_test"]
    units_tr, cyc_tr = A_tr[:, 0], A_tr[:, 1]
    units_te, cyc_te = A_te[:, 0], A_te[:, 1]

    fit_row_mask = np.isin(units_tr, fit_units)
    hold_row_mask = np.isin(units_tr, holdout_units)

    # ---- preprocessing fitted on the fit units ONLY
    prep = fit_preprocessing(W_tr[fit_row_mask], Xs_tr[fit_row_mask])

    dev = build_windows(
        W_tr, Xs_tr, raw["y_train"], units_tr, cyc_tr, prep,
        window_size=window, step=step_train,
        use_cycle=use_cycle, use_baseline_delta=use_baseline_delta,
    )
    test = build_windows(
        W_te, Xs_te, raw["y_test"], units_te, cyc_te, prep,
        window_size=window, step=step_test,
        use_cycle=use_cycle, use_baseline_delta=use_baseline_delta,
    )

    dev_units = dev["meta"]["unit"].values
    fit_idx = np.where(np.isin(dev_units, fit_units))[0]
    hold_idx = np.where(np.isin(dev_units, holdout_units))[0]

    # ---- tabular branch
    t0 = time.time()
    lgbm = make_lgbm(seed).fit(dev["X_tab"][fit_idx], dev["y"][fit_idx])
    t_lgb = time.time() - t0
    p_lgb_hold = lgbm.predict(dev["X_tab"][hold_idx])
    p_lgb_test = lgbm.predict(test["X_tab"])

    # ---- sequential branch
    t0 = time.time()
    model, history = fit_bilstm(
        dev["X_seq"], dev["y"], fit_idx, hold_idx, seed=seed, epochs=epochs
    )
    t_lstm = time.time() - t0
    p_lstm_hold = model.predict(dev["X_seq"][hold_idx], verbose=0).ravel()
    p_lstm_test = model.predict(test["X_seq"], verbose=0).ravel()

    return {
        "seed": seed,
        "prep": prep,
        "lgbm": lgbm,
        "bilstm": model,
        "history": history,
        "dev": dev,
        "test": test,
        "fit_idx": fit_idx,
        "hold_idx": hold_idx,
        "p_lgb_hold": p_lgb_hold,
        "p_lgb_test": p_lgb_test,
        "p_lstm_hold": p_lstm_hold,
        "p_lstm_test": p_lstm_test,
        "t_lgb": t_lgb,
        "t_lstm": t_lstm,
        "n_params": int(model.count_params()),
        "use_cycle": use_cycle,
    }


def oof_base_predictions(raw: dict, dev_units, n_splits: int = 3, seed: int = 42,
                         window: int = 50, step_train: int = 3, epochs: int = 15,
                         use_cycle: bool = True) -> dict:
    """Out-of-fold base predictions over the dev units, refitting per fold.

    Each fold refits the scalers, the polynomial basis and the 14 residual
    ridges on that fold's training units, so the scored units never contributed
    to any transform. The window grid is identical across folds (same units,
    same step), so the predictions line up row for row.
    """
    A_tr = raw["A_train"]
    W_tr, Xs_tr = raw["W_train"], raw["Xs_train"]
    units_tr, cyc_tr = A_tr[:, 0], A_tr[:, 1]
    y_raw = raw["y_train"]

    unique_units = np.unique(dev_units)
    rng = np.random.RandomState(seed)
    shuffled = unique_units.copy()
    rng.shuffle(shuffled)
    unit_folds = [shuffled[i::n_splits] for i in range(n_splits)]

    n_windows = None
    p_lstm = None
    p_lgb = None
    meta = None
    cover = None
    timing = []

    for fold_id, held_units in enumerate(unit_folds):
        train_units = np.setdiff1d(unique_units, held_units)
        fit_row_mask = np.isin(units_tr, train_units)

        prep = fit_preprocessing(W_tr[fit_row_mask], Xs_tr[fit_row_mask])
        dev = build_windows(
            W_tr, Xs_tr, y_raw, units_tr, cyc_tr, prep,
            window_size=window, step=step_train, use_cycle=use_cycle,
        )
        w_units = dev["meta"]["unit"].values
        tr_idx = np.where(np.isin(w_units, train_units))[0]
        va_idx = np.where(np.isin(w_units, held_units))[0]

        if n_windows is None:
            n_windows = len(dev["y"])
            p_lstm = np.full(n_windows, np.nan)
            p_lgb = np.full(n_windows, np.nan)
            cover = np.zeros(n_windows, dtype=int)
            meta = dev["meta"].copy()

        assert not np.intersect1d(w_units[tr_idx], w_units[va_idx]).size

        t0 = time.time()
        lgbm = make_lgbm(seed).fit(dev["X_tab"][tr_idx], dev["y"][tr_idx])
        model, _ = fit_bilstm(
            dev["X_seq"], dev["y"], tr_idx, va_idx, seed=seed, epochs=epochs
        )
        timing.append({"fold": fold_id, "scored_units": [float(u) for u in held_units],
                       "seconds": round(time.time() - t0, 1)})

        p_lstm[va_idx] = model.predict(dev["X_seq"][va_idx], verbose=0).ravel()
        p_lgb[va_idx] = lgbm.predict(dev["X_tab"][va_idx])
        cover[va_idx] += 1

    if not np.all(cover == 1):
        raise AssertionError(
            f"OOF coverage is not exactly 1 everywhere (min={cover.min()}, max={cover.max()})"
        )

    return {
        "units": meta["unit"].values,
        "cycles": meta["cycle"].values,
        "y": dev["y"],
        "pred_lstm": p_lstm,
        "pred_lgb": p_lgb,
        "unit_folds": [[float(u) for u in f] for f in unit_folds],
        "timing": timing,
    }


def seed_summary(rows: list) -> pd.DataFrame:
    """Mean ± standard deviation across seeds, plus the per-seed values."""
    frame = pd.DataFrame(rows)
    agg = (
        frame.groupby("Modelo")[["RMSE", "MAE", "R2", "NASA_Score"]]
        .agg(["mean", "std"])
        .round(4)
    )
    agg.columns = [f"{metric}_{stat}" for metric, stat in agg.columns]
    return agg.reset_index()


def ablation_table(raw: dict, seeds=(42,), window: int = 50, step_train: int = 3,
                   step_test: int = 2, epochs: int = 22, fit_units=None,
                   holdout_units=None, include_bilstm: bool = True) -> pd.DataFrame:
    """Measure — not assert — what the cycle counter and the baseline delta buy.

    The tabular variants are seconds each; the BiLSTM variants are the expensive
    part and are gated by `include_bilstm`.
    """
    rows = []
    variants = [
        ("cyc_norm ON  (baseline)", True, False),
        ("cyc_norm OFF", False, False),
        ("cyc_norm OFF + baseline delta", False, True),
        ("cyc_norm ON  + baseline delta", True, True),
    ]
    for label, use_cycle, use_delta in variants:
        out = run_seed(
            raw, seed=seeds[0], fit_units=fit_units, holdout_units=holdout_units,
            test_units=None, window=window, step_train=step_train, step_test=step_test,
            epochs=epochs, use_cycle=use_cycle, use_baseline_delta=use_delta,
        )
        test = out["test"]
        units = test["meta"]["unit"].values
        cycles = test["meta"]["cycle"].values
        y_test = test["y"]

        lgb_metrics = evaluate_predictions(y_test, out["p_lgb_test"], f"LGBM | {label}")
        rows.append({"variant": label, "model": "LGBM", **{k: lgb_metrics[k] for k in ("RMSE", "MAE", "R2", "NASA_Score")}})

        if include_bilstm:
            lstm_metrics = evaluate_predictions(y_test, out["p_lstm_test"], f"BiLSTM | {label}")
            rows.append({"variant": label, "model": "BiLSTM", **{k: lstm_metrics[k] for k in ("RMSE", "MAE", "R2", "NASA_Score")}})

            from .smoothing import causal_ema_by_unit

            sm = causal_ema_by_unit(out["p_lstm_test"], units, cycles, span=5)
            sm_metrics = evaluate_predictions(y_test, sm, f"BiLSTM+EMA | {label}")
            rows.append({"variant": label, "model": "BiLSTM+EMA", **{k: sm_metrics[k] for k in ("RMSE", "MAE", "R2", "NASA_Score")}})

        del out
    return pd.DataFrame(rows)


def nasa(y, p) -> float:
    return calculate_nasa_score(y, p)
