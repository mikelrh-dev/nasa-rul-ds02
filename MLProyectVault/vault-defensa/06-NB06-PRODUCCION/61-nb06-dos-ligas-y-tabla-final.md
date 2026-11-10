---
title: NB06 · Dos ligas y tabla final
course: Reto 1 · SAA+PIA+MIA
block: 06 — NB06 producción
node: B6.2
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - nb06
  - grano
  - tabla-final
---

# NB06 · Dos ligas y tabla final

> [!abstract] En una frase
> Fila y ventana no compiten: miden unidades distintas. Mezclarlas en un ranking es el error más
> fácil de cometer y el más difícil de defender.

## Qué digo

«La tabla final tiene dos campeones porque hay dos granos. En grano fila, cada muestra es una
fila con 22 features: gana el MLP E2 con 7,72 de test. En grano ventana, cada muestra son 50
filas y 93 features: gana el híbrido C con 4,34. No comparo 7,72 con 4,34 porque no miden lo
mismo; lo que sí es común es el criterio: validación, desempate al más simple, test una vez.»

## La tabla

| Grano | Campeón | Test | Nota |
|---|---|---|---|
| Fila (22 features) | MLP E2 | 7,721 | El mejor del track de clase |
| Ventana (50×19) | Híbrido C + EMA5 | 4,338 | El desplegado |

## Por qué se dice así

- La rúbrica SAA-9 pide «tabla con métricas y tiempo, elige la métrica según el negocio». La
  tabla final es esa tabla, pero además explica por qué hay dos filas ganadoras.
- Anticipa la pregunta trampa: «¿por qué dos campeones?».

## Evidencia

- `resultados/tabla_final_clase.csv` (escritor `src/clase/tabla_final.py:22`, `main` en `:68`).
- NB06 c52 reconstruye la tabla con `construir_tabla` y exige igualdad con el CSV.

## Pregunta probable

**«Entonces, ¿cuál usas?»**
→ «El de ventana, porque el sistema vive sobre secuencias y porque su error es menor con el mismo
protocolo de test. El de fila queda como referencia y como prueba de que el preprocesado y el
split están bien hechos.»

## Lo que NO digo

- No pongo las dos cifras en la misma columna de un ranking.
- No digo que 4,34 sea «mejor» que 7,72 sin decir que cambia el grano.

## Di esto en el tribunal

> «Dos granos, dos campeones: E2 en fila y el híbrido en ventana; no se comparan, se eligen con el
> mismo criterio.»

## Flashcards #flashcards

- ¿Cuál es el campeón de cada grano? :: E2 (7,721) en fila y el híbrido C (4,338) en ventana.
- ¿Por qué no se comparan? :: porque cada grano mide una unidad de muestra distinta.
