---
title: NB04 · BiLSTM y pooling
course: Reto 1 · SAA+PIA+MIA
block: 04 — NB04 BiLSTM
node: B4.2
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - nb04
  - bilstm
  - pooling
---

# NB04 · BiLSTM y pooling

> [!abstract] En una frase
> El BiLSTM no «entiende» el motor: recorre la ventana en los dos sentidos y resume 50 pasos en
> un vector. El pooling es lo que decide **qué parte del vuelo** pesa.

## Qué digo

«La red lee la ventana en los dos sentidos —pasado y futuro dentro de la ventana, no del
motor— y con triple pooling resume la secuencia: último estado, media y máximo. Cada uno captura
algo distinto: el estado final, el nivel medio y el peor instante. Sale una predicción por
ventana, 5,65 de RMSE en test por sí sola.»

## Por qué se dice así

- Distingue «bidireccional dentro de la ventana» de «mirar el futuro del motor»: lo segundo sería
  fuga, lo primero es una ventana completa ya observada.
- El triple pooling explica por qué la rama secuencial aporta algo que el resumen tabular no:
  el máximo captura el pico de degradación.

## Evidencia

- Arquitectura: `src/ds02_rul/` (construcción del modelo), `models/bilstm_ds02.keras`.
- Cascada de la rama: 5,654 sola; 5,618 con EMA5 ([[60-nb06-cascada-bundle-c]]).
- Parámetros: 154 253, entrada `(None, 50, 19)`.

## Pregunta probable

**«¿Por qué bidireccional y no unidireccional?»**
→ «Porque la ventana ya está completa cuando predigo: no hay futuro del motor que espiar, solo
pasado inmediato en los dos sentidos de la secuencia. Si predijera en streaming, tendría que ser
unidireccional.»

## Lo que NO digo

- No digo «el BiLSTM aprende la física del motor».
- No digo «bidireccional ve el futuro»: ve el resto de la ventana, que ya ocurrió.

## Di esto en el tribunal

> «El BiLSTM resume 50 pasos con triple pooling: estado final, media y máximo; cada uno aporta
> una parte distinta de la degradación.»

## Flashcards #flashcards

- ¿Qué tres cosas resume el pooling? :: último estado, media y máximo de la secuencia.
- ¿Por qué es lícito que sea bidireccional? :: porque la ventana ya está completa; no se espía el futuro del motor.
