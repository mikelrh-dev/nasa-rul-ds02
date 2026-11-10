---
title: Guion de 3 minutos
course: Reto 1 · SAA+PIA+MIA
block: 00 — Arranque
node: A1.1
spine: false
status: en-curso
tags:
  - guion
  - recorte
---

# Guion de 3 minutos

> [!abstract] En una frase
> Si el tribunal recorta a 3 minutos, se conserva la **cadena completa**: problema → dato →
> cascada → decisión → acción. Todo lo demás es detalle.

## Los cuatro tramos

**0:00–0:40 · El problema y el dato.** «Un motor que se degrada sin aviso obliga a elegir entre
inmovilizar de más o volar con riesgo. Tenemos telemetría por ciclo de 9 unidades DS02 y
sabemos su RUL real: es un problema supervisado de regresión.»

**0:40–1:30 · La cascada, en una línea.** «LightGBM cuantílico da 7,07; el BiLSTM 5,65; el
suavizado causal 5,62; el meta que aprende a mezclarlos, 4,34. Ninguna etapa sobra: cada una
baja el error de la anterior.»

**1:30–2:30 · La decisión.** «No decidimos con la predicción puntual: con el límite inferior
de una banda al 90 %. Seis reglas con prioridad convierten eso en APTO, INSPECCIÓN o HANGAR, y
una regla de seguridad manda sobre todas: si el dato es imposible, no se decide.»

**2:30–3:00 · La acción y el límite.** «La rama HANGAR llama a nuestra propia API y registra
la decisión con idempotencia. Lo que no hacemos: certificar aeronavegabilidad ni prometer
anticipación fuera de esta flota.»

## Qué se sacrifica

- Los cinco modelos clásicos y el MLP: se mencionan como «el camino que descartó los modelos
  simples» sin tabla.
- La ablación de `cyc_norm`: una frase («el reloj ayuda a la secuencia, no al resumen»).
- MLflow y la estructura: se dicen de pasada en la frase de código.

## Di esto en el tribunal

> «En tres minutos: el problema cuesta dinero, la cascada baja el error de 7,07 a 4,34, la
> decisión la gobierna el límite inferior y la acción la ejecuta nuestra API.»

## Flashcards #flashcards

- ¿Qué cuatro cosas sobreviven en el recorte? :: problema, cascada, decisión, acción.
- ¿Qué se puede perder sin romper el relato? :: la tabla de cinco modelos, la ablación y MLflow.
