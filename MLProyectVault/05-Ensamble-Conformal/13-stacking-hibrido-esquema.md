---
title: Esquema — Stacking híbrido
course: DS02-RUL
block: B5 — Ensamble y conformal
node: N13
type: esquema
status: en-curso
tags:
  - esquema
  - stacking
---

# Esquema — Stacking híbrido

> Nota de repaso rápido. Teoría completa: [[13-stacking-hibrido]]

## La idea en una frase

> Meta 50/50, beta 1.00, EMA5, clip: 4.275.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| Ridge + LGBM | Árbitro 50/50 | Dos jueces que promedian |
| Beta 1.00 | Todo el meta | Volumen al máximo |
| EMA5 + clip | Pulso firme, sin negativos | Pulso y suelo |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    B[Base x2] --> M[Meta]
    M --> H[Híbrido 4.275]
```

## Sí / No (trampas frecuentes)

- ✅ El meta se ajusta en holdout, nunca en test.
- ❌ Beta se entrena con gradiente (se elige por grid OOF).

## Flashcards #flashcards

- ¿Fórmula del híbrido? :: p = lstm + beta·(meta − lstm), EMA5, clip ≥ 0.
- ¿RMSE del híbrido semilla 42? :: 4.275.

## Estado

- [ ] En curso
