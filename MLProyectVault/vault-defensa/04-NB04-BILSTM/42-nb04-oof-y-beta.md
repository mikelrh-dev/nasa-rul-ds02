---
title: NB04 · OOF y beta
course: Reto 1 · SAA+PIA+MIA
block: 04 — NB04 BiLSTM
node: B4.3
indicador: SAA-9
descriptor: 10
spine: true
status: en-curso
tags:
  - nb04
  - oof
  - beta
---

# NB04 · OOF y beta

> [!abstract] En una frase
> El meta-aprendiz no puede entrenarse con predicciones que ya vieron su propia verdad: por eso
> las predicciones son **out-of-fold** y la beta se elige fuera de fold.

## Qué digo

«Para entrenar el meta necesito predicciones de las dos ramas sobre datos que no hayan visto.
Eso es OOF: 14 915 ventanas puras de cinco unidades, sin la 16. Sobre eso elijo beta —cuánto
pesa cada rama— con una rejilla agrupada por motor, y sale 1,0 con folds 1,00 / 1,00 / 0,00:
media 1,0, IQR 0,5. Que la mediana sea 1 no significa que el BiLSTM sobre: significa que en dos
de los tres folds el error lo domina él.»

## Por qué se dice así

- Es la objeción «meta entrenado con predicciones in-sample»: la respuesta es OOF + holdout. Sin
  esta nota, el 4,338 es indefendible.
- La beta es la palanca que el ADR-001 discute; decir el IQR evita vender un único número.

## Evidencia

- OOF: `src/ds02_rul/pipeline.py` (`oof_base_predictions`).
- Beta: `stacking.select_beta_grouped` — `beta = 1.0`, folds `[1.00, 1.00, 0.00]`, mediana 1.0,
  IQR 0.5.
- Filas OOF puras: 14 915 (unidades 2, 5, 10, 18, 20; sin 16).

## Pregunta probable

**«Si beta es 1, ¿el LightGBM no aporta nada?»**
→ «Beta 1 en la mediana dice que el meta carga el peso en el BiLSTM cuando compiten; pero el
LightGBM sigue aportando en los folds donde la secuencia falla, y la cascada lo demuestra: sin
él, el híbrido no baja a 4,34. La beta no es un juicio sobre el modelo, es un peso condicionado
al fold.»

## Lo que NO digo

- No digo «beta 1 significa que el árbol sobra».
- No digo que el OOF incluya la unidad 16: está excluida a propósito.

## Di esto en el tribunal

> «El meta se entrena con predicciones out-of-fold de cinco unidades puras y se valida en la 16;
> la beta se elige fuera de fold, no sobre test.»

## Flashcards #flashcards

- ¿Qué son las 14 915 filas OOF? :: ventanas de cinco unidades puras, excluida la 16, con predicciones fuera de fold.
- ¿Qué beta sale y con qué dispersión? :: 1,0 de mediana, folds 1,00/1,00/0,00, IQR 0,5.
