"""Tests del ciclo de hangar (`app/hangar.py`).

El módulo es una máquina de estados pura: transiciones permitidas, cola por
urgencia y una decisión de entrada que **no** se reescribe cuando cambian los
umbrales. Nada de Streamlit aquí.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import os
import sys

import pytest

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
sys.path.insert(0, APP)

import hangar as H  # noqa: E402

UMBRALES = {"apto": 30.0, "hangar": 25.0}


def test_abrir_congela_la_decision_de_entrada():
    registro = H.abrir("ESN-01", 40, 24.0, UMBRALES, "R9_HANGAR", nota="AOG")
    assert registro["estado"] == H.AOG
    assert registro["entrada"] == {
        "ciclo": 40, "lower": 24.0,
        "umbrales": {"apto": 30.0, "hangar": 25.0},
        "regla": "R9_HANGAR",
    }
    assert [e["estado"] for e in registro["eventos"]] == [H.AOG]


def test_avanzar_acepta_solo_la_ruta_declarada():
    registro = H.abrir("ESN-01", 40, 24.0, UMBRALES, "R9_HANGAR")
    with pytest.raises(ValueError) as exc:
        H.avanzar(registro, H.EN_SERVICIO, 41)
    assert "no permitida" in str(exc.value)
    assert H.TALLER in str(exc.value)

    en_taller = H.avanzar(registro, H.TALLER, 41, nota="desmontaje")
    assert en_taller["estado"] == H.TALLER
    assert en_taller["eventos"][-1]["nota"] == "desmontaje"
    # El original no se muta: la máquina devuelve copias.
    assert registro["estado"] == H.AOG


def test_el_ciclo_completo_vuelve_al_servicio():
    registro = H.abrir("ESN-01", 40, 24.0, UMBRALES, "R9_HANGAR")
    for destino, ciclo in ((H.TALLER, 41), (H.BANCO, 42), (H.EN_SERVICIO, 43)):
        registro = H.avanzar(registro, destino, ciclo)
    assert registro["estado"] == H.EN_SERVICIO
    assert len(registro["eventos"]) == 4


def test_la_cola_ordena_por_urgencia():
    en_taller = H.avanzar(
        H.abrir("ESN-A", 10, 22.0, UMBRALES, "R9_HANGAR"), H.TALLER, 11)
    registros = {
        "ESN-B": H.abrir("ESN-B", 12, 18.0, UMBRALES, "R9_HANGAR"),
        "ESN-A": en_taller,
        "ESN-C": H.abrir("ESN-C", 9, 24.0, UMBRALES, "R9_HANGAR"),
        "ESN-D": H.abrir("ESN-D", 9, 40.0, UMBRALES, "R7_APTO",
                         estado=H.EN_SERVICIO),
    }
    orden = [r["unidad"] for r in H.cola(registros)]
    assert orden == ["ESN-B", "ESN-C", "ESN-A"]


def test_la_revision_no_reescribe_la_entrada():
    """Subir o bajar el umbral después no cambia lo que se decidió."""
    registro = H.abrir("ESN-01", 40, 24.0, UMBRALES, "R9_HANGAR")
    revision = H.revision(registro, {"apto": 30.0, "hangar": 20.0}, "INSPECCION")
    assert revision["congelada"] == "HANGAR"
    assert revision["hoy"] == "INSPECCION"
    assert revision["cambia"] is True
    assert revision["umbrales_entrada"] == {"apto": 30.0, "hangar": 25.0}
    assert revision["umbrales_hoy"] == {"apto": 30.0, "hangar": 20.0}
    assert registro["entrada"]["lower"] == 24.0


def test_resumen_cuenta_abiertos_y_estados():
    registros = {
        "ESN-A": H.abrir("ESN-A", 1, 20.0, UMBRALES, "R9_HANGAR"),
        "ESN-B": H.abrir("ESN-B", 1, 40.0, UMBRALES, "R7_APTO",
                         estado=H.EN_SERVICIO),
    }
    resumen = H.resumen(registros)
    assert resumen["total"] == 2
    assert resumen["abiertos"] == 1
    assert resumen["por_estado"][H.AOG] == 1
    assert resumen["por_estado"][H.EN_SERVICIO] == 1


def test_estado_desconocido_es_un_error():
    with pytest.raises(ValueError):
        H.abrir("ESN-01", 1, 24.0, UMBRALES, "R9_HANGAR", estado="VOLANDO")
