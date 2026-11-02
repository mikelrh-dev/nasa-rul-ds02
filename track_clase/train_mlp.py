"""Fase 2.3 — MLP base + 3 experimentos + importancia del mejor clásico.

SAA 7: base + E1 capacidad / E2 reg-lr / E3 batch-early, cada uno con hipótesis.
SAA 9-parcial: importancia por permutación sobre el mejor clásico (SVM) con
200 filas test (fallback declarado: `shap` no está en requirements; la
trazabilidad SHAP — explainer/masker/fondo — queda para el change MLflow).
Todo con el `pre` compartido (sin fuga) y test tocado 1 vez.
"""

from __future__ import annotations

import os
import sys
import time

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from track_clase.pipeline_clase import make_pipeline  # noqa: E402

RANDOM_STATE = 42
BASE_KW = dict(activation="relu", learning_rate_init=1e-3, max_iter=300,
               early_stopping=True, random_state=RANDOM_STATE, verbose=False)

EXPS = {
    "base": (dict(hidden_layer_sizes=(128, 64), alpha=1e-3), "MLP medio: RUL no lineal por régimen, 2 capas bastan sin memorizar."),
    "E1_capacidad": (dict(hidden_layer_sizes=(256, 128, 64), alpha=1e-3), "Más capacidad capta interacción régimen-degradación hasta overfit."),
    "E2_reg_lr": (dict(hidden_layer_sizes=(128, 64), alpha=1e-2), "Más regularización frena memorización de 93 feats ruidosas."),
    "E3_batch": (dict(hidden_layer_sizes=(128, 64), alpha=1e-3, batch_size=1024), "Batch grande estabiliza gradiente en ventanas correladas."),
}


def _m(y_tr, p_tr, y_te, p_te) -> dict:
    return {
        "rmse_train": round(float(np.sqrt(mean_squared_error(y_tr, p_tr))), 4),
        "mae_train": round(float(mean_absolute_error(y_tr, p_tr)), 4),
        "r2_train": round(float(r2_score(y_tr, p_tr)), 4),
        "rmse_test": round(float(np.sqrt(mean_squared_error(y_te, p_te))), 4),
        "mae_test": round(float(mean_absolute_error(y_te, p_te)), 4),
        "r2_test": round(float(r2_score(y_te, p_te)), 4),
    }


def entrenar_mlp(verbose: bool = True) -> pd.DataFrame:
    X_tr = pd.read_parquet("data/processed/X_train.parquet")
    y_tr = pd.read_parquet("data/processed/y_train.parquet").values.ravel().astype(float)
    X_te = pd.read_parquet("data/processed/X_test.parquet")
    y_te = pd.read_parquet("data/processed/y_test.parquet").values.ravel().astype(float)
    filas = []
    for nombre, (kw, hipotesis) in EXPS.items():
        pipe = make_pipeline(MLPRegressor(**{**BASE_KW, **kw}))
        t0 = time.time()
        pipe.fit(X_tr, y_tr)
        secs = time.time() - t0
        m = _m(y_tr, pipe.predict(X_tr), y_te, pipe.predict(X_te))
        filas.append({"experimento": nombre, "hipotesis": hipotesis,
                      "params": str(kw), "tiempo_s": round(secs, 1), **m})
        if verbose:
            print(f"{nombre}: RMSE test {m['rmse_test']:.3f} | {secs:.0f}s")
    comp = pd.DataFrame(filas)
    comp.to_csv("resultados/mlp_comparativa.csv", index=False)
    return comp


def importancia_mejor_clasico(n_filas: int = 200, seed: int = 7) -> pd.DataFrame:
    """Permutación sobre el mejor clásico (SVM): qué variables pesan más.

    200 filas test, 5 repeticiones, scoring RMSE. No causal: describe el modelo,
    no el motor. SHAP (explainer/masker/fondo explícitos) queda para el change
    MLflow donde se pinnea `shap[plots]==0.52.0`.
    """
    pipe = joblib.load("models/mejor_modelo_clase.joblib")
    X_te = pd.read_parquet("data/processed/X_test.parquet").reset_index(drop=True)
    y_te = pd.read_parquet("data/processed/y_test.parquet").reset_index(drop=True).values.ravel().astype(float)
    rng = np.random.default_rng(seed)
    pos = rng.choice(len(X_te), size=min(n_filas, len(X_te)), replace=False)
    muestra = X_te.iloc[pos].reset_index(drop=True)
    y_mu = y_te[pos]
    r = permutation_importance(pipe, muestra, y_mu, n_repeats=5,
                               scoring="neg_root_mean_squared_error",
                               random_state=seed, n_jobs=-1)
    # permutation_importance permuta columnas de ENTRADA (21: 19 num + fase),
    # no las transformadas (22 tras OneHot): los nombres son los de muestra.
    nombres = list(muestra.columns)
    assert len(nombres) == len(r.importances_mean), (len(nombres), len(r.importances_mean))
    imp = pd.DataFrame({"variable": nombres, "peso": r.importances_mean,
                        "peso_std": r.importances_std}).sort_values("peso", ascending=False)
    imp.to_csv("resultados/importancia_permutacion.csv", index=False)
    top = imp.head(15).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(top["variable"], top["peso"], xerr=top["peso_std"])
    ax.set_title("Importancia por permutación — mejor clásico (SVM, 200 filas test)")
    ax.set_xlabel("caída RMSE al permutar")
    fig.tight_layout()
    fig.savefig("resultados/importancia_permutacion.png", dpi=120)
    plt.close(fig)
    print("top3:", ", ".join(imp.head(3)["variable"].tolist()))
    return imp


if __name__ == "__main__":
    entrenar_mlp()
    importancia_mejor_clasico()
