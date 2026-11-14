"""Contracts for the readable order preview, the honest countdown and grid names.

Found by the second live Playwright audit: the order preview printed an internal JSON
object, the fleet countdown counted a future crossing for a unit already grounded, and
data grids carried no name in the DOM.
"""
from __future__ import annotations

import ast
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, ROOT)

from app.lib import simulacion as S  # noqa: E402
from app.lib import vista_orden as VO  # noqa: E402


# --------------------------------------------------------------- vista de la orden
def _bloqueada(**sobre):
    base = {
        "unidad": 11,
        "estado": "AOG",
        "regla": "R9_HANGAR",
        "ventana_evaluada": {
            "filas": 50, "step": 2, "ciclo": 31,
            "start_index": 3336, "ventanas_en_ciclo": 44,
        },
        "ciclo_simulado": 31,
        "ciclo_evaluado": 31,
        "rul_estimada": 31.4,
        "limite_inferior": 17.0,
        "limite_superior": 45.8,
        "rul_real": 32.0,
        "motivo": "L_inf < 20 ciclos",
        "accion": "derivar a hangar",
    }
    base.update(sobre)
    return base


def test_la_vista_previa_se_lee_y_no_vuelca_json():
    df = VO.tabla_orden([_bloqueada()])

    assert list(df.columns) == [
        "Unidad", "Estado", "Regla", "Ventana evaluada", "Ciclo simulado",
        "Ciclo evaluado", "RUL estimada", "L_inf", "L_sup", "RUL real", "Acción",
    ]
    for celda in df.astype(str).to_numpy().ravel():
        assert "{" not in celda and "}" not in celda, celda
    ventana = str(df.loc[0, "Ventana evaluada"])
    assert "ciclo 31" in ventana and "50 filas" in ventana and "paso 2" in ventana


def test_la_vista_previa_conserva_los_campos_que_justifican():
    df = VO.tabla_orden([_bloqueada()]).iloc[0]

    assert float(df["RUL estimada"]) == pytest.approx(31.4)
    assert float(df["L_inf"]) == pytest.approx(17.0)
    assert float(df["L_sup"]) == pytest.approx(45.8)
    assert float(df["RUL real"]) == pytest.approx(32.0)
    assert str(df["Acción"]) == "derivar a hangar"


def test_la_vista_previa_no_se_rompe_sin_rul_real():
    externa = _bloqueada(unidad=99, rul_real=None)

    df = VO.tabla_orden([externa])

    assert str(df.loc[0, "Unidad"]) == "99"
    assert str(df.loc[0, "RUL real"]).lower() in ("", "nan", "none")


# ------------------------------------------------------------- cuenta atras honesta
def test_una_unidad_ya_en_hangar_no_cuenta_como_que_se_acerca():
    resumen = S.resumen_ciclos_hasta_fallo(
        faltan={11: 1, 14: None, 15: 3},
        actuales={11: 17.0, 14: 40.0, 15: 22.0},
        umbral=20.0,
    )

    assert resumen[11] == "ya por debajo del umbral"
    assert "ciclo" not in resumen[11].lower()
    assert resumen[14] == "nunca en la vida registrada"
    assert resumen[15] == "3 ciclos"


# ------------------------------------------------------------ nombre de las rejillas
def test_cada_rejilla_declara_su_descripcion():
    """`st.dataframe(...)` sin `alt=` deja la rejilla sin nombre accessible."""
    faltan = []
    for ruta in sorted(os.listdir(os.path.join(APP, "ui"))):
        if not ruta.endswith(".py"):
            continue
        arbol = ast.parse(open(os.path.join(APP, "ui", ruta), encoding="utf-8").read())
        for nodo in ast.walk(arbol):
            es_dataframe = (
                isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "dataframe"
                and isinstance(nodo.func.value, ast.Name)
                and nodo.func.value.id == "st"
            )
            if es_dataframe and not any(k.arg == "alt" for k in nodo.keywords):
                faltan.append(f"{ruta}:{nodo.lineno}")

    assert not faltan, f"rejillas sin alt=: {faltan}"
