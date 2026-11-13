import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import pytest

from app.lib import alta as A
from app.lib import ui_data_loader as L

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build/build_ui_cache.py`",
)


def _banda(v):
    return L.classify(v)


def test_perfiles_caen_en_su_banda():
    windows = L.get_windows()
    idx = windows.groupby(["unit", "cycle"])["lower"].idxmin()
    pc = windows.loc[idx, ["unit", "cycle", "lower"]]
    esperado = {
        "Recién salido de revisión": "APTO",
        "Recién salido de revisión (U15)": "APTO",
        "Desgaste operativo medio": "INSPECCION",
        "Desgaste operativo medio (U14)": "INSPECCION",
        "Fin de vida / crítico": "HANGAR",
        "Fin de vida / crítico (U11)": "HANGAR",
        "Caso atípico (U14)": "APTO",
    }
    for perfil, (u, c) in A.PERFILES.items():
        row = pc[(pc["unit"] == u) & (pc["cycle"] == c)]
        assert len(row) == 1, f"{perfil}: sin ciclo {c} para U{u}"
        assert _banda(float(row.iloc[0]["lower"])) == esperado[perfil]


def test_ciclos_inexistentes_lanzan_valueerror():
    windows = L.get_windows()
    with pytest.raises(ValueError):
        A.ventanas_de_alta(windows, 14, 1, A.unidad_alta(0))
    with pytest.raises(ValueError):
        A.ventanas_de_alta(windows, 15, 1, A.unidad_alta(1))


def test_el_estado_de_demo_es_el_medido():
    demo = A.estado_demo()
    assert demo["umbrales"] == (25.0, 20.0)
    assert demo["ciclo"] == 34
    assert demo["unidad"] == 14


def test_una_aeronave_de_alta_entra_en_la_flota():
    windows = L.get_windows()
    altas = [
        {
            "matricula": "EC-MKR",
            "unidad": 11,
            "ciclo": 27,  # C: U11 L_inf<20 desde el 27 con la política 25/20
            "unit_id": A.unidad_alta(0),
        }
    ]
    frame = A.frame_con_altas(
        windows, windows, altas, False, {"apto": 25.0, "hangar": 20.0}
    )
    snapshot = L.fleet_snapshot(frame, 27, 25.0, 20.0)
    assert int(A.unidad_alta(0)) in set(snapshot["unit"])
    fila = snapshot[snapshot["unit"] == int(A.unidad_alta(0))].iloc[0]
    assert fila["state"] == L.AOG
