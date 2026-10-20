"""Per-sensor residualisation against the flight regime.

A measured sensor is the sum of (a) unit-specific degradation, which correlates
with RUL, and (b) the operating point (altitude, Mach, throttle, total
temperature), which does not. Subtracting a degree-2 ridge fit of the regime
from each sensor leaves the degradation signal and stops a tree model from
splitting on pilot manoeuvre.
"""
from __future__ import annotations

import numpy as np


class SensorResidualizer:
    """Subtract the regime-explained part of each sensor, then standardise.

    Attributes
    ----------
    poly : sklearn.preprocessing.PolynomialFeatures
        Degree-2, `include_bias=False`, fitted on standardised `W`.
    ridges : list of sklearn.linear_model.Ridge
        One per sensor (14), each fitted on the polynomial regime terms.
    res_scaler : sklearn.preprocessing.StandardScaler
        Fitted on the residual matrix.
    """

    def __init__(self, poly, ridges, res_scaler):
        self.poly = poly
        self.ridges = ridges
        self.res_scaler = res_scaler

    def transform(self, W_scaled: np.ndarray, Xs_raw: np.ndarray) -> np.ndarray:
        """Return standardised residuals for `Xs_raw` given standardised `W`."""
        P = self.poly.transform(W_scaled)
        out = np.zeros_like(Xs_raw, dtype=np.float64)
        for j, ridge in enumerate(self.ridges):
            out[:, j] = Xs_raw[:, j] - ridge.predict(P)
        return self.res_scaler.transform(out)
