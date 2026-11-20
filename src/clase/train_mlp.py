"""Fase 2.3: MLP base, tres experimentos e importancia del mejor clásico.

Se prueban base, E1 (capacidad), E2 (regularización) y E3 (batch), cada uno con
su hipótesis. La importancia por permutación se mide sobre el mejor clásico
(XGB) con 200 filas de validación (fold-0). Todo usa el `pre` compartido y sin
fuga. La tabla trae train y validación (OOF de GroupKFold(3) por motor); el test
se evalúa UNA sola vez y solo para el elegido por `rmse_val`.
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
from sklearn.model_selection import GroupKFold, cross_val_predict
from sklearn.neural_network import MLPRegressor

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.clase.pipeline_clase import make_pipeline  # noqa: E402

RANDOM_STATE = 42
BASE_KW = dict(activation="relu", learning_rate_init=1e-3, max_iter=300,
               early_stopping=True, random_state=RANDOM_STATE, verbose=False)

EXPS = {
    "base": (dict(hidden_layer_sizes=(128, 64), alpha=1e-3), "MLP medio: RUL no lineal por régimen, 2 capas bastan sin memorizar."),
    "E1_capacidad": (dict(hidden_layer_sizes=(256, 128, 64), alpha=1e-3), "Más capacidad capta interacción régimen-degradación hasta overfit."),
    "E2_reg_lr": (dict(hidden_layer_sizes=(128, 64), alpha=1e-2), "Más regularización frena memorización de 22 feats transformadas (19 num + fase_vuelo) ruidosas."),
    "E3_batch": (dict(hidden_layer_sizes=(128, 64), alpha=1e-3, batch_size=1024), "Batch grande estabiliza gradiente en ventanas correladas."),
}


ORDEN_MLP = {"base": 0, "E2_reg_lr": 1, "E3_batch": 2, "E1_capacidad": 3}
CV_MLP = GroupKFold(n_splits=3)
# E2 se eligió por rmse_val (7.3404) y rmse_test 7.72 en resultados/mlp_comparativa.csv.
# Se guarda aparte para el SHAP del MLP; NO pisa mejor_modelo_clase.joblib (XGB).
E2_MODEL_PATH = "models/mejor_modelo_clase_E2.joblib"
# XGB de clase (mejor clásico): también guardado por SEC-JOBLIB-01.
CLASE_MODEL_PATH = "models/mejor_modelo_clase.joblib"


def _registrar_checksum_e2() -> None:
    """Refresca `clase_e2_sha256` en `models/ds02_manifest.json` (SEC-JOBLIB-01).

    Tras persistir E2, el digest registrado quedaría obsoleto y el guard
    rechazaría la carga válida. Idempotente; conserva CRLF/indent-2.
    """
    import json

    from src.ds02_rul.persistence import sha256_of

    destino = os.path.join(_ROOT, E2_MODEL_PATH)
    manifest_path = os.path.join(_ROOT, "models", "ds02_manifest.json")
    if not os.path.exists(destino) or not os.path.exists(manifest_path):
        return
    with open(manifest_path, encoding="utf-8") as fh:
        manifest = json.load(fh)
    manifest.setdefault("artifacts", {})["clase_e2_sha256"] = sha256_of(destino)
    texto = json.dumps(manifest, indent=2, ensure_ascii=False)
    with open(manifest_path, "wb") as fh:
        fh.write(texto.replace("\n", "\r\n").encode("utf-8"))


def _m_train(y_tr, p_tr) -> dict:
    return {
        "rmse_train": round(float(np.sqrt(mean_squared_error(y_tr, p_tr))), 4),
        "mae_train": round(float(mean_absolute_error(y_tr, p_tr)), 4),
        "r2_train": round(float(r2_score(y_tr, p_tr)), 4),
    }


def _m_oof(y_tr, oof) -> dict:
    """Validación honesta: predicciones out-of-fold del CV por motor."""
    return {
        "rmse_val": round(float(np.sqrt(mean_squared_error(y_tr, oof))), 4),
        "mae_val": round(float(mean_absolute_error(y_tr, oof)), 4),
        "r2_val": round(float(r2_score(y_tr, oof)), 4),
    }


def _m_test(y_te, p_te) -> dict:
    return {
        "rmse_test": round(float(np.sqrt(mean_squared_error(y_te, p_te))), 4),
        "mae_test": round(float(mean_absolute_error(y_te, p_te)), 4),
        "r2_test": round(float(r2_score(y_te, p_te)), 4),
    }


# Compat: el NB02 espeja el loop con estas piezas (ver celda 15).
def _m(y_tr, p_tr, y_te, p_te) -> dict:
    return {**_m_train(y_tr, p_tr), **_m_test(y_te, p_te)}


def entrenar_mlp(verbose: bool = True) -> pd.DataFrame:
    """Entrena base/E1/E2/E3, elige por validación y mide el test una vez."""
    X_tr = pd.read_parquet("data/processed/X_train.parquet")
    y_tr = pd.read_parquet("data/processed/y_train.parquet").values.ravel().astype(float)
    X_te = pd.read_parquet("data/processed/X_test.parquet")
    y_te = pd.read_parquet("data/processed/y_test.parquet").values.ravel().astype(float)
    g_tr = X_tr["unit"].to_numpy()
    filas, pipes = [], {}
    for nombre, (kw, hipotesis) in EXPS.items():
        t0 = time.time()
        pipe = make_pipeline(MLPRegressor(**{**BASE_KW, **kw}))
        pipe.fit(X_tr, y_tr)
        secs = time.time() - t0
        oof = cross_val_predict(make_pipeline(MLPRegressor(**{**BASE_KW, **kw})),
                                X_tr, y_tr, groups=g_tr, cv=CV_MLP, n_jobs=1)
        m = {**_m_train(y_tr, pipe.predict(X_tr)), **_m_oof(y_tr, oof),
             "rmse_test": float("nan"), "mae_test": float("nan"),
             "r2_test": float("nan")}
        filas.append({"experimento": nombre, "hipotesis": hipotesis,
                      "params": str(kw), "tiempo_s": round(secs, 1), **m})
        pipes[nombre] = pipe
        if verbose:
            print(f"{nombre}: RMSE val {m['rmse_val']:.3f} | {secs:.0f}s")
    comp = pd.DataFrame(filas)
    comp["_ord"] = comp["experimento"].map(ORDEN_MLP)
    mejor = comp.sort_values(["rmse_val", "_ord"]).iloc[0]["experimento"]
    comp = comp.drop(columns=["_ord"])
    m_te = _m_test(y_te, pipes[mejor].predict(X_te))
    for k, v in m_te.items():
        comp.loc[comp["experimento"] == mejor, k] = v
    comp.to_csv("resultados/mlp_comparativa.csv", index=False)
    if verbose:
        print("mejor (por rmse_val):", mejor)
    # E2 se guarda siempre (Pipeline completo), aunque no sea el mejor numérico:
    # es el modelo que se explica con SHAP. Va en una ruta aparte del XGB.
    joblib.dump(pipes["E2_reg_lr"], E2_MODEL_PATH)
    _registrar_checksum_e2()
    if verbose:
        print("guardado E2:", E2_MODEL_PATH)
    return comp


def persistir_e2(destino: str = E2_MODEL_PATH, verbose: bool = True):
    """Entrena SOLO E2_reg_lr sobre todo el train y guarda el Pipeline completo.

    No toca `models/mejor_modelo_clase.joblib` (XGB verificado, steps[1]
    XGBRegressor) ni ningun otro artefacto desplegado.
    """
    X_tr = pd.read_parquet("data/processed/X_train.parquet")
    y_tr = pd.read_parquet("data/processed/y_train.parquet").values.ravel().astype(float)
    kw, _ = EXPS["E2_reg_lr"]
    pipe = make_pipeline(MLPRegressor(**{**BASE_KW, **kw}))
    pipe.fit(X_tr, y_tr)
    joblib.dump(pipe, destino)
    _registrar_checksum_e2()
    if verbose:
        print("guardado E2:", destino)
    return pipe


def importancia_mejor_clasico(n_filas: int = 200, seed: int = 7) -> pd.DataFrame:
    """Permutación sobre el mejor clásico (XGB): qué variables pesan más.

    200 filas de VALIDACIÓN (fold-0, nunca test — v5), 5 repeticiones,
    scoring RMSE. No causal: describe el modelo, no el motor.
    """
    from src.clase.train_clasicos import grupos_validacion
    # SEC-JOBLIB-01: checksum verificado ANTES de deserializar.
    from src.ds02_rul.persistence import verify_artifact_sha256

    verify_artifact_sha256(CLASE_MODEL_PATH, "clase_xgb_sha256")
    pipe = joblib.load(CLASE_MODEL_PATH)
    X_tr = pd.read_parquet("data/processed/X_train.parquet").reset_index(drop=True)
    y_tr = pd.read_parquet("data/processed/y_train.parquet").reset_index(drop=True).values.ravel().astype(float)
    va = grupos_validacion(X_tr["unit"].to_numpy())
    X_va, y_va = X_tr.iloc[va].reset_index(drop=True), y_tr[va]
    rng = np.random.default_rng(seed)
    pos = rng.choice(len(X_va), size=min(n_filas, len(X_va)), replace=False)
    muestra = X_va.iloc[pos].reset_index(drop=True)
    y_mu = y_va[pos]
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
    ax.set_title("Importancia por permutación — mejor clásico (XGB, 200 filas validación)")
    ax.set_xlabel("caída RMSE al permutar")
    fig.tight_layout()
    fig.savefig("resultados/importancia_permutacion.png", dpi=120)
    plt.close(fig)
    print("top3:", ", ".join(imp.head(3)["variable"].tolist()))
    return imp


if __name__ == "__main__":
    entrenar_mlp()
    importancia_mejor_clasico()
