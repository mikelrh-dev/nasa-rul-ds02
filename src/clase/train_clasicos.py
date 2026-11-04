"""Fase 2.2 — 5 clásicos de clase con GridSearchCV + GroupKFold(groups=unit).

SAA 6 (30%): regresión/Ridge, KNN, RF, XGB, SVR. Grids mínimos publicados.
PIA 3: mismo `pre` de `src/clase/pipeline_clase.py` dentro de cada Pipeline
(pre refit por fold, sin fuga). SVR sobre submuestra 5k estratificada por
unidad (O(n^2) en 52k imposible). Guarda `resultados/comparativa.csv` y
`models/mejor_modelo_clase.joblib` (mejor por rmse_val; desempate al simple).
SAA-8: la tabla trae train + validación (medias out-of-fold del CV, sin
coste extra: multimetric sobre los mismos fits). El test se evalúa UNA sola
vez y solo para el elegido (SAA test-una-vez).
"""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GroupKFold, GridSearchCV
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR
from xgboost import XGBRegressor

from src.clase.pipeline_clase import make_pipeline

RANDOM_STATE = 42
CV = GroupKFold(n_splits=3)
# Multimétrica sobre los mismos fits (sin re-entrenos extra): el refit manda rmse.
SCORING = {"rmse": "neg_root_mean_squared_error",
           "mae": "neg_mean_absolute_error",
           "r2": "r2"}

ESPEC = {
    "regresion": (Ridge(random_state=RANDOM_STATE), {"reg__alpha": [0.1, 1.0, 10.0]}),
    "knn": (KNeighborsRegressor(), {"reg__n_neighbors": [5, 15, 31]}),
    "rf": (
        RandomForestRegressor(n_estimators=200, random_state=RANDOM_STATE, n_jobs=-1),
        {"reg__max_depth": [8, 15, None]},
    ),
    "xgb": (
        XGBRegressor(
            n_estimators=300, max_depth=4, learning_rate=0.05,
            subsample=0.8, colsample_bytree=0.8, n_jobs=-1,
            random_state=RANDOM_STATE, verbosity=0,
        ),
        {"reg__max_depth": [4, 6]},
    ),
    "svm": (
        SVR(),
        {"reg__C": [1.0, 10.0], "reg__epsilon": [0.5, 1.0]},
    ),
}
ORDEN_SIMPLE = {"regresion": 0, "knn": 1, "rf": 2, "xgb": 3, "svm": 4}
SVR_MUESTRA = 5_000
FOLD_VALIDACION = 0


def grupos_validacion(g_tr, n_splits: int = 3,
                      fold: int = FOLD_VALIDACION) -> np.ndarray:
    """Índices de la partición `fold` del GroupKFold por motor.

    Fuente única de "validación" para SHAP/permutación (SAA-9 v5:
    validación, nunca test). Determinista: mismo split que el CV.
    """
    gkf = GroupKFold(n_splits=n_splits)
    _, va = list(gkf.split(np.zeros(len(g_tr)), groups=g_tr))[fold]
    return np.asarray(va)


def _metricas_train(y_tr, p_tr) -> dict:
    return {
        "rmse_train": float(np.sqrt(mean_squared_error(y_tr, p_tr))),
        "mae_train": float(mean_absolute_error(y_tr, p_tr)),
        "r2_train": float(r2_score(y_tr, p_tr)),
    }


def _metricas_val(gs_gs) -> dict:
    """Validación honesta: medias out-of-fold del CV en los mejores params."""
    i = int(gs_gs.best_index_)
    cv = gs_gs.cv_results_
    return {
        "rmse_val": float(-cv["mean_test_rmse"][i]),
        "mae_val": float(-cv["mean_test_mae"][i]),
        "r2_val": float(cv["mean_test_r2"][i]),
    }


def _metricas_test(y_te, p_te) -> dict:
    return {
        "rmse_test": float(np.sqrt(mean_squared_error(y_te, p_te))),
        "mae_test": float(mean_absolute_error(y_te, p_te)),
        "r2_test": float(r2_score(y_te, p_te)),
    }


def entrenar_todo(sample_svm: int = SVR_MUESTRA, verbose: bool = True) -> pd.DataFrame:
    X_tr = pd.read_parquet("data/processed/X_train.parquet")
    y_tr = pd.read_parquet("data/processed/y_train.parquet").values.ravel().astype(float)
    X_te = pd.read_parquet("data/processed/X_test.parquet")
    y_te = pd.read_parquet("data/processed/y_test.parquet").values.ravel().astype(float)
    g_tr = X_tr["unit"].to_numpy()

    filas, pipes = [], {}
    for nombre, (reg, grid) in ESPEC.items():
        pipe = make_pipeline(reg)
        t0 = time.time()
        if nombre == "svm":
            rng = np.random.default_rng(RANDOM_STATE)
            idx = rng.choice(len(X_tr), size=min(sample_svm, len(X_tr)), replace=False)
            Xs, ys, gs = X_tr.iloc[idx], y_tr[idx], g_tr[idx]
            gs_gs = GridSearchCV(pipe, grid, cv=GroupKFold(3), scoring=SCORING,
                                 refit="rmse", n_jobs=-1)
            gs_gs.fit(Xs, ys, groups=gs)
        else:
            gs_gs = GridSearchCV(pipe, grid, cv=CV, scoring=SCORING,
                                 refit="rmse", n_jobs=-1)
            gs_gs.fit(X_tr, y_tr, groups=g_tr)
        secs = time.time() - t0
        best = gs_gs.best_estimator_
        m_tr = _metricas_train(y_tr, best.predict(X_tr))
        m_va = _metricas_val(gs_gs)
        m = {**m_tr, **m_va,
             "rmse_test": float("nan"), "mae_test": float("nan"),
             "r2_test": float("nan")}
        filas.append({"modelo": nombre, "mejores_params": str(gs_gs.best_params_),
                      "tiempo_s": round(secs, 1), **{k: round(v, 4) for k, v in m.items()}})
        pipes[nombre] = (best, gs_gs.best_params_)
        if verbose:
            print(f"{nombre}: RMSE val {m_va['rmse_val']:.3f} | {gs_gs.best_params_} | {secs:.0f}s")
    comp = pd.DataFrame(filas).sort_values("modelo")
    # Elección por validación; desempate documentado: a igualdad, el más simple.
    comp["_ord"] = comp["modelo"].map(ORDEN_SIMPLE)
    mejor = comp.sort_values(["rmse_val", "_ord"]).iloc[0]["modelo"]
    comp = comp.drop(columns=["_ord"])
    # Test UNA sola vez y solo para el elegido.
    best_pipe = pipes[mejor][0]
    m_te = _metricas_test(y_te, best_pipe.predict(X_te))
    for k, v in m_te.items():
        comp.loc[comp["modelo"] == mejor, k] = round(v, 4)
    comp.to_csv("resultados/comparativa.csv", index=False)
    joblib.dump(best_pipe, "models/mejor_modelo_clase.joblib")
    if verbose:
        print("mejor (por rmse_val):", mejor, "-> models/mejor_modelo_clase.joblib")
    return comp


if __name__ == "__main__":
    entrenar_todo()
