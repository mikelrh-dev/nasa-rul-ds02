"""Live MLflow tracking for notebook re-execution (mlflow-live-notebooks).

Text-only file store under ``mlruns/`` (same store the backfill writes).
Live runs are tagged ``fuente=live_notebook`` so the historic backfill
(``fuente=historico``) never counts, deletes or overwrites them.

Rules enforced here:
- params via ``log_param``, metrics via ``log_metric``;
- NaN/inf metrics are skipped, never logged (frozen-bundle timings in
  ``puente_c`` are NaN by design: the bundle was not retrained);
- no ``log_model``/autolog: binaries stay under ``models/``.
"""
from __future__ import annotations

import csv
import json
import math
import os
from pathlib import Path
from typing import Any, Iterable

EXPERIMENT = "ds02-clase"
FUENTE_LIVE = "live_notebook"
FUENTE_HISTORICO = "historico"

_ROOT = Path(__file__).resolve().parents[2]
STORE = _ROOT / "mlruns"
RESULTADOS = _ROOT / "resultados"

TIMING_FIELDS = ["run_key", "t_lgb_s", "t_bilstm_s", "tiempo_s", "fuente"]


def clean_metric(value: Any) -> float | None:
    """Return a finite float, or None for NaN/inf/non-numeric (skip logging)."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(number):
        return None
    return number


def clean_timing_value(value: Any) -> float | None:
    """Limpia un valor de tiempo: devuelve float o None si no es un número finito."""
    return clean_metric(value)


def setup_mlflow(tracking_uri: str | None = None, experiment: str = EXPERIMENT) -> str:
    """Point MLflow at the text-only store and ensure the experiment exists."""
    os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
    import mlflow

    uri = tracking_uri or STORE.resolve().as_uri()
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(experiment)
    return uri


def _client():
    os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
    from mlflow.tracking import MlflowClient

    return MlflowClient(tracking_uri=STORE.resolve().as_uri())


def _experiment_id(client, experiment: str = EXPERIMENT) -> str:
    exp = client.get_experiment_by_name(experiment)
    if exp is not None:
        return exp.experiment_id
    return client.create_experiment(experiment)


def _sum_oof_seconds(timing: Any) -> float | None:
    """Sum finite ``seconds`` from an OOF timing list; None if empty."""
    if not isinstance(timing, (list, tuple)):
        return None
    secs = []
    for entry in timing:
        raw = entry.get("seconds") if isinstance(entry, dict) else entry
        value = clean_metric(raw)
        if value is not None:
            secs.append(value)
    return sum(secs) if secs else None


def timing_from_result(result: dict[str, Any] | None) -> dict[str, float | None]:
    """Normalise any ``run_seed``/``puente_c``/OOF result to clean keys."""
    if result is None:
        return {"t_lgb_s": None, "t_bilstm_s": None, "tiempo_s": None}
    if isinstance(result, (list, tuple)):
        return {"t_lgb_s": None, "t_bilstm_s": None, "tiempo_s": _sum_oof_seconds(result)}
    if not isinstance(result, dict):
        return {"t_lgb_s": None, "t_bilstm_s": None, "tiempo_s": clean_metric(result)}
    raw_timing = result.get("timing") or result
    if isinstance(raw_timing, (list, tuple)):
        return {
            "t_lgb_s": None,
            "t_bilstm_s": None,
            "tiempo_s": _sum_oof_seconds(raw_timing),
        }
    if not isinstance(raw_timing, dict):
        raw_timing = {}
    timing = raw_timing
    t_lgb = clean_metric(timing.get("t_lgb", timing.get("t_lgb_s")))
    t_lstm = clean_metric(
        timing.get("t_lstm", timing.get("t_bilstm", timing.get("t_bilstm_s")))
    )
    total = clean_metric(timing.get("t_total", timing.get("tiempo_s")))
    if total is None and (t_lgb is not None or t_lstm is not None):
        total = (t_lgb or 0.0) + (t_lstm or 0.0)
    return {"t_lgb_s": t_lgb, "t_bilstm_s": t_lstm, "tiempo_s": total}


def log_live_run(
    run_key: str,
    params: dict[str, Any] | None = None,
    metrics: dict[str, Any] | None = None,
    timings: dict[str, Any] | None = None,
    tags: dict[str, Any] | None = None,
    notebook: str = "",
    experiment: str = EXPERIMENT,
) -> str:
    """Create one live run: log_param + log_metric, NaN skipped, FINISHED."""
    client = _client()
    exp_id = _experiment_id(client, experiment)
    run_tags = {
        "run_key": str(run_key),
        "fuente": FUENTE_LIVE,
        "notebook": str(notebook),
        **{str(k): str(v) for k, v in (tags or {}).items()},
    }
    run = client.create_run(exp_id, run_name=str(run_key), tags=run_tags)
    run_id = run.info.run_id

    for key, value in (params or {}).items():
        client.log_param(run_id, str(key), str(value), synchronous=True)

    merged_metrics: dict[str, Any] = dict(metrics or {})
    if timings is not None:
        clean = timing_from_result(timings)
        for key, value in clean.items():
            if value is not None:
                merged_metrics[key] = value
    for key, value in merged_metrics.items():
        number = clean_metric(value)
        if number is None:
            continue
        client.log_metric(run_id, str(key), number, synchronous=True)

    client.set_terminated(run_id, status="FINISHED")
    return run_id


def persist_timings(
    rows: Iterable[dict[str, Any]],
    stem: str,
    out_dir: str | Path | None = None,
) -> tuple[Path, Path]:
    """Persist only rows with a finite timing to ``tiempos_<stem>.json/.csv``."""
    out = Path(out_dir) if out_dir is not None else RESULTADOS
    out.mkdir(parents=True, exist_ok=True)
    norm = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        run_key = row.get("run_key", "")
        if not run_key:
            continue
        cleaned = {
            "run_key": run_key,
            "t_lgb_s": clean_metric(row.get("t_lgb_s")),
            "t_bilstm_s": clean_metric(row.get("t_bilstm_s")),
            "tiempo_s": clean_metric(row.get("tiempo_s")),
            "fuente": row.get("fuente", "live_notebook"),
        }
        if all(cleaned[field] is None for field in ("t_lgb_s", "t_bilstm_s", "tiempo_s")):
            continue
        norm.append(cleaned)
    json_path = out / f"tiempos_{stem}.json"
    csv_path = out / f"tiempos_{stem}.csv"
    json_path.write_text(json.dumps(norm, indent=2, ensure_ascii=False), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=TIMING_FIELDS)
        writer.writeheader()
        for row in norm:
            writer.writerow(
                {k: ("" if v is None else v) for k, v in row.items()}
            )
    return json_path, csv_path
