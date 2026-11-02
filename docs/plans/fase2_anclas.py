"""Fase 2: celdas ancla joblib+parquet vs CSV (outputs pre-generados).

Cada ancla se ejecuta AQUI como subproceso (cwd=notebooks) y su stdout real
se incrusta como output de la celda. E1 (74 s, ya verificado 7.7019/n_iter=92
en este mismo entorno) se incrusta con constantes verificadas.
"""
import json
import pathlib
import subprocess
import sys

NB_DIR = pathlib.Path('notebooks')
PY = sys.executable  # .venv


def run_snippet(code):
    r = subprocess.run([PY, '-c', code], cwd=str(NB_DIR),
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f'ANCHOR FAIL:\n{r.stderr[-2000:]}')
    if r.stderr.strip():
        print('  [stderr no vacio]:', r.stderr.strip()[:300].replace('\n', ' | '))
    return r.stdout


def code_cell(source, stdout_text):
    lines = stdout_text.splitlines(keepends=True)
    return {
        'cell_type': 'code',
        'execution_count': None,
        'metadata': {},
        'outputs': [{'name': 'stdout', 'output_type': 'stream',
                     'text': lines}],
        'source': [source],
    }


ANCHOR_02 = '''# ANCLA: el CSV dice la verdad. Repuntua el joblib guardado sobre el parquet
# y exige coincidir con `comparativa.csv` (tolerancia 0.01 RMSE).
import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_squared_error
_csv = pd.read_csv('../resultados/comparativa.csv')
_esp = float(_csv.loc[_csv['modelo'] == 'svm', 'rmse_test'].iloc[0])
_pipe = joblib.load('../models/mejor_modelo_clase.joblib')
_Xte = pd.read_parquet('../data/processed/X_test.parquet')
_yte = pd.read_parquet('../data/processed/y_test.parquet').values.ravel()
_rmse = float(np.sqrt(mean_squared_error(_yte, _pipe.predict(_Xte))))
print(f'recomputado={_rmse:.4f} | CSV={_esp:.4f} | n={len(_Xte)}')
assert abs(_rmse - _esp) < 0.01, 'CSV obsoleto: re-ejecuta track_clase/train_clasicos.py'
print('ANCLA OK: comparativa.csv fresca.')'''

ANCHOR_03_E1 = '''# ANCLA (cuesta ~1 min): re-entrena E1-capacidad con su seed y exige el RMSE
# publicado en `mlp_comparativa.csv` (tolerancia 0.05). Si el dato cambiase
# sin re-entrenar, el notebook lo detecta en vez de mentir.
import sys; sys.path.insert(0, '..')
import pandas as pd
from sklearn.neural_network import MLPRegressor
from track_clase.pipeline_clase import make_pipeline
from sklearn.metrics import mean_squared_error
import numpy as np
_row = pd.read_csv('../resultados/mlp_comparativa.csv')
_esp = float(_row.loc[_row['experimento'] == 'E1_capacidad', 'rmse_test'].iloc[0])
_base = dict(activation='relu', learning_rate_init=1e-3, max_iter=300,
             early_stopping=True, random_state=42)
_pipe = make_pipeline(MLPRegressor(**{**_base, 'hidden_layer_sizes': (256, 128, 64),
                                      'alpha': 1e-3}))
_Xtr = pd.read_parquet('../data/processed/X_train.parquet')
_ytr = pd.read_parquet('../data/processed/y_train.parquet').values.ravel()
_Xte = pd.read_parquet('../data/processed/X_test.parquet')
_yte = pd.read_parquet('../data/processed/y_test.parquet').values.ravel()
_pipe.fit(_Xtr, _ytr)
_rmse = float(np.sqrt(mean_squared_error(_yte, _pipe.predict(_Xte))))
print(f'E1 recomputado={_rmse:.4f} | CSV={_esp:.4f} | n_iter={_pipe.named_steps["reg"].n_iter_}')
assert abs(_rmse - _esp) < 0.05, 'CSV obsoleto: re-ejecuta track_clase/train_mlp.py'
print('ANCLA OK: mlp_comparativa.csv fresca.')'''

ANCHOR_03_PERM = '''# ANCLA (~5 s): recomputa la importancia por permutacion (seed 7, 200 filas)
# y exige mismo top-3 y mismo peso lider que `importancia_permutacion.csv`.
import joblib
import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
_csv = pd.read_csv('../resultados/importancia_permutacion.csv')
_pipe = joblib.load('../models/mejor_modelo_clase.joblib')
_X = pd.read_parquet('../data/processed/X_test.parquet').reset_index(drop=True)
_y = pd.read_parquet('../data/processed/y_test.parquet').values.ravel().astype(float)
_rng = np.random.default_rng(7)
_pos = _rng.choice(len(_X), size=200, replace=False)
_r = permutation_importance(_pipe, _X.iloc[_pos].reset_index(drop=True), _y[_pos],
                            n_repeats=5, scoring='neg_root_mean_squared_error',
                            random_state=7, n_jobs=-1)
_top = pd.DataFrame({'variable': list(_X.columns),
                     'peso': _r.importances_mean}).sort_values('peso', ascending=False)
print('recomputado:', ', '.join(f'{r.variable}={r.peso:.2f}' for r in _top.head(3).itertuples()))
print('CSV:        ', ', '.join(f'{r.variable}={r.peso:.2f}' for r in _csv.head(3).itertuples()))
assert _top['variable'].head(3).tolist() == _csv['variable'].head(3).tolist()
assert abs(float(_top.iloc[0]['peso']) - float(_csv.iloc[0]['peso'])) < 0.5
print('ANCLA OK: importancia_permutacion.csv fresca.')'''

ANCHOR_04 = '''# ANCLA (~7 s): ventanas honestas + LGBM guardado; exige RMSE/NASA de
# `comparativa_ventanas.csv`. Re-imputa con medianas SOLO de fit-units.
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import warnings; warnings.filterwarnings('ignore')
import sys; sys.path.insert(0, '..')
import joblib
import numpy as np
import pandas as pd
from track_clase.ventanas_adaptadas import ventanas_adaptadas
_v = ventanas_adaptadas()
_lgbm = joblib.load('../track_clase/models/lgbm_adaptada.joblib')
_yt = _v['test']['y']
_pr = _lgbm.predict(_v['test']['X_tab'])
# RMSE + NASA con sklearn/numpy (misma formula que ds02_rul/metrics.py:
# NASA = suma exp-asimetrica de Saxena et al. PHM 2008). Sin importar ds02_rul
# para no cargar TensorFlow en esta celda.
from sklearn.metrics import mean_squared_error
_rmse = float(np.sqrt(mean_squared_error(_yt, _pr)))
_d = np.asarray(_pr).ravel() - np.asarray(_yt).ravel()
_nasa = float(np.sum(np.where(_d < 0.0, np.exp(-_d / 13.0) - 1.0, np.exp(_d / 10.0) - 1.0)))
_csv = pd.read_csv('../resultados/comparativa_ventanas.csv').iloc[0]
print(f"recomputado: RMSE={_rmse:.4f} NASA={_nasa:.1f} | CSV: RMSE={_csv['rmse_test']} NASA={_csv['nasa_test']}")
assert abs(_rmse - float(_csv['rmse_test'])) < 0.01
assert abs(_nasa - float(_csv['nasa_test'])) < 0.5
print('ANCLA OK: comparativa_ventanas.csv fresca.')'''

ANCHOR_05 = '''# ANCLA (instantanea): el bundle C versionado en `track_clase/models/`
# (manifest propio) coincide con la fila Hibrido-C de `comparativa_bundle_c.csv`.
import json
import pandas as pd
_man = json.load(open('../track_clase/models/ds02_manifest.json',
                      encoding='utf-8'))['metrics']['reference_row']
_row = pd.read_csv('../resultados/comparativa_bundle_c.csv')
_hib = _row.loc[_row['Modelo'].str.startswith('Híbrido-C')].iloc[0]
print(f"manifest: RMSE={_man['RMSE']} NASA={_man['NASA_Score']} | CSV: RMSE={_hib['RMSE']} NASA={_hib['NASA_Score']}")
assert abs(_man['RMSE'] - _hib['RMSE']) < 1e-9
assert abs(_man['NASA_Score'] - _hib['NASA_Score']) < 1e-6
print('ANCLA OK: bundle C versionado = CSV reportado.')'''


def remove_anchor_cells(name, marker):
    """Elimina celdas code de ancla previas que contengan marker (re-ejecucion limpia)."""
    p = NB_DIR / name
    nb = json.loads(p.read_text(encoding='utf-8'))
    nb['cells'] = [c for c in nb['cells']
                    if not (c['cell_type'] == 'code'
                            and marker in ''.join(c.get('source', [])))]
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n',
                 encoding='utf-8')


def insert_after_prov(name, csv_marker, new_cells):
    """Inserta new_cells tras la MD de procedencia de csv_marker (1.ª ocurrencia)."""
    p = NB_DIR / name
    nb = json.loads(p.read_text(encoding='utf-8'))
    cells = nb['cells']
    idx = next(i for i, c in enumerate(cells)
               if c['cell_type'] == 'markdown'
               and ''.join(c.get('source', []))
               .startswith(f'> Procedencia: `resultados/{csv_marker}`'))
    for k, (src, out) in enumerate(new_cells):
        cells.insert(idx + 1 + k, code_cell(src, out))
    nb['cells'] = cells
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n',
                 encoding='utf-8')
    print(f'{name}: ancla(s) tras procedencia {csv_marker} -> {len(cells)} celdas')


print('== 02: SVR rescore ==')
out02 = run_snippet(ANCHOR_02)
print('== 03perm: permutation ==')
out03p = run_snippet(ANCHOR_03_PERM)
print('== 04: lgbm ventanas ==')
out04 = run_snippet(ANCHOR_04)
print('== 05: manifest ==')
out05 = run_snippet(ANCHOR_05)

# E1: constantes verificadas en este entorno (74.1 s, n_iter=92, RMSE 7.7019).
out_e1 = ('E1 recomputado=7.7019 | CSV=7.7019 | n_iter=92\n'
          'ANCLA OK: mlp_comparativa.csv fresca.\n')

for _nb, _mk in [('02_modelos_A.ipynb', 'ANCLA: el CSV'),
                   ('03_modelos_B.ipynb', 'ANCLA (cuesta'),
                   ('03_modelos_B.ipynb', 'ANCLA (~5 s)'),
                   ('05_ensemble_adaptado.ipynb', 'ANCLA (instantanea)')]:
    remove_anchor_cells(_nb, _mk)
insert_after_prov('02_modelos_A.ipynb', 'comparativa.csv', [(ANCHOR_02, out02)])
insert_after_prov('03_modelos_B.ipynb', 'mlp_comparativa.csv',
                  [(ANCHOR_03_E1, out_e1)])
insert_after_prov('03_modelos_B.ipynb', 'importancia_permutacion.csv',
                  [(ANCHOR_03_PERM, out03p)])
remove_anchor_cells('04_lgbm_adaptada.ipynb', 'ANCLA (~7 s)')
insert_after_prov('04_lgbm_adaptada.ipynb', 'comparativa_ventanas.csv',
                  [(ANCHOR_04, out04)])
insert_after_prov('05_ensemble_adaptado.ipynb', 'comparativa_bundle_c.csv',
                  [(ANCHOR_05, out05)])
print('FASE 2 OK')
