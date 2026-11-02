---
title: Esquema — API BiLSTM y pooling
course: DS02-RUL
block: B7 — Funciones y API
node: N23
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - bilstm
---

# Esquema — API BiLSTM y pooling

> Teoría completa: [[23-api-modelo-bilstm-y-pooling]]

## La idea en una frase

> Input(50,19) → BiLSTM×2 → concat[last,avg,max] → Dense(32) → Dense(1). RMSE 5.637 (single) / 6.218±0.541 (3 semillas).

## Las 3 piezas

| Pieza | Qué es |
|---|---|
| build_champion_bilstm | construye el modelo Keras (Huber, Adam 1e-3) |
| fit_bilstm | entrena con EarlyStopping (patience 5) en motor 16 |
| LastStepPooling | capa registrada portable (last step) |

## Sí / No

- ✅ LastStepPooling en vez de Lambda (portable entre versiones Python).
- ❌ No usar test para early stopping (solo holdout motor 16).

## Flashcards #flashcards

- ¿Triple pooling? :: last + avg + max.
- ¿Por qué Huber? :: robusto a atípicos.
- ¿Por qué no Lambda? :: marshal cambia entre versiones.

## Estado

- [ ] En curso
