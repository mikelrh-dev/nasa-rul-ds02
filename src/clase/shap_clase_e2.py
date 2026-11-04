"""SHAP sobre el MLP elegido E2 (SAA-9 de 7 a 10).

E2_reg_lr (alpha=1e-2, hidden (128,64)): elegido por rmse_val 7.3404 y
rmse_test 7.72 en `resultados/mlp_comparativa.csv`. Persistido como Pipeline
completo en `models/mejor_modelo_clase_E2.joblib` (ver `train_mlp.persistir_e2`).
NO toca `models/mejor_modelo_clase.joblib` (XGB) ni ningun otro artefacto
desplegado.

Diseño:
- Modelo: `reg.predict` del Pipeline E2 (MLPRegressor) sobre el espacio
  transformado por `pre` (pipeline_clase). `reg.predict(pre.transform(X))`
  es idéntico a `pipe.predict(X)`; la explicación vive en el espacio de
  entrada del regresor, donde el masker es numérico (la fase categórica
  cruda rompería Independent/Permutation de SHAP).
- Explainer: PermutationExplainer, masker Independent, budget 2*n+1
  (n = 22 features transformadas → 45), seed 42.
- Fondo (background): 200 filas de TRAIN fold-0 del GroupKFold(3)
  (groups=unit), muestreadas con seed 42. Nunca test.
- Explicadas: 200 filas de VALIDACIÓN fold-0 (nunca test — v5).
- Salida: RUL en ciclos (regresión).
- Aditividad validada por construcción: base + suma(SHAP) == predict con
  rtol 1e-5, atol 1e-6 (la aproximación por permutaciones conserva la
  eficiencia exacta: cada permutación telescopa).

Salidas: `resultados/mlp_shap_E2/{bar,beeswarm,waterfall}.png`,
`importancia.csv`, `metadata.json`.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import GroupKFold

from src.clase.pipeline_clase import FEATURE_COLS
from src.clase.train_mlp import E2_MODEL_PATH

N_FONDO = 200
N_EXPLICADAS = 200
SEED = 42
OUT_DIR = "resultados/mlp_shap_E2"
RTOL = 1e-5
ATOL = 1e-6
STATEMENT = ("SHAP describe el modelo, no el motor: asociaciones no causales.")

try:
    import sklearn
    import shap as _shap
    import xgboost

    VERSIONES = {"shap": _shap.__version__, "sklearn": sklearn.__version__,
                 "xgboost": xgboost.__version__, "pandas": pd.__version__,
                 "numpy": np.__version__}
except Exception:  # pragma: no cover
    VERSIONES = {}


def split_fold0(X_tr: pd.DataFrame, n_splits: int = 3, fold: int = 0):
    """(train_idx, val_idx) del fold dado del GroupKFold por motor."""
    g = X_tr["unit"].to_numpy()
    tr, va = list(GroupKFold(n_splits=n_splits).split(np.zeros(len(g)), groups=g))[fold]
    return tr, va


def validar_aditividad(base, valores, pred, rtol: float = RTOL, atol: float = ATOL) -> float:
    """Devuelve el error máximo |base+suma-pred|; asserts rtol/atol."""
    base = np.asarray(base, dtype=float).ravel()
    valores = np.asarray(valores, dtype=float)
    pred = np.asarray(pred, dtype=float).ravel()
    assert valores.shape == (len(pred), valores.shape[1])
    recon = base + valores.sum(axis=1)
    err = float(np.abs(recon - pred).max())
    assert np.allclose(recon, pred, rtol=rtol, atol=atol), f"aditividad rota: {err}"
    return err


def ejecutar_shap(
    n_filas: int = N_EXPLICADAS,
    n_fondo: int = N_FONDO,
    seed: int = SEED,
    modelo: str = E2_MODEL_PATH,
    out_dir: str = OUT_DIR,
    verbose: bool = True,
) -> pd.DataFrame:
    """SHAP Permutation sobre E2. Guarda PNGs + CSV + metadata.json."""
    if not os.path.exists(modelo):
        from src.clase.train_mlp import persistir_e2

        persistir_e2(destino=modelo, verbose=verbose)
    pipe = joblib.load(modelo)
    pre, reg = pipe.named_steps["pre"], pipe.named_steps["reg"]
    nombres = list(pre.get_feature_names_out())
    assert not any(n.startswith("f") and n[1:].isdigit() for n in nombres), nombres

    X_tr = pd.read_parquet("data/processed/X_train.parquet").reset_index(drop=True)
    tr, va = split_fold0(X_tr)

    rng = np.random.default_rng(seed)
    # Fondo: SOLO train fold-0 (nunca test). Explicadas: validación fold-0.
    bg_idx = rng.choice(tr, size=min(n_fondo, len(tr)), replace=False)
    Z_fondo = pre.transform(X_tr.iloc[bg_idx][FEATURE_COLS])
    ex_idx = va[: min(n_filas, len(va))]
    Z_exp = pre.transform(X_tr.iloc[ex_idx][FEATURE_COLS])
    X_exp_raw = X_tr.iloc[ex_idx][FEATURE_COLS]

    masker = shap.maskers.Independent(data=Z_fondo)
    explainer = shap.PermutationExplainer(reg.predict, masker=masker, seed=seed)
    budget = 2 * len(nombres) + 1
    resp = explainer(Z_exp, max_evals=budget, silent=not verbose)
    valores = np.asarray(resp.values, dtype=float)
    base = np.asarray(resp.base_values, dtype=float).ravel()
    pred = pipe.predict(X_exp_raw)
    err = validar_aditividad(base, valores, pred)

    imp = (
        pd.DataFrame({
            "feature": nombres,
            "mean_abs_shap": np.abs(valores).mean(axis=0),
            "mean_shap": valores.mean(axis=0),
            "std_shap": valores.std(axis=0),
        })
        .sort_values("mean_abs_shap", ascending=False)
        .reset_index(drop=True)
    )

    os.makedirs(out_dir, exist_ok=True)
    imp.to_csv(os.path.join(out_dir, "importancia.csv"), index=False)

    top = imp.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(top["feature"], top["mean_abs_shap"])
    ax.set_xlabel("mean |SHAP| (ciclos RUL)")
    ax.set_title(f"SHAP Permutation — MLP E2 ({len(ex_idx)} filas validación fold-0)")
    fig.tight_layout()
    fig.savefig(os.path.join(out_dir, "bar.png"), dpi=120)
    plt.close(fig)

    fig = plt.figure()
    shap.plots.beeswarm(resp, show=False)
    fig.savefig(os.path.join(out_dir, "beeswarm.png"), dpi=120, bbox_inches="tight")
    plt.close(fig)

    fig = plt.figure()
    shap.plots.waterfall(resp[0], show=False)
    fig.savefig(os.path.join(out_dir, "waterfall.png"), dpi=120, bbox_inches="tight")
    plt.close(fig)

    meta = {
        "modelo": "MLP E2_reg_lr (alpha=1e-2, hidden (128,64))",
        "ruta_modelo": modelo,
        "output": "RUL regression (RUL en ciclos)",
        "unidades": "ciclos RUL",
        "explainer": "PermutationExplainer",
        "masker": "Independent",
        "n_features": len(nombres),
        "budget": budget,
        "n_background": len(bg_idx),
        "background": ("200 train fold-0 GroupKFold(3) groups=unit, "
                       "seed 42 (nunca test)"),
        "n_explicadas": len(ex_idx),
        "explicadas": "validación fold-0 GroupKFold(3) (nunca test)",
        "seed": seed,
        "aditividad_max_error": err,
        "aditividad_tol": {"rtol": RTOL, "atol": ATOL},
        "versiones": VERSIONES,
        "nota": STATEMENT,
    }
    with open(os.path.join(out_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    if verbose:
        print(imp.head(5).to_string(index=False))
        print(f"aditividad: max error {err:.2e} | guardado: {out_dir}/")
    return imp


if __name__ == "__main__":
    ejecutar_shap()
