---
title: Lo que descartamos
course: Reto 1 · SAA+PIA+MIA
block: 10 — Decisiones
node: E3
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - decisiones
  - descartes
---

# Lo que descartamos

> [!abstract] En una frase
> Los descartes son la prueba de que el proyecto se pensó: cualquiera puede añadir; defender es
> saber qué no.

## La mesa de descartes

| Descartado | Por qué | Dónde está escrito |
|---|---|---|
| MCAR 3 % en 14 sensores | Rompe demasiadas ventanas del BiLSTM y el relato es débil | `openspec/changes/…/design.md` |
| `SimpleImputer(mean)` global | Rompe la causalidad y miente en crucero | `src/clase/dataset_clase.py` |
| `dropna` | Sesga el crucero, que es donde está el dato bueno | nota NB01 |
| Blend lineal de las dos ramas | El promedio arrastra el error de la rama mala | `ADR-001` |
| Objetivo mediana | Mejor en dev, peor en test | `ADR-007` |
| Recalibrar la banda en la 16 | 3,35 de ancho y 31 % de cobertura | `ADR-012` |
| Simulador de flota desacoplado | Sin pub/sub; el polling añade latencia | `ADR-010` |
| Unificar los imports `ds02_rul` / `src.*` | Rompe el pickle de los artefactos | `docs/defensa/mapa-nb01-nb07.md` |
| Mantener el bundle B vivo | Dos artefactos, dos verdades | `ADR-011` |

## Qué digo

«Descartamos el nulo aleatorio porque rompía las ventanas; el promedio fijo porque arrastra el
error; la mediana porque ganaba en desarrollo y perdía en test; y recalibrar la banda en test
porque la dejaba cubriendo un tercio. Cada descarte está escrito con su razón, no con un
"no funcionó".»

## Por qué se dice así

- Enseñar descartes demuestra criterio y evita la pregunta «¿y no probasteis X?»: la respuesta ya
  está dada.
- El descarte de unificar imports es el más técnico y el más valioso: enseña que se entiende el
  contrato del artefacto.

## Pregunta probable

**«¿Por qué no probasteis un transformer?»**
→ «Porque el cuello no era la capacidad del modelo: era la varianza entre motores y la falta de
ventanas en el 14. Un modelo más grande con 760 ventanas de test no arregla eso; lo empeora.»

## Lo que NO digo

- No digo «no dio tiempo»: un descarte por tiempo no es un descarte técnico.
- No invento descartes que no están escritos.

## Di esto en el tribunal

> «Cada descarte está escrito con su razón: nulo aleatorio, promedio fijo, mediana, recalibrar en
> test y unificar imports. Saber qué no hacer es parte del resultado.»

## Flashcards #flashcards

- ¿Qué tres tratamientos de nulos se descartaron? :: MCAR 3 %, imputación por media global y `dropna`.
- ¿Por qué no se recalibra la banda en la 16? :: porque colapsa a 3,35 de ancho con 31 % de cobertura.
- ¿Por qué no se unifican los imports? :: porque rompe el pickle de los artefactos guardados.
