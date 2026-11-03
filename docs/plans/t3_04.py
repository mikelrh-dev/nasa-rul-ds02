"""T3 — 04: LGBM entrenado en vivo (sin escrituras), estilo viejo."""
import json
import pathlib
import subprocess
import sys

NB = pathlib.Path('notebooks/04_lgbm_adaptada.ipynb')
PY = sys.executable

TRAIN_LGBM = '''# ENTRENO EN VIVO (mismo codigo que `track_clase/train_lgbm_adaptada.py`,
# sin escribir CSV ni joblib: el modelo vive solo en esta celda).
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import warnings; warnings.filterwarnings('ignore')
import sys; sys.path.insert(0, '..')
import time
import numpy as np
import pandas as pd
from track_clase.ventanas_adaptadas import FIT_UNITS, ventanas_adaptadas
from ds02_rul.metrics import evaluate_predictions
from ds02_rul.pipeline import make_lgbm
_v = ventanas_adaptadas()
_dev, _test = _v['dev'], _v['test']
_wunits = _dev['meta']['unit'].to_numpy()
_fit = np.where(np.isin(_wunits, FIT_UNITS))[0]
_t0 = time.time()
_lgbm = make_lgbm(42).fit(_dev['X_tab'][_fit], _dev['y'][_fit])
_secs = time.time() - _t0
_m = evaluate_predictions(_test['y'], _lgbm.predict(_test['X_tab']), 'LGBM-adaptada')
_csv = pd.read_csv('../resultados/comparativa_ventanas.csv').iloc[0]
print(f"entrenado en {_secs:.1f}s sobre {len(_fit)} ventanas fit-units")
print(f"vivo: RMSE={float(_m['RMSE']):.4f} NASA={float(_m['NASA_Score']):.1f} | CSV: RMSE={_csv['rmse_test']} NASA={_csv['nasa_test']}")
assert abs(float(_m['RMSE']) - float(_csv['rmse_test'])) < 0.01
assert abs(float(_m['NASA_Score']) - float(_csv['nasa_test'])) < 0.5
print('TABLA OK: el notebook calcula lo mismo que el CSV archivado.')'''

MD_QUEVEMOS = '''## Qué vemos (números del entreno en vivo)

- LGBM-adaptada **7.067** vs B-histórico **7.098** (spread B ±0.034): el MAR+ffill **no degrada** la rama tabular. La diferencia (0.031) cabe dentro del ruido entre semillas.
- La puerta del 04 se abre: el plumbing honesto funciona y el coste del dropout es ~0. Entrar al BiLSTM en 05 está justificado.'''


def run_snippet(code):
    r = subprocess.run([PY, '-c', code], cwd='notebooks',
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f'T3 FAIL:\n{r.stderr[-2000:]}')
    if r.stderr.strip():
        print('  [stderr]:', r.stderr.strip()[:200].replace('\n', ' | '))
    return r.stdout


print('== train lgbm (~10 s) ==')
out = run_snippet(TRAIN_LGBM)

nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']
cells = [c for c in cells
         if not (c['cell_type'] == 'code'
                 and '# ANCLA (~7 s)' in ''.join(c.get('source', [])))]
nb['cells'] = cells
idx = next(i for i, c in enumerate(cells)
           if c['cell_type'] == 'markdown'
           and ''.join(c.get('source', []))
           .startswith('> Procedencia: `resultados/comparativa_ventanas.csv`'))
cell = {'cell_type': 'code', 'execution_count': None, 'metadata': {},
        'outputs': [{'name': 'stdout', 'output_type': 'stream',
                     'text': out.splitlines(keepends=True)}],
        'source': [TRAIN_LGBM]}
cells.insert(idx + 1, cell)
cells.insert(idx + 2, {'cell_type': 'markdown', 'metadata': {},
                       'source': [MD_QUEVEMOS]})
nb['cells'] = cells
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'04: {len(cells)} celdas. T3 insertado.')
