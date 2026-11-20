"""Helpers de MLflow en vivo y contrato de tiempos.

Aquí no se ejecuta ningún notebook ni se entrena ningún modelo. Los tests fijan:
- las métricas NaN/inf nunca se registran (manejo de NaN del bundle congelado);
- run_seed y oof miden con perf_counter y devuelven el tiempo total;
- ablation_table lleva columnas de tiempo por fila;
- persist_timings escribe JSON y CSV coherentes;
- las especificaciones del backfill son solo históricas (fuente=historico);
- los NB01-07 llevan la cabecera de MLflow, una celda de registro en vivo, sin
  TF_ENABLE_ONEDNN_OPTS tardío y con el renombrado de STEP_TRAIN_OOF.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted((ROOT / "notebooks").glob("0*.ipynb"))


def _load_backfill():
    path = ROOT / "scripts" / "operativo" / "backfill_mlflow.py"
    spec = importlib.util.spec_from_file_location("backfill_mlflow_live", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _nb_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _nb_cells(path: Path):
    return json.loads(_nb_text(path))["cells"]


def _cell_source(cell) -> str:
    return "".join(cell.get("source", []))


# --- mlflow_live helpers -------------------------------------------------

def test_clean_metric_drops_nan_inf_none():
    from ds02_rul.mlflow_live import clean_metric

    assert clean_metric(float("nan")) is None
    assert clean_metric(float("inf")) is None
    assert clean_metric(None) is None
    assert clean_metric(3.5) == 3.5
    assert clean_metric("not-a-number") is None


def test_timing_from_result_converts_nan_to_none():
    from ds02_rul.mlflow_live import timing_from_result

    timing = timing_from_result({"t_lgb": float("nan"), "t_lstm": 2.0, "t_total": 3.0})
    assert timing["t_lgb_s"] is None
    assert timing["t_bilstm_s"] == 2.0
    assert timing["tiempo_s"] == 3.0


def test_timing_from_result_uses_timing_dict():
    from ds02_rul.mlflow_live import timing_from_result

    timing = timing_from_result(
        {"timing": {"t_lgb": 0.5, "t_lstm": 1.5, "t_total": 2.0}}
    )
    assert timing == {"t_lgb_s": 0.5, "t_bilstm_s": 1.5, "tiempo_s": 2.0}


def test_persist_timings_writes_matching_json_and_csv(tmp_path):
    from ds02_rul.mlflow_live import persist_timings

    rows = [
        {"run_key": "live__x", "t_lgb_s": 0.5, "t_bilstm_s": None, "tiempo_s": 0.5, "fuente": "live_notebook"},
        {"run_key": "live__y", "t_lgb_s": 0.6, "t_bilstm_s": 4.0, "tiempo_s": 4.6, "fuente": "live_notebook"},
    ]
    json_path, csv_path = persist_timings(rows, "nb03", out_dir=tmp_path)
    assert json_path.exists() and csv_path.exists()
    assert json.loads(json_path.read_text(encoding="utf-8")) == rows
    with csv_path.open(encoding="utf-8", newline="") as fh:
        csv_rows = list(csv.DictReader(fh))
    assert len(csv_rows) == 2
    assert csv_rows[0]["run_key"] == "live__x"
    assert csv_rows[1]["t_bilstm_s"] == "4.0"


def test_log_live_run_skips_nan_and_tags_fuente(tmp_path, monkeypatch):
    from ds02_rul import mlflow_live

    calls = {"params": [], "metrics": [], "tags": []}

    class FakeClient:
        def get_experiment_by_name(self, name):
            return type("E", (), {"experiment_id": "exp-1"})()

        def create_run(self, exp_id, run_name=None, tags=None):
            calls["tags"].append(dict(tags or {}))
            return type("R", (), {"info": type("I", (), {"run_id": "fake-id"})()})()

        def log_param(self, run_id, key, value, synchronous=True):
            calls["params"].append((key, value))

        def log_metric(self, run_id, key, value, synchronous=True):
            calls["metrics"].append((key, value))

        def set_tag(self, run_id, key, value, synchronous=True):
            calls["tags"].append({key: value})

        def set_terminated(self, run_id, status="FINISHED"):
            calls["terminated"] = status

    monkeypatch.setattr(mlflow_live, "_client", lambda: FakeClient())
    run_id = mlflow_live.log_live_run(
        "live__test",
        params={"seed": 42},
        metrics={"rmse_test": 4.338, "tiempo_s": float("nan")},
        timings={"t_lgb": float("nan"), "t_lstm": 1.0},
        notebook="03",
    )
    assert run_id == "fake-id"
    assert ("seed", "42") in calls["params"]
    metric_keys = {k for k, _ in calls["metrics"]}
    assert "rmse_test" in metric_keys
    # un tiempo_s NaN nunca se registra tal cual; el total derivado (0+1.0) sí es real
    assert dict(calls["metrics"])["tiempo_s"] == pytest.approx(1.0)
    assert "t_lgb_s" not in metric_keys  # la rama NaN nunca se registra
    assert "t_bilstm_s" in metric_keys
    all_tags = {}
    for tag in calls["tags"]:
        all_tags.update(tag)
    assert all_tags["fuente"] == "live_notebook"
    assert all_tags["run_key"] == "live__test"
    assert all_tags["notebook"] == "03"


# --- pipeline timing ------------------------------------------------------

def test_run_seed_uses_perf_counter():
    source = (ROOT / "src" / "ds02_rul" / "pipeline.py").read_text(encoding="utf-8")
    assert "time.perf_counter()" in source
    # no queda ningún tiempo de rama medido con reloj de pared
    assert "time.time() - t0" not in source
    assert "time.time()-t0" not in source


def test_ablation_table_has_timing_columns():
    source = (ROOT / "src" / "ds02_rul" / "pipeline.py").read_text(encoding="utf-8")
    for col in ("t_lgb_s", "t_bilstm_s", "tiempo_s"):
        assert col in source
    # las filas deben incluirlas, no solo mencionarlas
    assert '"t_lgb_s"' in source or "'t_lgb_s'" in source


def test_ablation_table_timing_rows_with_fake_run_seed(monkeypatch):
    import numpy as np
    import pandas as pd

    from ds02_rul import pipeline

    meta = pd.DataFrame({"unit": [11.0, 14.0], "cycle": [10.0, 20.0]})

    def fake_run_seed(raw, seed, fit_units, holdout_units, test_units=None, **kw):
        return {
            "test": {"meta": meta, "y": np.array([1.0, 2.0])},
            "p_lgb_test": np.array([1.1, 2.1]),
            "p_lstm_test": np.array([0.9, 1.9]),
            "t_lgb": 0.5,
            "t_lstm": 4.0,
            "t_total": 4.5,
            "timing": {"t_lgb": 0.5, "t_lstm": 4.0, "t_total": 4.5},
        }

    monkeypatch.setattr(pipeline, "run_seed", fake_run_seed)
    table = pipeline.ablation_table({}, seeds=(42,), fit_units=[2], holdout_units=[16])
    for col in ("t_lgb_s", "t_bilstm_s", "tiempo_s"):
        assert col in table.columns, col
    lgb = table[table["model"] == "LGBM"].iloc[0]
    bil = table[table["model"] == "BiLSTM"].iloc[0]
    ema = table[table["model"] == "BiLSTM+EMA"].iloc[0]
    assert float(lgb["t_lgb_s"]) == pytest.approx(0.5)
    assert float(lgb["tiempo_s"]) == pytest.approx(0.5)
    assert float(bil["t_bilstm_s"]) == pytest.approx(4.0)
    assert float(bil["tiempo_s"]) == pytest.approx(4.0)
    assert math.isnan(float(ema["tiempo_s"])) or ema["tiempo_s"] == ""


# --- puente_c NaN refresh -------------------------------------------------

def test_puente_c_timing_dict_is_none_with_fuente():
    from ds02_rul.puente_c import clean_timing_value, puente_c

    # contrato del helper puro (no necesita cargar el bundle)
    assert clean_timing_value(float("nan")) is None
    assert clean_timing_value(1.25) == 1.25
    result_source = (ROOT / "src" / "ds02_rul" / "puente_c.py").read_text(encoding="utf-8")
    assert '"timing"' in result_source
    assert "bundle_congelado" in result_source
    assert "timing_measured" in result_source


# --- backfill solo histórico ------------------------------------------------

def test_backfill_specs_are_historic_only():
    mod = _load_backfill()
    specs = mod.build_specs()
    assert len(specs) == 17
    for spec in specs:
        assert spec["tags"].get("fuente") == "historico", spec["run_key"]


def test_backfill_check_helper_separates_live_runs():
    source = (ROOT / "scripts" / "operativo" / "backfill_mlflow.py").read_text(encoding="utf-8")
    assert "historico" in source
    assert "live_notebook" in source


# --- live store isolation -------------------------------------------------

def test_live_store_defaults_to_mlruns_live():
    from ds02_rul import mlflow_live

    store = mlflow_live._live_store()
    assert store.name == "mlruns-live"
    assert store == mlflow_live._ROOT / "mlruns-live"


def test_live_store_respects_env_override(monkeypatch, tmp_path):
    from ds02_rul import mlflow_live

    target = tmp_path / "custom-store"
    monkeypatch.setenv("MLFLOW_LIVE_STORE", str(target))
    assert mlflow_live._live_store() == target


def test_gitignore_ignores_live_store():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "mlruns-live/" in gitignore


# --- notebooks static contract ---------------------------------------------

def test_all_notebooks_have_mlflow_header_and_log_cell():
    assert len(NOTEBOOKS) == 8
    for path in NOTEBOOKS:
        cells = _nb_cells(path)
        header = _cell_source(cells[0])
        assert "MLFLOW_ALLOW_FILE_STORE" in header, path.name
        assert "setup_mlflow" in header, path.name
        assert "TF_ENABLE_ONEDNN_OPTS" in header, path.name
        body = "\n".join(_cell_source(c) for c in cells)
        assert "log_live_run" in body, f"{path.name} sin celda live"
        assert "persist_timings" in body, f"{path.name} sin persistencia"


def test_no_late_tfenable_onednn_opts():
    for path in NOTEBOOKS:
        cells = _nb_cells(path)
        for idx, cell in enumerate(cells):
            if idx == 0:
                continue
            src = _cell_source(cell)
            assert "TF_ENABLE_ONEDNN_OPTS" not in src, f"{path.name} cell {idx} tardio"


def test_step_train_oof_renamed_nb04():
    nb04 = [p for p in NOTEBOOKS if p.name.startswith("04_")][0]
    body = "\n".join(_cell_source(c) for c in _nb_cells(nb04))
    assert "STEP_TRAIN_OOF" in body
    # la llamada OOF debe usar la constante renombrada, no la del protocolo
    assert "step_train=STEP_TRAIN_OOF" in body.replace(" ", "")
    # la asignación que ocultaba el nombre ya no está
    assert "STEP_TRAIN = 1" not in body
