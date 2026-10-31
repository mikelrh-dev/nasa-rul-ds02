---
title: Anexo NB03 celdas (B refactor)
course: DS02-RUL
block: B0 - Guion defensa B
node: A3
status: en-curso
tags:
  - anexo
  - nb03
---

# Anexo NB03 celdas B refactor (multisemilla + reload)

> Version B (refactor novato-friendly): src/ds02_rul/viz.py + from ds02_rul.viz import * en 1 linea, glosario WINDOW/STEP/BETA/EMA5/L_inf/OOF/macro y Que entra/sale por celda. Logica identica al bundle A; cifras bundle B: ref RMSE 4.251, R2 0.9482, NASA 2305.1, macro 4.8433, LGBM 7.098, hashes ensemble 7acba335 / bilstm d0c5ed7f.

## Idea central

NB03 prueba que el hilo aguanta: semillas 42/7/123, persistencia y RELOAD OK.

## Celdas (Que entra hacia sale)

| Bloque | Hace | .py que llama | Imprime |
|---|---|---|---|
| Multi | run_seed 42/7/123 | pipeline.py | hibrido 4.340+-0.101 vs BiLSTM 6.218+-0.541 |
| Diagnostico | peor motor 14, cobertura | metrics.py/conformal.py | macro 4.8433, cobertura aprox 90% |
| Persistencia | save_ensemble | persistence.py | ensemble 7acba335, bilstm d0c5ed7f |
| Reload | proceso limpio | persistence.py | RELOAD OK recargado==memoria True |

## Literal para LM

Ver codigo-para-LM/nb03_evidencia_multisemilla_diagnostico.codigo.md + src-persistence/pooling/inference.codigo.md.

## Resumen

> 3 semillas + peor motor + guardar + recargar identico.

## Autoevaluacion

1. Media hibrido vs BiLSTM?
2. Que motor duele mas y cuanto?
3. Que demuestra RELOAD OK?
