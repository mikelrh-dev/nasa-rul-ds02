---
title: Persistencia y notebooks (B)
course: DS02-RUL
block: B0 - Guion defensa B
node: N5
status: en-curso
tags:
  - persistencia
  - notebooks
---

# Persistencia y notebooks (B)

> Version B (refactor novato-friendly): src/ds02_rul/viz.py + from ds02_rul.viz import * en 1 linea, glosario WINDOW/STEP/BETA/EMA5/L_inf/OOF/macro y Que entra/sale por celda. Logica identica al bundle A; cifras bundle B: ref RMSE 4.251, R2 0.9482, NASA 2305.1, macro 4.8433, LGBM 7.098, hashes ensemble 7acba335 / bilstm d0c5ed7f.

## Idea central

El contrato que nos obsesiona: guardar bundle + scaler + keras nativo y recargar bit-identico en proceso limpio.

## Las piezas

### Bundle (persistence.py)

save_ensemble escribe ensemble.joblib + scaler.joblib + bilstm_ds02.keras + manifiesto. El grafo va por ruta, nunca picklado. load_ensemble reatacha el grafo (registra LastStepPooling antes).

### RELOAD OK

B consigue RELOAD OK recargado==memoria True (proceso limpio). Misma logica que A, nuevos hashes: ensemble 7acba335, bilstm d0c5ed7f.

### Notebooks pequenos

NB01 (27 celdas) hacia NB02 (18 codigos) hacia NB03 (multisemilla + persistencia). Cada celda: glosario + Que entra/sale + 1 idea. viz.py sustituye la celda gigante de 12 def.

## El proceso

```mermaid
flowchart LR
    NB01[NB01 suelo] --> NB02[NB02 decision]
    NB02 --> NB03[NB03 evidencia]
    NB03 --> SAVE[save_ensemble]
    SAVE --> RELOAD[RELOAD OK]
```

## Que no confundir

| Concepto | Que significa | Que no significa |
|---|---|---|
| Bundle | 3 ficheros + manifiesto | Un pickle con todo |
| RELOAD OK | Memoria == recargado | Metrica alta |

## Conexion notebooks

- NB03 final + src-persistence/pooling/inference.codigo.md + src-viz.codigo.md.

## Resumen

> Guardar 3 piezas + recargar identico + notebooks pequenos.

## Autoevaluacion

1. Por que el grafo no se pickla?
2. Que registra load_bilstm antes de cargar?
3. Que pone viz.py en vez de la celda gigante?
