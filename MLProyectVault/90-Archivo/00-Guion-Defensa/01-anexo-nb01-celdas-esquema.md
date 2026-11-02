---
title: Esquema — Anexo NB01
course: DS02-RUL
block: B0 — Guion defensa
node: A1
type: esquema
status: en-curso
tags:
  - esquema
  - nb01
---

# Esquema — Anexo NB01

> Nota de repaso rápido. Teoría completa: [[01-anexo-nb01-celdas]]

## La idea en una frase

> Suelo honesto + 2 bases 42 + puente.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| 9/11/13 | Datos→ventanas | Cimientos |
| 15/20 | LGBM + BiLSTM | Dos pilotos |
| 21 | Puente | Relevos |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    D[Datos] --> P[Prepro]
    P --> V[Ventanas]
    V --> B[Bases 42]
    B --> PU[Puente]
```

## Sí / No (trampas frecuentes)

- ✅ NB02 no re-entrena la 42.
- ❌ Ninguna celda funciona suelta.

## Flashcards #flashcards

- ¿Qué guarda NB01? :: artifacts npz + bilstm_seed42.keras.
- ¿Cuántas ventanas dev/test? :: 17450 / 6196.

## Estado

- [ ] En curso
