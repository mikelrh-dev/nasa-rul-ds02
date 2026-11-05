---
tipo: sistema
status: sin-estudiar
tags:
  - lightgbm
  - cuantil
  - tabular
---

# LightGBM cuantílico — modelo base A

> [!abstract] En una frase
> La rama tabular predice el cuantil 0,35 con 93 columnas y pierde a propósito contra el BiLSTM.

## Contrato

| Entra | Sale |
|---|---|
| Vector de 93 features por ventana | Predicción `p_lgb` del cuantil 0,35 |
| Semilla 42, 7 o 123 | Misma forma, distinto ruido de ajuste |

## Cómo está implementado

La fábrica vive en `src/ds02_rul/pipeline.py:46` y el manifiesto fija `alpha` 0,35 (`models/ds02_manifest.json`).

| Pieza | Valor | Dónde |
|---|---|---|
| Objetivo | `quantile` con `alpha` 0,35 | `models/ds02_manifest.json` |
| Entrada | 93 features tabulares | `src/ds02_rul/ensemble.py:193` |
| Constructor | `make_lgbm(seed)` | `src/ds02_rul/pipeline.py:46` |
| Papel | Base A del stacking | `src/ds02_rul/ensemble.py:49` |

La pérdida es pinball ([[c05-regresion-cuantilica]]): castiga más por un lado que por otro para situarse en el cuantil pedido, no en la media. Con `alpha` 0,35 el modelo subestima de forma sistemática, y eso es intencional: complementa al BiLSTM en el meta.

Solo da ≈7.1 en RMSE (≈7.067 la adaptada sobre base con nulos, [[e00-cifras-autoritativas]]). No compite con el BiLSTM: aporta una lectura distinta del mismo desgaste.

## La decisión que hay detrás

ADR-005 elige cuantil 0,35 tras barrer `alpha` fuera del test. La media (0,5) era más precisa sola pero menos útil combinada: se solapaba con el BiLSTM en vez de complementarlo.

Se rechazó usar LightGBM como predictor final único: su NASA de ≈5772 es casi el doble que el híbrido. Es buen comparsa y mal solista.

## Qué medimos

LightGBM solo: RMSE 7.098 ± 0.034, MAE 5.572 ± 0.034, R² 0.8557 ± 0.0014, NASA 5772.5 ± 50.1 ([[e00-cifras-autoritativas]]).

La mejora del híbrido sobre esta rama (≈2.76 ciclos de RMSE) es la que justifica el ensamble ([[s10-stacking-hibrido]]).

## El límite

> [!warning] Lo que esta rama no hace
> No ve orden temporal: lee resúmenes de la ventana, no la película. Un cambio brusco dentro de los 50 pasos se diluye en la media. Por eso necesita al BiLSTM al lado.

## Di esto en el tribunal

> [!quote]
> «LightGBM lee 93 resúmenes tabulares y predice el cuantil 0,35. Solo da ≈7.1 de RMSE, peor que el BiLSTM. Su valor no es ganar solo, es equivocarse distinto para que el meta combine.»

## Flashcards

> [!question]- ¿Qué predice LightGBM y con qué entrada?
> El cuantil 0,35 con 93 features tabulares por ventana.

> [!question]- ¿Dónde se fija alpha 0,35?
> En el objetivo `quantile` del manifiesto y en `make_lgbm`.

> [!question]- ¿Cuánto da solo y por qué sigue en el ensamble?
> RMSE ≈7.1. Sigue porque su error complementa al del BiLSTM.

> [!question]- ¿Qué pérdida usa y qué minimiza?
> Pinball loss: su mínimo está en el cuantil, no en la media.

> [!question]- ¿Qué afirma esta nota en una frase?
> La rama tabular predice el cuantil 0,35 con 93 columnas y pierde a propósito contra el BiLSTM.

> [!question]- ¿Cómo la contarías en el tribunal?
> «LightGBM lee 93 resúmenes tabulares y predice el cuantil 0,35. Solo da ≈7.1 de RMSE, peor que el BiLSTM. Su valor no es ganar solo, es equivocarse distinto para que el meta combine.»

> [!question]- ¿Qué archivo respalda esta nota?
`src/ds02_rul/pipeline.py:46`

## Conexiones

Antes: [[s04-ventanas-y-features]] · Después: [[s06-bilstm-triple-pooling]] · Mecanismo: [[c05-regresion-cuantilica]]
