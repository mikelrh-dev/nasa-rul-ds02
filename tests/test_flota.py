"""Tests del registro de motores (`app/flota.py`).

El registro es la unica fuente de nombres de motor: una clave y una etiqueta
por motor, en el muro, en los gemelos, en el hangar y en las ordenes. Cuatro
vistas, una clave.

Modulo puro: no importa Streamlit, para poder probarlo sin levantar la app.

Run:  python -m pytest tests/test_flota.py -q
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import flota as M  # noqa: E402
import ui_data_loader as L  # noqa: E402


def test_cada_motor_tiene_una_clave_y_una_etiqueta():
    # La etiqueta de la cache sale de L.UNIT_LABELS, nunca se reescribe.
    assert M.etiqueta("U11") == L.UNIT_LABELS[11]
    assert M.etiqueta("U14") == L.UNIT_LABELS[14]
    assert M.etiqueta("U15") == L.UNIT_LABELS[15]
    # Una clave externa (matricula o id de gemelo) es su propia etiqueta.
    assert M.etiqueta("EC-MKR") == "EC-MKR"


def test_la_clave_y_la_unidad_son_inversas():
    for clave, unidad in [("U11", 11.0), ("U14", 14.0), ("U15", 15.0)]:
        assert M.clave_de(unidad) == clave
        assert M.unidad_de(clave) == unidad


def test_una_alta_toma_su_matricula_como_clave():
    registro = {}
    registro = M.registrar_alta(registro, "EC-MKR", unidad_cache=11, ciclo=20)
    assert "EC-MKR" in registro[M.ALTAS_KEY]
    assert M.etiqueta("EC-MKR") == "EC-MKR"
    # Con el registro cargado, el id negativo vuelve a su matricula.
    assert M.clave_de(registro[M.ALTAS_KEY]["EC-MKR"]["unit_id"], registro) == "EC-MKR"
    assert M.unidad_de("EC-MKR", registro) == registro[M.ALTAS_KEY]["EC-MKR"]["unit_id"]
    # Sin registro degrada a U<int>, que es lo que hace la cache hoy.
    assert M.clave_de(-1000.0) == "U-1000"


def test_el_contador_de_alta_no_reutiliza_ids():
    registro = {}
    for matricula in ("AAA-111", "BBB-222"):
        registro = M.registrar_alta(registro, matricula, unidad_cache=11, ciclo=20)
    id_aaa = registro[M.ALTAS_KEY]["AAA-111"]["unit_id"]
    registro = M.quitar_alta(registro, "AAA-111")
    registro = M.registrar_alta(registro, "CCC-333", unidad_cache=11, ciclo=20)
    id_ccc = registro[M.ALTAS_KEY]["CCC-333"]["unit_id"]
    ids = [alta["unit_id"] for alta in registro[M.ALTAS_KEY].values()]
    assert len(ids) == len(set(ids)), ids
    # El id de CCC-333 no puede ser el que tenia AAA-111: el contador solo crece.
    assert id_ccc != id_aaa, f"el id {id_ccc} reutiliza el de AAA-111 ({id_aaa})"
    assert id_ccc < id_aaa  # negativos decrecientes: el nuevo es siempre mas bajo


def test_la_matricula_corta_lanza_valueerror():
    import pytest

    with pytest.raises(ValueError):
        M.normalizar_matricula("AB")
