"""Metrics for RUL evaluation.

`calculate_nasa_score` is a SUM over rows, not a mean: its magnitude scales with
the number of scored windows and is only comparable between models evaluated on
the same rows. The DS02 path applies no 125-cycle clamp (that clamp exists only
in the C-MAPSS FD001 loader).
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def calculate_nasa_score(y_true, y_pred) -> float:
    """Asymmetric exponential penalty, summed over rows (Saxena et al., PHM 2008)."""
    d = np.asarray(y_pred).ravel() - np.asarray(y_true).ravel()
    score = np.where(d < 0.0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)
    return float(np.sum(score))


def evaluate_predictions(y_true, y_pred, model_name: str = "Modelo") -> dict:
    """Return RMSE / MAE / R2 / NASA as a flat dict, rounded for display."""
    return {
        "Modelo": model_name,
        "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 3),
        "MAE": round(float(mean_absolute_error(y_true, y_pred)), 3),
        "R2": round(float(r2_score(y_true, y_pred)), 4),
        "NASA_Score": round(calculate_nasa_score(y_true, y_pred), 1),
    }
