---
title: Esquema — SHAP y aditividad
course: Reto 1 · SAA+PIA+MIA
block: 07 — NB07 SHAP
node: B7.1
type: esquema
status: en-curso
tags:
  - esquema
  - shap
---

# Esquema — SHAP y aditividad

> Nota de repaso rápido. Teoría completa: [[70-nb07-shap-aditividad]]

## La idea en una frase
> SHAP se comprueba: base + suma de aportes = predicción, con tolerancia 1e-5, sobre validación.

## Las piezas
| Pieza | Valor |
|---|---|
| Conjunto | validación, fold-0, 200 filas |
| Control | aditividad a 1e-5 |
| Top | `cycle` y `T50` |
| Contraste | permutación (cycle 20,76 · T50 6,16) |

## Sí / No
- ✅ «robusto al método, no causalidad».
- ❌ «SHAP demuestra que…».
- ❌ decir que se calculó en test.

## Flashcards #flashcards
- ¿Qué control valida SHAP? :: la aditividad a 1e-5.
- ¿Qué dos variables mandan? :: `cycle` y `T50`.

## Estado
- [ ] En curso
