---
title: Esquema — API Ventanas e inferencia
course: DS02-RUL
block: B7 — Funciones y API
node: N22
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - ventanas
---

# Esquema — API Ventanas e inferencia

> Teoría completa: [[22-api-ventanas-e-inferencia]]

## La idea en una frase

> Una ventana = 50 filas consecutivas; su etiqueta es el RUL de la última fila.

## Las 5 piezas

| Función | Qué hace |
|---|---|
| build_windows | corta ventanas → X_seq (N,50,19) + X_tab (N,93) + y |
| per_unit_baseline | media sana de los 3 primeros ciclos por motor |
| raw_windows | ventanas crudas (step=1) para la vía en vivo |
| windows_for_unit | filtra raw_windows a un motor |
| validate_window | valida forma y ausencia de NaN/Inf |

## Sí / No

- ✅ window=50 son 50 filas muestreadas (stride 100), no 50 ciclos.
- ✅ step=3 train / step=2 test.
- ❌ raw_windows no hace prepro: eso lo hace el ensamble.

## Flashcards #flashcards

- ¿Etiqueta de una ventana? :: RUL de la última fila.
- ¿Qué valida validate_window? :: Forma (50, n_feat) y sin NaN/Inf.
- ¿Para qué sirve per_unit_baseline? :: Calibración causal (3 primeros ciclos).

## Estado

- [ ] En curso
