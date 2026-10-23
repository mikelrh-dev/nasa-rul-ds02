---
title: Bandas conformal por tramo de RUL
course: DS02-RUL
block: B5 — Ensamble y conformal
node: N14
status: en-curso
tags:
  - conformal
  - incertidumbre
  - bandas
---

# Bandas conformal por tramo de RUL

## Idea central

Una predicción puntual no basta para decidir mantenimiento: la banda split-conformal da un intervalo asimétrico por tramo de RUL, calibrado con residuos que el meta nunca vio.

> El punto dice "cuándo"; la banda dice "con qué margen me puedo equivocar".

## ¿Qué problema resuelve?

Mantenimiento decide con rangos. La banda 90% promete cubrir el RUL real el 90% de las veces, y su ancho crece donde el error crece (tramo alto: [−24.41, −16.99]).

## Las piezas del modelo mental

### Split-conformal

Residuos `y − pred` del OOF (filas que no ajustaron el meta) agrupados por RUL predicho en bins [0,25,50,75,∞); cuantiles 5%/95% por bin (`src/ds02_rul/conformal.py:fit_conformal`). Asimétrica a propósito: la penalización NASA también lo es.

### `apply_conformal` y garantías

`lower/upper` nunca cruzan el punto; cota inferior recortada a 0 solo si el punto es ≥ 0. Bins con <100 filas usan cuantiles globales.

### Tres bandas publicadas

Enviada (OOF 6 motores, ancho 25.92), motor 16 (diagnóstico: solo cubre 31.9% → el meta no transfiere nivel), sin sesgo (diagnóstico de dispersión). Cobertura en test: 100% global — sobre-cubre porque los folds son más débiles que el desplegado; se publica el trade-off en vez de estrecharla eligiendo sobre test.

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    OOF[Residuos OOF] --> BINS[Bins por RUL]
    BINS --> Q[Cuantiles 5/95]
    Q --> BANDA[Punto ± margen]
    BANDA --> COB[Cobertura: se mide, no se supone]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| 90% nominal | Objetivo de diseño | Garantía en 3 motores |
| 100% cobertura | Sobre-cobertura honesta publicada | Mejor banda (es ancha) |

## Conexión con el aprendizaje

Es la diferencia entre predecir y decidir: el punto es ciencia, la banda es ingeniería.

## Conexión con los notebooks del repositorio

- `02_decision_ablacion_oof_ensamble.ipynb`, celdas 25–26 (calibración + cobertura por motor).
- `src/ds02_rul/conformal.py:fit_conformal/apply_conformal/empirical_coverage`.

## Resumen para recordar

> Banda asimétrica de residuos honestos; cobertura medida por motor, no supuesta.

## Autoevaluación

1. ¿Por qué la banda es asimétrica?
2. ¿Por qué se calibra con el OOF y no con el test?
3. ¿Qué revela que la banda de motor 16 solo cubra 31.9%?
