"""Banda dual conforme: la interna del artefacto (17 450 filas) y la de
decision R6 (14 915 filas OOF puras) comparten codigo, no numeros.

RED -> GREEN sobre `src/ds02_rul/conformal.py` con datos sinteticos
(semilla fija, sin entrenos): bins, cobertura 0.90, fallback global y los
bordes que nunca cruzan el punto ni bajan de cero.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from ds02_rul.conformal import (  # noqa: E402
    apply_conformal,
    empirical_coverage,
    fit_conformal,
)


def _sintetico(n=4000, seed=42):
    """Prediccion y verdad con residuo acotado por tramo de RUL."""
    rng = np.random.default_rng(seed)
    pred = rng.uniform(0, 120, n)
    residuo = rng.uniform(-10, 10, n) + np.where(pred > 75, -5.0, 0.0)
    return pred + residuo, pred


def test_banda_dual_suma_bins_y_apunta_0_90():
    """Cuatro bins, `n` suma la calibracion y el objetivo es 0.90."""
    y, p = _sintetico(2000)
    cal = fit_conformal(y, p, target=0.90)
    assert len(cal["bins"]) == 4
    assert cal["target_coverage"] == 0.90
    assert cal["alpha_each_side"] == 0.05
    assert sum(b["n"] for b in cal["bins"]) == cal["n_calibration"] == 2000
    assert cal["bins"][-1]["pred_range"][1] is None  # `inf` -> null JSON


def test_banda_dual_lower_nunca_negativo_ni_cruza_el_punto():
    """`lower >= 0` para punto no negativo y `lower <= punto <= upper`."""
    y, p = _sintetico(4000)
    cal = fit_conformal(y, p, target=0.90)
    puntos = np.array([-50.0, 0.0, 10.0, 30.0, 60.0, 90.0, 200.0])
    lower, upper = apply_conformal(puntos, cal)
    assert np.all(lower[puntos >= 0] >= 0.0)
    assert np.all(lower <= puntos) and np.all(puntos <= upper)


def test_cobertura_empirica_cerca_de_0_90_en_sintetico():
    """En residuo uniforme simetrico la cobertura medida ronda el 0.90."""
    y, p = _sintetico(6000, seed=7)
    cal = fit_conformal(y, p, target=0.90, min_rows=50)
    lower, upper = apply_conformal(p, cal)
    cobertura = empirical_coverage(y, lower, upper)
    assert 0.86 <= cobertura <= 0.94, cobertura


def test_bin_escaso_cae_al_fallback_global():
    """Con `min_rows` imposible todos los bins heredan los cuantiles globales."""
    y, p = _sintetico(800)
    cal = fit_conformal(y, p, target=0.90, min_rows=10**9)
    assert all(b["source"] == "global" for b in cal["bins"])
    for b in cal["bins"]:
        assert [b["q_low"], b["q_high"]] == cal["global_quantiles"]


def test_bin_con_filas_suficientes_usa_su_propio_cuantil():
    """Un bin poblado con residuo propio no copia el global."""
    y, p = _sintetico(800)
    cal = fit_conformal(y, p, target=0.90, min_rows=10)
    assert any(b["source"] == "bin" for b in cal["bins"])
    bin0 = cal["bins"][0]
    assert bin0["n"] >= 10 and bin0["source"] == "bin"


def test_banda_dual_17450_interna_vs_14915_decision():
    """La banda interna (17 450, con 16) y la R6 (14 915, sin 16) no se mezclan."""
    with open(os.path.join(ROOT, "models", "ds02_manifest.json"),
              encoding="utf-8") as fh:
        manifiesto = json.load(fh)
    with open(os.path.join(ROOT, "src", "mia", "calibracion_banda.json"),
              encoding="utf-8") as fh:
        decision = json.load(fh)
    assert manifiesto["conformal"]["n_calibration"] == 17450
    assert manifiesto["conformal_decision"]["n_calibration"] == 14915
    assert decision["n_calibration"] == 14915
    assert decision["target_coverage"] == 0.90
    assert sum(b["n"] for b in decision["bins"]) == 14915
    assert 16 not in decision["procedencia"]["unidades_calibracion"]
