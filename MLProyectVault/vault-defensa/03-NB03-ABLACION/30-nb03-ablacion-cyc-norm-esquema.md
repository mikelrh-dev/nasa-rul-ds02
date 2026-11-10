---
title: Esquema — Ablación de cyc_norm
course: Reto 1 · SAA+PIA+MIA
block: 03 — NB03 ablación
node: B3.1
type: esquema
status: en-curso
tags:
  - esquema
  - ablacion
---

# Esquema — Ablación de cyc_norm

> Nota de repaso rápido. Teoría completa: [[30-nb03-ablacion-cyc-norm]]

## La idea en una frase
> El reloj ayuda a la secuencia y estorba al resumen: la misma feature mejora una rama y empeora la otra.

## Las dos ramas
| Variante | BiLSTM | LightGBM |
|---|---|---|
| Con reloj | **5,796** | 7,067 |
| Sin reloj | 6,563 | **6,297** |

## Sí / No
- ✅ «quitarlo sube el BiLSTM casi un ciclo y baja el árbol siete décimas».
- ❌ citarla como run de MLflow (no lo es).
- ❌ mezclar la tabla del notebook con la del README.

## Flashcards #flashcards
- ¿Qué le pasa al BiLSTM sin reloj? :: empeora de 5,796 a 6,563.
- ¿Y al árbol? :: mejora de 7,067 a 6,297.

## Estado
- [ ] En curso
