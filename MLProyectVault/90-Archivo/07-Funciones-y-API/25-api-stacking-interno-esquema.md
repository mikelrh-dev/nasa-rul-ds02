---
title: Esquema — API Stacking interno
course: DS02-RUL
block: B7 — Funciones y API
node: N25
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - stacking
---

# Esquema — API Stacking interno

> Teoría completa: [[25-api-stacking-interno]]

## La idea en una frase

> Meta 50/50 (Ridge+lgbm), beta=1.00 por holdout agrupado, EMA5, clip. Fórmula: p = lstm + beta·(meta − lstm).

## Las 10 piezas

| Función | Qué hace |
|---|---|
| MetaSpec | config del meta (dataclass) |
| meta_design | construye Z (p_lstm, p_lgb, +ciclo) |
| fit_meta | ajusta RidgeCV + LGBM |
| predict_meta | predicción del meta (media 50/50) |
| grouped_folds | folds por motor (seed) |
| fit_meta_learners | ajusta ridge + lgbm |
| meta_predict | media de las dos predicciones |
| score_beta_holdout | RMSE por beta en holdout |
| select_beta_grouped | elige beta por motor |
| in_sample_beta_diagnostic | diagnóstico in-sample (trap) |

## Sí / No

- ✅ Beta por holdout agrupado (por motor).
- ❌ Beta=0 sería BiLSTM puro.

## Flashcards #flashcards

- ¿Fórmula del híbrido? :: p = lstm + beta·(meta − lstm).
- ¿Beta elegido? :: 1.00.
- ¿Cuántos folds piden 1.00? :: Dos (uno pide 0.00).

## Estado

- [ ] En curso
