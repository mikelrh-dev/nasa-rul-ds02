"""Radiografia alineada por RUL: contratos y hallazgo medido sobre la cache.

Comprueba que la vista agregada se construye desde la cache con la misma
definicion de baseline que la vista por ciclo, que el hallazgo medido se
sostiene en estos datos y que la figura y el caption no pueden desmentirlo.

Run:  python -m pytest tests/test_radioografia_alineada.py -q
"""
from __future__ import annotations

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, ROOT)

from app.lib import theme as TH  # noqa: E402
from app.lib import ui_data_loader as L  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build/build_ui_cache.py`",
)

PRESIONES = ["P15", "P2", "P21", "P24", "Ps30", "P40", "P50"]
TEMAS = ["T24", "T2", "T50"]
CANALES = TEMAS + PRESIONES
ROWS_PATH = os.path.join(APP, "cache", "ds02_rows.parquet")


# --------------------------------------------------------------- contratos
@needs_cache
def test_el_frame_alineado_tiene_columnas_y_una_fila_por_unidad_ciclo_canal():
    frame, resumen = L.drift_por_rul(["T50", "P24"])

    assert {"unit", "cycle", "rul", "canal", "deriva"} <= set(frame.columns)
    assert len(frame) == len(frame.drop_duplicates(["unit", "cycle", "canal"]))
    assert set(resumen.index) == {"T50", "P24"}


@needs_cache
def test_la_baseline_es_la_media_de_los_5_primeros_ciclos_de_cada_unidad():
    rows = pd.read_parquet(ROWS_PATH)
    frame, _ = L.drift_por_rul(["T50"])

    for unidad, grupo in rows.groupby("unit"):
        por_ciclo = grupo.groupby("cycle")["T50"].mean().sort_index()
        baseline = por_ciclo.head(5).mean()
        esperado = ((por_ciclo / baseline - 1.0) * 100.0).rename("esperado")
        obtenido = (
            frame[frame["unit"] == unidad]
            .pivot_table(index="cycle", values="deriva", aggfunc="first")
            .sort_index()
        )
        comparacion = obtenido.join(esperado, how="inner")
        assert len(comparacion) > 0
        assert (comparacion["deriva"].round(4) == comparacion["esperado"].round(4)).all()


@needs_cache
def test_el_hallazgo_medido_se_sostiene_en_esta_cache():
    """Medido: solo T50 combina efecto y tendencia; las presiones no tienen ninguna."""
    _, resumen = L.drift_por_rul(CANALES)

    t50 = resumen.loc["T50"]
    assert t50["salto"] > 0.5, "T50 debe subir entre el inicio y el fin de la vida"
    assert t50["corr_rul"] < -0.3, "T50 debe subir al bajar el RUL"
    for ch in PRESIONES:
        assert abs(resumen.loc[ch, "corr_rul"]) < 0.15, f"{ch} no debe tener tendencia"


@needs_cache
def test_el_resaltado_es_exactamente_el_conjunto_calculado_por_correlacion():
    frame, resumen = L.drift_por_rul(CANALES)

    calculados = [
        canal for canal in CANALES
        if abs(resumen.loc[canal, "corr_rul"]) >= 0.3
        and abs(resumen.loc[canal, "salto"]) >= 0.5
    ]
    marcados = resumen.index[resumen["resaltar"]].tolist()

    assert sorted(marcados) == sorted(calculados)
    assert "T50" in marcados


# ------------------------------------------------------------- figura y texto
@needs_cache
def test_la_figura_alineada_marca_la_zona_critica_y_resalta_lo_que_deriva():
    canales = TEMAS + PRESIONES[:2]
    frame, resumen = L.drift_por_rul(canales)

    fig = TH.fig_deriva_vida(frame, resumen, canales, threshold_aog=20.0)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) == len(canales)
    anchos = {traza.name: (traza.line.width or 0) for traza in fig.data}
    assert anchos["T50"] > anchos["P15"], "el canal con deriva debe destacar"
    rectangulos = [forma for forma in fig.layout.shapes if forma.type == "rect"]
    assert rectangulos, "falta la banda critica (RUL < umbral)"
    assert fig.layout.margin.t >= 72, "el titulo Y rotado necesita margen superior"


@needs_cache
def test_el_caption_trae_cifras_calculadas_metodo_y_fuente():
    _, resumen = L.drift_por_rul(CANALES)

    texto = TH.caption_deriva_vida(resumen)

    assert f"{resumen.loc['T50', 'salto']:.2f}" in texto
    assert "%" in texto
    assert "cache" in texto.lower()

    solo_presiones = TH.caption_deriva_vida(resumen, PRESIONES)
    assert "T50" not in solo_presiones, "el caption acotado no debe citar otros canales"
    assert "cache" in solo_presiones.lower()
