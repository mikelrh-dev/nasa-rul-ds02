"""Media móvil exponencial causal por unidad.

El desgaste crece con el ciclo, pero una predicción ventana a ventana no. La EMA
quita ese ruido de discontinuidad sin mirar hacia delante: `adjust=False` hace
que la recursión dependa solo de la muestra actual y las pasadas, y agrupar por
unidad evita que dos motores se contaminen entre sí.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def causal_ema_by_unit(pred, units, cycles, span: int = 5) -> np.ndarray:
    """Suaviza `pred` dentro de cada unidad, con las filas ordenadas por ciclo.

    Parámetros
    ----------
    pred : array-like de forma (n,)
    units : array-like de forma (n,)
    cycles : array-like de forma (n,)
    span : int
        Span de `ewm` de pandas. `span=5` equivale a alpha = 2 / (5 + 1).

    Devuelve
    --------
    np.ndarray de forma (n,), con el mismo orden que la entrada.
    """
    pred = np.asarray(pred, dtype=np.float64)
    units = np.asarray(units)
    cycles = np.asarray(cycles)
    out = np.zeros_like(pred)
    for unit in np.unique(units):
        idx = np.where(units == unit)[0]
        idx = idx[np.argsort(cycles[idx], kind="stable")]
        out[idx] = pd.Series(pred[idx]).ewm(span=span, adjust=False).mean().values
    return out
