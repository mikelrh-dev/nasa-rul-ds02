---
title: Esquema — Bandas conformal
course: DS02-RUL
block: B5 — Ensamble y conformal
node: N14
type: esquema
status: en-curso
tags:
  - esquema
  - conformal
---

# Esquema — Bandas conformal

> Nota de repaso rápido. Teoría completa: [[14-bandas-conformal]]

## La idea en una frase

> Banda asimétrica de residuos honestos; cobertura medida, no supuesta.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| Bins | Tramos [0,25,50,75,∞) | Tallas de ropa |
| Cuantiles 5/95 | Margen por tramo | Elástico por talla |
| 100% test | Sobre-cobertura publicada | Paraguas demasiado grande |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    R[Residuos] --> B[Banda]
    B --> C[Cobertura]
```

## Sí / No (trampas frecuentes)

- ✅ La cobertura se publica por motor.
- ❌ Estrechar la banda hasta dar 90% justo en test (sería elegir sobre test).

## Flashcards #flashcards

- ¿Ancho medio de la banda enviada? :: 25.92 ciclos.
- ¿De dónde salen los residuos de calibración? :: Del OOF, filas que el meta no vio.

## Estado

- [ ] En curso
