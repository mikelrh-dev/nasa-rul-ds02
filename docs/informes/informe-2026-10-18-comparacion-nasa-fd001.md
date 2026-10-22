# Comparación NASA FD001 — resultados medidos

Todos los números salen de `notebook_nasa_fd001.ipynb` ejecutado de punta a punta
(0 celdas con error) el 18/10/2026. Métricas crudas: `models/v2_metrics.json`.

## Protocolo

- Entrenamiento: todas las ventanas de `train_FD001.txt`, RUL = `max_cycle - cycle` recortado a 125.
- Test: **solo la última ventana** de cada motor, comparada contra `RUL_FD001.txt` (clip 125).
- Train RMSE se mide por ventana; test RMSE/MAE por motor (no son la misma unidad).
- Modelos tabulares: ventana de 30 × 24 aplanada (720 features). LSTM: secuencia 30 × 24 (o 50 × 24 en la variante C).

## Tabla final

| Modelo | RMSE train | RMSE test | MAE test | Tiempo (s) | n motores |
|---|---|---|---|---|---|
| XGBoost baseline (por ciclo, media de ventana) | 14.02 | 26.16 | 20.27 | — | 100 |
| Random Forest (ventana aplanada) | 10.73 | 16.53 | 12.17 | 111.4 | 100 |
| **LightGBM (ventana aplanada)** | **7.34** | **13.42** | **10.33** | **7.7** | **100** |
| Linear Regression (ventana aplanada) | 16.61 | 15.94 | 13.07 | 1.9 | 100 |
| LSTM 2 capas 100-50 (baseline, w=30) | 11.24 | 15.14 | 11.77 | — | 100 |
| LSTM mejor variante (C, w=50) | 12.95 | 15.57 | 10.97 | 213.6 | 93 |


## Variantes LSTM

| Variante | RMSE train | RMSE test (sus motores) | RMSE test (mismo n=93) | MAE test | n |
|---|---|---|---|---|---|
| A: LSTM 3 capas 100-64-32 + Dropout 0.2 (w=30) | 10.38 | 15.91 | 16.24 | 11.27 | 100 |
| B: Bidirectional LSTM 100-50 + Dropout 0.2 (w=30) | 9.77 | 15.47 | 15.69 | 10.89 | 100 |
| C: LSTM 2 capas 100-50 + Dropout 0.2 (w=50) | 12.95 | 15.57 | 15.57 | 10.97 | 93 |

Ganadora entre las variantes: **C: LSTM 2 capas 100-50 + Dropout 0.2 (w=50)**. Objetivo RMSE test < 15: **no alcanzado** (15.57).

## Semáforo

Real (RUL_FD001.txt): 9 ROJO / 16 AMARILLO / 75 VERDE.

| Modelo | ROJO | AMARILLO | VERDE | Zona correcta |
|---|---|---|---|---|
| XGBoost | 0 | 4 | 96 | 76/100 (76.0%) |
| Random Forest | 7 | 11 | 82 | 85/100 (85.0%) |
| LightGBM | 10 | 11 | 79 | 89/100 (89.0%) |
| Linear Regression | 8 | 6 | 86 | 87/100 (87.0%) |
| LSTM 2 capas | 7 | 12 | 81 | 90/100 (90.0%) |
| LSTM best (50 ciclos) | 11 | 15 | 67 | 84/93 (90.3%) |

## Lectura

- El baseline XGBoost por ciclo (26.16) es el peor: promedia predicciones sin ver la trayectoria.
- Meter la ventana en un GBDT cambia el resultado: LightGBM 13.42, RF 16.53.
- LSTM 2 capas w=30: 15.14; mejor variante (C, w=50): 15.57 con 93 motores.
- Por tanto: la ventaja no es de la recurrencia, es de la ventana. LightGBM es el mejor coste/beneficio
  (7.7 s de entrenamiento frente a ~214 s de la mejor LSTM).

## Artefactos

- `models/xgb_FD001_baseline.joblib`, `models/lstm_FD001_2layer.h5`
- `models/rf_FD001_baseline.joblib`, `models/lgb_FD001_baseline.joblib`, `models/lr_FD001_baseline.joblib`
- `models/lstm_FD001_best.h5` + `models/lstm_FD001_best.json` (ventana y métricas)
- `models/test_eval_ultima_ventana.csv` (predicciones por motor de los 6 modelos)
- `models/v2_metrics.json` (todas las métricas de la ejecución)
