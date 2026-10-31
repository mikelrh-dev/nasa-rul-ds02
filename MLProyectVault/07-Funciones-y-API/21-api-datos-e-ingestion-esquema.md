---
title: Esquema — API Datos e ingestión
course: DS02-RUL
block: B7 — Funciones y API
node: N21
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - datos
---

# Esquema — API Datos e ingestión

> Teoría completa: [[21-api-datos-e-ingestion]]

## La idea en una frase

> `load_ds02(stride=100)` → dict con W/Xs/units/cycles/y. Ese dict alimenta todo.

## Las 4 piezas

| Función | Qué hace | Devuelve |
|---|---|---|
| resolve_ds02 | localiza el HDF5 | ruta str |
| load_ds02 | carga + stride 100 | dict |
| load_fd001_reference | carga FD001 (solo referencia) | dict |
| data_fingerprint | hash de los arrays | hexdigest |

## Sí / No

- ✅ stride=100 ⇒ 50 filas ≈ 0.4 ciclos.
- ❌ FD001 no se usa en la UI (solo referencia académica).

## Flashcards #flashcards

- ¿Qué devuelve load_ds02? :: dict con W/Xs/units/cycles/y.
- ¿Con qué stride? :: 100.
- ¿FD001 se usa en la app? :: No.

## Estado

- [ ] En curso
