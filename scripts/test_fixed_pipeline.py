import pathlib
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
from xgboost import XGBRegressor

CLIP = 125
WINDOW = 30
COLS = ['engine_id', 'cycle', 'setting1', 'setting2', 'setting3'] + [f's{i}' for i in range(1, 22)]

# Constantes identificadas en el EDA
CONST_COLS = ['setting3', 's1', 's5', 's10', 's16', 's18', 's19']
# Sensores informativos (14 sensores con varianza)
ACTIVE_SENSORS = [f's{i}' for i in range(1, 22) if f's{i}' not in CONST_COLS]

print("Columnas activas:", ACTIVE_SENSORS)

# Carga de datos
train = pd.read_csv('archive/CMaps/train_FD001.txt', sep=r'\s+', header=None, names=COLS)
test = pd.read_csv('archive/CMaps/test_FD001.txt', sep=r'\s+', header=None, names=COLS)
rul_df = pd.read_csv('archive/CMaps/RUL_FD001.txt', sep=r'\s+', header=None, names=['RUL'])

def prepare(df, rul_df=None, scaler=None, fit=False, feature_cols=ACTIVE_SENSORS):
    df = df.copy()
    max_cycle = df.groupby('engine_id')['cycle'].transform('max')
    
    if rul_df is not None:
        # En test: sumamos el RUL remanente real de RUL_FD001.txt a cada motor
        rul_map = dict(zip(range(1, len(rul_df) + 1), rul_df['RUL'].values))
        true_max_cycle = max_cycle + df['engine_id'].map(rul_map)
        df['RUL'] = (true_max_cycle - df['cycle']).clip(upper=CLIP)
    else:
        # En train: el motor llega hasta el fallo (RUL = 0 al final)
        df['RUL'] = (max_cycle - df['cycle']).clip(upper=CLIP)
        
    X = df[feature_cols].values
    if fit:
        scaler = scaler.fit(X)
    X_scaled = scaler.transform(X)
    y = df['RUL'].values
    meta = df[['engine_id', 'cycle']].copy()
    meta['RUL'] = y
    return X_scaled, y, meta, scaler

scaler = StandardScaler()
X_train, y_train, meta_train, scaler = prepare(train, scaler=scaler, fit=True)
X_test, y_test, meta_test, _ = prepare(test, rul_df=rul_df, scaler=scaler, fit=False)

print(f"X_train: {X_train.shape}, y_train mean: {y_train.mean():.2f}, max: {y_train.max()}, min: {y_train.min()}")
print(f"X_test:  {X_test.shape},  y_test mean: {y_test.mean():.2f}, max: {y_test.max()}, min: {y_test.min()}")

# NASA scoring function
def nasa_score(y_true, y_pred):
    d = np.asarray(y_pred) - np.asarray(y_true)
    score = np.where(d < 0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)
    return float(np.sum(score))

print("Data preparation check complete.")
