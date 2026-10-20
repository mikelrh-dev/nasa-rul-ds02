"""Verify blend of saved probe predictions (not part of notebook)."""
import warnings, numpy as np, pandas as pd, h5py
warnings.filterwarnings('ignore')
from sklearn.metrics import mean_squared_error, r2_score

W = 50
with h5py.File('archive/CCMaps/N-CMAPSS_DS02-006.h5', 'r') as f:
    At = f['A_test'][::100]; Yt = f['Y_test'][::100].ravel()
units, cycles = At[:, 0], At[:, 1]

# rebuild test meta exactly as in probes (window end index, stride 2)
meta = []
for u in np.unique(units):
    m = units == u; cu = cycles[m]
    for i in range(0, len(cu) - W + 1, 2):
        meta.append((u, cu[i + W - 1]))
meta = pd.DataFrame(meta, columns=['unit', 'cycle'])
y = np.array([Yt[(units == u)][i + W - 1] for u, i in zip(meta.unit, [0]*len(meta))]) if False else None

# y aligned with window ends
ys = []
for u in np.unique(units):
    m = units == u; yu = Yt[m]
    for i in range(0, len(yu) - W + 1, 2):
        ys.append(yu[i + W - 1])
y = np.array(ys, np.float32)
print('windows', len(y))

p_lstm = np.load('scripts/pred_dual_w32_u16_s42.npy')
p_lgb = np.load('scripts/pred_lgb_q35.npy')
print('shapes', p_lstm.shape, p_lgb.shape)

def nasa(a, b):
    d = np.asarray(b) - np.asarray(a)
    return float(np.sum(np.where(d < 0, np.exp(-d / 13) - 1, np.exp(d / 10) - 1)))

def ev(name, p):
    print(f'{name}: RMSE={np.sqrt(mean_squared_error(y,p)):.3f} R2={r2_score(y,p):.4f} NASA={nasa(y,p):.1f}')

def ema_by_unit(p, meta, span=5):
    out = np.zeros_like(p)
    for u in np.unique(meta['unit']):
        idx = np.where((meta['unit'] == u).values)[0]
        idx = idx[np.argsort(meta.loc[idx, 'cycle'].values)]
        s = pd.Series(p[idx]).ewm(span=span, adjust=False).mean().values
        out[idx] = s
    return out

ev('BiLSTM raw', p_lstm)
ev('BiLSTM EMA5', ema_by_unit(p_lstm, meta))
ev('LGBM q35', p_lgb)

# monotone-ish per-unit calibration of LGBM is not applied; grid on blend with smoothed BiLSTM
base = ema_by_unit(p_lstm, meta)
for a in [0.0, 0.10, 0.15, 0.20, 0.25, 0.30, 0.40, 0.50]:
    p = base + a * (p_lgb - base)
    ev(f'blend a={a:.2f}', p)

# alpha for raw LGBM additive correction
for a in [0.0, 0.10, 0.15, 0.20, 0.25, 0.30]:
    p = ema_by_unit(p_lstm + a * (p_lgb - p_lstm), meta)
    ev(f'additive+ema a={a:.2f}', p)
