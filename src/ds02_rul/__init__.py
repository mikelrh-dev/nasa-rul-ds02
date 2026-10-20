"""DS02 RUL prediction: importable pipeline objects.

Everything that must be pickled with a module-qualified name lives here, so an
artifact can be loaded by any process — not only by the notebook that trained it.

Public API
----------
SensorResidualizer      per-sensor residualisation against the flight regime
HybridStackingEnsemble  BiLSTM + LightGBM + meta-learner + causal EMA
LastStepPooling         serializable replacement for the bare Lambda
causal_ema_by_unit      causal per-unit exponential moving average
calculate_nasa_score    asymmetric exponential penalty, summed
evaluate_predictions    RMSE / MAE / R2 / NASA
"""

from .ensemble import PARADIGM, HybridStackingEnsemble
from .metrics import calculate_nasa_score, evaluate_predictions
from .pooling import LastStepPooling
from .residualizer import SensorResidualizer
from .smoothing import causal_ema_by_unit

__all__ = [
    "PARADIGM",
    "HybridStackingEnsemble",
    "LastStepPooling",
    "SensorResidualizer",
    "calculate_nasa_score",
    "causal_ema_by_unit",
    "evaluate_predictions",
]

__version__ = "4.1.0"
