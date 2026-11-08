"""SHAP-C sin ejecutar SHAP pesado: solo las funciones puras del modulo.

Nombres de features (19/93/meta), `split_fold0`, aditividad, `build_meta_Z`
y `grouped_perm_phis` con un predictor lineal sintetico. Sin TF, sin bundle,
sin `ejecutar_shap_c`.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from ds02_rul.shap_c import (  # noqa: E402
    bilstm_feature_names,
    build_meta_Z,
    grouped_perm_phis,
    lgb_feature_names,
    meta_feature_names,
    split_fold0,
    validar_aditividad,
)

OP = ["alt", "Mach", "TRA", "T2"]
SENSORES = [f"s{i}" for i in range(14)]


def test_bilstm_feature_names_son_19_con_cyc_norm_al_final():
    """19 canales en orden del scaler: 4 op + 14 sensores + `cyc_norm`."""
    nombres = bilstm_feature_names(op_cols=OP, sensor_cols=SENSORES)
    assert len(nombres) == 19
    assert nombres[:4] == OP
    assert nombres[4:18] == SENSORES
    assert nombres[-1] == "cyc_norm"


def test_lgb_feature_names_son_93_en_bloques():
    """93 = 1 + 4*2 + 14*6: `cyc_norm` primero y bloques en orden D3."""
    nombres = lgb_feature_names(op_cols=OP, sensor_cols=SENSORES)
    assert len(nombres) == 93
    assert nombres[0] == "cyc_norm"
    assert nombres[1:5] == [f"{c}_mean" for c in OP]
    assert nombres[5:9] == [f"{c}_last" for c in OP]
    assert nombres[-1] == "s13_pres"


def test_meta_feature_names_segun_ancho_real():
    """Ancho 2 -> [p_lstm, p_lgb]; 3 -> + ciclos; otro ancho, ValueError."""
    assert meta_feature_names(2) == ["p_lstm", "p_lgb"]
    assert meta_feature_names(3) == ["p_lstm", "p_lgb", "cycles/100"]
    with pytest.raises(ValueError, match="ancho meta"):
        meta_feature_names(4)


def test_split_fold0_separa_por_motor_sin_solape():
    """Train y val del fold 0 no comparten filas ni motores y cubren todo."""
    units = np.repeat([2, 5, 10, 16, 18, 20], 10)
    tr, va = split_fold0(units, n_splits=3, fold=0)
    assert len(tr) + len(va) == len(units)
    assert not set(units[tr]) & set(units[va])       # motores disjuntos
    assert set(units[tr]) | set(units[va]) == set(units)


def test_validar_aditividad_acepta_descomposicion_exacta_y_rechaza_rota():
    """`base + suma(valores) == pred` pasa con error ~0; si no, AssertionError."""
    base = np.array([10.0, 20.0])
    valores = np.array([[1.0, 2.0], [-1.0, 4.0]])
    pred = base + valores.sum(axis=1)
    assert validar_aditividad(base, valores, pred) < 1e-9
    with pytest.raises(AssertionError, match="aditividad rota"):
        validar_aditividad(base, valores, pred + 5.0)


def test_build_meta_Z_respeta_el_ancho_real():
    """2 columnas con [p_lstm, p_lgb]; 3 anade ciclos/100; mismatch, ValueError."""
    p_lstm = np.array([10.0, 20.0])
    p_lgb = np.array([12.0, 22.0])
    ciclos = np.array([100.0, 200.0])
    Z2 = build_meta_Z(p_lstm, p_lgb, ciclos, 2)
    assert Z2.shape == (2, 2)
    np.testing.assert_allclose(Z2, [[10.0, 12.0], [20.0, 22.0]])
    Z3 = build_meta_Z(p_lstm, p_lgb, ciclos, 3)
    assert Z3.shape == (2, 3)
    np.testing.assert_allclose(Z3[:, 2], [1.0, 2.0])
    with pytest.raises(ValueError, match="meta espera"):
        build_meta_Z(p_lstm, p_lgb, ciclos, 5)


def test_grouped_perm_phis_telescopa_exacto_con_predictor_lineal():
    """Con modelo lineal, forward+reverse reparten exacto: base+suma == pred."""
    rng = np.random.default_rng(0)
    X = rng.normal(size=(4, 5, 3))                    # 4 filas, ventana 5, 3 canales
    ref = np.zeros((1, 5, 3))
    pesos = np.array([2.0, -1.0, 0.5])

    def batch_pred(A):
        return (A.mean(axis=1) * pesos).sum(axis=1)

    phis = grouped_perm_phis(batch_pred, X, ref, seed=42)
    assert phis.shape == (4, 3)
    base = float(batch_pred(ref)[0])
    pred = batch_pred(X)
    err = validar_aditividad(np.full(4, base), phis, pred)
    assert err < 1e-9
