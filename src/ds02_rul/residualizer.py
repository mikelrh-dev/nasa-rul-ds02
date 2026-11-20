"""Residualización de cada sensor contra el régimen de vuelo.

Un sensor medido suma (a) la degradación propia de la unidad, que correlaciona
con la RUL, y (b) el punto de operación (altitud, Mach, empuje, temperatura
total), que no. Restar a cada sensor un ajuste de cresta de grado 2 del régimen
deja la señal de degradación y evita que un modelo de árboles corte por una
maniobra del piloto.
"""
from __future__ import annotations

import numpy as np


class SensorResidualizer:
    """Resta la parte de cada sensor explicada por el régimen y estandariza.

    Atributos
    ---------
    poly : sklearn.preprocessing.PolynomialFeatures
        Grado 2, `include_bias=False`, ajustado sobre `W` estandarizado.
    ridges : list de sklearn.linear_model.Ridge
        Una por sensor (14), ajustadas sobre los términos polinómicos del régimen.
    res_scaler : sklearn.preprocessing.StandardScaler
        Ajustado sobre la matriz de residuos.
    """

    def __init__(self, poly, ridges, res_scaler):
        self.poly = poly
        self.ridges = ridges
        self.res_scaler = res_scaler

    def transform(self, W_scaled: np.ndarray, Xs_raw: np.ndarray) -> np.ndarray:
        """Devuelve residuos estandarizados de `Xs_raw` dado `W` estandarizado."""
        P = self.poly.transform(W_scaled)
        out = np.zeros_like(Xs_raw, dtype=np.float64)
        for j, ridge in enumerate(self.ridges):
            out[:, j] = Xs_raw[:, j] - ridge.predict(P)
        return self.res_scaler.transform(out)
