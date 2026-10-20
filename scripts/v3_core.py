"""Núcleo v3: features de salud, ventanas, OOF por motor, umbral por coste y quantiles.

Uso como librería desde el notebook o desde scripts/v3_run.py.

Claves del protocolo:
- Validación OOF con GroupKFold agrupando por `engine_id` (nunca filas del mismo motor
  en train y validación a la vez).
- Test: última ventana de cada motor contra RUL_FDxxx.txt (clip 125).
- El umbral de alarma se calibra en predicciones OOF de train, jamás en test.
"""
import pathlib

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.metrics import mean_squared_error, mean_absolute_error

CLIP = 125
WINDOW = 30
KEY = ['s2', 's3', 's4', 's7', 's11', 's12', 's15']
COLS = ['engine_id', 'cycle', 'setting1', 'setting2', 'setting3'] + [f's{i}' for i in range(1, 22)]
SENSORS = [f's{i}' for i in range(1, 22)]


# ---------------------------------------------------------------- datos
ROOT = pathlib.Path(__file__).resolve().parents[1] / 'archive' / 'CMaps'


def load_fd(fd='FD001', root=ROOT):
    train = pd.read_csv(f'{root}/train_{fd}.txt', sep=r'\s+', header=None, names=COLS)
    test = pd.read_csv(f'{root}/test_{fd}.txt', sep=r'\s+', header=None, names=COLS)
    rul = pd.read_csv(f'{root}/RUL_{fd}.txt', sep=r'\s+', header=None, names=['RUL'])
    rul.insert(0, 'engine_id', range(1, len(rul) + 1))
    for d in (train, test):
        d['RUL'] = (d.groupby('engine_id')['cycle'].transform('max') - d['cycle']).clip(upper=CLIP)
    return train, test, rul


def add_health_features(df):
    """Features causales por motor (solo usan pasado) + normalización por motor."""
    df = df.sort_values(['engine_id', 'cycle']).copy()
    g = df.groupby('engine_id', group_keys=False)
    out = {}
    for c in SENSORS:
        mean = g[c].transform(lambda s: s.expanding().mean())
        std = g[c].transform(lambda s: s.expanding().std()).replace(0, np.nan)
        out['z_' + c] = ((df[c] - mean) / std).fillna(0.0)
    for c in KEY:
        out['d10_' + c] = g[c].diff(10).fillna(0.0)
        out['d30_' + c] = g[c].diff(30).fillna(0.0)
        out['sd15_' + c] = g[c].transform(
            lambda s: s.rolling(15, min_periods=3).std()).fillna(0.0)
        out['m5_' + c] = g[c].transform(lambda s: s.rolling(5, min_periods=1).mean())
    feats = pd.DataFrame(out, index=df.index)
    return df, feats


# ---------------------------------------------------------------- ventanas
def make_windows(df, feats, window=WINDOW, only_last=False):
    """Devuelve X (n, window, n_feat), y, meta con engine_id, ciclo_fin, es_ultima."""
    X, y, eng, cyc, last = [], [], [], [], []
    for eid, g in df.groupby('engine_id', sort=True):
        idx = g.index
        A = feats.loc[idx].values
        Y = g['RUL'].values
        C = g['cycle'].values
        n = len(A)
        if n < window:
            continue
        starts = [n - window] if only_last else range(n - window + 1)
        for i in starts:
            X.append(A[i:i + window])
            y.append(Y[i + window - 1])
            eng.append(int(eid))
            cyc.append(int(C[i + window - 1]))
            last.append(bool(i + window == n))
    meta = pd.DataFrame({'engine_id': eng, 'ciclo_fin': cyc, 'es_ultima': last})
    return np.asarray(X), np.asarray(y), meta


def test_last(df, feats, rul_df, window=WINDOW):
    X, y, meta = make_windows(df, feats, window, only_last=True)
    X = X[meta['es_ultima'].values]
    meta = meta[meta['es_ultima']].reset_index(drop=True)
    meta = meta.merge(rul_df.rename(columns={'RUL': 'RUL_real'}), on='engine_id', how='left')
    meta['RUL_real'] = meta['RUL_real'].clip(upper=CLIP)
    return X, meta


# ---------------------------------------------------------------- métricas
def rmse(a, b):
    return float(np.sqrt(mean_squared_error(a, b)))


def mae(a, b):
    return float(mean_absolute_error(a, b))


def oof_predict(X, y, groups, make_model, folds=5, seeds=(42,), flat=True):
    """OOF por motor. Devuelve dict seed -> predicciones OOF."""
    Xf = X.reshape(len(X), -1) if flat else X
    res = {}
    for seed in seeds:
        oof = np.zeros(len(y))
        for tr, va in GroupKFold(folds).split(Xf, y, groups):
            m = make_model(seed)
            m.fit(Xf[tr], y[tr])
            oof[va] = m.predict(Xf[va])
        res[seed] = oof
    return res


def calibrate_threshold(oof_pred, y_true, cfn=20, cfp=1, event=15, grid=None):
    """Umbral que minimiza coste cfn*FN + cfp*FP para 'RUL real < event'."""
    y_true = np.asarray(y_true)
    oof_pred = np.asarray(oof_pred)
    pos = y_true < event
    if grid is None:
        grid = np.arange(5, 45.5, 0.5)
    best = (None, np.inf, None)
    for T in grid:
        pred = oof_pred < T
        tp = int((pred & pos).sum())
        fp = int((pred & ~pos).sum())
        fn = int((~pred & pos).sum())
        c = cfn * fn + cfp * fp
        if c < best[1]:
            best = (float(T), c, (tp, fp, fn))
    return {'T': best[0], 'coste': int(best[1]), 'tp': best[2][0], 'fp': best[2][1], 'fn': best[2][2],
            'recall': round(100 * best[2][0] / max(1, best[2][0] + best[2][2]), 1),
            'precision': round(100 * best[2][0] / max(1, best[2][0] + best[2][1]), 1)}


def eval_alarm(pred, real, T, cfn=20, cfp=1, event=15):
    pred = np.asarray(pred)
    real = np.asarray(real)
    pos = real < event
    alarma = pred < T
    tp = int((alarma & pos).sum())
    fp = int((alarma & ~pos).sum())
    fn = int((~alarma & pos).sum())
    return {'T': float(T), 'alarmas': int(alarma.sum()), 'tp': tp, 'fp': fp, 'fn': fn,
            'recall': round(100 * tp / max(1, tp + fn), 1),
            'precision': round(100 * tp / max(1, tp + fp), 1),
            'coste': int(cfn * fn + cfp * fp)}


def resumen(y_pred, meta, label, oof=None, y_oof=None):
    real = meta['RUL_real'].values
    d = {'modelo': label, 'n': int(len(real)),
         'rmse_test': round(rmse(real, y_pred), 2), 'mae_test': round(mae(real, y_pred), 2),
         'sesgo': round(float(np.mean(np.asarray(y_pred) - real)), 2)}
    if oof is not None:
        d['rmse_oof'] = round(rmse(y_oof, oof), 2)
        d['mae_oof'] = round(mae(y_oof, oof), 2)
    return d
