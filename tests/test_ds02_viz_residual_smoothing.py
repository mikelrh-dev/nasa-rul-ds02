"""Residualizacion por regimen y EMA causal por unidad.

Solo transformaciones puras con datos sinteticos: ninguna funcion entrena ni
toca artefactos. `span=5` es alpha 1/3 en pandas.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from ds02_rul.residualizer import SensorResidualizer  # noqa: E402
from ds02_rul.smoothing import causal_ema_by_unit  # noqa: E402


def test_residualizer_resta_el_regimen_y_estandariza():
    """Con sklearn real: residuo = sensor menos prediccion ridge del regimen."""
    from sklearn.linear_model import Ridge
    from sklearn.preprocessing import PolynomialFeatures, StandardScaler

    rng = np.random.default_rng(3)
    W = rng.uniform(0, 1, (60, 2))          # regimen estandarizado
    Xs = rng.uniform(0, 1, (60, 3))         # sensores crudos
    poly = PolynomialFeatures(degree=2, include_bias=False).fit(W)
    P = poly.transform(W)
    ridges = [Ridge(alpha=1.0).fit(P, Xs[:, j]) for j in range(3)]
    crudos = np.column_stack([Xs[:, j] - ridges[j].predict(P) for j in range(3)])
    scaler = StandardScaler().fit(crudos)

    res = SensorResidualizer(poly, ridges, scaler)
    out = res.transform(W, Xs)
    np.testing.assert_allclose(out, scaler.transform(crudos))
    assert out.shape == (60, 3)


def test_smoothing_causal_alpha_un_tercio_con_span_5():
    """`span=5` -> alpha 1/3: el primer valor se queda y el segundo mezcla."""
    pred = np.array([30.0, 24.0, 18.0])
    out = causal_ema_by_unit(pred, [11, 11, 11], [1, 2, 3], span=5)
    assert out[0] == pytest.approx(30.0)
    assert out[1] == pytest.approx((1 / 3) * 24.0 + (2 / 3) * 30.0)
    assert out[2] == pytest.approx((1 / 3) * 18.0 + (2 / 3) * out[1])


def test_smoothing_causal_el_futuro_no_cambia_el_pasado():
    """Recortar la cola no altera los valores ya calculados (causal)."""
    pred = np.array([10.0, 20.0, 30.0, 40.0, 50.0])
    completo = causal_ema_by_unit(pred, [7] * 5, [1, 2, 3, 4, 5], span=5)
    prefijo = causal_ema_by_unit(pred[:3], [7] * 3, [1, 2, 3], span=5)
    np.testing.assert_allclose(prefijo, completo[:3])


def test_smoothing_aisla_unidades_y_respeta_el_orden_de_entrada():
    """Dos motores entrelazados no se sangran y el orden de salida es el de entrada."""
    pred = np.array([100.0, 10.0, 90.0, 20.0])       # unidades 11,14,11,14
    units = np.array([11, 14, 11, 14])
    cycles = np.array([2, 2, 1, 1])                    # ciclo 1 va segundo en entrada
    out = causal_ema_by_unit(pred, units, cycles, span=5)
    # Unidad 11 en orden de ciclo: 90 (c1) -> 100 (c2); 14: 20 (c1) -> 10 (c2).
    assert out[2] == pytest.approx(90.0) and out[3] == pytest.approx(20.0)
    assert out[0] == pytest.approx((1 / 3) * 100.0 + (2 / 3) * 90.0)
    assert out[1] == pytest.approx((1 / 3) * 10.0 + (2 / 3) * 20.0)
