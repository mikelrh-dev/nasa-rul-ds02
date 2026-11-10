---
title: NB06 · Macro-RMSE y motor 14
course: Reto 1 · SAA+PIA+MIA
block: 06 — NB06 producción
node: B6.3
indicador: MIA-1
descriptor: 10
spine: false
status: en-curso
tags:
  - nb06
  - macro
  - motor-14
---

# NB06 · Macro-RMSE y motor 14

> [!abstract] En una frase
> El 4,34 es el promedio de la flota; el 5,02 macro es lo que sufre un motor elegido al azar. La
> diferencia es el dato de negocio que abre la defensa.

## La tabla por motor

| Motor | RMSE | Ventanas |
|---|---|---|
| 11 | 3,633 | 3 293 |
| 14 | **8,576** | **760** |
| 15 | 2,837 | 2 143 |
| **Macro (1/3 cada uno)** | **5,0153** | 6 196 |

## Qué digo

«El promedio pondera por ventanas y por eso es amable: el motor 14 tiene el peor error y la menor
cantidad de ventanas —760, el 12 % de las muestras— pero concentra el 47,9 % del error cuadrático.
Si el operador elige un motor al azar, lo que sufre es 5,02, no 4,34. Publico las dos cifras
porque la segunda es la que decide si el sistema sirve para gestión de flota.»

## Por qué se dice así

- MIA-1 pide un dato del problema de negocio y qué mejora supondría. Este es el dato: hay motores
  donde el error se dispara, y eso es exactamente donde el sistema tiene que ser conservador.
- Es la respuesta natural a «¿y por qué no presumes de 4,34?».

## Evidencia

- `models/ds02_manifest.json` → `macro_rmse` y por motor.
- `resultados/bundle_c_por_motor.csv`.
- 760 ventanas de la unidad 14 frente a 3 293 del 11.

## Pregunta probable

**«¿Por qué el 14 falla tanto?»**
→ «Porque tiene menos ventanas y su degradación es más abrupta: con menos ejemplos, el modelo ve
menos transiciones. Es un límite de datos, no del algoritmo; se declara y se compensa con la
banda conservadora.»

## Lo que NO digo

- No digo «el modelo es igual de bueno en todos los motores».
- No oculto el 8,58 detrás del 4,34.

## Di esto en el tribunal

> «El 4,34 es el promedio; el 5,02 macro es lo que sufre un motor al azar, y el 14 concentra el
> 48 % del error porque tiene menos ventanas.»

## Flashcards #flashcards

- ¿Qué mide el macro-RMSE que no mide el global? :: el error de un motor elegido al azar, sin ponderar por ventanas.
- ¿Qué motor concentra el error y por qué? :: el 14, con 760 ventanas y degradación abrupta: 47,9 % del error cuadrático.
