"""Build `notebooks/07_shap_c_bundle_c.ipynb` (SHAP por ramas sobre el bundle C).

Pure `nbformat` emitter: writes cells as verbatim strings, executes nothing,
does not read the dataset and writes no artifacts. The notebook is a build
output; edit this file, never the `.ipynb`.

The notebook is thin on purpose: it only calls `ejecutar_shap_c`
(`src/ds02_rul/shap_c.py`, Fase 6) with the frozen bundle C
(`models/ensemble.joblib`, seed 42, read-only) and displays what the call
leaves in `resultados/shap_bundle_C/`. No retraining happens here, and
`models/` plus NB01-06 are never touched.

Execution (do it once the notebook is built)::

    PYTHONHASHSEED=42 TF_NUM_INTEROP_THREADS=1 TF_NUM_INTRAOP_THREADS=1 \\
    OMP_NUM_THREADS=1 .venv/Scripts/python.exe -m nbconvert --to notebook \\
    --execute --inplace --ExecutePreprocessor.kernel_name=ds02-venv \\
    --ExecutePreprocessor.timeout=3600 notebooks/07_shap_c_bundle_c.ipynb

`PYTHONHASHSEED` must be set on the launching process (it cannot be fixed
from inside the kernel); TF single-thread env vars are also set in the first
cell, before anything imports TensorFlow (lazy-load: TF only loads inside
`ejecutar_shap_c`). Jupyter NotebookLM-style markdown export
(`notebooksMD/`) is NOT done by this builder — the repo's builders never
export markdown either; generate it by hand with
`.venv/Scripts/python.exe -m nbconvert --to markdown` if needed.
"""
from __future__ import annotations

from pathlib import Path

import nbformat as nbf

CELLS = []


def md(text: str) -> None:
    """Devuelve una celda markdown para el notebook generado."""
    CELLS.append(nbf.v4.new_markdown_cell(text))


def code(text: str) -> None:
    """Devuelve una celda de codigo para el notebook generado."""
    CELLS.append(nbf.v4.new_code_cell(text))


code("""# Descubrimiento robusto de la raiz del proyecto (no usar ../ relativo)
import pathlib as _pl, os as _os, sys as _sys
_ROOT = _pl.Path().resolve()
while not (_ROOT / "pyproject.toml").exists() and _ROOT != _ROOT.parent:
    _ROOT = _ROOT.parent
_os.chdir(_ROOT)
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in _sys.path:
    _sys.path.insert(0, str(_ROOT / "src"))

# --- MLflow live (mlflow-live-notebooks): env BEFORE any TF/Keras import ---
_os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")
_os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")
_os.environ.setdefault("TF_NUM_INTEROP_THREADS", "1")
_os.environ.setdefault("TF_NUM_INTRAOP_THREADS", "1")
_os.environ.setdefault("OMP_NUM_THREADS", "1")
from ds02_rul.mlflow_live import log_live_run, persist_timings, setup_mlflow
setup_mlflow()
print("mlflow live: store=mlruns experiment=ds02-clase (fuente=live_notebook)")

# Entorno de ejecucion reproducible: TF en 1 hilo (antes de importar Keras/TF;
# `ejecutar_shap_c` carga el bundle con lazy-load dentro de la funcion).
_os.environ["TF_NUM_INTEROP_THREADS"] = "1"
_os.environ["TF_NUM_INTRAOP_THREADS"] = "1"
_os.environ["OMP_NUM_THREADS"] = "1"
_os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")

import shap as _shap
print("cwd:      ", _os.getcwd())
print("python:   ", _sys.version.split()[0])
print("shap:     ", _shap.__version__)
""")

md(r"""# 07 — SHAP por ramas sobre el bundle C

Cuaderno fino: no entrena nada. Llama a `ejecutar_shap_c`
(`src/ds02_rul/shap_c.py`) sobre el bundle C ya congelado
(`models/ensemble.joblib`, seed 42) en **solo lectura** y muestra lo que deja
en `resultados/shap_bundle_C/`: tres CSV de importancia, tres graficos de
barras y `metadata.json`.

- **BiLSTM**: Permutation agrupado por canal (19 canales de la ventana
  `(50,19)`; `DeepExplainer` no aplica en este entorno — ver nota en el
  modulo).
- **LGBM**: `TreeExplainer` interventional sobre las 93 features tabulares.
- **Meta**: `PermutationExplainer` sobre el ancho real del meta-aprendiz
  (2 = `[p_lstm, p_lgb]`).

Fondo: solo train del fold-0 del GroupKFold(3) por motor (sin test 11/14/15),
seed 42. EMA fuera: no se atribuye.

> SHAP describe el modelo, no el motor: asociaciones no causales.
""")

code("""import time

from src.ds02_rul.shap_c import ejecutar_shap_c

# Parametros documentados: tamano completo (mismo que N_FILAS/N_FONDO del modulo).
N_FILAS = 200
N_FONDO = 200
SEED = 42

t0 = time.time()
res = ejecutar_shap_c(n_filas=N_FILAS, n_fondo=N_FONDO, seed=SEED, verbose=True)
print(f"ejecutado en {time.time() - t0:.1f} s")
print("[NB07 OK]")
res
""")

code("""import json

import pandas as pd

OUT = "resultados/shap_bundle_C"

for nombre in ("shap_bilstm", "shap_lgbm", "shap_meta"):
    df = pd.read_csv(f"{OUT}/{nombre}.csv")
    print(f"== {nombre}.csv: {len(df)} filas x {len(df.columns)} columnas ==")
    print(df.head(5).to_string(index=False))
    print()

meta = json.load(open(f"{OUT}/metadata.json", encoding="utf-8"))
print(json.dumps({
    "shap_shapes": meta["shap_shapes"],
    "aditividad_max_error": meta["aditividad_max_error"],
    "n_background": meta["n_background"],
    "n_explicadas": meta["n_explicadas"],
    "nasa_sin_clamp": meta["nasa_sin_clamp"],
    "nota": meta["nota"],
}, indent=2, ensure_ascii=False))
""")

code("""from IPython.display import Image, display

for rama in ("bilstm", "lgbm", "meta"):
    print(f"== bar_{rama}.png ==")
    display(Image(f"resultados/shap_bundle_C/bar_{rama}.png"))
""")

md(r"""## Lectura y limites

- Los valores son importancias del modelo sobre la validacion fold-0:
  describen como el modelo reparte su salida, no el comportamiento del motor.
- La rama BiLSTM agrega por canal: se pierde el detalle dentro de la ventana
  de 50 pasos (limitacion declarada en `src/ds02_rul/shap_c.py`).
- La EMA de produccion queda fuera de la atribucion y no aparece en estos CSV.
- `resultados/shap_bundle_C/` se regenera al ejecutar la celda de SHAP;
  `models/` y NB01-06 no se tocan. Para reconstruir este cuaderno sin
  ejecutarlo: `python scripts/build/build_07_shap_c_notebook.py` (con el
  interprete del `.venv`).

> SHAP describe el modelo, no el motor: asociaciones no causales.
""")

code("""# --- MLflow live: SHAP (params-only run; explanation, not training) ---
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
""")

nb = nbf.v4.new_notebook()
nb.cells = CELLS
nb.metadata = {
    "kernelspec": {
        "display_name": ".venv (3.12.10)",
        "language": "python",
        "name": "python3",
    },
    "language_info": {
        "codemirror_mode": {"name": "ipython", "version": 3},
        "file_extension": ".py",
        "mimetype": "text/x-python",
        "name": "python",
        "nbconvert_exporter": "python",
        "pygments_lexer": "ipython3",
        "version": "3.12.10",
    },
}

destino = Path(__file__).resolve().parents[2] / "notebooks" / "07_shap_c_bundle_c.ipynb"
with open(destino, "w", encoding="utf-8") as fh:
    nbf.write(nb, fh)

print("Notebook regenerado:", destino, "-", len(CELLS), "celdas")
