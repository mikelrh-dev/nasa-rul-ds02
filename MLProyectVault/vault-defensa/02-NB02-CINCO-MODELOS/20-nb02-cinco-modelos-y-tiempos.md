---
title: NB02 · Cinco modelos y tiempos
course: Reto 1 · SAA+PIA+MIA
block: 02 — NB02 cinco modelos
node: B2.1
indicador: SAA-6
descriptor: 10
spine: true
status: en-curso
tags:
  - nb02
  - modelos
  - rubrica/saa-6
---

# NB02 · Cinco modelos y tiempos

> [!abstract] En una frase
> Cinco modelos, **el mismo pipeline** y el mismo split: lo único que cambia es el estimador.
> Así la comparación mide el modelo, no el preprocesado.

## La tabla que se enseña

| Modelo | RMSE train | RMSE val | MAE val | R² val | Tiempo (s) |
|---|---|---|---|---|---|
| KNN (`k=31`) | 6,984 | 9,409 | 8,186 | 0,818 | 9,1 |
| Regresión (`alpha=10`) | 8,200 | 8,276 | 7,661 | 0,850 | 3,5 |
| Random Forest (`max_depth=8`) | 7,157 | 9,070 | 8,153 | 0,827 | 79,6 |
| SVM (`C=10`, `epsilon=1`) | 7,525 | 8,293 | 7,530 | 0,857 | 2,7 |
| **XGBoost (`max_depth=4`)** | **7,189** | **8,217** | **7,469** | **0,854** | **7,2** |

Fuente: `resultados/comparativa.csv`. Todos con `Pipeline(preprocesado, estimador)` y
`GroupKFold` por motor.

## Qué digo

«Los cinco ven exactamente el mismo preprocesado y el mismo split por motor. Gana XGBoost por
validación, 8,22, pero el mensaje importante está en la primera columna: KNN y Random Forest se
ajustan al train y se caen en validación; la regresión y el SVM no se caen tanto porque son más
rígidos. Es el clásico sesgo-varianza, medido.»

## Por qué se dice así

- La rúbrica pide «los 5 modelos» y, para el 10, **probar algo no visto en clase**. Eso se
  cubre dos veces: con la ablación de `cyc_norm` ([[30-nb03-ablacion-cyc-norm]]) y con el
  híbrido BiLSTM + meta ([[60-nb06-cascada-bundle-c]]).
- El tiempo de entrenamiento está en la tabla porque la rúbrica SAA-9 lo pide explícitamente.

## Evidencia

- Escritor oficial: `src/clase/train_clasicos.py:108` (`entrenar_todo`), ordena por `rmse_val`
  en la línea 145 y escribe el CSV y el joblib.
- Pipeline: `src/clase/pipeline_clase.py:27` (`ColumnTransformer`).
- Split: `GroupKFold` por `unit`, nunca por fila.

## Pregunta probable

**«¿Por qué no hay SMOTE?»**
→ «SMOTE es para clasificación desbalanceada. Esto es regresión: no hay clases que balancear.
El análogo aquí es el desbalance de motores —el 14 tiene 760 ventanas frente a 3 293 del 11— y
se trata con el macro-RMSE y el split por motor, no remuestreando.»

## Lo que NO digo

- No digo «probé muchos modelos y me quedé con el mejor» sin decir el criterio: el criterio es
  validación y desempate al más simple.
- No mezclo el `rmse_val` de XGB (8,22) con el `rmse_test` de E2 (7,72): son otra liga.

## Di esto en el tribunal

> «Cinco modelos, un solo pipeline y un split por motor: la tabla mide el estimador, no el
> preprocesado.»

## Flashcards #flashcards

- ¿Cuál gana entre los cinco y con qué métrica? :: XGBoost, 8,217 de RMSE en validación.
- ¿Qué dos modelos se sobreajustan más? :: KNN (6,98 train / 9,41 val) y Random Forest (7,16 / 9,07).
- ¿Por qué no SMOTE? :: porque es regresión; el desbalance se trata con macro-RMSE y split por motor.
