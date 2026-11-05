"""SHAP real sobre el track de clase (SAA-9: explainer/masker/fondo explícitos).

Estrategia honesta y barata, SIN reentreno (v5):
- Modelo: XGB ya entrenado en `models/mejor_modelo_clase.joblib` (Pipeline
  pre + XGB elegido por validación en `resultados/comparativa.csv`).
  TreeExplainer exacto, segundos en 200 filas. La carga del joblib es lazy
  (dentro de `ejecutar_shap`, no a nivel de módulo) para no arrastrar el
  modelo al importar este módulo.
- Fondo (masker): 200 filas de train transformadas con el `pre` persistido.
- Explicadas: 200 filas de VALIDACIÓN (fold-0 del GroupKFold, nunca test).
- Check de aditividad: base (expected_value) + suma(SHAP) == predicción,
  con assert y tolerancia 1e-5; si falla, el error se declara, no se oculta.

Salidas: `resultados/shap_importancia.png` (barras mean|SHAP|) y
`resultados/shap_importancia.csv` (tabla top-k).
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import joblib  # noqa: F401
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap

from src.clase.pipeline_clase import FEATURE_COLS

N_FILAS = 200
SEED = 7
MODEL_PATH = "models/mejor_modelo_clase.joblib"
ADITIVIDAD_TOL = 1e-5


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


def check_aditividad(sv: np.ndarray, base: float,
                     pred: np.ndarray, tol: float = ADITIVIDAD_TOL) -> float:
    """Comprueba base + suma(SHAP) == predicción (tol relativa). Devuelve error max."""
    suma = base + np.asarray(sv).sum(axis=1)
    pred = np.asarray(pred, dtype=float)
    error = float(np.abs(suma - pred).max())
    # XGB predice en float32: contra |pred| max se compara en relativo.
    assert error < tol * float(np.abs(pred).max()), (
        f"SHAP no aditivo: base+suma(SHAP) != predict "
        f"(error max {error:.3e} >= tol relativa {tol:.3e})"
    )
    return error


def ejecutar_shap(
    n_filas: int = N_FILAS,
    seed: int = SEED,
    png: str = "resultados/shap_importancia.png",
    csv: str = "resultados/shap_importancia.csv",
    top_k: int = 10,
    verbose: bool = True,
) -> pd.DataFrame:
    """Explica el XGB persistido (sin reentrenar) con TreeExplainer; guarda PNG+CSV."""
    from src.clase.train_clasicos import grupos_validacion

    # SEC-JOBLIB-01: checksum verificado ANTES de deserializar (sin checksum
    # válido, RuntimeError sin tocar el pickle). Lazy a propósito: importar
    # este módulo no carga el modelo.
    from src.ds02_rul.persistence import verify_artifact_sha256

    verify_artifact_sha256(MODEL_PATH, "clase_xgb_sha256")
    pipe = joblib.load(MODEL_PATH)
    pre = pipe.named_steps["pre"]
    reg = pipe.named_steps["reg"]
    nombres = list(pre.get_feature_names_out())

    Xtr = pd.read_parquet("data/processed/X_train.parquet")
    va = grupos_validacion(Xtr["unit"].to_numpy())
    Xva = Xtr.iloc[va].reset_index(drop=True)
    unidades_va = sorted(float(u) for u in Xtr.iloc[va]["unit"].unique())

    Ztr = pre.transform(Xtr[FEATURE_COLS])  # fondo: train transformado
    fondo = shap.sample(Ztr, min(n_filas, len(Ztr)), random_state=seed)
    explainer = shap.TreeExplainer(reg, data=fondo)  # explainer + fondo explícitos

    Zva = pre.transform(Xva[FEATURE_COLS])  # masker: filas de validación
    Zexp = Zva[:n_filas]
    sv = np.asarray(explainer.shap_values(Zexp), dtype=float)
    base = float(np.asarray(explainer.expected_value).ravel()[0])
    pred = np.asarray(reg.predict(Zexp), dtype=float)
    error_adit = check_aditividad(sv, base, pred)

    top = top_shap(sv, nombres, k=top_k)
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
                 "unidades": unidades_va,
                 "aditividad_max_error": error_adit},
                "src/clase/models/shap_xgb_top.joblib")
    if verbose:
        print(top.to_string(index=False))
        print(f"guardado: {png} + {csv} (aditividad_max_error={error_adit:.2e})")
    return top


if __name__ == "__main__":
    ejecutar_shap()
