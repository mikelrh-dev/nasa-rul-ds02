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
from sklearn.metrics import mean_squared_error, mean_absolute_error

CLIP = 125
KEY = ['s2', 's3', 's4', 's7', 's11', 's12', 's15']
COLS = ['engine_id', 'cycle', 'setting1', 'setting2', 'setting3'] + [f's{i}' for i in range(1, 22)]
SENSORS = [f's{i}' for i in range(1, 22)]


# ---------------------------------------------------------------- datos
ROOT = pathlib.Path(__file__).resolve().parents[1] / 'archive' / 'CMaps'


def load_fd(fd='FD001', root=ROOT):
    """Carga el split FD001 (train, test y RUL) desde su CSV."""
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


# ---------------------------------------------------------------- métricas
def rmse(a, b):
    """RMSE entre verdad y prediccion."""
    return float(np.sqrt(mean_squared_error(a, b)))


def mae(a, b):
    """MAE entre verdad y prediccion."""
    return float(mean_absolute_error(a, b))


def resumen(y_pred, meta, label, oof=None, y_oof=None):
    """Resume metricas y alarmas en una tabla imprimible."""
    real = meta['RUL_real'].values
    d = {'modelo': label, 'n': int(len(real)),
         'rmse_test': round(rmse(real, y_pred), 2), 'mae_test': round(mae(real, y_pred), 2),
         'sesgo': round(float(np.mean(np.asarray(y_pred) - real)), 2)}
    if oof is not None:
        d['rmse_oof'] = round(rmse(y_oof, oof), 2)
        d['mae_oof'] = round(mae(y_oof, oof), 2)
    return d
