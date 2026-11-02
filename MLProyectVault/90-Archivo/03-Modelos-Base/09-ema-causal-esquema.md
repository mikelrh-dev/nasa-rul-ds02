---
title: Esquema — EMA causal
course: DS02-RUL
block: B3 — Modelos base
node: N9
type: esquema
status: en-curso
tags:
  - esquema
  - ema
---

# Esquema — EMA causal

> Nota de repaso rápido. Teoría completa: [[09-ema-causal]]

## La idea en una frase

> Suaviza atrás, nunca adelante, nunca mezclando motores.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| Causal | Solo pasado (`adjust=False`) | Conducir mirando atrás por el retrovisor, nunca adivinando |
| Por motor | Una serie por unidad | Un cuaderno por paciente |
| Span 5 | Memoria de ~5 ventanas | Pulso firme, no temblor |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    R[Ruidosa] --> E[EMA5]
    E --> S[Suave]
```

## Sí / No (trampas frecuentes)

- ✅ La EMA mejora décimas sin entrenar.
- ❌ Suavizar con toda la serie junta (mezcla motores).

## Flashcards #flashcards

- ¿Qué hace causal_ema_by_unit? :: EMA por motor ordenada por ciclo.
- ¿BiLSTM con y sin EMA5? :: 5.637 → 5.595.

## Estado

- [ ] En curso
