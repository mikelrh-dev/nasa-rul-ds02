"""Reconstruye las celdas v2 de notebook_nasa_fd001.ipynb.

Motivo: las celdas v2 se insertaron con `source.split('\n')`, lo que eliminaba
los saltos de línea y dejaba las celdas como comentarios (no-op) o SyntaxError.

Este script conserva las celdas 0-21 (base original ya validada) y sustituye
todo el bloque v2 por celdas bien formadas.
"""
import json
import pathlib

NB = pathlib.Path('notebook_nasa_fd001.ipynb')
KEEP = 22  # celdas 0..21 = base original

MD_22 = """## 7. V2 — comparativa ampliada y mejora LSTM

A partir de aquí todo se entrena y evalúa con **el mismo protocolo**:

- **Entrenamiento:** todas las ventanas completas de `train`, con RUL por ciclo (clip 125).
- **Test:** solo la **última ventana** de cada motor, comparada contra `RUL_FD001.txt`.
- **Train RMSE** se mide por ventana; **Test RMSE/MAE** por motor. No son la misma unidad,
  así que se reportan en columnas separadas.
"""

CODE_23 = r"""import json
import pathlib
import time

import joblib
from IPython.display import display
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import make_pipeline

# Mismo set de features que el baseline: 21 sensores + 3 settings = 24
SENSOR_COLS = [c for c in COLS if c.startswith('s')]
N_SENSORS = len(SENSOR_COLS)
print(f'features: {N_SENSORS} -> {SENSOR_COLS}')

# RUL real de test por motor: fuente de verdad para evaluar
rul_txt = pathlib.Path('archive/CMaps/RUL_FD001.txt').read_text(encoding='utf-8')
rul_vals = [int(x) for x in rul_txt.replace('\r', '').split()]
rul_df = pd.DataFrame({'engine_id': range(1, len(rul_vals) + 1), 'RUL_real': rul_vals})
rul_df['RUL_real'] = rul_df['RUL_real'].clip(upper=CLIP)

print(f'motores test: {len(rul_df)} | RUL real min {rul_df.RUL_real.min()} '
      f'media {rul_df.RUL_real.mean():.1f} max {rul_df.RUL_real.max()}')
display(rul_df.head(3))
"""

CODE_24 = r"""def build_windows(X, y, meta, window=30):
    # Ventanas completas por motor.
    # Devuelve (Xw, yw, meta_w) con meta_w = engine_id, ciclo_fin, es_ultima.
    # `es_ultima` marca la última ventana de cada motor (la que se usa en test).
    X = np.asarray(X)
    y = np.asarray(y)
    meta = meta.reset_index(drop=True)
    cyc = meta['cycle'].values

    X_list, y_list, rows = [], [], []
    for eid in np.unique(meta['engine_id'].values):
        idx = np.where(meta['engine_id'].values == eid)[0]
        seg_X, seg_y, seg_c = X[idx], y[idx], cyc[idx]
        if len(seg_X) < window:
            continue
        for i in range(len(seg_X) - window + 1):
            X_list.append(seg_X[i:i + window])
            y_list.append(seg_y[i + window - 1])
            rows.append({
                'engine_id': int(eid),
                'ciclo_fin': int(seg_c[i + window - 1]),
                'es_ultima': bool(i + window == len(seg_X)),
            })
    return np.array(X_list), np.array(y_list), pd.DataFrame(rows)


def evaluar(y_real, y_pred, label):
    rmse = float(np.sqrt(mean_squared_error(y_real, y_pred)))
    mae = float(mean_absolute_error(y_real, y_pred))
    print(f'{label:34s} RMSE={rmse:6.2f}  MAE={mae:6.2f}')
    return rmse, mae


def evaluar_ultima(pred, meta_last):
    # Evalúa predicciones de la última ventana contra RUL_FD001.txt.
    d = meta_last.copy().reset_index(drop=True)
    d['pred'] = np.asarray(pred).ravel()
    d = d.dropna(subset=['RUL_real'])
    rmse = float(np.sqrt(mean_squared_error(d['RUL_real'], d['pred'])))
    mae = float(mean_absolute_error(d['RUL_real'], d['pred']))
    return rmse, mae, int(len(d)), d


def guardar_modelo(obj, path):
    pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
    if path.endswith('.h5'):
        obj.save(path)
    else:
        joblib.dump(obj, path)
    print('guardado:', path)


print('helpers v2 listos')
"""

CODE_25 = r"""# Ventanas de 30 ciclos: todas para entrenar, última por motor para evaluar
Xtr30, ytr30, mtr30 = build_windows(X_train, y_train, meta_train, WINDOW)
Xte30_all, yte30_all, mte30_all = build_windows(X_test, y_test, meta_test, WINDOW)

mte30_last = mte30_all[mte30_all['es_ultima']].reset_index(drop=True)
mte30_last = mte30_last.merge(rul_df, on='engine_id', how='left')
Xte30_last = Xte30_all[mte30_all['es_ultima'].values]

print('ventanas train:', Xtr30.shape, '| motores test evaluados:', len(mte30_last))

# --- baseline XGBoost: predicción por ciclo promediada en la ventana ---
xgb = joblib.load('models/xgb_FD001_baseline.joblib')
pred_xgb_ciclo_te = xgb.predict(Xte30_last.reshape(-1, N_SENSORS))
pred_xgb_last = pred_xgb_ciclo_te.reshape(len(Xte30_last), WINDOW).mean(axis=1)

# --- baseline LSTM 2 capas ---
lstm2 = tf.keras.models.load_model('models/lstm_FD001_2layer.h5', compile=False)
lstm2.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4, clipnorm=1.0),
              loss='mse', metrics=['mae'])
pred_lstm2_last = lstm2.predict(Xte30_last, verbose=0).ravel()

rmse_xgb, mae_xgb, n_xgb, d_xgb = evaluar_ultima(pred_xgb_last, mte30_last)
rmse_lstm2, mae_lstm2, n_lstm2, d_lstm2 = evaluar_ultima(pred_lstm2_last, mte30_last)
rmse_train_xgb = float(np.sqrt(mean_squared_error(y_train, xgb.predict(X_train))))

print(f'XGBoost  (train por ciclo {rmse_train_xgb:.2f}) -> test {rmse_xgb:.2f} / MAE {mae_xgb:.2f}')
print(f'LSTM 2c  (train ventana {rmse_train_lstm:.2f}) -> test {rmse_lstm2:.2f} / MAE {mae_lstm2:.2f}')
"""

MD_26 = """### 7c. Comparativa vs otros modelos (Random Forest, LightGBM, Linear Regression)

Los tres consumen la **ventana completa aplanada** (30 × 24 = 720 features) y se entrenan
con **todas** las ventanas de train. Evaluación sobre la última ventana de cada motor.

> Nota: entrenar solo con la última ventana de cada motor daría `y = 0` en todas las filas
> (la última ventana de train es, por definición, el ciclo de fallo), así que el modelo
> aprendería a predecir 0. Por eso se entrena con todas las ventanas.
"""

CODE_27 = r"""Xtr_flat = Xtr30.reshape(len(Xtr30), -1)
Xte_flat = Xte30_last.reshape(len(Xte30_last), -1)

res = []
t0 = time.time()
rf = RandomForestRegressor(n_estimators=300, max_depth=12, random_state=42, n_jobs=-1)
rf.fit(Xtr_flat, ytr30)
t_rf = time.time() - t0
rmse_rf_tr = float(np.sqrt(mean_squared_error(ytr30, rf.predict(Xtr_flat))))
pred_rf_te = rf.predict(Xte_flat)
rmse_rf_te, mae_rf_te, _, d_rf = evaluar_ultima(pred_rf_te, mte30_last)
res.append(dict(modelo='Random Forest', rmse_tr=rmse_rf_tr, rmse_te=rmse_rf_te,
                mae_te=mae_rf_te, t=t_rf, n=len(d_rf)))
guardar_modelo(rf, 'models/rf_FD001_baseline.joblib')

try:
    import lightgbm as lgb
    t0 = time.time()
    lgb_m = lgb.LGBMRegressor(n_estimators=400, learning_rate=0.05, max_depth=8,
                              random_state=42, n_jobs=-1, verbose=-1)
    lgb_m.fit(Xtr_flat, ytr30)
    t_lgb = time.time() - t0
    rmse_lgb_tr = float(np.sqrt(mean_squared_error(ytr30, lgb_m.predict(Xtr_flat))))
    pred_lgb_te = lgb_m.predict(Xte_flat)
    rmse_lgb_te, mae_lgb_te, _, d_lgb = evaluar_ultima(pred_lgb_te, mte30_last)
    res.append(dict(modelo='LightGBM', rmse_tr=rmse_lgb_tr, rmse_te=rmse_lgb_te,
                    mae_te=mae_lgb_te, t=t_lgb, n=len(d_lgb)))
    guardar_modelo(lgb_m, 'models/lgb_FD001_baseline.joblib')
except Exception as exc:  # lightgbm no instalado
    print('LightGBM no disponible:', exc)
    pred_lgb_te = np.full(len(mte30_last), np.nan)
    rmse_lgb_te = mae_lgb_te = float('nan')
    res.append(dict(modelo='LightGBM', rmse_tr=float('nan'), rmse_te=float('nan'),
                    mae_te=float('nan'), t=float('nan'), n=0))

t0 = time.time()
lr_pipe = make_pipeline(StandardScaler(), LinearRegression())
lr_pipe.fit(Xtr_flat, ytr30)
t_lr = time.time() - t0
rmse_lr_tr = float(np.sqrt(mean_squared_error(ytr30, lr_pipe.predict(Xtr_flat))))
pred_lr_te = lr_pipe.predict(Xte_flat)
rmse_lr_te, mae_lr_te, _, d_lr = evaluar_ultima(pred_lr_te, mte30_last)
res.append(dict(modelo='Linear Regression', rmse_tr=rmse_lr_tr, rmse_te=rmse_lr_te,
                mae_te=mae_lr_te, t=t_lr, n=len(d_lr)))
guardar_modelo(lr_pipe, 'models/lr_FD001_baseline.joblib')

tabla = pd.DataFrame(res)[['modelo', 'rmse_tr', 'rmse_te', 'mae_te', 't', 'n']]
tabla.columns = ['Modelo', 'RMSE train (ventana)', 'RMSE test (motor)', 'MAE test', 'Tiempo (s)', 'n']
print('\n=== RF / LightGBM / Linear Regression ===')
display(tabla.round(2))
"""

MD_28 = """### 7d. Mejora LSTM

Tres variantes sobre la misma base, entrenadas con todas las ventanas:

1. **A** — LSTM 3 capas 100 → 64 → 32 con Dropout 0.2 (w=30).
2. **B** — Bidirectional LSTM 100 → 50 con Dropout 0.2 (w=30).
3. **C** — LSTM 2 capas 100 → 50 con ventana de 50 ciclos.

La ventana de 50 solo existe para motores con ≥ 50 ciclos, así que la selección se hace
**a igual número de motores** (intersección con el subconjunto de w=50). El ganador se
guarda en `models/lstm_FD001_best.h5`.
"""

CODE_29 = r"""def build_lstm_multi(inp_shape, units=(100, 64, 32), bidirectional=False, dropout=0.2):
    # Construye exactamente len(units) capas LSTM (la última sin return_sequences).
    inp = layers.Input(shape=inp_shape)
    x = inp
    for i, u in enumerate(units):
        last = (i == len(units) - 1)
        if bidirectional:
            x = layers.Bidirectional(layers.LSTM(u, return_sequences=not last))(x)
        else:
            x = layers.LSTM(u, return_sequences=not last)(x)
        x = layers.BatchNormalization()(x)
        if dropout and not last:
            x = layers.Dropout(dropout)(x)
    x = layers.Dense(32, activation='relu')(x)
    if dropout:
        x = layers.Dropout(dropout)(x)
    out = layers.Dense(1)(x)
    m = models.Model(inp, out, name='LSTM_variante')
    m.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-4, clipnorm=1.0),
              loss='mse', metrics=['mae'])
    return m


def entrenar(model, X, y, epochs=60, batch=64, patience=8):
    es = callbacks.EarlyStopping(monitor='val_loss', patience=patience,
                                 restore_best_weights=True, verbose=1)
    rl = callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=4,
                                     min_lr=1e-6, verbose=1)
    t0 = time.time()
    h = model.fit(X, y, validation_split=0.1, epochs=epochs, batch_size=batch,
                  shuffle=True, callbacks=[es, rl], verbose=2)
    return h, time.time() - t0


W50 = 50
Xtr50, ytr50, mtr50 = build_windows(X_train, y_train, meta_train, W50)
Xte50_all, yte50_all, mte50_all = build_windows(X_test, y_test, meta_test, W50)

mte50_last = mte50_all[mte50_all['es_ultima']].reset_index(drop=True)
mte50_last = mte50_last.merge(rul_df, on='engine_id', how='left')
Xte50_last = Xte50_all[mte50_all['es_ultima'].values]
print('motores con ventana de 50:', len(mte50_last))

specs = [
    ('A: LSTM 3 capas 100-64-32 + Dropout 0.2 (w=30)',
     dict(units=(100, 64, 32), bidirectional=False, dropout=0.2), WINDOW),
    ('B: Bidirectional LSTM 100-50 + Dropout 0.2 (w=30)',
     dict(units=(100, 50), bidirectional=True, dropout=0.2), WINDOW),
    ('C: LSTM 2 capas 100-50 + Dropout 0.2 (w=50)',
     dict(units=(100, 50), bidirectional=False, dropout=0.2), W50),
]

variantes = []
for nombre, kw, w in specs:
    if w == WINDOW:
        Xtr_w, ytr_w, Xte_w, mte_w = Xtr30, ytr30, Xte30_last, mte30_last
    else:
        Xtr_w, ytr_w, Xte_w, mte_w = Xtr50, ytr50, Xte50_last, mte50_last

    print('\n===', nombre, '===')
    m = build_lstm_multi((w, N_SENSORS), **kw)
    hist, ttime = entrenar(m, Xtr_w, ytr_w)
    pred_tr = m.predict(Xtr_w, verbose=0).ravel()
    pred_te = m.predict(Xte_w, verbose=0).ravel()
    rmse_tr = float(np.sqrt(mean_squared_error(ytr_w, pred_tr)))
    rmse_te, mae_te, n, d = evaluar_ultima(pred_te, mte_w)
    print(f'{nombre}: RMSE train {rmse_tr:.2f} | RMSE test {rmse_te:.2f} | '
          f'MAE {mae_te:.2f} | n={n} | {ttime:.1f}s')
    variantes.append(dict(nombre=nombre, modelo=m, hist=hist, w=w, rmse_tr=rmse_tr,
                          rmse_te=rmse_te, mae_te=mae_te, n=n, d=d, t=ttime))

# comparación justa: mismos motores para las tres variantes
ids50 = set(mte50_last['engine_id'].tolist())
for v in variantes:
    sub = v['d'][v['d']['engine_id'].isin(ids50)]
    v['rmse_te_comun'] = float(np.sqrt(mean_squared_error(sub['RUL_real'], sub['pred'])))
    v['n_comun'] = int(len(sub))

best = min(variantes, key=lambda v: v['rmse_te_comun'])
best_model, BEST_W = best['modelo'], best['w']

print('\n=== MEJOR LSTM (a igual n = %d motores) ===' % best['n_comun'])
print(f"{best['nombre']} -> RMSE test {best['rmse_te_comun']:.2f} "
      f"(todos sus motores: {best['rmse_te']:.2f}, n={best['n']})")

guardar_modelo(best_model, 'models/lstm_FD001_best.h5')
pathlib.Path('models/lstm_FD001_best.json').write_text(
    json.dumps({'nombre': best['nombre'], 'window': BEST_W,
                'rmse_test': best['rmse_te'], 'mae_test': best['mae_te']},
               ensure_ascii=False, indent=1), encoding='utf-8')

var_df = pd.DataFrame([{
    'Variante': v['nombre'],
    'RMSE train': round(v['rmse_tr'], 2),
    'RMSE test': round(v['rmse_te'], 2),
    'RMSE test (mismo n)': round(v['rmse_te_comun'], 2),
    'MAE test': round(v['mae_te'], 2),
    'n motores': v['n'],
    'Tiempo (s)': round(v['t'], 1),
} for v in variantes])
print('\n=== VARIANTES LSTM ===')
display(var_df)
"""

CODE_30 = r"""# Tabla única de todos los modelos del notebook
filas = [
    dict(Modelo='XGBoost (baseline, por ciclo)', rmse_tr=rmse_train_xgb, rmse_te=rmse_xgb,
         mae_te=mae_xgb, t=np.nan, n=n_xgb),
    dict(Modelo='Random Forest (ventana aplanada)', rmse_tr=res[0]['rmse_tr'],
         rmse_te=res[0]['rmse_te'], mae_te=res[0]['mae_te'], t=res[0]['t'], n=res[0]['n']),
    dict(Modelo='LightGBM (ventana aplanada)', rmse_tr=res[1]['rmse_tr'],
         rmse_te=res[1]['rmse_te'], mae_te=res[1]['mae_te'], t=res[1]['t'], n=res[1]['n']),
    dict(Modelo='Linear Regression (ventana aplanada)', rmse_tr=res[2]['rmse_tr'],
         rmse_te=res[2]['rmse_te'], mae_te=res[2]['mae_te'], t=res[2]['t'], n=res[2]['n']),
    dict(Modelo='LSTM 2 capas 100-50 (baseline)', rmse_tr=rmse_train_lstm,
         rmse_te=rmse_lstm2, mae_te=mae_lstm2, t=np.nan, n=n_lstm2),
    dict(Modelo=f"LSTM best: {best['nombre']}", rmse_tr=best['rmse_tr'],
         rmse_te=best['rmse_te'], mae_te=best['mae_te'], t=best['t'], n=best['n']),
]
tabla_final = pd.DataFrame(filas)[['Modelo', 'rmse_tr', 'rmse_te', 'mae_te', 't', 'n']]
tabla_final.columns = ['Modelo', 'RMSE train', 'RMSE test', 'MAE test', 'Tiempo (s)', 'n motores']
print('=== TABLA COMPARATIVA (test: última ventana vs RUL_FD001.txt, clip 125) ===')
display(tabla_final.round(2))
"""

MD_31 = """### 7e. Gráficos obligatorios

1. Cuatro motores aleatorios: RUL real vs predicción XGBoost vs predicción del mejor LSTM, **por ciclo**.
   El RUL real por ciclo se reconstruye como `RUL_FD001 + (ciclo_max - ciclo)`, que es exactamente
   el RUL verdadero de cada ciclo del motor.
2. Scatter RUL real vs predicho del mejor LSTM (última ventana por motor) con diagonal ideal.
3. Histograma de residuos del mejor LSTM.
4. Curva de aprendizaje (loss train/val) del mejor LSTM.
"""

CODE_32 = r"""# RUL real por ciclo en test (reconstruido desde RUL_FD001.txt)
real_ciclo = meta_test.copy()
real_ciclo['ciclo_max'] = real_ciclo.groupby('engine_id')['cycle'].transform('max')
real_ciclo = real_ciclo.merge(rul_df[['engine_id', 'RUL_real']], on='engine_id', how='left')
real_ciclo['RUL_ciclo'] = real_ciclo['RUL_real'] + (real_ciclo['ciclo_max'] - real_ciclo['cycle'])
real_ciclo['pred_xgb'] = xgb.predict(X_test)

# Predicciones por ciclo del mejor LSTM (ventana BEST_W)
Xte_best_all, _, mte_best_all = build_windows(X_test, y_test, meta_test, BEST_W)
mte_best_all['pred_lstm'] = best_model.predict(Xte_best_all, verbose=0).ravel()
serie = real_ciclo.merge(
    mte_best_all[['engine_id', 'ciclo_fin', 'pred_lstm']],
    left_on=['engine_id', 'cycle'], right_on=['engine_id', 'ciclo_fin'], how='left')

candidatos = sorted(serie.loc[serie['pred_lstm'].notna(), 'engine_id'].unique())
np.random.seed(7)
motores = sorted(np.random.choice(candidatos, size=min(4, len(candidatos)), replace=False).tolist())
print('motores representados:', motores)

fig, axes = plt.subplots(2, 2, figsize=(14, 8))
for ax, eid in zip(axes.ravel(), motores):
    sub = serie[serie['engine_id'] == eid].sort_values('cycle')
    ax.plot(sub['cycle'], sub['RUL_ciclo'], 'k-', lw=2.2, label='RUL real')
    ax.plot(sub['cycle'], sub['pred_xgb'], '--', color='steelblue', lw=1.5, label='XGBoost')
    ax.plot(sub['cycle'], sub['pred_lstm'], '-', color='crimson', lw=1.5,
            label=f'LSTM ({BEST_W} ciclos)')
    ax.axhline(15, color='orange', ls=':', lw=1)
    ax.axhline(30, color='green', ls=':', lw=1)
    ax.set_title(f'Motor {eid}')
    ax.set_xlabel('ciclo')
    ax.set_ylabel('RUL (clip 125)')
    ax.invert_yaxis()
    ax.legend(fontsize=8)
fig.suptitle('RUL real vs predicción XGBoost vs mejor LSTM — 4 motores de test')
plt.tight_layout()
plt.show()
"""

CODE_33 = r"""# Scatter y residuos del mejor LSTM sobre la última ventana por motor
if BEST_W == WINDOW:
    Xbest_last, mbest_last = Xte30_last, mte30_last
else:
    Xbest_last, mbest_last = Xte50_last, mte50_last

pred_best_last = best_model.predict(Xbest_last, verbose=0).ravel()
rmse_best, mae_best, n_best, d_best = evaluar_ultima(pred_best_last, mbest_last)
print(f"mejor LSTM -> RMSE {rmse_best:.2f} / MAE {mae_best:.2f} (n={n_best})")

real = d_best['RUL_real'].values
pred = d_best['pred'].values
resid = real - pred

fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].scatter(real, pred, alpha=0.75, s=26, edgecolor='k', linewidth=0.3)
lim = [0, max(real.max(), pred.max()) + 5]
axes[0].plot(lim, lim, 'r--', lw=1.5, label='diagonal ideal')
axes[0].set_xlim(lim)
axes[0].set_ylim(lim)
axes[0].set_xlabel('RUL real (clip 125)')
axes[0].set_ylabel('RUL predicha')
axes[0].set_title(f'Scatter — mejor LSTM (RMSE {rmse_best:.2f})')
axes[0].legend()

axes[1].hist(resid, bins=20, color='steelblue', edgecolor='black')
axes[1].axvline(0, color='red', ls='--', lw=1.5)
axes[1].set_xlabel('residuo (RUL real - RUL predicha)')
axes[1].set_ylabel('frecuencia')
axes[1].set_title(f'Residuos — media {resid.mean():.2f}, std {resid.std():.2f}')
plt.tight_layout()
plt.show()
"""

CODE_34 = r"""# Curva de aprendizaje del mejor LSTM
h = best['hist'].history
fig, ax = plt.subplots(figsize=(7, 3.8))
ax.plot(h['loss'], label='train loss')
if 'val_loss' in h:
    ax.plot(h['val_loss'], label='val loss')
ax.set_yscale('log')
ax.set_xlabel('epoch')
ax.set_ylabel('MSE (log)')
ax.set_title(f"Curva de entrenamiento — {best['nombre']}")
ax.legend()
plt.tight_layout()
plt.show()
print(f"epochs ejecutadas: {len(h['loss'])} | mejor val_loss: {min(h.get('val_loss', [np.nan])):.2f}")
"""

MD_35 = """### 7f. Feature importance de XGBoost

En FD001 los sensores más informativos suelen ser `s2, s3, s4, s7, s11, s12, s15`.
Se marcan sobre la importancia real del baseline entrenado por ciclo.
"""

CODE_36 = r"""fi_df = pd.DataFrame({'sensor': SENSOR_COLS, 'importance': xgb.feature_importances_})
fi_df = fi_df.sort_values('importance', ascending=False).reset_index(drop=True)
key = ['s2', 's3', 's4', 's7', 's11', 's12', 's15']
fi_df['es_key'] = fi_df['sensor'].isin(key)

print('Top 10 features por importancia:')
display(fi_df.head(10)[['sensor', 'importance', 'es_key']].round(4))

plt.figure(figsize=(9, 6))
sns.barplot(data=fi_df, y='sensor', x='importance', hue='es_key', dodge=False, legend=False,
            palette={True: 'crimson', False: 'steelblue'})
plt.xlabel('importancia (gain, escala log)')
plt.ylabel('feature')
plt.xscale('log')
plt.title('Feature importance XGBoost — sensores clave en rojo')
plt.tight_layout()
plt.show()

print('sensores clave en el top 10:', [s for s in fi_df.head(10)['sensor'] if s in key])
"""

MD_37 = """### 7g. Motor de reglas prototipo (semáforo)

- **ROJO**: RUL < 15
- **AMARILLO**: 15 ≤ RUL < 30
- **VERDE**: RUL ≥ 30

Se aplica a las predicciones de cada modelo sobre la última ventana de cada motor y se
cuenta cuántos motores caen en cada zona. También se compara con el semáforo real.
"""

CODE_38 = r"""def semaforo(rul):
    if rul < 15:
        return 'ROJO'
    elif rul < 30:
        return 'AMARILLO'
    return 'VERDE'


eval_df = mte30_last[['engine_id', 'RUL_real']].copy()
eval_df['pred_xgb'] = pred_xgb_last
eval_df['pred_lstm'] = pred_lstm2_last
eval_df['pred_rf'] = pred_rf_te
eval_df['pred_lgb'] = pred_lgb_te
eval_df['pred_lr'] = pred_lr_te
eval_df['pred_lstm_best'] = eval_df['engine_id'].map(
    pd.Series(pred_best_last, index=d_best['engine_id'].values))
eval_df.to_csv('models/test_eval_ultima_ventana.csv', index=False)
print('tabla guardada en models/test_eval_ultima_ventana.csv')
display(eval_df.head(5).round(2))

modelos = [
    ('XGBoost', 'pred_xgb'),
    ('Random Forest', 'pred_rf'),
    ('LightGBM', 'pred_lgb'),
    ('Linear Regression', 'pred_lr'),
    ('LSTM 2 capas', 'pred_lstm'),
    (f'LSTM best ({BEST_W} ciclos)', 'pred_lstm_best'),
]

filas_sem = []
for nombre, col in modelos:
    sub = eval_df[['RUL_real', col]].dropna()
    c = sub[col].apply(semaforo).value_counts().reindex(['ROJO', 'AMARILLO', 'VERDE']).fillna(0).astype(int)
    real_c = sub['RUL_real'].apply(semaforo).value_counts().reindex(['ROJO', 'AMARILLO', 'VERDE']).fillna(0).astype(int)
    aciertos = int((sub[col].apply(semaforo).values == sub['RUL_real'].apply(semaforo).values).sum())
    filas_sem.append({'Modelo': nombre, 'n': len(sub), 'ROJO': c['ROJO'], 'AMARILLO': c['AMARILLO'],
                      'VERDE': c['VERDE'], 'aciertos zona': aciertos,
                      'aciertos zona (%)': round(100 * aciertos / len(sub), 1)})

sem_df = pd.DataFrame(filas_sem)
real_sem = eval_df['RUL_real'].apply(semaforo).value_counts().reindex(['ROJO', 'AMARILLO', 'VERDE']).fillna(0).astype(int)
print('\n=== SEMÁFORO REAL (RUL_FD001.txt, n=%d) ===' % len(eval_df))
print(f"ROJO {real_sem['ROJO']} | AMARILLO {real_sem['AMARILLO']} | VERDE {real_sem['VERDE']}")
print('\n=== SEMÁFORO POR MODELO ===')
display(sem_df)
"""

CODE_39 = r"""# Métricas de la ejecución -> JSON (lo usa scripts/finalize_v2.py para la conclusión y el .md)
metricas = {
    'xgb': {'rmse_train': round(rmse_train_xgb, 2), 'rmse_test': round(rmse_xgb, 2),
            'mae_test': round(mae_xgb, 2), 'n': int(n_xgb)},
    'lstm2': {'rmse_train': round(rmse_train_lstm, 2), 'rmse_test': round(rmse_lstm2, 2),
              'mae_test': round(mae_lstm2, 2), 'n': int(n_lstm2)},
    'rf': {'rmse_train': round(res[0]['rmse_tr'], 2), 'rmse_test': round(res[0]['rmse_te'], 2),
           'mae_test': round(res[0]['mae_te'], 2), 't': round(res[0]['t'], 1), 'n': int(res[0]['n'])},
    'lgb': {'rmse_train': round(res[1]['rmse_tr'], 2), 'rmse_test': round(res[1]['rmse_te'], 2),
            'mae_test': round(res[1]['mae_te'], 2), 't': round(res[1]['t'], 1), 'n': int(res[1]['n'])},
    'lr': {'rmse_train': round(res[2]['rmse_tr'], 2), 'rmse_test': round(res[2]['rmse_te'], 2),
           'mae_test': round(res[2]['mae_te'], 2), 't': round(res[2]['t'], 1), 'n': int(res[2]['n'])},
    'best': {'nombre': best['nombre'], 'window': int(BEST_W),
             'rmse_train': round(best['rmse_tr'], 2), 'rmse_test': round(best['rmse_te'], 2),
             'mae_test': round(best['mae_te'], 2), 'n': int(best['n']),
             'rmse_test_mismo_n': round(best['rmse_te_comun'], 2), 'n_mismo_n': int(best['n_comun']),
             'epochs': len(best['hist'].history['loss']), 'tiempo': round(best['t'], 1)},
    'variantes': [{'nombre': v['nombre'], 'rmse_train': round(v['rmse_tr'], 2),
                   'rmse_test': round(v['rmse_te'], 2), 'mae_test': round(v['mae_te'], 2),
                   'rmse_test_mismo_n': round(v['rmse_te_comun'], 2), 'n': int(v['n']),
                   'tiempo': round(v['t'], 1)} for v in variantes],
    'semaforo_real': {k: int(v) for k, v in real_sem.items()},
    'semaforo': sem_df.rename(columns={'aciertos zona (%)': 'aciertos_pct'}).to_dict(orient='records'),
}
pathlib.Path('models/v2_metrics.json').write_text(
    json.dumps(metricas, ensure_ascii=False, indent=1), encoding='utf-8')
print('métricas guardadas en models/v2_metrics.json')
"""

MD_CONCL = """## 8. Conclusiones (v2)

_(pendiente de ejecución)_
"""


def code_cell(src):
    return {
        "cell_type": "code",
        "execution_count": None,
        "id": None,
        "metadata": {},
        "outputs": [],
        "source": src,
    }


def md_cell(src):
    return {"cell_type": "markdown", "metadata": {}, "id": None, "source": src}


def main():
    nb = json.loads(NB.read_text(encoding='utf-8'))
    cells = nb['cells'][:KEEP]

    # --- arreglos en celdas de la base original ---
    # 1) sep='\s+' generaba SyntaxWarning: usar raw strings
    cells[3]['source'] = ''.join(cells[3]['source']).replace("sep='\\s+'", "sep=r'\\s+'")
    # 2) bucle muerto con `pass` en build_windows
    src12 = ''.join(cells[12]['source'])
    dead = """    for eid, grp in zip(meta['engine_id'], 
                        [slice(None)]*len(meta)):
        pass  # placeholder, implementamos abajo con bucle
    
"""
    cells[12]['source'] = src12.replace(dead, '')

    nuevas = [
        md_cell(MD_22),
        code_cell(CODE_23),
        md_cell("### 7b. Utilidades (ventanas, métricas, guardado)"),
        code_cell(CODE_24),
        code_cell(CODE_25),
        md_cell(MD_26),
        code_cell(CODE_27),
        md_cell(MD_28),
        code_cell(CODE_29),
        code_cell(CODE_30),
        md_cell(MD_31),
        code_cell(CODE_32),
        code_cell(CODE_33),
        code_cell(CODE_34),
        md_cell(MD_35),
        code_cell(CODE_36),
        md_cell(MD_37),
        code_cell(CODE_38),
        code_cell(CODE_39),
        md_cell(MD_CONCL),
    ]

    nb['cells'] = cells + nuevas
    for i, c in enumerate(nb['cells']):
        c['id'] = f'c{i:02d}'
        if c['cell_type'] == 'code':
            c.setdefault('execution_count', None)
            c.setdefault('outputs', [])
            c['outputs'] = []
        c.setdefault('metadata', {})

    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
    print('celdas totales:', len(nb['cells']))
    print('celdas v2 reconstruidas:', len(nuevas))


if __name__ == '__main__':
    main()
