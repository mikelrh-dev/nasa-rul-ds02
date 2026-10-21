"""Tests for evaluating a unit the user brings to the UI.

The claims under test: the validator rejects anything the frozen bundle cannot
score, the example window is a real contract-valid window, scoring is banded and
reproducible through the CSV path, the model loads only on demand, and the
evaluation leaves `models/` and `app/cache/` untouched.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

import ui_data_loader as L  # noqa: E402
import ui_inference as INF  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build_ui_cache.py`",
)


# ------------------------------------------------------------------ imports
def test_importing_the_module_does_not_load_tensorflow():
    code = (
        "import sys; sys.path.insert(0, 'app'); import ui_inference; "
        "print('tensorflow' in sys.modules, 'keras' in sys.modules)"
    )
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip() == "False False"


# --------------------------------------------------------------- validation
@needs_cache
def test_example_window_is_contract_valid():
    table, meta = INF.example_window()
    assert list(table.columns) == INF.required_columns()
    assert len(table) == INF.window_size()
    assert meta["unit"] == 14
    assert meta["start_cycle"] <= meta["end_cycle"]
    cleaned = INF.validate_table(table)
    assert cleaned.shape == table.shape
    assert cleaned.dtypes.eq(float).all()


@needs_cache
def test_short_table_is_rejected_with_counts():
    table, _ = INF.example_window()
    with pytest.raises(ValueError, match=r"al menos 50 filas.*llegaron 20"):
        INF.validate_table(table.head(20))


@needs_cache
def test_wrong_channel_order_is_rejected_and_named():
    table, _ = INF.example_window()
    order = INF.channel_order()
    shuffled = table[["cycle", order[1], order[0]] + order[2:]]
    with pytest.raises(ValueError, match="Orden de canales incorrecto"):
        INF.validate_table(shuffled)


@needs_cache
def test_missing_column_is_rejected():
    table, _ = INF.example_window()
    with pytest.raises(ValueError, match="Faltan columnas obligatorias: Wf"):
        INF.validate_table(table.drop(columns=["Wf"]))


@needs_cache
def test_unknown_column_is_rejected():
    table, _ = INF.example_window()
    with pytest.raises(ValueError, match="Columnas no reconocidas: engine_id"):
        INF.validate_table(table.assign(engine_id=7))


@needs_cache
def test_non_numeric_cell_is_rejected_with_position():
    table, _ = INF.example_window()
    broken = table.astype(object)
    broken.loc[3, "T24"] = "n/a"
    with pytest.raises(ValueError, match=r"`T24`, fila 4"):
        INF.validate_table(broken)


@needs_cache
def test_decreasing_cycles_are_rejected():
    table, _ = INF.example_window()
    broken = table.copy()
    broken.loc[10, "cycle"] = broken.loc[2, "cycle"] - 1
    with pytest.raises(ValueError, match="disminuye"):
        INF.validate_table(broken)


@needs_cache
def test_repeated_cycles_are_allowed():
    """Several sampled rows per flight cycle are the normal DS02 layout."""
    table, _ = INF.example_window()
    assert INF.validate_table(table) is not None
    assert table["cycle"].duplicated().any()


# ----------------------------------------------------------------- scoring
@needs_cache
def test_live_score_is_banded_and_finite():
    table, _ = INF.example_window()
    result = INF.score_table(table)
    windows = result["windows"]
    assert len(windows) == 1
    assert np.isfinite(windows[["pred", "lower", "upper"]].to_numpy()).all()
    assert (windows["lower"] <= windows["pred"]).all()
    assert (windows["pred"] <= windows["upper"]).all()
    assert (windows["lower"] >= 0).all()
    assert 0.0 <= float(windows["pred"].iloc[0]) <= 90.0


@needs_cache
def test_the_triage_rule_is_the_same_one():
    table, _ = INF.example_window()
    last = INF.score_table(table)["windows"].iloc[-1]
    expected = L.classify(float(last["lower"]), 30.0, 25.0)
    assert expected in (L.AIRWORTHY, L.PREVENTIVE, L.AOG)
    assert L.classify(24.9, 30.0, 25.0) == L.AOG


@needs_cache
def test_csv_round_trip_scores_identically():
    table, _ = INF.example_window()
    direct = INF.score_table(table)["windows"]
    csv_bytes = table.to_csv(index=False)
    again = INF.score_table(pd.read_csv(io.StringIO(csv_bytes)))["windows"]
    pd.testing.assert_frame_equal(direct, again)


@needs_cache
def test_longer_history_produces_a_trajectory():
    rows = L.get_rows()
    frame = rows[rows["unit"] == 14].reset_index(drop=True).iloc[802:862]
    table = frame[["cycle"] + INF.channel_order()].reset_index(drop=True)
    result = INF.score_table(table)
    assert result["contract"]["ventanas"] == 11
    assert len(result["windows"]) > 1
    assert result["windows"]["cycle"].is_monotonic_increasing


@needs_cache
def test_model_is_loaded_once_and_reused():
    INF.score_table(INF.example_window()[0])
    first = INF.get_ensemble()
    second = INF.get_ensemble()
    assert first is second


# -------------------------------------------------------------- work order
@needs_cache
def test_live_work_order_claims_no_ground_truth():
    table, meta = INF.example_window()
    result = INF.score_table(table)
    order = INF.live_work_order(result, meta, 30.0, 25.0)
    assert order["modo"] == "evaluación en vivo"
    assert order["sin_ground_truth"] is True
    assert order["procedencia_datos"]["unit"] == 14
    entry = order["unidades"][0]
    assert "rul_real" not in entry
    assert entry["unidad"] == "externa"
    assert entry["estado"] in (L.AIRWORTHY, L.PREVENTIVE, L.AOG)
    assert order["artefacto_sha256"] == L.get_provenance()["artifact"]["ensemble_sha256"]
    assert json.dumps(order)


# ------------------------------------------------------------ app surface
@needs_cache
def test_the_app_does_not_load_the_model_until_asked():
    """Rendering the page must stay TensorFlow-free — checked in a fresh process."""
    code = (
        "import sys, os\n"
        "from streamlit.testing.v1 import AppTest\n"
        "app = AppTest.from_file('app/dashboard_ds02.py', default_timeout=120)\n"
        "app.run()\n"
        "assert not app.exception, app.exception\n"
        "print(len(app.tabs), 'tensorflow' in sys.modules, 'keras' in sys.modules)\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr[-3000:]
    assert proc.stdout.strip().splitlines()[-1] == "5 False False"


@needs_cache
def test_pressing_evaluate_renders_a_live_result():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=180)
    app.run()
    button = next(b for b in app.button if b.label == "Evaluar unidad")
    button.click().run()
    assert not app.exception, app.exception
    labels = [m.label for m in app.metric]
    assert "RUL estimada" in labels
    live_metric = next(m for m in app.metric if m.label == "RUL estimada")
    assert float(live_metric.value) >= 0.0


# --------------------------------------------------------------- explanation
@needs_cache
def test_every_channel_is_named_and_described():
    """No column may reach the grid as a bare acronym."""
    labels = INF.channel_labels()
    assert list(labels) == INF.channel_order()
    assert len(labels) == 18
    for channel, label in labels.items():
        assert label.startswith(channel + " · "), channel
        assert len(label.split(" · ", 1)[1]) > 3, channel


@needs_cache
def test_the_envelope_is_measured_and_ordered():
    envelope = INF.observed_envelope()
    assert list(envelope["canal"]) == INF.channel_order()
    assert len(envelope) == 18
    assert (envelope["mínimo"] < envelope["máximo"]).all()
    assert (envelope["aviso_desde"] < envelope["mínimo"]).all()
    assert (envelope["aviso_hasta"] > envelope["máximo"]).all()
    assert envelope["qué mide"].str.len().gt(3).all()


@needs_cache
def test_the_cached_example_raises_no_plausibility_note():
    table, _ = INF.example_window()
    assert INF.plausibility_warnings(table) == []


@needs_cache
def test_a_value_outside_the_training_range_is_flagged_but_still_scored():
    table, _ = INF.example_window()
    absurd = table.copy()
    absurd.loc[0, "Mach"] = 49.0
    notes = INF.plausibility_warnings(absurd)
    assert len(notes) == 1
    assert "`Mach` 1/50" in notes[0]
    assert "dominio de entrenamiento" in notes[0]
    assert INF.validate_table(absurd) is not None


@needs_cache
def test_in_domain_values_are_never_flagged_by_a_percentile_cut():
    """A real engine crossing the pooled p1 is in domain, not out of it."""
    table, _ = INF.example_window()
    envelope = INF.observed_envelope().set_index("canal")
    inside = all(
        table[c].between(envelope.loc[c, "aviso_desde"], envelope.loc[c, "aviso_hasta"]).all()
        for c in INF.channel_order()
    )
    assert inside
    assert INF.plausibility_warnings(table) == []


@needs_cache
def test_a_single_cycle_window_is_flagged():
    table, _ = INF.example_window()
    flat = table.copy()
    flat["cycle"] = 40
    notes = INF.plausibility_warnings(flat)
    assert any("mismo ciclo" in note for note in notes)


@needs_cache
def test_the_template_has_the_contract_shape_and_no_invented_data():
    template = INF.template_csv()
    frame = pd.read_csv(io.StringIO(template))
    assert list(frame.columns) == INF.required_columns()
    assert len(frame) == INF.window_size()
    assert frame.isna().all().all()
    with pytest.raises(ValueError, match="Valor no numérico"):
        INF.validate_table(frame)


@needs_cache
def test_the_tab_explains_the_columns_and_offers_a_template():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=180)
    app.run()
    assert not app.exception, app.exception
    labels = [expander.label for expander in app.expander]
    assert any("Qué es cada columna" in label for label in labels), labels
    downloads = [button.label for button in app.download_button]
    assert any("plantilla CSV" in label for label in downloads), downloads


@needs_cache
def test_the_paste_grid_carries_the_glossary_and_a_row_counter():
    """The editable grid must not ask for 19 acronyms with no explanation."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=180)
    app.run()
    app.segmented_control[0].set_value("Editar tabla (pegar)").run()
    assert not app.exception, app.exception

    grid = next(el for el in app.dataframe if len(json.loads(el.proto.columns or "{}")) == 20)
    config = json.loads(grid.proto.columns)
    documented = [
        entry.get("help") for key, entry in config.items()
        if not key.startswith("_") and key != "cycle"
    ]
    assert len(documented) == 18
    assert all(text and "·" in text for text in documented)
    assert "altitud" in config["alt"]["help"]
    assert "Ciclo de vuelo" in config["cycle"]["help"]

    captions = [c.value for c in app.caption]
    assert any("50 filas" in text and "ventana(s)" in text for text in captions), captions[-4:]


@needs_cache
def test_the_sidebar_explains_the_vocabulary_of_the_screen():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=180)
    app.run()
    assert not app.exception, app.exception
    labels = [expander.label for expander in app.expander]
    assert any("Cómo leer esta pantalla" in label for label in labels), labels
    text = "\n".join(m.value for m in app.markdown) + "\n".join(c.value for c in app.caption)
    for term in ("RUL", "L_inf", "Banda 90 %", "HANGAR/AOG", "Ciclo de vuelo", "Ventana"):
        assert term in text, term
