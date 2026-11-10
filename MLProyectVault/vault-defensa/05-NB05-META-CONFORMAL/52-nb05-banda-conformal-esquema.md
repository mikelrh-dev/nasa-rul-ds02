---
title: Esquema — Banda conformal
course: Reto 1 · SAA+PIA+MIA
block: 05 — NB05 meta y banda
node: B5.3
type: esquema
status: en-curso
tags:
  - esquema
  - conformal
---

# Esquema — Banda conformal

> Nota de repaso rápido. Teoría completa: [[52-nb05-banda-conformal]]

## La idea en una frase
> No es un intervalo de confianza: es una cota calibrada fuera de fold que gobierna la decisión.

## Las piezas
| Pieza | Valor |
|---|---|
| Calibración | 17 450 residuales OOF de 6 motores |
| Objetivo | 90 % |
| Cobertura test | 100 % |
| Ancho medio | 26,41 ciclos |
| Recalibrada en 16 | 3,35 de ancho · 31,4 % de cobertura (rechazada) |

## Sí / No
- ✅ «cubre de más a propósito».
- ❌ «intervalo de confianza al 90 %».
- ❌ decidir con el punto.

## Flashcards #flashcards
- ¿Con qué se calibra? :: 17 450 residuales fuera de fold.
- ¿Qué pasa al recalibrar en la 16? :: 3,35 de ancho y 31,4 % de cobertura: se rechazó.

## Estado
- [ ] En curso
