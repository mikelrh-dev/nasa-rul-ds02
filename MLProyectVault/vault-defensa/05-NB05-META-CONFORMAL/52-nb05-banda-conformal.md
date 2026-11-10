---
title: NB05 · Banda conformal
course: Reto 1 · SAA+PIA+MIA
block: 05 — NB05 meta y banda
node: B5.3
indicador: SAA-9
descriptor: 10
spine: true
status: en-curso
tags:
  - nb05
  - conformal
  - banda
  - adr-008
---

# NB05 · Banda conformal

> [!abstract] En una frase
> La banda no es un intervalo de confianza del modelo: es una **cota** calibrada con residuales
> fuera de fold. Sirve para decidir, no para prometer.

## Qué digo

«Calibro con 17 450 residuales fuera de fold de seis motores de desarrollo, objetivo 90 %. En
test cubre el 100 % con un ancho medio de 26,41 ciclos: cubre de más. Y eso es deliberado: la
calibración usa modelos de fold más débiles que el desplegado. Es una cota conservadora, no un
intervalo de probabilidad.»

## La prueba de que se midió y se rechazó

| Variante | Ancho | Cobertura |
|---|---|---|
| Enviada (OOF, 6 motores) | 26,41 | 100 % |
| Recalibrada en la unidad 16 | 3,35 | 31,4 % (41,4 % por debajo, 27,2 % por arriba) |

Recalibrar en la 16 estrecha la banda a 3,35 y la deja cubriendo un tercio: **peor que no tener
banda**. Se midió y se rechazó; está en `ADR-012`.

## Por qué se dice así

- Es la objeción más dura: «un 100 % de cobertura es inútil». La respuesta es que la banda
  gobierna una decisión asimétrica, donde cubrir de más es el error barato.
- Enseñar el rechazo de la variante estrecha demuestra criterio, no pereza.

## Evidencia

- Decisión: `ADR-008-conformal-lower-bound-triage.md` y `ADR-012-verify-the-band-against-a-frozen-instrument.md`.
- Cobertura por motor: 11 → 26,92 · 14 → 26,03 · 15 → 25,75 de ancho.
- La decisión usa el **límite inferior**, nunca el punto ([[91-mia-seis-reglas]]).

## Pregunta probable

**«Si cubre el 100 %, ¿para qué calibrar?»**
→ «Porque la cobertura se mide, no se asume; y porque el ancho sí informa: 26 ciclos es el precio
de no fallar por abajo. Una banda que cubre el 31 % sería más estrecha y arruinaría la decisión de
hangar, que es la única que no puede fallar.»

## Lo que NO digo

- No digo «intervalo de confianza al 90 %»: es una cota empírica.
- No digo «cubre el 100 %, así que es perfecta»: cubre de más y se declara.
- No uso el punto de la predicción para decidir.

## Di esto en el tribunal

> «La banda se calibró fuera de fold y en test cubre el 100 % con 26 ciclos de ancho: es una cota
> conservadora, y la decisión la gobierna su límite inferior.»

## Flashcards #flashcards

- ¿Con qué se calibra la banda? :: con 17 450 residuales fuera de fold de 6 motores de desarrollo.
- ¿Qué pasa si se recalibra en la 16? :: se estrecha a 3,35 y cubre solo el 31,4 %: se rechazó.
- ¿Qué parte de la banda decide? :: el límite inferior, nunca el punto.
