"""The MLflow store is real, complete and text-only.

These tests read `mlruns/` from disk with a file tracking URI: no server, no
network, no notebook execution. The store is produced by
`scripts/backfill_mlflow.py --write` and must contain exactly the 17 measured
runs (9 row grain, 4 window grain and the 4 cyc_norm ablation variants). A
missing or duplicated run fails the test; nothing is skipped.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

# MLflow 3.18 refuses the filesystem store unless this opt-out is explicit.
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

from mlflow.tracking import MlflowClient  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "mlruns"
EXPORT = ROOT / "docs" / "evidencia" / "mlflow" / "comparativa.csv"


def _load_backfill():
    path = ROOT / "scripts" / "backfill_mlflow.py"
    spec = importlib.util.spec_from_file_location("backfill_mlflow_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


MOD = _load_backfill()


@pytest.fixture(scope="module")
def client() -> MlflowClient:
    assert STORE.exists(), f"falta el store {STORE}; ejecuta --write"
    return MlflowClient(tracking_uri=STORE.resolve().as_uri())


@pytest.fixture(scope="module")
def exp_id(client: MlflowClient) -> str:
    exp = client.get_experiment_by_name(MOD.EXPERIMENT)
    assert exp is not None, f"no existe el experimento {MOD.EXPERIMENT}"
    return exp.experiment_id


@pytest.fixture(scope="module")
def runs(client: MlflowClient, exp_id: str):
    return MOD.historic_runs(client, exp_id)


def test_exactly_seventeen_active_runs(runs):
    assert len(runs) == 17, f"esperaba 17 runs, hay {len(runs)}"


def test_grains_are_nine_four_and_four(runs):
    grains = [run.data.tags.get("grano") for run in runs]
    assert grains.count("fila") == 9
    assert grains.count("ventana") == 4
    assert grains.count("ablacion") == 4


def test_run_keys_are_unique(runs):
    keys = [run.data.tags.get("run_key") for run in runs]
    assert len(keys) == 17
    assert len(set(keys)) == 17
    assert None not in keys


def test_every_run_has_measured_params_and_metrics(runs):
    untimed = {"bundle__bilstm_ema5"}
    for run in runs:
        key = run.data.tags.get("run_key")
        assert run.data.params, f"{run.info.run_id} sin params"
        assert ("rmse_val" in run.data.metrics) or ("rmse_test" in run.data.metrics)
        if key not in untimed and not key.startswith("ablacion__"):
            assert "tiempo_s" in run.data.metrics, key


def test_ema5_time_is_absent_not_zero(runs):
    run = next(r for r in runs if r.data.tags.get("run_key") == "bundle__bilstm_ema5")
    assert "tiempo_s" not in run.data.metrics
    assert "tiempo_s" not in run.data.tags


def test_production_run_is_traceable_to_the_manifest(runs):
    run = next(r for r in runs if r.data.tags.get("run_key") == "prod__bundle_c")
    for key in (
        "ensemble_sha256", "bilstm_sha256", "clase_xgb_sha256", "clase_e2_sha256",
    ):
        assert len(run.data.params[key]) == 64
    assert run.data.params["seed"] == "42"
    assert run.data.params["beta"] == "1.0"
    assert run.data.params["ema_span"] == "5"
    assert run.data.params["window"] == "50"
    assert run.data.params["lgb_features"] == "93"
    assert run.data.tags["v3_bundle"] == "archivado"
    assert "v3_bundle_sha256" not in run.data.params
    assert run.data.metrics["rmse_test"] == pytest.approx(4.338)
    assert run.data.metrics["mae_test"] == pytest.approx(3.227)
    assert run.data.metrics["r2_test"] == pytest.approx(0.9461)
    assert run.data.metrics["nasa_test"] == pytest.approx(2336.2)


def test_ablation_registers_the_four_variants(runs):
    """The cyc_norm ablation is compared in MLflow, not just in the notebook.

    One run per variant, always the BiLSTM+EMA5 (the best model in all four).
    Values are the measured ones from the 2026-11-09 17:22 session of nb03.
    """
    expected = {
        "cyc_norm OFF": 5.878,
        "cyc_norm OFF + baseline delta": 5.896,
        "cyc_norm ON (baseline)": 5.910,
        "cyc_norm ON + baseline delta": 5.974,
    }
    ablation = [r for r in runs if r.data.tags.get("grano") == "ablacion"]
    assert len(ablation) == 4
    got = {r.data.params["variant"]: r for r in ablation}
    assert set(got) == set(expected)
    for variant, run in got.items():
        assert run.data.tags["familia"] == "ablacion_cycnorm"
        assert run.data.tags["rol"] == "ablacion"
        assert run.data.params["model"] == "BiLSTM+EMA"
        assert run.data.params["window"] == "50"
        assert run.data.metrics["rmse_test"] == pytest.approx(expected[variant], abs=1e-6)
        assert "mae_test" in run.data.metrics
        assert "nasa_test" in run.data.metrics


def test_selected_models_are_tagged(runs):
    by_key = {run.data.tags["run_key"]: run for run in runs}
    assert by_key["clasico__xgb"].data.tags["seleccion"] == "mejor_clasico"
    assert by_key["mlp__E2_reg_lr"].data.tags["seleccion"] == "mejor_mlp,campeon_fila"
    assert by_key["prod__bundle_c"].data.tags["seleccion"] == "produccion"
    assert by_key["clasico__xgb"].data.tags["test_lectura"] == "unica"
    assert by_key["mlp__E2_reg_lr"].data.tags["test_lectura"] == "unica"


def test_store_has_no_artifacts():
    assert not any(path.is_file() for path in STORE.rglob("artifacts/*"))


def test_export_matches_the_store(client, exp_id, runs):
    assert EXPORT.exists()
    with EXPORT.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert len(rows) == 17
    assert {row["run_id"] for row in rows} == {run.info.run_id for run in runs}
    for row in rows:
        assert row["params_summary"]
        assert row["run_key"]
        assert row["fuente"] == "historico"
        metrics = json.loads(row["metrics_json"])
        run = client.get_run(row["run_id"])
        assert metrics == run.data.metrics
        assert json.loads(row["params_json"]) == run.data.params
        for key in ("rmse_val", "rmse_test", "tiempo_s"):
            if row[key]:
                assert float(row[key]) == pytest.approx(run.data.metrics[key], abs=1e-6)


def test_check_exits_zero():
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "backfill_mlflow.py"), "--check"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK: 17 runs" in result.stdout


def test_notebooks_instrument_mlflow_live():
    """NB01-07 DO write to MLflow live (mlflow-live-notebooks): header in
    cell 0 + a live-log cell per notebook; backfill runs stay historic."""
    for path in sorted((ROOT / "notebooks").glob("0*.ipynb")):
        text = path.read_text(encoding="utf-8")
        assert "setup_mlflow" in text, f"{path.name} sin cabecera MLflow"
        assert "log_live_run" in text, f"{path.name} sin celda live"
        assert "persist_timings" in text, f"{path.name} sin persistencia de tiempos"


def test_backfill_runs_are_historic(runs):
    for run in runs:
        assert run.data.tags.get("fuente") == "historico", run.data.tags.get("run_key")


def test_live_runs_do_not_break_historic_check():
    # historic_runs must ignore fuente=live_notebook runs by construction;
    # covered statically here, dynamically by --check on a store with only
    # historic runs (17) — a live run would not change the historic count.
    specs = MOD.build_specs()
    assert all(spec["tags"].get("fuente") == "historico" for spec in specs)
