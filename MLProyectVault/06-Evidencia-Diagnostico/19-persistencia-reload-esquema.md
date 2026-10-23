---
title: Esquema — Persistencia y reload
course: DS02-RUL
block: B6 — Evidencia y diagnóstico
node: N19
type: esquema
status: en-curso
tags:
  - esquema
  - persistencia
---

# Esquema — Persistencia y reload

> Nota de repaso rápido. Teoría completa: [[19-persistencia-reload]]

## La idea en una frase

> Tres piezas, pasaporte con hashes y reload que clava el número.

## Las N piezas

| Pieza | Qué es | Analogía |
|---|---|---|
| .keras + joblib | Grafo y bundle separados | Motor y papeles por separado |
| Manifest + sha256 | Pasaporte auditable | DNI con huellas |
| RELOAD OK | 60.34 vs 58.00 | Arrancar con la copia |

## El flujo (memorizar el orden)

```mermaid
flowchart LR
    G[Guarda] --> V[Verifica]
    V --> R[Recarga]
```

## Sí / No (trampas frecuentes)

- ✅Pickle solo para estimadores sklearn, nunca el grafo.
- ❌ Un Lambda serializado vale (ata a la versión de Python).

## Flashcards #flashcards

- ¿Qué 3 piezas se guardan en models/? :: ensemble.joblib, scaler.joblib, bilstm_ds02.keras.
- ¿Qué verifica assert_ds02_artifact? :: 18 canales y n_op=4.

## Estado

- [ ] En curso
