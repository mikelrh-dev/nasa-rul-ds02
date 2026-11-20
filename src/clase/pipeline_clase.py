"""Pipeline sklearn compartido del track de clase.

Un solo `ColumnTransformer` para los 5 clásicos + MLP:
- numéricas (19): cycle, alt, Mach, TRA, T2 + 14 sensores → StandardScaler
- categórica (1): fase_vuelo → OneHot(handle_unknown=ignore)

`unit` NO es predictor (es el grupo de GroupKFold). El `Pipeline` completo
(pre + reg) se guarda en `models/mejor_modelo_clase.joblib` y predice 1 caso
nuevo con `predict_caso_nuevo`.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))

from ds02_rul.data import SENSOR_COLS  # noqa: E402

NUM_COLS = ["cycle", "alt", "Mach", "TRA", "T2"] + list(SENSOR_COLS)
CAT_COLS = ["fase_vuelo"]
FEATURE_COLS = list(NUM_COLS) + list(CAT_COLS)


def make_pre() -> ColumnTransformer:
    """Unico preprocesado compartido (fit SOLO en train)."""
    return ColumnTransformer(
        [
            ("num", StandardScaler(), list(NUM_COLS)),
            ("cat", OneHotEncoder(handle_unknown="ignore", sparse_output=False), list(CAT_COLS)),
        ],
        verbose_feature_names_out=False,
    )


def make_pipeline(reg) -> Pipeline:
    """Pipeline completo pre + regresor (lo que se guarda en joblib)."""
    return Pipeline([("pre", make_pre()), ("reg", reg)])


def predict_caso_nuevo(pipe: Pipeline, caso: dict) -> float:
    """Puntúa 1 caso nuevo dict (19 numéricas + fase_vuelo). Devuelve RUL."""
    fila = pd.DataFrame([{c: caso[c] for c in FEATURE_COLS}])
    pred = pipe.predict(fila)
    return round(float(np.ravel(pred)[0]), 2)
