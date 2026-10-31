---
title: Datos prepro y ventanas (B)
course: DS02-RUL
block: B0 - Guion defensa B
node: N1
status: en-curso
tags:
  - datos
  - prepro
  - ventanas
---

# Datos prepro y ventanas (B)

> Version B (refactor novato-friendly): src/ds02_rul/viz.py + from ds02_rul.viz import * en 1 linea, glosario WINDOW/STEP/BETA/EMA5/L_inf/OOF/macro y Que entra/sale por celda. Logica identica al bundle A; cifras bundle B: ref RMSE 4.251, R2 0.9482, NASA 2305.1, macro 4.8433, LGBM 7.098, hashes ensemble 7acba335 / bilstm d0c5ed7f.

## Idea central

El suelo honesto no cambio: reparto por motor, prepro solo-fit en motores de ajuste, ventanas de 50.

> Si el prepro ve el motor de test, el resto es teatro.

## Que problema resuelve?

Evitar fuga: el scaler y los ridges solo se ajustan en motores de ajuste, nunca en test (unidades 11/14/15).

## Las piezas

### Reparto por motor

Dev 52635 filas (6 motores), test 12538 (11/14/15), ajuste 44982. El motor 16 valida el early-stop del BiLSTM.

### Prepro solo-fit (features.py)

Scaler de 18 canales + 14 ridges por sensor. En B el codigo es el mismo; la celda del notebook ahora trae glosario + Que entra/sale.

### Ventanas (window 50, step 3 train / 2 test)

Dev (17450,50,19), test (6196,50,19). Etiqueta = ultimo RUL de la ventana.

## El proceso

```mermaid
flowchart LR
    RAW[load_ds02] --> PREP[fit_preprocessing solo-fit]
    PREP --> WIN[build_windows 50]
    WIN --> BASES[LGBM + BiLSTM]
```

## Que no confundir

| Concepto | Que significa | Que no significa |
|---|---|---|
| Solo-fit | Ajustar solo en ajuste | Ajustar en todo y evaluar |
| Step 3/2 | Densidad train/test | Solape de fuga |

## Conexion notebooks

- 01_datos_y_bases.ipynb celdas 9/11/13 + codigo-para-LM/nb01_datos_y_bases.codigo.md.
- src-data.py y src-features.py literales en codigo-para-LM/.

## Resumen

> Reparto por motor + solo-fit + ventana 50.

## Autoevaluacion

1. Por que solo-fit?
2. Que forma tiene dev tras ventanas?
3. Que hace viz.py aqui? (solo dibuja, no toca prepro).
