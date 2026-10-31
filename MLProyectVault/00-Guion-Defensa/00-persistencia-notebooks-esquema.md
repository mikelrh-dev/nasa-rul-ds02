---
title: Esquema — Persistencia y notebooks
course: DS02-RUL
block: B0 — Guion defensa
node: N05
type: esquema
status: en-curso
tags:
  - esquema
  - persistencia
---

# Esquema — Persistencia y notebooks

> Nota de repaso rápido. Teoría completa: [[00-persistencia-notebooks]]

## La idea en una frase

> Keras aparte, joblib sin grafo, recarga que lo prueba.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| .keras | Grafo nativo | Motor aparte |
| joblib | Resto + ruta | Maleta sin motor |
| artifacts/ | Puente NB01-03 | Relevos |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    NB1[NB01] --> NB2[NB02]
    NB2 --> NB3[NB03]
    NB3 --> SAVE[models/]
```

## Sí / No (trampas frecuentes)

- ✅ `load_ensemble('models/ensemble.joblib')` en proceso limpio.
- ❌ No re-ejecutar NB03 antes de defensa.

## Flashcards #flashcards

- ¿Dónde va el grafo? :: En .keras nativo.
- ¿Qué prueba la recarga? :: predicho == en memoria.

## Estado

- [ ] En curso
