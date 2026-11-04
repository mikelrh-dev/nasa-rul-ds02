"""SHAP real sobre el track de clase (SAA-9: explainer/masker/fondo explícitos).

Estrategia honesta y barata:
- Modelo: XGBRegressor (elegido por validación) con los mejores hiperparámetros
  de `resultados/comparativa.csv`. TreeExplainer exacto, segundos en 200 filas.
- Fondo (masker): 200 filas de train transformadas.
- Explicadas: 200 filas de VALIDACIÓN (fold-0 del GroupKFold, nunca test — v5).
- La permutación sobre el XGB elegido se mantiene como lectura complementaria;
  SHAP responde "qué variables pesan más" con atribución aditiva por predicción.

Salidas: `resultados/shap_importancia.png` (barras mean|SHAP|) y
`resultados/shap_importancia.csv` (tabla top-k).
"""

from __future__ import annotations

import ast
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
from xgboost import XGBRegressor

from src.clase.pipeline_clase import FEATURE_COLS, make_pre

N_FILAS = 200
SEED = 7


def top_shap(shap_values: np.ndarray, nombres: list[str], k: int = 10) -> pd.DataFrame:
    """Tabla top-k por media de |SHAP| (pura, testeable sin entrenar nada)."""
    media = np.abs(np.asarray(shap_values)).mean(axis=0)
    top = (
        pd.DataFrame({"feature": list(nombres), "mean_abs_shap": media})
        .sort_values("mean_abs_shap", ascending=False)
        .head(k)
        .reset_index(drop=True)
    )
    return top


def ejecutar_shap(
    n_filas: int = N_FILAS,
    seed: int = SEED,
    png: str = "resultados/shap_importancia.png",
    csv: str = "resultados/shap_importancia.csv",
    top_k: int = 10,
    verbose: bool = True,
) -> pd.DataFrame:
    """Entrena XGB (mejores params de comparativa.csv), TreeExplainer, guarda PNG+CSV."""
    from src.clase.train_clasicos import grupos_validacion
    Xtr = pd.read_parquet("data/processed/X_train.parquet")
    ytr = pd.read_parquet("data/processed/y_train.parquet").values.ravel()
    va = grupos_validacion(Xtr["unit"].to_numpy())
    Xva = Xtr.iloc[va].reset_index(drop=True)
    unidades_va = sorted(float(u) for u in Xtr.iloc[va]["unit"].unique())
    comp = pd.read_csv("resultados/comparativa.csv")
    params = ast.literal_eval(    comp.loc[comp["modelo"] == "xgb", "mejores_params"].iloc[0])
    kw = params.get("reg__", params)
    kw = {k.replace("reg__", ""): v for k, v in kw.items()}

    pre = make_pre().fit(Xtr[FEATURE_COLS])
    nombres = list(pre.get_feature_names_out())
    Ztr = pre.transform(Xtr[FEATURE_COLS])

    base = dict(n_estimators=300, max_depth=6, learning_rate=0.05,
                subsample=0.8, random_state=seed, n_jobs=-1)
    base.update(kw)
    reg = XGBRegressor(**base)
    reg.fit(Ztr, ytr)

    Zva = pre.transform(Xva[FEATURE_COLS])
    fondo = shap.sample(Ztr, min(n_filas, len(Ztr)), random_state=seed)
    explainer = shap.TreeExplainer(reg, data=fondo)  # explainer + fondo explícitos
    sv = explainer.shap_values(Zva[:n_filas])  # masker: filas de validación
    top = top_shap(np.asarray(sv), nombres, k=top_k)
    top.to_csv(csv, index=False)

    fig, ax = plt.subplots(figsize=(7, 4.5))
    d = top.iloc[::-1]
    ax.barh(d["feature"], d["mean_abs_shap"])
    ax.set_xlabel("mean |SHAP| (ciclos RUL)")
    ax.set_title(f"SHAP — XGB clase ({n_filas} filas validación, TreeExplainer exacto)")
    fig.tight_layout()
    fig.savefig(png, dpi=120)
    plt.close(fig)
    joblib.dump({"nombres": nombres, "top": top, "fuente": "validacion-fold0",
                 "unidades": unidades_va}, "src/clase/models/shap_xgb.joblib")
    if verbose:
        print(top.to_string(index=False))
        print(f"guardado: {png} + {csv}")
    return top


if __name__ == "__main__":
    ejecutar_shap()
