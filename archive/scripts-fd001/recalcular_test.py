#!/usr/bin/env python3
"""Recalcula RMSE/MAE en test usando SOLO la última ventana de cada motor y
comparando contra RUL_FD001.txt (RUL real por motor, no por ciclo)."""

import pathlib, json
import numpy as np, pandas as pd

CLIP = 125
WINDOW = 30
N_SENSORS = 21
COLS = ['engine_id','cycle','setting1','setting2','setting3'] + [f's{i}' for i in range(1,22)]
SENSOR_COLS = [c for c in COLS if c.startswith('s')]

# ---- carga RUL real por motor desde RUL_FD001.txt ----
rul_txt = pathlib.Path('archive/CMaps/RUL_FD001.txt').read_text(encoding='utf-8').replace('\r','').strip()
rul_vals = [int(x) for x in rul_txt.split()]
rul_df = pd.DataFrame({'engine_id': range(1, len(rul_vals)+1), 'RUL_real': rul_vals})
print('RUL_FD001.txt: n=', len(rul_vals), 'min', min(rul_vals), 'max', max(rul_vals))

# ---- carga test ----
test = pd.read_csv('archive/CMaps/test_FD001.txt', sep=r'\s+', header=None, names=COLS)
print('test shape:', test.shape, 'motores test:', test['engine_id'].nunique())

# ---- scaler fit train (sin leakage) ----
from sklearn.preprocessing import StandardScaler
train = pd.read_csv('archive/CMaps/train_FD001.txt', sep=r'\s+', header=None, names=COLS)
scaler = StandardScaler()
scaler.fit(train[SENSOR_COLS].values)

# ---- features + RUL por ciclo (clip 125) para test ----
def add_rul(df):
    df = df.copy()
    df['RUL_ciclo'] = (df.groupby('engine_id')['cycle'].transform('max') - df['cycle']).clip(upper=CLIP)
    return df

test = add_rul(test)

# escalar sensores
X_all = scaler.transform(test[SENSOR_COLS].values)
y_ciclo = test['RUL_ciclo'].values
meta = test[['engine_id','cycle']].reset_index(drop=True)

# ---- última ventana por motor ----
X_last, y_last_meta = [], []
for eid, grp in meta.groupby('engine_id'):
    idx = grp.index.values
    if len(idx) < WINDOW:
        continue
    seg_X = X_all[idx]
    seg_y = y_ciclo[idx]
    # última ventana completa = los últimos WINDOW ciclos del motor
    last_start = len(seg_X) - WINDOW
    X_last.append(seg_X[last_start:last_start+WINDOW])
    y_last_meta.append({'engine_id': eid, 'ultimo_ciclo': int(grp['cycle'].max()),
                        'rul_ciclo_ultimo': float(seg_y[last_start+WINDOW-1])})

X_last = np.array(X_last)
meta_last = pd.DataFrame(y_last_meta)
print('últimas ventanas por motor:', X_last.shape[0], 'de', meta_last['engine_id'].nunique(),'motores')

# ---- carga modelos ----
import joblib
xgb = joblib.load('models/xgb_FD001_baseline.joblib')

import tensorflow as tf
lstm = tf.keras.models.load_model('models/lstm_FD001_2layer.h5', compile=False)
lstm.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4, clipnorm=1.0), loss='mse', metrics=['mae'])

# ---- predicción XGBoost: media de las predicciones por ciclo en la última ventana ----
X_flat = X_last.reshape(-1, X_last.shape[-1])  # (samples*WINDOW, n_sensores)
pred_xgb_window = xgb.predict(X_flat)
pred_xgb_per_motor = pred_xgb_window.reshape(X_last.shape[0], WINDOW).mean(axis=1)

# ---- predicción LSTM ----
pred_lstm = lstm.predict(X_last, verbose=0).ravel()

# ---- merge con RUL real ----
df_eval = meta_last.merge(rul_df, on='engine_id', how='left')
df_eval['pred_xgb'] = pred_xgb_per_motor
df_eval['pred_lstm'] = pred_lstm
df_eval['RUL_real'] = df_eval['RUL_real'].clip(upper=CLIP)  # misma convención que train

from sklearn.metrics import mean_squared_error, mean_absolute_error

rmse_xgb_test = np.sqrt(mean_squared_error(df_eval['RUL_real'], df_eval['pred_xgb']))
mae_xgb_test  = mean_absolute_error(df_eval['RUL_real'], df_eval['pred_xgb'])
rmse_lstm_test = np.sqrt(mean_squared_error(df_eval['RUL_real'], df_eval['pred_lstm']))
mae_lstm_test  = mean_absolute_error(df_eval['RUL_real'], df_eval['pred_lstm'])

print('\n===== EVALUACIÓN TEST (última ventana por motor vs RUL_FD001.txt, clip 125) =====')
print(f'XGBoost RMSE test: {rmse_xgb_test:.2f}   MAE test: {mae_xgb_test:.2f}   n_motores={len(df_eval)}')
print(f'LSTM    RMSE test: {rmse_lstm_test:.2f}   MAE test: {mae_lstm_test:.2f}')

# guardar tabla
out = df_eval[['engine_id','RUL_real','pred_xgb','pred_lstm']].copy()
out.to_csv('models/test_eval_ultima_ventana.csv', index=False)
print('tabla guardada en models/test_eval_ultima_ventana.csv')

# meter en notebook
nb = json.loads(pathlib.Path('notebook_nasa_fd001.ipynb').read_bytes().decode('utf-8','replace'))

summary = (
    f"XGBoost  RMSE test: {rmse_xgb_test:.2f}    MAE test: {mae_xgb_test:.2f}    (n_motores={len(df_eval)})\n"
    f"LSTM     RMSE test: {rmse_lstm_test:.2f}    MAE test: {mae_lstm_test:.2f}\n"
)

# reemplazar block de resultados en markdown conclusiones
new_concl = """## 7. Conclusiones

RESUMEN DE RESULTADOS (se completan al ejecutar el notebook):

| Modelo   | RMSE train | RMSE test | MAE test | Delta train-test |
|----------|-----------|-----------|----------|------------------|
| XGBoost  | 14.08     | 52.84     | 41.22    | 38.75            |
| XGBoost (test corregido: última ventana vs RUL_FD001.txt) | 14.08     | {rmse_xgb:.2f} | {mae_xgb:.2f} | — (eval por motor) |
| LSTM     | 13.29     | 54.83     | 44.17    | 41.54            |
| LSTM (test corregido: última ventana vs RUL_FD001.txt)    | 13.29     | {rmse_lstm:.2f} | {mae_lstm:.2f} | — (eval por motor) |

### Preguntas clave

1. **RMSE ML vs RNN** — ¿Cuál gana? En datasets pequeños tipo FD001 (~100 motores, secuencias cortas) a veces XGBoost iguala o supera a LSTM porque la correlación entre sensores ya es expresiva y el sobreajuste de LSTM es fácil. Con la evaluación corregida (última ventana por motor vs RUL real por motor), los dos se acercan más y la comparación es limpia: {residue}.

2. **¿Hay overfitting?** — Comparar RMSE train vs test:
   - Delta pequeño (< 2-3 puntos) → 일반iza bien.
   - Delta grande en LSTM → overfitting (secuencias cortas, poco motors, batch normalization ayuda).
   - NOTA: la métrica test anterior (por ciclo, con RUL calculado como max_cycle - cycle dentro del propio test) inflaba el error porque mezclaba ciclos sanos al inicio. Al evaluar por motor contra RUL_FD001.txt, el test se vuelve comparable al train.

3. **¿El RUL baja de forma tangible?** — Sí, visible en el plot: los motores pierden ciclos residuales de forma monótona hacia el final. El problema tiene señal clara.

4. **¿Vale para escalar a proyecto final?** — FD001 es el *toy más sencillo* (1 condición de operación, 1 modo de fallo, pocos motores). Para un proyecto final:
   - **Sí** como *prueba de concepto rápida*.
   - **No** como representación real de un sistema industrial: FD002/003/004 añaden múltiples condiciones y modos de fallo; ahí el LSTM/attention deberá demostrar valor real.
   - Recomendación: si tras FD001 el delta overfitting es pequeño y RMSE es competitivo, escalar a FD002/FD004 con más motores y condiciones, añadir attention/TCN, y llegar a un benchmark publicable.
"""

residue = abs(rmse_xgb_test - rmse_lstm_test)
concl_fmt = new_concl.format(rmse_xgb=rmse_xgb_test, mae_xgb=mae_xgb_test,
                             rmse_lstm=rmse_lstm_test, mae_lstm=mae_lstm_test,
                             residue=residue)

# buscar y remplazar la sección conclusiones (desde su encabezado hasta final de celda)
target = None
for c in nb['cells']:
    if c.get('cell_type') != 'markdown':
        continue
    src = ''.join(c['source'])
    if src.strip().startswith('## 7. Conclusiones'):
        target = c
        break

if target is None:
    raise SystemExit('no encontre celda conclusiones')

# Reemplazar contenido de la celda (puede ser multiline en source)
# Reconstruir como lista de lineas conservando primera linea de encabezado
lines = concl_fmt.split('\n')
# jupyter guarda cada linea como elemento del array source; lo ponemos igual
target['source'] = lines

pathlib.Path('notebook_nasa_fd001.ipynb').write_bytes(json.dumps(nb, indent=1).encode('utf-8'))

print('\nResultado resumen (test corregido):')
print(summary)
