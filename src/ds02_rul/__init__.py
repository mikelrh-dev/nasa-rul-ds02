"""Predicción de RUL DS02: objetos del pipeline importables.

Aquí vive todo lo que debe serializarse con un nombre cualificado por módulo,
para que un artefacto se pueda cargar desde cualquier proceso y no solo desde el
notebook que lo entrenó.

API pública
-----------
SensorResidualizer      residualización por sensor contra el régimen de vuelo
HybridStackingEnsemble  BiLSTM + LightGBM + meta-aprendiz + EMA causal
LastStepPooling         sustituto serializable del Lambda suelto
causal_ema_by_unit      media móvil exponencial causal por unidad
calculate_nasa_score    penalización exponencial asimétrica, sumada
evaluate_predictions    RMSE / MAE / R2 / NASA
macro_rmse              RMSE por motor y su media sin ponderar
fit_conformal           banda asimétrica por tramo (split conformal)
apply_conformal         (inferior, superior) de una banda calibrada
empirical_coverage      cobertura observada de una banda
"""

from .conformal import apply_conformal, empirical_coverage, fit_conformal
from .ensemble import PARADIGM, HybridStackingEnsemble
from .metrics import (
    aggregate_seed_metrics,
    calculate_nasa_score,
    evaluate_predictions,
    macro_rmse,
    regression_metrics,
)
from .pooling import LastStepPooling
from .residualizer import SensorResidualizer
from .smoothing import causal_ema_by_unit

__all__ = [
    "PARADIGM",
    "HybridStackingEnsemble",
    "LastStepPooling",
    "SensorResidualizer",
    "aggregate_seed_metrics",
    "apply_conformal",
    "calculate_nasa_score",
    "causal_ema_by_unit",
    "empirical_coverage",
    "evaluate_predictions",
    "regression_metrics",
    "fit_conformal",
    "macro_rmse",
]

__version__ = "4.1.0"
