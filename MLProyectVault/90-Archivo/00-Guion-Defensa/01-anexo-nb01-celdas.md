---
title: Anexo NB01 celdas
course: DS02-RUL
block: B0 — Guion defensa
node: A1
status: en-curso
tags:
  - anexo
  - nb01
---

# Anexo NB01 celdas (12 códigos)

## Idea central

NB01 deja el suelo: datos, prepro, ventanas, 2 bases semilla 42, puente a 02.

## Celdas

| Celda | Hace | .py que llama | Imprime |
|---|---|---|---|
| 3 FIX ruta + imports | vuelve a raíz, calla TF, carga `ds02_rul` | `pathlib/os` | `cwd: .../nasa` |
| 5 compat clase | alias sin entrenar | `evaluate_predictions/tabla_modelos` | nada (0 outputs) |
| 7 utils presentación | 12 `def` gráficos/tablas | solo `matplotlib/pandas` | nada nuevo |
| 9 datos | `load_ds02 stride 100` + reparto | `data.py:load_ds02` | dev 52635 filas (6 motores), test 12538 (11/14/15), ajuste 44982 |
| 11 prepro | `fit_preprocessing` solo-fit | `features.py:fit_preprocessing` | scaler 18 canales, media `[:4]=[21930,0.6249,68.6,475]`, base 4→14, 14 ridges |
| 13 ventanas | `build_windows 50, step 3/2` | `features.py:build_windows` | dev `(17450,50,19)/(17450,93)`, test `(6196,50,19)`, 1.1s, 66.3MB |
| 15 LGBM | `make_lgbm(42).fit` tabular fit | `pipeline.py:make_lgbm` | 0.27s, 93 feats, `RMSE 7.113, MAE 5.585, R2 0.8551, NASA 5794.9` |
| 17 baseline | media train 38.08 | `metrics.py` | tabla LGBM 7.113 vs baseline 20.022, top feats |
| 20 BiLSTM | `fit_bilstm` early stop motor 16 | `model.py:build_champion_bilstm` | 65.1s, 9 épocas, val 8.317, `RMSE 5.839, MAE 4.491, R2 0.9023` |
| 21 NB1 OK | guarda `artifacts/` | `persistence` parcial | `[NB1 OK] artefactos en .../artifacts` |
| 22-23 EDA extra | correlación + distribución | `raw/dev` ya calculados | 2 figuras solo lectura |

```python
# El contrato de NB01 en 3 líneas:
prep = fit_preprocessing(W_tr[fit], Xs_tr[fit])   # features.py:25 solo-fit
dev = build_windows(..., window_size=50, step=3)   # features.py:79 etiqueta final
out = run_seed(raw, 42, fit, [16], test)           # pipeline.py:88 entrena 42
```

## Resumen para recordar

> NB01 = suelo honesto + 2 bases 42 + puente.

## Autoevaluación

1. ¿Qué guarda NB01 para NB02?
2. ¿Qué valida el motor 16?
3. ¿Por qué step 3 en train y 2 en test?
