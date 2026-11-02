---
title: Esquema — API Ensamble e intervalos
course: DS02-RUL
block: B7 — Funciones y API
node: N26
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - ensamble
---

# Esquema — API Ensamble e intervalos

> Teoría completa: [[26-api-ensamble-e-intervalos]]

## La idea en una frase

> HybridStackingEnsemble: prepro → meta → beta → EMA5 → clip. predict (punto) y predict_interval (punto+banda). Exige units.

## Las 6 piezas

| Método | Qué hace |
|---|---|
| __init__ | guarda bilstm, lgbm, scaler, meta, beta, conformal |
| _resolve_model | resuelve modelo según n_features |
| predict | punto: prepro → meta → mezcla → EMA5 → clip |
| predict_interval | punto + banda conformal |
| _sequence | reconstruye X_seq (50,19) |
| _tabular | reconstruye X_tab (93) |

## Sí / No

- ✅ predict_interval devuelve (point, lower, upper).
- ❌ Sin units, EMA mezcla motores (aviso).

## Flashcards #flashcards

- ¿predict vs predict_interval? :: Punto vs punto+banda.
- ¿Qué exige predict? :: units (para EMA por motor).
- ¿Qué hace _tabular? :: Reconstruye las 93 features tabulares.

## Estado

- [ ] En curso
