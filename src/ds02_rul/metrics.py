"""Metrics for RUL evaluation.

`calculate_nasa_score` is a SUM over rows, not a mean: its magnitude scales with
the number of scored windows and is only comparable between models evaluated on
the same rows. The DS02 path applies no 125-cycle clamp (that clamp exists only
in the legacy C-MAPSS pipeline).
"""
from __future__ import annotations

import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


def calculate_nasa_score(y_true, y_pred) -> float:
    """Asymmetric exponential penalty, summed over rows (Saxena et al., PHM 2008)."""
    d = np.asarray(y_pred).ravel() - np.asarray(y_true).ravel()
    score = np.where(d < 0.0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)
    return float(np.sum(score))


def regression_metrics(y_true, y_pred) -> dict:
    """RMSE / MAE / R2 / NASA sin redondear, para agregar entre semillas."""
    return {
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "R2": float(r2_score(y_true, y_pred)),
        "NASA_Score": calculate_nasa_score(y_true, y_pred),
    }


def macro_rmse(y_true, y_pred, units) -> dict:
    """Mean of the per-engine RMSEs, each engine weighing 1/n regardless of size.

    The window-weighted RMSE is dominated by the engine with the most windows.
    Reporting both is the point: on the deployed bundle the weighted figure
    (4.3382) is kinder than the macro one (5.0153) because the worst engine is
    also the smallest.
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
    raw = regression_metrics(y_true, y_pred)
    return {
        "Modelo": model_name,
        "RMSE": round(raw["RMSE"], 3),
        "MAE": round(raw["MAE"], 3),
        "R2": round(raw["R2"], 4),
        "NASA_Score": round(raw["NASA_Score"], 1),
    }


def aggregate_seed_metrics(
    rows: list[dict], metrics=("RMSE", "MAE", "R2", "NASA_Score")
) -> dict:
    """Media ± desviación muestral de las métricas entre semillas.

    `rows` son dicts con `seed` y las claves de `metrics`. Es la única
    agregación multisemilla: `scripts/operativo/evaluate_bundle_stability.py` la reutiliza.
    """
    if not rows:
        raise ValueError("se necesita al menos una fila para agregar")
    out = {
        "n_semillas": len(rows),
        "seeds": [int(row["seed"]) for row in rows],
    }
    for key in metrics:
        values = np.asarray([row[key] for row in rows], dtype=float)
        ddof = 1 if len(rows) > 1 else 0
        prefix = {"RMSE": "rmse", "MAE": "mae", "R2": "r2", "NASA_Score": "nasa"}.get(
            key, key.lower()
        )
        out[f"{prefix}_media"] = float(values.mean())
        out[f"{prefix}_std"] = float(values.std(ddof=ddof))
    return out
