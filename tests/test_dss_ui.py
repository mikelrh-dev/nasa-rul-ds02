"""Tests for the DS02 decision-support surface.

Four claims are checked, and each corresponds to a blocker found in the audit of
the original UI plan:

1. the triage thresholds behave (green is reachable, AOG is conservative);
2. the cache holds what the frozen bundle predicts (counts, band invariant);
3. the work order contains only grounded units and carries provenance;
4. no FD001 artifact leaks into a DS02 surface.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

import ui_data_loader as L  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build_ui_cache.py`",
)


# ------------------------------------------------------------------- policy
@pytest.mark.parametrize(
    "lower, expected",
    [
        (35.7, L.AIRWORTHY),
        (30.0, L.AIRWORTHY),
        (29.9, L.PREVENTIVE),
        (25.0, L.PREVENTIVE),
        (24.9, L.AOG),
        (-3.0, L.AOG),
    ],
)
def test_triage_states_follow_the_lower_bound(lower, expected):
    assert L.classify(lower) == expected


def test_airworthy_state_is_reachable_on_this_band():
    """The original plan's `L_inf >= 50` rule could never turn green."""
    assert L.classify(36.0) == L.AIRWORTHY
    assert L.classify(50.0) == L.AIRWORTHY


def test_thresholds_must_be_ordered():
    with pytest.raises(ValueError, match="aog < airworthy"):
        L.classify(30.0, airworthy=25.0, aog=30.0)
    with pytest.raises(ValueError, match="umbral inválido"):
        L.thresholds_from(airworthy=20.0, aog=25.0)


# -------------------------------------------------------------------- cache
@needs_cache
def test_cache_counts_match_the_evaluation_contract():
    windows = L.get_windows()
    counts = windows.groupby("unit").size().to_dict()
    assert len(windows) == 6196
    assert counts == {11: 3293, 14: 760, 15: 2143}


@needs_cache
def test_band_contains_its_point_estimate_and_is_non_negative():
    windows = L.get_windows()
    assert (windows["lower"] <= windows["pred"]).all()
    assert (windows["pred"] <= windows["upper"]).all()
    assert (windows["lower"] >= 0.0).all()
    assert np.isfinite(windows[["y_true", "pred", "lower", "upper"]].to_numpy()).all()


@needs_cache
def test_first_scored_cycle_is_airworthy_for_every_unit():
    windows = L.get_windows()
    for unit in (11, 14, 15):
        cycle = int(windows.loc[windows["unit"] == unit, "cycle"].min())
        snapshot = L.fleet_snapshot(windows, cycle)
        row = snapshot[snapshot["unit"] == unit].iloc[0]
        assert row["state"] == L.AIRWORTHY, (unit, cycle, row["lower"])


@needs_cache
def test_units_are_clamped_not_extrapolated():
    windows = L.get_windows()
    snapshot = L.fleet_snapshot(windows, 76)
    row = snapshot[snapshot["unit"] == 11].iloc[0]
    assert int(row["scored_cycle"]) == 59
    assert bool(row["clamped"]) is True
    row14 = snapshot[snapshot["unit"] == 14].iloc[0]
    assert int(row14["scored_cycle"]) == 76
    assert bool(row14["clamped"]) is False


@needs_cache
def test_engine_without_flight_is_not_given_a_state():
    windows = L.get_windows()
    snapshot = L.fleet_snapshot(windows, 1)
    row = snapshot[snapshot["unit"] == 14].iloc[0]
    assert row["state"] == L.NO_DATA
    assert row["state"] not in (L.AIRWORTHY, L.AOG)


@needs_cache
def test_metrics_are_recomputed_from_the_cache():
    windows = L.get_windows()
    live = L.global_metrics(windows)
    y = windows["y_true"].to_numpy()
    p = windows["pred"].to_numpy()
    assert live["rmse"] == pytest.approx(float(np.sqrt(np.mean((p - y) ** 2))), abs=1e-9)
    assert live["mae"] == pytest.approx(float(np.mean(np.abs(p - y))), abs=1e-9)
    per_unit = L.per_unit_metrics(windows)
    assert live["macro_rmse"] == pytest.approx(float(per_unit["rmse"].mean()), abs=1e-9)
    # The cache scores the shipped bundle: it must reproduce the manifest's record.
    recorded = L.get_manifest()["macro_rmse"]["per_unit_rmse"]
    for unit in (11, 14, 15):
        assert live["macro_rmse"] > 0
        assert per_unit.loc[per_unit["unit"] == unit, "rmse"].iloc[0] == pytest.approx(
            recorded[str(float(unit))], abs=5e-3
        )


@needs_cache
def test_mae_by_band_covers_every_row_once():
    windows = L.get_windows()
    bands = L.mae_by_band(windows)
    assert bands["windows"].sum() == len(windows)
    # A band with no rows is allowed to have no MAE; a populated band is not.
    populated = bands[bands["windows"] > 0]
    assert not populated.empty
    assert populated["mae"].notna().all()
    assert (populated["mae"] >= 0).all()


@needs_cache
def test_channels_use_the_dataset_names():
    rows = L.get_rows()
    for name in ("T24", "T30", "T48", "T50", "P15", "P2", "P21", "P24",
                 "Ps30", "P40", "P50", "Nf", "Nc", "Wf", "alt", "Mach", "TRA", "T2"):
        assert name in rows.columns, name
    assert not any(col.startswith("s") and col[1:].isdigit() for col in rows.columns)


# --------------------------------------------------------------- work order
@needs_cache
def test_work_order_lists_only_grounded_units():
    windows = L.get_windows()
    provenance = L.get_provenance()
    snapshot = L.fleet_snapshot(windows, 40)
    order = L.work_order(snapshot, provenance)
    blocked = set(snapshot.loc[snapshot["state"] == L.AOG, "unit"].astype(int))
    assert blocked, "the fixture cycle should ground at least one unit"
    assert {entry["unidad"] for entry in order["unidades"]} == blocked
    for entry in order["unidades"]:
        assert entry["motivo"]
        assert entry["limite_inferior"] < 25.0


@needs_cache
def test_work_order_carries_provenance():
    windows = L.get_windows()
    provenance = L.get_provenance()
    order = L.work_order(L.fleet_snapshot(windows, 40), provenance, airworthy=32.0, aog=26.0)
    assert order["artefacto_sha256"] == provenance["artifact"]["ensemble_sha256"]
    assert order["umbrales"] == {
        "apto_si_limite_inferior_ge": 32.0,
        "hangar_si_limite_inferior_lt": 26.0,
    }
    assert json.dumps(order)  # serialisable


@needs_cache
def test_empty_work_order_is_still_a_valid_document():
    windows = L.get_windows()
    provenance = L.get_provenance()
    order = L.work_order(L.fleet_snapshot(windows, 1), provenance)
    assert order["unidades"] == []
    csv_text = L.work_order_csv(order)
    assert csv_text.strip().splitlines() == [
        "unidad,estado,ciclo_simulado,ciclo_evaluado,rul_estimada,limite_inferior,"
        "limite_superior,rul_real,motivo,accion"
    ]


# --------------------------------------------------------- dataset isolation
def _ui_sources() -> list[str]:
    sources = []
    for name in ("dashboard_ds02.py", "ui_data_loader.py"):
        with open(os.path.join(APP, name), encoding="utf-8") as fh:
            sources.append(fh.read())
    return sources


def test_no_fd001_artifact_is_referenced():
    joined = "\n".join(_ui_sources())
    assert "alarm_policy" not in joined
    assert "test_eval_ultima_ventana" not in joined


def test_ui_does_not_reimplement_the_model():
    joined = "\n".join(_ui_sources())
    for forbidden in ("tensorflow", "import keras", "joblib.load", "train_", "fit("):
        assert forbidden not in joined, forbidden


@needs_cache
def test_reading_the_ui_leaves_the_frozen_artifacts_untouched():
    """`models/` is read-only: hashes before and after a full UI data pass."""
    import hashlib

    watched = [
        os.path.join(ROOT, "models", name)
        for name in ("ensemble.joblib", "bilstm_ds02.keras", "scaler.joblib",
                     "ds02_manifest.json")
    ]

    def digest(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    before = {path: digest(path) for path in watched}
    windows = L.get_windows()
    snapshot = L.fleet_snapshot(windows, 40)
    L.work_order(snapshot, L.get_provenance())
    L.get_manifest()
    after = {path: digest(path) for path in watched}
    assert before == after
    assert os.path.exists(L.MANIFEST_PATH) and L.MANIFEST_PATH.endswith("ds02_manifest.json")


# ------------------------------------------------------------------- render
@needs_cache
def test_app_renders_headless_without_exception():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=120)
    app.run()
    assert not app.exception, app.exception
    assert "DS02" in app.title[0].value
    assert len(app.tabs) == 5
    labels = [tab.label for tab in app.tabs]
    assert any("Hangar" in label for label in labels)
    assert any("Motor 14" in label for label in labels)
    assert any("Evaluar" in label for label in labels)


@needs_cache
def test_every_chart_and_grid_has_an_accessible_name():
    """`alt=` is the accessible name: no chart or grid may ship without one."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=120)
    app.run()
    assert not app.exception, app.exception
    charts = app.get("plotly_chart")
    grids = app.get("dataframe")
    assert len(charts) >= 6, f"lost a chart: {len(charts)}"
    assert len(grids) >= 7, f"lost a grid: {len(grids)}"
    for element in list(charts) + list(grids):
        assert element.proto.alt and element.proto.alt.strip(), element.proto


def test_theme_config_is_dark_and_parseable():
    """The polished look lives in config.toml, not in injected CSS."""
    import tomllib

    path = os.path.join(ROOT, ".streamlit", "config.toml")
    with open(path, "rb") as fh:
        config = tomllib.load(fh)
    theme = config["theme"]
    assert theme["base"] == "dark"
    assert theme["backgroundColor"].startswith("#")
    assert theme["textColor"].startswith("#")
    assert len(theme["chartSequentialColors"]) == 10
    assert len(theme["chartDivergingColors"]) == 10
    assert "font" in theme and "headingFont" in theme
    assert config["theme"]["sidebar"]["backgroundColor"] != theme["backgroundColor"]


def test_no_css_is_injected_into_the_app():
    joined = "\n".join(_ui_sources())
    assert "unsafe_allow_html" not in joined
    assert "<style" not in joined


@needs_cache
def test_the_cycle_slider_drives_the_grounded_kpi():
    """The simulator is interactive: moving the clock changes the fleet state."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=120)
    app.run()
    app.slider[0].set_value(40).run()
    assert not app.exception, app.exception

    expected = int((L.fleet_snapshot(L.get_windows(), 40)["state"] == L.AOG).sum())
    assert expected > 0, "cycle 40 should ground at least one unit"
    kpi = next(m for m in app.metric if "hangar" in m.label.lower())
    assert kpi.value.startswith(f"{expected} /")

    downloads = [
        widget for widget in app.get("download_button")
        if "orden" in widget.proto.label.lower()
    ]
    assert len(downloads) == 2, "a grounded fleet must offer the work order (JSON + CSV)"
    for widget in downloads:
        assert widget.proto.disabled is False
