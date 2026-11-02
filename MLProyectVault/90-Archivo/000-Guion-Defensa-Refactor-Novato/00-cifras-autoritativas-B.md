---
title: Cifras autoritativas bundle B
course: DS02-RUL
block: B0 - Guion defensa B
node: N6
status: en-curso
tags:
  - cifras
  - bundle-B
---

# Cifras autoritativas bundle B

> Version B (refactor novato-friendly): src/ds02_rul/viz.py + from ds02_rul.viz import * en 1 linea, glosario WINDOW/STEP/BETA/EMA5/L_inf/OOF/macro y Que entra/sale por celda. Logica identica al bundle A; cifras bundle B: ref RMSE 4.251, R2 0.9482, NASA 2305.1, macro 4.8433, LGBM 7.098, hashes ensemble 7acba335 / bilstm d0c5ed7f.

## Idea central

Si el tribunal pide un numero, sale de aqui. Todo lo que cite 0acd795b es del bundle A viejo.

## Tabla ref (fila test, semilla 42)

| Modelo | RMSE | MAE | R2 | NASA |
|---|---|---|---|---|
| Hibrido B | 4.251 | 3.183 | 0.9482 | 2305.1 |
| (A viejo) | 4.289 | 3.179 | 0.9473 | 2310.6 |
| LightGBM | 7.098 | - | - | - |
| BiLSTM 42 | aprox 5.84 | aprox 4.49 | aprox 0.90 | - |

## Macro y multisemilla

- Macro B 4.8433 (A 4.9026). Motor 14: 7.997 (antes 8.175, el que mas duele).
- Media 3 semillas: hibrido 4.340+-0.101 vs BiLSTM 6.218+-0.541 hacia victoria (1.88 > 0.54), no empate.

## Hashes y estado

- ensemble 7acba335, bilstm d0c5ed7f, manifiesto nuevo, app/cache nueva.
- RELOAD OK recargado==memoria True. 4 tests de frontera en rojo por recongelar (U14-30, faltan 21 hacia 20, 2 de ui_alta), resto 207 en verde. Ver docs/plans/pendiente-adopcion-bundle-B.md.

## Resumen

> B = mismas o mejores metricas (+-0.1 no-determinismo TF), otros hashes, 4 umbrales por adaptar.

## Autoevaluacion

1. Ref y macro B de memoria?
2. Por que 4 tests caen al recongelar?
3. Que hash citas si te piden el bundle B?
