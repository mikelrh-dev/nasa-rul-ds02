"""Probe unit-relative health features for LightGBM (not part of notebook)."""
import warnings, numpy as np, pandas as pd, h5py, lightgbm as lgb
warnings.filterwarnings('ignore')
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score

W = 50
with h5py.File('archive/CCMaps/N-CMAPSS_DS02-006.h5', 'r') as f:
    A = f['A_dev'][::100]; Wd = f['W_dev'][::100]; Xs = f['X_s_dev'][::100]; Y = f['Y_dev'][::100].ravel()
    At = f['A_test'][::100]; Wt = f['W_test'][::100]; Xst = f['X_s_test'][::100]; Yt = f['Y_test'][::100].ravel()
scw = StandardScaler().fit(Wd)
Wtr = scw.transform(Wd); Wte = scw.transform(Wt)
poly = PolynomialFeatures(2, include_bias=False).fit(Wtr)
Ptr, Pte = poly.transform(Wtr), poly.transform(Wte)
res_tr = np.zeros_like(Xs); res_te = np.zeros_like(Xst)
for j in range(Xs.shape[1]):
    r = Ridge(alpha=1.0).fit(Ptr, Xs[:, j])
    res_tr[:, j] = Xs[:, j] - r.predict(Ptr)
    res_te[:, j] = Xst[:, j] - r.predict(Pte)
scr = StandardScaler().fit(res_tr)
res_tr = scr.transform(res_tr); res_te = scr.transform(res_te)

def build(Wd, Xs, y, units, cycles, step, mode):
    tab, yy, meta = [], [], []
    X = np.hstack([Wd, Xs]); n_op = Wd.shape[1]
    for u in np.unique(units):
        m = units == u; Xu, yu, cu = X[m], y[m], cycles[m]
        base = Xu[:20]; bmean = base[:, n_op:].mean(0); bstd = base[:, n_op:].std(0) + 1e-6
        for i in range(0, len(Xu)-W+1, step):
            win = Xu[i:i+W]; cyc = cu[i+W-1]
            op, xs = win[:, :n_op], win[:, n_op:]
            f = [cyc/100., *op.mean(0), *op[-1], *xs.mean(0), *xs[-1], *xs.std(0),
                 *xs[-10:].mean(0), *xs[-1]-xs[0], *xs[-5:].mean(0)-xs[:5].mean(0)]
            if mode >= 1:
                hist = Xu[:i+W, n_op:]
                f += [*(xs[-1]-bmean)/bstd]
                f += [*(hist.mean(0)-bmean)/bstd]
            if mode >= 2:
                # per-sensor percentile of current value within history
                f += [float((hist[:, j] <= xs[-1, j]).mean()) for j in range(hist.shape[1])]
                # normalized time since each sensor's historical extreme
                f += [float((i+W-1-np.argmax(hist[:, j]))/(i+W)) for j in range(hist.shape[1])]
            tab.append(f); yy.append(yu[i+W-1]); meta.append((u, cyc))
    return np.array(tab, np.float32), np.array(yy, np.float32), pd.DataFrame(meta, columns=['unit','cycle'])

def nasa(a, b):
    d = np.asarray(b)-np.asarray(a)
    return float(np.sum(np.where(d<0, np.exp(-d/13)-1, np.exp(d/10)-1)))

for mode in [0, 1, 2]:
    Xtr, ytr, meta = build(Wtr, res_tr, Y, A[:,0], A[:,1], 3, mode)
    Xte, yte, metat = build(Wte, res_te, Yt, At[:,0], At[:,1], 2, mode)
    units = np.unique(meta['unit']); vm = (meta['unit']==units[-1]).values; tm = ~vm
    m = lgb.LGBMRegressor(n_estimators=300, learning_rate=.02, num_leaves=15, max_depth=4,
                          min_child_samples=50, reg_alpha=1., reg_lambda=5.,
                          colsample_bytree=.8, subsample=.8, random_state=42, verbose=-1).fit(Xtr[tm], ytr[tm])
    p = m.predict(Xte)
    print(f'mode {mode} nfeat {Xtr.shape[1]}: RMSE={np.sqrt(mean_squared_error(yte,p)):.3f} R2={r2_score(yte,p):.4f} NASA={nasa(yte,p):.1f} val={np.sqrt(mean_squared_error(ytr[vm],m.predict(Xtr[vm]))):.3f}', flush=True)
    for u in np.unique(metat.unit):
        mm = (metat.unit==u).values
        print('  unit', u, round(np.sqrt(mean_squared_error(yte[mm], p[mm])),2), round(float((p[mm]-yte[mm]).mean()),2))
