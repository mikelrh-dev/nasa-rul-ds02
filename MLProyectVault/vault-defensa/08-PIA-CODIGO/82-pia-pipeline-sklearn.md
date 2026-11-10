---
title: PIA · Pipeline de sklearn
course: Reto 1 · SAA+PIA+MIA
block: 08 — PIA código
node: C3
indicador: PIA-3
descriptor: 10
spine: false
status: en-curso
tags:
  - pia
  - pipeline
  - rubrica/pia-3
---

# PIA · Pipeline de sklearn

> [!abstract] En una frase
> El pipeline no es orden: es la garantía de que el escalado **se ajusta solo en train** y de que
> el artefacto guardado sabe preprocesar un caso nuevo sin código alrededor.

## Qué digo

«Hay un `ColumnTransformer` con `StandardScaler` para lo numérico y `OneHotEncoder` para la fase
de vuelo; ese transformador va dentro del `Pipeline` junto al estimador. Lo usan los cinco
modelos y el MLP. Y el joblib que se guarda **incluye el pipeline**, así que predecir un caso
nuevo es cargar el artefacto y llamar a `predict`, sin repetir el preprocesado a mano.»

## Por qué importa tanto

- El 7 exige el pipeline; el 10 exige **además** que el modelo guardado lo incluya y prediga un
  caso nuevo. Es la diferencia entre «lo hice en el notebook» y «lo puedo servir».
- Si el escalado se ajustara sobre todo el dataset, la validación mentiría: es la fuga más común.

## Evidencia

- `src/clase/pipeline_clase.py:27` (`ColumnTransformer`) y `:38` (`make_pipeline`).
- Artefactos que incluyen el pipeline: `models/mejor_modelo_clase.joblib`,
  `models/mejor_modelo_clase_E2.joblib`.
- Predicción de caso nuevo: `scripts/predict_ds02.py` y la app ([[84-pia-streamlit-test-y-caso-nuevo]]).

## Pregunta probable

**«¿Por qué no escalar una vez y guardar los arrays?»**
→ «Porque entonces el preprocesado queda fuera del artefacto y hay que replicarlo en cada
consumidor. Con el pipeline dentro, el mismo objeto que se entrenó es el que predice; y si mañana
cambia el encoder, cambia en un solo sitio.»

## Lo que NO digo

- No digo «normalizo el dataset»: el scaler se ajusta con `fit` solo en train.
- No digo que el pipeline del track de clase sea el mismo que el del sistema de ventanas: son dos
  preprocesados distintos con el mismo principio.

## Di esto en el tribunal

> «Un `ColumnTransformer` con escalado y one-hot dentro del `Pipeline`; el joblib guardado incluye
> el pipeline, así que predice un caso nuevo sin preprocesar a mano.»

## Flashcards #flashcards

- ¿Qué dos transformadores van en el `ColumnTransformer`? :: `StandardScaler` y `OneHotEncoder`.
- ¿Dónde se ajusta el escalado? :: solo en train, dentro del `Pipeline`.
- ¿Qué garantiza que el artefacto prediga un caso nuevo? :: que el joblib guardado incluye el pipeline completo.
