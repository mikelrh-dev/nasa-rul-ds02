"""RED tests for the mejoras-streamlit change (P0+P1+P2)."""
import ast
import os
import re
import sys

APP = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
DASH = os.path.join(APP, "dashboard_ds02.py")


def read_dash() -> str:
    return open(DASH, encoding="utf-8").read()


def test_hash_cached_with_cache_data():
    src = read_dash()
    assert "@st.cache_data" in src
    assert "_sha256_cached" in src
    # PR1/PR2 (dashboard-split-monolito): dueño único `ui_data_loader`
    # (re-export en `ui_modulos`); el dashboard ya no define
    # `def _sha256_cached`, lo re-exporta para compat.
    owners = ""
    for fn in ("ui_data_loader.py", os.path.join("ui_modulos", "__init__.py")):
        path = os.path.join(APP, fn)
        if os.path.exists(path):
            owners += open(path, encoding="utf-8").read()
    assert "def _sha256_cached" in owners


def test_pdf_cached_with_cache_data():
    src = read_dash()
    assert "_informe_pdf_cached" in src
    # decorator precedes the def
    assert re.search(r"@st\.cache_data[\s\S]*?def _informe_pdf_cached", src)


def test_tabs_fragmented():
    src = read_dash()
    # PR2 (dashboard-split-monolito): `_sandbox_estres` vive en
    # `ui_modulos/_sandbox_estres.py`; el conteo incluye los módulos
    # extraídos, no solo el dashboard.
    blob = src
    mod_dir = os.path.join(APP, "ui_modulos")
    if os.path.isdir(mod_dir):
        for fn in os.listdir(mod_dir):
            if fn.endswith(".py"):
                blob += open(os.path.join(mod_dir, fn), encoding="utf-8").read()
    assert blob.count("@st.fragment") >= 6, blob.count("@st.fragment")
    # each tab has a fragment-defined function
    for name in ("_tab_flota", "_tab_motor", "_tab_auditoria", "_tab_casos"):
        assert f"def {name}" in src, name


def test_single_shap_panel():
    src = read_dash()
    assert src.count("def shap_panel") == 1
    assert "shap_panel(" in src


def test_no_tmp_waterfall_path():
    blob = ""
    for fn in ("dashboard_ds02.py", "ui_shap.py"):
        blob += open(os.path.join(APP, fn), encoding="utf-8").read()
    assert "/tmp/shap_waterfall.png" not in blob
    assert "tempfile" in blob


def test_shap_waterfall_png_uses_tempfile():
    sys.path.insert(0, APP)
    import inspect
    import ui_shap

    sig = inspect.signature(ui_shap.shap_waterfall_png)
    # default must not be the fixed /tmp path
    assert sig.parameters["out_path"].default in (None, ""), sig.parameters["out_path"].default
    assert hasattr(ui_shap, "shap_waterfall_fig")


def test_every_slider_multiselect_selectbox_has_help():
    src = read_dash()
    lines = src.splitlines()
    bad = []
    for i, line in enumerate(lines, 1):
        if "st.slider(" in line or "st.multiselect(" in line or "st.selectbox(" in line:
            block = "\n".join(lines[i - 1 : i + 14])
            if "help=" not in block[:1500]:
                bad.append((i, line.strip()))
    assert not bad, bad


def test_score_table_has_timeout():
    sys.path.insert(0, APP)
    import inspect

    import ui_inference as INF

    assert "timeout_s" in inspect.signature(INF.score_table).parameters


def test_dashboard_friendly_shap_message():
    src = read_dash()
    assert "pip install" in src.lower()
    assert "ImportError" in src


def test_banner_aligned_no_pruebahangar():
    src = read_dash()
    # the old separate caption must be gone
    assert "Además, **" not in src
    # banner now counts wall cards: numerator includes twins
    assert "hangar_en_muro" in src or "len(tarjetas" in src
    reg = os.path.join(APP, "registros_flota.json")
    if os.path.exists(reg):
        assert "PRUEBAHANGAR" not in open(reg, encoding="utf-8").read()


def test_pdf_generated_on_demand():
    src = read_dash()
    # PR5 (dashboard-split-monolito): el informe vive en
    # `ui_modulos/_tab_auditoria.py`; la búsqueda incluye los módulos
    # extraídos, no solo el dashboard.
    blob = src
    mod_dir = os.path.join(APP, "ui_modulos")
    if os.path.isdir(mod_dir):
        for fn in os.listdir(mod_dir):
            if fn.endswith(".py"):
                blob += open(os.path.join(mod_dir, fn), encoding="utf-8").read()
    # generate button pattern: PDF builder only invoked behind a flag/button
    assert "_pdf_generado" in blob or "btn_gen_pdf" in blob or "Generar informe" in blob
    # the unconditional call pattern `except Exception as exc:  # pragma: no cover` block
    # that built PDF on every render must be replaced
    assert "btn_gen_pdf" in blob
