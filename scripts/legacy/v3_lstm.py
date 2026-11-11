"""Fase 0/2 para la RNN: holdout POR MOTOR + features de salud.

Split: 20 % de los motores (elegidos con semilla fija) queda fuera del entrenamiento.
Se entrena con todas las ventanas de los motores de train y se valida con todas las
ventanas de los motores retenidos (cubre todo el rango de RUL, a diferencia de un
split temporal, que solo ve el final de la vida y no aprende el rango completo).
El umbral de alarma se calibra en las predicciones de validación, nunca en test.

Uso: python scripts/v3_lstm.py --fd FD001 --epochs 60 --seed 42
"""
import argparse
import json
import pathlib
import time

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import StandardScaler
from tensorflow.keras import callbacks, layers, models

import v3_core as c

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'models' / 'v3_results.json'


def split_engines(df, frac=0.2, seed=42):
    """Holdout por motor: 20 % de los motores fuera del entrenamiento."""
    ids = np.array(sorted(df['engine_id'].unique()))
    rng = np.random.default_rng(seed)
    val_ids = rng.choice(ids, size=max(1, int(round(len(ids) * frac))), replace=False)
    return df[~df['engine_id'].isin(val_ids)], df[df['engine_id'].isin(val_ids)], val_ids


def build(inp_shape, units=(100, 50), dropout=0.2):
    """Construye el modelo BiLSTM v3 con la ventana y canales configurados."""
    inp = layers.Input(shape=inp_shape)
    x = inp
    for i, u in enumerate(units):
        last = i == len(units) - 1
        x = layers.LSTM(u, return_sequences=not last)(x)
        x = layers.BatchNormalization()(x)
        if dropout and not last:
            x = layers.Dropout(dropout)(x)
    x = layers.Dense(32, activation='relu')(x)
    x = layers.Dropout(dropout)(x)
    out = layers.Dense(1)(x)
    m = models.Model(inp, out)
    m.compile(optimizer=tf.keras.optimizers.Adam(1e-4, clipnorm=1.0), loss='mse', metrics=['mae'])
    return m


def run(fd, epochs, seed, frac=0.2, cfn=20):
    """Entrena el BiLSTM v3 y devuelve test y predicciones."""
    tf.keras.utils.set_random_seed(seed)
    tr, te, rul = c.load_fd(fd)
    _, f_tr = c.add_health_features(tr)
    _, f_te = c.add_health_features(te)

    tr_e, tr_l, val_ids = split_engines(tr, frac, seed)

    # La RNN sí necesita features escaladas (deltas y medias están en unidades de sensor).
    # El scaler se ajusta SOLO con las filas de los motores de entrenamiento.
    scaler = StandardScaler().fit(f_tr.loc[tr_e.index].values)
    f_tr_s = pd.DataFrame(scaler.transform(f_tr.values), index=f_tr.index, columns=f_tr.columns)
    f_te_s = pd.DataFrame(scaler.transform(f_te.values), index=f_te.index, columns=f_te.columns)
    f_e, f_l = f_tr_s.loc[tr_e.index], f_tr_s.loc[tr_l.index]
    Xe, ye, _ = c.make_windows(tr_e, f_e)
    Xl, yl, ml = c.make_windows(tr_l, f_l)
    Xt, mt = c.test_last(te, f_te_s, rul)
    print(f'{fd}: train {Xe.shape} ({tr_e.engine_id.nunique()} motores) | '
          f'val {Xl.shape} ({len(val_ids)} motores) | test {Xt.shape}')

    model = build((Xe.shape[1], Xe.shape[2]))
    es = callbacks.EarlyStopping(monitor='val_loss', patience=8, restore_best_weights=True, verbose=1)
    rl = callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=4, min_lr=1e-6, verbose=1)
    t0 = time.time()
    h = model.fit(Xe, ye, validation_data=(Xl, yl), epochs=epochs, batch_size=64,
                  shuffle=True, callbacks=[es, rl], verbose=2)
    tt = time.time() - t0

    p_val = model.predict(Xl, verbose=0).ravel()
    p_te = model.predict(Xt, verbose=0).ravel()
    cal = c.calibrate_threshold(p_val, yl, cfn=cfn)
    rec = {
        'features': 'health', 'modelo': 'LSTM 2x100-50 (holdout por motor)',
        'rmse_val': round(c.rmse(yl, p_val), 2), 'mae_val': round(c.mae(yl, p_val), 2),
        'rmse_test': round(c.rmse(mt.RUL_real, p_te), 2),
        'mae_test': round(c.mae(mt.RUL_real, p_te), 2),
        'sesgo': round(float(np.mean(p_te - mt.RUL_real)), 2),
        'T': cal['T'],
        'alarma_T': c.eval_alarm(p_te, mt.RUL_real.values, cal['T'], cfn=cfn),
        'alarma_15': c.eval_alarm(p_te, mt.RUL_real.values, 15.0, cfn=cfn),
        'epochs': len(h.history['loss']), 'segundos': round(tt, 1), 'seed': seed,
        'val_frac': frac, 'n_val_engines': int(len(val_ids)),
    }
    print(f"{fd} LSTM holdout: val {rec['rmse_val']:.2f} | test {rec['rmse_test']:.2f} | "
          f"T*={rec['T']:.1f} recall {rec['alarma_T']['recall']:.0f}% "
          f"({rec['alarma_T']['alarmas']} alarmas) | {tt:.0f}s")

    model.save(ROOT / 'models' / f'lstm_{fd}_v3_holdout.h5')
    data = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {}
    data.setdefault(fd, {}).setdefault('models', {})['health/LSTM holdout'] = rec
    data[fd]['lstm_holdout'] = rec
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding='utf-8')
    print('guardado en', OUT)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--fd', default='FD001')
    ap.add_argument('--epochs', type=int, default=60)
    ap.add_argument('--seed', type=int, default=42)
    a = ap.parse_args()
    run(a.fd, a.epochs, a.seed)
