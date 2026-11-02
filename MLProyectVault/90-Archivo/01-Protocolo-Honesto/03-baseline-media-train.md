---
title: Baseline de media train
course: DS02-RUL
block: B1 — Protocolo honesto
node: N3
status: en-curso
tags:
  - baseline
  - referencia
---

# Baseline de media train

## Idea central

El modelo más tonto —predecir siempre la media del RUL de train— pone el suelo que todo modelo útil debe superar.

> Baseline media train = 38.08 ciclos, RMSE 20.022: cualquier cosa peor que esto no es un modelo.

## ¿Qué problema resuelve?

Sin referencia, un RMSE 7.113 no dice nada: ¿es bueno o malo? Contra el baseline 20.022, el LightGBM ya gana por goleada, y eso calibra toda la tabla titular.

## Las piezas del modelo mental

### Media solo de fit

`float(np.asarray(dev["y"])[fit_idx].mean())` — la media se calcula SOLO con motores de ajuste. Usar la media global sería fuga.

### `evaluar_clase` no entrena

Es un alias de `evaluate_predictions` (`src/ds02_rul/metrics.py:evaluate_predictions`): devuelve RMSE/MAE/R²/NASA de unas predicciones ya hechas. Igual que el `evaluar()` de clase, pero post-hoc.

### Lectura

RMSE 20.022, R² −0.148 (negativo: peor que predecir la media, por definición). Todo lo que venga después debe quedar muy por debajo.

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    MEDIA[Media fit 38.08] --> PRED[Predice 38.08 a todo test]
    PRED --> EV[evaluar_clase]
    EV --> SUELO[RMSE 20.022 = suelo]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| Baseline | Referencia tonta que calibra | Modelo candidato |
| R² negativo | Peor que la media (esperado aquí) | Error de cálculo |

## Conexión con el aprendizaje

Es el "grado cero" de la comparativa: el primer peldaño de la escalera de modelos.

## Conexión con los notebooks del repositorio

- `01_datos_y_bases.ipynb`, celda 17 (Fase A: baseline + importancias LGBM).
- `02_decision_ablacion_oof_ensamble.ipynb`, celda 21 (baseline en tabla titular).
- `src/ds02_rul/metrics.py:evaluate_predictions`.

## Resumen para recordar

> 38.08 siempre: si no ganas al tonto, no hay modelo.

## Autoevaluación

1. ¿Por qué la media se calcula solo con fit_idx?
2. ¿Por qué el R² del baseline es negativo?
3. ¿Qué diferencia hay entre `evaluar_clase` y el `evaluar()` de clase?
