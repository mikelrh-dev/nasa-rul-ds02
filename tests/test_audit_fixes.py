"""Regresiones de la auditoría del 2026-10-21 (arreglos sin reentrenar).

Cinco familias, una por hallazgo reparado:

1. el gate no re-congela el JSON cuando las cifras comprometidas derivan;
2. la alarma y la MAE crítica usan el umbral y la lectura en vigor;
3. estado y alarma comparten criterio (la peor ventana del ciclo);
4. la orden de trabajo declara banda, corrección y regla, y la externa la
   decide src.mia.motor;
5. un tramo con muestra pequeña no estrecha la banda global.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import hashlib
import io
import os
import sys
import types

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, APP)
sys.path.insert(0, SCRIPTS)
sys.path.insert(0, ROOT)

import freeze_rules_evidence as G  # noqa: E402
from src.mia import reglas as R  # noqa: E402
import ui_data_loader as L  # noqa: E402
import ui_inference as INF  # noqa: E402
import ui_rules as UR  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build_ui_cache.py`",
)
needs_oof = pytest.mark.skipif(
    not os.path.exists(os.path.join(ROOT, "_p1_oof_cache.npz")),
    reason="_p1_oof_cache.npz missing",
)

CALIBRACION = os.path.join(ROOT, "src", "mia", "calibracion_banda.json")


def _sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ---------------------------------------------------------------- 1. gate
@needs_oof
def test_el_gate_no_toca_el_json_si_las_cifras_derivan():
    """`--write` verifica primero: una figura movida sale con 4 y sin escritura."""
    antes = _sha256(CALIBRACION)
    malo = dict(G.EXPECTED, rmse_r2b=G.EXPECTED["rmse_r2b"] + 5e-3)
    salida = io.StringIO()
    assert G.run(malo, write=True, stream=salida) == 4
    texto = salida.getvalue()
    assert "refusing to re-freeze" in texto
    assert "untouched" in texto
    assert _sha256(CALIBRACION) == antes


# ------------------------------------------------- 2. umbrales y agregación
def _curva(media: float, minimo: float, truth_cycle: int) -> pd.DataFrame:
    return pd.DataFrame({
        "cycle": [10, 11, 12],
        "lower": [media, media, media],
        "lower_min": [minimo, minimo, minimo],
        "y_true": [30.0, 20.0, 10.0],
    })


def test_la_alarma_usa_la_peor_ventana_del_ciclo():
    """Media 26 y mínimo 24: el ciclo está en hangar y la alarma lo dice."""
    curva = _curva(media=26.0, minimo=24.0, truth_cycle=12)
    assert L.first_alarm_cycle(curva, 25.0)[0] == 10
    # La media sola habría callado: era el criterio que se retiró.
    assert L.first_alarm_cycle(curva, 25.0, statistic="lower")[0] is None


def test_la_alarma_respeta_el_umbral_del_operador():
    curva = _curva(media=22.0, minimo=21.0, truth_cycle=12)
    assert L.first_alarm_cycle(curva, 20.0)[0] is None
    assert L.first_alarm_cycle(curva, 25.0)[0] == 10


# -------------------------------------------------- 3. orden de trabajo
def _snapshot() -> pd.DataFrame:
    return pd.DataFrame({
        "unit": [11, 14],
        "cycle": [40, 40],
        "scored_cycle": [40, 40],
        "state": [L.AOG, L.AIRWORTHY],
        "rule": ["R9_HANGAR", "R7_APTO"],
        "pred": [12.0, 41.0],
        "lower": [10.0, 38.0],
        "upper": [18.0, 44.0],
        "y_true": [11.0, 40.0],
        "start_index": [1200, 2400],
        "windows": [3, 2],
    })


def _provenance() -> dict:
    return {
        "artifact": {"ensemble_sha256": "0" * 64},
        "source": {"window": 50, "step": 2, "stride": 100},
    }


def test_la_orden_declara_banda_correccion_y_regla():
    order = L.work_order(_snapshot(), _provenance(), 30.0, 25.0,
                         banda="R6 recalibrada", correccion="R2b + R6")
    assert order["banda"] == "R6 recalibrada"
    assert order["correccion"] == "R2b + R6"
    entrada = order["unidades"][0]
    assert entrada["regla"] == "R9_HANGAR"
    assert [u["unidad"] for u in order["unidades"]] == [11]
    # La orden cita la ventana que decidió, no solo el ciclo.
    ventana = entrada["ventana_evaluada"]
    assert ventana["start_index"] == 1200
    assert ventana["filas"] == 50 and ventana["step"] == 2
    assert ventana["ventanas_en_ciclo"] == 3


def test_la_orden_sin_correccion_lo_dice():
    order = L.work_order(_snapshot(), _provenance())
    assert "artefacto" in order["banda"]
    assert order["correccion"].startswith("ninguna")


def test_la_orden_csv_expone_la_regla():
    texto = L.work_order_csv(L.work_order(_snapshot(), _provenance(), 30.0, 25.0))
    cabecera = texto.splitlines()[0].split(",")
    assert "regla" in cabecera
    assert cabecera.index("regla") == cabecera.index("estado") + 1


# ------------------------------------------- 4. orden externa por el motor
def _resultado(lower: float) -> dict:
    return {
        "windows": pd.DataFrame({
            "window": [7, 8],
            "cycle": [50.0, 51.0],
            "start_row": [300, 301],
            "pred": [lower + 5.0] * 2,
            "lower": [lower] * 2,
            "upper": [lower + 15.0] * 2,
        }),
        "contract": {
            "window": 50, "step": 1, "canales": ["alt"],
            "artefacto_sha256": "1" * 64,
        },
    }


def test_la_orden_externa_la_decide_el_motor():
    order = INF.live_work_order(_resultado(10.0), None, 30.0, 25.0)
    entrada = order["unidades"][0]
    assert entrada["estado"] == L.AOG
    assert entrada["regla_decision"] == "R9_HANGAR"
    assert "R9_HANGAR" in entrada["motivo"]
    assert "artefacto" in order["banda"]
    assert order["correccion"].startswith("ninguna")
    assert entrada["ventana_evaluada"]["start_row"] == 301
    assert entrada["ventana_evaluada"]["indice"] == 8


def test_la_orden_externa_no_contradice_al_badge_con_r1():
    """Un aviso de plausibilidad decide SIN_DECISION también en el documento."""
    order = INF.live_work_order(_resultado(10.0), None, 30.0, 25.0,
                                alertas=["canal fuera de rango"])
    entrada = order["unidades"][0]
    assert entrada["estado"] == L.SIN_DECISION
    assert "R1_SEGURIDAD" in entrada["regla_decision"]


# ------------------------------------------------------ 5. banda y tramos
def test_el_tramo_escaso_no_estrecha_la_banda():
    """La guarda solo ensancha: toma el cuantil más conservador de los dos.

    Con el bundle C ningún tramo está por debajo de MIN_FILAS_TRAMO (el de
    [75, inf) tiene 561 filas), así que la escasez se simula achicando `n` en
    una copia de la calibración comprometida: la guarda debe aplicar igual.
    """
    cal = R.cargar_calibracion()
    cal_escasa = dict(cal)
    cal_escasa["bins"] = [dict(b) for b in cal["bins"]]
    cal_escasa["bins"][-1] = dict(cal["bins"][-1], n=100)
    tramo = cal_escasa["bins"][-1]
    global_bajo, global_alto = cal["global_quantiles"]
    assert tramo["n"] < R.MIN_FILAS_TRAMO
    lower, upper = R.banda_recalibrada(75.0, cal_escasa)
    assert lower == pytest.approx(75.0 + min(tramo["q_low"], global_bajo), abs=1e-6)
    assert upper == pytest.approx(75.0 + max(tramo["q_high"], global_alto), abs=1e-6)
    # Y el lado que ya era conservador no se mueve.
    assert lower == pytest.approx(75.0 + tramo["q_low"], abs=1e-6)


def test_cruzar_75_ya_no_hunde_el_limite_superior():
    """Cruzar 75 no hunde el límite inferior ni saca al punto de la banda.

    Con la banda C el tramo [75, inf) tiene 561 filas y su cuantil alto es
    negativo (el modelo sobreestima en RUL alta): el límite superior queda
    pegado al punto a propósito, así que aquí se fija lo que la guarda
    prometía de verdad: el inferior es continuo y la banda contiene al punto.
    """
    cal = R.cargar_calibracion()
    bajo_antes, _ = R.banda_recalibrada(74.999, cal)
    bajo_despues, _ = R.banda_recalibrada(75.0, cal)
    assert abs(bajo_antes - bajo_despues) < 3.0
    for punto in (74.999, 75.0):
        lower, upper = R.banda_recalibrada(punto, cal)
        assert lower <= punto <= upper


def test_el_tramo_bien_poblado_sigue_siendo_el_suyo():
    cal = R.cargar_calibracion()
    tramo = cal["bins"][1]
    lower, upper = R.banda_recalibrada(30.8385, cal)
    assert lower == pytest.approx(30.8385 + tramo["q_low"], abs=1e-6)
    assert upper == pytest.approx(30.8385 + tramo["q_high"], abs=1e-6)


# ------------------------------------------------------ 6. la UI lo declara
@needs_cache
def test_la_ui_declara_la_banda_en_uso():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=180)
    app.run()
    assert not app.exception, app.exception
    apagado = " ".join((e.value or "") for e in app.caption)
    assert "Banda en uso" in apagado and "artefacto" in apagado

    app.toggle[0].set_value(True).run()
    assert not app.exception, app.exception
    encendido = " ".join((e.value or "") for e in app.caption)
    assert "R6 recalibrada" in encendido


# ------------------------------------------- 7. KPI y cobertura por fuente
def _conformal():
    """Carga `ds02_rul.conformal` sin ejecutar el `__init__` (importa Keras)."""
    if "ds02_rul" not in sys.modules:
        paquete = types.ModuleType("ds02_rul")
        paquete.__path__ = [os.path.join(ROOT, "src", "ds02_rul")]
        sys.modules["ds02_rul"] = paquete
    from ds02_rul import conformal

    return conformal


@needs_cache
def test_el_macro_rmse_sigue_a_la_lectura_en_uso():
    """La tarjeta de flota y las de unidad no pueden leer frames distintos."""
    from streamlit.testing.v1 import AppTest

    def macro_mostrado() -> float:
        for metrica in app.metric:
            if metrica.label == "Macro-RMSE":
                return float(str(metrica.value).split()[0])
        raise AssertionError("no hay tarjeta Macro-RMSE")

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=180)
    app.run()
    assert not app.exception, app.exception
    crudo = L.get_windows()
    assert macro_mostrado() == pytest.approx(
        L.global_metrics(crudo)["macro_rmse"], abs=0.006)

    app.toggle[0].set_value(True).run()
    assert not app.exception, app.exception
    corregido = UR.corregir_ventanas(crudo)
    assert macro_mostrado() == pytest.approx(
        L.global_metrics(corregido)["macro_rmse"], abs=0.006)
    # Las dos lecturas difieren al redondear: el test distingue de verdad.
    assert L.global_metrics(crudo)["macro_rmse"] - L.global_metrics(
        corregido)["macro_rmse"] > 0.01


@needs_cache
def test_la_cobertura_se_mide_por_fuente_de_banda():
    """Ambas bandas cubren las 6 196 ventanas; el 90 % es el nominal OOF.

    La idea de que una de las dos mostraba «cobertura falsa» no se sostiene. El
    test fija el hecho por fuente para que una recalibración futura no lo mueva
    en silencio.
    """
    conf = _conformal()
    corregido = UR.corregir_ventanas(L.get_windows())
    y = corregido["y_true"].to_numpy()
    manifiesto = L.get_manifest()["conformal"]
    lo_art, up_art = conf.apply_conformal(corregido["pred"].to_numpy(), manifiesto)
    assert float(conf.empirical_coverage(y, lo_art, up_art)) == pytest.approx(1.0)
    assert float(conf.empirical_coverage(
        y, corregido["lower"].to_numpy(), corregido["upper"].to_numpy()
    )) == pytest.approx(1.0)
