---
title: Esquema — API Persistencia y reload
course: DS02-RUL
block: B7 — Funciones y API
node: N28
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - persistencia
---

# Esquema — API Persistencia y reload

> Teoría completa: [[28-api-persistencia-y-reload]]

## La idea en una frase

> save_ensemble → .joblib+.keras+manifest. load_ensemble + assert_ds02_artifact → RELOAD OK. Hashes detectan sustituciones.

## Las 9 piezas

| Función | Qué hace |
|---|---|
| sha256_of | SHA-256 de un archivo |
| build_manifest | construye manifest JSON |
| assert_ds02_artifact | verifica integridad del artefacto |
| save_ensemble | guarda .joblib + .keras + manifest |
| _detached_copy | copia con BiLSTM desde disco |
| load_bilstm | carga el .keras |
| load_ensemble | carga el .joblib |
| write_manifest | escribe manifest JSON |
| data_fingerprint | hash de arrays |

## Sí / No

- ✅ assert_ds02_artifact lanza si el artefacto no es DS02.
- ❌ RELOAD OK no es bit-a-bit idéntico al entrenado.

## Flashcards #flashcards

- ¿Qué detecta assert_ds02_artifact? :: Integridad del artefacto.
- ¿Qué significa RELOAD OK? :: recargado == memoria.
- ¿Para qué sirve data_fingerprint? :: Huella de datos.

## Estado

- [ ] En curso
