"""T1 — 02: GridSearch oficial en vivo (sin escrituras), estilo viejo."""
import json
import pathlib
import subprocess
import sys

NB = pathlib.Path('notebooks/02_modelos_A.ipynb')
PY = sys.executable

FULL_LOOP = '''# ENTRENO OFICIAL EN VIVO (mismo loop que `track_clase/train_clasicos.py`,
# orquestado aqui sin escribir nada: ni CSV ni joblib. Todo queda en memoria).
import sys; sys.path.insert(0, '..')
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold, GridSearchCV
from track_clase.pipeline_clase import make_pipeline
from track_clase.train_clasicos import (
    ESPEC, CV, SCORING, RANDOM_STATE, SVR_MUESTRA, _metricas)
_Xtr = pd.read_parquet('../data/processed/X_train.parquet')
_ytr = pd.read_parquet('../data/processed/y_train.parquet').values.ravel().astype(float)
_Xte = pd.read_parquet('../data/processed/X_test.parquet')
_yte = pd.read_parquet('../data/processed/y_test.parquet').values.ravel().astype(float)
_gtr = _Xtr['unit'].to_numpy()
_filas = []
for _nombre, (_reg, _grid) in ESPEC.items():
    _pipe = make_pipeline(_reg)
    _t0 = time.time()
    if _nombre == 'svm':
        _rng = np.random.default_rng(RANDOM_STATE)
        _idx = _rng.choice(len(_Xtr), size=min(SVR_MUESTRA, len(_Xtr)), replace=False)
        _Xs, _ys, _gs = _Xtr.iloc[_idx], _ytr[_idx], _gtr[_idx]
        _gsc = GridSearchCV(_pipe, _grid, cv=GroupKFold(3), scoring=SCORING, n_jobs=-1)
        _gsc.fit(_Xs, _ys, groups=_gs)
    else:
        _gsc = GridSearchCV(_pipe, _grid, cv=CV, scoring=SCORING, n_jobs=-1)
        _gsc.fit(_Xtr, _ytr, groups=_gtr)
    _secs = time.time() - _t0
    _best = _gsc.best_estimator_
    _m = _metricas(_ytr, _best.predict(_Xtr), _yte, _best.predict(_Xte))
    _filas.append({'modelo': _nombre, 'mejores_params': str(_gsc.best_params_),
                   'tiempo_s': round(_secs, 1),
                   **{k: round(v, 4) for k, v in _m.items()}})
    print(f'{_nombre}: RMSE test {_m["rmse_test"]:.4f} | {_gsc.best_params_} | {_secs:.0f}s')
_viva = pd.DataFrame(_filas).sort_values('modelo')
_csv = pd.read_csv('../resultados/comparativa.csv').sort_values('modelo')
_d = float(np.abs(_viva['rmse_test'].values - _csv['rmse_test'].values).max())
print(f'diferencia maxima vs comparativa.csv: {_d:.4f}')
assert _d < 0.01, 'el re-entreno no reproduce el CSV oficial'
print('TABLA OK: el notebook calcula lo mismo que el CSV archivado.')'''

MD_ESTILO = '''## Cómo leer esta tabla (baseline primero, regla de empate)

- El baseline es `regresion` (Ridge): cualquier modelo útil tiene que ganarle. Aquí ni siquiera el mejor clásico (SVM 9.06) se acerca al híbrido (4.25, citado como extra no visto en clase).
- **Regla de empate (por escrito):** se resta el RMSE del 1.º y del 2.º; si la diferencia es menor que el spread entre semillas/folds, gana el más simple. Aquí SVM (9.06) le saca 2.5 al siguiente: no hay empate que desempatar.
- **Qué vemos:** el orden se mantiene con el CSV archivado al céntimo — el re-entreno es determinista (seeds fijas, GroupKFold por motor).'''


def run_snippet(code):
    r = subprocess.run([PY, '-c', code], cwd='notebooks',
                       capture_output=True, text=True, timeout=600)
    if r.returncode != 0:
        raise RuntimeError(f'T1 FAIL:\n{r.stderr[-2000:]}')
    return r.stdout


print('== full loop (~2 min) ==')
out = run_snippet(FULL_LOOP)

nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']
# Retira ancla SVR y demo rapida (las reemplaza el entreno oficial).
cells = [c for c in cells
         if not (c['cell_type'] == 'code'
                 and ('# ANCLA: el CSV dice la verdad' in ''.join(c.get('source', []))
                      or '# MECANISMO (demo rapida)' in ''.join(c.get('source', []))))]
nb['cells'] = cells
# Inserta tras la procedencia de comparativa.csv.
idx = next(i for i, c in enumerate(cells)
           if c['cell_type'] == 'markdown'
           and ''.join(c.get('source', []))
           .startswith('> Procedencia: `resultados/comparativa.csv`'))
full_cell = {'cell_type': 'code', 'execution_count': None, 'metadata': {},
             'outputs': [{'name': 'stdout', 'output_type': 'stream',
                          'text': out.splitlines(keepends=True)}],
             'source': [FULL_LOOP]}
cells.insert(idx + 1, full_cell)
cells.insert(idx + 2, {'cell_type': 'markdown', 'metadata': {},
                       'source': [MD_ESTILO]})
nb['cells'] = cells
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print(f'02: {len(cells)} celdas. T1 insertado.')
