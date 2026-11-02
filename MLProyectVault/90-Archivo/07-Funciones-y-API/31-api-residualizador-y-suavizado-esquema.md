---
title: Esquema — API Residualizador y suavizado
course: DS02-RUL
block: B7 — Funciones y API
node: N31
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - residualizador
  - ema
---

# Esquema — API Residualizador y suavizado

> Teoría completa: [[31-api-residualizador-y-suavizado]]

## La idea en una frase

> SensorResidualizer: ridge(P) → residuo → estandarizar. causal_ema_by_unit: EMA por motor, solo pasado, span=5.

## Las 2 piezas

| Pieza | Qué hace |
|---|---|
| SensorResidualizer (__init__/transform) | quita régimen (ridge) y estandariza |
| causal_ema_by_unit | EMA causal por motor (span=5) |

## Sí / No

- ✅ EMA causal (solo pasado, sin fuga).
- ❌ Sin units, EMA mezcla motores.

## Flashcards #flashcards

- ¿Qué quita el residualizador? :: El régimen de vuelo (W).
- ¿Por qué EMA causal? :: Evita fuga (no mira el futuro).
- ¿Qué es BASE_CYCLES? :: 3 primeros ciclos por motor.

## Estado

- [ ] En curso
