"""Tests del registro de gemelos (`app/twin.py`).

Cuatro invariantes:

1. la huella identifica los valores, no el formato del fichero;
2. el gemelo se construye desde el resultado del modelo y conserva la serie;
3. el estado se deriva al leer (mover el umbral cambia la decisión, no la serie);
4. la verdad reportada da error y cobertura contra la banda guardada.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.lib import twin as T  # noqa: E402

UMBRALES = {"apto": 30.0, "hangar": 25.0}


def _resultado(ventanas: list[tuple[float, float, float, float]]) -> dict:
    filas = []
    for i, (ciclo, pred, lower, upper) in enumerate(ventanas):
        filas.append({"window": i, "cycle": ciclo, "start_row": i, "pred": pred,
                      "lower": lower, "upper": upper})
    return {
        "windows": pd.DataFrame(filas),
        "contract": {"window": 50, "step": 1, "canales": ["alt"],
                     "artefacto_sha256": "a" * 64, "motor": "ESN-01"},
    }


def _tabla(valor: float = 1.0) -> pd.DataFrame:
    return pd.DataFrame({"cycle": [1, 2], "alt": [valor, valor + 0.5]})


def test_la_huella_ignora_el_formato():
    a = pd.DataFrame({"cycle": [1, 2], "alt": [1, 2.5]})
    b = pd.DataFrame({"cycle": [1.0, 2.0], " alt ": [1.0, 2.5]})
    assert T.fingerprint(a) == T.fingerprint(b)
    assert len(T.fingerprint(a)) == 64
    assert T.fingerprint(a) != T.fingerprint(pd.DataFrame({"cycle": [1, 2], "alt": [1, 3.5]}))


def test_el_id_se_normaliza_y_se_valida():
    assert T.normalizar_id(" esn-01 ") == "ESN-01"
    with pytest.raises(ValueError):
        T.normalizar_id("ab")


def test_el_gemelo_guarda_la_serie_y_el_contrato():
    resultado = _resultado([(10.0, 40.0, 35.0, 45.0), (11.0, 30.0, 24.0, 36.0)])
    gemelo = T.make_twin("esn-01", resultado, source="csv", banda="artefacto",
                         correccion="ninguna", umbrales=UMBRALES,
                         fingerprint_value="f" * 64)
    assert gemelo["id"] == "ESN-01"
    assert len(gemelo["serie"]) == 2
    assert gemelo["serie"][1]["lower"] == 24.0
    assert gemelo["contrato"]["motor"] == "ESN-01"
    assert gemelo["truth"] is None


def test_registrar_rechaza_duplicados_sin_tocar_el_original():
    gemelo = T.make_twin("ESN-01", _resultado([(10.0, 40.0, 35.0, 45.0)]),
                         source="csv", banda="artefacto", correccion="ninguna",
                         umbrales=UMBRALES)
    registro = T.registrar({}, gemelo)
    with pytest.raises(ValueError) as exc:
        T.registrar(registro, gemelo)
    assert "ESN-01" in str(exc.value)
    assert len(registro) == 1


def test_registrar_puede_reemplazar_y_conserva_la_verdad():
    """Re-puntuar el mismo motor actualiza la serie; la RUL real no se pierde."""
    viejo = T.make_twin("ESN-01", _resultado([(10.0, 40.0, 35.0, 45.0)]),
                        source="csv", banda="artefacto", correccion="ninguna",
                        umbrales=UMBRALES)
    registro = T.registrar({}, T.con_verdad(viejo, 12.0, 10.0))

    nuevo = T.make_twin("ESN-01", _resultado([(12.0, 30.0, 22.0, 34.0)]),
                        source="csv", banda="artefacto", correccion="ninguna",
                        umbrales=UMBRALES, fingerprint_value="e" * 64)
    actualizado = T.registrar(registro, nuevo, reemplazar=True)
    assert len(actualizado) == 1
    assert actualizado["ESN-01"]["serie"] == nuevo["serie"]
    assert actualizado["ESN-01"]["fingerprint"] == "e" * 64
    assert actualizado["ESN-01"]["truth"]["rul_real"] == 12.0
    # El original no se muta: el registro es nuevo, no un alias.
    assert registro["ESN-01"]["serie"][0]["lower"] == 35.0


def test_eliminar_saca_un_gemelo_y_deja_el_resto():
    uno = T.make_twin("ESN-01", _resultado([(10.0, 40.0, 35.0, 45.0)]),
                      source="csv", banda="artefacto", correccion="ninguna",
                      umbrales=UMBRALES)
    dos = T.make_twin("ESN-02", _resultado([(10.0, 40.0, 35.0, 45.0)]),
                      source="csv", banda="artefacto", correccion="ninguna",
                      umbrales=UMBRALES)
    registro = T.registrar(T.registrar({}, uno), dos)
    assert list(T.eliminar(registro, "esn-01")) == ["ESN-02"]
    assert len(registro) == 2


def test_el_estado_se_deriva_de_la_peor_ventana():
    """Dos ventanas en el mismo ciclo: decide la de menor límite inferior."""
    resultado = _resultado([(10.0, 40.0, 35.0, 45.0),
                            (10.0, 30.0, 24.0, 36.0),
                            (11.0, 31.0, 28.0, 38.0)])
    gemelo = T.make_twin("ESN-01", resultado, source="csv", banda="artefacto",
                         correccion="ninguna", umbrales=UMBRALES)
    curva = T.ciclo_a_ciclo(gemelo, UMBRALES)
    primero = curva[curva["cycle"] == 10.0].iloc[0]
    assert primero["lower_min"] == 24.0
    assert primero["lower_media"] == 29.5
    assert primero["decision"] == "HANGAR"
    assert primero["regla"] == "R9_HANGAR"

    estado = T.estado_actual(gemelo, UMBRALES)
    assert estado["cycle"] == 11.0
    assert estado["decision"] == "INSPECCION"


def test_mover_el_umbral_cambia_la_decision_y_no_la_serie():
    gemelo = T.make_twin("ESN-01", _resultado([(11.0, 31.0, 28.0, 38.0)]),
                         source="csv", banda="artefacto", correccion="ninguna",
                         umbrales=UMBRALES)
    antes = T.estado_actual(gemelo, UMBRALES)["decision"]
    despues = T.estado_actual(gemelo, {"apto": 30.0, "hangar": 29.0})["decision"]
    assert antes == "INSPECCION"
    assert despues == "HANGAR"
    assert gemelo["serie"][0]["lower"] == 28.0


def test_la_verdad_reportada_da_error_y_cobertura():
    gemelo = T.make_twin("ESN-01", _resultado([(40.0, 20.0, 12.0, 30.0)]),
                         source="csv", banda="artefacto", correccion="ninguna",
                         umbrales=UMBRALES)
    con_verdad = T.con_verdad(gemelo, 21.0, 40.0)
    metricas = T.metricas_verdad(con_verdad)
    assert metricas["cubierta"] is True
    assert metricas["error"] == pytest.approx(-1.0)

    fuera = T.metricas_verdad(T.con_verdad(gemelo, 45.0, 40.0))
    assert fuera["cubierta"] is False


def test_con_verdad_rechaza_valores_imposibles():
    gemelo = T.make_twin("ESN-01", _resultado([(40.0, 20.0, 12.0, 30.0)]),
                         source="csv", banda="artefacto", correccion="ninguna",
                         umbrales=UMBRALES)
    with pytest.raises(ValueError):
        T.con_verdad(gemelo, -1.0)


def test_resumen_agrega_cobertura_y_mae():
    a = T.con_verdad(T.make_twin("ESN-A", _resultado([(40.0, 20.0, 12.0, 30.0)]),
                                 source="csv", banda="artefacto",
                                 correccion="ninguna", umbrales=UMBRALES), 21.0)
    b = T.con_verdad(T.make_twin("ESN-B", _resultado([(40.0, 20.0, 12.0, 30.0)]),
                                 source="csv", banda="artefacto",
                                 correccion="ninguna", umbrales=UMBRALES), 45.0)
    resumen = T.resumen({"ESN-A": a, "ESN-B": b, "ESN-C": T.make_twin(
        "ESN-C", _resultado([(40.0, 20.0, 12.0, 30.0)]), source="csv",
        banda="artefacto", correccion="ninguna", umbrales=UMBRALES)})
    assert resumen["total"] == 3
    assert resumen["con_verdad"] == 2
    assert resumen["cubiertos"] == 1
    assert resumen["mae"] == pytest.approx((1.0 + 25.0) / 2)
