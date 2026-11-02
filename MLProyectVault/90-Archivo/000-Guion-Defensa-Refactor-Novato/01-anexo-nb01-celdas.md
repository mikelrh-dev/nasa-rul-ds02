---
title: Anexo NB01 celdas (B refactor)
course: DS02-RUL
block: B0 - Guion defensa B
node: A1
status: en-curso
tags:
  - anexo
  - nb01
---

# Anexo NB01 celdas B refactor (27 celdas)

> Version B (refactor novato-friendly): src/ds02_rul/viz.py + from ds02_rul.viz import * en 1 linea, glosario WINDOW/STEP/BETA/EMA5/L_inf/OOF/macro y Que entra/sale por celda. Logica identica al bundle A; cifras bundle B: ref RMSE 4.251, R2 0.9482, NASA 2305.1, macro 4.8433, LGBM 7.098, hashes ensemble 7acba335 / bilstm d0c5ed7f.

## Idea central

NB01 deja el suelo: datos, prepro, ventanas, 2 bases semilla 42, puente a 02. Mismas llamadas que A, celdas pequenas.

## Celdas (Que entra hacia sale)

| Celda | Hace | .py que llama | Imprime |
|---|---|---|---|
| 3 FIX ruta + imports | vuelve a raiz, calla TF, from ds02_rul.viz import * | viz.py | cwd + import OK |
| 5 compat clase | evaluar_clase/mostrar_clase alias sin entrenar | metrics.py | nada (0 outputs) |
| 7 hacia viz.py | 12 def fuera del notebook | viz.py (solo matplotlib/pandas) | nada nuevo |
| 9 datos | load_ds02 stride 100 + reparto | data.py | dev 52635 (6 motores), test 12538 (11/14/15) |
| 11 prepro | fit_preprocessing solo-fit | features.py | scaler 18 canales, 14 ridges |
| 13 ventanas | build_windows 50, step 3/2 | features.py | dev (17450,50,19), test (6196,50,19) |
| 15 LGBM | make_lgbm(42).fit | pipeline.py | RMSE 7.098 determinista |
| 17 baseline | media train 38.08 | metrics.py | LGBM vs baseline |
| 20 BiLSTM | fit_bilstm early-stop motor 16 | model.py | aprox 65s, RMSE aprox 5.84 |
| 21 NB1 OK | guarda artifacts/ | persistence parcial | [NB1 OK] |

## Literal para LM

Ver codigo-para-LM/nb01_datos_y_bases.codigo.md + src-viz/data/features/pipeline/model/metrics.codigo.md.

## Resumen

> NB01 = suelo honesto + 2 bases 42 + puente, con viz fuera.

## Autoevaluacion

1. Que guarda NB01 para NB02?
2. Que valida el motor 16?
3. Que linea sustituye la celda gigante?
