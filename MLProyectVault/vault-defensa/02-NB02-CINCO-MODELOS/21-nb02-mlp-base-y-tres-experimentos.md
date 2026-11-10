---
title: NB02 · MLP base y tres experimentos
course: Reto 1 · SAA+PIA+MIA
block: 02 — NB02 cinco modelos
node: B2.2
indicador: SAA-7
descriptor: 10
spine: true
status: en-curso
tags:
  - nb02
  - mlp
  - rubrica/saa-7
---

# NB02 · MLP base y tres experimentos

> [!abstract] En una frase
> No son «tres pruebas»: son tres **hipótesis** con su predicción escrita antes de mirar el
> resultado. Por eso el experimento que falla también sirve.

## La tabla

| Exp. | Hipótesis (por qué) | RMSE val | Tiempo (s) |
|---|---|---|---|
| `base` | MLP medio, 2 capas: el RUL no es lineal por régimen | 7,358 | 27,5 |
| `E1_capacidad` | Más capacidad capta la interacción régimen-degradación… hasta sobreajustar | 7,481 | 70,7 |
| **`E2_reg_lr`** | Más regularización frena la memorización de 22 features ruidosas | **7,340** | 33,3 |
| `E3_batch` | Batch grande estabiliza el gradiente en ventanas correladas | 7,355 | 38,6 |

Fuente: `resultados/mlp_comparativa.csv` (columna `hipotesis`).

## Qué digo

«Tres experimentos, cada uno atacando una causa distinta: capacidad, regularización y tamaño de
batch. E1 confirma que más capacidad sobreajusta —empeora en validación aunque mejore en train—;
E2 confirma que el problema era varianza; E3 queda en tablas, sin mejora. Gana E2 con 7,34 de
validación, y su test, leído una sola vez, es 7,72.»

## Por qué se dice así

- El 7 son «3 experimentos»; el 10 exige explicar **por qué** cada uno. La columna `hipotesis`
  del CSV existe exactamente para eso.
- E1 empeorando es la prueba de que el experimento se diseñó antes de ver el número: si solo
  se enseña el ganador, parece que se probó hasta acertar.

## Evidencia

- Escritor: `src/clase/train_mlp.py:107` (`entrenar_mlp`), ordena por `rmse_val`.
- Artefacto del campeón: `models/mejor_modelo_clase_E2.joblib`.
- Test de E2 leído una vez: `7,7211` / MAE `5,8132` / R² `0,8343`.

## Pregunta probable

**«¿Por qué el MLP de clase no es el que despliegas?»**
→ «Porque compiten en dos ligas distintas. E2 es el mejor del track de fila con 22 features:
7,34 en validación. El sistema desplegado es el híbrido sobre ventanas: 4,34. El test se leyó
una vez en cada liga y no se comparan entre sí.»

## Lo que NO digo

- No presento 7,34 como test: es validación.
- No digo «E1 era una mala idea»: era una hipótesis razonable que los datos rechazaron.
- No confundo E2 (regresión con regularización) con E2 como «segundo experimento»: el nombre
  viene de `reg_lr`.

## Di esto en el tribunal

> «Base más tres experimentos con hipótesis escrita: capacidad, regularización y batch. Gana
> regularización, y eso dice que el problema era varianza.»

## Flashcards #flashcards

- ¿Qué ataca cada experimento? :: E1 capacidad, E2 regularización, E3 tamaño de batch.
- ¿Qué demuestra que E1 empeore? :: que el experimento se diseñó antes de ver el resultado; el problema era varianza.
- ¿Cuál es el test de E2 y cuántas veces se leyó? :: 7,7211, una sola vez.
