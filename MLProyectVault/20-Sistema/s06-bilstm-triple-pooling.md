---
tipo: sistema
status: sin-estudiar
tags:
  - bilstm
  - secuencias
  - campeon
---

# BiLSTM triple pooling — modelo base B

> [!abstract] En una frase
> El campeón lee la película de 50 pasos en dos direcciones y resume con tres lecturas a la vez.

## Contrato

| Entra | Sale |
|---|---|
| Secuencia `(50, 19)` ordenada por ciclo | Predicción `p_lstm` del RUL |
| Semilla y early stopping en unidad genuina | Mismo grafo, distinto ruido (±0.54) |

## Cómo está implementado

El grafo vive en `src/ds02_rul/model.py:19` y el entrenamiento en `src/ds02_rul/pipeline.py:50`.

| Pieza | Qué hace | Dónde |
|---|---|---|
| 2 capas BiLSTM | Leen 50 pasos hacia adelante y hacia atrás | `src/ds02_rul/model.py:19` |
| Triple pooling | Combina last, media y máximo temporal | `src/ds02_rul/model.py:19` |
| Capa densa 32 | Proyecta el resumen a RUL | `src/ds02_rul/model.py:19` |
| `LastStepPooling` serializable | Evita el Lambda no serializable | `src/ds02_rul/pooling.py:16` |
| Early stopping | Para en unidad genuinamente retenida | `src/ds02_rul/pipeline.py:50` |

Parámetros totales: 154 253 (`models/ds02_manifest.json`). La clase de pooling registra `get_config` para que el `.keras` recargue sin código fantasma (`src/ds02_rul/pooling.py:25`).

Solo da ≈6.22 ± 0.54 en RMSE: mejor que LightGBM pero con más varianza entre semillas ([[e00-cifras-autoritativas]]). Es el campeón del ensamble: `beta=0` reproduce exactamente esta rama ([[s10-stacking-hibrido]]).

## La decisión que hay detrás

ADR-003 elige BiLSTM bidireccional frente a LSTM unidireccional y frente a TCN: la degradación se lee mejor con contexto pasado y futuro dentro de la ventana. El triple pooling se queda porque cada lectura aporta: el último paso la posición, la media el nivel, el máximo el pico.

Se rechazó serializar con Lambda: el `.keras` no recargaba fuera del entrenamiento. La capa propia lo arregla.

## Qué medimos

BiLSTM solo: RMSE 6.218 ± 0.541, MAE 4.820 ± 0.477, R² 0.8887 ± 0.0191, NASA 4397.8 ± 550.9 ([[e00-cifras-autoritativas]]).

La dispersión ±0.54 es resolución del cómputo en CPU, no error de medida ([[c14-ruido-y-reproducibilidad]]). Por eso el bundle cita media y desviación, no una sola corrida.

## El límite

> [!warning] Lo que el campeón no ve
> Medio ciclo de contexto no basta para colas largas, y la varianza entre semillas es alta. Sin el meta y sin EMA, el campeón oscila de ventana a ventana. Es el mejor solo, pero no es estable solo.

## Di esto en el tribunal

> [!quote]
> «El BiLSTM lee 50 pasos en dos direcciones con triple pooling y 154 mil parámetros. Solo da 6.22 con dispersión de medio punto entre semillas. Es el campeón: si beta es cero, el híbrido es él.»

## Flashcards

> [!question]- ¿Qué forma entra y cuántos parámetros tiene?
> `(None, 50, 19)` y 154 253 parámetros.

> [!question]- ¿Qué combina el triple pooling?
> Last, media y máximo temporal antes de la densa.

> [!question]- ¿Por qué existe LastStepPooling?
> Para serializar el `.keras` sin un Lambda que impida recargar.

> [!question]- ¿Cuánto da solo y con qué dispersión?
> RMSE ≈6.22 ± 0.54 entre las tres semillas.

> [!question]- ¿Qué afirma esta nota en una frase?
> El campeón lee la película de 50 pasos en dos direcciones y resume con tres lecturas a la vez.

> [!question]- ¿Cómo la contarías en el tribunal?
> «El BiLSTM lee 50 pasos en dos direcciones con triple pooling y 154 mil parámetros. Solo da 6.22 con dispersión de medio punto entre semillas. Es el campeón: si beta es cero, el híbrido es él.»

## Conexiones

Antes: [[s05-lightgbm-cuantilico]] · Después: [[s07-ema-por-motor]] · Mecanismo: [[c06-bilstm-y-secuencias]]
