"""Capa del modelo (SAA): carga el artefacto congelado y puntúa una ventana.

`predecir(caso)` deja en la ficha:

* `rul_punto`        — estimación puntual del ensamble híbrido.
* `limite_inferior`  — extremo inferior de la banda conformal enviada.
* `limite_superior`  — extremo superior de la banda conformal enviada.

No entrena nada: el bundle está congelado en `models/ensemble.joblib` y se carga
una sola vez. El caso debe traer `X_raw` (una ventana `(1, 50, 18)` en el orden
de `COLUMNAS`), `ciclo` y `unidad`.
"""
from __future__ import annotations

import os
import sys

import numpy as np

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTEFACTO = os.path.join(RAIZ, "models", "ensemble.joblib")
SRC = os.path.join(RAIZ, "src")

# Orden de canales del dataset DS02: 4 condiciones de operación + 14 sensores.
# Es el orden que `ds02_rul.inference.raw_windows` espera (`hstack([W, Xs])`).
# El dueño del esquema es `ds02_rul.data`: aquí solo se compone.
if SRC not in sys.path:
    sys.path.insert(0, SRC)
from ds02_rul.data import OP_COLS, SENSOR_COLS  # noqa: E402

COLUMNAS = list(OP_COLS) + list(SENSOR_COLS)

_ensemble = None


def _cargar():
    """Carga perezosa del bundle congelado (una sola vez por proceso)."""
    global _ensemble
    if _ensemble is None:
        if SRC not in sys.path:
            sys.path.insert(0, SRC)
        from ds02_rul.persistence import load_ensemble

        _ensemble = load_ensemble(ARTEFACTO)
    return _ensemble


def predecir(caso: dict) -> float:
    """Puntúa la ventana del caso y devuelve la estimación puntual."""
    X = np.asarray(caso["X_raw"], dtype=np.float64)
    if X.ndim == 2:
        X = X.reshape(1, X.shape[0], X.shape[1])
    if X.ndim != 3 or X.shape[1:] != (50, len(COLUMNAS)):
        raise ValueError(
            f"la ventana debe ser (n, 50, {len(COLUMNAS)}), llegó {X.shape}"
        )

    ens = _cargar()
    cycles = np.asarray([float(caso["ciclo"])], dtype=np.float64)
    units = np.asarray([float(caso["unidad"])], dtype=np.float64)
    point, lower, upper = ens.predict_interval(X, cycles, units)

    caso["rul_punto"] = float(point[0])
    caso["limite_inferior"] = float(lower[0])
    caso["limite_superior"] = float(upper[0])
    return caso["rul_punto"]
