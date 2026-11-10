---
title: NB02 · Métricas y error de negocio
course: Reto 1 · SAA+PIA+MIA
block: 02 — NB02 cinco modelos
node: B2.3
indicador: SAA-8
descriptor: 10
spine: false
status: en-curso
tags:
  - nb02
  - metricas
  - rubrica/saa-8
---

# NB02 · Métricas y error de negocio

> [!abstract] En una frase
> RMSE, MAE y R² no son tres formas de decir lo mismo: RMSE castiga los fallos grandes, MAE
> dice el error típico y R² dice cuánto se explica. Al tribunal le importa **qué significa el
> error en ciclos**.

## Qué digo

«Uso RMSE porque un error grande en un motor que se va a hangar cuesta más que muchos errores
pequeños; MAE para decir el error típico; R² para saber cuánto de la varianza se explica. En el
track de clase, XGB queda en 8,22 de RMSE en validación con R² 0,854. En el sistema desplegado,
4,338 con MAE 3,227 y R² 0,9461: el error típico son unos tres ciclos y medio.»

## La traducción a negocio

| Métrica | Valor desplegado | Qué significa para el operador |
|---|---|---|
| RMSE | 4,338 | Un fallo grande pesa el doble que dos pequeños; el castigo está donde duele |
| MAE | 3,227 | Me equivoco ~3 ciclos de media, frente a un margen de 9–23 ciclos |
| R² | 0,9461 | Explico el 94,6 % de la variación del RUL en test |
| NASA score | 2336,2 | Suma asimétrica: penaliza predecir tarde más que pronto |

## Por qué se dice así

- El 7 son «varias métricas en train y validación». El 10 exige **explicar qué significan los
  errores para la empresa**: eso es la tabla de arriba.
- Decir «3,2 ciclos de error contra 9–23 de margen» es la frase que convierte una métrica en
  una decisión.

## Evidencia

- `resultados/comparativa.csv` y `resultados/mlp_comparativa.csv` (train y validación).
- Desplegado: `models/ds02_manifest.json` → `metrics.reference_row`.
- Real frente a predicho: `resultados/real_vs_predicho_bundle_c.png`.

## Pregunta probable

**«¿Por qué solo XGB tiene columnas de test en la tabla?»**
→ «Porque el test se toca una sola vez y solo con el elegido. Las columnas vacías son la prueba
de que no se eligió mirando el test; rellenarlas sería hacer trampa, no completar la tabla.»

## Lo que NO digo

- No digo «accuracy»: es regresión.
- No comparo el RMSE de un modelo medido en validación con el de otro medido en test.
- No digo que R² 0,95 signifique que acierta el 95 % de las veces.

## Di esto en el tribunal

> «El error típico son 3,2 ciclos contra un margen de actuación de 9 a 23: el aviso llega antes
> de que la decisión sea urgente.»

## Flashcards #flashcards

- ¿Por qué RMSE y no solo MAE? :: porque castiga los fallos grandes, que son los caros.
- ¿Qué significa MAE 3,227 en la práctica? :: que el error típico es de ~3 ciclos frente a un margen de 9–23.
- ¿Por qué la tabla tiene columnas de test vacías? :: porque el test se lee una vez, solo con el modelo elegido.
