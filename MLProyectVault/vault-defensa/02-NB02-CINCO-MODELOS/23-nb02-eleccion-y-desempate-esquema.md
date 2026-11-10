---
title: Esquema — Elección y desempate
course: Reto 1 · SAA+PIA+MIA
block: 02 — NB02 cinco modelos
node: B2.4
type: esquema
status: en-curso
tags:
  - esquema
  - eleccion
---

# Esquema — Elección y desempate

> Nota de repaso rápido. Teoría completa: [[23-nb02-eleccion-y-desempate]]

## La idea en una frase
> Se elige por validación con la métrica del negocio y se desempata al más simple; el test confirma.

## Las dos ligas
| Liga | Campeón | Test |
|---|---|---|
| Fila (22 features) | MLP E2 | 7,721 |
| Ventana (50×19) | Híbrido C | 4,338 |

## Sí / No
- ✅ «depende de la liga» con las dos cifras.
- ❌ decir «el mejor es 4,34» sin aclarar el grano.
- ❌ «elegí por test».

## Flashcards #flashcards
- ¿Qué conjunto decide? :: validación; el test se lee una vez.
- ¿Criterio de desempate? :: el modelo más simple.

## Estado
- [ ] En curso
