"""Probe history/rate features for LightGBM standalone (not part of notebook)."""
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

def build(X, y, units, cycles, step):
    tab, yy, meta = [], [], []
    for u in np.unique(units):
        m = units == u; Xu, yu, cu = X[m], y[m], cycles[m]
        x0 = Xu[0]; early = Xu[:10].mean(0)
        for i in range(0, len(Xu) - W + 1, step):
            win = Xu[i:i+W]; cyc = cu[i+W-1]
            op, xs = win[:, :4], win[:, 4:]
            delta = xs[-1] - x0[4:]
            rate = delta / max(cyc - 1, 1)
            hist = Xu[:i+W]
            hmean = hist[:, 4:].mean(0) - early[4:]
            hstd = hist[:, 4:].std(0) - Xu[:10, 4:].std(0)
            f = np.hstack([cyc/100., op.mean(0), op[-1], xs.mean(0), xs[-1], xs.std(0),
                           xs[-10:].mean(0), xs[-1]-xs[0], xs[-5:].mean(0)-xs[:5].mean(0),
                           delta, rate, hmean, hstd])
            tab.append(f); yy.append(yu[i+W-1]); meta.append((u, cyc))
    return np.array(tab, np.float32), np.array(yy, np.float32), pd.DataFrame(meta, columns=['unit','cycle'])

Xtr, ytr, meta = build(X, Y, A[:,0], A[:,1], 3)
Xte, yte, metat = build(Xt, Yt, At[:,0], At[:,1], 2)
print('shapes', Xtr.shape, Xte.shape)
units = np.unique(meta['unit']); vm = (meta['unit']==units[-1]).values; tm = ~vm

def nasa(a, b):
    d = np.asarray(b)-np.asarray(a)
    return float(np.sum(np.where(d<0, np.exp(-d/13)-1, np.exp(d/10)-1)))

def ev(name, p):
    print(f'{name}: RMSE={np.sqrt(mean_squared_error(yte,p)):.3f} R2={r2_score(yte,p):.4f} NASA={nasa(yte,p):.1f}', flush=True)
    for u in np.unique(metat.unit):
        m = (metat.unit==u).values
        print('  unit', u, 'rmse', round(np.sqrt(mean_squared_error(yte[m], p[m])),2), 'bias', round(float((p[m]-yte[m]).mean()),2))

cfgs = [
 ('reg', dict(n_estimators=200, learning_rate=.02, num_leaves=15, max_depth=4, min_child_samples=100, reg_alpha=5., reg_lambda=10., colsample_bytree=.6, subsample=.7)),
 ('mid', dict(n_estimators=400, learning_rate=.03, num_leaves=31, max_depth=6, min_child_samples=40, reg_alpha=.5, reg_lambda=2., colsample_bytree=.8, subsample=.85)),
 ('deep', dict(n_estimators=600, learning_rate=.02, num_leaves=63, max_depth=8, min_child_samples=20, reg_alpha=0., reg_lambda=1., colsample_bytree=.8, subsample=.9)),
]
for name, c in cfgs:
    m = lgb.LGBMRegressor(**c, random_state=42, verbose=-1).fit(Xtr[tm], ytr[tm])
    ev('lgb_'+name, m.predict(Xte))
    pv = m.predict(Xtr[vm]); print('  val', round(np.sqrt(mean_squared_error(ytr[vm], pv)),3))
    if name == 'reg':
        imp = pd.Series(m.feature_importances_, index=[f'f{i}' for i in range(Xtr.shape[1])]).sort_values(ascending=False)
        print(imp.head(12).to_dict())

r = RidgeCV(alphas=np.logspace(-2,3,20)).fit(Xtr[tm], ytr[tm]); ev('ridge', r.predict(Xte))
print('ridge alpha', r.alpha_)
