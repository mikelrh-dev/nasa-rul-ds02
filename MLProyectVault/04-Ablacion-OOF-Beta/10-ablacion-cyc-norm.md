---
title: Ablación de cyc_norm (medir, no afirmar)
course: DS02-RUL
block: B4 — Ablación, OOF y beta
node: N10
status: en-curso
tags:
  - ablacion
  - ciclo
---

# Ablación de cyc_norm (medir, no afirmar)

## Idea central

Quitar el canal del reloj y re-entrenar mide cuánto dependía el modelo de él: +0.355 RMSE en el BiLSTM (5.625 → 5.980).

> Si quitas el reloj y apenas empeora, el modelo entiende degradación; si se hunde, leía el contador.

## ¿Qué problema resuelve?

Sustituye una afirmación ("el modelo usa el ciclo como atajo") por un número medido. Es el experimento que la versión anterior citaba sin haber corrido.

## Las piezas del modelo mental

### 4 variantes

`cyc_norm ON/OFF × baseline delta ON/OFF` (`src/ds02_rul/pipeline.py:ablation_table`): cada variante re-entrena LGBM y BiLSTM (caro) sobre test 11/14/15, semilla 42.

### Resultado BiLSTM

ON 5.625 → OFF 5.980: cuesta +0.355. Con delta de baseline el coste se repite. El reloj ayuda, pero el modelo no vive de él.

### Baseline delta

Restar la media sana de cada motor (`per_unit_baseline`, `BASE_CYCLES=3`): calibración causal registrada en producción. Variante honesta, no atajo.

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    ON[Con reloj 5.625] --> QUITA[Quita canal 19]
    QUITA --> OFF[Sin reloj 5.980]
    OFF --> DELTA[+0.355 medido]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| Ablación | Re-entrenar sin la pieza | Ponerla a cero en inferencia |
| Baseline delta | Calibración sana causal | Fuga (solo usa sus 3 primeros ciclos) |

## Conexión con el aprendizaje

Es el patrón "medir, no afirmar": cada afirmación del proyecto lleva su tabla.

## Conexión con los notebooks del repositorio

- `02_decision_ablacion_oof_ensamble.ipynb`, celdas 8–9 (tabla + veredicto +0.355).
- `src/ds02_rul/pipeline.py:ablation_table`, `features.py:per_unit_baseline`.

## Resumen para recordar

> +0.355 medido: el reloj ayuda, el modelo no vive de él.

## Autoevaluación

1. ¿Por qué hay que re-entrenar y no basta con poner el canal a cero?
2. ¿Qué es `BASE_CYCLES=3` y por qué es causal?
3. ¿Qué dirías si quitar el reloj mejorara el RMSE?
