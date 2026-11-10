---
title: NB02 · Elección y desempate
course: Reto 1 · SAA+PIA+MIA
block: 02 — NB02 cinco modelos
node: B2.4
indicador: SAA-9
descriptor: 10
spine: true
status: en-curso
tags:
  - nb02
  - eleccion
  - rubrica/saa-9
---

# NB02 · Elección y desempate

> [!abstract] En una frase
> La elección no es «el que mejor número da»: es **la métrica que importa al negocio**, leída en
> validación, con desempate al modelo más simple. El test solo confirma.

## Qué digo

«Elijo por RMSE de validación, porque el coste del error es cuadrático y lo caro es el fallo
grande. Si hay empate, gana el más simple: menos piezas, menos formas de romperse. Con ese
criterio, en el track de fila gana E2 (7,34) sobre XGB (8,22); en el track de ventana gana el
híbrido C (4,34). Son dos ligas y las dos se eligen igual: validación, nunca test.»

## La tabla de decisión

| Liga | Modelo elegido | RMSE val | Test | Por qué ese |
|---|---|---|---|---|
| Fila (22 features) | MLP E2 (regularizado) | 7,340 | 7,721 | Mejor validación + más simple que E1 |
| Ventana (50×19) | Híbrido C (BiLSTM + LGBM + meta + EMA) | 4,34 | 4,338 | Baja el error de cada componente por separado |

## Por qué se dice así

- SAA-9 pide tabla con métricas **y tiempo**, elección por negocio y desempate al más simple.
- La trampa clásica es decir «elegí el de menor RMSE» sin decir en qué conjunto. Aquí se dice:
  **validación**.

## Evidencia

- Orden por `rmse_val`: `src/clase/train_clasicos.py:145` y `src/clase/train_mlp.py:107`.
- Tabla consolidada: `resultados/tabla_final_clase.csv`.
- SHAP del elegido: [[70-nb07-shap-aditividad]] (validación, no test).

## Pregunta probable

**«Entonces, ¿cuál es tu mejor modelo?»**
→ «Depende de la liga y lo digo sin titubear: en fila, E2 con 7,72 de test; en ventana, el
híbrido C con 4,338. No son comparables porque cambian el grano de la muestra y las features.
Lo que sí es común es el criterio de elección.»

## Lo que NO digo

- No digo «el mejor es el de 4,34» sin aclarar que juega en otra liga.
- No digo «probé y me quedé con el que mejor iba en test»: el test no participa en la elección.
- No invento decimales: 4,338 es la fila del manifiesto; 4,33 es una media de semillas.

## Di esto en el tribunal

> «Elijo por validación con la métrica del negocio y desempato al más simple; el test se lee una
> vez y solo para confirmar.»

## Flashcards #flashcards

- ¿Qué conjunto decide la elección? :: la validación; el test solo confirma una vez.
- ¿Cuál es el criterio de desempate? :: el modelo más simple.
- ¿Cuál es el campeón de cada liga? :: E2 en fila (7,72 test) y el híbrido C en ventana (4,338).
