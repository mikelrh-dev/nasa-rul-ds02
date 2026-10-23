---
title: Esquema — OOF agrupado
course: DS02-RUL
block: B4 — Ablación, OOF y beta
node: N11
type: esquema
status: en-curso
tags:
  - esquema
  - oof
---

# Esquema — OOF agrupado

> Nota de repaso rápido. Teoría completa: [[11-oof-agrupado]]

## La idea en una frase

> Cada fila, un tribunal virgen; cobertura exactamente uno.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| 3 folds | [2,10] [5,18] [20,16] | Tres tribunales |
| Refit total | Prepro + modelos por fold | Examinadores que no te conocen |
| Coverage 1 | Assert que lo garantiza | Sello anti-trampa |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    F[Folds] --> R[Refit]
    R --> P[Puntúa]
```

## Sí / No (trampas frecuentes)

- ✅ El OOF tarda ~270 s porque re-entrena 3 BiLSTM.
- ❌ Reutilizar el prepro global en los folds (fuga).

## Flashcards #flashcards

- ¿Qué folds puntúa cada uno? :: [2,10], [5,18], [20,16].
- ¿Qué garantiza el assert de cobertura? :: Cada ventana puntuada exactamente una vez.

## Estado

- [ ] En curso
