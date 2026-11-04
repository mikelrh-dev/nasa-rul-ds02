"""Tests del simulador de turnos (`app/simulacion.py`).

El simulador es el punto que minimiza Streamlit: la logica de turnos vive en
un modulo puro, sin `st.`, y el dashboard solo la dibuja. Asi es testeable sin
servidor.

Lee la cache ya puntuada. No llama al modelo: re-puntuar una ventana no
reproduce la cache (el punto esta suavizado con un EMA causal y la cache va a
step=2 mientras la via en vivo va a step=1).

Run:  python -m pytest tests/test_simulacion.py -q
"""
from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "app"))

import flota as F  # noqa: E402
import simulacion as S  # noqa: E402
import ui_data_loader as L  # noqa: E402
import ui_rules as UR  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build_ui_cache.py`",
)

UMBRALES = {"apto": 30.0, "hangar": 25.0}


@needs_cache
def _frame():
    """Frame decidido de la cache, tal como lo consume el simulador."""
    windows = L.get_windows()
    return UR.decidir_ventanas(windows, UMBRALES)


@needs_cache
def test_avanzar_mueve_toda_la_flota_menos_los_retenidos():
    frame = _frame()
    ciclo = 10
    retenidos = S.retenidos(frame, ciclo, UMBRALES)
    avance = S.avanzar(frame, ciclo, retenidos, n=10)

    for unidad, nuevo in avance.items():
        if unidad in retenidos:
            assert nuevo == ciclo, (unidad, nuevo)
        else:
            assert nuevo == ciclo + 10, (unidad, nuevo)


@needs_cache
def test_un_motor_que_cruza_el_umbral_queda_retenido():
    """U14 cruza a hangar en el ciclo 25 (C; B: 29): desde ahi no debe avanzar."""
    frame = _frame()
    # Antes del cruce, no esta retenido.
    assert 14 not in S.retenidos(frame, 10, UMBRALES)
    # En el ciclo del cruce, si.
    assert 14 in S.retenidos(frame, 29, UMBRALES)
    # Y el avance lo deja donde esta.
    assert S.avanzar(frame, 29, {14}, n=10)[14] == 29


@needs_cache
def test_ciclos_hasta_fallo_coincide_con_la_cache():
    """Los ciclos que faltan se leen de la cache, no se calculan de nuevo."""
    frame = _frame()
    faltan = S.ciclos_hasta_fallo(frame, 1, UMBRALES)

    # U14 entra en hangar en el ciclo 25 segun la cache C (B: 29).
    assert faltan[14] == 24, faltan[14]
    # U11 entra en hangar en el ciclo 23 (B: 22).
    assert faltan[11] == 22, faltan[11]
    # Todos los motores tienen un numero: la cache cubre toda su vida.
    assert set(faltan) == {11, 14, 15}


@needs_cache
def test_reiniciar_vida_vuelve_al_primer_ciclo_y_se_marca_como_replay():
    """El reinicio es un replay de la vida registrada, no una reparacion."""
    frame = _frame()
    registro = {}
    registro = F.registrar_alta(registro, "EC-REPLAY", unidad_cache=11, ciclo=20)
    # El motor esta en taller desde el ciclo 20.
    registro = S.reiniciar_vida(registro, "EC-REPLAY", ciclo_taller=20)

    alta = registro[F.ALTAS_KEY]["EC-REPLAY"]
    assert alta["replay_desde"] == 20
    # El primer ciclo puntuado de la U11 es el 1: vuelve a empezar.
    assert alta["ciclo"] == 1
    # Y el marco dice la verdad: es repetir lo grabado, no reparar.
    assert "replay" in alta["motivo"].lower()


@needs_cache
def test_reiniciar_un_motor_que_no_existe_lanza_valueerror():
    registro = {}
    with pytest.raises(ValueError, match="EC-NAUFRAGIO"):
        S.reiniciar_vida(registro, "EC-NAUFRAGIO", ciclo_taller=10)
