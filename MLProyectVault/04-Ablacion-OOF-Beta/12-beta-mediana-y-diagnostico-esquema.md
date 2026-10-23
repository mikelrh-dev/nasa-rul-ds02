---
title: Esquema — Beta y diagnóstico
course: DS02-RUL
block: B4 — Ablación, OOF y beta
node: N12
type: esquema
status: en-curso
tags:
  - esquema
  - beta
---

# Esquema — Beta y diagnóstico

> Nota de repaso rápido. Teoría completa: [[12-beta-mediana-y-diagnostico]]

## La idea en una frase

> Beta 1.00 por mediana honesta; el 0.716x queda como museo del error.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| Grid 0–1 | Cuánto caso al meta | El volumen del consejero |
| Mediana 1.00 | Robusta al fold 2 (0.00) | Voto mediano, no media |
| 0.716x | Firma del autoexamen | La foto del error pasado |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    G[Grid] --> M[Mediana]
    M --> B[Beta 1.00]
```

## Sí / No (trampas frecuentes)

- ✅ Cada fold lo puntúa un meta ajustado en otros motores.
- ❌ Elegir beta en las filas del ajuste (autoexamen).

## Flashcards #flashcards

- ¿Beta elegido y cómo? :: 1.00, mediana de [1.00, 1.00, 0.00].
- ¿Qué folds y betas? :: [2,10]→1.00, [5,18]→1.00, [16,20]→0.00.

## Estado

- [ ] En curso
