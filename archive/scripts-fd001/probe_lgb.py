"""Diagnose LightGBM standalone error on DS02 (not part of the notebook)."""
import os, warnings
warnings.filterwarnings('ignore')
import numpy as np, pandas as pd, h5py, lightgbm as lgb
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.linear_model import LinearRegression

SEED = 42
W = 50
with h5py.File('archive/CCMaps/N-CMAPSS_DS02-006.h5', 'r') as f:
    A = f['A_dev'][::100]; Wd = f['W_dev'][::100]; Xs = f['X_s_dev'][::100]; Y = f['Y_dev'][::100].ravel()
    At = f['A_test'][::100]; Wt = f['W_test'][::100]; Xst = f['X_s_test'][::100]; Yt = f['Y_test'][::100].ravel()
X = np.hstack([Wd, Xs]); Xt = np.hstack([Wt, Xst])
sc = StandardScaler().fit(X); X = sc.transform(X); Xt = sc.transform(Xt)

def build(X, y, units, cycles, step, extra=False):
    seq, tab, yy, meta = [], [], [], []
    for u in np.unique(units):
        m = units == u; Xu, yu, cu = X[m], y[m], cycles[m]
        base = Xu[:20].mean(0)
        for i in range(0, len(Xu) - W + 1, step):
            win = Xu[i:i+W]; cyc = cu[i+W-1]
            op, xs = win[:, :4], win[:, 4:]
            f = [cyc/100., *op.mean(0), *op[-1], *xs.mean(0), *xs[-1], *xs.std(0),
                 *xs[-10:].mean(0), *xs[-1]-xs[0], *xs[-5:].mean(0)-xs[:5].mean(0)]
            if extra:
                f += [*(xs.mean(0) - base[4:]), *(xs[-1] - base[4:]),
                      *(np.abs(xs[-1] - base[4:])), *(xs.std(0) - Xu[:20, 4:].std(0))]
            tab.append(f); yy.append(yu[i+W-1]); meta.append((u, cyc))
    return np.array(tab, np.float32), np.array(yy, np.float32), pd.DataFrame(meta, columns=['unit','cycle'])

Xtr, ytr, meta = build(X, Y, A[:,0], A[:,1], 3, extra=True)
Xte, yte, metat = build(Xt, Yt, At[:,0], At[:,1], 2, extra=True)
units = np.unique(meta['unit']); vm = (meta['unit']==units[-1]).values; tm=~vm
print('shapes', Xtr.shape, Xte.shape, 'val unit', units[-1])
print('y_test mean/std', yte.mean(), yte.std(), 'pred mean target RMSE', np.sqrt(mean_squared_error(yte, np.full_like(yte, ytr.mean()))))

def ev(name, p):
    print(f'{name}: RMSE={np.sqrt(mean_squared_error(yte,p)):.3f} R2={r2_score(yte,p):.4f}')

for params in [
    dict(n_estimators=200, learning_rate=0.02, num_leaves=15, max_depth=4, min_child_samples=100, reg_alpha=5., reg_lambda=10., colsample_bytree=0.6, subsample=0.7),
    dict(n_estimators=500, learning_rate=0.03, num_leaves=31, max_depth=6, min_child_samples=30, reg_alpha=0.1, reg_lambda=1., colsample_bytree=0.8, subsample=0.9),
    dict(n_estimators=800, learning_rate=0.02, num_leaves=63, max_depth=8, min_child_samples=20, reg_alpha=0., reg_lambda=1., colsample_bytree=0.8, subsample=0.9),
]:
    m = lgb.LGBMRegressor(**params, random_state=SEED, verbose=-1)
    m.fit(Xtr[tm], ytr[tm])
    ev('LGB '+str(params['num_leaves'])+'/'+str(params['n_estimators']), m.predict(Xte))
    pv = m.predict(Xtr[vm]); print('   val RMSE', np.sqrt(mean_squared_error(ytr[vm], pv)))

# cycle only linear
lr = LinearRegression().fit(Xtr[tm][:, :1], ytr[tm]); ev('cyc lin', lr.predict(Xte[:, :1]))
# LGB cycle only
m = lgb.LGBMRegressor(n_estimators=300, learning_rate=.05, num_leaves=31, random_state=SEED, verbose=-1).fit(Xtr[tm][:, :1], ytr[tm]); ev('cyc lgb', m.predict(Xte[:, :1]))
print('pred stats best-ish', np.percentile(m.predict(Xte[:, :1]), [0,25,50,75,100]))
