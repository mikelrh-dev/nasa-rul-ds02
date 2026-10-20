"""Probe unit-lifespan estimation from early data (not part of notebook)."""
import warnings, numpy as np, h5py
warnings.filterwarnings('ignore')
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import RidgeCV, LinearRegression
from sklearn.metrics import mean_squared_error

W = 50
with h5py.File('archive/CCMaps/N-CMAPSS_DS02-006.h5', 'r') as f:
    A = f['A_dev'][::100]; Wd = f['W_dev'][::100]; Xs = f['X_s_dev'][::100]; Y = f['Y_dev'][::100].ravel()
    At = f['A_test'][::100]; Wt = f['W_test'][::100]; Xst = f['X_s_test'][::100]; Yt = f['Y_test'][::100].ravel()
X = np.hstack([Wd, Xs]); Xt = np.hstack([Wt, Xst])
sc = StandardScaler().fit(X); X = sc.transform(X); Xt = sc.transform(Xt)

def unit_feats(X, units, cycles, early=50):
    feats, life = [], []
    for u in np.unique(units):
        m = units == u; Xu = X[m]; cu = cycles[m]
        e = Xu[:early]
        # descriptors of the earliest part of the trajectory
        feats.append(np.hstack([e.mean(0), e.std(0), e[-1] - e[0], e[:10].mean(0), e.min(0), e.max(0)]))
        life.append(cu.max())
    return np.array(feats), np.array(life)

F, L = unit_feats(X, A[:,0], A[:,1])
Ft, Lt = unit_feats(Xt, At[:,0], At[:,1])
print('dev life', L, 'test life', Lt)
print('feature shape', F.shape)
for i in range(len(L)):
    tr = np.arange(len(L)) != i
    for name, model in [('ridge', RidgeCV(alphas=np.logspace(-2, 3, 20))),
                        ('gbr', GradientBoostingRegressor(n_estimators=100, max_depth=2, learning_rate=.05, random_state=0))]:
        model.fit(F[tr], L[tr])
        print(i, name, 'pred', round(float(model.predict(F[i:i+1])[0]), 1), 'true', L[i])
for name, model in [('ridge', RidgeCV(alphas=np.logspace(-2, 3, 20))),
                    ('gbr', GradientBoostingRegressor(n_estimators=100, max_depth=2, learning_rate=.05, random_state=0))]:
    model.fit(F, L)
    pred = model.predict(Ft)
    print(name, 'test lifespan pred', np.round(pred, 1), 'true', Lt, 'RUL rmse', np.sqrt(mean_squared_error(Yt, np.clip(pred[:,None] - At[:,1:2], 0, None))))
