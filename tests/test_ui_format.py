"""Contratos de presentación: precisión acotada en las tablas y en las métricas de calidad.

El Streamlit 1.66.0 instalado ignora ``NumberColumn(format=...)`` (comprobado con
una prueba mínima en un servidor de prueba), así que el dashboard formatea los
valores antes de que lleguen a ``st.dataframe``. Estos tests fijan el formateador
compartido, la métrica R2 en vivo y la ausencia de declaraciones de formato
muertas en las tres pestañas con tablas numéricas.
"""
from __future__ import annotations

import ast
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, ROOT)

from app.lib import ui_data_loader as L  # noqa: E402
from app.lib import ui_format as F  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build/build_ui_cache.py`",
)

DASHBOARD = os.path.join(APP, "entrypoints", "dashboard_ds02.py")
TABS = ("_tab_auditoria.py", "_tab_casos.py", "_tab_flota.py")


# --------------------------------------------------------------- formateadores
def test_los_formateadores_redondean_y_con_signo():
    serie = pd.Series([1.23456, -0.72249, None], dtype="float64")

    assert list(F.tres_decimales(serie)) == ["1.235", "-0.722", ""]
    assert list(F.con_signo_3(serie)) == ["+1.235", "-0.722", ""]


def test_entero_y_cuatro_significativos():
    assert list(F.entero(pd.Series([2521.0, None]))) == ["2521", ""]
    assert list(F.cuatro_sig(pd.Series([0.000123456]))) == ["0.0001235"]


def test_formatea_copia_y_deja_lo_demas():
    df = pd.DataFrame({"a": [1.23456], "b": ["x"]})

    out = F.formatea(df, {"a": F.tres_decimales})

    assert list(out["a"]) == ["1.235"]
    assert list(out["b"]) == ["x"]
    assert list(df["a"]) == [1.23456]


# ---------------------------------------------------------------------- metricas
@needs_cache
def test_global_metrics_incluye_el_contrato_de_calidad():
    g = L.global_metrics(L.get_windows())

    assert g["rmse"] == pytest.approx(4.338, abs=0.001)
    assert g["mae"] == pytest.approx(3.227, abs=0.001)
    assert g["nasa_score"] == pytest.approx(2336.2, abs=0.05)
    assert g["r2"] == pytest.approx(0.9461, abs=0.0005)


# ------------------------------------------------------------ contratos de fuente
@pytest.mark.parametrize("tab", TABS)
def test_cada_pestana_formatea_con_el_helper(tab):
    src = open(os.path.join(APP, "ui", tab), encoding="utf-8").read()

    assert "from app.lib.ui_format import" in src, f"{tab} no importa el formateador"
    assert "formatea(" in src, f"{tab} no usa el formateador compartido"


@pytest.mark.parametrize("tab", TABS)
def test_no_queda_format_muerto_en_numbercolumn(tab):
    """Streamlit 1.66 ignora `format=`; declararlo sería configuración muerta."""
    arbol = ast.parse(open(os.path.join(APP, "ui", tab), encoding="utf-8").read())

    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Call)
                and isinstance(nodo.func, ast.Attribute)
                and nodo.func.attr == "NumberColumn"):
            assert not any(k.arg == "format" for k in nodo.keywords), (
                f"{tab} declara un formato que este Streamlit ignora"
            )


# -------------------------------------------------------------------------- UI
@needs_cache
def test_auditoria_muestra_el_contrato_de_calidad():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(DASHBOARD, default_timeout=180)
    app.run()
    assert not app.exception, app.exception

    partes = [m.value for m in app.markdown]
    partes += [c.value for c in app.caption]
    partes += [s.value for s in app.subheader]
    partes += [f"{m.label} {m.value}" for m in app.metric]
    texto = "\n".join(partes)

    for etiqueta in ("MAE ponderado", "NASA score", "R²"):
        assert etiqueta.lower() in texto.lower(), f"falta «{etiqueta}» en la calidad del modelo"
