---
title: Apertura de 30 segundos
course: Reto 1 · SAA+PIA+MIA
block: 00 — Arranque
node: A2
spine: true
indicador: SAA-1, SAA-2, MIA-1
descriptor: 10
status: en-curso
tags:
  - apertura
  - negocio
  - ia-debil
---

# Apertura de 30 segundos

> [!abstract] En una frase
> Los primeros 30 segundos deciden si el tribunal te escucha como ingeniero o como alumno
> recitando. Se abre con dinero y con una limitación declarada, no con arquitectura.

## El texto, literal

> «Un motor que se degrada sin aviso obliga al operador a elegir entre inmovilizar de más o
> volar con riesgo. Nuestro sistema estima la vida útil restante de cada motor con telemetría
> de vuelo y la convierte en tres decisiones: apto, inspección programada o derivación a
> hangar. Es una **IA débil**: solo sabe hacer esta tarea, con estos datos; no razona fuera de
> DS02. Y esa estrechez es la virtud: es barata, rápida y se puede auditar regla a regla.
> El sistema baja el error de 7,07 a 4,34 ciclos y avisa entre 9 y 23 ciclos antes del umbral
> de hangar, según el motor.»

## Por qué se dice así

- **Empieza por el coste, no por el modelo.** MIA-1 pide «un dato» del problema de negocio;
  el dato es el error frente al margen de actuación (4,34 contra 9–23 ciclos de antelación),
  no un porcentaje inventado.
- **Declara la debilidad antes de que la pregunten.** SAA-1 da 10 solo si comparas con una IA
  fuerte y razonas; decirlo tú convierte una objeción en un punto.
- **Cierra con una cifra verificable.** 7,07 → 4,34 es la cascada del bundle C; 9/23/17 es el
  lead time por motor. Ambas están en [[103-cifras-y-lista-negra]].

## Evidencia

- Cascada y cifras: `models/ds02_manifest.json` → `metrics.reference_row`, `macro_rmse`.
- Lead time por motor: capa de reglas, `src/mia/calibracion_banda.json`; resume en `README.md`.
- IA débil y supervisada: `README.md:29` (compara con AGI y razona por qué no transfiere).
- Problema y quién lo usa: `README.md:21-26` («La necesidad de negocio»).

## Pregunta probable

**«¿Y si el motor falla antes de lo que predices?»**
→ «Por eso no decidimos con el punto: con el límite inferior de la banda. La banda se calibró
para cubrir, y publicamos su cobertura: 100 % en test con 26,41 ciclos de ancho. Es una cota
conservadora y lo declaramos como tal.»

## Lo que NO digo

- No digo «predecimos la vida útil exacta»: es una estimación con error declarado.
- No digo «certifica» ni «garantiza»: el sistema prioriza inspecciones, no firma aeronavegabilidad.
- No empiezo por «usamos un BiLSTM con stacking»: eso es el minuto 6, no el 0.

## Di esto en el tribunal

> «Es IA débil a propósito: solo predice RUL de DS02, y por eso un taller puede auditarla sin
> un doctorado.»

## Flashcards #flashcards

- ¿Con qué se abre la defensa? :: con el coste del fallo sin aviso y el error frente al margen de actuación.
- ¿Qué cifra cierra la apertura? :: la cascada 7,07 → 4,34 y el lead time de 9 a 23 ciclos.
- ¿Por qué se declara la IA débil antes de que la pregunten? :: porque SAA-1 da 10 si comparas con IA fuerte y razonas.
