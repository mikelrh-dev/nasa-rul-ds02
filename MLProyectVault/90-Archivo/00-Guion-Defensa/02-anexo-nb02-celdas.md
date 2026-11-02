---
title: Anexo NB02 celdas
course: DS02-RUL
block: B0 — Guion defensa
node: A2
status: en-curso
tags:
  - anexo
  - nb02
---

# Anexo NB02 celdas (18 códigos)

## Idea central

NB02 decide: ablación medida, beta fuera de fold, híbrido + banda.

## Celdas

| Celda | Hace | .py que llama | Imprime |
|---|---|---|---|
| 1-3 puente | recarga `artifacts/` NB01 | `np.load/joblib` | `[LOAD NB1 OK] dev (17450,50,19), test (6196,50,19), bilstm recargado` |
| 5 compat | alias evaluar/mostrar | `metrics.py` | `[FASE A OK]` |
| 8 ablación | `run_seed` con/sin `cyc_norm` + línea base sana | `pipeline.py:run_seed` | BiLSTM 5.419→6.513 sin ciclo, base sana 5.998; LGBM se derrumba 6.297→8.667 |
| 9 extra | tabla `extra` EMA | `smoothing.py` | curiosear, no decide |
| 11 titular | `tabla_modelos` titular | `metrics.py:evaluate_predictions` | híbrido el mejor |
| 14 OOF | `oof_base_predictions` 3 folds | `pipeline.py:oof_base_predictions` | 269.9s, folds `[[2,10],[5,18],[20,16]]` |
| 15 beta_hat | `select_beta_grouped` mediana | `stacking.py:select_beta_grouped` | beta 1.0, dispersión min 0 max 1 |
| 16 legado | `in_sample_beta_diagnostic` | `stacking.py` | RMSE 6.347 vs 9.335, cociente 0.68 = defecto visible |
| 18 meta | `fit_meta_learners` en motor 16 | `stacking.py:fit_meta_learners` | ridge alpha 7.848, coef `[0.1368,0.7672]`, beta 1.0 |
| 19 titular | híbrido+EMA5 | `metrics.py + smoothing.py` | `4.276 + NASA 2322.4`, ¿mejora? True/True |
| 21 extra EMA | EMA 10/5/3 | `smoothing.py` | +1.563 del BiLSTM al híbrido |
| 23 por motor | `macro_rmse` | `metrics.py:macro_rmse` | 11:3.867, 14:8.018, 15:2.662, macro 4.849 vs global 4.276 |
| 25 banda | `fit_conformal` OOF 17450 | `conformal.py:fit_conformal` | ancho medio 23.49, tramo alto `[-24.41,-16.99]` |
| 26 cobertura | `empirical_coverage` | `conformal.py` | test 100% (sobre-cubre, se publica) |
| 27 NB2 OK | guarda `nb2_*.joblib + p_ens` | `persistence` parcial | `[NB2 OK] beta=1.0, p_ens (6196,)` |
| 28 puente | deja listo para 03 | — | siguiente: abrir 03 |

```python
# El corazón de NB02:
oof = oof_base_predictions(raw, dev_units)      # pipeline.py:157
beta = select_beta_grouped(y, p_lstm, p_lgb)    # stacking.py:234 → 1.0
ridge, lgb = fit_meta_learners(Z16, y16)       # stacking.py:161 solo-16
p = p_lstm + beta*(meta_predict(...) - p_lstm)  # stacking.py:184
s = causal_ema_by_unit(p, units, cycles, 5)     # smoothing.py:14
lo, hi = apply_conformal(s, fit_conformal(...)) # conformal.py:28/90
```

## Resumen para recordar

> Medir ablación, elegir beta fuera de fold, decidir por L_inf.

## Autoevaluación

1. ¿Qué mide la ablación y qué concluye?
2. ¿Por qué beta 1.0 es meta puro?
3. ¿Por qué la banda sobre-cubre y qué se hace?
