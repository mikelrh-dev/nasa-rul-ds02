---
title: Guion 30 segundos (B refactor)
course: DS02-RUL
block: B0 - Guion defensa B
node: N0
status: en-curso
tags:
  - guion
  - defensa
  - refactor-B
---

# Guion 30 segundos (B refactor)

> Version B (refactor novato-friendly): src/ds02_rul/viz.py + from ds02_rul.viz import * en 1 linea, glosario WINDOW/STEP/BETA/EMA5/L_inf/OOF/macro y Que entra/sale por celda. Logica identica al bundle A; cifras bundle B: ref RMSE 4.251, R2 0.9482, NASA 2305.1, macro 4.8433, LGBM 7.098, hashes ensemble 7acba335 / bilstm d0c5ed7f.

## Idea central

Predecimos cuantos ciclos le quedan a un motor y decidimos sobre el peor caso.

> Ventana de 50 lecturas hacia RUL. Si dudamos, miramos el limite inferior.

## Que problema resuelve?

El tribunal no quiere 19 ficheros en 30 segundos. Quiere una frase para colgar todo lo demas.

## Las piezas

### La frase

> Predecimos la vida restante por ventanas, quitamos el efecto del vuelo, combinamos dos modelos con beta honesta y decidimos sobre el peor caso de la banda al 90%.

### Las 5 paradas

1. Ventana de 50 hacia un numero.
2. Residualizar: quitar el regimen, quedarse el desgaste.
3. Dos bases: BiLSTM ve la pelicula, LightGBM ve la tabla.
4. Beta OOF: combinar sin mirarse al espejo.
5. Decidir por L_inf: el peor caso defendible.

## El proceso

```mermaid
flowchart LR
    VENT[Ventana 50] --> RES[Residuo]
    RES --> BASES[BiLSTM + LGBM]
    BASES --> BETA[Beta OOF]
    BETA --> LINF[L_inf 90%]
```

## Que no confundir

| Concepto | Que significa | Que no significa |
|---|---|---|
| Guion | Orden para contar | Demostracion tecnica |
| Refactor B | Mismo modelo, celdas pequenas | Otro modelo |

## Conexion con los notebooks

- 01_datos_y_bases.ipynb hacia paradas 1-3 (ahora con from ds02_rul.viz import *).
- 02_decision_ablacion_oof_ensamble.ipynb hacia paradas 4-5.
- 03_evidencia_multisemilla_diagnostico.ipynb hacia 3 semillas + reload.
- Copias literales en codigo-para-LM/ para NotebookLM.

## Resumen

> Ventana, residuo, dos bases, beta honesta, peor caso.

## Autoevaluacion

1. Cuales son las 5 paradas en orden?
2. Que cambio en B respecto a A (viz + glosario)?
3. Que cifra ref/macro citas del bundle B?
