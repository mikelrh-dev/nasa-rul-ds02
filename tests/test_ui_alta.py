import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))

import pytest

import ui_alta as A
import ui_data_loader as L

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build_ui_cache.py`",
)


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


# ------------------------------------------------------------ modo historia
@needs_cache
def test_el_modo_historia_se_deriva_de_la_cache():
    """Los pasos salen de la caché, no de constantes: si cambia, el test lo ve."""
    pasos = A.estado_historia(L.get_windows(), {"apto": 30.0, "hangar": 25.0})

    assert [p["paso"] for p in pasos] == [1, 2, 3, 4]
    # Paso 1: el hangar esta mañana, en el primer ciclo puntuado.
    assert (pasos[0]["unidad"], pasos[0]["ciclo"]) == (11, 1)
    # Paso 2: la primera inspección del motor problemático (el de mayor RMSE).
    assert (pasos[1]["unidad"], pasos[1]["ciclo"]) == (14, 9)
    # Paso 3: su primera derivación a hangar.
    assert (pasos[2]["unidad"], pasos[2]["ciclo"]) == (14, 29)
    # Paso 4: los mismos umbrales aflojados en 5.
    assert pasos[3]["umbrales"] == {"apto": 35.0, "hangar": 20.0}

    for paso in pasos:
        assert paso["titulo"] and paso["cuenta"]


@needs_cache
def test_el_motor_problematico_es_el_de_mayor_error():
    """El «motor problemático» se deriva, no se escribe: es el de mayor RMSE."""
    pasos = A.estado_historia(L.get_windows(), {"apto": 30.0, "hangar": 25.0})
    rmse = {}
    for unit, grupo in L.get_windows().groupby("unit"):
        residuo = grupo["pred"].to_numpy() - grupo["y_true"].to_numpy()
        rmse[int(unit)] = float((residuo ** 2).mean() ** 0.5)
    assert pasos[1]["unidad"] == max(rmse, key=rmse.get) == 14


@needs_cache
def test_el_paso_critico_cae_en_hangar_y_el_primero_no():
    """Cada paso deja el estado que declara: el crítico deriva, el primero no."""
    pasos = A.estado_historia(L.get_windows(), {"apto": 30.0, "hangar": 25.0})
    ventanas = L.get_windows()

    def estado(unidad, ciclo, umbrales):
        idx = ventanas.groupby(["unit", "cycle"])["lower"].idxmin()
        pc = ventanas.loc[idx, ["unit", "cycle", "lower"]]
        lower = float(pc[(pc["unit"] == unidad) & (pc["cycle"] == ciclo)]["lower"].iloc[0])
        if lower >= umbrales["apto"]:
            return "APTO"
        if lower >= umbrales["hangar"]:
            return "INSPECCION"
        return "HANGAR"

    assert estado(11, 1, pasos[0]["umbrales"]) == "APTO"
    assert estado(14, 8, pasos[1]["umbrales"]) == "APTO"
    assert estado(14, 29, pasos[2]["umbrales"]) == "HANGAR"
