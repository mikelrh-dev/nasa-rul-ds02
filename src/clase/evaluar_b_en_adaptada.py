"""B congelado bajo dropout: ¿cuánto pierde el campeón con señal degradada?

Solo inferencia sobre el bundle de `models/` (lectura; nunca se escribe ahí).
Protocolo:
1. `medianas_produccion` — medianas de sensores del train LIMPIO de B
   (`train.parquet`, fit-units): lo que producción conocería.
2. `imputar_como_produccion` — ffill causal por unidad + esas medianas.
3. `ventanas_bajo_dropout` — `build_windows(step=2)` sobre el test adaptado
   con los OBJETOS ajustados del propio bundle (scaler/scaler_w/
   residualizer): exactamente lo que producción aplica en `_tabular`.
4. `evaluar` — `predict` del ensemble congelado + RMSE/MAE/R²/NASA.

Regla pre-registrada (puerta D11-bis):
- B_dropout claramente peor que C (RMSE > 4.314 + 0.05) → C gana donde
  importa: re-freeze justificado, C a producción.
- B_dropout ≈ B_limpio (±0.05) → el ffill repara la señal y el dropout no
  muerde: B sigue; el pipeline es insensible a este régimen.
- Tierra de nadie → B sigue (no se toca lo que funciona).
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))

from src.clase.dataset_clase import OP_COLS, SENSOR_COLS  # noqa: E402
from ds02_rul.features import build_windows  # noqa: E402
from ds02_rul.metrics import evaluate_predictions, macro_rmse  # noqa: E402

FIT_UNITS = [2.0, 5.0, 10.0, 18.0, 20.0]
TEST_UNITS = [11.0, 14.0, 15.0]
C_MEAN = {"rmse": 4.314, "nasa": 2339.1}  # multiseed (42, 7, 123)
B_CLEAN = {"rmse": 4.251, "nasa": 2305.1}  # bundle congelado, dato limpio


def medianas_produccion() -> pd.Series:
    """Medianas del train LIMPIO de B (fit-units). Sin fuga por construcción."""
    limpio = pd.read_parquet(
        os.path.join(_ROOT, "data", "processed", "train.parquet")
    )
    fit = limpio[limpio["unit"].isin(FIT_UNITS)]
    return fit[SENSOR_COLS].median(numeric_only=True)


def imputar_como_produccion(
    df: pd.DataFrame, medianas: pd.Series
) -> pd.DataFrame:
    """ffill causal por unidad en orden temporal + medianas de producción."""
    orden = df.sort_values(["unit", "cycle"]).reset_index(drop=True)
    out = orden.copy()
    out[SENSOR_COLS] = out.groupby("unit", sort=False)[SENSOR_COLS].ffill()
    out[SENSOR_COLS] = out[SENSOR_COLS].fillna(medianas)
    return out


def prep_de_b() -> dict:
    """Los objetos ajustados del propio bundle congelado (solo lectura).

    Se intentó reproducir el `prep` reajustando sobre `train.parquet` limpio,
    pero difiere del bundle en la media de T30 (0.054): el bundle committed
    se ajustó en una ejecución distinta. Reusar sus objetos es además lo más
    fiel: es exactamente lo que producción aplica en `ensemble._tabular`.
    """
    from functools import lru_cache

    from ds02_rul.persistence import load_ensemble

    @lru_cache(maxsize=1)
    def _bundle():
        return load_ensemble(os.path.join(_ROOT, "models", "ensemble.joblib"))

    ens = _bundle()
    assert int(ens.scaler.n_features_in_) == 18
    return {
        "scaler": ens.scaler,
        "scaler_w": ens.scaler_w,
        "residualizer": ens.residualizer,
    }


def ventanas_bajo_dropout() -> dict:
    """Ventanas del test adaptado con el preproceso de B (mismo grid que C)."""
    con = pd.read_parquet(
        os.path.join(_ROOT, "data", "processed", "test_con_nulos.parquet")
    )
    imp = imputar_como_produccion(con, medianas_produccion())
    assert int(imp[SENSOR_COLS].isna().sum().sum()) == 0
    return build_windows(
        imp[OP_COLS].to_numpy(dtype=np.float64),
        imp[SENSOR_COLS].to_numpy(dtype=np.float64),
        imp["RUL"].to_numpy(dtype=float),
        imp["unit"].to_numpy(dtype=float),
        imp["cycle"].to_numpy(dtype=float),
        prep_de_b(),
        window_size=50,
        step=2,
    )


def evaluar(verbose: bool = True) -> dict:
    """`predict` del bundle congelado sobre ventanas degradadas + veredicto."""
    from ds02_rul.persistence import load_ensemble

    ensemble = load_ensemble(os.path.join(_ROOT, "models", "ensemble.joblib"))

    w = ventanas_bajo_dropout()
    units = w["meta"]["unit"].values
    cycles = w["meta"]["cycle"].values
    p = ensemble.predict(w["X_raw"], cycles, units)
    assert np.all(np.isfinite(p))

    m = evaluate_predictions(w["y"], p, "B-bajo-dropout")
    macro = macro_rmse(w["y"], p, units)
    comp = pd.DataFrame([
        {"Modelo": "B-bajo-dropout", "RMSE": m["RMSE"], "MAE": m["MAE"],
         "R2": m["R2"], "NASA_Score": m["NASA_Score"], "grano": "ventana"},
        {"Modelo": "C-media (42,7,123)", "RMSE": C_MEAN["rmse"],
         "MAE": None, "R2": None, "NASA_Score": C_MEAN["nasa"],
         "grano": "ventana"},
        {"Modelo": "B-limpio (congelado)", "RMSE": B_CLEAN["rmse"],
         "MAE": 3.183, "R2": 0.9482, "NASA_Score": B_CLEAN["nasa"],
         "grano": "ventana"},
    ])
    comp.to_csv(
        os.path.join(_ROOT, "resultados", "comparativa_b_dropout.csv"),
        index=False,
    )

    rmse, nasa = float(m["RMSE"]), float(m["NASA_Score"])
    if rmse > C_MEAN["rmse"] + 0.05:
        veredicto = ("C GANA bajo dropout: re-freeze justificado, C a producción")
    elif abs(rmse - B_CLEAN["rmse"]) <= 0.05:
        veredicto = ("B INSENSIBLE al dropout (ffill repara): B sigue en producción")
    else:
        veredicto = ("tierra de nadie: B sigue (no se toca lo que funciona)")
    if verbose:
        print(comp.to_string(index=False))
        print(f"\nmacro-RMSE B-dropout: {macro['macro_rmse']:.3f}")
        print(f"B-dropout: RMSE {rmse:.3f} | NASA {nasa:.1f}")
        print("Veredicto:", veredicto)
    return {"rmse": rmse, "nasa": nasa, "macro": macro, "veredicto": veredicto}


if __name__ == "__main__":
    evaluar()
