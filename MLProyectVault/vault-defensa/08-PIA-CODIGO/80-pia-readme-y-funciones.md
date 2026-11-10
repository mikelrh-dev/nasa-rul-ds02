---
title: PIA · README y funciones documentadas
course: Reto 1 · SAA+PIA+MIA
block: 08 — PIA código
node: C1
indicador: PIA-1
descriptor: 10
spine: false
status: en-curso
tags:
  - pia
  - readme
  - rubrica/pia-1
---

# PIA · README y funciones documentadas

> [!abstract] En una frase
> El README no describe el repo: **vende el sistema en el orden en que el corrector lo busca**.
> Y las funciones no llevan comentario: llevan docstring con contrato.

## Los seis apartados obligatorios, y dónde están

| # | Apartado (* obligatorio) | Dónde |
|---|---|---|
| 1 | Título y una frase | `README.md` (H1 + subtítulo) |
| 2 | Captura de la app | `README.md`, arriba |
| 3 | La necesidad de negocio | `README.md:21` |
| 4 | Qué hemos construido (esquema + IA débil) | `README.md:27` |
| 5 | Los datos (tabla + hallazgo + figuras) | `README.md:45` |
| 6 | Resultados (tabla MLflow, elegido, test, captura) | `README.md:106` y `:161` |

Además hay apartados propios —arquitectura, ablación, estabilidad entre semillas, cómo ejecutar,
estructura— que es exactamente lo que pide el 10 («además añade apartados propios»).

## Qué digo

«El README sigue los seis apartados obligatorios en orden y añade los propios: arquitectura,
ablación del reloj, estabilidad entre semillas y guía de ejecución. Las funciones públicas están
documentadas con docstring: el último recuento da cero funciones públicas sin documentar.»

## Evidencia

- `README.md` (apartados y líneas citadas arriba); `src/clase/README.md` para el track de clase.
- Ejemplo de referencia del enunciado: `docClase/README_ejemplo_CV.md`.
- Docstrings: auditoría 2026-11-10, bloque P-03 → 0 funciones públicas sin docstring.

## Pregunta probable

**«¿Por qué el README habla de dos tracks?»**
→ «Porque el proyecto tiene dos ligas: el track de clase con cinco modelos y MLP, y el sistema
desplegado sobre ventanas. El README lo dice desde el principio para que nadie compare 7,72 con
4,34 como si fueran lo mismo.»

## Lo que NO digo

- No digo «el README está completo» sin nombrar los seis apartados.
- No confundo documentar con comentar: lo que se exige es docstring de contrato.

## Di esto en el tribunal

> «Los seis apartados obligatorios están en orden y el README añade arquitectura, ablación y
> estabilidad; las funciones públicas van con docstring, no con comentarios sueltos.»

## Flashcards #flashcards

- ¿Cuáles son los seis apartados obligatorios? :: título y frase, captura, necesidad de negocio, qué hemos construido, datos y resultados.
- ¿Qué añade el README para el 10? :: apartados propios: arquitectura, ablación, estabilidad y ejecución.
