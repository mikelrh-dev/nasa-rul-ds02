"""Tests del paquete `mia/`: motor de reglas, corrección y decisión.

Se comprueban cuatro cosas:

1. la forma del motor (tuplas de cinco y retorno `decision`/`usadas`/`porque`);
2. que los casos de `mia/casos.py` salen todos en BIEN;
3. que la corrección es causal, isotónica en el prefijo y no rompe el invariante de la banda;
4. que la calibración congelada es la que dice ser (14 915 filas, sin unidad 16).

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MIA = os.path.join(ROOT, "mia")
sys.path.insert(0, MIA)

import reglas as R  # noqa: E402
from casos import CASOS, ficha_invalida, hay_cache, probar_casos  # noqa: E402
from motor import motor  # noqa: E402

needs_cache = pytest.mark.skipif(not hay_cache(), reason="app/cache missing")
needs_oof = pytest.mark.skipif(
    not os.path.exists(os.path.join(ROOT, "_p1_oof_cache.npz")),
    reason="_p1_oof_cache.npz missing",
)


# --------------------------------------------------------------- forma
def test_cada_regla_es_una_tupla_de_cinco_datos():
    for lista in (R.REGLAS_CORRECCION, R.REGLAS_DECISION):
        for regla in lista:
            assert len(regla) == 5, regla
            nombre, condicion, efecto, prioridad, porque = regla
            assert isinstance(nombre, str) and nombre
            assert callable(condicion)
            assert isinstance(prioridad, int)
            assert porque and porque.strip()


def test_el_motor_devuelve_decision_usadas_y_porque():
    caso = ficha_invalida()
    r = motor(caso, R.REGLAS_CORRECCION, R.REGLAS_DECISION)
    assert set(r) == {"decision", "usadas", "porque"}
    assert r["decision"] == R.SIN_DECISION
    assert r["usadas"] and r["porque"]
    assert len(r["usadas"]) == len(r["porque"])


# --------------------------------------------------------------- casos
@needs_cache
def test_todos_los_casos_salen_BIEN():
    from modelo import predecir

    filas = probar_casos(R.REGLAS_CORRECCION, R.REGLAS_DECISION, predecir, motor)
    assert len(filas) == len(CASOS)
    fallos = [f for f in filas if f["bien"] != "BIEN"]
    assert not fallos, fallos


@needs_cache
def test_hay_casos_para_cada_estado_y_para_sin_decision():
    from modelo import predecir

    decisiones = {f["decision"] for f in probar_casos(
        R.REGLAS_CORRECCION, R.REGLAS_DECISION, predecir, motor)}
    assert decisiones == {R.APTO, R.INSPECCION, R.HANGAR, R.SIN_DECISION}


# ---------------------------------------------------------- corrección
def test_la_monotonia_es_causal():
    """El valor en t no depende de lo que venga despues."""
    con_mas = R.pava_causal_no_creciente([1.0, 2.0, 5.0, 3.0, 10.0])
    sin_mas = R.pava_causal_no_creciente([1.0, 2.0])
    np.testing.assert_allclose(con_mas[:2], sin_mas)
    np.testing.assert_allclose(sin_mas, [1.0, 1.5])


def test_la_envolvente_monotono_es_el_running_min():
    """La monotonia estricta de esta regla ES la regla R2, que se descarto.

    Identidad medida: `minimum.accumulate(pava_causal(y)) == minimum.accumulate(y)`.
    Por tanto, si se quisiera monotonía estricta, la regla sería R2 y no esta.
    """
    for serie in ([5, 3, 4, 1], [1, 2, 3, 0.5], [9, 1, 1, 1, 8], [2, 2, 1, 3, 0]):
        ajuste = R.pava_causal_no_creciente(serie)
        envolvente = np.minimum.accumulate(ajuste)
        np.testing.assert_allclose(envolvente, np.minimum.accumulate(serie))


def test_el_extremo_puede_subir_y_no_es_monotono_estricto():
    """Dicho sin rodeos: esta regla no garantiza una secuencia no creciente."""
    ajuste = R.pava_causal_no_creciente([1.0, 2.0, 3.0, 0.5])
    np.testing.assert_allclose(ajuste, [1.0, 1.5, 2.0, 0.5])
    assert np.max(np.diff(ajuste)) > 0.0


def test_la_banda_recalibrada_contiene_al_punto_y_no_baja_de_cero():
    cal = R.cargar_calibracion()
    for punto in (-5.0, 0.0, 12.5, 25.0, 49.9, 60.0, 88.0):
        lower, upper = R.banda_recalibrada(punto, cal)
        assert lower <= punto <= upper
        if punto >= 0.0:
            assert lower >= 0.0


def test_la_version_vectorizada_y_la_escalar_coinciden():
    cal = R.cargar_calibracion()
    puntos = np.array([0.0, 12.5, 25.0, 49.9, 60.0, 88.0])
    lower, upper = R.banda_recalibrada_vector(puntos, cal)
    for i, punto in enumerate(puntos):
        lo, up = R.banda_recalibrada(float(punto), cal)
        assert lower[i] == pytest.approx(lo)
        assert upper[i] == pytest.approx(up)


# ------------------------------------------------------------ seguridad
def test_la_seguridad_gana_a_los_umbrales():
    caso = ficha_invalida()
    # Sin la regla de seguridad, el punto valido llevaria a inspeccion.
    caso["alertas_datos"] = []
    assert motor(caso, R.REGLAS_CORRECCION, R.REGLAS_DECISION)["decision"] == R.INSPECCION
    # Con ella, no se decide.
    caso["alertas_datos"] = ["canal fuera de rango"]
    assert motor(caso, R.REGLAS_CORRECCION, R.REGLAS_DECISION)["decision"] == R.SIN_DECISION


def test_la_seguridad_no_depende_del_historial():
    caso = ficha_invalida()
    caso["historial"] = [(1.0, 50.0), (2.0, 40.0)]
    r = motor(caso, R.REGLAS_CORRECCION, R.REGLAS_DECISION)
    assert r["decision"] == R.SIN_DECISION
    assert "R1_SEGURIDAD" in r["usadas"]


# ------------------------------------------------------------ calibración
def test_la_calibracion_congelada_es_la_pura():
    with open(R.CALIBRACION_PATH, encoding="utf-8") as fh:
        cal = json.load(fh)
    procedencia = cal["procedencia"]
    assert procedencia["filas_calibracion"] == 14915
    assert procedencia["unidades_calibracion"] == [2, 5, 10, 18, 20]
    assert 16 not in procedencia["unidades_calibracion"]
    assert len(cal["bins"]) == 4
    assert cal["target_coverage"] == 0.9


@needs_oof
def test_la_correccion_mejora_el_nasa_en_el_oof_puro():
    """Regresión sobre la medicion: la correccion baja el NASA Score en OOF."""
    cache = np.load(os.path.join(ROOT, "_p1_oof_cache.npz"))
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from ds02_rul.metrics import calculate_nasa_score
    from ds02_rul.stacking import select_beta_grouped

    sel = select_beta_grouped(cache["units"], cache["cycles"], cache["y"],
                              cache["p_lstm"], cache["p_lgb"], span=5,
                              use_cycle_feature=False)
    calib = sel["oof_calib"]
    pure = np.isin(np.asarray(calib["units"], float), [2.0, 5.0, 10.0, 18.0, 20.0])
    puntos = np.asarray(calib["pred_ema"], float)[pure]
    unidades = np.asarray(calib["units"], float)[pure]
    ciclos = np.asarray(calib["cycles"], float)[pure]
    verdad = np.asarray(calib["y"], float)[pure]

    corregido = np.empty(len(puntos))
    for u in np.unique(unidades):
        idx = np.where(unidades == u)[0]
        idx = idx[np.argsort(ciclos[idx], kind="stable")]
        corregido[idx] = R.pava_causal_no_creciente(puntos[idx])

    assert calculate_nasa_score(verdad, corregido) < calculate_nasa_score(verdad, puntos)


@needs_oof
def test_la_cobertura_pura_es_la_nominal():
    """Regresión: la recalibración se ajustó al 90 % en las 14 915 filas puras."""
    cache = np.load(os.path.join(ROOT, "_p1_oof_cache.npz"))
    sys.path.insert(0, os.path.join(ROOT, "src"))
    from ds02_rul.conformal import apply_conformal, empirical_coverage
    from ds02_rul.stacking import select_beta_grouped

    sel = select_beta_grouped(cache["units"], cache["cycles"], cache["y"],
                              cache["p_lstm"], cache["p_lgb"], span=5,
                              use_cycle_feature=False)
    calib = sel["oof_calib"]
    pure = np.isin(np.asarray(calib["units"], float), [2.0, 5.0, 10.0, 18.0, 20.0])
    puntos = np.asarray(calib["pred_ema"], float)[pure]
    unidades = np.asarray(calib["units"], float)[pure]
    ciclos = np.asarray(calib["cycles"], float)[pure]
    verdad = np.asarray(calib["y"], float)[pure]

    corregido = np.empty(len(puntos))
    for u in np.unique(unidades):
        idx = np.where(unidades == u)[0]
        idx = idx[np.argsort(ciclos[idx], kind="stable")]
        corregido[idx] = R.pava_causal_no_creciente(puntos[idx])

    with open(R.CALIBRACION_PATH, encoding="utf-8") as fh:
        cal = json.load(fh)
    lower, upper = apply_conformal(corregido, cal)
    assert empirical_coverage(verdad, lower, upper) == pytest.approx(0.90, abs=0.01)


def test_el_informe_queda_en_el_repositorio():
    """El informe de medición es parte del entregable."""
    assert os.path.exists(os.path.join(ROOT, "INFORME_reglas_oof.md"))
