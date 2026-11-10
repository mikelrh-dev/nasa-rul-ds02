---
title: Esquema — OOF y beta
course: Reto 1 · SAA+PIA+MIA
block: 04 — NB04 BiLSTM
node: B4.3
type: esquema
status: en-curso
tags:
  - esquema
  - oof
---

# Esquema — OOF y beta

> Nota de repaso rápido. Teoría completa: [[42-nb04-oof-y-beta]]

## La idea en una frase
> El meta no puede entrenarse con predicciones que ya vieron su verdad: OOF puro y beta fuera de fold.

## Las piezas
| Pieza | Valor |
|---|---|
| Filas OOF | 14 915 ventanas (unidades 2, 5, 10, 18, 20) |
| Excluida | unidad 16 (holdout del meta) |
| Beta | 1,0 mediana · folds 1,00/1,00/0,00 · IQR 0,5 |

## Sí / No
- ✅ beta 1 es peso condicionado al fold.
- ❌ «beta 1 significa que el árbol sobra».

## Flashcards #flashcards
- ¿Qué son las 14 915 filas? :: ventanas puras de cinco unidades, sin la 16.
- ¿Qué beta sale? :: 1,0 de mediana con IQR 0,5.

## Estado
- [ ] En curso
