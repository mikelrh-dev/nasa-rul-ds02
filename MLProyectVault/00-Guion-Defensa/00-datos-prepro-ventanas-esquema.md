---
title: Esquema — Datos, prepro y ventanas
course: DS02-RUL
block: B0 — Guion defensa
node: N01
type: esquema
status: en-curso
tags:
  - esquema
  - datos
---

# Esquema — Datos, prepro y ventanas

> Nota de repaso rápido. Teoría completa: [[00-datos-prepro-ventanas]]

## La idea en una frase

> Reparto primero, Ridge solo-fit, ventana 50 con etiqueta final.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| Reparto | Fit/holdout/test por motor | Examen con temas no vistos |
| Ridge | Sensor menos vuelo | Quitar fiebre del termómetro |
| Ventana | 50 filas → RUL final | Foto + pie de foto |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    H5[HDF5] --> REP[Reparto]
    REP --> PREP[Ridge fit]
    PREP --> VENT[Ventanas 50]
```

## Sí / No (trampas frecuentes)

- ✅ El prepro se ajusta solo con fit-units.
- ❌ La ventana no son 50 ciclos reales (hay stride 100).

## Flashcards #flashcards

- ¿Dónde se ajusta el scaler? :: Solo con motores de ajuste.
- ¿Qué RUL hereda la ventana? :: El de su última fila.

## Estado

- [ ] En curso
