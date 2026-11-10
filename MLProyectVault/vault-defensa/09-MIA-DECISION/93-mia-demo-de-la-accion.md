---
title: MIA · Demo de la acción
course: Reto 1 · SAA+PIA+MIA
block: 09 — MIA decisión
node: D4
indicador: MIA-3
descriptor: 10
spine: false
status: en-curso
tags:
  - mia
  - demo
---

# MIA · Demo de la acción

> [!abstract] En una frase
> Dos minutos, tres pestañas y una decisión que se ve cambiar. La demo no enseña el modelo:
> enseña que la decisión mueve algo.

## El recorrido, en orden

1. **Pestaña flota.** «Aquí está la flota con su estado: verde apto, ámbar inspección, rojo hangar.
   El color no lo pone el RUL: lo pone el límite inferior.»
2. **Pestaña motor.** Se elige la unidad 14 y un ciclo. «Mira el gauge: RUL estimado, y debajo la
   banda; la decisión se lee del límite inferior, no del centro.» Se abre la traza: qué regla
   disparó y con qué porqué.
3. **n8n.** «Cuando la decisión es hangar, el flujo abre la rama y llama a nuestra API; aquí está
   el registro con su `fingerprint`.»
4. **Vuelta a la flota.** «Y el motor aparece en hangar. Eso es la cadena completa: predicción,
   regla, acción, registro.»

## Qué digo si algo falla

- Si la app no carga: enseño la captura y sigo con la traza de reglas explicada en papel.
- Si n8n no responde: enseño `flujo.json` y la vista de ejecuciones capturada.
- Si me preguntan por el dato: «es del artefacto congelado; el test se leyó una vez».

## Por qué se dice así

- MIA-3 no se demuestra con un diagrama: se demuestra con una decisión que produce un efecto
  distinto según el caso. La demo es la prueba.
- Elegir la unidad 14 no es casual: es la que peor error tiene, así que la demo enseña el caso
  difícil, no el bonito.

## Evidencia

- `app/dashboard_ds02.py` (pestaña de flota y de motor).
- `app/ui_modulos/_tab_flota.py` (estado por unidad y cambio de estado por ciclo).
- `app/api.py:262` y `n8n/flujo.json`.

## Pregunta probable

**«¿Puedo cambiar el umbral y ver qué pasa?»**
→ «Puedes mover el control y ver cómo cambia la decisión, pero no la banda: la calibración es
parte del artefacto congelado. Mover el umbral es una política; recalibrar la banda es reentrenar.»

## Lo que NO digo

- No digo «en vivo» si estoy enseñando una captura.
- No toco el umbral sin avisar de que es una simulación de política.

## Di esto en el tribunal

> «Tres pestañas: la flota, el motor con su traza de reglas y el flujo que registra la decisión en
> nuestra API. La cadena se ve entera, no por partes.»

## Flashcards #flashcards

- ¿Qué se enseña en la demo? :: flota, motor con traza de reglas y flujo con registro en la API.
- ¿Por qué la unidad 14? :: porque es la de peor error: enseña el caso difícil.
