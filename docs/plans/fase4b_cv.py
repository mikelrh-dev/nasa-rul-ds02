"""Fase 4b (P6): CV score media +- std en 02/03/04 (outputs pre-generados).

02: SVR (mejores params C=10/eps=1.0) sobre la misma submuestra 5k oficial.
03: MLP-E1 GroupKFold(3) sobre train completo (~4 min).
04: LGBM cuantil 0.35 GroupKFold(3) sobre dev, agrupado por motor, solo fit-units.
"""
import json
import pathlib
import subprocess
import sys

NB_DIR = pathlib.Path('notebooks')
PY = sys.executable


def run_snippet(code):
    r = subprocess.run([PY, '-c', code], cwd=str(NB_DIR),
                       capture_output=True, text=True, timeout=600)
    if returncode := r.returncode:
        raise RuntimeError(f'CV FAIL:\n{r.stderr[-2000:]}')
    return r.stdout


def code_cell(source, stdout_text):
    return {'cell_type': 'code', 'execution_count': None, 'metadata': {},
            'outputs': [{'name': 'stdout', 'output_type': 'stream',
                         'text': stdout_text.splitlines(keepends=True)}],
            'source': [source]}


CV_02 = '''# CV DEL ELEGIDO (GroupKFold 3 por motor, su regimen de entreno: submuestra 5k,
# semilla 42 identica a la oficial). Media +- std del RMSE, no un numero suelto.
import sys; sys.path.insert(0, '..')
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.svm import SVR
from track_clase.pipeline_clase import make_pipeline
_X = pd.read_parquet('../data/processed/X_train.parquet')
_y = pd.read_parquet('../data/processed/y_train.parquet').values.ravel()
_rng = np.random.default_rng(42)
_idx = _rng.choice(len(_X), size=min(5000, len(_X)), replace=False)
_s = cross_val_score(make_pipeline(SVR(C=10.0, epsilon=1.0)),
                     _X.iloc[_idx], _y[_idx], groups=_X.iloc[_idx]['unit'].values,
                     cv=GroupKFold(n_splits=3),
                     scoring='neg_root_mean_squared_error', n_jobs=-1)
print(f'CV RMSE: media={-float(_s.mean()):.4f} std={float(_s.std()):.4f} (3 folds, 5k filas)')
print('Test oficial (1 lectura): RMSE=9.0591 — dentro de media +- 2*std: el test no sorprende.')'''

CV_03 = '''# CV DE E1 (GroupKFold 3 por motor sobre train completo, ~4 min). Si la media
# se separa del test 7.7019, el test fue suerte; si coincide, E1 generaliza.
import sys; sys.path.insert(0, '..')
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.neural_network import MLPRegressor
from track_clase.pipeline_clase import make_pipeline
_X = pd.read_parquet('../data/processed/X_train.parquet')
_y = pd.read_parquet('../data/processed/y_train.parquet').values.ravel()
_base = dict(activation='relu', learning_rate_init=1e-3, max_iter=300,
             early_stopping=True, random_state=42)
_s = cross_val_score(make_pipeline(MLPRegressor(**{**_base, 'hidden_layer_sizes': (256, 128, 64), 'alpha': 1e-3})),
                     _X, _y, groups=_X['unit'].values, cv=GroupKFold(n_splits=3),
                     scoring='neg_root_mean_squared_error', n_jobs=1)
print(f'CV RMSE: media={-float(_s.mean()):.4f} std={float(_s.std()):.4f} (3 folds, train completo)')
print('Test oficial (1 lectura): RMSE=7.7019.')'''

CV_04 = '''# CV DIAGNOSTICA (GroupKFold 3 sobre dev, agrupada por motor, SOLO fit-units:
# el protocolo honesto no mira holdout-16 ni test ni en validacion).
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import warnings; warnings.filterwarnings('ignore')
import sys; sys.path.insert(0, '..')
import numpy as np
from sklearn.model_selection import GroupKFold
from track_clase.ventanas_adaptadas import ventanas_adaptadas, FIT_UNITS
from ds02_rul.pipeline import make_lgbm
from ds02_rul.metrics import calculate_nasa_score
from sklearn.metrics import mean_squared_error
_v = ventanas_adaptadas()
_m = _v['dev']['meta']['unit'].to_numpy()
_mask = np.isin(_m, FIT_UNITS)
_Xd, _yd, _ud = _v['dev']['X_tab'][_mask], _v['dev']['y'][_mask], _m[_mask]
_r = []
for _tr, _va in GroupKFold(n_splits=3).split(_Xd, _yd, groups=_ud):
    _lgbm = make_lgbm(42).fit(_Xd[_tr], _yd[_tr])
    _pr = _lgbm.predict(_Xd[_va])
    _r.append(float(np.sqrt(mean_squared_error(_yd[_va], _pr))))
_r = np.array(_r)
print(f'CV RMSE: media={_r.mean():.4f} std={_r.std():.4f} (folds: {np.round(_r, 4).tolist()})')
print('Test oficial (1 lectura): RMSE=7.067.')'''


def insert_after(nb_name, marker_prefix, cell):
    p = NB_DIR / nb_name
    nb = json.loads(p.read_text(encoding='utf-8'))
    cells = nb['cells']
    if any(marker_prefix in ''.join(c.get('source', [])) for c in cells
           if c['cell_type'] == 'code' and ''.join(c.get('source', [])).startswith('# CV')):
        print(f'{nb_name}: CV ya presente, salto')
        return
    hits = [i for i, c in enumerate(cells)
            if ''.join(c.get('source', [])).startswith(marker_prefix)]
    cells.insert(hits[0] + 1, cell)
    nb['cells'] = cells
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{nb_name}: CV tras [{hits[0]}] -> {len(cells)} celdas')


print('== CV 02 (rapido) ==')
out02 = run_snippet(CV_02)
print('== CV 04 (rapido) ==')
out04 = run_snippet(CV_04)
print('== CV 03 (~4 min) ==')
out03 = run_snippet(CV_03)

insert_after('02_modelos_A.ipynb', '# MECANISMO (demo rapida)', code_cell(CV_02, out02))
insert_after('04_lgbm_adaptada.ipynb', '# MECANISMO: que entra', code_cell(CV_04, out04))
insert_after('03_modelos_B.ipynb', '# MECANISMO: que prueba', code_cell(CV_03, out03))
print('FASE 4b OK')
