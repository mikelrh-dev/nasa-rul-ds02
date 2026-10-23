---
title: Esquema — Prepro solo en fit
course: DS02-RUL
block: B2 — Prepro y features
node: N4
type: esquema
status: en-curso
tags:
  - esquema
  - prepro
---

# Esquema — Prepro solo en fit

> Nota de repaso rápido. Teoría completa: [[04-prepro-solo-fit-motores]]

## La idea en una frase

> Ajusta con fit, transforma con todos; el holdout no enseña nada.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| Scalers | Medias/varianzas de 18 canales | El cero de la báscula |
| Poly + ridges | Explicar sensor por régimen | Descontar el viento |
| 0 filas | Prueba impresa en el notebook | El precinto intacto |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    FIT[Fit] --> AJUSTA[Ajusta]
    AJUSTA --> TODO[Transforma todo]
```

## Sí / No (trampas frecuentes)

- ✅ Transformar el test con el scaler de fit es correcto.
- ❌ Ajustar el scaler con el test es inocuo (es fuga).

## Flashcards #flashcards

- ¿Con qué filas se ajusta el prepro? :: Solo fit-motores, 44.982 filas.
- ¿Qué imprime el notebook como prueba? :: Que el holdout aportó 0 filas.

## Estado

- [ ] En curso
