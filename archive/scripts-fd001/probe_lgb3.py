"""Probe normalized age-fraction target for LightGBM (not part of notebook)."""
import warnings, numpy as np, pandas as pd, h5py, lightgbm as lgb
warnings.filterwarnings('ignore')
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import RidgeCV

W = 50
with h5py.File('archive/CCMaps/N-CMAPSS_DS02-006.h5', 'r') as f:
    A = f['A_dev'][::100]; Wd = f['W_dev'][::100]; Xs = f['X_s_dev'][::100]; Y = f['Y_dev'][::100].ravel()
    At = f['A_test'][::100]; Wt = f['W_test'][::100]; Xst = f['X_s_test'][::100]; Yt = f['Y_test'][::100].ravel()
X = np.hstack([Wd, Xs]); Xt = np.hstack([Wt, Xst])
sc = StandardScaler().fit(X); X = sc.transform(X); Xt = sc.transform(Xt)

def build(X, y, units, cycles, step, rel=False):
    tab, yy, age, meta = [], [], [], []
    for u in np.unique(units):
        m = units == u; Xu, yu, cu = X[m], y[m], cycles[m]
        maxc = cu.max(); base = Xu[:20].mean(0)
        for i in range(0, len(Xu) - W + 1, step):
            win = Xu[i:i+W]; cyc = cu[i+W-1]
            op, xs = win[:, :4], win[:, 4:]
            f = [cyc/100., *op.mean(0), *op[-1], *xs.mean(0), *xs[-1], *xs.std(0),
                 *xs[-10:].mean(0), *xs[-1]-xs[0], *xs[-5:].mean(0)-xs[:5].mean(0)]
            if rel:
                f += [*(xs[-1]-base[4:]), *(xs.mean(0)-base[4:])]
            tab.append(f); yy.append(yu[i+W-1]); age.append(cyc/maxc); meta.append((u, cyc))
    return np.array(tab, np.float32), np.array(yy, np.float32), np.array(age, np.float32), pd.DataFrame(meta, columns=['unit','cycle'])

Xtr, ytr, atr, meta = build(X, Y, A[:,0], A[:,1], 3)
Xte, yte, ate, metat = build(Xt, Yt, At[:,0], At[:,1], 2)
units = np.unique(meta['unit']); vm = (meta['unit']==units[-1]).values; tm = ~vm
cyc_te = metat['cycle'].values

def nasa(a, b):
    d = np.asarray(b)-np.asarray(a)
    return float(np.sum(np.where(d<0, np.exp(-d/13)-1, np.exp(d/10)-1)))

def ev(name, p):
    print(f'{name}: RMSE={np.sqrt(mean_squared_error(yte,p)):.3f} R2={r2_score(yte,p):.4f} NASA={nasa(yte,p):.1f}', flush=True)
    for u in np.unique(metat.unit):
        m = (metat.unit==u).values
        print('  unit', u, 'rmse', round(np.sqrt(mean_squared_error(yte[m], p[m])),2), 'bias', round(float((p[m]-yte[m]).mean()),2))

for rel in [False, True]:
    Xt_, yt_, at_, me_ = build(X, Y, A[:,0], A[:,1], 3, rel)
    Xe_, ye_, ae_, metae_ = build(Xt, Yt, At[:,0], At[:,1], 2, rel)
    for name, c in [('reg', dict(n_estimators=300, learning_rate=.02, num_leaves=15, max_depth=4, min_child_samples=50, reg_alpha=1., reg_lambda=5., colsample_bytree=.8, subsample=.8)),
                    ('mid', dict(n_estimators=500, learning_rate=.03, num_leaves=31, max_depth=6, min_child_samples=30, reg_alpha=.1, reg_lambda=1., colsample_bytree=.8, subsample=.9))]:
        m = lgb.LGBMRegressor(**c, random_state=42, verbose=-1).fit(Xt_[tm], at_[tm])
        ahat = np.clip(m.predict(Xe_), 0.02, 0.98)
        rul = metae_['cycle'].values * (1-ahat)/ahat
        ev(f'lgb_age_{name}_rel{rel}', rul)
