"""T4 — inserta en 05_ensemble_adaptado.ipynb las celdas de entreno en vivo (A-E).

Fuente de outputs: docs/plans/t4_chain_out.txt (stdout real de t4_chain.py,
ejecutado con el venv del proyecto). Los PNG se adjuntan como display_data.
"""
import base64
import json
import pathlib
import re

NB = pathlib.Path('notebooks/05_ensemble_adaptado.ipynb')
OUT = pathlib.Path('docs/plans/t4_chain_out.txt')

HEAD = """import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import warnings; warnings.filterwarnings('ignore')
import sys; sys.path.insert(0, '..'); sys.path.insert(0, '../src')
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
"""

CELL_A = HEAD + """from track_clase.train_ensemble_adaptado import (
    construir_raw_adaptado, FIT_UNITS, HOLDOUT_UNITS, TEST_UNITS, EPOCHS)
from ds02_rul.pipeline import run_seed
raw = construir_raw_adaptado()
out = run_seed(raw, seed=42, fit_units=FIT_UNITS,
               holdout_units=HOLDOUT_UNITS, test_units=TEST_UNITS,
               window=50, step_train=3, step_test=2, epochs=EPOCHS)
test = out['test']
units_te = test['meta']['unit'].values
cycles_te = test['meta']['cycle'].values
h = out['history'].history
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(h['loss'], label='train')
if 'val_loss' in h:
    ax.plot(h['val_loss'], label='val (holdout-16)')
ax.set_title('Curva de pérdida - BiLSTM seed 42 (early stopping)')
ax.set_xlabel('epoca'); ax.set_ylabel('MSE'); ax.legend()
fig.tight_layout(); fig.savefig('../resultados/loss_curve_c.png', dpi=120)
plt.close(fig)
from IPython.display import Image, display
display(Image('../resultados/loss_curve_c.png'))"""

CELL_B = """from track_clase.train_ensemble_adaptado import EPOCHS_OOF
from ds02_rul.pipeline import oof_base_predictions
from ds02_rul.stacking import select_beta_grouped
oof = oof_base_predictions(raw, raw['A_train'][:, 0], n_splits=3,
                           seed=42, window=50, step_train=3,
                           epochs=EPOCHS_OOF)
selection = select_beta_grouped(oof['units'], oof['cycles'], oof['y'],
                                oof['pred_lstm'], oof['pred_lgb'],
                                span=5, use_cycle_feature=False)
beta = float(selection['beta'])"""

CELL_C = HEAD + """from track_clase.dataset_clase import OP_COLS
from ds02_rul import HybridStackingEnsemble
from ds02_rul.metrics import evaluate_predictions, macro_rmse
from ds02_rul.smoothing import causal_ema_by_unit
from ds02_rul.stacking import fit_meta_learners
Z_hold = np.column_stack([out['p_lstm_hold'], out['p_lgb_hold']])
ridge_meta, lgb_meta = fit_meta_learners(
    Z_hold, out['dev']['y'][out['hold_idx']], seed=42)
ensemble = HybridStackingEnsemble(
    bilstm_model=out['bilstm'], lgb_standalone=out['lgbm'],
    ridge_meta=ridge_meta, lgb_meta=lgb_meta,
    residualizer=out['prep']['residualizer'],
    scaler=out['prep']['scaler'], scaler_w=out['prep']['scaler_w'],
    n_op=len(OP_COLS), window_size=50, beta=beta, ema_span=5)
p_ens = ensemble.predict(test['X_raw'], cycles_te, units_te)
p_lstm_ema = causal_ema_by_unit(out['p_lstm_test'], units_te, cycles_te, span=5)
rows = [
    evaluate_predictions(test['y'], out['p_lgb_test'], 'LGBM-C (cuantil 0.35)'),
    evaluate_predictions(test['y'], out['p_lstm_test'], 'BiLSTM-C'),
    evaluate_predictions(test['y'], p_lstm_ema, 'BiLSTM-C + EMA5'),
    evaluate_predictions(test['y'], p_ens, 'Hibrido-C (beta=%.2f) + EMA5' % beta),
]
macro = macro_rmse(test['y'], p_ens, units_te)
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(test['y'], p_ens, s=4, alpha=0.35)
lims = [float(test['y'].min()), float(test['y'].max())]
ax.plot(lims, lims, 'r--', lw=1)
ax.set_xlabel('RUL real'); ax.set_ylabel('RUL predicho (Hibrido-C vivo)')
fig.tight_layout()
fig.savefig('../resultados/real_vs_predicho_bundle_c.png', dpi=120)
plt.close(fig)
from IPython.display import Image, display
display(Image('../resultados/real_vs_predicho_bundle_c.png'))"""

CELL_D = """from ds02_rul.conformal import fit_conformal
calib = selection['oof_calib']
banda = fit_conformal(calib['y'], calib['pred_ema'], target=0.90)"""

CELL_E = """res = np.asarray(p_ens).ravel() - np.asarray(test['y']).ravel()
yt = np.asarray(test['y']).ravel()"""

MD_INTRO = """## El entreno de C, paso a paso (seed 42, en memoria)

Mismo protocolo que B, dieta adaptada (MAR T30 + ffill). Nada se persiste: el
bundle versionado sigue siendo `track_clase/models/` (manifest 4.338 / 2336.2).

> TIP: lo vivo debe caer cerca de lo archivado. Si difiere en centésimas es el
> no-determinismo de TF en CPU (`notebooks/ds02_ensemble/EVALUACION_EJECUCION.md`),
> no un error de implementación."""

MD_B = """> TIP (beta): `beta` decide cuánto de la opinión del meta-aprendiz reemplaza a
> la del BiLSTM. Se calibra fuera de fold y agrupada por motor: cada ventana la
> puntúa un meta que nunca la vio entrenar. `beta = 1.00` significa meta puro."""

MD_C = """### Qué acaba de pasar

1. El meta se ajusta **solo** con las predicciones de los dos especialistas en
   el holdout (motor 16) — nunca con el test.
2. `beta` mezcla: `p = p_lstm + beta·(p_meta − p_lstm)`.
3. EMA causal 5 suaviza por motor en orden de ciclo (decisión de hoy sin mirar
   la ventana de mañana).

Si el RMSE del híbrido no bate al del mejor especialista, el stacking no está
aportando: eso es información, no un fallo."""

MD_D = """## Cómo leer la banda

El intervalo es *split conformal* sobre residuales fuera de fold: con objetivo
90 %, unas 9 de cada 10 ventanas reales deben caer dentro. Si la cobertura en
test se aleja mucho del 90 %, la banda miente aunque el RMSE sea bueno."""

MD_E = """## Qué vemos (diagnóstico del C vivo, en memoria)

- **Residuos**: deben centrarse en cero con pocas colas. Cada ventana con
  |res| > 10 es un fallo gordo que el RMSE castiga y el negocio paga.
- **MAE por tramo**: dice *dónde* falla. Cerca del fallo (RUL < 25) el error
  debe ser pequeño; lejos, puede abrirse. Si se invierte, el modelo no sirve
  para decidir hangar aunque su RMSE global brille."""

MD_FRAMING = """### Lo vivo y lo archivado, uno al lado del otro

Arriba: reentrenado en este notebook. Abajo: el manifest determinista del
bundle versionado. Deben coincidir dentro de décimas; la puerta D11 no depende
del decimal. C es un banco de pruebas de robustez: B sigue en producción
porque C no le gana en las mismas ventanas."""


def read_text(p):
    return p.read_bytes().decode('utf-8', 'replace')


def img_output(png):
    b64 = base64.b64encode(pathlib.Path(png).read_bytes()).decode()
    return {'output_type': 'display_data',
            'data': {'image/png': b64,
                     'text/plain': ['<IPython.core.display.Image object>']},
            'metadata': {}}


def stream_output(text):
    return {'name': 'stdout', 'output_type': 'stream',
            'text': text.splitlines(keepends=True)}


txt = read_text(OUT)
parts = {}
pos = 0
for m in re.finditer(r'<<<SEC_([A-E])_END>>>', txt):
    parts['SEC_' + m.group(1)] = txt[pos:m.start()].strip('\r\n') + '\n'
    pos = m.end()
missing = {'SEC_A', 'SEC_B', 'SEC_C', 'SEC_D', 'SEC_E'} - set(parts)
if missing:
    raise SystemExit('Faltan secciones: %s' % sorted(missing))
if len(parts['SEC_A']) < 50:
    raise SystemExit('SEC_A demasiado corta; revisa t4_chain_out.txt')

nb = json.loads(NB.read_text(encoding='utf-8'))
cells = nb['cells']

# Idempotencia: fuera las celdas A-E que ya hubiera.
drop_marks = ('construir_raw_adaptado()\nout = run_seed',
              'oof_base_predictions(raw, raw[',
              'Z_hold = np.column_stack',
              "calib = selection['oof_calib']",
              'res = np.asarray(p_ens).ravel()')
cells = [c for c in cells
         if not (c['cell_type'] == 'code'
                 and any(m in ''.join(c.get('source', [])) for m in drop_marks))]
cells = [c for c in cells
         if not (c['cell_type'] == 'markdown'
                 and any(m in ''.join(c.get('source', []))
                         for m in ['El entreno de C, paso a paso',
                                   'Lo vivo y lo archivado, uno al lado del otro']))]

anchor = next(i for i, c in enumerate(cells)
              if c['cell_type'] == 'markdown'
              and 'Qué es cada pieza (II)' in ''.join(c.get('source', [])))

new = [
    {'cell_type': 'markdown', 'metadata': {}, 'source': [MD_INTRO]},
    {'cell_type': 'code', 'execution_count': 1, 'metadata': {},
     'outputs': [stream_output(parts['SEC_A']),
                 img_output('resultados/loss_curve_c.png')],
     'source': [CELL_A]},
    {'cell_type': 'code', 'execution_count': 2, 'metadata': {},
     'outputs': [stream_output(parts['SEC_B'])], 'source': [CELL_B]},
    {'cell_type': 'markdown', 'metadata': {}, 'source': [MD_B]},
    {'cell_type': 'code', 'execution_count': 3, 'metadata': {},
     'outputs': [stream_output(parts['SEC_C']),
                 img_output('resultados/real_vs_predicho_bundle_c.png')],
     'source': [CELL_C]},
    {'cell_type': 'markdown', 'metadata': {}, 'source': [MD_C]},
    {'cell_type': 'markdown', 'metadata': {}, 'source': [MD_D]},
    {'cell_type': 'code', 'execution_count': 4, 'metadata': {},
     'outputs': [stream_output(parts['SEC_D'])], 'source': [CELL_D]},
    {'cell_type': 'markdown', 'metadata': {}, 'source': [MD_E]},
    {'cell_type': 'code', 'execution_count': 5, 'metadata': {},
     'outputs': [stream_output(parts['SEC_E'])], 'source': [CELL_E]},
]
for k, cell in enumerate(new):
    cells.insert(anchor + 1 + k, cell)

# Framing justo antes de la primera lectura del CSV archivado.
j = next(i for i, c in enumerate(cells)
         if c['cell_type'] == 'code'
         and 'comparativa_bundle_c.csv' in ''.join(c.get('source', [])))
if not any(MD_FRAMING[:30] in ''.join(c.get('source', [])) for c in cells):
    cells.insert(j, {'cell_type': 'markdown', 'metadata': {},
                     'source': [MD_FRAMING]})

nb['cells'] = cells
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
print('05 OK: %d celdas' % len(cells))
print('SEC_A:', parts['SEC_A'].splitlines()[-1])
print('SEC_C:', parts['SEC_C'].splitlines()[-2:])
print('SEC_D:', parts['SEC_D'].strip()[:120])
