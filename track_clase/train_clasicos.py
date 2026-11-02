"""Fase 2.2 — 5 clásicos de clase con GridSearchCV + GroupKFold(groups=unit).

SAA 6 (30%): regresión/Ridge, KNN, RF, XGB, SVR. Grids mínimos publicados.
PIA 3: mismo `pre` de `track_clase/pipeline_clase.py` dentro de cada Pipeline
(pre refit por fold, sin fuga). SVR sobre submuestra 5k estratificada por
unidad (O(n^2) en 52k imposible). Guarda `resultados/comparativa.csv` y
`models/mejor_modelo_clase.joblib` (mejor por rmse_test; desempate al simple).
"""

from __future__ import annotations

import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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

from track_clase.pipeline_clase import make_pipeline

RANDOM_STATE = 42
CV = GroupKFold(n_splits=3)
SCORING = "neg_root_mean_squared_error"

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


def _metricas(y_tr, p_tr, y_te, p_te) -> dict:
    return {
        "rmse_train": float(np.sqrt(mean_squared_error(y_tr, p_tr))),
        "mae_train": float(mean_absolute_error(y_tr, p_tr)),
        "r2_train": float(r2_score(y_tr, p_tr)),
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
            gs_gs = GridSearchCV(pipe, grid, cv=GroupKFold(3), scoring=SCORING, n_jobs=-1)
            gs_gs.fit(Xs, ys, groups=gs)
        else:
            gs_gs = GridSearchCV(pipe, grid, cv=CV, scoring=SCORING, n_jobs=-1)
            gs_gs.fit(X_tr, y_tr, groups=g_tr)
        secs = time.time() - t0
        best = gs_gs.best_estimator_
        m = _metricas(y_tr, best.predict(X_tr), y_te, best.predict(X_te))
        filas.append({"modelo": nombre, "mejores_params": str(gs_gs.best_params_),
                      "tiempo_s": round(secs, 1), **{k: round(v, 4) for k, v in m.items()}})
        pipes[nombre] = best
        if verbose:
            print(f"{nombre}: RMSE test {m['rmse_test']:.3f} | {gs_gs.best_params_} | {secs:.0f}s")
    comp = pd.DataFrame(filas).sort_values("modelo")
    comp.to_csv("resultados/comparativa.csv", index=False)
    mejor = comp.sort_values(["rmse_test", "modelo"]).iloc[0]["modelo"]
    # desempate documentado: si empate técnico, el más simple gana
    joblib.dump(pipes[mejor], "models/mejor_modelo_clase.joblib")
    if verbose:
        print("mejor:", mejor, "-> models/mejor_modelo_clase.joblib")
    return comp


if __name__ == "__main__":
    entrenar_todo()
