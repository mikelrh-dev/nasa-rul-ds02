"""Utilidades del track de clase (fachada con los nombres que pide la rúbrica).

La rúbrica del reto exige `src/utils.py` con las funciones del proyecto.
La lógica vive en `src/clase/pipeline_clase.py` (pipeline de clase) y en
`src/ds02_rul/metrics.py` (métricas de producción); este módulo solo las
re-exporta con nombres estables y documentadas, para que los notebooks las
usen sin repetir código (PIA-2):

- `make_pipeline(reg)` — pipeline sklearn completo (pre + regresor).
- `make_pre()` — preprocesado compartido (StandardScaler + OneHot).
- `FEATURE_COLS` — columnas de entrada del modelo de clase.
- `predict_caso_nuevo(pipe, caso)` — puntúa 1 caso nuevo dict, devuelve RUL.
- `evaluate_predictions(y_true, y_pred, model_name)` — RMSE/MAE/R²/NASA.
"""

from __future__ import annotations

from ds02_rul.metrics import evaluate_predictions
from src.clase.pipeline_clase import (
    CAT_COLS,
    FEATURE_COLS,
    NUM_COLS,
    make_pipeline,
    make_pre,
    predict_caso_nuevo,
)

__all__ = [
    "FEATURE_COLS",
    "NUM_COLS",
    "CAT_COLS",
    "make_pipeline",
    "make_pre",
    "predict_caso_nuevo",
    "evaluate_predictions",
]
