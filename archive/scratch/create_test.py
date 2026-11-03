import json
ROOT="C:/Users/mikel/Desktop/Pruebas/nasa"
NB=ROOT+"/notebooks"
cell_src = '''# Descubrimiento robusto de la raiz del proyecto
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

import ds02_rul
import track_clase
print("ds02_rul:", ds02_rul.__file__)
print("track_clase:", track_clase.__file__ if hasattr(track_clase, "__file__") else "namespace")

from pathlib import Path
import numpy as np
art = _ROOT / "notebooks" / "ds02_ensemble" / "artifacts" / "nb1_dev.npz"
assert art.exists(), f"missing {art}"
d = np.load(art)
print("npz keys:", list(d.keys()))
print("[PATHING OK]")
'''
nb = {
 "cells": [{"cell_type":"code","execution_count":None,"metadata":{},"outputs":[],"source":cell_src.splitlines(keepends=True)}],
 "metadata":{"kernelspec":{"display_name":".venv (3.12.10)","language":"python","name":"ds02-venv"}},
 "nbformat":4,"nbformat_minor":5
}
with open(NB+"/00_test_pathing.ipynb","w",encoding="utf-8") as f:
    json.dump(nb,f,ensure_ascii=False,indent=1)
print("created test notebook")
