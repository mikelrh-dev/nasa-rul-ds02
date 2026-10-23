---
title: Esquema — Ablación cyc_norm
course: DS02-RUL
block: B4 — Ablación, OOF y beta
node: N10
type: esquema
status: en-curso
tags:
  - esquema
  - ablacion
---

# Esquema — Ablación cyc_norm

> Nota de repaso rápido. Teoría completa: [[10-ablacion-cyc-norm]]

## La idea en una frase

> +0.355 medido: el reloj ayuda, el modelo no vive de él.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| ON 5.625 | Con reloj | Correr con cronómetro |
| OFF 5.980 | Sin reloj | Correr a sensaciones |
| +0.355 | Precio del atajo | Lo que cuesta no mirar el reloj |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    C[Con] --> S[Sin]
    S --> P[Precio]
```

## Sí / No (trampas frecuentes)

- ✅ Cada variante re-entrena desde cero.
- ❌ Apagar el canal en inferencia equivale a ablacionar.

## Flashcards #flashcards

- ¿Coste medido de quitar cyc_norm en BiLSTM? :: +0.355 RMSE.
- ¿Qué 4 variantes prueba ablation_table? :: cyc ON/OFF × baseline delta ON/OFF.

## Estado

- [ ] En curso
