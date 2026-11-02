---
tipo: concepto
status: sin-estudiar
tags:
  - pooling
  - bilstm
  - serializacion
  - keras
---

# Pooling temporal: cómo 50 pasos se vuelven un vector

> [!abstract] En una frase
> El pooling decide qué parte de la trayectoria sobrevive; el campeón de este proyecto no elige una vista, concatena tres.

## El problema que resuelve

Una capa recurrente con `return_sequences=True` devuelve un tensor de forma `(batch, 50, 128)`: un vector por cada paso. La cabeza densa que produce la RUL necesita un vector de tamaño fijo por ventana. Alguien tiene que colapsar el eje temporal, y la forma de colapsarlo es una decisión de modelado, no un detalle de implementación.

Cada colapso conserva algo distinto y descarta algo distinto. Elegir "el último paso" y elegir "el promedio" producen modelos con sesgos diferentes sobre el mismo tensor.

## Cómo funciona

| Pooling | Qué conserva | Qué descarta |
|---|---|---|
| último paso | el estado final de la recurrencia, que ya acumuló la ventana | deja toda la decisión en un único vector, sensible al ruido del último ciclo |
| media | el nivel medio de la ventana | borra el final, y con él la parte más cercana a la falla |
| máximo | el valor más extremo de cada dimensión | no distingue un pico de degradación de un outlier de sensor |

**Triple pooling.** El campeón concatena las tres vistas en lugar de elegir una:

```
Concatenate( LastStepPooling, GlobalAveragePooling1D, GlobalMaxPooling1D )
```

Cada vista aporta 128 dimensiones —64 por sentido de la capa bidireccional—, así que la concatenación entrega 384. La cabeza densa posterior decide cuánto pesar cada vista; el modelo no tiene que apostar a una sola. En `src/ds02_rul/model.py:34` se ve la concatenación y en `src/ds02_rul/model.py:36` a `model.py:38` las tres ramas.

**El problema de serializar un `Lambda`.** La versión original del cuaderno tomaba el último paso con `Lambda(lambda z: z[:, -1, :])`. Keras serializa un lambda suelto como bytecode de Python marshaleado, y el formato de los objetos código cambia entre versiones menores del intérprete. Consecuencia práctica: un artefacto guardado así solo se puede cargar con el mismo Python que lo escribió. El `.keras` deja de ser portable, y un bundle que no se puede recargar en otra máquina no es un entregable.

**`LastStepPooling` como capa registrada.** La solución es una subclase de `layers.Layer` registrada como serializable, que declara su configuración y su forma de salida. Se serializa por valor —nombre de clase y parámetros—, no por bytecode. El código son tres métodos: `call` devuelve `inputs[:, -1, :]`, `compute_output_shape` devuelve `(batch, features)` y `get_config` delega en la clase base. Ver `src/ds02_rul/pooling.py:19`, `src/ds02_rul/pooling.py:22` y `src/ds02_rul/pooling.py:25`.

El docstring del módulo lo dice sin rodeos: el grafo es compatible en orden de pesos con el original, y el único cambio es que el corte del último paso es una capa registrada en lugar de un `Lambda` (`src/ds02_rul/pooling.py:3`).

## Dónde aparece en este proyecto

- `src/ds02_rul/model.py:34` — `Concatenate(name="temporal_pooling")` con las tres ramas; es el nudo donde se define el tamaño de la cabeza.
- `src/ds02_rul/model.py:41` — un `Dropout(0.2)` sobre el vector concatenado, antes de la proyección densa de 32 unidades (`model.py:42`).
- `src/ds02_rul/pooling.py:15` — el decorador `register_keras_serializable(package="ds02_rul")` que hace cargable la capa.
- `src/ds02_rul/persistence.py:170` — `load_bilstm` registra la capa personalizada antes de cargar el grafo; sin ese registro, la carga falla.
- El efecto sobre el artefacto final está en [[s06-bilstm-triple-pooling]] y el contrato de guardado en [[s12-persistencia-y-contrato]].

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Solo último paso | Deja toda la decisión en un vector; un pico de ruido en el ciclo final manda en la predicción |
| Solo media | Borra el final de la ventana, que es la parte más informativa sobre el estado actual |
| Solo máximo | Se satura con un outlier de sensor y no distingue pico de degradación de ruido |
| `Flatten` de los 50 pasos | 6 400 dimensiones de entrada a la cabeza densa: parámetros de más y sobreajuste seguro con 17 450 ventanas de dev |
| `Lambda` para el último paso | Se serializa como bytecode y ata el artefacto a la versión menor de Python que lo escribió |

> [!warning] La trampa
> El triple pooling **concatena**, no promedia. Decir "promedio el último paso, la media y el máximo" describe otro modelo y otra dimensión de cabeza. Y el `Lambda` no es un detalle cosmético: un bundle que solo carga en el intérprete que lo escribió no se puede desplegar ni auditar fuera de esa máquina.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «El pooling es la decisión de qué parte de la ventana sobrevive; el campeón no elige una, concatena el último paso, la media y el máximo en 384 dimensiones».
> «El `Lambda` del cuaderno original guardaba bytecode y ataba el modelo a una versión de Python; lo reemplacé por una capa registrada que se serializa por valor».
> «Ese cambio no toca ni un peso: el grafo es compatible en orden de pesos con el original, solo cambia cómo se guarda».

## Flashcards

> [!question]- ¿Qué tres vistas temporales combina el campeón y en qué orden?
> Último paso, media global y máximo global, concatenadas en ese orden por `layers.Concatenate`. Cada una aporta 128 dimensiones, así que la cabeza recibe 384.

> [!question]- ¿Qué información pierde el pooling por media que el último paso conserva?
> El final de la ventana. La media resume el nivel de los 50 ciclos, pero no distingue una ventana que termina degradada de una que empezó degradada y se recuperó.

> [!question]- ¿Por qué un `Lambda` de Keras rompe el guardado del modelo?
> Porque Keras lo serializa como bytecode marshaleado, y el formato de esos objetos cambia entre versiones menores de Python. El artefacto queda atado al intérprete que lo escribió y no se puede recargar en otro entorno.

> [!question]- ¿Qué hace que `LastStepPooling` sea portable?
> Es una subclase registrada de `layers.Layer` con `get_config` propio, así que se serializa por nombre de clase y configuración en lugar de por código. Al cargar, basta con registrar la clase antes de abrir el `.keras`.

## Conexiones

Antes: [[c06-bilstm-y-secuencias]] · Después: [[s06-bilstm-triple-pooling]]
