#!/usr/bin/env python
"""Backfill the 17 measured runs into the `ds02-clase` MLflow experiment.

PIA-4 (20 % of PIA) asks for every model and experiment with hyperparameters,
metrics and a comparison; SAA asks for a table "taken from MLflow". This script
records what is already measured in `resultados/` and `models/ds02_manifest.json`.
It never trains, never writes `models/`, and never calls `log_model`/`autolog`.

Usage
-----
    python scripts/backfill_mlflow.py --write   # create/replace the 17 runs
    python scripts/backfill_mlflow.py --check   # verify the store and the export
    python scripts/backfill_mlflow.py --export  # regenerate the CSV from the store

The store is `./mlruns` (text-only file store). `--write` is idempotent by the
`run_key` tag: it deletes an existing active run with the same key and creates it
again from the CSV. Re-running it never creates an 18th run.

The 17 runs are: 9 row-grain models (5 classic + 4 MLP), 4 window-grain models
(LGBM, BiLSTM, BiLSTM+EMA5 and the deployed bundle C) and the 4 `cyc_norm`
ablation variants in `resultados/ablacion_cycnorm.csv` (one run per variant,
always the BiLSTM+EMA5, which is the best model in all four). The full 4 x 3
grid stays in the notebook output and in that CSV. Nothing here re-executes a
notebook.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

# MLflow 3.18 refuses the filesystem store unless this opt-out is explicit.
# The plan requires a text-only store (no SQLite, no server), so set it before
# importing mlflow. It is harmless if the caller already exported it.
os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")

from mlflow.tracking import MlflowClient  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT = "ds02-clase"
STORE = ROOT / "mlruns"
EXPORT = ROOT / "docs" / "evidencia" / "mlflow" / "comparativa.csv"
ABLATION = ROOT / "resultados" / "ablacion_cycnorm.csv"
N_RUNS = 17

EXPORT_FIELDS = [
    "run_key", "run_id", "run_name", "grano", "familia", "rol", "seleccion",
    "origen", "fuente", "params_summary", "params_json", "metrics_json",
    "rmse_train", "mae_train", "r2_train",
    "rmse_val", "mae_val", "r2_val",
    "rmse_test", "mae_test", "r2_test", "nasa_test",
    "tiempo_s", "t_lgb_s", "t_bilstm_s", "macro_rmse",
]

FUENTE_HISTORICO = "historico"
FUENTE_LIVE = "live_notebook"


def _is_historic(run) -> bool:
    """Historic backfill run: fuente=historico, or legacy run with a known
    historic run_key and no fuente tag yet (pre mlflow-live-notebooks)."""
    fuente = run.data.tags.get("fuente") if run.data.tags else None
    if fuente is not None:
        return fuente == FUENTE_HISTORICO
    return run.data.tags.get("run_key") in {
        f"clasico__{name}" for name in ("regresion", "knn", "rf", "svm", "xgb")
    } | {
        f"mlp__{name}" for name in ("base", "E1_capacidad", "E2_reg_lr", "E3_batch")
    } | {"bundle__lgbm_c", "bundle__bilstm_c", "bundle__bilstm_ema5", "prod__bundle_c"}


def historic_runs(client: MlflowClient, exp_id: str) -> list:
    """Only the historic backfill runs; live notebook runs are ignored."""
    return [r for r in client.search_runs([exp_id], max_results=100) if _is_historic(r)]

DESCRIPTION = (
    "Reto 1 — 17 runs medidos: 9 de grano fila (5 clásicos + 4 MLP), 4 de grano "
    "ventana (LGBM, BiLSTM, BiLSTM+EMA5 y el bundle C desplegado) y 4 de la "
    "ablación de cyc_norm (OFF / OFF+delta / ON / ON+delta sobre BiLSTM+EMA5). "
    "Los granos fila y ventana NO son comparables entre sí: fila = una lectura, "
    "ventana = 50 lecturas. Las 4 runs de ablación filtran la variante con el tag "
    "`familia=ablacion_cycnorm`; el grid 4x3 completo está en "
    "`resultados/ablacion_cycnorm.csv`. El store es texto; los binarios siguen en "
    "models/ y se identifican por SHA."
)

CLASSIC_EXTRAS: dict[str, dict[str, Any]] = {
    "regresion": {},
    "knn": {},
    "rf": {"n_estimators": 200},
    "xgb": {
        "n_estimators": 300, "learning_rate": 0.05,
        "subsample": 0.8, "colsample_bytree": 0.8,
    },
    "svm": {"subsample": 5000, "seed_subsample": 42},
}

MLP_EXTRAS: dict[str, Any] = {
    "activation": "relu",
    "learning_rate_init": 0.001,
    "max_iter": 300,
    "early_stopping": True,
    "batch_size": "auto",
}

CLASSIC_SUMMARY = {
    "regresion": "alpha=10.0",
    "knn": "n_neighbors=31",
    "rf": "max_depth=8, n_estimators=200",
    "svm": "C=10.0, epsilon=1.0 (submuestra 5000)",
    "xgb": "max_depth=4, n_estimators=300, lr=0.05",
}


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _git() -> tuple[str, str]:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True
        ).strip()
    except Exception:
        commit = "unknown"
    try:
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=ROOT, text=True
            ).strip()
        )
    except Exception:
        dirty = True
    return commit, "true" if dirty else "false"


def _data_hashes() -> str:
    parts = []
    for name in ("train", "test"):
        path = ROOT / "data" / "processed" / f"{name}.parquet"
        parts.append(f"{name}={_sha256(path) if path.exists() else 'unavailable'}")
    return ";".join(parts)


def _param_text(value: Any) -> str:
    """MLflow stores every parameter as text; keep the same spelling in --check."""
    return str(value)


def _flatten_reg(params: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, value in params.items():
        out[key.split("__", 1)[1] if key.startswith("reg__") else key] = value
    return out


def _hidden_text(value: Any) -> str:
    if isinstance(value, (tuple, list)):
        return "-".join(str(int(v)) for v in value)
    return str(value)


def _common_tags(grano: str, familia: str, origen: str, extra: dict[str, Any]) -> dict[str, str]:
    commit, dirty = _git()
    tags: dict[str, Any] = {
        "grano": grano,
        "familia": familia,
        "origen": origen,
        "fuente": FUENTE_HISTORICO,
        "dataset": "DS02",
        "dataset_variant": "DS02-adaptada (MAR T30 + ffill, medianas fit-units)",
        "job": "reto-1-saa-pia-mia",
        "git_commit": commit,
        "git_dirty": dirty,
    }
    if grano == "fila":
        tags.update({
            "cv_scheme": "GroupKFold", "cv_folds": "3", "cv_group": "unit",
            "scoring": "rmse", "refit": "rmse", "seed": "42",
            "pipeline": "StandardScaler(19)+OneHot(fase_vuelo)",
            "n_features": "22", "n_train": "52635", "n_test": "12538",
        })
    else:
        tags.update({
            "cv_scheme": "grouped_out_of_fold", "cv_group": "unit",
            "scoring": "rmse", "seed": "42",
            "pipeline": "SensorResidualizer+StandardScaler(18)+window 50x19",
            "n_features": "93", "n_channels": "19",
            "n_train": "17450", "n_test": "6196", "n_units_test": "3",
        })
    tags.update(extra)
    return {key: str(value) for key, value in tags.items()}


def _row_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []

    for row in _read_csv(ROOT / "resultados" / "comparativa.csv"):
        name = row["modelo"]
        params = _flatten_reg(ast.literal_eval(row["mejores_params"]))
        params.update(CLASSIC_EXTRAS[name])
        metrics = {
            key: float(row[key])
            for key in ("rmse_train", "mae_train", "r2_train",
                        "rmse_val", "mae_val", "r2_val",
                        "rmse_test", "mae_test", "r2_test")
            if row.get(key) not in (None, "", "nan")
        }
        if row.get("tiempo_s") not in (None, "", "nan"):
            metrics["tiempo_s"] = float(row["tiempo_s"])
        extra = {
            "run_key": f"clasico__{name}",
            "rol": "comparado",
            "params_summary": CLASSIC_SUMMARY[name],
        }
        if name == "xgb":
            extra.update({"seleccion": "mejor_clasico", "test_lectura": "unica"})
        note = (
            f"Mejor clásico por rmse_val ({metrics['rmse_val']:.4f}). "
            "Test leído una sola vez y solo para el elegido."
            if name == "xgb" else
            f"Clásico del track de clase; selección por rmse_val ({metrics['rmse_val']:.4f})."
        )
        specs.append({
            "run_key": f"clasico__{name}",
            "run_name": f"clasico__{name}",
            "params": params,
            "metrics": metrics,
            "tags": _common_tags("fila", "clasico", "comparativa.csv", extra),
            "note": note,
        })

    for row in _read_csv(ROOT / "resultados" / "mlp_comparativa.csv"):
        name = row["experimento"]
        params = dict(MLP_EXTRAS)
        params.update(ast.literal_eval(row["params"]))
        params["hidden_layer_sizes"] = _hidden_text(params["hidden_layer_sizes"])
        metrics = {
            key: float(row[key])
            for key in ("rmse_train", "mae_train", "r2_train",
                        "rmse_val", "mae_val", "r2_val",
                        "rmse_test", "mae_test", "r2_test")
            if row.get(key) not in (None, "", "nan")
        }
        if row.get("tiempo_s") not in (None, "", "nan"):
            metrics["tiempo_s"] = float(row["tiempo_s"])
        hidden = params["hidden_layer_sizes"]
        summary = f"hidden={hidden}, alpha={params['alpha']}"
        if params.get("batch_size") not in (None, "auto"):
            summary += f", batch={params['batch_size']}"
        extra = {
            "run_key": f"mlp__{name}",
            "rol": "comparado",
            "params_summary": summary,
        }
        if name == "E2_reg_lr":
            extra.update({"seleccion": "mejor_mlp,campeon_fila", "test_lectura": "unica"})
        note = str(row["hipotesis"])
        if name == "E2_reg_lr":
            note += (
                f" Elegido por rmse_val ({metrics['rmse_val']:.4f}); test leído "
                f"una sola vez ({metrics.get('rmse_test', float('nan')):.4f})."
            )
        specs.append({
            "run_key": f"mlp__{name}",
            "run_name": f"mlp__{name}",
            "params": params,
            "metrics": metrics,
            "tags": _common_tags("fila", "mlp", "mlp_comparativa.csv", extra),
            "note": note,
        })

    return specs


def _times_from_log() -> dict[str, float]:
    text = (ROOT / "resultados" / "bundle_c_train.log").read_text(
        encoding="utf-8", errors="replace"
    )
    lgb = re.search(r"LGBM\s+([\d.]+)s", text)
    bil = re.search(r"BiLSTM\s+([\d.]+)s", text)
    total = re.search(r"total\s+(\d+)s", text)
    if not (lgb and bil and total):
        raise SystemExit("No pude leer los tiempos de resultados/bundle_c_train.log")
    return {"lgbm": float(lgb.group(1)), "bilstm": float(bil.group(1)),
            "total": float(total.group(1))}


def _bundle_metrics(row: dict[str, str]) -> dict[str, float]:
    return {
        "rmse_test": float(row["RMSE"]),
        "mae_test": float(row["MAE"]),
        "r2_test": float(row["R2"]),
        "nasa_test": float(row["NASA_Score"]),
    }


def _window_specs() -> list[dict[str, Any]]:
    rows = {row["Modelo"]: row for row in
            _read_csv(ROOT / "resultados" / "comparativa_bundle_c.csv")}
    times = _times_from_log()
    specs: list[dict[str, Any]] = []

    lgbm_params = {
        "objective": "quantile", "alpha": 0.35, "n_estimators": 300,
        "learning_rate": 0.02, "num_leaves": 15, "max_depth": 4,
        "min_child_samples": 50, "reg_alpha": 1.0, "reg_lambda": 5.0,
        "colsample_bytree": 0.8, "subsample": 0.8, "seed": 42,
    }
    specs.append({
        "run_key": "bundle__lgbm_c",
        "run_name": "bundle__lgbm_c",
        "params": lgbm_params,
        "metrics": {**_bundle_metrics(rows["LGBM-C (cuantil 0.35)"]),
                    "tiempo_s": times["lgbm"]},
        "tags": _common_tags("ventana", "bundle_c",
                             "comparativa_bundle_c.csv+bundle_c_train.log", {
                                 "run_key": "bundle__lgbm_c",
                                 "rol": "componente",
                                 "alias": "lgbm_adaptada",
                                 "params_summary": "quantile 0.35, 300 trees, lr=0.02, leaves=15",
                             }),
        "note": (
            "Componente tabular del bundle C. Es el mismo modelo que "
            "`lgbm_adaptada`; se registra una sola run con alias para no duplicar."
        ),
    })

    bilstm_params = {
        "n_layers": 2, "units": 64, "dropout": 0.2, "dense_units": 32,
        "input_window": 50, "input_channels": 19, "optimizer": "adam",
        "learning_rate": 0.001, "loss": "huber", "huber_delta": 10.0,
        "epochs": 22, "batch_size": 128, "early_stopping_patience": 5,
        "seed": 42, "n_params": 154253,
    }
    specs.append({
        "run_key": "bundle__bilstm_c",
        "run_name": "bundle__bilstm_c",
        "params": bilstm_params,
        "metrics": {**_bundle_metrics(rows["BiLSTM-C"]),
                    "tiempo_s": times["bilstm"]},
        "tags": _common_tags("ventana", "bundle_c",
                             "comparativa_bundle_c.csv+bundle_c_train.log", {
                                 "run_key": "bundle__bilstm_c",
                                 "rol": "componente",
                                 "params_summary": "2x64, dropout=0.2, epochs=22, batch=128",
                             }),
        "note": "Componente secuencial del bundle C; 154 253 parámetros.",
    })

    specs.append({
        "run_key": "bundle__bilstm_ema5",
        "run_name": "bundle__bilstm_ema5",
        "params": {"ema_span": 5, "base": "bilstm_c", "seed": 42},
        "metrics": _bundle_metrics(rows["BiLSTM-C + EMA5"]),
        "tags": _common_tags("ventana", "bundle_c",
                             "comparativa_bundle_c.csv+bundle_c_train.log", {
                                 "run_key": "bundle__bilstm_ema5",
                                 "rol": "variante",
                                 "base": "bilstm_c",
                                 "params_summary": "span=5, base=bilstm_c",
                             }),
        "note": (
            "Variante suavizada del BiLSTM. No se cronometró: el tiempo queda "
            "vacío, no se rellena con 0."
        ),
    })

    manifest = json.loads((ROOT / "models" / "ds02_manifest.json").read_text(encoding="utf-8"))
    shape = manifest["model_shape"]
    conf = manifest["conformal"]
    inf = manifest["inference_contract"]
    art = manifest["artifacts"]
    ref = manifest["metrics"]["reference_row"]
    prod_params = {
        "seed": manifest["seed"],
        "beta": inf["beta"],
        "ema_span": inf["ema_span"],
        "window": inf["window_size"],
        "lgb_features": shape["lgb_n_features"],
        "scaler_features": shape["scaler_n_features"],
        "n_op": shape["n_op"],
        "bilstm_input": "50x19",
        "meta_features": shape["meta_features"],
        "epochs": 22,
        "epochs_oof": 15,
        "step_train": 3,
        "step_test": 2,
        "conformal_target": conf["target_coverage"],
        "n_calibration": conf["n_calibration"],
        "lgb_objective": manifest["lgb_objective"]["objective"],
        "lgb_alpha": manifest["lgb_objective"]["alpha"],
        "n_params": shape["bilstm_params"],
        "ensemble_sha256": art["ensemble_sha256"],
        "bilstm_sha256": art["bilstm_sha256"],
        "clase_xgb_sha256": art["clase_xgb_sha256"],
        "clase_e2_sha256": art["clase_e2_sha256"],
    }
    prod_metrics = {
        "rmse_test": float(ref["RMSE"]),
        "mae_test": float(ref["MAE"]),
        "r2_test": float(ref["R2"]),
        "nasa_test": float(ref["NASA_Score"]),
        "macro_rmse": float(manifest["metrics"]["macro_rmse"]),
        "tiempo_s": times["total"],
        "t_lgb_s": times["lgbm"],
        "t_bilstm_s": times["bilstm"],
    }
    specs.append({
        "run_key": "prod__bundle_c",
        "run_name": "prod__bundle_c",
        "params": prod_params,
        "metrics": prod_metrics,
        "tags": _common_tags("ventana", "bundle_c", "manifest", {
            "run_key": "prod__bundle_c",
            "rol": "produccion",
            "seleccion": "produccion",
            "v3_bundle": "archivado",
            "params_summary": "seed=42, beta=1.0, EMA=5, window=50, 93 feats",
        }),
        "note": (
            "Modelo desplegado (bundle C). Métricas del manifiesto, no de un "
            "reentrenamiento; el tiempo es el total del entrenamiento del bundle "
            "(447 s), con LGBM 0.3 s y BiLSTM 113.2 s. `v3_bundle` es un tag "
            "archivado, no un parámetro."
        ),
    })
    return specs


ABLATION_MODEL_KEY = {"LGBM": "lgbm", "BiLSTM": "bilstm", "BiLSTM+EMA": "bilstm_ema5"}

ABLATION_VARIANT_KEY = {
    "cyc_norm OFF": "off",
    "cyc_norm OFF + baseline delta": "off_delta",
    "cyc_norm ON (baseline)": "on",
    "cyc_norm ON + baseline delta": "on_delta",
}

ABLATION_METRIC_KEYS = (
    "rmse_test", "mae_test", "r2_test", "nasa_test",
    "tiempo_s", "t_lgb_s", "t_bilstm_s",
)


def _ablation_specs() -> list[dict[str, Any]]:
    """Las 4 variantes de cyc_norm, una run por variante con el mejor modelo.

    El grid completo (4 variantes x 3 modelos) se mide en nb03 y queda en
    `resultados/ablacion_cycnorm.csv`. Aqui se registra una run por variante con
    el modelo de menor RMSE de esa variante (BiLSTM+EMA5 gana las cuatro), para
    que la comparacion en MLflow aisele el efecto de cyc_norm sin mezclar
    familias dentro de la misma grafica.
    """
    rows = _read_csv(ABLATION)
    if not rows:
        raise SystemExit(f"{ABLATION.relative_to(ROOT)} esta vacio")

    best: dict[str, dict[str, str]] = {}
    for row in rows:
        variant = " ".join(row["variant"].split())
        if variant not in ABLATION_VARIANT_KEY:
            raise SystemExit(f"variante desconocida en el CSV: {variant!r}")
        model = row["model"]
        if model not in ABLATION_MODEL_KEY:
            raise SystemExit(f"modelo desconocido en el CSV: {model!r}")
        current = best.get(variant)
        if current is None or float(row["rmse_test"]) < float(current["rmse_test"]):
            best[variant] = row

    missing = set(ABLATION_VARIANT_KEY) ^ set(best)
    if missing:
        raise SystemExit(f"faltan variantes en el CSV: {sorted(missing)}")

    specs: list[dict[str, Any]] = []
    for variant, row in best.items():
        model = row["model"]
        run_key = f"ablacion__{ABLATION_VARIANT_KEY[variant]}__{ABLATION_MODEL_KEY[model]}"
        params: dict[str, Any] = {
            "variant": variant, "model": model, "window": 50, "seed": 42,
        }
        if model == "BiLSTM+EMA":
            params["ema_span"] = 5
        metrics = {
            key: float(row[key])
            for key in ABLATION_METRIC_KEYS
            if row.get(key) not in (None, "", "nan")
        }
        specs.append({
            "run_key": run_key,
            "run_name": run_key,
            "params": params,
            "metrics": metrics,
            "tags": _common_tags("ablacion", "ablacion_cycnorm",
                                 "ablacion_cycnorm.csv", {
                                     "run_key": run_key,
                                     "rol": "ablacion",
                                     "variant": variant,
                                     "params_summary": f"{variant}; {model}; test 11/14/15",
                                 }),
            "note": (
                f"Ablacion cyc_norm, variante '{variant}' con {model}. Medida "
                "sobre test 11/14/15 (semilla 42) en nb03; no se reentrena. El "
                "grid 4x3 completo esta en resultados/ablacion_cycnorm.csv."
            ),
        })
    return specs


def build_specs() -> list[dict[str, Any]]:
    """Devuelve las 17 especificaciones historicas (params, metricas, tags) del backfill."""
    specs = _row_specs() + _window_specs() + _ablation_specs()
    keys = [spec["run_key"] for spec in specs]
    if len(specs) != N_RUNS:
        raise SystemExit(f"Esperaba {N_RUNS} runs, construí {len(specs)}")
    if len(set(keys)) != len(keys):
        raise SystemExit(f"run_key duplicado: {keys}")
    return specs


def _experiment_tags() -> dict[str, str]:
    return {
        "python": "3.12.10",
        "sklearn": "1.9.1",
        "xgboost": "3.4.1",
        "lightgbm": "4.7.0",
        "tensorflow": "2.21.0",
        "keras": "3.15.1",
        "job": "reto-1-saa-pia-mia",
        "data_sha256": _data_hashes(),
    }


def ensure_experiment(client: MlflowClient) -> str:
    """Crea el experimento ds02-clase si no existe y devuelve su id."""
    exp = client.get_experiment_by_name(EXPERIMENT)
    exp_id = exp.experiment_id if exp is not None else client.create_experiment(EXPERIMENT)
    for key, value in _experiment_tags().items():
        client.set_experiment_tag(exp_id, key, str(value))
    client.set_experiment_tag(exp_id, "mlflow.note.content", DESCRIPTION)
    return exp_id


def write_runs(client: MlflowClient, exp_id: str) -> None:
    """Crea o reemplaza los runs historicos de forma idempotente por run_key."""
    specs = build_specs()
    for spec in specs:
        existing = historic_runs(client, exp_id)
        for old in existing:
            if old.data.tags.get("run_key") == spec["run_key"]:
                client.delete_run(old.info.run_id)
        tags = dict(spec["tags"])
        tags["run_key"] = spec["run_key"]
        run = client.create_run(exp_id, run_name=spec["run_name"], tags=tags)
        run_id = run.info.run_id
        for key, value in spec["params"].items():
            client.log_param(run_id, key, _param_text(value), synchronous=True)
        for key, value in spec["metrics"].items():
            client.log_metric(run_id, key, float(value), synchronous=True)
        client.set_tag(run_id, "mlflow.note.content", spec["note"], synchronous=True)
        client.set_terminated(run_id, status="FINISHED")
    print(f"Escritos {len(specs)} runs en {EXPERIMENT}")


def _metric_text(data: Any, key: str) -> str:
    value = data.metrics.get(key)
    if value is None:
        return ""
    return f"{float(value):.10g}"


def export_csv(client: MlflowClient, exp_id: str) -> None:
    """Exporta el store a docs/evidencia/mlflow/comparativa.csv."""
    runs = historic_runs(client, exp_id)
    rows = []
    for run in runs:
        data = run.data
        rows.append({
            "run_key": data.tags.get("run_key", ""),
            "run_id": run.info.run_id,
            "run_name": run.info.run_name or "",
            "grano": data.tags.get("grano", ""),
            "familia": data.tags.get("familia", ""),
            "rol": data.tags.get("rol", ""),
            "seleccion": data.tags.get("seleccion", ""),
            "origen": data.tags.get("origen", ""),
            "fuente": data.tags.get("fuente", FUENTE_HISTORICO),
            "params_summary": data.tags.get("params_summary", ""),
            "params_json": json.dumps(data.params, sort_keys=True, ensure_ascii=False),
            "metrics_json": json.dumps(data.metrics, sort_keys=True, ensure_ascii=False),
            "rmse_train": _metric_text(data, "rmse_train"),
            "mae_train": _metric_text(data, "mae_train"),
            "r2_train": _metric_text(data, "r2_train"),
            "rmse_val": _metric_text(data, "rmse_val"),
            "mae_val": _metric_text(data, "mae_val"),
            "r2_val": _metric_text(data, "r2_val"),
            "rmse_test": _metric_text(data, "rmse_test"),
            "mae_test": _metric_text(data, "mae_test"),
            "r2_test": _metric_text(data, "r2_test"),
            "nasa_test": _metric_text(data, "nasa_test"),
            "tiempo_s": _metric_text(data, "tiempo_s"),
            "t_lgb_s": _metric_text(data, "t_lgb_s"),
            "t_bilstm_s": _metric_text(data, "t_bilstm_s"),
            "macro_rmse": _metric_text(data, "macro_rmse"),
        })
    rows.sort(key=lambda row: (row["grano"], row["familia"], row["run_key"]))
    EXPORT.parent.mkdir(parents=True, exist_ok=True)
    with EXPORT.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=EXPORT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Exportadas {len(rows)} filas a {EXPORT.relative_to(ROOT)}")


def check(client: MlflowClient, exp_id: str) -> int:
    """Comprueba store y export (17 runs, sin artefactos) y devuelve 0 si cuadra."""
    specs = build_specs()
    expected = {spec["run_key"]: spec for spec in specs}
    runs = historic_runs(client, exp_id)
    errors: list[str] = []

    if len(runs) != N_RUNS:
        errors.append(f"esperaba {N_RUNS} runs activos, hay {len(runs)}")

    by_key: dict[str, list[Any]] = {}
    for run in runs:
        key = run.data.tags.get("run_key")
        if not key:
            errors.append(f"run {run.info.run_id} sin tag run_key")
            continue
        by_key.setdefault(key, []).append(run)

    if set(by_key) != set(expected):
        errors.append(f"run_key extra/faltante: {sorted(set(by_key) ^ set(expected))}")

    for key, spec in expected.items():
        found = by_key.get(key, [])
        if len(found) != 1:
            errors.append(f"{key}: {len(found)} runs activos (esperaba 1)")
            continue
        run = found[0]
        for name, value in spec["params"].items():
            if run.data.params.get(name) != _param_text(value):
                errors.append(f"{key}: param {name}={run.data.params.get(name)!r} != {_param_text(value)!r}")
        for name, value in spec["metrics"].items():
            got = run.data.metrics.get(name)
            if got is None or abs(float(got) - float(value)) > 1e-9:
                errors.append(f"{key}: métrica {name}={got!r} != {value!r}")
        for name in ("grano", "familia", "origen", "rol", "seleccion", "fuente"):
            want = spec["tags"].get(name)
            if want is not None and run.data.tags.get(name) != want:
                errors.append(f"{key}: tag {name}={run.data.tags.get(name)!r} != {want!r}")

    if any(path.is_file() for path in STORE.rglob("artifacts/*")):
        errors.append("hay artefactos en mlruns/**/artifacts/ (debe ser texto)")

    if not EXPORT.exists():
        errors.append(f"falta {EXPORT.relative_to(ROOT)}")
    else:
        with EXPORT.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.DictReader(fh))
        if len(rows) != N_RUNS:
            errors.append(f"CSV con {len(rows)} filas (esperaba {N_RUNS})")
        run_ids = {run.info.run_id for run in runs}
        csv_ids = {row.get("run_id", "") for row in rows}
        if csv_ids != run_ids:
            errors.append("los run_id del CSV no coinciden con el store")
        for row in rows:
            key = row.get("run_key", "")
            spec = expected.get(key)
            if spec is None:
                errors.append(f"CSV con run_key desconocido: {key}")
                continue
            for name in ("rmse_val", "rmse_test", "tiempo_s"):
                if row.get(name):
                    want = spec["metrics"].get(name)
                    if want is None or abs(float(row[name]) - float(want)) > 1e-6:
                        errors.append(f"{key}: CSV {name}={row[name]} != {want}")

    if errors:
        print("FALLOS:")
        for error in errors:
            print(f"- {error}")
        return 2

    print(f"OK: {N_RUNS} runs ({sum(1 for s in specs if s['tags']['grano'] == 'fila')} fila + "
          f"{sum(1 for s in specs if s['tags']['familia'] == 'bundle_c')} ventana + "
          f"{sum(1 for s in specs if s['tags']['familia'] == 'ablacion_cycnorm')} ablacion), "
          f"export y store coinciden, sin artefactos.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada CLI: --write, --check o --live."""
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true", help="crear/reemplazar los 17 runs")
    group.add_argument("--check", action="store_true", help="verificar store y export")
    group.add_argument("--export", action="store_true", help="regenerar el CSV desde el store")
    args = parser.parse_args(argv)

    client = MlflowClient(tracking_uri=STORE.resolve().as_uri())
    if args.check:
        exp = client.get_experiment_by_name(EXPERIMENT)
        if exp is None:
            print(f"FALLO: no existe el experimento {EXPERIMENT}")
            return 2
        return check(client, exp.experiment_id)

    exp_id = ensure_experiment(client)
    if args.write:
        write_runs(client, exp_id)
        export_csv(client, exp_id)
    elif args.export:
        export_csv(client, exp_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
