---
title: NB05 · Multisemilla
course: Reto 1 · SAA+PIA+MIA
block: 05 — NB05 meta y banda
node: B5.2
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - nb05
  - semillas
  - ruido
---

# NB05 · Multisemilla

> [!abstract] En una frase
> Un 4,338 es una corrida, no una propiedad. La pregunta correcta no es «¿cuánto da?» sino
> «¿cuánto se mueve?».

## Qué digo

«Corrí tres semillas y publiqué media y desviación. La fila oficial es la semilla 42, que es la
que está en disco: 4,338. Las medias de tres semillas —4,330 en NB05 y 4,322 en NB06— y el CSV
vigente `bundle_c_multiseed.csv` (4,324 ± 0,107 con 42/7/123) miden estabilidad, no el artefacto.
Si difieren en centésimas es ruido de TensorFlow en CPU, no contradicción.»

## Por qué se dice así

- La rúbrica no lo pide; el tribunal pregunta «¿y si cambias la semilla?». Tener la respuesta con
  desviación es lo que separa un número de una medición.
- Declarar el ruido antes evita que una cifra distinta parezca un error.

## Evidencia

- `resultados/bundle_c_multiseed.csv` (7 = 4,211; 123 = 4,424) y `resultados/comparativa_c_multisemilla.csv`
  (**obsoleto**, no citar su 4,368).
- Media del CSV vigente con la 42 del manifiesto: 4,324 ± 0,107 · NASA 2341,0 ± 54,1.
- Medias impresas en NB05 (4,330 ± 0,053) y NB06 (4,322 ± 0,064): histórico, no regenerable.

## Pregunta probable

**«¿Entonces tu resultado es 4,33 o 4,338?»**
→ «El artefacto en disco es la semilla 42: 4,338. 4,324 es la media de tres semillas y mide
estabilidad. Cuando cito una cifra, digo cuál de las dos es.»

## Lo que NO digo

- No cito 4,368: es una media obsoleta de un CSV reemplazado.
- No presento la media como si fuera la fila del manifiesto.
- No digo que el ruido sea «un problema del modelo»: es de la ejecución en CPU.

## Di esto en el tribunal

> «La fila oficial es la semilla 42, 4,338; la media de tres semillas es 4,324 ± 0,107 y mide
> estabilidad, no el artefacto.»

## Flashcards #flashcards

- ¿Qué cifra es el artefacto y cuál la media? :: 4,338 es la semilla 42 en disco; 4,324 ± 0,107 la media de tres.
- ¿Qué cifra está prohibida? :: 4,368, media obsoleta de un CSV reemplazado.
