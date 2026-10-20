import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor

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

# RUL calculation
train_max = train.groupby('engine_id')['cycle'].transform('max')
train['RUL'] = (train_max - train['cycle']).clip(upper=CLIP)

test_max = test.groupby('engine_id')['cycle'].transform('max')
rul_map = dict(zip(range(1, len(rul_df) + 1), rul_df['RUL'].values))
test_true_max = test_max + test['engine_id'].map(rul_map)
test['RUL'] = (test_true_max - test['cycle']).clip(upper=CLIP)

# Rolling features for XGBoost: rolling mean & std (window 5 & 10)
def extract_tabular_features(df, sensor_cols=ACTIVE_SENSORS):
    feats = []
    # baseline sensors
    feats.append(df[sensor_cols])
    
    # rolling mean / std por motor
    for w in [5, 10]:
        rmean = df.groupby('engine_id')[sensor_cols].rolling(w, min_periods=1).mean().reset_index(level=0, drop=True)
        rmean.columns = [f'{c}_rmean_{w}' for c in sensor_cols]
        rstd = df.groupby('engine_id')[sensor_cols].rolling(w, min_periods=1).std().fillna(0).reset_index(level=0, drop=True)
        rstd.columns = [f'{c}_rstd_{w}' for c in sensor_cols]
        feats.extend([rmean, rstd])
        
    res = pd.concat(feats, axis=1)
    return res

X_train_tab = extract_tabular_features(train)
X_test_tab = extract_tabular_features(test)

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_tab)
X_test_scaled = scaler.transform(X_test_tab)

y_train = train['RUL'].values
y_test = test['RUL'].values

# Split train/val by engine
rng = np.random.RandomState(42)
eids = train['engine_id'].unique()
perm = rng.permutation(len(eids))
val_eids = set(eids[perm[:20]])
train_mask = ~train['engine_id'].isin(val_eids).values
val_mask = train['engine_id'].isin(val_eids).values

xgb = XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.03, subsample=0.8, colsample_bytree=0.8, random_state=42, n_jobs=-1)
xgb.fit(X_train_scaled[train_mask], y_train[train_mask])

# Evaluate XGBoost on full test cycles
pred_test_xgb = xgb.predict(X_test_scaled)
print(f"XGBoost all cycles RMSE: {np.sqrt(mean_squared_error(y_test, pred_test_xgb)):.2f}, MAE: {mean_absolute_error(y_test, pred_test_xgb):.2f}")

# Evaluate XGBoost on LAST cycle of each engine (standard benchmark)
last_cycle_mask = test.groupby('engine_id')['cycle'].transform('max') == test['cycle']
pred_last_xgb = pred_test_xgb[last_cycle_mask]
y_last_real = y_test[last_cycle_mask]

rmse_last = np.sqrt(mean_squared_error(y_last_real, pred_last_xgb))
mae_last = mean_absolute_error(y_last_real, pred_last_xgb)
score_last = nasa_score(y_last_real, pred_last_xgb)
print(f"XGBoost LAST window (100 engines) -> RMSE: {rmse_last:.2f}, MAE: {mae_last:.2f}, NASA Score: {score_last:.1f}")
