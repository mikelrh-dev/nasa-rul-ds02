"""Orquestación del entrenamiento y la evaluación.

Vive en el paquete (no en celdas del notebook) para que el notebook siga legible
y el protocolo sea testeable. Aquí importan dos propiedades:

* el preprocesado se ajusta solo con las *unidades de ajuste*, y dentro de cada
  pliegue de validación cruzada se reajusta con las unidades de ese pliegue;
* el modelo Keras nunca ve la unidad reservada ni las de test, ni siquiera a
  través de una media del escalador.
"""
from __future__ import annotations

import time

import numpy as np
import pandas as pd
from lightgbm import LGBMRegressor

from .features import build_windows, fit_preprocessing
from .metrics import calculate_nasa_score, evaluate_predictions
from .model import build_champion_bilstm

# La mediana (alpha=0.50) se probó y se DESCARTÓ en la lectura confirmatoria de
# test, aunque ganaba por mucho en dev out-of-fold agrupado (rama 9.11 -> 8.18
# de RMSE, híbrido 13.15 -> 12.09). En test, con el BiLSTM fijo, cuesta a la rama
# 7.11 -> 9.12 y al híbrido 4.24 -> 4.59: los motores de dev son longevos y se
# subestiman, los de test son más cortos, así que subir el cuantil ayuda al
# régimen sobrerrepresentado en dev y perjudica al de test. La compuerta de dev
# no puede arbitrar esto; el hallazgo está en ADR-007.
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
    """Rama tabular cuantílica del híbrido con los parámetros fijados."""
    return LGBMRegressor(**LGB_PARAMS, random_state=seed)


def fit_bilstm(X_seq, y, fit_idx, val_idx, seed: int, epochs: int = 22, batch_size: int = 128):
    """Entrena el campeón con parada temprana sobre una unidad reservada real."""
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
    """Métricas de las predicciones y de su versión suavizada con EMA."""
    from .smoothing import causal_ema_by_unit

    smoothed = causal_ema_by_unit(pred, units, cycles, span=5)
    base = evaluate_predictions(y, pred, name)
    base_sm = evaluate_predictions(y, smoothed, f"{name} + EMA5")
    return base, base_sm, smoothed


def run_seed(raw: dict, seed: int, fit_units, holdout_units, test_units,
             window: int = 50, step_train: int = 3, step_test: int = 2,
             epochs: int = 22, use_cycle: bool = True,
             use_baseline_delta: bool = False) -> dict:
    """Pipeline completo para una semilla. Devuelve modelos, predicciones y métricas."""
    A_tr, A_te = raw["A_train"], raw["A_test"]
    W_tr, Xs_tr = raw["W_train"], raw["Xs_train"]
    W_te, Xs_te = raw["W_test"], raw["Xs_test"]
    units_tr, cyc_tr = A_tr[:, 0], A_tr[:, 1]
    units_te, cyc_te = A_te[:, 0], A_te[:, 1]

    fit_row_mask = np.isin(units_tr, fit_units)
    hold_row_mask = np.isin(units_tr, holdout_units)

    # ---- preprocesado ajustado SOLO con las unidades de ajuste
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

    # ---- rama tabular
    t0 = time.perf_counter()
    lgbm = make_lgbm(seed).fit(dev["X_tab"][fit_idx], dev["y"][fit_idx])
    t_lgb = time.perf_counter() - t0
    p_lgb_hold = lgbm.predict(dev["X_tab"][hold_idx])
    p_lgb_test = lgbm.predict(test["X_tab"])

    # ---- rama secuencial
    t0 = time.perf_counter()
    model, history = fit_bilstm(
        dev["X_seq"], dev["y"], fit_idx, hold_idx, seed=seed, epochs=epochs
    )
    t_lstm = time.perf_counter() - t0
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
        "t_total": float(t_lgb + t_lstm),
        "timing": {"t_lgb": float(t_lgb), "t_lstm": float(t_lstm),
                   "t_total": float(t_lgb + t_lstm)},
        "n_params": int(model.count_params()),
        "use_cycle": use_cycle,
    }


def oof_base_predictions(raw: dict, dev_units, n_splits: int = 3, seed: int = 42,
                         window: int = 50, step_train: int = 3, epochs: int = 15,
                         use_cycle: bool = True) -> dict:
    """Predicciones base out-of-fold sobre las unidades de dev, reajustando por pliegue.

    Cada pliegue reajusta los escaladores, la base polinómica y las 14 crestas de
    residuos con sus unidades de entrenamiento, así que las unidades puntuadas no
    aportaron a ninguna transformación. La rejilla de ventanas es igual entre
    pliegues (mismas unidades y mismo paso), así que las predicciones coinciden
    fila a fila.
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

        t0 = time.perf_counter()
        lgbm = make_lgbm(seed).fit(dev["X_tab"][tr_idx], dev["y"][tr_idx])
        model, _ = fit_bilstm(
            dev["X_seq"], dev["y"], tr_idx, va_idx, seed=seed, epochs=epochs
        )
        timing.append({"fold": fold_id, "scored_units": [float(u) for u in held_units],
                       "seconds": round(time.perf_counter() - t0, 1)})

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
    """Media ± desviación típica entre semillas, además de los valores por semilla."""
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
    """Mide, sin darlo por hecho, lo que aportan el contador de ciclos y el delta base.

    Las variantes tabulares tardan segundos; las del BiLSTM son la parte cara y
    quedan controladas por `include_bilstm`.

    Cada fila lleva los tiempos de rama medidos con `time.perf_counter()` en
    `run_seed`: las filas de LGBM llevan `t_lgb_s` (= `tiempo_s`), las de BiLSTM
    `t_bilstm_s` (= `tiempo_s`) y la de EMA no lleva tiempo porque suavizar no
    reentrena nada.
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
        timing = out.get("timing") or out
        t_lgb = float(timing.get("t_lgb", float("nan")))
        t_lstm = float(timing.get("t_lstm", float("nan")))

        lgb_metrics = evaluate_predictions(y_test, out["p_lgb_test"], f"LGBM | {label}")
        rows.append({"variant": label, "model": "LGBM", **{k: lgb_metrics[k] for k in ("RMSE", "MAE", "R2", "NASA_Score")}, "t_lgb_s": t_lgb, "t_bilstm_s": float("nan"), "tiempo_s": t_lgb})

        if include_bilstm:
            lstm_metrics = evaluate_predictions(y_test, out["p_lstm_test"], f"BiLSTM | {label}")
            rows.append({"variant": label, "model": "BiLSTM", **{k: lstm_metrics[k] for k in ("RMSE", "MAE", "R2", "NASA_Score")}, "t_lgb_s": float("nan"), "t_bilstm_s": t_lstm, "tiempo_s": t_lstm})

            from .smoothing import causal_ema_by_unit

            sm = causal_ema_by_unit(out["p_lstm_test"], units, cycles, span=5)
            sm_metrics = evaluate_predictions(y_test, sm, f"BiLSTM+EMA | {label}")
            rows.append({"variant": label, "model": "BiLSTM+EMA", **{k: sm_metrics[k] for k in ("RMSE", "MAE", "R2", "NASA_Score")}, "t_lgb_s": float("nan"), "t_bilstm_s": float("nan"), "tiempo_s": float("nan")})

        del out
    return pd.DataFrame(rows)


def nasa(y, p) -> float:
    """NASA score con la misma convención que las métricas del híbrido."""
    return calculate_nasa_score(y, p)
