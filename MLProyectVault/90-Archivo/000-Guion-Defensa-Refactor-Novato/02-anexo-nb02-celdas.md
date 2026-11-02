---
title: Anexo NB02 celdas (B refactor)
course: DS02-RUL
block: B0 - Guion defensa B
node: A2
status: en-curso
tags:
  - anexo
  - nb02
---

# Anexo NB02 celdas B refactor (18 codigos)

> Version B (refactor novato-friendly): src/ds02_rul/viz.py + from ds02_rul.viz import * en 1 linea, glosario WINDOW/STEP/BETA/EMA5/L_inf/OOF/macro y Que entra/sale por celda. Logica identica al bundle A; cifras bundle B: ref RMSE 4.251, R2 0.9482, NASA 2305.1, macro 4.8433, LGBM 7.098, hashes ensemble 7acba335 / bilstm d0c5ed7f.

## Idea central

NB02 decide: ablacion cyc-norm, OOF agrupado hacia beta mediana, stacking + EMA + banda 90%.

## Celdas (Que entra hacia sale)

| Bloque | Hace | .py que llama | Imprime |
|---|---|---|---|
| Ablacion | con/sin cyc-norm | features.py | cyc-norm gana, se queda |
| OOF | 3 folds por motor | pipeline.py | OOF honesto por motor |
| Beta | mediana por fold | stacking.py | beta estable |
| Stack | BiLSTM+LGBM+meta+EMA | ensemble.py/smoothing.py | hibrido ref 4.251 |
| Banda | fit/apply_conformal 90% | conformal.py | (lower, upper), decidir L_inf |
| Tablas | evaluar_clase/mostrar_clase | viz.py + metrics.py | ref + macro 4.8433 |

## Literal para LM

Ver codigo-para-LM/nb02_decision_ablacion_oof_ensamble.codigo.md + src-stacking/ensemble/smoothing/conformal.codigo.md.

## Resumen

> OOF honesto hacia beta mediana hacia stacking + EMA + L_inf.

## Autoevaluacion

1. Por que OOF agrupado?
2. Que imprime la banda?
3. Ref y macro B?
