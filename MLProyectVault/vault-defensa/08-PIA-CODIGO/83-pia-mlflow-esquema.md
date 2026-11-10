---
title: Esquema — MLflow
course: Reto 1 · SAA+PIA+MIA
block: 08 — PIA código
node: C4
type: esquema
status: en-curso
tags:
  - esquema
  - mlflow
---

# Esquema — MLflow

> Nota de repaso rápido. Teoría completa: [[83-pia-mlflow]]

## La idea en una frase
> Trece runs con parámetros, métricas y capturas; la ablación del reloj es el único experimento que no está.

## Las piezas
| Pieza | Valor |
|---|---|
| Runs | 13 (9 fila + 4 ventana) |
| Export | `docs/evidencia/mlflow/comparativa.csv` |
| Comprobación | `backfill_mlflow.py --check` → 0 |
| Hueco | ablación `cyc_norm`: 0 runs |

## Sí / No
- ✅ «falta la ablación y lo declaro».
- ❌ «todos los experimentos están registrados».
- ❌ decir que el store está completo en git.

## Flashcards #flashcards
- ¿Cuántos runs y de qué tipos? :: 13: nueve de fila y cuatro de ventana.
- ¿Qué falta? :: la run de la ablación `cyc_norm`.

## Estado
- [ ] En curso
