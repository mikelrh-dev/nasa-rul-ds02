---
title: Esquema — API Métricas
course: DS02-RUL
block: B7 — Funciones y API
node: N29
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - metricas
---

# Esquema — API Métricas

> Teoría completa: [[29-api-metricas]]

## La idea en una frase

> calculate_nasa_score (asimétrico) + macro_rmse (por motor) + evaluate_predictions (todo en un dict). Bundle B: ref RMSE 4.251, MAE 3.183, R2 0.9482, NASA 2305.1, macro 4.8433.

## Las 3 piezas

| Función | Qué hace |
|---|---|
| calculate_nasa_score | suma asimétrica (castiga tarde) |
| macro_rmse | media de RMSE por motor |
| evaluate_predictions | RMSE/MAE/R2/NASA/macro en un dict |

## Sí / No

- ✅ macro-RMSE ≠ RMSE global (macro no pondera por ventanas).
- ❌ NASA score no es una media.

## Flashcards #flashcards

- ¿Qué castiga NASA score? :: Predecir tarde.
- ¿Qué devuelve macro_rmse? :: dict con per_unit_rmse, macro_rmse, n_units.
- ¿evaluate_predictions? :: dict con todas las métricas.

## Estado

- [ ] En curso
