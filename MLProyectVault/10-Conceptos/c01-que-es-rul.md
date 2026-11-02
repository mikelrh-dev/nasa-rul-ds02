---
tipo: concepto
status: sin-estudiar
tags:
  - rul
  - regresion
  - objetivo
---

# Qué es RUL y por qué se predice con regresión

> [!abstract] En una frase
> RUL es la cantidad de ciclos de vuelo que le quedan a un motor antes del fallo, y se predice con una regresión porque la decisión de mantenimiento necesita un número de ciclos, no una etiqueta.

## El problema que resuelve

Un motor se degrada de forma monótona: cada ciclo que vuela lo acerca al fallo. Lo que el taller no sabe es **cuántos ciclos le quedan**, y esa cifra decide si el motor sigue volando, entra a inspección o va a hangar.

La RUL se mide en **ciclos de vuelo**, no en horas ni en días. Un ciclo es un vuelo completo, desde el arranque hasta el apagado. Cada motor vive una cantidad distinta de ciclos, así que la misma cifra de RUL significa distinto según la unidad.

El objetivo es una variable continua, ordenada y con signo útil: no da lo mismo equivocarse tres ciclos por arriba que tres por abajo. El score de evaluación cobra distinto cada dirección, y por eso el problema se plantea como regresión.

## Cómo funciona

El modelo no predice la RUL de un motor: predice la RUL de una **ventana** de 50 filas. La etiqueta es un solo número, la RUL de la **última fila** de esa ventana:

```python
y_list.append(float(y_u[i + window_size - 1]))
```

`src/ds02_rul/features.py:156`

De ahí salen dos consecuencias que ordenan todo el resto del proyecto.

- La ventana aporta el contexto; la etiqueta mira el futuro de su última fila. Nunca se etiqueta con la primera fila, porque eso desplazaría el objetivo hacia el pasado.
- Como las ventanas se solapan, las etiquetas también se solapan. Eso obliga a validar por motor y no por fila ([[c03-fuga-de-informacion]]).

La predicción se devuelve por ventana: `predict` recibe `(n, window, 18)` y devuelve un `(n,)` (`src/ds02_rul/ensemble.py:101`). Para armar la curva de un motor se ordenan sus ventanas por ciclo.

Una precisión que se pregunta siempre: **el clamp a 125 ciclos no existe en este proyecto**. Ese recorte es del cargador de FD001:

```python
train["RUL"] = (...).clip(upper=125)
test["RUL"] = (...).clip(upper=125)
```

`src/ds02_rul/data.py:94` y `src/ds02_rul/data.py:97`

El cargador de DS02 no aplica ningún recorte, y lo dice en su propio docstring (`src/ds02_rul/data.py:53`). La RUL de DS02 llega hasta el final de vida real de cada motor.

## Dónde aparece en este proyecto

- La etiqueta se construye en `src/ds02_rul/features.py:156`, una por ventana, tomada de la última fila.
- El contrato de inferencia devuelve un número por ventana en `src/ds02_rul/ensemble.py:101`.
- El recorte a 125 ciclos vive solo en `src/ds02_rul/data.py:94` y `:97`, dentro de `load_fd001_reference`.
- La capa de decisión compara una cota en ciclos contra umbrales (`src/ds02_rul/ensemble.py:161`), no contra probabilidades: [[s13-capa-de-reglas-y-decision]].
- El reparto de unidades que hace evaluable esa cifra: [[s02-datos-ds02-y-reparto]].

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Clasificación en tres estados (APTO / INSPECCIÓN / HANGAR) | Aprende fronteras, no distancias. Cambiar un umbral obligaría a reentrenar, y el tribunal pierde la magnitud del error. |
| Clasificación binaria «¿falla en los próximos N ciclos?» | Devuelve una probabilidad, y una probabilidad no dice cuántos ciclos quedan ni permite calcular una cota inferior. |
| RUL en horas de vuelo | La degradación está indexada por ciclos en el dataset; convertir introduce una regla de negocio que el modelo no puede verificar. |
| Etiquetar la ventana con la RUL de su primera fila | Desplaza el objetivo al pasado y hace que el modelo aprenda con información que en producción todavía no existe. |

> [!warning] La trampa
> Si citás el clamp de 125 ciclos como parte de este pipeline, te equivocaste de cargador. Ese `clip` está en `load_fd001_reference` y el camino DS02 lo evita a propósito: truncar la RUL borraría la parte alta del objetivo, que es justo donde el modelo se equivoca más.

## Di esto en el tribunal

> [!quote]
> «Predigo RUL en ciclos de vuelo: cuántos ciclos le quedan al motor antes del fallo. Es una regresión y no una clasificación porque la decisión se toma comparando una cota numérica contra umbrales, y porque el error tiene magnitud y dirección, que se cobran distinto. El clamp a 125 ciclos pertenece al camino FD001 —está en `data.py`, líneas 94 y 97— y el cargador de DS02 no lo aplica: acá el objetivo llega hasta el final de vida real de cada motor.»

## Flashcards

> [!question]- ¿Qué se predice exactamente: el motor o la ventana?
> La ventana. Cada ventana de 50 filas produce una predicción, y su etiqueta es la RUL de la última fila de esa ventana (`src/ds02_rul/features.py:156`).

> [!question]- ¿La RUL está recortada a 125 ciclos en DS02?
> No. El `clip(upper=125)` está solo en `load_fd001_reference` (`src/ds02_rul/data.py:94` y `:97`). El cargador de DS02 no recorta nada.

> [!question]- ¿Por qué no clasificación en tramos de mantenimiento?
> Porque los tramos son una decisión posterior. Un clasificador aprende las fronteras y pierde la distancia a la falla; además, mover un umbral exigiría reentrenar. Los tramos se aplican después, sobre la cota de la banda.

> [!question]- ¿Qué unidad tiene el error?
> Ciclos. RMSE y MAE se leen en ciclos de vuelo, y por eso «equivocarse 3,2 ciclos en promedio» es una frase con sentido para el taller.

## Conexiones

Antes: [[c00-glosario]] · Después: [[c02-ventanas-y-horizonte]] · Decisión: [[s13-capa-de-reglas-y-decision]]
