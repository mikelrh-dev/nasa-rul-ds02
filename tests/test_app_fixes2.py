"""RED→GREEN de app-fixes-2 (2026-11-06-app-fixes-2).

F1 muro dedupe 3→4→3, F2 preset/correction full rerun sin quitar fragment,
F3 R9 evaluada en Motor, F4 fmt_miles punto. strict_tdd: true.
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

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing",
)
DASHBOARD = os.path.join(APP, "dashboard_ds02.py")


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


def _metric_hangar_total(app) -> int:
    for m in app.metric:
        if (m.label or "") == "Unidades en hangar":
            # valor "N / Total"
            return int(str(m.value).split("/")[1].strip())
    pytest.fail("metrica Unidades en hangar no encontrada")


def _banda_text(app) -> str:
    for c in app.caption:
        v = (c.value or "")
        if "Banda en uso" in v:
            return v
    return ""


@needs_cache
def test_incorporar_no_duplica_muro():
    app = _app()
    app.run()
    assert not app.exception
    assert _click(app, "Incorporar unidad")
    assert not app.exception
    altas = app.session_state.get(F.ALTAS_KEY) or {}
    twins = app.session_state.get("twins") or {}
    assert len(altas) == 1 and len(twins) == 1
    # El gemelo sigue en sesion (Gemelos registrados) pero no duplica el muro:
    # total 4 y sin interseccion cache/gemelos.
    total = _metric_hangar_total(app)
    assert total == 4, f"muro tras Incorporar: {total} (esperado 4)"
    assert total == 3 + len(altas)
    matricula = next(iter(altas))
    assert matricula in twins  # sigue registrado, solo filtrado del muro
    assert _click(app, "Quitar", key="alta_quitar_btn")
    assert not app.exception
    assert _metric_hangar_total(app) == 3, "muro tras Reset debe volver a 3"


@needs_cache
def test_preset_muestra_umbrales_y_banda_en_una_pasada():
    # Estructural: callbacks full-scope en _tab_flota (sin quitar fragment).
    src = open(os.path.join(APP, "ui_modulos", "_tab_flota.py"), encoding="utf-8").read()
    assert "on_change" in src, "preset/toggle sin on_change: banda stale en navegador"
    assert 'scope="app"' in src or "scope='app'" in src, "rerun debe ser full-scope"
    assert "@st.fragment" in src, "no se puede quitar el fragment (paginar el muro)"
    app = _app()
    app.run()
    assert not app.exception
    for s in app.selectbox:
        if s.key == "preset":
            s.set_value("Prudente (+5)").run()
            break
    else:
        pytest.fail("selectbox preset no encontrado")
    assert not app.exception
    vals = _th_values(app)
    assert vals.get("th_apto_Prudente (+5)") == 35.0, vals
    assert vals.get("th_aog_Prudente (+5)") == 30.0, vals
    # Toggle on cambia banda en la misma pasada (AppTest puede ya pasar por
    # full-rerun del harness; el RED real es el on_change estructural).
    for t in app.toggle:
        if t.key == "aplicar_reglas":
            t.set_value(True).run()
            break
    assert not app.exception
    assert "R2b" in _banda_text(app), _banda_text(app)


def test_r9_evaluada_visible_en_motor():
    from src.mia import reglas as R

    umb = {"apto": 30.0, "hangar": 25.0}
    assert R.si_R9_HANGAR({"limite_inferior": 35.2, "alertas_datos": [], "umbrales": umb}) is False
    assert R.si_R9_HANGAR({"limite_inferior": 20.0, "alertas_datos": [], "umbrales": umb}) is True
    if not L.cache_available():
        pytest.skip("app/cache missing")
    app = _app()
    app.run()
    assert not app.exception
    texts = [str(c.value or "") for c in app.caption] + [str(m.value or "") for m in app.markdown]
    joined = "\n".join(texts)
    assert "R9 evaluada" in joined, "fila R9 evaluada ausente en Motor"
    assert "evaluada, no dispara" in joined
    # En APTO nunca se puede afirmar "dispara".
    if "APTO" in joined or "APTO" in "\n".join(str(m.label or "") for m in app.metric):
        # comprueba que ninguna linea dice que R9 dispara en APTO
        for line in joined.splitlines():
            if "R9" in line and "dispara" in line.lower():
                assert "no dispara" in line.lower()


def test_fmt_miles():
    assert hasattr(L, "fmt_miles"), "fmt_miles ausente en ui_data_loader"
    assert L.fmt_miles(6196) == "6.196"
    assert "6,196" not in L.fmt_miles(6196)
