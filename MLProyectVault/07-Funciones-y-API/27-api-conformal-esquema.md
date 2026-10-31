---
title: Esquema — API Conformal
course: DS02-RUL
block: B7 — Funciones y API
node: N27
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - conformal
---

# Esquema — API Conformal

> Teoría completa: [[27-api-conformal]]

## La idea en una frase

> fit_conformal (OOF) → apply_conformal (pred) → empirical_coverage (medir, no suponer). Banda asimétrica, target 0.9.

## Las 4 piezas

| Función | Qué hace |
|---|---|
| _bin_index | asigna pred a bin [0,25,50,75,∞] |
| fit_conformal | cuantiles 5/95 por bin (OOF) |
| apply_conformal | aplica banda (lower/upper, clip 0) |
| empirical_coverage | fracción de reales en banda |

## Sí / No

- ✅ Se calibra con OOF (residuos honestos).
- ❌ No estrechar la banda sobre test (sobre-cobertura publicada).

## Flashcards #flashcards

- ¿Bins? :: [0, 25, 50, 75, ∞].
- ¿Target? :: 0.90 (alpha 0.05 por lado).
- ¿Cobertura en test? :: 100% (sobre-cobertura).

## Estado

- [ ] En curso
