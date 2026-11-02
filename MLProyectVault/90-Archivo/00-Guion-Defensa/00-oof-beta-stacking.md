---
title: OOF, beta y stacking
course: DS02-RUL
block: B0 — Guion defensa
node: N03
status: en-curso
tags:
  - oof
  - beta
  - stacking
---

# OOF, beta y stacking

## Idea central

Combinar sin mirarse al espejo: cada ventana la puntúa un meta que no la vio.

> Si eliges beta con las mismas filas que ajustaron el meta, el RMSE miente (0.308 en la revisión rota).

## ¿Qué problema resuelve?

El meta-aprendiz puede memorizar. OOF agrupado por motor + beta fuera de fold lo impide.

## Las piezas del modelo mental

### OOF agrupado (`src/ds02_rul/pipeline.py:157`)

```python
def oof_base_predictions(raw, dev_units, n_splits=3, seed=42, ...):
    # cada fold reajusta scaler + poly + 14 ridges con sus train-units
    # folds: [[2,10],[5,18],[20,16]] — la ventana se puntúa con otro motor
```

- Qué entra: dev + 3 folds por motor.
- Qué sale: `p_lstm/p_lgb` OOF alineadas fila a fila.
- En notebook: NB02 celda 14 (269.9s, tiempos por fold).

### Meta solo-motor-16 (`src/ds02_rul/stacking.py:161`)

```python
def fit_meta_learners(Z, y, seed=42):
    ridge = RidgeCV(alphas=...).fit(Z, y)   # Z = [p_lstm, p_lgb]
    lgbm = LGBMRegressor(max_depth=3,...).fit(Z, y)
def meta_predict(ridge, lgbm, Z):
    return 0.5*ridge.predict(Z) + 0.5*lgbm.predict(Z)
```

- Qué entra: `Z` de 2535 ventanas del motor 16 (RUL 0-62).
- Qué sale: `ridge, lgbm` + `p_meta`.
- Por qué solo 16: probar el meta sobre OOF de los 5 fit-motores aprende un prior de nivel que no transfiere (39.9 vs 31.5, RMSE 4.04→10.17). Medido y rechazado.

### Beta honesta (`src/ds02_rul/stacking.py:234`)

```python
# p = p_lstm + beta*(p_meta - p_lstm), beta mediana de 3 folds
# fold0 1.0, fold1 1.0, fold2 0.0 → mediana 1.0
```

- Qué entra: `y, p_lstm, p_lgb, folds, grid beta`.
- Qué sale: `beta=1.0` + tabla por fold.
- En notebook: NB02 celdas 15 (beta_hat) y 18 (meta). Con beta=1 el híbrido ES el meta.

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    OOF[OOF por motor] --> META[Meta en 16]
    META --> BETA[Beta mediana]
    BETA --> ENS[Hibrido]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| OOF | Puntuar con otro motor | Validación aleatoria |
| beta=1 | Todo meta | Mezcla a medias |

## Conexión con los notebooks del repositorio

- NB02 celdas 14/15/16/18/19: OOF, beta_hat, protocolo legado (diagnóstico), meta, tabla titular 4.276 + NASA 2322.4.

## Resumen para recordar

> Otro motor puntúa, mediana decide, beta 1 es meta puro.

## Autoevaluación

1. ¿Por qué OOF por motor y no KFold?
2. ¿Por qué el meta solo ve el motor 16?
3. ¿Qué significa beta=1?
