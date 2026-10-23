---
title: Persistencia y reload verificado
course: DS02-RUL
block: B6 — Evidencia y diagnóstico
node: N19
status: en-curso
tags:
  - persistencia
  - artefactos
  - manifest
---

# Persistencia y reload verificado

## Idea central

El modelo se guarda en 3 piezas nativas con manifiesto y hashes, y se recarga desde disco demostrando que predice igual: RUL 60.34 vs 58.00 real.

> Guardar no es serializar: es empaquetar con pasaporte y reabrirlo delante del tribunal.

## ¿Qué problema resuelve?

Un `pickle` con un `Lambda` ataba el artefacto a una versión de Python (el fallo legacy). El formato actual carga en cualquier intérprete y el manifiesto impide que un bundle FD001 sustituya a uno DS02 sin que nadie lo note.

## Las piezas del modelo mental

### Tres piezas

`bilstm_ds02.keras` (grafo nativo, `LastStepPooling` registrada), `ensemble.joblib` (bundle sin el grafo: solo la ruta), `scaler.joblib` + `ds02_manifest.json` (procedencia, formas, sha256).

### `assert_ds02_artifact`

Abortar si el scaler no tiene 18 canales o `n_op != 4`: el cargador FD001 es ruta separada y nunca toca esta ubicación.

### `[RELOAD OK]`

`load_ensemble` re-adjunta el grafo y predice 60.34 vs 58.00 (`recargado == en memoria: True`): el artefacto en disco es el modelo, no un souvenir.

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    MEM[En memoria] --> SAVE[.keras + joblib + manifest]
    SAVE --> CHECK[assert 18/4 + sha256]
    CHECK --> LOAD[load_ensemble]
    LOAD --> OK[60.34 vs 58.00]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| Nativo .keras | Grafo por valor, portable | Pickle del modelo |
| Manifest | Pasaporte auditable | Documentación |

## Conexión con el aprendizaje

Es el cierre del protocolo honesto: lo que se evaluó es exactamente lo que se guarda.

## Conexión con los notebooks del repositorio

- `03_evidencia_multisemilla_diagnostico.ipynb`, celdas 51–52 (manifiesto + reload).
- `src/ds02_rul/persistence.py:save_ensemble/load_ensemble/build_manifest`.

## Resumen para recordar

> Tres piezas, pasaporte con hashes y reload que clava el número.

## Autoevaluación

1. ¿Por qué el grafo no viaja dentro del joblib?
2. ¿Qué impide que un bundle FD001 reemplace al DS02?
3. ¿Qué demuestra exactamente el `[RELOAD OK]`?
