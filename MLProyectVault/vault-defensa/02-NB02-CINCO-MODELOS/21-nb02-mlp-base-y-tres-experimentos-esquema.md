---
title: Esquema — MLP base y tres experimentos
course: Reto 1 · SAA+PIA+MIA
block: 02 — NB02 cinco modelos
node: B2.2
type: esquema
status: en-curso
tags:
  - esquema
  - mlp
---

# Esquema — MLP base y tres experimentos

> Nota de repaso rápido. Teoría completa: [[21-nb02-mlp-base-y-tres-experimentos]]

## La idea en una frase
> Cada experimento es una hipótesis escrita antes de ver el número; por eso E1 empeorando vale.

## Las cuatro piezas
| Exp. | Hipótesis | RMSE val |
|---|---|---|
| base | RUL no lineal por régimen | 7,358 |
| E1 | más capacidad… hasta sobreajustar | 7,481 |
| **E2** | regularización frena memorización | **7,340** |
| E3 | batch grande estabiliza gradiente | 7,355 |

## Sí / No
- ✅ 7,34 es validación; 7,7211 es test leído una vez.
- ❌ «E1 era una mala idea»: era una hipótesis razonable.

## Flashcards #flashcards
- ¿Qué ataca cada experimento? :: capacidad, regularización y batch.
- ¿Qué demuestra que E1 empeore? :: que el problema era varianza y la hipótesis se escribió antes.

## Estado
- [ ] En curso
