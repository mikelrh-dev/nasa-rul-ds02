---
title: Anexo NB03 celdas
course: DS02-RUL
block: B0 — Guion defensa
node: A3
status: en-curso
tags:
  - anexo
  - nb03
---

# Anexo NB03 celdas (25 códigos)

## Idea central

NB03 prueba que no fue suerte: 3 semillas, comparativa, diagnóstico dónde falla, persistencia que recarga.

## Celdas

| Celda | Hace | .py que llama | Imprime |
|---|---|---|---|
| 1-3 puente | recarga NB01+NB02 | `np.load/joblib` | `[LOAD NB2 OK] BETA=1.0, p_ens (6196,)` |
| 5 compat | alias | `metrics.py` | `[FASE A OK]` |
| 8 multisemilla | `run_seed` 7 y 123 + 42 | `pipeline.py:run_seed` | tabla por semilla |
| 9 redondeo | `seed_summary` | `pipeline.py` | LightGBM 7.098±0.034, BiLSTM 6.347±0.748, Híbrido 4.278±0.051 |
| 11-14 vistas | 4 vistas amigables lectura | ya calculado | solo lectura |
| 18 comparativa | fila por modelo media±std | `metrics.py` | híbrido gana 4 métricas |
| 20-24 estabilidad | barras + por semilla + deltas | `metrics.py` | híbrido 0.136 entre semillas vs BiLSTM 1.134; -39.4% vs LGBM, -30.1% vs BiLSTM |
| 26 mejora base | `%` contra cada base | `metrics.py` | orden LGBM<BiLSTM<híbrido |
| 28 elección | regla empate | — | elegido `Híbrido+EMA5`, test no elige |
| 30 tabla redonda | titular final | `metrics.py` | la que se defiende |
| 33 real vs pred | nube por ventana | — | se pega <25, se abre a la derecha, máx 60.64 vs real 73 |
| 36 residuos | `pred-real`, sesgo, banda ±1std | `metrics.py` | sesgo +0.369, rango -14.76/+9.52, 58.8% se pasa (lado caro NASA) |
| 39 tramo | MAE por banda RUL | `metrics.py` | 1.204 / 4.091 / 5.264 (x4.4): preciso donde se decide |
| 42 por motor | `macro_rmse` | `metrics.py:macro_rmse` | 11:3.847, 14:7.833, 15:2.688; sesgos +3.09/-4.75/-2.00 se cancelan en +0.369 |
| 45 curva | `history` early stop motor 16 | `pipeline.py:fit_bilstm` | 8 épocas, val 8.664; más épocas ≠ mejor |
| 48 folds beta | `select_beta_grouped` detalle | `stacking.py` | 2 folds piden 1.0, 1 pide 0.0; mediana esconde discrepancia |
| 51 save | `save_ensemble` a `models/` | `persistence.py:save_ensemble` | escribe ensemble/scaler/keras/manifiesto + sha |
| 52 reload | `load_ensemble` proceso limpio | `persistence.py:load_ensemble` | `[RELOAD OK] 60.40 vs 58.00, recargado==memoria True` |
| 54-55 cierre | conclusiones 1-5 | — | sin fuga, beta honesta, stacking apila, cyc auditado, desplegable |

```python
# El cierre de NB03:
save_ensemble(ens, out_dir="models", manifest=build_manifest(...))  # persistence.py:108
reloaded = load_ensemble("models/ensemble.joblib")                  # persistence.py:189
assert max(abs(reloaded.predict(...) - ens.predict(...))) < 1e-6
```

## Resumen para recordar

> 3 semillas, gana estable, falla en el 14 del lado seguro, guarda y recarga igual.

## Autoevaluación

1. ¿Por qué media±std y no una semilla?
2. ¿Dónde falla y por qué ese orden es bueno?
3. ¿Qué prueba el RELOAD OK?
