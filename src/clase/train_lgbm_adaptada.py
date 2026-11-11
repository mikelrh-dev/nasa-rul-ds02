"""Fase 5 (NB04): LGBM cuantil 0.35 sobre ventanas adaptadas honestas.

Prototipo barato antes del NB05: valida que el plumbing honesto
(re-imputación fit-units + `fit_preprocessing` + `build_windows`) funciona y
mide cuánto cuesta el MAR+ffill en la rama tabular. Sin `fase_vuelo`
(contrato 93 intacto). Grano ventana: la comparación con el E1-fila (7.70)
va en columna separada, prohibido el ranking mixto.
"""

from __future__ import annotations

import os
import sys
import time

import joblib
import numpy as np
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))

from ds02_rul.data import FIT_UNITS  # noqa: E402
from src.clase.ventanas_adaptadas import ventanas_adaptadas  # noqa: E402
from ds02_rul.metrics import evaluate_predictions  # noqa: E402
from ds02_rul.pipeline import make_lgbm  # noqa: E402

SEED = 42


def entrenar(verbose: bool = True) -> pd.DataFrame:
    """Entrena LightGBM en la base adaptada y mide el test una sola vez."""
    v = ventanas_adaptadas()
    dev, test = v["dev"], v["test"]
    w_units = dev["meta"]["unit"].to_numpy()
    fit_idx = np.where(np.isin(w_units, FIT_UNITS))[0]

    t0 = time.time()
    lgbm = make_lgbm(SEED).fit(dev["X_tab"][fit_idx], dev["y"][fit_idx])
    secs = time.time() - t0
    pred = lgbm.predict(test["X_tab"])
    m = evaluate_predictions(test["y"], pred, "LGBM-adaptada")
    fila = {"modelo": "lgbm_adaptada", "grano": "ventana",
            "tiempo_s": round(secs, 1),
            "rmse_test": round(float(m["RMSE"]), 4),
            "mae_test": round(float(m["MAE"]), 4),
            "r2_test": round(float(m["R2"]), 4),
            "nasa_test": round(float(m["NASA_Score"]), 1),
            "n_test": int(len(test["y"]))}
    comp = pd.DataFrame([fila])
    # Referencia histórica B (misma partición y grano, bundle congelado)
    comp = pd.concat([comp, pd.DataFrame([{
        "modelo": "lgbm_bundleB_hist", "grano": "ventana", "tiempo_s": None,
        "rmse_test": 7.098, "mae_test": 5.572, "r2_test": 0.8557,
        "nasa_test": 5772.5, "n_test": 6196,
    }])], ignore_index=True)
    comp.to_csv(os.path.join(_ROOT, "resultados", "comparativa_ventanas.csv"), index=False)
    out_dir = os.path.join(_ROOT, "src", "clase", "models")
    os.makedirs(out_dir, exist_ok=True)
    joblib.dump(lgbm, os.path.join(out_dir, "lgbm_adaptada.joblib"))
    if verbose:
        print(comp.to_string(index=False))
    return comp


if __name__ == "__main__":
    entrenar()
