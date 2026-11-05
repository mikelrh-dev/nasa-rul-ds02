---
tipo: sistema
status: sin-estudiar
tags:
  - dataset
  - clase
  - preproceso
---

# Dataset de clase — la base tabular

> [!abstract] En una frase
> 65 173 filas downsampleadas con la columna objetivo RUL, nulos T30 tratados y fase_vuelo derivada: la materia prima del track tabular.

## Contrato

| Entra | Sale |
|---|---|
| HDF5 DS02 (`archive/CCMaps/N-CMAPSS_DS02-006.h5`), STRIDE 100 | 65 173 filas: train = dev (52 635, uds 2/5/10/18/20/16), test = uds 11/14/15 (12 538, una lectura) |

## Cómo está implementado

| Pieza | Dónde | Qué hace |
|---|---|---|
| `SENSOR_COLS` (14 sensores) | `src/clase/dataset_clase.py:31` | T24, T30, T48, T50, P15, P2, P21, P24, Ps30, P40, P50, Nf, Nc, Wf |
| Imputación T30 MAR | `src/clase/dataset_clase.py` | ffill causal por unidad + mediana de fit-units para el primer NaN |
| `fase_vuelo` | `src/clase/dataset_clase.py` | derivada de alt/Mach (Ascenso 26% / Crucero 30% / Descenso 44%) |
| Split | por motor, nunca por fila | dev y test disjuntos por construcción |

0 duplicados funcionales; Mach en [0.33, 0.74], alt en [10k, 35k]. La RUL nunca se inyecta como feature.

## Conexiones

- Mecanismo de los nulos: [[c17-nulos-mar-e-imputacion-causal]] · la fase: [[c18-fase-vuelo-y-onehot]] · el grano fila: [[c15-grano-fila-vs-ventana]]
- Consume esta base: [[s16-pipeline-de-clase]] · la base adaptada de ventanas: `src/clase/train_ensemble_adaptado.py:67`

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «65 mil filas, nueve motores, split por motor: el test son tres motores que el modelo no vio nunca, leídos una sola vez».

## Flashcards

> [!question]- ¿Qué contiene la base de clase y cómo se parte?
> 65 173 filas (dev 52 635 en 6 motores, test 12 538 en uds 11/14/15), con RUL como objetivo, T30 imputado causalmente y fase_vuelo derivada; el split es por motor, nunca por fila.
