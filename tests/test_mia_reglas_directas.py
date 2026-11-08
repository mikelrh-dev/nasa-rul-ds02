"""Reglas MIA directas: condiciones y efectos de R2b/R6/R7/R8/R9/R1/R10/R11.

Sin duplicar `test_mia_rules.py` (forma del motor, casos, calibracion
congelada): aqui van los bordes exactos de cada `si_*`/`efecto_*` y quien
gana cuando varias se cumplen a la vez.
"""
from __future__ import annotations

import os
import sys

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src", "mia"))

from src.mia import reglas as R  # noqa: E402
from src.mia.motor import motor  # noqa: E402

UMB = {"apto": 30.0, "hangar": 25.0}


def _ficha(**kw):
    caso = {"limite_inferior": 27.0, "umbrales": dict(UMB), "alertas_datos": []}
    caso.update(kw)
    return caso


def test_R2b_exige_historial_y_punto():
    """Sin historial no hay nada que corregir; con ambos, si."""
    assert R.si_R2b_ISOTONICO({"rul_punto": 40.0}) is False
    assert R.si_R2b_ISOTONICO({"historial": [(1.0, 50.0)]}) is False
    assert R.si_R2b_ISOTONICO({"historial": [(1.0, 50.0)], "rul_punto": 40.0}) is True


def test_R2b_sustituye_el_punto_por_el_extremo_pava():
    """El efecto es el ultimo valor del PAVA causal del historial mas el punto."""
    caso = {"historial": [(1.0, 50.0), (2.0, 45.0)], "rul_punto": 60.0}
    esperado = float(R.pava_causal_no_creciente([50.0, 45.0, 60.0])[-1])
    efecto = R.efecto_R2b_ISOTONICO(caso)
    assert efecto == {"rul_punto": esperado, "corregido_por_isotonico": True}


def test_R6_exige_un_punto_al_que_trasladar_la_banda():
    """Sin `rul_punto` la banda no se recalibra."""
    assert R.si_R6_BANDA({}) is False
    assert R.si_R6_BANDA({"rul_punto": 33.0}) is True


def test_R6_banda_contiene_al_punto_y_no_baja_de_cero():
    """La banda recalibrada envuelve al punto corregido (calibracion real)."""
    efecto = R.efecto_R6_BANDA({"rul_punto": 40.0})
    assert efecto["banda_recalibrada"] is True
    assert efecto["limite_inferior"] <= 40.0 <= efecto["limite_superior"]
    assert efecto["limite_inferior"] >= 0.0


def test_R7_apto_en_el_borde_exactamente_en_el_umbral():
    """`L_inf >= apto`: en el borde (30) es APTO, por debajo no."""
    assert R.si_R7_APTO(_ficha(limite_inferior=30.0)) is True
    assert R.si_R7_APTO(_ficha(limite_inferior=29.9)) is False
    assert R.si_R7_APTO(_ficha(limite_inferior=45.0)) is True


def test_R8_inspeccion_en_los_bordes_hangar_y_apto():
    """`hangar <= L_inf < apto`: el borde hangar entra, el borde apto no."""
    assert R.si_R8_INSPECCION(_ficha(limite_inferior=25.0)) is True
    assert R.si_R8_INSPECCION(_ficha(limite_inferior=30.0)) is False
    assert R.si_R8_INSPECCION(_ficha(limite_inferior=24.9)) is False


def test_R9_hangar_por_debajo_del_borde():
    """`L_inf < hangar` es HANGAR; en el borde (25) ya es inspeccion."""
    assert R.si_R9_HANGAR(_ficha(limite_inferior=24.9)) is True
    assert R.si_R9_HANGAR(_ficha(limite_inferior=25.0)) is False
    assert R.si_R9_HANGAR(_ficha(limite_inferior=10.0)) is True


def test_R1_seguridad_gana_a_hangar_en_el_motor():
    """Dato imposible + riesgo alto: no se decide, y la traza dice R1 (prio 10)."""
    caso = _ficha(limite_inferior=5.0, alertas_datos=["canal fuera de rango"])
    assert R.si_R1_SEGURIDAD(caso) is True
    r = motor(caso, R.REGLAS_CORRECCION, R.REGLAS_DECISION)
    assert r["decision"] == R.SIN_DECISION
    assert "R1_SEGURIDAD" in r["usadas"]
    assert "dato imposible" in caso["motivo"]


def test_R10_datos_insuficientes_cierran_en_sin_decision():
    """Ficha sana pero incompleta (sin limite): R10 lo dice, no el silencio."""
    caso = {"umbrales": dict(UMB), "alertas_datos": []}
    assert R.si_R10_DATOS_INSUFICIENTES(caso) is True
    assert R.si_R10_DATOS_INSUFICIENTES(_ficha()) is False
    r = motor(caso, R.REGLAS_CORRECCION, R.REGLAS_DECISION)
    assert r["decision"] == R.SIN_DECISION
    assert "R10_DATOS_INSUFICIENTES" in r["usadas"]


def test_R11_umbrales_incoherentes_no_clasifican_ni_en_el_borde_igual():
    """`hangar >= apto` (incluido el empate) es error de configuracion."""
    invertidos = _ficha(umbrales={"apto": 20.0, "hangar": 30.0})
    empatados = _ficha(umbrales={"apto": 25.0, "hangar": 25.0})
    assert R.si_R11_UMBRALES_INCOHERENTES(invertidos) is True
    assert R.si_R11_UMBRALES_INCOHERENTES(empatados) is True
    assert R.si_R11_UMBRALES_INCOHERENTES(_ficha()) is False
    r = motor(dict(invertidos), R.REGLAS_CORRECCION, R.REGLAS_DECISION)
    assert r["decision"] == R.SIN_DECISION
    assert "R11_UMBRALES_INCOHERENTES" in r["usadas"]
