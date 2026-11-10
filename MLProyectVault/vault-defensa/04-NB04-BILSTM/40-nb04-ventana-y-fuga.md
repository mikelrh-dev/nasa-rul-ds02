---
title: NB04 · Ventana y fuga de información
course: Reto 1 · SAA+PIA+MIA
block: 04 — NB04 BiLSTM
node: B4.1
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - nb04
  - ventana
  - fuga
---

# NB04 · Ventana y fuga de información

> [!abstract] En una frase
> El RUL es una serie por motor: si una fila va a train y su vecina a validación, la validación
> miente. Todo el protocolo nace de esa frase.

## Qué digo

«La ventana son 50 filas consecutivas del mismo motor, con stride 100. En train avanzo de 3 en 3
y en test de 2 en 2, porque en test quiero más ventanas por motor. El split es por motor: cinco
unidades para ajuste, una de holdout para el meta y tres de test. Nunca parto por fila.»

## Los números del protocolo

| Dato | Valor |
|---|---|
| Ventana | 50 filas |
| Stride | 100 |
| Entrada de la red | `(None, 50, 19)` · 154 253 parámetros |
| Features tabulares | 93 |
| Ventanas dev / test | 17 450 / 6 196 |
| Filas dev / test | 52 635 / 12 538 |
| Unidades de ajuste | 2, 5, 10, 18, 20 |
| Holdout del meta | 16 |
| Test | 11, 14, 15 |

## Por qué se dice así

- Es la pregunta que hunde defensas: «¿cómo evitaste la fuga?». La respuesta no es «usé
  `train_test_split`», es «el split es por motor y el escalado se ajusta solo en ajuste».
- La unidad 16 no es test: es el holdout del meta-aprendiz. Mezclarlas invalidaría el 4,338.

## Evidencia

- Ventanas: `src/clase/ventanas_adaptadas.py` (`WINDOW`, `STEP`, construcción).
- Protocolo y constantes: `src/ds02_rul/pipeline.py`.
- Assert de formas en NB01 c31 y NB05 c32 (93 columnas, 6 196 ventanas de test).

## Pregunta probable

**«¿Por qué stride 100 y no 1?»**
→ «Porque ventanas consecutivas están casi duplicadas. Con stride 100 gano independencia
efectiva y reduzco cómputo; el precio es menos muestras, y por eso el motor 14 —que tiene
menos— es el que más sufre.»

## Lo que NO digo

- No digo que la ventana «captura la física»: captura contexto temporal de sensores.
- No digo «normalizo todo el dataset»: el scaler se ajusta en ajuste y se aplica.

## Di esto en el tribunal

> «El split es por motor porque las filas de un motor están correladas; partir por fila sería
> fuga, no validación.»

## Flashcards #flashcards

- ¿Cuál es el tamaño de ventana y el stride? :: 50 filas, stride 100.
- ¿Qué unidades son test y cuál es holdout? :: test 11/14/15; holdout del meta, la 16.
