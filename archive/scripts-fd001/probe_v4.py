"""Quick probe of the v4 feature set and dual-pooling BiLSTM (not part of the notebook)."""
import os, time, warnings
warnings.filterwarnings('ignore')
os.environ.setdefault('TF_CPP_MIN_LOG_LEVEL', '2')
import numpy as np, pandas as pd, h5py, lightgbm as lgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks

SEED = 42
np.random.seed(SEED); tf.random.set_seed(SEED)
WINDOW_SIZE = 50
STRIDE = 100

with h5py.File('archive/CCMaps/N-CMAPSS_DS02-006.h5', 'r') as f:
    A_tr = f['A_dev'][::STRIDE]; W_tr = f['W_dev'][::STRIDE]
    Xs_tr = f['X_s_dev'][::STRIDE]; Y_tr = f['Y_dev'][::STRIDE].ravel()
    A_te = f['A_test'][::STRIDE]; W_te = f['W_test'][::STRIDE]
    Xs_te = f['X_s_test'][::STRIDE]; Y_te = f['Y_test'][::STRIDE].ravel()

Xtr = np.hstack([W_tr, Xs_tr]); Xte = np.hstack([W_te, Xs_te])
scaler = StandardScaler().fit(Xtr)
Xtr = scaler.transform(Xtr); Xte = scaler.transform(Xte)
unit_tr, cyc_tr = A_tr[:, 0], A_tr[:, 1]
unit_te, cyc_te = A_te[:, 0], A_te[:, 1]
print('rows', Xtr.shape, Xte.shape)


def make_windows(X, y, units, cycles, step):
    seq, tab, yy, meta = [], [], [], []
    for u in np.unique(units):
        m = units == u
        Xu, yu, cu = X[m], y[m], cycles[m]
        for i in range(0, len(Xu) - WINDOW_SIZE + 1, step):
            win = Xu[i:i + WINDOW_SIZE]
            cyc = cu[i + WINDOW_SIZE - 1]
            w_op, w_xs = win[:, :4], win[:, 4:]
            op_feat = np.hstack([w_op.mean(0), w_op[-1]])
            xs_mean, xs_last, xs_std = w_xs.mean(0), w_xs[-1], w_xs.std(0)
            xs_ema10 = w_xs[-10:].mean(0)
            xs_diff = w_xs[-1] - w_xs[0]
            xs_slope = w_xs[-5:].mean(0) - w_xs[:5].mean(0)
            tab_feat = np.hstack([cyc / 100.0, op_feat, xs_mean, xs_last,
                                  xs_std, xs_ema10, xs_diff, xs_slope])
            seq.append(win); tab.append(tab_feat); yy.append(yu[i + WINDOW_SIZE - 1])
            meta.append((u, cyc))
    return (np.array(seq, np.float32), np.array(tab, np.float32),
            np.array(yy, np.float32), pd.DataFrame(meta, columns=['unit', 'cycle']))


t0 = time.time()
Xtr_seq, Xtr_tab, ytr, meta = make_windows(Xtr, Y_tr, unit_tr, cyc_tr, 3)
Xte_seq, Xte_tab, yte, meta_te = make_windows(Xte, Y_te, unit_te, cyc_te, 2)
print('windows', Xtr_seq.shape, Xtr_tab.shape, Xte_seq.shape, Xte_tab.shape, f'{time.time()-t0:.1f}s')

units = np.unique(meta['unit']); val_u = units[-1]
vm = (meta['unit'] == val_u).values; tm = ~vm

def nasa(a, b):
    d = np.asarray(b).ravel() - np.asarray(a).ravel()
    return float(np.sum(np.where(d < 0, np.exp(-d / 13.0) - 1, np.exp(d / 10.0) - 1)))

def show(name, p):
    print(f'{name}: RMSE={np.sqrt(mean_squared_error(yte, p)):.3f} MAE={mean_absolute_error(yte, p):.3f} R2={r2_score(yte, p):.4f} NASA={nasa(yte, p):.1f}')

# LightGBM standalone with cycle feature
m = lgb.LGBMRegressor(n_estimators=200, learning_rate=0.02, num_leaves=15, max_depth=4,
                      min_child_samples=100, reg_alpha=5.0, reg_lambda=10.0,
                      colsample_bytree=0.6, subsample=0.7, random_state=SEED, verbose=-1)
m.fit(Xtr_tab[tm], ytr[tm])
show('LGBM 93f', m.predict(Xte_tab))


def build(input_shape):
    inp = layers.Input(shape=input_shape, name='input_window')
    x = layers.BatchNormalization(name='batch_norm_input')(inp)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True), name='bilstm_layer_1')(x)
    x = layers.Dropout(0.2, name='dropout_1')(x)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True), name='bilstm_layer_2')(x)
    x = layers.Dropout(0.2, name='dropout_2')(x)
    x = layers.Concatenate(name='dual_temporal_pooling')([
        layers.Lambda(lambda z: z[:, -1, :], name='last_timestep')(x),
        layers.GlobalAveragePooling1D(name='gap')(x),
        layers.GlobalMaxPooling1D(name='gmp')(x),
    ])
    x = layers.Dropout(0.2, name='dropout_pool')(x)
    x = layers.Dense(64, activation='relu', name='dense_proj')(x)
    return models.Model(inp, layers.Dense(1, name='rul_output')(x), name='BiLSTM_Champion_RUL')

model = build((WINDOW_SIZE, Xtr_seq.shape[2]))
model.compile(optimizer=tf.keras.optimizers.Adam(0.001), loss=tf.keras.losses.Huber(delta=10.0), metrics=['mae'])
model.summary()
t0 = time.time()
h = model.fit(Xtr_seq[tm], ytr[tm], validation_data=(Xtr_seq[vm], ytr[vm]), batch_size=128,
              epochs=22, verbose=2,
              callbacks=[callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True, verbose=1),
                         callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2, verbose=1)])
print(f'train time {time.time()-t0:.1f}s epochs={len(h.history["loss"])}')
p_te = model.predict(Xte_seq, verbose=0).ravel()
show('BiLSTM v4', p_te)
print('val preds saved')
np.savez('scripts/probe_v4_cache.npz', p_te=p_te, yte=yte, ytr=ytr,
         p_lgb_te=m.predict(Xte_tab), p_lgb_tr=m.predict(Xtr_tab))
