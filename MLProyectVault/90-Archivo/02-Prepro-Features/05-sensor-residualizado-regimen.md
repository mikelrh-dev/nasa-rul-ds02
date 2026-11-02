---
title: Sensor residualizado contra el régimen
course: DS02-RUL
block: B2 — Prepro y features
node: N5
status: en-curso
tags:
  - residualizado
  - regimen
  - ridge
---

# Sensor residualizado contra el régimen

## Idea central

Cada sensor mide degradación (correlaciona con RUL) más régimen de vuelo (no correlaciona): restamos lo segundo para quedarnos con lo primero.

> Sensor = degradación + punto de operación; el ridge quita el punto de operación.

## ¿Qué problema resuelve?

Un árbol partiría por maniobras del piloto (altitud, Mach) en vez de por desgaste. Al residualizar, el LightGBM solo ve señal útil y no aprende atajos de régimen.

## Las piezas del modelo mental

### Régimen W

4 canales: alt, Mach, TRA, T2. No predicen RUL, pero mueven todos los sensores.

### Ridge por sensor

14 regresiones `Ridge(alpha=1.0)` de cada sensor contra la base polinómica del régimen (`src/ds02_rul/features.py:fit_preprocessing`, `src/ds02_rul/residualizer.py:SensorResidualizer`).

### Residuo estandarizado

`Xs - ridge(P)` pasado por `res_scaler`: lo que el régimen no explica, en unidades comparables.

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    XS[Sensor crudo] --> MENOS[Menos ridge de W]
    MENOS --> RES[Residuo = degradación]
    RES --> STD[Estandariza]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| Residuo | Lo que el régimen no explica | Ruido sin información |
| Régimen | Condición de vuelo | Desgaste |

## Conexión con el aprendizaje

Es el "descontar el viento" del proyecto: separa lo que importa (desgaste) de lo que distrae (maniobra).

## Conexión con los notebooks del repositorio

- `01_datos_y_bases.ipynb`, celda 11 (`ridges de residuos: 14`, `base polinómica 4 → 14`).
- `src/ds02_rul/residualizer.py:SensorResidualizer.transform`.

## Resumen para recordar

> Quita el régimen, quédate el desgaste.

## Autoevaluación

1. ¿Por qué un árbol sin residualizar partiría por maniobras?
2. ¿Qué pinta la base polinómica de grado 2?
3. ¿Dónde se aplica el residualizado en inferencia? (`ensemble.py:_tabular` deshace el escalado global antes de residualizar.)
