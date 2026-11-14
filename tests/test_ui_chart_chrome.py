"""Contratos de legibilidad del chrome de los graficos Plotly del dashboard.

Todas las figuras del dashboard salen de `chart_layout`/`style_axes`
(`app/lib/theme.py`). Con margenes de 8 px y sin `automargin`, Plotly dibujaba
ticks y titulos de eje fuera del viewport del SVG y la leyenda se envolvia sobre
el area de trazado (medido en el DOM vivo de 127.0.0.1:8501). Tambien la modebar
flotante se superponia a la esquina superior derecha y la tabla de tramos
duplicaba una columna cruda en ingles.

Estos tests fijan ese contrato. No miden pixels: comprueban el layout que el
codigo entrega a Plotly y que todos los puntos de llamada usan el mismo config.

Run:  python -m pytest tests/test_ui_chart_chrome.py -q
"""
from __future__ import annotations

import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, ROOT)

from app.lib.theme import chart_layout  # noqa: E402


# ------------------------------------------------------------------ layout
def test_chart_layout_reserva_aire_para_ticks_y_titulos():
    """Con 8 px los ticks X perdian hasta 12 px por abajo y los de Y por la izquierda."""
    layout = chart_layout()
    margin = layout["margin"]
    assert margin["l"] >= 56, "el margen izquierdo debe sacar los ticks del eje Y"
    assert margin["b"] >= 64, "el margen inferior debe sacar ticks y titulo de X"


def test_chart_layout_activa_automargin_en_ambos_ejes():
    layout = chart_layout()
    assert layout["xaxis"]["automargin"] is True
    assert layout["yaxis"]["automargin"] is True


def test_chart_layout_con_overrides_respeta_automargin():
    """Un llamador puede ensanchar margenes, pero no debe quedarse sin automargin."""
    layout = chart_layout(margin=dict(l=80, r=20, t=44, b=70))
    assert layout["margin"]["l"] == 80
    assert layout["xaxis"]["automargin"] is True
    assert layout["yaxis"]["automargin"] is True


def test_leyenda_debajo_del_area_de_trazado():
    legend = chart_layout()["legend"]
    assert legend["orientation"] == "h"
    assert legend["yanchor"] == "top"
    assert legend["y"] < 0, "la leyenda debe colgar por debajo del plot, no encima"


# ------------------------------------------------------- config compartido
def test_el_config_del_dashboard_apaga_la_modebar():
    from app.lib import theme

    assert getattr(theme, "CHART_CONFIG", None) == {"displayModeBar": False}


def _llamadas_plotly_chart(ruta: str) -> list[ast.Call]:
    arbol = ast.parse(open(ruta, encoding="utf-8").read())
    return [
        nodo for nodo in ast.walk(arbol)
        if isinstance(nodo, ast.Call)
        and isinstance(nodo.func, ast.Attribute)
        and nodo.func.attr == "plotly_chart"
    ]


def test_cada_grafico_usa_el_config_compartido():
    rutas = []
    for base, _dirs, ficheros in os.walk(APP):
        if "__pycache__" in base:
            continue
        for nombre in ficheros:
            if nombre.endswith(".py"):
                rutas.append(os.path.join(base, nombre))

    llamadas = [(r, c) for r in rutas for c in _llamadas_plotly_chart(r)]
    assert llamadas, "no se encontro ningun st.plotly_chart en app/"

    for ruta, llamada in llamadas:
        claves = {k.arg for k in llamada.keywords}
        assert "config" in claves, f"{ruta}:{llamada.lineno} no pasa config"
        kw = next(k for k in llamada.keywords if k.arg == "config")
        assert isinstance(kw.value, ast.Name) and kw.value.id == "CHART_CONFIG", (
            f"{ruta}:{llamada.lineno} debe usar CHART_CONFIG, no una literal"
        )


# ------------------------------------------------------ tabla de tramos
def test_tabla_de_tramos_sin_columna_duplicada():
    ruta = os.path.join(APP, "ui", "_tab_auditoria.py")
    src = open(ruta, encoding="utf-8").read()
    arbol = ast.parse(src)

    for nodo in ast.walk(arbol):
        if (
            isinstance(nodo, ast.Call)
            and isinstance(nodo.func, ast.Attribute)
            and nodo.func.attr == "assign"
        ):
            for kw in nodo.keywords:
                assert kw.arg != "Tramo", (
                    f"{ruta}:{nodo.lineno} duplica la columna con assign(Tramo=...)"
                )

    normalizado = src.replace("'", '"')
    assert 'rename(columns={"band": "Tramo"})' in normalizado, (
        "la tabla debe renombrar band -> Tramo en vez de copiarla"
    )
