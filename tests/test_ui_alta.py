import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest

import ui_alta as A
import ui_data_loader as L


def _banda(v):
    return "APTO" if v >= 30 else ("INSPECCION" if v >= 25 else "HANGAR")


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
    assert demo["umbrales"] == (30.0, 25.0)
    assert demo["ciclo"] == 29
    assert demo["unidad"] == 14


def test_una_aeronave_de_alta_entra_en_la_flota():
    windows = L.get_windows()
    altas = [
        {
            "matricula": "EC-MKR",
            "unidad": 11,
            "ciclo": 22,
            "unit_id": A.unidad_alta(0),
        }
    ]
    frame = A.frame_con_altas(
        windows, windows, altas, False, {"apto": 30.0, "hangar": 25.0}
    )
    snapshot = L.fleet_snapshot(frame, 22, 30.0, 25.0)
    assert int(A.unidad_alta(0)) in set(snapshot["unit"])
    fila = snapshot[snapshot["unit"] == int(A.unidad_alta(0))].iloc[0]
    assert fila["state"] == L.AOG
