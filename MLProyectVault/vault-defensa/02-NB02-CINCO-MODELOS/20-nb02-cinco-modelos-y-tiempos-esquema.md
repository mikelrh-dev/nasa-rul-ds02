---
title: Esquema — Cinco modelos y tiempos
course: Reto 1 · SAA+PIA+MIA
block: 02 — NB02 cinco modelos
node: B2.1
type: esquema
status: en-curso
tags:
  - esquema
  - modelos
---

# Esquema — Cinco modelos y tiempos

> Nota de repaso rápido. Teoría completa: [[20-nb02-cinco-modelos-y-tiempos]]

## La idea en una frase
> Mismo pipeline, mismo split: lo único que cambia es el estimador, así la tabla mide el modelo.

## La tabla
| Modelo | RMSE val | Tiempo (s) |
|---|---|---|
| KNN | 9,409 | 9,1 |
| Regresión | 8,276 | 3,5 |
| Random Forest | 9,070 | 79,6 |
| SVM | 8,293 | 2,7 |
| **XGBoost** | **8,217** | **7,2** |

## Sí / No
- ✅ KNN y RF se caen de train a validación: es varianza.
- ✅ Sin SMOTE: es regresión.
- ❌ «probé muchos y me quedé con el mejor» sin criterio.

## Flashcards #flashcards
- ¿Cuál gana entre los cinco? :: XGBoost, 8,217 en validación.
- ¿Por qué no SMOTE? :: es regresión; el desbalance se trata con macro-RMSE.

## Estado
- [ ] En curso
