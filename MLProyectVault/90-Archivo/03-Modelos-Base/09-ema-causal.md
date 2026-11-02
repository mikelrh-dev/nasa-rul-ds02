---
title: EMA causal por motor
course: DS02-RUL
block: B3 — Modelos base
node: N9
status: en-curso
tags:
  - ema
  - suavizado
  - causal
---

# EMA causal por motor

## Idea central

Media móvil exponencial que suaviza las predicciones ventana a ventana sin mirar al futuro y sin mezclar motores.

> Suaviza el ruido diente de sierra mirando solo atrás y solo al mismo motor.

## ¿Qué problema resuelve?

El RUL real es monótono por ciclo, pero predecir ventana a ventana produce saltos. La EMA los aplana y suele mejorar décimas gratis (BiLSTM 5.637 → +EMA5 5.595).

## Las piezas del modelo mental

### Causal

`pd.Series.ewm(span=5, adjust=False)`: cada punto solo usa el presente y el pasado. Mirar al futuro sería fuga en producción.

### Por motor

Se agrupa por `unit` y se ordena por `cycle` antes de suavizar (`src/ds02_rul/smoothing.py:causal_ema_by_unit`). Sin `units`, todas las ventanas colapsarían en una sola serie: el código avisa con `UserWarning`.

### Span 5

Alpha = 2/(5+1): memoria de unas 5 ventanas. Suave sin aplanar la señal.

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    PRED[Dientes de sierra] --> GRP[Por motor y ciclo]
    GRP --> EMA[EMA5 causal]
    EMA --> SUAVE[Curva suave]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| Causal | Solo pasado | Centrada (miraría al futuro) |
| Por motor | Series separadas | Una serie global |

## Conexión con el aprendizaje

Es el "gratis" del proyecto: mejora sin entrenar nada, y por eso los extras de EMA viven en tabla aparte.

## Conexión con los notebooks del repositorio

- `02_decision_ablacion_oof_ensamble.ipynb`, celda 21 (extras EMA 3/5/10).
- `src/ds02_rul/smoothing.py:causal_ema_by_unit`, `ensemble.py` (`ema_span=5`).

## Resumen para recordar

> Suaviza atrás, nunca adelante, nunca mezclando motores.

## Autoevaluación

1. ¿Por qué `adjust=False` es la clave de la causalidad?
2. ¿Qué pasaría si se omite `units`?
3. ¿Por qué la EMA va en tabla `extra` y no en la titular?
