# Plan de Evolución Predictiva: De 7/10 a 9+/10 en N-CMAPSS DS02

## Diagnóstico de partida (Versión 4.1.0 — Nota: 7.0 / 10)
- **RMSE Global Test (motores 11, 14, 15):** `4.315 ± 0.045` ciclos (`R² = 0.9466`, `NASA Score = 2326.3`).
- **Debilidad 1 (Sesgo en Motor 14 y cancelación de errores):** El sesgo global (+0.185) esconde que el Motor 11 sobreestima (+3.027, RMSE 3.724) y el Motor 14 subestima severamente (-5.194, RMSE 8.044).
- **Debilidad 2 (Degradación a vida alta):** El MAE pasa de `1.126` en `RUL < 25` a `5.356` en `RUL [50, 75)` (4.8x mayor). La predicción máxima satura en `60.64` ciclos cuando la RUL real alcanza `73`.
- **Debilidad 3 (Horizonte temporal ciego):** Con `STRIDE = 100` y `WINDOW_SIZE = 50`, cada ventana abarca `0.44 ciclos de vuelo`. El modelo no observa evolución inter-ciclo.
- **Debilidad 4 (Meta-aprendiz ajustado en 1 solo motor):** En producción/test, `ridge_meta` y `lgb_meta` se ajustan únicamente sobre las predicciones del Motor 16 (`holdout`, RUL máx ~63), provocando que `lgb_meta` trunque cualquier extrapolación por encima de ~61 ciclos.

---

## Fase 1: Corrección del Meta-Aprendiz y Extrapolación a Vida Alta (Impacto rápido, sin tocar features)

### 1.1. Entrenar el Meta-Aprendiz sobre todo el vector Out-of-Fold (OOF) de `dev`
- **Problema actual:** `ridge_meta` y `lgb_meta` se ajustan solo en `hold_idx` (Motor 16).
- **Solución:** Aprovechar las predicciones fuera de fold (`oof['pred_lstm']`, `oof['pred_lgb']`) generadas en los 6 motores de `dev` para ajustar el meta-aprendiz sobre las 17.450 ventanas y los 6 perfiles de vida útil (que incluyen motores con vidas más largas que el Motor 16).
- **Cambio en el estimador meta:** Sustituir el `LGBMRegressor` del meta-aprendiz (que trunca las hojas en los extremos de RUL alta) por un estimador continuo capaz de extrapolar linealmente en el extremo superior (ej. `HuberRegressor` o `RidgeCV` con polinomio de grado 2 e interacción `p_lstm * p_lgb`), o entrenar el LightGBM base en un par de cuantiles (`alpha=0.35` para zona crítica y `alpha=0.50` / `L2` para el nivel real) pasando 3 columnas al meta-aprendiz: `[p_lstm, p_lgb_q35, p_lgb_l2]`.

---

## Fase 2: Características Multi-Ciclo y Calibración por Motor (Romper la barrera del Motor 14)

### 2.1. Contexto histórico inter-ciclo (Cycle-Level Memory)
- **Problema actual:** Una ventana de 50 muestras a `stride=100` solo ve medio vuelo (`0.44 ciclos`).
- **Solución:** Agregar en `features.py` descriptores causales a nivel de ciclo de vuelo:
  1. Calcular la media de los 14 residuos por cada `(unit, cycle)`.
  2. Añadir al vector de cada ventana la media exponencial lenta a lo largo de los ciclos previos del mismo motor (`cycle_ema_5`, `cycle_ema_15`) y la tasa de cambio inter-ciclo (`cycle_ trend = cycle_ema_5 - cycle_ema_15`).
  3. Esto da visión real de varios vuelos hacia atrás sin aumentar el tamaño del tensor 3D `X_seq`.

### 2.2. Anclaje de salud inicial suave para Árboles (Health Offset Correction)
- **Problema actual:** La ablación demostró que restar la línea base de los 3 primeros ciclos (`baseline_delta`) mejora el MAE del BiLSTM (`4.206 -> 3.892`) y su NASA Score (`3655 -> 3343`), pero deteriora el LightGBM (`7.113 -> 8.578`) al reemplazar el valor absoluto del residuo.
- **Solución:** No reemplazar los residuos brutos en `X_tab`, sino **mantener los residuos originales para el LightGBM** y usar la línea base sana por motor en la rama del BiLSTM (o añadir en `X_tab` únicamente el resumen escalar de salud inicial de los 4 sensores críticos de núcleo: `T48`, `T50`, `Ps30`, `Wf`). Esto corrige el sesgo estático entre los motores 11, 14 y 15.

---

## Fase 3: Cuantificación de Incertidumbre y Validación Exhaustiva (Nivel Producción 9+/10)

### 3.1. Intervalos de Predicción Conformales (Split Conformal Prediction)
- En mantenimiento aeronáutico, una predicción puntual sin incertidumbre no es desplegable.
- Utilizar los residuos fuera de fold (`oof_residuals = y_oof - p_ens_oof`) agrupados por tramo de RUL predicha para calcular bandas de confianza calibradas al 90% (`[RUL_lower_90, RUL_pred, RUL_upper_90]`).

### 3.2. Reporte Leave-One-Unit-Out (LOUO) y Métricas Desglosadas como Titular
- Elevar la tabla por motor (`Motor 11`, `Motor 14`, `Motor 15`) y el **Macro-RMSE por motor** (media de los 3 RMSE individuales, donde cada motor pesa 1/3 independientemente de sus ventanas) a métrica principal junto al RMSE global ponderado por ventana.