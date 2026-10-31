# src/ds02_rul/__init__.py — copia literal para NotebookLM

> Copia literal de `src/ds02_rul/__init__.py`. No resumido, no adaptado. Para pegar en NotebookLM.

```python
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
macro_rmse              per-engine RMSEs and their unweighted mean
fit_conformal           per-bin asymmetric prediction band (split conformal)
apply_conformal         (lower, upper) from a calibrated band
empirical_coverage      realised coverage of a band
"""

from .conformal import apply_conformal, empirical_coverage, fit_conformal
from .ensemble import PARADIGM, HybridStackingEnsemble
from .metrics import calculate_nasa_score, evaluate_predictions, macro_rmse
from .pooling import LastStepPooling
from .residualizer import SensorResidualizer
from .smoothing import causal_ema_by_unit

__all__ = [
    "PARADIGM",
    "HybridStackingEnsemble",
    "LastStepPooling",
    "SensorResidualizer",
    "apply_conformal",
    "calculate_nasa_score",
    "causal_ema_by_unit",
    "empirical_coverage",
    "evaluate_predictions",
    "fit_conformal",
    "macro_rmse",
]

__version__ = "4.1.0"

```
