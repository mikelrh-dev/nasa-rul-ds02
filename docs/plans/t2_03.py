"""T2 — 03: MLP base+E1/E2/E3 en vivo + SHAP vivo (sin escrituras salvo PNG)."""
import json
import pathlib
import subprocess
import sys

NB = pathlib.Path('notebooks/03_modelos_B.ipynb')
PY = sys.executable

FULL_MLP = '''# ENTRENO OFICIAL EN VIVO (mismo loop que `track_clase/train_mlp.py`,
# sin escribir CSV: todo queda en memoria y se exige igual al archivado).
import sys; sys.path.insert(0, '..')
import time
import numpy as np
import pandas as pd
from sklearn.neural_network import MLPRegressor
from track_clase.pipeline_clase import make_pipeline
from track_clase.train_mlp import EXPS, BASE_KW, _m
_Xtr = pd.read_parquet('../data/processed/X_train.parquet')
_ytr = pd.read_parquet('../data/processed/y_train.parquet').values.ravel().astype(float)
_Xte = pd.read_parquet('../data/processed/X_test.parquet')
_yte = pd.read_parquet('../data/processed/y_test.parquet').values.ravel().astype(float)
_filas = []
for _nombre, (_kw, _hip) in EXPS.items():
    _pipe = make_pipeline(MLPRegressor(**{**BASE_KW, **_kw}))
    _t0 = time.time()
    _pipe.fit(_Xtr, _ytr)
    _secs = time.time() - _t0
    _mm = _m(_ytr, _pipe.predict(_Xtr), _yte, _pipe.predict(_Xte))
    _filas.append({'experimento': _nombre, 'rmse_test': _mm['rmse_test'],
                   'mae_test': _mm['mae_test'], 'r2_test': _mm['r2_test']})
    print(f'{_nombre}: RMSE test {_mm["rmse_test"]:.4f} | {_secs:.0f}s | {_hip}')
_viva = pd.DataFrame(_filas).set_index('experimento')
_csv = pd.read_csv('../resultados/mlp_comparativa.csv').set_index('experimento')
_d = float(np.abs(_viva['rmse_test'] - _csv['rmse_test']).max())
print(f'diferencia maxima vs mlp_comparativa.csv: {_d:.4f}')
assert _d < 0.05, 'el re-entreno no reproduce el CSV oficial'
print('TABLA OK: el notebook calcula lo mismo que el CSV archivado.')'''

SHAP_VIVO = '''# SHAP EN VIVO (mismo codigo que `track_clase/shap_clase.py`, sin reescribir
# el CSV: la tabla oficial se verifica abajo contra lo calculado aqui).
import sys; sys.path.insert(0, '..')
import ast
import joblib, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from xgboost import XGBRegressor
from track_clase.pipeline_clase import FEATURE_COLS, make_pre
from track_clase.shap_clase import top_shap, N_FILAS, SEED
_Xtr = pd.read_parquet('../data/processed/X_train.parquet')
_ytr = pd.read_parquet('../data/processed/y_train.parquet').values.ravel()
_Xte = pd.read_parquet('../data/processed/X_test.parquet')
_comp = pd.read_csv('../resultados/comparativa.csv')
_params = ast.literal_eval(_comp.loc[_comp['modelo'] == 'xgb', 'mejores_params'].iloc[0])
_kw = {k.replace('reg__', ''): v for k, v in _params.items()}
_pre = make_pre().fit(_Xtr[FEATURE_COLS])
_nombres = list(_pre.get_feature_names_out())
_Ztr, _zte = _pre.transform(_Xtr[FEATURE_COLS]), _pre.transform(_Xte[FEATURE_COLS])
_reg = XGBRegressor(**{**dict(n_estimators=300, max_depth=6, learning_rate=0.05,
                              subsample=0.8, random_state=SEED, n_jobs=-1,
                              verbosity=0), **_kw})
_reg.fit(_Ztr, _ytr)
_fondo = shap.sample(_Ztr, min(N_FILAS, len(_Ztr)), random_state=SEED)
_sv = np.asarray(shap.TreeExplainer(_reg, data=_fondo).shap_values(_zte[:N_FILAS]))
_top = top_shap(_sv, _nombres, k=10)
_csv = pd.read_csv('../resultados/shap_importancia.csv')
assert _top['feature'].tolist() == _csv['feature'].tolist(), 'orden SHAP distinto del CSV'
print(_top.to_string(index=False))
print('Top-1:', _top.iloc[0]['feature'], f"({float(_top.iloc[0]['mean_abs_shap']):.2f}) — coincide con el CSV.")
fig, ax = plt.subplots(figsize=(7, 5))
ax.barh(_top['feature'][::-1], _top['mean_abs_shap'][::-1])
ax.set_title('SHAP (XGB, TreeExplainer exacto, 200 filas test)')
ax.set_xlabel('mean|SHAP|'); fig.tight_layout()
fig.savefig('../resultados/shap_importancia.png', dpi=120); plt.close(fig)
print('SHAP OK: calculado en vivo, figura regenerada.')
from IPython.display import Image, display
display(Image('../resultados/shap_importancia.png'))'''

MD_QUEVEMOS = '''## Qué vemos (números del entreno en vivo)

- E1 (7.70) < base (7.78): la capacidad ayuda. E2 (7.72) y E3 (7.76) no superan a E1: ni más regularización ni batch grande compran nada aquí.
- E1 < mejor clásico (SVM 9.06) por 1.36 RMSE: la no-linealidad con historia corta gana a los clásicos, pero sin memoria larga no alcanza al híbrido (4.25, citado).
- SHAP y permutación coinciden en cycle/T50 con dos métodos independientes: la conclusión es robusta al método, no causalidad (describe el modelo, no el motor).'''


def run_snippet(code):
    r = subprocess.run([PY, '-c', code], cwd='notebooks',
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f'T2 FAIL:\n{r.stderr[-2000:]}')
    return r.stdout


print('== full MLP (~2 min) ==')
out_mlp = run_snippet(FULL_MLP)
print('== SHAP vivo (~1 min) ==')
out_shap = run_snippet(SHAP_VIVO)

nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']
# Retira ancla E1 (la reemplaza el loop) y celda SHAP de solo-lectura.
cells = [c for c in cells
         if not (c['cell_type'] == 'code'
                 and ('# ANCLA (cuesta' in ''.join(c.get('source', []))
                      or (''.join(c.get('source', [])).startswith('import pandas as pd')
                          and 'shap_importancia.csv' in ''.join(c.get('source', [])))))]
nb['cells'] = cells
idx = next(i for i, c in enumerate(cells)
           if c['cell_type'] == 'markdown'
           and ''.join(c.get('source', []))
           .startswith('> Procedencia: `resultados/mlp_comparativa.csv`'))
mlp_cell = {'cell_type': 'code', 'execution_count': None, 'metadata': {},
            'outputs': [{'name': 'stdout', 'output_type': 'stream',
                         'text': out_mlp.splitlines(keepends=True)}],
            'source': [FULL_MLP]}
cells.insert(idx + 1, mlp_cell)
cells.insert(idx + 2, {'cell_type': 'markdown', 'metadata': {},
                       'source': [MD_QUEVEMOS]})
# SHAP vivo antes de su procedencia.
j = next(i for i, c in enumerate(cells)
         if c['cell_type'] == 'markdown'
         and ''.join(c.get('source', []))
         .startswith('> Procedencia: `resultados/shap_importancia.csv`'))
shap_cell = {'cell_type': 'code', 'execution_count': None, 'metadata': {},
             'outputs': [{'name': 'stdout', 'output_type': 'stream',
                          'text': out_shap.splitlines(keepends=True)}],
             'source': [SHAP_VIVO]}
cells.insert(j, shap_cell)
nb['cells'] = cells
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'03: {len(cells)} celdas. T2 insertado.')
