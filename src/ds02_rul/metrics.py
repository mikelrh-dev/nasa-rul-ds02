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


def macro_rmse(y_true, y_pred, units) -> dict:
    """Mean of the per-engine RMSEs, each engine weighing 1/n regardless of size.

    The window-weighted RMSE is dominated by the engine with the most windows.
    Reporting both is the point: on bundle B the weighted figure (4.2515) is
    kinder than the macro one (4.8433) because the worst engine is also the
    smallest.
    """
    y_true = np.asarray(y_true, dtype=np.float64).ravel()
    y_pred = np.asarray(y_pred, dtype=np.float64).ravel()
    units = np.asarray(units).ravel()
    per_unit = {}
    for unit in np.unique(units):
        mask = units == unit
        per_unit[float(unit)] = round(
            float(np.sqrt(np.mean((y_true[mask] - y_pred[mask]) ** 2))), 4
        )
    values = list(per_unit.values())
    return {
        "per_unit_rmse": per_unit,
        "macro_rmse": round(float(np.mean(values)), 4) if values else None,
        "n_units": len(values),
    }


def evaluate_predictions(y_true, y_pred, model_name: str = "Modelo") -> dict:
    """Return RMSE / MAE / R2 / NASA as a flat dict, rounded for display."""
    return {
        "Modelo": model_name,
        "RMSE": round(float(np.sqrt(mean_squared_error(y_true, y_pred))), 3),
        "MAE": round(float(mean_absolute_error(y_true, y_pred)), 3),
        "R2": round(float(r2_score(y_true, y_pred)), 4),
        "NASA_Score": round(calculate_nasa_score(y_true, y_pred), 1),
    }
