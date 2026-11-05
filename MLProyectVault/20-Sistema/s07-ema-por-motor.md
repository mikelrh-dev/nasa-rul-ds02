---
tipo: sistema
status: sin-estudiar
tags:
  - ema
  - suavizado
  - causal
---

# EMA por motor — suavizado causal

> [!abstract] En una frase
> La predicción cruda oscila; la media exponencial causal por motor la estabiliza sin mirar el futuro.

## Contrato

| Entra | Sale |
|---|---|
| Serie `p_raw` ordenada por ciclo dentro de un motor | Serie `p_ema` suavizada con `span 5` |
| Predicciones de cualquier semilla | Misma longitud, menos diente de sierra |

## Cómo está implementado

El suavizado vive en `src/ds02_rul/smoothing.py` y se aplica dentro de `src/ds02_rul/ensemble.py:101`.

| Pieza | Qué hace | Dónde |
|---|---|---|
| EMA causal | Promedia pasado y presente, nunca futuro | `src/ds02_rul/smoothing.py` |
| Por motor | Reinicia en cada unidad, no mezcla motores | `src/ds02_rul/ensemble.py:101` |
| `ema_span 5` | Constante de memoria del suavizado | `models/ds02_manifest.json` |
| Clipping en cero | Recorta RUL negativas tras suavizar | `src/ds02_rul/ensemble.py:101` |

Causal significa que la predicción de la ventana `t` solo usa ventanas `≤t` del mismo motor ([[c13-ema-causal]]). Un suavizado centrado miraría el futuro y sería trampa en despliegue.

El efecto es sistemático: cada fila `_row` reporta métrica cruda y con EMA (`src/ds02_rul/pipeline.py:78`). El híbrido publicado es siempre «+ EMA5».

## La decisión que hay detrás

ADR-006 adopta EMA causal frente a media simple y frente a suavizado centrado. La media simple reacciona tarde; el centrado es deshonesto porque usa futuro. EMA con span 5 equilibra reacción y estabilidad.

Se rechazó suavizar entre motores: mezclar series de degradaciones distintas crea una inercia ficticia.

## Qué medimos

El híbrido + EMA5 da ≈4.3 con fila de disco 4.338 (bundle C, [[e00-cifras-autoritativas]]). Sin EMA el diente de sierra entre ventanas vecinas infla el RMSE en décimas.

La banda conformal se calibra sobre predicciones ya suavizadas: el ancho medio de 26.41 ciclos incluye este efecto ([[s11-banda-conformal]]).

## El límite

> [!warning] Lo que el suavizado no arregla
> EMA retrasa los cambios bruscos por construcción: si el motor cae de golpe, la media tarda unas ventanas en seguirlo. Span mayor estabiliza más pero avisa más tarde. El 5 es un compromiso, no un óptimo universal.

## Di esto en el tribunal

> [!quote]
> «Aplico media móvil exponencial causal con span 5, por motor y sin mirar el futuro. La serie deja de oscilar y el RMSE baja en décimas. Si usara futuro, la validación mentiría.»

## Flashcards

> [!question]- ¿Qué significa causal en la EMA?
> Que la ventana t solo usa ventanas pasadas y presente del mismo motor.

> [!question]- ¿Qué span se usa y dónde vive?
> Span 5, en el contrato de inferencia del manifiesto.

> [!question]- ¿Por qué se reinicia por motor?
> Porque mezclar degradaciones de motores distintos crea inercia falsa.

> [!question]- ¿Qué se recorta tras suavizar?
> Las RUL negativas se llevan a cero.

> [!question]- ¿Qué afirma esta nota en una frase?
> La predicción cruda oscila; la media exponencial causal por motor la estabiliza sin mirar el futuro.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Aplico media móvil exponencial causal con span 5, por motor y sin mirar el futuro. La serie deja de oscilar y el RMSE baja en décimas. Si usara futuro, la validación mentiría.»

> [!question]- ¿Qué archivo respalda esta nota?
`src/ds02_rul/smoothing.py`

## Conexiones

Antes: [[s06-bilstm-triple-pooling]] · Después: [[s08-ablacion-cyc-norm]] · Mecanismo: [[c13-ema-causal]]
