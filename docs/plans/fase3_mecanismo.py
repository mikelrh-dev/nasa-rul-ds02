"""Fase 3: mecanismo visible en 02/03/04/05 (outputs pre-generados).

- 02: GridSearch-fast (2k filas, 2 folds, grids reducidos) + MD SVR-5k.
- 03: EXPS dict visible (importado de train_mlp, sin re-entrenar).
- 04: shapes/particion/contrato-93 de ventanas_adaptadas.
- 05: MD esquema + tabla final reconstruida en vivo y comparada con el CSV.
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
    if r.returncode != 0:
        raise RuntimeError(f'MECHANISM FAIL:\n{r.stderr[-2000:]}')
    if r.stderr.strip():
        print('  [stderr]:', r.stderr.strip()[:200].replace('\n', ' | '))
    return r.stdout


def md_cell(source):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': [source]}


def code_cell(source, stdout_text):
    return {'cell_type': 'code', 'execution_count': None, 'metadata': {},
            'outputs': [{'name': 'stdout', 'output_type': 'stream',
                         'text': stdout_text.splitlines(keepends=True)}],
            'source': [source]}


def insert_after(nb_name, marker_prefix, new_cells, occurrence=0):
    p = NB_DIR / nb_name
    nb = json.loads(p.read_text(encoding='utf-8'))
    cells = nb['cells']
    hits = [i for i, c in enumerate(cells)
            if ''.join(c.get('source', [])).startswith(marker_prefix)]
    idx = hits[occurrence]
    for k, cell in enumerate(new_cells):
        cells.insert(idx + 1 + k, cell)
    nb['cells'] = cells
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n',
                 encoding='utf-8')
    print(f'{nb_name}: insertado tras [{idx}] {marker_prefix[:50]!r} -> {len(cells)} celdas')


def remove_marked(nb_name, marker):
    p = NB_DIR / nb_name
    nb = json.loads(p.read_text(encoding='utf-8'))
    nb['cells'] = [c for c in nb['cells']
                    if marker not in ''.join(c.get('source', []))]
    p.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n',
                 encoding='utf-8')


# ---------------- 02: GridSearch-fast ----------------
FAST_02 = '''# MECANISMO (demo rapida): el mismo Pipeline(pre, reg) + GroupKFold por motor,
# en 2000 filas y 2 folds con grids reducidos. Los numeros oficiales (grid
# completo, 3 folds) viven en `comparativa.csv` y estan anclados arriba.
import sys; sys.path.insert(0, '..')
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, GridSearchCV
from sklearn.linear_model import Ridge
from sklearn.neighbors import KNeighborsRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR
from xgboost import XGBRegressor
from track_clase.pipeline_clase import make_pipeline
_X = pd.read_parquet('../data/processed/X_train.parquet')
_y = pd.read_parquet('../data/processed/y_train.parquet').values.ravel()
_mu = _X.sample(2000, random_state=0).index
_Xm, _ym = _X.loc[_mu], _y[_X.index.get_indexer(_mu)]
print('filas demo:', len(_Xm), '| grupos (unit):', sorted(_Xm['unit'].unique().tolist()))
ESP_DEMO = {
    'regresion': (Ridge(random_state=42), {'reg__alpha': [0.1, 10.0]}),
    'knn': (KNeighborsRegressor(), {'reg__n_neighbors': [5, 31]}),
    'rf': (RandomForestRegressor(n_estimators=50, random_state=42, n_jobs=-1), {'reg__max_depth': [8, None]}),
    'xgb': (XGBRegressor(n_estimators=100, max_depth=4, learning_rate=0.05, subsample=0.8, n_jobs=-1, random_state=42, verbosity=0), {'reg__max_depth': [4, 6]}),
    'svm': (SVR(), {'reg__C': [0.5, 2.0]}),
}
for _nombre, (_reg, _grid) in ESP_DEMO.items():
    _gs = GridSearchCV(make_pipeline(_reg), _grid,
                       cv=GroupKFold(n_splits=2), scoring='neg_root_mean_squared_error', n_jobs=-1)
    _gs.fit(_Xm, _ym, groups=_Xm['unit'].values)
    print(f'{_nombre}: mejor={_gs.best_params_} RMSE_cv={-float(_gs.best_score_):.4f}')
print('MECANISMO OK: un Pipeline(pre, reg) por modelo, CV agrupada por motor.')'''

MD_SVR = '''> Nota de coste (por que el SVR oficial va en submuestra 5k): el SVR con kernel RBF
> es O(n²) en memoria/tiempo; en 52k filas es inviable en un portatil. El oficial se
> entrena en 5000 filas estratificadas por motor (`track_clase/train_clasicos.py`).
> El resto de modelos ven el train completo.'''

# ---------------- 03: EXPS visible ----------------
EXPS_03 = '''# MECANISMO: que prueba cada experimento MLP (definicion unica en
# `track_clase/train_mlp.py`; el notebook la muestra, no la duplica).
import sys; sys.path.insert(0, '..')
from track_clase.train_mlp import EXPS, BASE_KW
print('BASE:', BASE_KW)
for _k, (_kw, _hip) in EXPS.items():
    print(f'- {_k}: {_kw}')
    print(f'  hipotesis: {_hip}')'''

# ---------------- 04: shapes ----------------
SHAPES_04 = '''# MECANISMO: que entra por arriba del pipeline honesto (sin entrenar nada aqui).
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import warnings; warnings.filterwarnings('ignore')
import sys; sys.path.insert(0, '..')
from track_clase.ventanas_adaptadas import ventanas_adaptadas, FIT_UNITS, HOLDOUT_UNITS, TEST_UNITS
_v = ventanas_adaptadas()
print('fit-units (todo se ajusta aqui):', FIT_UNITS)
print('holdout-16 (reserva beta):', HOLDOUT_UNITS, '| test:', TEST_UNITS)
print('dev :', _v['dev']['X_tab'].shape, '| test:', _v['test']['X_tab'].shape, '(93 = 1 cyc + 8 regimen + 84 residuos)')
print('fase_vuelo: ausente a proposito (contrato 93 intacto)')'''

# ---------------- 05: esquema + tabla viva ----------------
MD_ESQUEMA_05 = '''## El camino completo C (que funcion se encarga de cada paso)

La base adaptada entra **por arriba** del pipeline honesto y a partir de ahi el
protocolo es el mismo que el de B, sin cambios (`track_clase/train_ensemble_adaptado.py`):

1. `construir_raw_adaptado()` — parquet MAR+ffill a dict raw (W/Xs/y/units/cycles).
2. `run_seed(seed)` — residualizacion Ridge + ventanas 50 + BiLSTM (triple pooling) y LGBM cuantil 0.35.
3. `oof_base_predictions` + `select_beta_grouped` — beta calibrada por OOF agrupado por motor.
4. `fit_meta_learners` — stacking RidgeCV + LightGBM sobre `[p_lstm, p_lgb]`.
5. `HybridStackingEnsemble(beta=1.00)` + `causal_ema_by_unit(span=5)` — ensemble + suavizado causal.
6. `fit_conformal` — banda asimetrica propia (manifest en `track_clase/models/`).

Como se construyo B (el extra no visto en clase): `notebooks/ds02_ensemble/01 -> 02 -> 03`
(residualizacion, ablacion cyc_norm, OOF, beta, EMA, conformal, multiseed). Este 05 no lo
repite: lo cita y lo compara en las mismas 6.196 ventanas.'''

TABLA_VIVA_05 = '''# TABLA VIVA: reconstruida aqui desde los 4 CSV de familia (misma funcion que
# `track_clase/tabla_final.py`) y exigida identica al CSV archivado.
import sys; sys.path.insert(0, '..')
import pandas as pd
from track_clase.tabla_final import construir_tabla
_viva = construir_tabla(pd.read_csv('../resultados/comparativa.csv'),
                        pd.read_csv('../resultados/mlp_comparativa.csv'),
                        pd.read_csv('../resultados/comparativa_ventanas.csv'),
                        pd.read_csv('../resultados/comparativa_bundle_c.csv'))
_arch = pd.read_csv('../resultados/tabla_final_clase.csv')
pd.testing.assert_frame_equal(_viva.reset_index(drop=True), _arch.reset_index(drop=True))
print(_viva[['modelo', 'grano', 'rmse_test', 'mae_test', 'r2_test']].to_string(index=False))
print()
print('Campeon grano fila :', _viva.loc[_viva['grano'] == 'fila'].sort_values('rmse_test').iloc[0]['modelo'])
print('Campeon grano ventana:', _viva.loc[_viva['grano'] == 'ventana'].sort_values('rmse_test').iloc[0]['modelo'])
print('TABLA VIVA OK: la conclusion del notebook se deriva en vivo, sin ranking mixto.')'''

print('== 02 fast ==')
out_fast = run_snippet(FAST_02)
print('== 03 exps ==')
out_exps = run_snippet(EXPS_03)
print('== 04 shapes ==')
out_shapes = run_snippet(SHAPES_04)
print('== 05 tabla viva ==')
out_tabla = run_snippet(TABLA_VIVA_05)

for nb, mk in [('02_modelos_A.ipynb', '# MECANISMO (demo rapida)'),
               ('03_modelos_B.ipynb', '# MECANISMO: que prueba'),
               ('04_lgbm_adaptada.ipynb', '# MECANISMO: que entra'),
               ('05_ensemble_adaptado.ipynb', '# TABLA VIVA:')]:
    remove_marked(nb, mk)
remove_marked('02_modelos_A.ipynb', '> Nota de coste')
remove_marked('05_ensemble_adaptado.ipynb', '## El camino completo C')

insert_after('02_modelos_A.ipynb', '# ANCLA: el CSV dice la verdad',
             [code_cell(FAST_02, out_fast), md_cell(MD_SVR)], occurrence=0)
insert_after('03_modelos_B.ipynb', '> Procedencia: `resultados/mlp_comparativa.csv`',
             [code_cell(EXPS_03, out_exps)], occurrence=0)
insert_after('04_lgbm_adaptada.ipynb', '> Procedencia: `resultados/comparativa_ventanas.csv`',
             [code_cell(SHAPES_04, out_shapes)], occurrence=0)
insert_after('05_ensemble_adaptado.ipynb', '## Tabla final: dos ligas, dos campeones',
             [md_cell(MD_ESQUEMA_05)], occurrence=0)
insert_after('05_ensemble_adaptado.ipynb', '> Procedencia: `resultados/tabla_final_clase.csv`',
             [code_cell(TABLA_VIVA_05, out_tabla)], occurrence=0)
print('FASE 3 OK')
