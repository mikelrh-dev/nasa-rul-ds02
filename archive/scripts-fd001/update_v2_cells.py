import json
import pathlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

NB_PATH = pathlib.Path('notebook_nasa_fd001.ipynb')
with open(NB_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

# Update cell 23
nb['cells'][23]['source'] = [
    "import json\n",
    "import pathlib\n",
    "import time\n",
    "\n",
    "import joblib\n",
    "from IPython.display import display\n",
    "from sklearn.ensemble import RandomForestRegressor\n",
    "from sklearn.linear_model import LinearRegression\n",
    "from sklearn.pipeline import make_pipeline\n",
    "\n",
    "# Sensores informativos activos seleccionados en el EDA (14 sensores)\n",
    "SENSOR_COLS = ACTIVE_SENSORS\n",
    "N_SENSORS = len(SENSOR_COLS)\n",
    "print(f'features activas para V2: {N_SENSORS} -> {SENSOR_COLS}')\n",
    "\n",
    "# RUL real de test por motor: fuente de verdad para evaluar\n",
    "rul_txt = pathlib.Path('archive/CMaps/RUL_FD001.txt').read_text(encoding='utf-8')\n",
    "rul_vals = [int(x) for x in rul_txt.replace('\\r', '').split()]\n",
    "rul_df = pd.DataFrame({'engine_id': range(1, len(rul_vals) + 1), 'RUL_real': rul_vals})\n",
    "rul_df['RUL_real'] = rul_df['RUL_real'].clip(upper=CLIP)\n",
    "\n",
    "print(f'motores test: {len(rul_df)} | RUL real min {rul_df.RUL_real.min()} ' \n",
    "      f'media {rul_df.RUL_real.mean():.1f} max {rul_df.RUL_real.max()}')\n",
    "display(rul_df.head(3))\n"
]

# Update cell 26
nb['cells'][26]['source'] = [
    "# Ventanas de 30 ciclos: todas para entrenar, última por motor para evaluar\n",
    "Xtr30, ytr30, mtr30 = build_windows(X_train, y_train, meta_train, WINDOW)\n",
    "Xte30_all, yte30_all, mte30_all = build_windows(X_test, y_test, meta_test, WINDOW)\n",
    "\n",
    "mte30_last = mte30_all[mte30_all['es_ultima']].reset_index(drop=True)\n",
    "mte30_last = mte30_last.merge(rul_df, on='engine_id', how='left')\n",
    "Xte30_last = Xte30_all[mte30_all['es_ultima'].values]\n",
    "\n",
    "print('ventanas train:', Xtr30.shape, '| motores test evaluados:', len(mte30_last))\n",
    "\n",
    "# --- baseline XGBoost (con features temporales evaluado en la última ventana) ---\n",
    "pred_xgb_last = pred_test_last_xgb\n",
    "\n",
    "# --- baseline LSTM 2 capas ---\n",
    "lstm2 = tf.keras.models.load_model('models/lstm_FD001_2layer.h5', compile=False)\n",
    "lstm2.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3, clipnorm=1.0),\n",
    "              loss='mse', metrics=['mae'])\n",
    "pred_lstm2_last = lstm2.predict(Xte30_last, verbose=0).ravel()\n",
    "\n",
    "rmse_xgb, mae_xgb, n_xgb, d_xgb = evaluar_ultima(pred_xgb_last, mte30_last)\n",
    "rmse_lstm2, mae_lstm2, n_lstm2, d_lstm2 = evaluar_ultima(pred_lstm2_last, mte30_last)\n",
    "rmse_train_xgb = float(rmse_xgb_all)\n",
    "\n",
    "print(f'XGBoost  (con rolling features) -> test {rmse_xgb:.2f} / MAE {mae_xgb:.2f}')\n",
    "print(f'LSTM 2c  (train ventana {rmse_lstm_all:.2f}) -> test {rmse_lstm2:.2f} / MAE {mae_lstm2:.2f}')\n"
]

# Update cell 37 (feature importance of XGBoost)
nb['cells'][37]['source'] = [
    "fi_df = pd.DataFrame({'sensor': X_train_tab.columns, 'importance': xgb.feature_importances_})\n",
    "fi_df = fi_df.sort_values('importance', ascending=False).reset_index(drop=True)\n",
    "key = ['s2', 's3', 's4', 's7', 's11', 's12', 's15']\n",
    "fi_df['es_key'] = fi_df['sensor'].apply(lambda x: any(k in x for k in key))\n",
    "\n",
    "print('Top 10 features temporales por importancia:')\n",
    "display(fi_df.head(10)[['sensor', 'importance', 'es_key']].round(4))\n",
    "\n",
    "plt.figure(figsize=(9, 6))\n",
    "sns.barplot(data=fi_df.head(15), y='sensor', x='importance', hue='es_key', dodge=False, legend=False,\n",
    "            palette={True: 'crimson', False: 'steelblue'})\n",
    "plt.xlabel('Importancia (Gini gain)')\n",
    "plt.ylabel('Feature')\n",
    "plt.title('Feature Importance XGBoost — Sensores y Lags Clave')\n",
    "plt.tight_layout()\n",
    "plt.show()\n"
]

with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Cells 23, 26, 37 updated successfully.")
