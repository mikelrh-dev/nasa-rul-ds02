"""Tercera ronda UX: recorte explícito y coma decimal.

Nada aquí toca el modelo: son persistencia de registros, validación de
entrada y símbolos de accesibilidad.
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from app.lib import ui_data_loader as L  # noqa: E402
from app.lib import ui_inference as INF  # noqa: E402


# ------------------------------------------------------- persistencia
def test_gemelos_sobreviven_a_un_reinicio(tmp_path):
    from app.lib import twin as T

    registro = {}
    gemelo = {
        "id": "ESN-T1",
        "source": "test",
        "fingerprint": "abc",
        "created_at": "x",
        "banda": "b",
        "correccion": "c",
        "umbrales": {"apto": 30.0, "hangar": 25.0},
        "contrato": {},
        "serie": [{"cycle": 1.0, "pred": 10.0, "lower": 8.0, "upper": 12.0,
                   "start_row": 0}],
        "truth": None,
    }
    registro = T.registrar(registro, gemelo)
    ruta = str(tmp_path / "twins.json")
    T.guardar_disco(registro, ruta)
    assert T.cargar_disco(ruta) == registro


def test_hangar_sobrevive_a_un_reinicio(tmp_path):
    from app.lib import hangar as HGR

    registros = {"U1": HGR.abrir("U1", 40, 20.0, {"apto": 30.0, "hangar": 25.0}, "R9")}
    ruta = str(tmp_path / "hangar.json")
    HGR.guardar_disco(registros, ruta)
    assert HGR.cargar_disco(ruta) == registros


def test_cargar_sin_fichero_devuelve_vacio(tmp_path):
    from app.lib import hangar as HGR
    from app.lib import twin as T

    assert T.cargar_disco(str(tmp_path / "nope.json")) == {}
    assert HGR.cargar_disco(str(tmp_path / "nope.json")) == {}


# ------------------------------------------------------- recorte
def test_limitar_filas_solo_recorta_por_encima_del_umbral():
    tabla, _ = INF.example_window()
    assert len(tabla) == INF.window_size()
    misma, hubo = INF.limitar_filas(tabla)
    assert hubo is False
    assert len(misma) == len(tabla)

    grande = pd.concat([tabla] * 40, ignore_index=True)
    assert len(grande) > INF.UMBRAL_RECORTE_EDITOR
    cortada, hubo = INF.limitar_filas(grande)
    assert hubo is True
    assert len(cortada) == INF.UMBRAL_RECORTE_EDITOR
    assert list(cortada.columns) == list(grande.columns)


# ------------------------------------------------------- coma decimal
def test_la_coma_decimal_europea_se_sugiere_en_vez_de_un_no_numerico_seco():
    tabla, _ = INF.example_window()
    tabla["Mach"] = tabla["Mach"].astype(object)
    tabla.loc[0, "Mach"] = "0,85"
    with pytest.raises(ValueError, match="coma decimal"):
        INF.validate_table(tabla)


def test_el_reorden_no_oculta_otro_error():
    tabla, _ = INF.example_window()
    tabla["Mach"] = tabla["Mach"].astype(object)
    tabla.loc[0, "Mach"] = "roto"
    with pytest.raises(ValueError, match="no numérico"):
        INF.reordenar_columnas(tabla)


# ------------------------------------------------------- símbolos
def test_cada_estado_tiene_simbolo_y_etiqueta():
    for estado in (L.AIRWORTHY, L.PREVENTIVE, L.AOG, L.NO_DATA, L.SIN_DECISION):
        assert estado in L.STATE_SYMBOLS and L.STATE_SYMBOLS[estado]
        assert estado in L.STATE_LABELS and L.STATE_LABELS[estado]
    assert len(set(L.STATE_SYMBOLS.values())) == len(L.STATE_SYMBOLS)


# ------------------------------------------------------- app
def test_todo_grafico_y_tabla_nuevos_tienen_nombre_accesible():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(ROOT, "app", "entrypoints", "dashboard_ds02.py"),
                            default_timeout=120)
    app.run()
    assert not app.exception, app.exception
    for element in list(app.get("plotly_chart")) + list(app.get("dataframe")):
        assert element.proto.alt and element.proto.alt.strip(), element.proto
