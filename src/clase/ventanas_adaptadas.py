"""Fase 5 (NB04): la base adaptada entra por arriba del pipeline honesto.

Lee `train_con_nulos` / `test_con_nulos` (MAR T30 ya inyectado), re-imputa con
medianas SOLO de fit-units `[2,5,10,18,20]` (no las de dev-completo del track
de clase) y ventanea con `fit_preprocessing`/`build_windows` sin cambios:
contrato 93 intacto, sin `fase_vuelo`; holdout 16 reservado para beta y test
`[11,14,15]` intacto. B vs C comparten particiones, grano y métricas.
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
from ds02_rul.features import build_windows, fit_preprocessing  # noqa: E402

FIT_UNITS = [2.0, 5.0, 10.0, 18.0, 20.0]
HOLDOUT_UNITS = [16.0]
TEST_UNITS = [11.0, 14.0, 15.0]


def _imputar_con_medianas(df: pd.DataFrame, medianas: pd.Series) -> pd.DataFrame:
    orden = df.sort_values(["unit", "cycle"]).reset_index(drop=True)
    out = orden.copy()
    out[SENSOR_COLS] = out.groupby("unit", sort=False)[SENSOR_COLS].ffill()
    out[SENSOR_COLS] = out[SENSOR_COLS].fillna(medianas)
    return out


def ventanas_adaptadas(window: int = 50, step_train: int = 3,
                       step_test: int = 2) -> dict:
    """Ventanas honestas sobre la base adaptada (MAR + ffill fit-units)."""
    train_con = pd.read_parquet(os.path.join(_ROOT, "data", "processed", "train_con_nulos.parquet"))
    test_con = pd.read_parquet(os.path.join(_ROOT, "data", "processed", "test_con_nulos.parquet"))

    fit_mask = train_con["unit"].isin(FIT_UNITS)
    medianas_fit = train_con.loc[fit_mask, SENSOR_COLS].median(numeric_only=True)

    train_imp = _imputar_con_medianas(train_con, medianas_fit)
    test_imp = _imputar_con_medianas(test_con, medianas_fit)
    assert int(train_imp[SENSOR_COLS].isna().sum().sum()) == 0
    assert int(test_imp[SENSOR_COLS].isna().sum().sum()) == 0

    W_fit = train_imp.loc[fit_mask, OP_COLS].to_numpy(dtype=np.float64)
    Xs_fit = train_imp.loc[fit_mask, SENSOR_COLS].to_numpy(dtype=np.float64)
    prep = fit_preprocessing(W_fit, Xs_fit)

    dev = build_windows(
        train_imp[OP_COLS].to_numpy(dtype=np.float64),
        train_imp[SENSOR_COLS].to_numpy(dtype=np.float64),
        train_imp["RUL"].to_numpy(dtype=float),
        train_imp["unit"].to_numpy(dtype=float),
        train_imp["cycle"].to_numpy(dtype=float),
        prep, window_size=window, step=step_train,
    )
    test = build_windows(
        test_imp[OP_COLS].to_numpy(dtype=np.float64),
        test_imp[SENSOR_COLS].to_numpy(dtype=np.float64),
        test_imp["RUL"].to_numpy(dtype=float),
        test_imp["unit"].to_numpy(dtype=float),
        test_imp["cycle"].to_numpy(dtype=float),
        prep, window_size=window, step=step_test,
    )
    return {
        "prep": prep,
        "medianas_fit": medianas_fit,
        "dev": dev,
        "test": test,
        "n_fit_rows": int(fit_mask.sum()),
        "dev_units_raw": train_imp["unit"].to_numpy(dtype=float),
        "columnas_tab": [f"f{i}" for i in range(dev["X_tab"].shape[1])],
    }
