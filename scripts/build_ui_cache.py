"""Precompute the telemetry cache the Streamlit DSS reads at render time.

    python scripts/build_ui_cache.py                 # base imputada (por defecto)
    python scripts/build_ui_cache.py --base limpia   # HDF5 sin imputar (histórico)

One offline pass over the frozen bundle (`models/ensemble.joblib` +
`models/bilstm_ds02.keras`) and the DS02 test split. **La fuente por defecto es
la base adaptada** (`data/processed/*_con_nulos.parquet` imputados con ffill y
medianas de fit-units), que es con la que se entrenó el bundle desplegado: si se
construyera desde el HDF5 limpio, la app mostraría métricas de otra población de
datos que las que firma el manifiesto.

Writes three small files under `app/cache/`:

* `ds02_windows.parquet` — one row per scored window: unit, cycle, window start,
  ground truth, point estimate and the conformal band.
* `ds02_rows.parquet` — one row per downsampled telemetry row: the four
  operating conditions and the fourteen physical channels, with their real names.
* `cache_manifest.json` — provenance: the bundle's SHA-256, the window contract,
  per-unit counts and the metric block.

Why a cache at all: the HDF5 is 2.3 GB and importing Keras costs seconds. The UI
only needs 6 196 scored windows and 12 538 telemetry rows, so the presentation
machine needs neither. Nothing under `models/` is written — the bundle is opened
read-only and the cache lives with the UI, per the repository rule that `models/`
is immutable.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

from ds02_rul.data import load_ds02  # noqa: E402
from ds02_rul.inference import raw_windows  # noqa: E402
from ds02_rul.metrics import evaluate_predictions, macro_rmse  # noqa: E402
from ds02_rul.persistence import load_ensemble, sha256_of  # noqa: E402

DEFAULT_OUT = os.path.join("app", "cache")
ENSEMBLE = os.path.join("models", "ensemble.joblib")
MANIFEST = os.path.join("models", "ds02_manifest.json")
PARQUET_TRAIN = os.path.join("data", "processed", "train_con_nulos.parquet")
PARQUET_TEST = os.path.join("data", "processed", "test_con_nulos.parquet")

BIN_EDGES = (0.0, 25.0, 50.0, 75.0)


def _raw_adaptada() -> dict:
    """Dict raw desde la base imputada (misma forma que devuelve `load_ds02`)."""
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    from src.clase.train_ensemble_adaptado import construir_raw_adaptado

    return construir_raw_adaptado()


def _fuente(raw: dict, base: str, stride: int, window: int, step: int,
            op_names: list, sensor_names: list) -> dict:
    """Bloque `source` del manifiesto: de dónde salieron exactamente las ventanas."""
    comun = {"stride": stride, "window": window, "step": step,
             "op_names": op_names, "sensor_names": sensor_names}
    if base == "adaptada":
        return {
            "base": "adaptada (MAR T30 + ffill causal, medianas de fit-units)",
            "parquet_train": PARQUET_TRAIN,
            "parquet_train_sha256": sha256_of(PARQUET_TRAIN),
            "parquet_test": PARQUET_TEST,
            "parquet_test_sha256": sha256_of(PARQUET_TEST),
            **comun,
        }
    return {"base": "limpia (HDF5 sin imputar)", "h5": raw["path"],
            "h5_sha256": sha256_of(raw["path"]), **comun}


def _unit_truth(A, y, unit: float, start_index: np.ndarray, window: int) -> np.ndarray:
    """Ground truth at each window's final row.

    A window ends on a specific downsampled row, so the target is read at
    `start_index + window - 1`. Averaging the whole window (or the whole cycle)
    would blur the target and make the cache's metrics incomparable to the ones
    the manifest records.
    """
    mask = A[:, 0] == unit
    y_unit = np.asarray(y[mask], dtype=np.float64)
    return y_unit[start_index + window - 1]


def _mae_by_band(y_true: np.ndarray, pred: np.ndarray) -> dict:
    """MAE per true-RUL band, the same cuts the reports use."""
    edges = list(BIN_EDGES) + [np.inf]
    out = {}
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (y_true >= lo) & (y_true < hi)
        key = f"[{lo:.0f}, {hi:.0f})" if np.isfinite(hi) else f"[{lo:.0f}, inf)"
        out[key] = {
            "windows": int(mask.sum()),
            "mae": round(float(np.mean(np.abs(pred[mask] - y_true[mask]))), 4)
            if mask.any()
            else None,
        }
    return out


def _density_reference(raw: dict) -> float:
    """Rows per flight cycle on the fit engines, as a comparison baseline."""
    A = raw["A_train"]
    densities = []
    for unit in np.unique(A[:, 0]):
        mask = A[:, 0] == unit
        densities.append(mask.sum() / float(A[mask, 1].max()))
    return float(np.mean(densities))


def build(out_dir: str = DEFAULT_OUT, stride: int = 100, step: int = 2,
          base: str = "adaptada") -> dict:
    """Construye los parquet de ventanas y filas y el manifiesto de procedencia."""
    if base == "adaptada":
        raw = _raw_adaptada()
    elif base == "limpia":
        raw = load_ds02(stride=stride)
    else:
        raise ValueError(f"base desconocida: {base!r} (usa 'adaptada' o 'limpia')")
    ensemble = load_ensemble(ENSEMBLE)
    window = int(ensemble.window_size)
    units = [float(u) for u in np.unique(raw["A_test"][:, 0])]

    op_names = list(raw["op_names"])
    sensor_names = list(raw["sensor_names"])

    window_frames = []
    for unit in units:
        X, cycles, uni, meta = raw_windows(
            raw["W_test"], raw["Xs_test"], raw["A_test"][:, 0], raw["A_test"][:, 1],
            window=window, step=step,
        )
        keep = uni == unit
        Xu, cycles_u, meta_u = X[keep], cycles[keep], meta[keep].reset_index(drop=True)
        point, lower, upper = ensemble.predict_interval(Xu, cycles_u, np.full(len(Xu), unit))
        window_frames.append(
            pd.DataFrame(
                {
                    "unit": int(unit),
                    "cycle": cycles_u.astype(np.int32),
                    "start_index": meta_u["start_index"].to_numpy(np.int32),
                    "y_true": _unit_truth(raw["A_test"], raw["y_test"], unit,
                                          meta_u["start_index"].to_numpy(), window),
                    "pred": point,
                    "lower": lower,
                    "upper": upper,
                }
            )
        )
    windows = pd.concat(window_frames, ignore_index=True)
    windows = windows.sort_values(["unit", "cycle", "start_index"], kind="stable").reset_index(drop=True)

    channels = pd.DataFrame(
        np.column_stack([raw["A_test"][:, 0], raw["A_test"][:, 1], raw["W_test"], raw["Xs_test"]]),
        columns=["unit", "cycle"] + op_names + sensor_names,
    )
    channels["unit"] = channels["unit"].astype(np.int32)
    channels["cycle"] = channels["cycle"].astype(np.int32)
    # Orden estable por (unit, cycle): la caché en disco es determinista y
    # coincide con el orden que la UI y los tests asumen.
    channels = channels.sort_values(["unit", "cycle"], kind="stable").reset_index(drop=True)

    y_true = windows["y_true"].to_numpy()
    pred = windows["pred"].to_numpy()
    unit_col = windows["unit"].to_numpy(dtype=float)

    metrics = macro_rmse(y_true, pred, unit_col)
    weighted_rmse = float(np.sqrt(np.mean((pred - y_true) ** 2)))
    per_unit = {}
    for unit in units:
        mask = unit_col == unit
        scored = evaluate_predictions(y_true[mask], pred[mask], f"Motor {int(unit)}")
        per_unit[str(int(unit))] = {
            "windows": int(mask.sum()),
            "rmse": round(float(scored["RMSE"]), 4),
            "mae": round(float(scored["MAE"]), 4),
            "bias": round(float(np.mean(pred[mask] - y_true[mask])), 4),
            "mae_by_band": _mae_by_band(y_true[mask], pred[mask]),
        }

    density_fit = _density_reference(raw)
    unit_rows = {}
    for unit in units:
        mask = channels["unit"].to_numpy() == unit
        life = float(channels.loc[mask, "cycle"].max())
        rows_per_cycle = float(mask.sum()) / life
        unit_rows[str(int(unit))] = {
            "rows": int(mask.sum()),
            "windows": int((unit_col == unit).sum()),
            "first_cycle": int(channels.loc[mask, "cycle"].min()),
            "last_cycle": int(life),
            "rows_per_cycle": round(rows_per_cycle, 2),
            "density_vs_fit": round(rows_per_cycle / density_fit, 3),
        }

    provenance = {
        "format_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "dataset": "DS02",
        "source": _fuente(raw, base, stride, window, step, op_names, sensor_names),
        "artifact": {
            "ensemble": ENSEMBLE,
            "ensemble_sha256": sha256_of(ENSEMBLE),
            "manifest": MANIFEST,
            "manifest_sha256": sha256_of(MANIFEST),
            "paradigm": getattr(ensemble, "paradigm", None),
            "beta": float(ensemble.beta),
            "ema_span": int(ensemble.ema_span),
            "conformal_target_coverage": float(
                (ensemble.conformal or {}).get("target_coverage", float("nan"))
            ),
        },
        "counts": {
            "windows": int(len(windows)),
            "rows": int(len(channels)),
            "units": unit_rows,
            "fit_engine_rows_per_cycle": round(density_fit, 2),
        },
        "metrics": {
            "rmse": round(weighted_rmse, 4),
            "mae": round(float(np.mean(np.abs(pred - y_true))), 4),
            "macro_rmse": round(float(metrics["macro_rmse"]), 4),
            "per_unit_rmse": {k: round(float(v), 4) for k, v in metrics["per_unit_rmse"].items()},
            "per_unit": per_unit,
            "mae_by_band": _mae_by_band(y_true, pred),
        },
        "defaults": {"threshold_airworthy": 30.0, "threshold_aog": 25.0},
    }

    os.makedirs(out_dir, exist_ok=True)
    windows_path = os.path.join(out_dir, "ds02_windows.parquet")
    rows_path = os.path.join(out_dir, "ds02_rows.parquet")
    prov_path = os.path.join(out_dir, "cache_manifest.json")

    windows.to_parquet(windows_path, index=False)
    channels.to_parquet(rows_path, index=False)
    # Hashes de contenido de la caché, calculados al build y firmados en el
    # manifest: la UI los verifica en cache_available y los usa para firmar
    # documentos (PDF), no los conteos.
    provenance["counts"]["windows_sha256"] = sha256_of(windows_path)
    provenance["counts"]["rows_sha256"] = sha256_of(rows_path)
    with open(prov_path, "w", encoding="utf-8") as fh:
        json.dump(provenance, fh, indent=2)

    return {
        "windows": windows_path,
        "rows": rows_path,
        "provenance": prov_path,
        "counts": provenance["counts"],
        "metrics": provenance["metrics"],
    }


def main() -> int:
    """CLI de la cache: --out, --stride, --step y --base."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default=DEFAULT_OUT, help="cache directory (default app/cache)")
    ap.add_argument("--stride", type=int, default=100, help="HDF5 row stride (default 100)")
    ap.add_argument("--step", type=int, default=2, help="window stride (default 2)")
    ap.add_argument("--base", choices=("adaptada", "limpia"), default="adaptada",
                    help="datos de origen: base imputada (default) o HDF5 limpio")
    args = ap.parse_args()

    result = build(out_dir=args.out, stride=args.stride, step=args.step, base=args.base)
    print(f"windows : {result['windows']}")
    print(f"rows    : {result['rows']}")
    print(f"prov    : {result['provenance']}")
    print("\ncounts")
    for unit, info in result["counts"]["units"].items():
        print(f"  unit {unit}: {info['windows']:5d} windows, {info['rows']:6d} rows, "
              f"life {info['last_cycle']:3d}, {info['rows_per_cycle']:6.2f} rows/cycle")
    print("\nmetrics (live, from the shipped bundle)")
    for k, v in result["metrics"]["per_unit"].items():
        print(f"  unit {k}: RMSE {v['rmse']:6.3f}  MAE {v['mae']:6.3f}  bias {v['bias']:+6.3f}")
    print(f"  macro-RMSE {result['metrics']['macro_rmse']:.4f}  "
          f"weighted RMSE {result['metrics']['rmse']:.4f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
