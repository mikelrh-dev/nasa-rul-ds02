#!/usr/bin/env python
"""Patch NB01-07 with the MLflow live header + log cell (no execution).

Idempotent nbformat edit: inserts the header block into cell 0 (before any
TF import), removes late ``TF_ENABLE_ONEDNN_OPTS`` lines, renames the OOF
``STEP_TRAIN`` shadow to ``STEP_TRAIN_OOF`` and appends one live-log cell
per notebook. Never executes a cell, never touches outputs/execution_count.

Run: python scripts/patch_mlflow_live_notebooks.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = sorted((ROOT / "notebooks").glob("0*.ipynb"))

HEADER_BLOCK = """
# --- MLflow live (mlflow-live-notebooks): env BEFORE any TF/Keras import ---
_os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
_os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
_os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")
_os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "1")
_os.environ.setdefault("OMP_NUM_THREADS", "1")
from ds02_rul.mlflow_live import log_live_run, persist_timings, setup_mlflow
setup_mlflow()
print("mlflow live: store=mlruns-live experiment=ds02-clase (fuente=live_notebook)")
"""

# One live-log cell per notebook, using only objects that notebook already
# produced in memory. Defensive globals().get so a re-run order change
# yields a params-only run instead of NameError.
LOG_CELLS = {
    "01_": '''# --- MLflow live: EDA run (params + counts; no training here) ---
from ds02_rul.mlflow_live import log_live_run, persist_timings
log_live_run(
    "live__nb01_eda",
    params={"notebook": "01_eda_y_contexto", "seed": 42},
    metrics={"n_train": float(len(globals().get("train", []))),
             "n_test": float(len(globals().get("test", [])))},
    notebook="01",
)
print("[NB01 MLflow live OK]")
''',
    "02_": '''# --- MLflow live: clasicos en vivo (_viva) + MLP (comp) ---
from ds02_rul.mlflow_live import log_live_run, persist_timings
_timing_rows = []
_viva = globals().get("_viva")
if _viva is not None:
    for _, _r in _viva.iterrows():
        _key = f"live__nb02_{_r['modelo']}"
        log_live_run(_key, params={"notebook": "02", "modelo": str(_r["modelo"])},
                     metrics={"rmse_val": float(_r["rmse_val"]),
                              "rmse_test": float(_r["rmse_test"])},
                     timings={"t_total": float(_r["tiempo_s"])}, notebook="02")
        _timing_rows.append({"run_key": _key, "t_lgb_s": None, "t_bilstm_s": None,
                             "tiempo_s": float(_r["tiempo_s"]), "fuente": "live_notebook"})
_comp = globals().get("comp")
if _comp is not None:
    for _, _r in _comp.iterrows():
        _key = f"live__nb02_mlp_{_r['experimento']}"
        log_live_run(_key, params={"notebook": "02", "experimento": str(_r["experimento"])},
                     metrics={"rmse_val": float(_r["rmse_val"]),
                              "rmse_test": float(_r["rmse_test"])},
                     timings={"t_total": float(_r["tiempo_s"])}, notebook="02")
        _timing_rows.append({"run_key": _key, "t_lgb_s": None, "t_bilstm_s": None,
                             "tiempo_s": float(_r["tiempo_s"]), "fuente": "live_notebook"})
persist_timings(_timing_rows, "nb02")
print("[NB02 MLflow live OK]")
''',
    "03_": '''# --- MLflow live: ablacion con tiempos (abl) ---
from ds02_rul.mlflow_live import log_live_run, persist_timings
_abl = globals().get("abl")
_timing_rows = []
if _abl is not None:
    for _, _r in _abl.iterrows():
        _key = f"live__nb03_{_r['model']}_{abs(hash(str(_r['variant']))) % 10000}"
        log_live_run(_key,
                     params={"notebook": "03", "variant": str(_r["variant"]),
                             "model": str(_r["model"]), "seed": 42, "window": 50,
                             "step_train": 3, "step_test": 2, "epochs": 22},
                     metrics={"rmse_test": float(_r["RMSE"]), "mae_test": float(_r["MAE"]),
                              "r2_test": float(_r["R2"]), "nasa_test": float(_r["NASA_Score"])},
                     timings={"t_lgb": float(_r["t_lgb_s"]), "t_lstm": float(_r["t_bilstm_s"]),
                              "t_total": float(_r["tiempo_s"])}, notebook="03")
        _timing_rows.append({"run_key": _key, "t_lgb_s": float(_r["t_lgb_s"]),
                             "t_bilstm_s": float(_r["t_bilstm_s"]),
                             "tiempo_s": float(_r["tiempo_s"]), "fuente": "live_notebook"})
persist_timings(_timing_rows, "nb03")
print("[NB03 MLflow live OK]")
''',
    "04_": '''# --- MLflow live: OOF + beta + macro (oof / selection / macro) ---
from ds02_rul.mlflow_live import log_live_run, persist_timings
_oof = globals().get("oof"); _sel = globals().get("selection"); _macro = globals().get("macro")
_timing_rows = [
    {"run_key": "live__nb04_oof", "t_lgb_s": None, "t_bilstm_s": None,
     "tiempo_s": float(sum(f["seconds"] for f in _oof.get("timing", []))) if _oof else None,
     "fuente": "live_notebook"}
]
log_live_run("live__nb04_oof",
             params={"notebook": "04", "seed": 42, "window": 50,
                     "step_train_oof": STEP_TRAIN_OOF, "epochs_oof": 15, "n_splits": 3},
             metrics={"beta": float(_sel["beta"]) if _sel is not None else float("nan"),
                      "macro_rmse": float(_macro) if _macro is not None else float("nan"),
                      "n_ventanas": float(len(_oof["y"])) if _oof else float("nan")},
             timings={"t_total": _timing_rows[0]["tiempo_s"]}, notebook="04")
persist_timings([r for r in _timing_rows if r["tiempo_s"] is not None], "nb04")
print("[NB04 MLflow live OK]")
''',
    "05_": '''# --- MLflow live: multisemilla (seed_rows / summary / per_seed) ---
from ds02_rul.mlflow_live import log_live_run, persist_timings
_summary = globals().get("summary"); _per_seed = globals().get("per_seed", [])
_timing_rows = []
if _summary is not None:
    for _label in ["LightGBM solo", "BiLSTM solo", "Híbrido + EMA5"]:
        _sub = _summary[_summary.Modelo == _label]
        if len(_sub):
            _sub = _sub.iloc[0]
            _key = f"live__nb05_{_label.replace(' ', '_').replace('+', 'plus')}"
            log_live_run(_key,
                         params={"notebook": "05", "seeds": "42,7,123", "window": 50,
                                 "step_train": 3, "step_test": 2, "epochs": 22},
                         metrics={"rmse_test": float(_sub["RMSE_mean"]),
                                  "rmse_std": float(_sub["RMSE_std"]),
                                  "nasa_test": float(_sub["NASA_Score_mean"])},
                         notebook="05")
for _row in _per_seed:
    _timing_rows.append({"run_key": f"live__nb05_seed_{_row['seed']}",
                         "t_lgb_s": None, "t_bilstm_s": None, "tiempo_s": None,
                         "fuente": "live_notebook"})
persist_timings(_timing_rows, "nb05")
print("[NB05 MLflow live OK]")
''',
    "06_": '''# --- MLflow live: bundle C en produccion (out / rows / macro / ms) ---
from ds02_rul.mlflow_live import log_live_run, persist_timings
_out = globals().get("out"); _rows = globals().get("rows", []); _macro = globals().get("macro")
_timing_rows = []
if _out is not None:
    _timing_rows.append({"run_key": "live__nb06_bundle_c",
                         "t_lgb_s": float(_out.get("t_lgb", float("nan"))),
                         "t_bilstm_s": float(_out.get("t_lstm", float("nan"))),
                         "tiempo_s": float(_out.get("t_total", float("nan"))),
                         "fuente": "live_notebook"})
_metrics = {"macro_rmse": float(_macro) if _macro is not None else float("nan")}
for _i, _r in enumerate(_rows):
    _metrics[f"rmse_test_{_i}"] = float(_r["RMSE"])
log_live_run("live__nb06_bundle_c",
             params={"notebook": "06", "seed": 42, "window": 50,
                     "step_train": 3, "step_test": 2, "epochs": 22,
                     "beta": float(globals().get("beta", float("nan")))},
             metrics=_metrics, timings=_out, notebook="06")
persist_timings([r for r in _timing_rows
                 if r["tiempo_s"] == r["tiempo_s"]], "nb06")
print("[NB06 MLflow live OK]")
''',
    "07_": '''# --- MLflow live: SHAP (params-only run; explanation, not training) ---
from ds02_rul.mlflow_live import log_live_run, persist_timings
_res = globals().get("res")
_metrics = {}
if isinstance(_res, dict):
    for _k in ("aditividad_max_error", "n_background", "n_explicadas"):
        if _k in _res:
            _metrics[_k] = float(_res[_k])
log_live_run("live__nb07_shap_c",
             params={"notebook": "07_shap_c_bundle_c", "seed": 42,
                     "n_filas": globals().get("N_FILAS", 200),
                     "n_fondo": globals().get("N_FONDO", 200)},
             metrics=_metrics, notebook="07")
print("[NB07 MLflow live OK]")
''',
}


def _src(cell) -> str:
    return "".join(cell.get("source", []))


def _set_src(cell, text: str) -> None:
    cell["source"] = text.splitlines(keepends=True)


def patch_notebook(path: Path) -> bool:
    """Inyecta cabecera, celda live y persistencia de tiempos en un notebook."""
    changed = False
    nb = json.loads(path.read_text(encoding="utf-8"))
    cells = nb["cells"]

    # 1) header in cell 0 (idempotent)
    header = _src(cells[0])
    if "setup_mlflow" not in header:
        if not header.endswith("\n"):
            header += "\n"
        _set_src(cells[0], header + HEADER_BLOCK)
        changed = True

    # 2) remove late TF_ENABLE_ONEDNN_OPTS lines (keep TF_CPP_MIN_LOG_LEVEL)
    for idx, cell in enumerate(cells):
        if idx == 0 or cell.get("cell_type") != "code":
            continue
        src = _src(cell)
        if "TF_ENABLE_ONEDNN_OPTS" not in src:
            continue
        # only drop executable assignment lines; comment mentions stay clean
        lines = [ln for ln in src.splitlines(True)
                 if "TF_ENABLE_ONEDNN_OPTS" not in ln or ln.lstrip().startswith("#")]
        new_src = "".join(lines)
        # drop any residual comment that still names the var to keep the
        # static contract simple (var lives only in cell 0)
        new_src = "".join(
            ln for ln in new_src.splitlines(True)
            if "TF_ENABLE_ONEDNN_OPTS" not in ln
        )
        if new_src != src:
            _set_src(cell, new_src)
            changed = True

    # 3) STEP_TRAIN_OOF rename (NB04 OOF shadow + NB06 OOF literal)
    for cell in cells:
        if cell.get("cell_type") != "code":
            continue
        src = _src(cell)
        new_src = src
        if "STEP_TRAIN = 1" in new_src:
            new_src = new_src.replace("STEP_TRAIN = 1", "STEP_TRAIN_OOF = 1")
            new_src = new_src.replace("step_train=STEP_TRAIN,", "step_train=STEP_TRAIN_OOF,")
        if "oof_base_predictions" in new_src and "step_train=3" in new_src:
            # NB06 OOF literal -> named constant (only in the OOF call)
            new_src = new_src.replace("step_train=3,", "step_train=STEP_TRAIN_OOF,", 1)
            if "STEP_TRAIN_OOF = 3" not in new_src:
                new_src = "STEP_TRAIN_OOF = 3  # OOF protocol (distinct from STEP_TRAIN=3 bundle)\n" + new_src
        if new_src != src:
            _set_src(cell, new_src)
            changed = True

    # 4) append live-log cell (idempotent marker)
    body = "\n".join(_src(c) for c in cells)
    if "MLflow live OK" not in body:
        key = next((k for k in LOG_CELLS if path.name.startswith(k)), None)
        if key is None:
            raise SystemExit(f"sin celda live para {path.name}")
        cells.append({
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": LOG_CELLS[key].splitlines(keepends=True),
        })
        changed = True

    if changed:
        raw = path.read_bytes()
        newline = b"\r\n" if b"\r\n" in raw else b"\n"
        text = json.dumps(nb, ensure_ascii=False, indent=1)
        text = text.replace("\r\n", "\n").replace("\n", newline.decode("ascii"))
        path.write_bytes((text + newline.decode("ascii")).encode("utf-8"))
    return changed


def main() -> int:
    """Aplica el parche a NB01-NB07 y escribe los ficheros."""
    for path in NOTEBOOKS:
        changed = patch_notebook(path)
        print(f"{path.name}: {'patched' if changed else 'already patched'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
