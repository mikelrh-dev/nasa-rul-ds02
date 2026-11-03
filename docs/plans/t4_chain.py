"""T4 chain: reentrena C (seed 42) en memoria. Sin writes salvo 2 PNGs.
Se ejecuta UNA vez en background; su stdout se reparte en celdas.
Uso: .venv/Scripts/python.exe docs/plans/t4_chain.py  (cwd = notebooks/)
"""
import os
import sys

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
import warnings
warnings.filterwarnings('ignore')

sys.path.insert(0, '..')
sys.path.insert(0, '../src')

import time
import numpy as np
import pandas as pd
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt

from track_clase.dataset_clase import OP_COLS
from track_clase.train_ensemble_adaptado import (
    construir_raw_adaptado, FIT_UNITS, HOLDOUT_UNITS, TEST_UNITS,
    EPOCHS, EPOCHS_OOF, B_HIST)
from ds02_rul import HybridStackingEnsemble
from ds02_rul.conformal import fit_conformal, apply_conformal, empirical_coverage
from ds02_rul.metrics import evaluate_predictions, macro_rmse
from ds02_rul.pipeline import oof_base_predictions, run_seed
from ds02_rul.smoothing import causal_ema_by_unit
from ds02_rul.stacking import fit_meta_learners, select_beta_grouped

t00 = time.time()
raw = construir_raw_adaptado()
print(f'raw: train {raw["W_train"].shape} | test {raw["W_test"].shape} '
      f'| medianas fit-units: {len(raw["medianas_fit"])} sensores')

# ---------------- A: run_seed 42 ----------------
out = run_seed(raw, seed=42, fit_units=FIT_UNITS,
               holdout_units=HOLDOUT_UNITS, test_units=TEST_UNITS,
               window=50, step_train=3, step_test=2, epochs=EPOCHS)
test = out['test']
units_te = test['meta']['unit'].values
cycles_te = test['meta']['cycle'].values
print(f"run_seed 42: LGBM {out['t_lgb']:.1f}s | BiLSTM {out['t_lstm']:.1f}s | "
      f"params {out['n_params']:,}")
print(f"dev ventanas: {out['dev']['X_tab'].shape} | test ventanas: "
      f"{test['X_tab'].shape} (6.196 esperadas)")
h = out['history'].history
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot(h['loss'], label='train')
ax.plot(h.get('val_loss', []), label='val (holdout-16)')
ax.set_title('Curva de pérdida — BiLSTM seed 42 (early stopping)')
ax.set_xlabel('época'); ax.set_ylabel('MSE'); ax.legend()
fig.tight_layout(); fig.savefig('../resultados/loss_curve_c.png', dpi=120)
plt.close(fig)
print(f"épocas: {len(h['loss'])} | loss {h['loss'][0]:.4f}->{h['loss'][-1]:.4f}")
print('<<<SEC_A_END>>>')

# ---------------- B: OOF + beta ----------------
oof = oof_base_predictions(raw, raw['A_train'][:, 0], n_splits=3,
                            seed=42, window=50, step_train=3,
                            epochs=EPOCHS_OOF)
selection = select_beta_grouped(oof['units'], oof['cycles'], oof['y'],
                                oof['pred_lstm'], oof['pred_lgb'],
                                span=5, use_cycle_feature=False)
beta = float(selection['beta'])
print(f"beta_hat (mediana OOF agrupada por motor) = {beta:.2f} | "
      f"dispersión={selection['spread']}")
print('<<<SEC_B_END>>>')

# ---------------- C: meta + ensemble + EMA + tabla + D11 ----------------
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
    evaluate_predictions(test['y'], p_ens, f'Híbrido-C (beta={beta:.2f}) + EMA5'),
]
comp = pd.DataFrame(rows)
print(comp.to_string(index=False))
rmse_c, nasa_c = float(rows[3]['RMSE']), float(rows[3]['NASA_Score'])
ok_r, ok_n = rmse_c <= B_HIST['rmse'], nasa_c <= B_HIST['nasa']
print(f'vivo: RMSE={rmse_c:.3f} NASA={nasa_c:.1f} | congelado B: 4.251/2305.1 | '
      f'manifest C: 4.338/2336.2')
assert 4.0 < rmse_c < 4.8, 'C fuera de rango: revisar entreno'
print(f"puerta D11: RMSE {rmse_c:.3f}<=4.251? {ok_r} | NASA {nasa_c:.1f}<=2305.1? "
      f"{ok_n} -> {'ADOPTAR' if ok_r and ok_n else 'C queda como experimento, B sigue'}")
macro = macro_rmse(test['y'], p_ens, units_te)
print(f"macro-RMSE C: {macro['macro_rmse']:.4f} | por motor: "
      + ', '.join(f"{int(k)}:{v:.2f}" for k, v in
                  sorted(macro['per_unit_rmse'].items())))
fig, ax = plt.subplots(figsize=(8, 5))
ax.scatter(test['y'], p_ens, s=4, alpha=0.35)
lims = [float(test['y'].min()), float(test['y'].max())]
ax.plot(lims, lims, 'r--', lw=1)
ax.set_xlabel('RUL real'); ax.set_ylabel('RUL predicho (Híbrido-C vivo)')
ax.set_title(f'Real vs predicho — C vivo seed 42 '
             f'(RMSE {rmse_c:.3f}, NASA {nasa_c:.1f})')
fig.tight_layout()
fig.savefig('../resultados/real_vs_predicho_bundle_c.png', dpi=120)
plt.close(fig)
print('<<<SEC_C_END>>>')

# ---------------- D: conformal ----------------
calib = selection['oof_calib']
banda = fit_conformal(calib['y'], calib['pred_ema'], target=0.90)
lo, hi = apply_conformal(p_ens, banda)
cob = empirical_coverage(test['y'], lo, hi)
ancho = float(np.median(hi - lo))
print(f"banda conformal 90%: cobertura en test = {cob:.3f} | ancho mediano = {ancho:.2f} ciclos")
print('<<<SEC_D_END>>>')

# ---------------- E: diagnóstico ----------------
res = np.asarray(p_ens).ravel() - np.asarray(test['y']).ravel()
print(f"residuos: media={res.mean():+.3f} | min={res.min():+.2f} | max={res.max():+.2f} | "
      f"|res|>10: {(np.abs(res) > 10).sum()} ventanas")
yt = np.asarray(test['y']).ravel()
for a, b, tag in [(0, 25, 'RUL<25'), (25, 60, '25-60'), (60, 200, '>60')]:
    m = (yt >= a) & (yt < b)
    mae = float(np.mean(np.abs(res[m]))) if m.any() else float('nan')
    print(f'MAE tramo {tag}: {mae:.3f} (n={m.sum()})')
print(f'total {time.time() - t00:.0f}s (solo inferencia+entreno, cero writes a models/)')
print('<<<SEC_E_END>>>')
