"""Recover the q35 LightGBM recipe that produced pred_lgb_q35.npy."""
import warnings, numpy as np, pandas as pd, h5py, lightgbm as lgb
warnings.filterwarnings('ignore')
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_squared_error, r2_score

W = 50
with h5py.File('archive/CCMaps/N-CMAPSS_DS02-006.h5', 'r') as f:
    A = f['A_dev'][::100]; Wd = f['W_dev'][::100]; Xs = f['X_s_dev'][::100]; Y = f['Y_dev'][::100].ravel()
    At = f['A_test'][::100]; Wt = f['W_test'][::100]; Xst = f['X_s_test'][::100]; Yt = f['Y_test'][::100].ravel()
scw = StandardScaler().fit(Wd); Wtr = scw.transform(Wd); Wte = scw.transform(Wt)
poly = PolynomialFeatures(2, include_bias=False).fit(Wtr)
Ptr, Pte = poly.transform(Wtr), poly.transform(Wte)
res_tr = np.zeros_like(Xs); res_te = np.zeros_like(Xst)
for j in range(Xs.shape[1]):
    r = Ridge(alpha=1.0).fit(Ptr, Xs[:, j])
    res_tr[:, j] = Xs[:, j] - r.predict(Ptr)
    res_te[:, j] = Xst[:, j] - r.predict(Pte)
scr = StandardScaler().fit(res_tr); res_tr = scr.transform(res_tr); res_te = scr.transform(res_te)

def build(Xs_, units, cycles, step):
    tab, yy, meta = [], [], []
    for u in np.unique(units):
        m = units == u; Xu, cu = Xs_[m], cycles[m]
        for i in range(0, len(Xu) - W + 1, step):
            win = Xu[i:i+W]; cyc = cu[i+W-1]
            op, xs = win[:, :4], win[:, 4:]
            tab.append(np.hstack([cyc/100., op.mean(0), op[-1], xs.mean(0), xs[-1], xs.std(0),
                                  xs[-10:].mean(0), xs[-1]-xs[0], xs[-5:].mean(0)-xs[:5].mean(0)]))
            meta.append((u, cyc))
    return np.array(tab, np.float32), pd.DataFrame(meta, columns=['unit','cycle'])

Xtr, meta = build(np.hstack([Wtr, res_tr]), A[:,0], A[:,1], 3)
Xte, metat = build(np.hstack([Wte, res_te]), At[:,0], At[:,1], 2)
ys = []
for u in np.unique(At[:,0]):
    m = At[:,0] == u; yu = Yt[m]
    for i in range(0, len(yu) - W + 1, 2):
        ys.append(yu[i+W-1])
yte = np.array(ys, np.float32)
ytr = np.array([Y[(A[:,0]==u)][i+W-1] for u, i in [(u, i) for u in np.unique(A[:,0]) for i in range(0, (A[:,0]==u).sum()-W+1, 3)]], np.float32)

def nasa(a, b):
    d = np.asarray(b) - np.asarray(a)
    return float(np.sum(np.where(d < 0, np.exp(-d/13)-1, np.exp(d/10)-1)))

save = np.load('scripts/pred_lgb_q35.npy')
print('saved', np.sqrt(mean_squared_error(yte, save)), nasa(yte, save), 'corr', np.corrcoef(save, np.zeros_like(save))[0,1] if False else '')
units = np.unique(meta['unit']); vm = (meta['unit']==units[-1]).values; tm = ~vm

cands = [
 ('quant_reg', dict(objective='quantile', alpha=0.35, n_estimators=300, learning_rate=.02, num_leaves=15, max_depth=4, min_child_samples=50, reg_alpha=1., reg_lambda=5., colsample_bytree=.8, subsample=.8)),
 ('quant_mid', dict(objective='quantile', alpha=0.35, n_estimators=500, learning_rate=.03, num_leaves=31, max_depth=6, min_child_samples=30, reg_alpha=.1, reg_lambda=1., colsample_bytree=.8, subsample=.9)),
 ('l2_reg', dict(n_estimators=300, learning_rate=.02, num_leaves=15, max_depth=4, min_child_samples=50, reg_alpha=1., reg_lambda=5., colsample_bytree=.8, subsample=.8)),
]
for name, c in cands:
    m = lgb.LGBMRegressor(**c, random_state=42, verbose=-1).fit(Xtr[tm], ytr[tm])
    p = m.predict(Xte)
    print(f'{name}: RMSE={np.sqrt(mean_squared_error(yte,p)):.3f} R2={r2_score(yte,p):.4f} NASA={nasa(yte,p):.1f} '
          f'corr_saved={np.corrcoef(p, save)[0,1]:.4f} maxdiff={np.abs(p-save).max():.3f}')
