---
tipo: sistema
status: sin-estudiar
tags:
  - persistencia
  - manifiesto
  - contrato
---

# Persistencia y contrato — artefacto reproducible

> [!abstract] En una frase
> Lo que se evalúa es lo que hay en disco: `.keras` nativo, `joblib` y manifiesto con hashes.

## Contrato

| Entra | Sale |
|---|---|
| Ensamble en memoria tras `run_seed` | `ensemble.joblib`, `bilstm_ds02.keras`, `scaler.joblib` |
| Métricas y formas | `ds02_manifest.json` con huellas y protocolo |

## Cómo está implementado

El guardado vive en `src/ds02_rul/persistence.py:108` y la carga en `src/ds02_rul/persistence.py:189`.

| Archivo | Huella | Dónde se verifica |
|---|---|---|
| `ensemble.joblib` | `7acba335…`, 470 446 bytes | `src/ds02_rul/persistence.py:29` |
| `bilstm_ds02.keras` | `d0c5ed7f…`, 1 935 382 bytes | `src/ds02_rul/persistence.py:170` |
| `ds02_manifest.json` | Métricas, formas y protocolo | `src/ds02_rul/persistence.py:37` |
| Guarda de forma | Aborta si el bundle no es DS02 | `src/ds02_rul/persistence.py:94` |

El `.keras` es nativo con la capa `LastStepPooling` registrada al cargar (`src/ds02_rul/persistence.py:170`). Nada de HDF5 legacy ni Lambdas sin registrar ([[s06-bilstm-triple-pooling]]).

El manifiesto fija semillas `[42, 7, 123]`, ventana 50, stride 100, steps 3 y 2, `beta` 1.0 y `ema_span` 5. Si el manifiesto y un cuaderno discrepan, gana el manifiesto ([[e00-cifras-autoritativas]]).

## La decisión que hay detrás

ADR-010 impone `.keras` nativo frente a `h5` y `joblib` frente a `pickle` suelto: el grafo recarga sin el código de entrenamiento y el resto viaja con versión fijada.

La guarda `assert_ds02_artifact` existe porque un bundle de FD001 cargado como DS02 puntuaría sin avisar. Falla alto antes de publicar números.

## Qué medimos

Fila de referencia en disco: 4.251 / 3.183 / 0.9482 / 2305.1 ([[e00-cifras-autoritativas]]). Es la corrida que reproduce `scripts/predict_ds02.py`, no la media de tres semillas.

Verificación en 30 segundos con el manifiesto y comparación contra `notebooks/ds02_ensemble/EVALUACION_EJECUCION.md`. Si difieren, se actualiza solo `e00`.

## El límite

> [!warning] Lo que el artefacto no congela
> El `.keras` fija pesos, no determinismo de reentreno. Reejecutar mueve el RMSE en ±0.1 por TensorFlow en CPU ([[c14-ruido-y-reproducibilidad]]). El disco es la verdad; la reejecución es una muestra nueva.

## Di esto en el tribunal

> [!quote]
> «Lo que defiendo es lo que hay en disco: ensemble con hash 7acba335 y BiLSTM con d0c5ed7f, más manifiesto con métricas y protocolo. La fila de disco da 4.251 y la recarga pasa por guarda de forma.»

## Flashcards

> [!question]- ¿Qué archivos forman el bundle?
> `ensemble.joblib`, `bilstm_ds02.keras`, `scaler.joblib` y `ds02_manifest.json`.

> [!question]- ¿Qué hashes tienen?
> Ensemble `7acba335…` y BiLSTM `d0c5ed7f…`.

> [!question]- ¿Qué hace assert_ds02_artifact?
> Aborta si el bundle no tiene la forma DS02 que declara.

> [!question]- ¿Qué manda si hay discrepancia?
> El manifiesto. La nota y el cuaderno se corrigen, el disco no se discute.

> [!question]- ¿Qué afirma esta nota en una frase?
> Lo que se evalúa es lo que hay en disco: `.keras` nativo, `joblib` y manifiesto con hashes.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Lo que defiendo es lo que hay en disco: ensemble con hash 7acba335 y BiLSTM con d0c5ed7f, más manifiesto con métricas y protocolo. La fila de disco da 4.251 y la recarga pasa por guarda de forma.»

> [!question]- ¿Qué archivo respalda esta nota?
`src/ds02_rul/persistence.py:108`

## Conexiones

Antes: [[s11-banda-conformal]] · Después: [[s13-capa-de-reglas-y-decision]] · Evidencia: [[e00-cifras-autoritativas]]
