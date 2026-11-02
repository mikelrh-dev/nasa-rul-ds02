---
tipo: concepto
status: sin-estudiar
tags:
  - bilstm
  - secuencias
  - rnn
  - lstm
---

# BiLSTM y secuencias: leer una trayectoria, no una foto

> [!abstract] En una frase
> Una RUL no está en una fila de sensores: está en cómo cambia esa fila a lo largo del tiempo, y una red recurrente es el mecanismo que convierte 50 ciclos ordenados en un vector de estado.

## El problema que resuelve

Un modelo tabular recibe un vector y devuelve un número. Si se le entrega una ventana como 50 filas apiladas, el orden se pierde: la fila 3 y la fila 47 son intercambiables bajo cualquier permutación de columnas. Peor todavía, promediar la ventana borra la dirección del cambio, y la dirección del cambio es exactamente la señal de degradación.

Dos trayectorias opuestas pueden compartir la misma media y la misma desviación. Una sube, la otra baja. Cualquier resumen sin orden —media, máximo, desviación estándar— las declara idénticas. Esa pérdida es la que ataca este modelo.

La ventana y su horizonte se explican en [[c02-ventanas-y-horizonte]]; el objetivo, en [[c01-que-es-rul]].

## Cómo funciona

**RNN.** Una red recurrente procesa la secuencia paso a paso y mantiene un estado oculto $h_t$ que se actualiza con la observación nueva y el estado anterior:

$$h_t = \tanh(W_x x_t + W_h h_{t-1} + b)$$

Los mismos pesos se aplican en cada paso; lo único que cambia es el estado. La longitud de la secuencia no está fijada en la arquitectura, solo el tamaño de cada paso.

**LSTM.** La RNN simple tiene un problema práctico: el gradiente que atraviesa muchos pasos se desvanece o explota, y la red termina olvidando lo que pasó veinte ciclos atrás. La LSTM agrega una celda de memoria $c_t$ y tres compuertas que deciden qué entra, qué permanece y qué se expone:

| Compuerta | Pregunta que responde |
|---|---|
| olvido | qué parte del estado anterior ya no sirve |
| entrada | qué parte de la observación nueva se escribe en la celda |
| salida | qué parte de la celda se publica como estado |

Las compuertas son sigmoides: valores entre 0 y 1 que multiplican. Con la compuerta de olvido cerca de 1, el gradiente viaja por la celda sin multiplicarse por la matriz recurrente en cada paso. Eso es lo que permite aprender dependencias largas.

**Bidireccionalidad.** Una capa `Bidirectional` corre dos LSTM sobre la misma secuencia, una de izquierda a derecha y otra de derecha a izquierda, y concatena sus salidas. Cada paso queda representado por 128 valores —64 por sentido— que resumen el pasado y el futuro de la ventana. Con 50 filas, el último paso ya no es "lo último que pasó": es un resumen que conoce toda la ventana. Esto es legítimo aquí porque la ventana completa existe al momento de predecir; en un streaming estricto, paso a paso, no lo sería.

## Dónde aparece en este proyecto

- `src/ds02_rul/model.py:30` y `src/ds02_rul/model.py:32` — dos capas `Bidirectional(LSTM(64))`, ambas con `return_sequences=True` para que la siguiente capa y el pooling reciban los 50 pasos.
- `src/ds02_rul/model.py:16` — `N_CHANNELS = 19`: 18 señales escaladas más el ciclo normalizado. Entrada `(None, 50, 19)`, 154 253 parámetros ([[e00-cifras-autoritativas]]).
- `src/ds02_rul/features.py:134` — donde el ciclo normalizado se repite como canal 19 en cada fila de la ventana.
- `src/ds02_rul/model.py:48` — pérdida `Huber(delta=10.0)`; el optimizador es Adam con tasa 0.001 (`model.py:47`).
- `src/ds02_rul/pipeline.py:50` — `fit_bilstm` recibe `val_idx` explícito y lo usa como `validation_data` (`pipeline.py:62`); esas filas son de la unidad 16, que no está en `fit_idx`. El detalle completo, en [[s06-bilstm-triple-pooling]].

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Ventana aplanada en un modelo tabular | El orden desaparece; 50 pasos se vuelven columnas sin estructura temporal |
| RNN simple, sin compuertas | El gradiente no sobrevive 50 pasos y no aprende dependencias largas |
| LSTM unidireccional | Desperdicia la segunda mitad de la ventana: el estado final no ve lo que viene después |
| CNN 1D sobre la ventana | Reconoce patrones locales, pero no acumula estado a lo largo de toda la vida del motor |

> [!warning] La trampa
> La bidireccionalidad no es gratis: solo es válida si la ventana completa está disponible al predecir. Y hay una superposición incómoda: la unidad 16 sirve a la vez para detener el entrenamiento y para ajustar el meta-aprendiz. Decir "el modelo nunca vio la unidad 16" es falso; la vio como validación. Está registrado como deuda en [[c10-oof-y-validacion-agrupada]].

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Una RUL no está en una foto de sensores, está en la película. Por eso el modelo secuencial recibe 50 ciclos ordenados y no una tabla».
> «La LSTM agrega compuertas que deciden qué recordar; la bidireccionalidad hace que cada paso vea el pasado y el futuro de la ventana».
> «Son dos capas de 64 unidades por sentido, 154 253 parámetros, y el entrenamiento se detiene con una unidad que no participa del ajuste de pesos».

## Flashcards

> [!question]- ¿Por qué aplanar la ventana en un modelo tabular pierde información que una LSTM conserva?
> Porque el aplanado destruye el orden temporal: cualquier permutación de las 50 filas produce la misma matriz de columnas. La LSTM procesa los pasos en secuencia y su estado acumula la dirección del cambio, que es la señal de degradación.

> [!question]- ¿Qué agrega una compuerta de olvido que una RNN simple no tiene?
> Un camino multiplicativo controlado para la celda de memoria. Si la compuerta está cerca de 1, el gradiente atraviesa muchos pasos sin desvanecerse, y la red puede aprender dependencias largas dentro de la ventana.

> [!question]- ¿Qué significa que la capa sea bidireccional y por qué es legítimo aquí?
> Que dos LSTM recorren la secuencia en sentidos opuestos y sus salidas se concatenan, de modo que cada paso ve el pasado y el futuro de la ventana. Es legítimo porque la ventana de 50 filas ya está completa cuando se predice; no habría que usarla en un escenario de streaming estricto.

> [!question]- ¿Sobre qué datos se hace el early stopping de la BiLSTM?
> Sobre la unidad 16, que no pertenece a las unidades de ajuste. Es una unidad realmente apartada para detener el entrenamiento, aunque después se reutiliza para ajustar el meta-aprendiz y esa reutilización es una limitación declarada.

## Conexiones

Antes: [[c02-ventanas-y-horizonte]] · Después: [[c07-pooling-temporal]]
