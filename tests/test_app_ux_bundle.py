"""Tests del bundle UX (change app-ux-bundle-fix).

Run:  python -m pytest tests/test_app_ux_bundle.py -q
"""
from __future__ import annotations

import csv
import io
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, ROOT)
sys.path.insert(0, APP)


# ---------------------------------------------------------- URL guard
def test_no_app_terminal_under_app():
    hits = []
    for dirpath, _dirs, files in os.walk(APP):
        for f in files:
            if f.endswith((".py", ".toml", ".md", ".txt")):
                p = os.path.join(dirpath, f)
                with open(p, encoding="utf-8", errors="replace") as fh:
                    if "/app/terminal" in fh.read():
                        hits.append(p)
    assert hits == []


# ---------------------------------------------------------- presets
def test_presets_conservador_agresivo_ordered():
    import re
    src = open(os.path.join(APP, "dashboard_ds02.py"), encoding="utf-8").read()
    m = re.search(r"_PRESETS\s*=\s*\{([^}]*)\}", src)
    assert m, "_PRESETS not found"
    block = m.group(1)
    assert "Conservador" in block and "Agresivo" in block
    # deltas ±10 alongside the existing ±5
    assert "(10.0, 10.0)" in block and "(-10.0, -10.0)" in block
    base_a, base_h = 30.0, 25.0
    for d_a, d_h in [(10.0, 10.0), (-10.0, -10.0), (5.0, 5.0), (-5.0, -5.0), (0.0, 0.0)]:
        assert max(0.0, base_h + d_h) < base_a + d_a


# ---------------------------------------------------------- helpers puros
def test_contrast_csv_columns():
    from dashboard_helpers import contraste_csv  # imported below; defined in app
    raw = pd.DataFrame({"unit": [14, 14], "cycle": [25, 26],
                        "lower": [24.0, 23.0]})
    corr = pd.DataFrame({"unit": [14, 14], "cycle": [25, 26],
                         "lower": [22.0, 21.0], "decision": ["HANGAR", "HANGAR"]})
    out = contraste_csv(raw, corr)
    rows = list(csv.DictReader(io.StringIO(out)))
    assert rows and set(rows[0]) >= {"unit", "cycle", "lower_raw", "lower_corregida", "decision"}
    assert float(rows[0]["lower_raw"]) == 24.0
    assert float(rows[0]["lower_corregida"]) == 22.0


def test_queue_filter_helper():
    from dashboard_helpers import cola_filtrada
    registros = {
        "a": {"unidad": "U14", "estado": "AOG_DERIVADO", "entrada": {"lower": 20.0}},
        "b": {"unidad": "U11", "estado": "EN_TALLER", "entrada": {"lower": 21.0}},
        "c": {"unidad": "U15", "estado": "EN_SERVICIO", "entrada": {"lower": 35.0}},
    }
    assert len(cola_filtrada(registros, {"AOG_DERIVADO"})) == 1
    assert cola_filtrada(registros, {"AOG_DERIVADO"})[0]["unidad"] == "U14"
    assert len(cola_filtrada(registros, {"AOG_DERIVADO", "EN_TALLER"})) == 2
    assert cola_filtrada(registros, set()) == []


def test_trajectory_csv_parse():
    from dashboard_helpers import trayectoria_csv
    curva = pd.DataFrame({"cycle": [1, 2, 3], "pred": [30.0, 28.0, 26.0],
                          "lower": [27.0, 25.0, 23.0], "upper": [33.0, 31.0, 29.0],
                          "decision": ["APTO", "INSPECCION", "HANGAR"]})
    out = trayectoria_csv(curva)
    rows = list(csv.DictReader(io.StringIO(out)))
    assert len(rows) == 3
    assert rows[0]["cycle"] == "1" and rows[-1]["decision"] == "HANGAR"


def test_six_decision_rules():
    from src.mia.reglas import REGLAS_DECISION
    from dashboard_helpers import reglas_decision_vista
    vista = reglas_decision_vista()
    assert len(REGLAS_DECISION) == 6
    assert len(vista) == 6
    assert {r["regla"] for r in vista} == {r[0] for r in REGLAS_DECISION}


def test_sandbox_helper_includes_sensor():
    src = open(os.path.join(APP, "dashboard_ds02.py"), encoding="utf-8").read()
    assert "sensor" in src
    # the cached helper signature carries the sensor so the key changes with it
    assert "sensor" in src.split("def _sandbox_puntua_cached")[1].split(")")[0]


def test_n8n_panel_button_via_helper():
    src = open(os.path.join(APP, "dashboard_ds02.py"), encoding="utf-8").read()
    assert src.count("enviar_decision(") == 1
    assert "DH.probar_n8n()" in src


# ---------------------------------------------------------- AppTest
pytestmark = pytest.mark.skipif(
    pytest.importorskip("streamlit", reason="streamlit not installed") is None,
    reason="streamlit not installed",
)


def test_app_renders_n8n_panel_without_env(monkeypatch):
    from streamlit.testing.v1 import AppTest
    monkeypatch.delenv("N8N_WEBHOOK_URL", raising=False)
    dash = os.path.join(APP, "dashboard_ds02.py")
    app = AppTest.from_file(dash, default_timeout=180).run()
    assert not app.exception, app.exception
    texts = " ".join(getattr(e, "value", "") or "" for e in app.caption) \
        + " " + " ".join(getattr(e, "value", "") or "" for e in app.markdown)
    assert "n8n" in texts.lower()
