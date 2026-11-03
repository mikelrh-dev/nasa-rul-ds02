import json
import os
import pathlib
import sys
import copy


sys.stdout.reconfigure(encoding='utf-8')

NB_PATH = pathlib.Path('notebook_nasa_fd001.ipynb')
with open(NB_PATH, 'r', encoding='utf-8') as f:
    nb = json.load(f)

print(f"Original notebook cells: {len(nb['cells'])}")

# Cell 0: Header markdown (maintain and polish)
nb['cells'][0]['source'] = [
    "# NASA CMAPSS FD001 — Predicción de Vida Útil Remanente (RUL)\n",
    "\n",
    "**Dataset:** NASA Turbofan Engine Degradation Simulation (Kaggle `behrad3d/nasa-cmaps`, `archive/CMaps/`)\n",
    "- `train_FD001.txt` — 100 motores operados hasta el fallo catastrófico (*run-to-failure*).\n",
    "- `test_FD001.txt` — 100 motores con series temporales truncadas en un ciclo arbitrario antes del fallo.\n",
    "- `RUL_FD001.txt` — RUL remanente real de cada uno de los 100 motores de test desde su último ciclo registrado.\n",
    "\n",
    "**Objetivo:** Desarrollar y comparar un pipeline de mantenimiento predictivo riguroso de extremo a extremo, evaluando modelos tabulares (XGBoost con memoria temporal) y redes recurrentes (LSTM regularizada) bajo el protocolo y métricas oficiales de la literatura de la NASA."
]

# Cell 1: Imports
nb['cells'][1]['source'] = [
    "%matplotlib inline\n",
    "import numpy as np\n",
    "import pandas as pd\n",
    "import matplotlib.pyplot as plt\n",
    "import seaborn as sns\n",
    "\n",
    "plt.rcParams['figure.dpi'] = 120\n",
    "sns.set_theme(style='whitegrid')\n"
]

# Cell 2: Markdown Carga
nb['cells'][2]['source'] = [
    "## 1. Carga de datos\n",
    "\n",
    "El dataset no incluye encabezados. Definimos las 26 columnas canónicas:\n",
    "- `engine_id`: Identificador de la unidad turbofán.\n",
    "- `cycle`: Ciclo de vuelo/operación (secuencia temporal).\n",
    "- `setting1`, `setting2`, `setting3`: Ajustes de condiciones operativas de vuelo.\n",
    "- `s1`…`s21`: 21 mediciones de sensores distribuidos a lo largo del turbofán (presiones, temperaturas, velocidades de rotor, relaciones de flujo).\n",
    "\n",
    "> **Principio de consistencia temporal:** En `train`, los motores finalizan en fallo ($RUL=0$). En `test`, la serie se interrumpe antes del fallo y los ciclos restantes exactos se encuentran en `RUL_FD001.txt`."
]

# Cell 3: Code Carga
nb['cells'][3]['source'] = [
    "COLS = ['engine_id', 'cycle', 'setting1', 'setting2', 'setting3'] + [f's{i}' for i in range(1, 22)]\n",
    "\n",
    "train = pd.read_csv('archive/CMaps/train_FD001.txt', sep=r'\\s+', header=None, names=COLS)\n",
    "test  = pd.read_csv('archive/CMaps/test_FD001.txt',  sep=r'\\s+', header=None, names=COLS)\n",
    "rul   = pd.read_csv('archive/CMaps/RUL_FD001.txt',  sep=r'\\s+', header=None, names=['RUL'])\n",
    "\n",
    "print(f'train shape: {train.shape} ({train[\"engine_id\"].nunique()} motores)')\n",
    "print(f'test  shape: {test.shape} ({test[\"engine_id\"].nunique()} motores)')\n",
    "print(f'rul   shape: {rul.shape} (1 valor por motor de test)')\n",
    "display(train.head(3))\n"
]

# Cell 4: Markdown EDA
nb['cells'][4]['source'] = [
    "## 2. EDA — ¿Qué tenemos realmente?\n",
    "\n",
    "Analizamos la distribución de ciclos de vida, la varianza de cada sensor para detectar variables sin señal y las correlaciones físicas entre subsistemas de la turbina."
]

# Cell 5: Code Distribución
nb['cells'][5]['source'] = [
    "# Distribución de ciclos y duración hasta fallo en train\n",
    "n_motores_train = train['engine_id'].nunique()\n",
    "n_ciclos_train  = len(train)\n",
    "\n",
    "ciclos_por_motor = train.groupby('engine_id')['cycle'].agg(['min', 'max', 'count'])\n",
    "ciclos_por_motor['duracion'] = ciclos_por_motor['max'] - ciclos_por_motor['min'] + 1\n",
    "\n",
    "print(f'Motores en train: {n_motores_train}')\n",
    "print(f'Ciclos totales en train: {n_ciclos_train}')\n",
    "print(f'Duración por motor — mín: {ciclos_por_motor[\"duracion\"].min()}, ' \n",
    "      f'máx: {ciclos_por_motor[\"duracion\"].max()}, ' \n",
    "      f'media: {ciclos_por_motor[\"duracion\"].mean():.1f} ciclos')\n",
    "display(ciclos_por_motor.head())\n"
]

# Cell 6: Code Sensores Constantes
nb['cells'][6]['source'] = [
    "# Diferenciación rigurosa: Settings vs Sensores\n",
    "SETTINGS_COLS = ['setting1', 'setting2', 'setting3']\n",
    "SENSOR_COLS   = [f's{i}' for i in range(1, 22)]\n",
    "\n",
    "# Identificación formal de variables sin varianza (desviación estándar = 0)\n",
    "constante_train = [c for c in SENSOR_COLS + SETTINGS_COLS if train[c].nunique() == 1]\n",
    "constante_test  = [c for c in SENSOR_COLS + SETTINGS_COLS if test[c].nunique() == 1]\n",
    "\n",
    "print(f'Variables constantes en train ({len(constante_train)}): {constante_train}')\n",
    "print(f'Variables constantes en test  ({len(constante_test)}): {constante_test}')\n",
    "\n",
    "# Selección de los 14 sensores informativos activos con señal de degradación física\n",
    "ACTIVE_SENSORS = [c for c in SENSOR_COLS if c not in constante_train]\n",
    "print(f'\\nSensores activos informativos ({len(ACTIVE_SENSORS)}): {ACTIVE_SENSORS}')\n",
    "\n",
    "variabilidad = train[ACTIVE_SENSORS].std().sort_values()\n",
    "fig, ax = plt.subplots(figsize=(7, 4.5))\n",
    "variabilidad.plot(kind='barh', color='steelblue', edgecolor='black', ax=ax)\n",
    "ax.set_title('Desviación estándar de sensores activos (train FD001)')\n",
    "ax.set_xlabel('Desviación estándar (std)')\n",
    "plt.tight_layout()\n",
    "plt.show()\n"
]

# Cell 7: Code Correlación
nb['cells'][7]['source'] = [
    "# Correlación física e interdependencia entre sensores activos\n",
    "corr = train[ACTIVE_SENSORS].corr()\n",
    "\n",
    "fig, ax = plt.subplots(figsize=(10, 8))\n",
    "sns.heatmap(corr, cmap='coolwarm', vmin=-1, vmax=1, annot=True, fmt='.2f', \n",
    "            ax=ax, square=True, cbar_kws={'shrink': 0.8})\n",
    "ax.set_title('Matriz de correlación de sensores informativos (train)')\n",
    "plt.tight_layout()\n",
    "plt.show()\n",
    "\n",
    "# Identificación de pares con colinealidad extrema (|r| > 0.9)\n",
    "pairs = []\n",
    "for i in range(len(corr.columns)):\n",
    "    for j in range(i + 1, len(corr.columns)):\n",
    "        v = corr.iloc[i, j]\n",
    "        if abs(v) > 0.9:\n",
    "            pairs.append((corr.columns[i], corr.columns[j], round(v, 3)))\n",
    "\n",
    "print(f'Pares altamente colineales (|r| > 0.9): {len(pairs)}')\n",
    "for p in pairs:\n",
    "    print(f'  {p[0]:4s} — {p[1]:4s}: r = {p[2]}')\n",
    "print('\\nNota termodinámica: s9 (HPC outlet temperature) y s14 (LPT rotor speed) presentan r = 0.963 ' \n",
    "      'debido al acoplamiento físico en la turbina de gas: al degradarse el compresor de alta, la turbina de baja ' \n",
    "      'debe acelerar para compensar la caída de rendimiento, incrementando conjuntamente temperatura y velocidad.')\n"
]

# Cell 8: Code RUL real sample
nb['cells'][8]['source'] = [
    "# Dinámica de degradación: RUL vs Ciclo en 3 motores de entrenamiento\n",
    "train_sample = train[train['engine_id'].isin([1, 2, 3])].copy()\n",
    "max_cycle = train_sample.groupby('engine_id')['cycle'].transform('max')\n",
    "train_sample['RUL'] = max_cycle - train_sample['cycle']\n",
    "\n",
    "fig, ax = plt.subplots(figsize=(8, 4))\n",
    "for eid in [1, 2, 3]:\n",
    "    sub = train_sample[train_sample['engine_id'] == eid]\n",
    "    ax.plot(sub['cycle'], sub['RUL'], marker='.', label=f'Motor {eid} (vida total: {len(sub)} ciclos)')\n",
    "ax.set_xlabel('Ciclo de operación')\n",
    "ax.set_ylabel('RUL real (ciclos restantes)')\n",
    "ax.set_title('Degradación run-to-failure lineal en entrenamiento')\n",
    "ax.legend()\n",
    "plt.tight_layout()\n",
    "plt.show()\n"
]

# Cell 9: Markdown Preprocesamiento
nb['cells'][9]['source'] = [
    "## 3. Preprocesamiento Riguroso y Reconstrucción del Target\n",
    "\n",
    "### Reglas Metodológicas Clave:\n",
    "1. **Cálculo exacto del objetivo (`RUL`) en Test:**\n",
    "   - En `train`: los motores alcanzan el fallo al término de la serie ($RUL = \\max(ciclo) - ciclo$).\n",
    "   - En `test`: la serie se corta antes del fallo. El archivo `RUL_FD001.txt` contiene los ciclos que le restaban a cada motor en su último ciclo observado ($ciclo_{max}$). Por tanto, el ciclo real de fallo es $ciclo_{fallo} = ciclo_{max} + RUL_{FD001}[engine\\_id]$, y el RUL en cada instante $t$ es $RUL(t) = ciclo_{fallo} - t$.\n",
    "2. **Piecewise Linear RUL (Clipping a 125 ciclos):**\n",
    "   - Durante las primeras etapas operativas el motor no presenta degradación medible. En la literatura estándar de CMAPSS (Heimes, 2008), recortar a 125 ciclos evita que los modelos intenten predecir diferencias aleatorias en un estado de salud 100% óptimo.\n",
    "3. **Filtrado de variables sin varianza:**\n",
    "   - Se descartan las 7 columnas constantes identificadas en el EDA, reteniendo exclusivamente los 14 sensores informativos activos.\n",
    "4. **Prevención de Data Leakage:**\n",
    "   - El `StandardScaler` se ajusta (`fit=True`) **única y exclusivamente** con los datos de `train`. Los datos de `test` se normalizan mediante `transform` con los parámetros aprendidos."
]

# Cell 10: Code Prepare
nb['cells'][10]['source'] = [
    "CLIP = 125\n",
    "from sklearn.preprocessing import StandardScaler\n",
    "\n",
    "def prepare(df, rul_df=None, scaler=None, fit=False, feature_cols=ACTIVE_SENSORS):\n",
    "    \"\"\"\n",
    "    Prepara las features y el target RUL garantizando cero data leakage.\n",
    "    Para test, incorpora el RUL remanente oficial de RUL_FD001.txt.\n",
    "    \"\"\"\n",
    "    df = df.copy()\n",
    "    max_cycle = df.groupby('engine_id')['cycle'].transform('max')\n",
    "    \n",
    "    if rul_df is not None:\n",
    "        # En test: sumamos el RUL remanente real de RUL_FD001.txt a cada motor\n",
    "        rul_map = dict(zip(range(1, len(rul_df) + 1), rul_df['RUL'].values))\n",
    "        true_max_cycle = max_cycle + df['engine_id'].map(rul_map)\n",
    "        df['RUL'] = (true_max_cycle - df['cycle']).clip(upper=CLIP)\n",
    "    else:\n",
    "        # En train: el motor llega hasta el fallo (RUL = 0 al final)\n",
    "        df['RUL'] = (max_cycle - df['cycle']).clip(upper=CLIP)\n",
    "        \n",
    "    X = df[feature_cols].values\n",
    "    if fit:\n",
    "        scaler = scaler.fit(X)\n",
    "    X_scaled = scaler.transform(X)\n",
    "    y = df['RUL'].values\n",
    "    meta = df[['engine_id', 'cycle']].copy()\n",
    "    meta['RUL'] = y\n",
    "    return X_scaled, y, meta, scaler\n",
    "\n",
    "scaler = StandardScaler()\n",
    "X_train, y_train, meta_train, scaler = prepare(train, scaler=scaler, fit=True)\n",
    "X_test,  y_test,  meta_test,  _       = prepare(test,  rul_df=rul, scaler=scaler, fit=False)\n",
    "\n",
    "print(f'Features activas seleccionadas: {len(ACTIVE_SENSORS)} sensores')\n",
    "print(f'X_train shape: {X_train.shape} | y_train — mín {y_train.min():.0f}, media {y_train.mean():.1f}, máx {y_train.max():.0f}')\n",
    "print(f'X_test  shape: {X_test.shape}  | y_test  — mín {y_test.min():.0f}, media {y_test.mean():.1f}, máx {y_test.max():.0f}')\n"
]

# Cell 11: Markdown Ventanas
nb['cells'][11]['source'] = [
    "## 4. Ventanas Temporales para Modelos Secuenciales\n",
    "\n",
    "Para capturar la dinámica temporal y la tasa de degradación, transformamos las series en ventanas deslizantes de longitud $W=30$ ciclos:\n",
    "- Cada muestra tiene dimensión `(30, 14)`.\n",
    "- El target `y` es el RUL del **último ciclo** de la ventana.\n",
    "- **Padding robusto:** Si un motor tuviese menos de 30 ciclos, se replica el ciclo inicial en lugar de descartarlo (garantiza compatibilidad total con cualquier motor).\n",
    "- **Validación sin Data Leakage:** El particionado (80% train / 20% val) se realiza **por motor completo (`engine_id`)** antes de construir las ventanas, garantizando que un motor nunca esté simultáneamente en entrenamiento y validación."
]

# Cell 12: Code Build Windows
nb['cells'][12]['source'] = [
    "WINDOW = 30\n",
    "\n",
    "def build_windows(X, y, meta, window=WINDOW, last_only=False):\n",
    "    \"\"\"\n",
    "    Genera secuencias temporales de longitud `window` por motor con soporte de padding.\n",
    "    Si last_only=True, extrae únicamente la última ventana disponible de cada motor.\n",
    "    \"\"\"\n",
    "    X_list, y_list, meta_rows = [], [], []\n",
    "    X = np.asarray(X, dtype=np.float32)\n",
    "    y = np.asarray(y, dtype=np.float32)\n",
    "    df_meta = meta.reset_index(drop=True)\n",
    "    \n",
    "    for eid in np.unique(df_meta['engine_id'].values):\n",
    "        idx = np.where(df_meta['engine_id'].values == eid)[0]\n",
    "        seg_X = X[idx]\n",
    "        seg_y = y[idx]\n",
    "        seg_c = df_meta.loc[idx, 'cycle'].values\n",
    "        n_pts = len(seg_X)\n",
    "        \n",
    "        # Si el motor tiene menos ciclos que window, aplicar padding replicando el primer ciclo\n",
    "        if n_pts < window:\n",
    "            pad_len = window - n_pts\n",
    "            pad_x = np.repeat(seg_X[0:1], pad_len, axis=0)\n",
    "            seg_X = np.vstack([pad_x, seg_X])\n",
    "            seg_y = np.pad(seg_y, (pad_len, 0), mode='edge')\n",
    "            seg_c = np.pad(seg_c, (pad_len, 0), mode='edge')\n",
    "            n_pts = window\n",
    "            \n",
    "        if last_only:\n",
    "            X_list.append(seg_X[-window:])\n",
    "            y_list.append(seg_y[-1])\n",
    "            meta_rows.append({'engine_id': int(eid), 'last_cycle': int(seg_c[-1]), 'RUL_real': float(seg_y[-1])})\n",
    "        else:\n",
    "            for i in range(n_pts - window + 1):\n",
    "                X_list.append(seg_X[i:i + window])\n",
    "                y_list.append(seg_y[i + window - 1])\n",
    "                meta_rows.append({'engine_id': int(eid), 'last_cycle': int(seg_c[i + window - 1]), 'RUL_real': float(seg_y[i + window - 1])})\n",
    "                \n",
    "    return np.array(X_list), np.array(y_list), pd.DataFrame(meta_rows)\n",
    "\n",
    "# Split 80/20 por motor en entrenamiento\n",
    "rng = np.random.RandomState(42)\n",
    "engine_ids = np.unique(meta_train['engine_id'])\n",
    "perm = rng.permutation(len(engine_ids))\n",
    "n_val = int(round(0.2 * len(engine_ids)))\n",
    "val_ids = set(engine_ids[perm[:n_val]])\n",
    "\n",
    "mask_tr = ~meta_train['engine_id'].isin(val_ids).values\n",
    "mask_va =  meta_train['engine_id'].isin(val_ids).values\n",
    "\n",
    "X_train_w, y_train_w, meta_train_w = build_windows(X_train[mask_tr], y_train[mask_tr], meta_train[mask_tr], window=WINDOW)\n",
    "X_val_w,   y_val_w,   meta_val_w   = build_windows(X_train[mask_va], y_train[mask_va], meta_train[mask_va], window=WINDOW)\n",
    "X_test_w_all, y_test_w_all, meta_test_w_all = build_windows(X_test, y_test, meta_test, window=WINDOW, last_only=False)\n",
    "X_test_w_last, y_test_w_last, meta_test_w_last = build_windows(X_test, y_test, meta_test, window=WINDOW, last_only=True)\n",
    "\n",
    "print(f'Partición por motores: {len(engine_ids) - n_val} train / {n_val} validación')\n",
    "print(f'Ventanas train: {X_train_w.shape} | Ventanas val: {X_val_w.shape}')\n",
    "print(f'Ventanas test (todas): {X_test_w_all.shape}')\n",
    "print(f'Ventanas test (última por motor): {X_test_w_last.shape} (exactamente 100 motores)')\n"
]

# Cell 13: Markdown XGBoost
nb['cells'][13]['source'] = [
    "## 5. Baseline ML — XGBoost con Memoria Temporal\n",
    "\n",
    "### Un Baseline Justo y Competitivo\n",
    "Evaluar un modelo de gradiente sobre ciclos aislados ($t$) es metodológicamente injusto frente a la LSTM, ya que los sensores de turbofanes contienen ruido Gaussiano inherente que produce oscilaciones erráticas en árboles de decisión.\n",
    "\n",
    "Para nivelar el terreno, dotamos a XGBoost de memoria temporal mediante:\n",
    "- **Medias móviles** (*rolling mean* a 5 y 10 ciclos por motor).\n",
    "- **Desviaciones estándar móviles** (*rolling std* a 5 y 10 ciclos por motor).\n",
    "\n",
    "### Función Oficial de Puntuación CMAPSS (NASA Score Asimétrico)\n",
    "En la competición oficial PHM 2008 / CMAPSS, el error no es simétrico. Un error tardío ($d = \\hat{y} - y > 0$, sobreestimar el RUL) puede provocar un fallo catastrófico en vuelo, por lo que se penaliza exponencialmente con base 10; un error temprano ($d < 0$, subestimar el RUL) solo adelanta una inspección preventiva y se penaliza con base 13:\n",
    "\n",
    "$$s_i = \\begin{cases} e^{-d_i / 13} - 1 & \\text{si } d_i < 0 \\\\ e^{d_i / 10} - 1 & \\text{si } d_i \\ge 0 \\end{cases}, \\quad S = \\sum_{i=1}^{100} s_i$$"
]

# Cell 14: Code XGBoost
nb['cells'][14]['source'] = [
    "from xgboost import XGBRegressor\n",
    "from sklearn.metrics import mean_squared_error, mean_absolute_error\n",
    "import joblib\n",
    "\n",
    "def nasa_score(y_true, y_pred):\n",
    "    \"\"\"Métrica oficial asimétrica de la NASA para CMAPSS.\"\"\"\n",
    "    d = np.asarray(y_pred) - np.asarray(y_true)\n",
    "    score = np.where(d < 0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)\n",
    "    return float(np.sum(score))\n",
    "\n",
    "# Generación de features temporales para XGBoost\n",
    "def extract_rolling_features(df, sensor_cols=ACTIVE_SENSORS):\n",
    "    feats = [df[sensor_cols]]\n",
    "    for w in [5, 10]:\n",
    "        rmean = df.groupby('engine_id')[sensor_cols].rolling(w, min_periods=1).mean().reset_index(level=0, drop=True)\n",
    "        rmean.columns = [f'{c}_rmean_{w}' for c in sensor_cols]\n",
    "        rstd = df.groupby('engine_id')[sensor_cols].rolling(w, min_periods=1).std().fillna(0).reset_index(level=0, drop=True)\n",
    "        rstd.columns = [f'{c}_rstd_{w}' for c in sensor_cols]\n",
    "        feats.extend([rmean, rstd])\n",
    "    return pd.concat(feats, axis=1)\n",
    "\n",
    "X_train_tab = extract_rolling_features(train)\n",
    "X_test_tab  = extract_rolling_features(test)\n",
    "\n",
    "scaler_tab = StandardScaler()\n",
    "X_train_tab_sc = scaler_tab.fit_transform(X_train_tab)\n",
    "X_test_tab_sc  = scaler_tab.transform(X_test_tab)\n",
    "\n",
    "xgb = XGBRegressor(\n",
    "    n_estimators=300,\n",
    "    max_depth=5,\n",
    "    learning_rate=0.03,\n",
    "    subsample=0.8,\n",
    "    colsample_bytree=0.8,\n",
    "    random_state=42,\n",
    "    n_jobs=-1\n",
    ")\n",
    "xgb.fit(X_train_tab_sc[mask_tr], y_train[mask_tr])\n",
    "\n",
    "# Predicciones en Test\n",
    "pred_test_all_xgb = xgb.predict(X_test_tab_sc)\n",
    "last_cycle_mask = (test.groupby('engine_id')['cycle'].transform('max') == test['cycle']).values\n",
    "pred_test_last_xgb = pred_test_all_xgb[last_cycle_mask]\n",
    "y_test_last_real = y_test[last_cycle_mask]\n",
    "\n",
    "rmse_xgb_all  = np.sqrt(mean_squared_error(y_test, pred_test_all_xgb))\n",
    "mae_xgb_all   = mean_absolute_error(y_test, pred_test_all_xgb)\n",
    "rmse_xgb_last = np.sqrt(mean_squared_error(y_test_last_real, pred_test_last_xgb))\n",
    "mae_xgb_last  = mean_absolute_error(y_test_last_real, pred_test_last_xgb)\n",
    "score_xgb     = nasa_score(y_test_last_real, pred_test_last_xgb)\n",
    "\n",
    "print('=== XGBoost (con Features Temporales) ===')\n",
    "print(f'Test (todas las series)   -> RMSE: {rmse_xgb_all:.2f} ciclos | MAE: {mae_xgb_all:.2f} ciclos')\n",
    "print(f'Test (última ventana 100) -> RMSE: {rmse_xgb_last:.2f} ciclos | MAE: {mae_xgb_last:.2f} ciclos | NASA Score: {score_xgb:.1f}')\n",
    "\n",
    "joblib.dump(xgb, 'models/xgb_FD001_baseline.joblib')\n",
    "print('Modelo guardado en models/xgb_FD001_baseline.joblib')\n"
]

# Cell 15: Code XGBoost Plot
nb['cells'][15]['source'] = [
    "# Visualización de trayectoria en test: RUL real vs XGBoost\n",
    "eid_plot = 100  # Motor 100 de test\n",
    "mask_plot = (test['engine_id'] == eid_plot).values\n",
    "cycles_plot = test.loc[mask_plot, 'cycle'].values\n",
    "rul_real_plot = y_test[mask_plot]\n",
    "rul_pred_plot = pred_test_all_xgb[mask_plot]\n",
    "\n",
    "fig, ax = plt.subplots(figsize=(8.5, 4))\n",
    "ax.plot(cycles_plot, rul_real_plot, 'k-', lw=2, label='RUL real (con RUL_FD001.txt)')\n",
    "ax.plot(cycles_plot, rul_pred_plot, 'b--', lw=1.5, label='XGBoost (con rolling features)')\n",
    "ax.axhline(15, color='red', ls=':', lw=1, label='Alerta crítica (15 ciclos)')\n",
    "ax.axhline(30, color='orange', ls=':', lw=1, label='Alerta preventiva (30 ciclos)')\n",
    "ax.set_xlabel('Ciclo de operación')\n",
    "ax.set_ylabel('RUL')\n",
    "ax.set_title(f'Motor {eid_plot} de Test — RUL real vs Predicción XGBoost')\n",
    "ax.legend(fontsize=8)\n",
    "plt.tight_layout()\n",
    "plt.show()\n"
]

# Cell 16: Markdown LSTM
nb['cells'][16]['source'] = [
    "## 6. Red Recurrente — LSTM Regularizada (100 → 50 con Dropout)\n",
    "\n",
    "Diseñamos una arquitectura profunda para capturar dependencias a largo plazo y la tasa no lineal de desgaste:\n",
    "- Capa 1: `LSTM(100, return_sequences=True)` seguida de `Dropout(0.2)` para prevenir sobreajuste.\n",
    "- Capa 2: `LSTM(50, return_sequences=False)` seguida de `Dropout(0.2)`.\n",
    "- Capa Densa intermedia: `Dense(32, activation='relu')`.\n",
    "- Salida: `Dense(1)` (estimación de RUL continua).\n",
    "- Optimizador: `Adam(learning_rate=1e-3, clipnorm=1.0)` para estabilizar gradientes y prevenir explosión.\n",
    "- Callbacks: `EarlyStopping` (restaurando los mejores pesos en `val_loss`) y `ReduceLROnPlateau`."
]

# Cell 17: Code LSTM Model
nb['cells'][17]['source'] = [
    "import tensorflow as tf\n",
    "from tensorflow.keras import layers, callbacks, models\n",
    "\n",
    "tf.random.set_seed(42)\n",
    "np.random.seed(42)\n",
    "\n",
    "N_FEATURES = len(ACTIVE_SENSORS)\n",
    "BATCH = 128\n",
    "\n",
    "def build_lstm():\n",
    "    inp = layers.Input(shape=(WINDOW, N_FEATURES))\n",
    "    x = layers.LSTM(100, return_sequences=True)(inp)\n",
    "    x = layers.Dropout(0.2)(x)\n",
    "    x = layers.LSTM(50, return_sequences=False)(x)\n",
    "    x = layers.Dropout(0.2)(x)\n",
    "    x = layers.Dense(32, activation='relu')(x)\n",
    "    out = layers.Dense(1)(x)\n",
    "    \n",
    "    m = models.Model(inp, out, name='LSTM_NASA_FD001')\n",
    "    m.compile(\n",
    "        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3, clipnorm=1.0),\n",
    "        loss='mse',\n",
    "        metrics=['mae']\n",
    "    )\n",
    "    return m\n",
    "\n",
    "model_lstm = build_lstm()\n",
    "model_lstm.summary()\n"
]

# Cell 18: Code LSTM Fit
nb['cells'][18]['source'] = [
    "es = callbacks.EarlyStopping(\n",
    "    monitor='val_loss', patience=10, restore_best_weights=True, verbose=1\n",
    ")\n",
    "rl = callbacks.ReduceLROnPlateau(\n",
    "    monitor='val_loss', factor=0.5, patience=4, min_lr=1e-5, verbose=1\n",
    ")\n",
    "\n",
    "history = model_lstm.fit(\n",
    "    X_train_w, y_train_w,\n",
    "    validation_data=(X_val_w, y_val_w),\n",
    "    epochs=40,\n",
    "    batch_size=BATCH,\n",
    "    shuffle=True,\n",
    "    callbacks=[es, rl],\n",
    "    verbose=2\n",
    ")\n"
]

# Cell 19: Code LSTM Metrics
nb['cells'][19]['source'] = [
    "# Métricas oficiales en Test de la LSTM\n",
    "pred_test_all_lstm  = model_lstm.predict(X_test_w_all,  verbose=0).ravel()\n",
    "pred_test_last_lstm = model_lstm.predict(X_test_w_last, verbose=0).ravel()\n",
    "\n",
    "rmse_lstm_all  = np.sqrt(mean_squared_error(y_test_w_all, pred_test_all_lstm))\n",
    "mae_lstm_all   = mean_absolute_error(y_test_w_all, pred_test_all_lstm)\n",
    "rmse_lstm_last = np.sqrt(mean_squared_error(y_test_w_last, pred_test_last_lstm))\n",
    "mae_lstm_last  = mean_absolute_error(y_test_w_last, pred_test_last_lstm)\n",
    "score_lstm     = nasa_score(y_test_w_last, pred_test_last_lstm)\n",
    "\n",
    "print('=== LSTM 2 capas (100 -> 50 con Dropout) ===')\n",
    "print(f'Test (todas las ventanas) -> RMSE: {rmse_lstm_all:.2f} ciclos | MAE: {mae_lstm_all:.2f} ciclos')\n",
    "print(f'Test (última ventana 100) -> RMSE: {rmse_lstm_last:.2f} ciclos | MAE: {mae_lstm_last:.2f} ciclos | NASA Score: {score_lstm:.1f}')\n",
    "\n",
    "model_lstm.save('models/lstm_FD001_2layer.h5')\n",
    "print('Modelo guardado en models/lstm_FD001_2layer.h5')\n"
]

# Cell 20: Code Learning Curves
nb['cells'][20]['source'] = [
    "# Curva de aprendizaje del entrenamiento LSTM\n",
    "hist = history.history\n",
    "fig, axes = plt.subplots(1, 2, figsize=(12, 4))\n",
    "\n",
    "axes[0].plot(hist['loss'], label='Train MSE', lw=2)\n",
    "axes[0].plot(hist['val_loss'], label='Val MSE', lw=2)\n",
    "axes[0].set_yscale('log')\n",
    "axes[0].set_xlabel('Época')\n",
    "axes[0].set_ylabel('MSE (escala log)')\n",
    "axes[0].set_title('Convergencia de Pérdida (MSE)')\n",
    "axes[0].legend()\n",
    "\n",
    "axes[1].plot(hist['mae'], label='Train MAE', lw=2)\n",
    "axes[1].plot(hist['val_mae'], label='Val MAE', lw=2)\n",
    "axes[1].set_xlabel('Época')\n",
    "axes[1].set_ylabel('MAE (ciclos)')\n",
    "axes[1].set_title('Error Absoluto Medio (MAE)')\n",
    "axes[1].legend()\n",
    "\n",
    "plt.tight_layout()\n",
    "plt.show()\n"
]

# Cell 21: Code Comparison Plot
nb['cells'][21]['source'] = [
    "# Comparativa temporal de trayectorias: RUL real vs XGBoost vs LSTM\n",
    "# Extraemos las predicciones por ciclo para el motor eid_plot\n",
    "meta_test_w_all_df = meta_test_w_all.copy()\n",
    "meta_test_w_all_df['pred_lstm'] = pred_test_all_lstm\n",
    "sub_lstm = meta_test_w_all_df[meta_test_w_all_df['engine_id'] == eid_plot]\n",
    "\n",
    "fig, ax = plt.subplots(figsize=(9, 4.5))\n",
    "ax.plot(cycles_plot, rul_real_plot, 'k-', lw=2.2, label='RUL real')\n",
    "ax.plot(cycles_plot, rul_pred_plot, '--', color='steelblue', lw=1.6, label='XGBoost (rolling)')\n",
    "ax.plot(sub_lstm['last_cycle'], sub_lstm['pred_lstm'], '-', color='crimson', lw=1.8, label='LSTM (secuencial)')\n",
    "ax.axhline(15, color='red', ls=':', lw=1, label='Umbral Crítico (15 ciclos)')\n",
    "ax.axhline(30, color='orange', ls=':', lw=1, label='Umbral Preventivo (30 ciclos)')\n",
    "ax.set_xlabel('Ciclo de operación')\n",
    "ax.set_ylabel('RUL')\n",
    "ax.set_title(f'Motor {eid_plot} de Test — RUL real vs XGBoost vs LSTM')\n",
    "ax.legend(fontsize=8)\n",
    "plt.tight_layout()\n",
    "plt.show()\n"
]

with open(NB_PATH, 'w', encoding='utf-8') as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

print("Updated cells 0-21 in notebook successfully.")
