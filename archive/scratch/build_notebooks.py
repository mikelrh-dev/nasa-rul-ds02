import json, copy, os

ROOT = "C:/Users/mikel/Desktop/Pruebas/nasa"
NB = ROOT + "/notebooks"

def load_nb(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

def deep(x):
    return copy.deepcopy(x)

DISCOVERY = """# Descubrimiento robusto de la raiz del proyecto (no usar ../ relativo)
import pathlib as _pl, os as _os, sys as _sys
_ROOT = _pl.Path().resolve()
while not (_ROOT / "pyproject.toml").exists() and _ROOT != _ROOT.parent:
    _ROOT = _ROOT.parent
_os.chdir(_ROOT)
if str(_ROOT) not in _sys.path:
    _sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in _sys.path:
    _sys.path.insert(0, str(_ROOT / "src"))
print("cwd:", _os.getcwd())
"""

DISCOVERY_CELL = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": DISCOVERY.splitlines(keepends=True),
}

PATH_PATTERNS = [
    "sys.path.insert(0, os.path.abspath('..'))",
    'sys.path.insert(0, os.path.abspath(".."))',
    "sys.path.insert(0, '..')",
    "sys.path.insert(0, \"..\")",
    "sys.path.insert(0, '../src')",
    "sys.path.insert(0, \"../src\")",
]

def transform_code(src):
    for pat in PATH_PATTERNS:
        src = src.replace(pat, "")
    # collapse leftover '../' relative paths to root-relative
    src = src.replace("../", "")
    return src

def transform_cell(cell):
    c = deep(cell)
    if c.get("cell_type") == "code":
        src = "".join(c.get("source", []))
        src = transform_code(src)
        c["source"] = src.splitlines(keepends=True)
        # ensure trailing newline
        if c["source"] and not c["source"][-1].endswith("\n"):
            c["source"][-1] += "\n"
    return c

def make_notebook(cells, transition_md=None):
    nb = {
        "cells": [deep(DISCOVERY_CELL)] + [transform_cell(c) for c in cells],
        "metadata": {
            "kernelspec": {
                "display_name": ".venv (3.12.10)",
                "language": "python",
                "name": "ds02-venv",
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    if transition_md:
        nb["cells"].append({
            "cell_type": "markdown",
            "metadata": {},
            "source": transition_md.splitlines(keepends=True),
        })
    return nb

def cells_of(nb, indices):
    out = []
    for i in indices:
        if i < 0 or i >= len(nb["cells"]):
            print("WARN: index", i, "out of range (nb has", len(nb["cells"]), "cells) - skipped")
            continue
        out.append(nb["cells"][i])
    return out

# Load sources
A = load_nb(NB + "/01_eda.ipynb")
B = load_nb(NB + "/02_modelos_A.ipynb")
C = load_nb(NB + "/03_modelos_B.ipynb")
D = load_nb(NB + "/04_lgbm_adaptada.ipynb")
E = load_nb(NB + "/05_ensemble_adaptado.ipynb")
F1 = load_nb(NB + "/ds02_ensemble/01_datos_y_bases.ipynb")
F2 = load_nb(NB + "/ds02_ensemble/02_decision_ablacion_oof_ensamble.ipynb")
F3 = load_nb(NB + "/ds02_ensemble/03_evidencia_multisemilla_diagnostico.ipynb")

def save(name, nb):
    path = NB + "/" + name
    with open(path, "w", encoding="utf-8") as f:
        json.dump(nb, f, ensure_ascii=False, indent=1)
    print("saved", path, "cells=", len(nb["cells"]))

# 01
cells = []
cells += [deep(c) for c in A["cells"]]  # all
# F1: 0-9,11,13,15,17,18,19-21,23 (18 added as EDA code matching md 17; 181 invalid skipped)
idx1 = list(range(0,10)) + [11,13,15,17,18] + list(range(19,22)) + [23]
cells += cells_of(F1, idx1)
nb = make_notebook(cells, "\n## Siguiente\nContinúa en `02_modelos_clasicos_y_mlp.ipynb`.\n")
save("01_eda_y_contexto.ipynb", nb)

# 02
cells = []
cells += [deep(c) for c in B["cells"]]
cells += [deep(c) for c in C["cells"]]
cells += cells_of(F1, list(range(19,24)))
nb = make_notebook(cells, "\n## Siguiente\nContinúa en `03_feature_engineering_secuencial.ipynb`.\n")
save("02_modelos_clasicos_y_mlp.ipynb", nb)

# 03
cells = []
cells += cells_of(F1, [10,12,14,16,18,20,22])
cells += cells_of(F2, [0,1,2,4,6,8])
nb = make_notebook(cells, "\n## Siguiente\nContinúa en `04_arquitectura_bilstm_oof.ipynb`.\n")
save("03_feature_engineering_secuencial.ipynb", nb)

# 04
cells = []
cells += cells_of(F2, [0,1,2,4,6,8,10,12,14,15,17,19,21,23,25,27,28,31])
nb = make_notebook(cells, "\n## Siguiente\nContinúa en `05_meta_ensemble_y_conformal.ipynb`.\n")
save("04_arquitectura_bilstm_oof.ipynb", nb)

# 05
cells = []
cells += cells_of(F3, [0,1,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32])
cells += cells_of(F2, [13,15,17,19,21,23,25,27,28,29,31])
cells += [deep(c) for c in D["cells"]]  # all 0-12
nb = make_notebook(cells, "\n## Siguiente\nContinúa en `06_evaluacion_produccion_comparativa.ipynb`.\n")
save("05_meta_ensemble_y_conformal.ipynb", nb)

# 06
cells = []
cells += [deep(c) for c in E["cells"]]  # all
cells += cells_of(F3, [34,36,38])
nb = make_notebook(cells, "\n## Cierre\nFin del recorrido. Artefactos reutilizados en `notebooks/ds02_ensemble/artifacts/`.\n")
save("06_evaluacion_produccion_comparativa.ipynb", nb)

print("DONE")
