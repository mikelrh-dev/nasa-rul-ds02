---
tipo: sistema
status: sin-estudiar
tags:
  - clasicos
  - mlp
  - clase
  - validacion
---

# Clásicos y MLP — el grano fila elige al E2

> [!abstract] En una frase
> Cinco clásicos + MLP con GridSearchCV y GroupKFold por motor; el campeón de fila es el MLP E2 (test 7.72), elegido por validación, no por test.

## Contrato

| Entra | Sale |
|---|---|
| Base de [[s15-dataset-de-clase]] + pipeline de [[s16-pipeline-de-clase]] | Campeón fila: MLP E2 + `resultados/mlp_comparativa.csv` |

## Cómo está implementado

| Pieza | Dónde | Qué hace |
|---|---|---|
| 5 clásicos | `src/clase/train_clasicos.py` | regresores base comparables con el mismo pipe y CV |
| MLP + GridSearchCV | `src/clase/train_mlp.py` | parrilla sobre capas/alpha con GroupKFold por `unit` |
| Hipótesis E2 | `resultados/mlp_comparativa.csv` | «más regularización frena memorización de 22 feats», alpha 0.01, (128, 64) |
| Números E2 | train 5.71 / **val 7.34** / **test 7.72** (MAE 5.81, R² 0.83) | elegido por val; test leído una vez |

La elección es por validación: la fila E2 gana en val (7.34) y solo después se lee su test. E1 (más capacidad) y E3 (batch grande) pierden en val y no llegan a test. La métrica que decide es el RMSE de validación porque un error grande es un AOG: hay que castigar el fallo gordo, no el promedio tibio ([[c04-metricas-y-baseline]], [[c22-cuanto-vale-acertar]]).

## Conexiones

- Grano fila: [[c15-grano-fila-vs-ventana]] · GroupKFold: [[c16-groupkfold-por-motor]] · tabla final: [[s19-tabla-final-y-grano]] · cifras: [[e00-cifras-autoritativas]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «El E2 se eligió por validación, con 7.34, y el test se leyó una sola vez: 7.72. Si hubiéramos elegido por test, estaríamos haciendo trampa con la métrica».

## Flashcards

> [!question]- ¿Cómo se elige el campeón de fila y con qué números?
> Por validación con GroupKFold por motor: el MLP E2 ((128,64), alpha 0.01) gana en val (7.34) y su test, leído una vez, da 7.72 / MAE 5.81 / R² 0.83.

> [!question]- ¿Cuáles son los cinco clásicos?
> Ridge (baseline lineal), KNN, Random Forest, XGBoost y SVR: los cinco con el mismo pipeline y GroupKFold por motor en `train_clasicos.py`.

> [!question]- ¿Qué hipótesis prueba el E2?
> Que más regularización frena la memorización de las 22 features transformadas ruidosas (frente a E1: más capacidad hasta overfit; E3: batch grande).
