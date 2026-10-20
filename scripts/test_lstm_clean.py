import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras import layers, callbacks, models
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error

tf.random.set_seed(42)
np.random.seed(42)

CLIP = 125
WINDOW = 30
COLS = ['engine_id', 'cycle', 'setting1', 'setting2', 'setting3'] + [f's{i}' for i in range(1, 22)]
CONST_COLS = ['setting3', 's1', 's5', 's10', 's16', 's18', 's19']
ACTIVE_SENSORS = [f's{i}' for i in range(1, 22) if f's{i}' not in CONST_COLS]

train = pd.read_csv('archive/CMaps/train_FD001.txt', sep=r'\s+', header=None, names=COLS)
test = pd.read_csv('archive/CMaps/test_FD001.txt', sep=r'\s+', header=None, names=COLS)
rul_df = pd.read_csv('archive/CMaps/RUL_FD001.txt', sep=r'\s+', header=None, names=['RUL'])

def nasa_score(y_true, y_pred):
    d = np.asarray(y_pred) - np.asarray(y_true)
    score = np.where(d < 0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)
    return float(np.sum(score))

# RUL
train_max = train.groupby('engine_id')['cycle'].transform('max')
train['RUL'] = (train_max - train['cycle']).clip(upper=CLIP)

test_max = test.groupby('engine_id')['cycle'].transform('max')
rul_map = dict(zip(range(1, len(rul_df) + 1), rul_df['RUL'].values))
test_true_max = test_max + test['engine_id'].map(rul_map)
test['RUL'] = (test_true_max - test['cycle']).clip(upper=CLIP)

scaler = StandardScaler()
train_scaled = train.copy()
test_scaled = test.copy()
train_scaled[ACTIVE_SENSORS] = scaler.fit_transform(train[ACTIVE_SENSORS])
test_scaled[ACTIVE_SENSORS] = scaler.transform(test[ACTIVE_SENSORS])

# Generador de ventanas con padding (robusto para secuencias cortas)
def gen_windows(df, window=WINDOW, feature_cols=ACTIVE_SENSORS, last_only=False):
    X_list, y_list, meta_list = [], [], []
    for eid, group in df.groupby('engine_id'):
        x_mat = group[feature_cols].values
        y_vec = group['RUL'].values
        cycles = group['cycle'].values
        n_pts = len(x_mat)
        
        # Si un motor tiene menos de 'window' ciclos, aplicar padding replicando el primer ciclo
        if n_pts < window:
            pad_len = window - n_pts
            pad_x = np.repeat(x_mat[0:1], pad_len, axis=0)
            x_mat = np.vstack([pad_x, x_mat])
            y_vec = np.pad(y_vec, (pad_len, 0), mode='edge')
            cycles = np.pad(cycles, (pad_len, 0), mode='edge')
            n_pts = window
            
        if last_only:
            X_list.append(x_mat[-window:])
            y_list.append(y_vec[-1])
            meta_list.append({'engine_id': eid, 'cycle': cycles[-1], 'RUL': y_vec[-1]})
        else:
            for i in range(n_pts - window + 1):
                X_list.append(x_mat[i:i + window])
                y_list.append(y_vec[i + window - 1])
                meta_list.append({'engine_id': eid, 'cycle': cycles[i + window - 1], 'RUL': y_vec[i + window - 1]})
                
    return np.array(X_list, dtype=np.float32), np.array(y_list, dtype=np.float32), pd.DataFrame(meta_list)

# Split 80/20 por motor (sin leakage)
rng = np.random.RandomState(42)
eids = train['engine_id'].unique()
perm = rng.permutation(len(eids))
val_eids = set(eids[perm[:20]])

train_df = train_scaled[~train_scaled['engine_id'].isin(val_eids)]
val_df = train_scaled[train_scaled['engine_id'].isin(val_eids)]

X_train_w, y_train_w, _ = gen_windows(train_df, WINDOW)
X_val_w, y_val_w, _ = gen_windows(val_df, WINDOW)
X_test_w_all, y_test_w_all, meta_test_all = gen_windows(test_scaled, WINDOW, last_only=False)
X_test_w_last, y_test_w_last, meta_test_last = gen_windows(test_scaled, WINDOW, last_only=True)

print(f"X_train_w: {X_train_w.shape}, X_val_w: {X_val_w.shape}")
print(f"X_test_w_all: {X_test_w_all.shape}, X_test_w_last: {X_test_w_last.shape}")

# Modelo LSTM con regularización Dropout
def build_model(inp_shape):
    inp = layers.Input(shape=inp_shape)
    x = layers.LSTM(100, return_sequences=True)(inp)
    x = layers.Dropout(0.2)(x)
    x = layers.LSTM(50, return_sequences=False)(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(32, activation='relu')(x)
    out = layers.Dense(1)(x)
    m = models.Model(inp, out, name='LSTM_NASA_FD001')
    m.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3, clipnorm=1.0), loss='mse', metrics=['mae'])
    return m

model = build_model((WINDOW, len(ACTIVE_SENSORS)))
es = callbacks.EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True, verbose=1)
rl = callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=4, min_lr=1e-5, verbose=1)

history = model.fit(
    X_train_w, y_train_w,
    validation_data=(X_val_w, y_val_w),
    epochs=40,
    batch_size=128,
    callbacks=[es, rl],
    verbose=2
)

# Evaluaciones
pred_all = model.predict(X_test_w_all, verbose=0).ravel()
pred_last = model.predict(X_test_w_last, verbose=0).ravel()

rmse_all = np.sqrt(mean_squared_error(y_test_w_all, pred_all))
mae_all = mean_absolute_error(y_test_w_all, pred_all)

rmse_last = np.sqrt(mean_squared_error(y_test_w_last, pred_last))
mae_last = mean_absolute_error(y_test_w_last, pred_last)
score_last = nasa_score(y_test_w_last, pred_last)

print("="*60)
print(f"LSTM ALL Windows Test -> RMSE: {rmse_all:.2f}, MAE: {mae_all:.2f}")
print(f"LSTM LAST Window Test (100 motores) -> RMSE: {rmse_last:.2f}, MAE: {mae_last:.2f}, NASA Score: {score_last:.1f}")
print("="*60)
