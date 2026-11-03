"""Additional dual-pooling variants (not part of notebook)."""
import os, time, warnings
warnings.filterwarnings('ignore')
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
import numpy as np, pandas as pd, h5py
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
import tensorflow as tf
from tensorflow.keras import layers, models, callbacks

W = 50
with h5py.File('archive/CCMaps/N-CMAPSS_DS02-006.h5', 'r') as f:
    A = f['A_dev'][::100]; Wd = f['W_dev'][::100]; Xs = f['X_s_dev'][::100]; Y = f['Y_dev'][::100].ravel()
    At = f['A_test'][::100]; Wt = f['W_test'][::100]; Xst = f['X_s_test'][::100]; Yt = f['Y_test'][::100].ravel()
X = np.hstack([Wd, Xs]); Xt = np.hstack([Wt, Xst])
sc = StandardScaler().fit(X); X = sc.transform(X); Xt = sc.transform(Xt)

def seqs(X, y, U, C, step):
    S, yy, meta = [], [], []
    for u in np.unique(U):
        m = U == u; Xu, yu, cu = X[m], y[m], C[m]
        for i in range(0, len(Xu)-W+1, step):
            S.append(Xu[i:i+W]); yy.append(yu[i+W-1]); meta.append((u, cu[i+W-1]))
    return np.array(S, np.float32), np.array(yy, np.float32), pd.DataFrame(meta, columns=['unit','cycle'])

S, y, meta = seqs(X, Y, A[:,0], A[:,1], 3)
St, yt, metat = seqs(Xt, Yt, At[:,0], At[:,1], 2)

def nasa(a, b):
    d = np.asarray(b)-np.asarray(a)
    return float(np.sum(np.where(d<0, np.exp(-d/13)-1, np.exp(d/10)-1)))

def build(seed, width=64, pooling='full'):
    tf.keras.backend.clear_session(); tf.random.set_seed(seed); np.random.seed(seed)
    inp = layers.Input((W, 18))
    x = layers.BatchNormalization()(inp)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True), name='bilstm_layer_1')(x)
    x = layers.Dropout(0.2)(x)
    x = layers.Bidirectional(layers.LSTM(64, return_sequences=True), name='bilstm_layer_2')(x)
    x = layers.Dropout(0.2)(x)
    parts = [layers.Lambda(lambda z: z[:, -1, :])(x), layers.GlobalAveragePooling1D()(x)]
    if pooling == 'full':
        parts.append(layers.GlobalMaxPooling1D()(x))
    x = layers.Concatenate()(parts)
    x = layers.Dropout(0.2)(x)
    x = layers.Dense(width, activation='relu')(x)
    m = models.Model(inp, layers.Dense(1)(x))
    m.compile(optimizer=tf.keras.optimizers.Adam(0.001), loss=tf.keras.losses.Huber(delta=10.0), metrics=['mae'])
    return m

def run(tag, seed, val_unit, width=64, pooling='full'):
    vm = (meta['unit'] == val_unit).values; tm = ~vm
    m = build(seed, width, pooling)
    t0 = time.time()
    m.fit(S[tm], y[tm], validation_data=(S[vm], y[vm]), batch_size=128, epochs=26, verbose=2,
          callbacks=[callbacks.EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True),
                     callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=2)])
    p = m.predict(St, verbose=0).ravel()
    print(f'RESULT {tag}: RMSE={np.sqrt(mean_squared_error(yt,p)):.3f} R2={r2_score(yt,p):.4f} NASA={nasa(yt,p):.1f} time={time.time()-t0:.1f}s', flush=True)
    np.save(f'scripts/pred_{tag}.npy', p)

run('dual_w32_u16_s42', 42, 16.0, width=32)
run('dual_u16_s7', 7, 16.0)
run('dual_u16_s123', 123, 16.0)
run('dual_u18_s42', 42, 18.0)
run('dual_nomax_u16_s42', 42, 16.0, pooling='lastgap')
run('old_u16_s7', 7, 16.0, width=32)
