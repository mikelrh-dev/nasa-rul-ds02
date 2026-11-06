"""RED→GREEN de app-fixes-1 (2026-11-06-app-fixes-1).

SHAPC-WF-01, muro 3→5→3, preset 30/25 e historia. Cada test nombra
el artefacto que no corre antes del arreglo (strict_tdd: true).
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

import flota as F  # noqa: E402
import ui_data_loader as L  # noqa: E402
import ui_shap as USH  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing",
)
DASHBOARD = os.path.join(APP, "dashboard_ds02.py")


def test_waterfall_builds_with_data(monkeypatch):
    import numpy as np

    sv = np.array([2.0, -1.0, 0.5, 0.2])
    values = np.zeros(4)
    names = ["a", "b", "c", "d"]
    monkeypatch.setattr(
        USH, "shap_waterfall_data",
        lambda unit, *a, **k: (sv, values, 10.0, names),
    )
    # st.cache_data sobre el cuerpo cacheado: limpia la clave para que
    # el mock entre (si no, sirve el valor anterior cacheado).
    try:
        USH._shap_waterfall_fig_cached.clear()
    except Exception:
        pass
    fig = USH.shap_waterfall_fig(11, max_display=4, solver_sha="s", rows_sha="r")
    assert fig is not None
    assert len(fig.data) == 1
    assert len(fig.data[0].x) > 0
    assert len(fig.data[0].y) > 0


def _wall(reg: dict) -> int:
    # tarjetas_cache (3 base + altas) + tarjetas_gemelos sin duplicar altas:
    # el gemelo cuya matricula esta en _altas() ya esta en la cache via frame.
    altas = set((reg.get(F.ALTAS_KEY) or {}).keys())
    twins = set((reg.get("twins") or {}).keys())
    return 3 + len(altas) + len(twins - altas)


def test_quitar_alta_removes_twin_and_hangar():
    registro = {
        F.ALTAS_KEY: {"EC-MKR": {"unit_id": -1000.0, "indice": 0}},
        "twins": {"EC-MKR": {"id": "EC-MKR"}},
        "hangar": {"EC-MKR": {"unidad": "EC-MKR"}},
    }
    assert _wall(registro) == 4
    nuevo = F.quitar_alta(registro, "EC-MKR")
    assert "EC-MKR" not in (nuevo.get(F.ALTAS_KEY) or {})
    assert "EC-MKR" not in (nuevo.get("twins") or {})
    assert "EC-MKR" not in (nuevo.get("hangar") or {})
    assert _wall(nuevo) == 3


def _app():
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(DASHBOARD, default_timeout=180)


def _click(app, needle: str, key: str | None = None) -> bool:
    for b in app.button:
        if key is not None and getattr(b, "key", None) == key:
            b.click().run()
            return True
        if needle and needle.lower() in (b.proto.label or "").lower():
            b.click().run()
            return True
    return False


def _th_values(app):
    vals = {}
    for n in app.number_input:
        if (n.key or "").startswith("th_"):
            vals[n.key] = float(n.value)
    return vals


def _set_preset(app, value: str):
    for s in app.selectbox:
        if s.key == "preset":
            s.set_value(value).run()
            return
    pytest.fail("selectbox preset no encontrado")


@needs_cache
def test_incorporar_y_reset_muro_3_4_3():
    app = _app()
    app.run()
    assert not app.exception
    assert _click(app, "Incorporar unidad")
    assert not app.exception
    altas = app.session_state.get(F.ALTAS_KEY) or {}
    twins = app.session_state.get("twins") or {}
    assert len(altas) == 1, altas
    assert len(twins) == 1, list(twins)
    assert _wall({"altas": altas, "twins": twins}) == 4
    matricula = next(iter(altas))
    assert _click(app, "Quitar", key="alta_quitar_btn")
    assert not app.exception
    altas2 = app.session_state.get(F.ALTAS_KEY) or {}
    twins2 = app.session_state.get("twins") or {}
    hangar2 = app.session_state.get("hangar") or {}
    assert matricula not in altas2
    assert matricula not in twins2, "Reset deja el gemelo: muro 4->3, no 3"
    assert matricula not in hangar2
    assert _wall({"altas": altas2, "twins": twins2}) == 3


@needs_cache
def test_preset_historia_restores_normal():
    app = _app()
    app.run()
    assert not app.exception
    assert _th_values(app).get("th_apto_Normal") == 30.0
    assert _th_values(app).get("th_aog_Normal") == 25.0
    # Historia paso 4: blandos 35/20 en la clave vigente (Normal).
    assert _click(app, "", key="historia_4")
    assert not app.exception
    assert _th_values(app).get("th_apto_Normal") == 35.0
    assert _th_values(app).get("th_aog_Normal") == 20.0
    # Volver al paso 1 debe restaurar la base del preset, no la contaminada.
    assert _click(app, "", key="historia_1")
    assert not app.exception
    assert _th_values(app).get("th_apto_Normal") == 30.0, _th_values(app)
    assert _th_values(app).get("th_aog_Normal") == 25.0, _th_values(app)
    # Ciclo de presets: Prudente 35/30, Normal 30/25.
    _set_preset(app, "Prudente (+5)")
    assert not app.exception
    vals = _th_values(app)
    assert vals.get("th_apto_Prudente (+5)") == 35.0, vals
    assert vals.get("th_aog_Prudente (+5)") == 30.0, vals
    _set_preset(app, "Normal")
    assert not app.exception
    assert _th_values(app).get("th_apto_Normal") == 30.0
    assert _th_values(app).get("th_aog_Normal") == 25.0
