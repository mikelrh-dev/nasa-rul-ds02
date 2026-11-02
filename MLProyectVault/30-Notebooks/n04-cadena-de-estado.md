---
tipo: notebook
status: sin-estudiar
tags:
  - cadena-estado
  - artefactos
  - nb01-nb03
---

# Cadena de estado — qué guarda cada cuaderno

> [!abstract] En una frase
> Tres cuadernos encadenados por artefactos: NB01 produce, NB02 combina, NB03 congela.

## Contrato

| Entra | Sale |
|---|---|
| HDF5 y semillas al inicio de NB01 | Bundle en `models/` al final de NB03 |
| Nada suelto entre cuadernos | Todo pasa por `artifacts/` verificado |

## Cómo está implementado

La cadena se prueba en `notebooks/ds02_ensemble/EVALUACION_EJECUCION.md` con tres marcas.

| Eslabón | Marca textual | Qué verifica |
|---|---|---|
| NB01 → NB02 | `[NB1 OK]` en `artifacts/` | Dev `(17450, 50, 19)`, test `(6196, 50, 19)` y BiLSTM guardados |
| NB01 → NB02 | `[LOAD NB1 OK]` en NB02 celda 3 | Dev y test intactos más BiLSTM recargado |
| NB02 → NB03 | `[NB2 OK] beta = 1.0` | `p_ens (6196,)` y beta listos |
| NB02 → NB03 | `[LOAD NB2 OK]` en NB03 celda 3 | Beta y predicciones intactas |
| NB03 → disco | Guarda en `models/` | `ensemble.joblib`, `.keras` y manifiesto |
| NB03 → servicio | `[RELOAD OK]` | `recargado == en memoria: True` |

NB01 guarda secuencias, tabulares, prep y bases. NB02 añade OOF, beta, meta y banda. NB03 añade multisemilla y persistencia final. Ningún cuaderno recalcula lo anterior: lo recarga y verifica.

```mermaid
flowchart LR
    A[NB01 datos-bases] -->|NB1 OK| B[NB02 decision-ensamble]
    B -->|NB2 OK beta 1.0| C[NB03 evidencia]
    C -->|RELOAD OK| D[models + app]
```
Fuente: [[visuals/n04-cadena-estado.mmd]]

## La decisión que hay detrás

Cortar en tres cuadernos en vez de uno gigante facilita defender por partes: datos y bases, decisión y ensamble, evidencia y persistencia. El costo es la cadena: si un eslabón cambia el formato, los demás rompen.

Se rechazó el cuaderno único: 58 celdas seguidas no se ensayan ni se depuran. Tres cuadernos con marcas de carga sí.

## Qué medimos

La cadena no tiene métrica: tiene prueba de identidad. `[RELOAD OK] 60.40 vs 58.00` demuestra que servir es recargar ([[s12-persistencia-y-contrato]]).

Las cifras que viajan por la cadena son las de [[e00-cifras-autoritativas]]: la fila de disco 4.251 es la que sale de NB03 celda 15.

## El límite

> [!warning] Lo que la cadena no blinda
> Si reejecutas NB01 con otra semilla y no reejecutas NB02 y NB03, la cadena miente: beta y banda pertenecerán a otro mundo. La regla es todo o nada: se ejecutan en orden 01 → 02 → 03 o no se ejecutan.

## Di esto en el tribunal

> [!quote]
> «Los cuadernos se encadenan por artefactos con marcas de carga: NB01 deja NB1 OK, NB02 recarga y deja beta 1.0, NB03 recarga y deja el bundle en models con reload idéntico.»

## Flashcards

> [!question]- ¿Qué marca deja NB01?
> `[NB1 OK]` en `artifacts/` con dev, test y BiLSTM.

> [!question]- ¿Qué verifica LOAD NB1 OK?
> Que NB02 recargó dev, test y BiLSTM intactos.

> [!question]- ¿Qué deja NB02 para NB03?
> `[NB2 OK]` con beta 1.0 y `p_ens (6196,)`.

> [!question]- ¿Qué prueba RELOAD OK?
> Que el bundle recargado predice igual que en memoria.

> [!question]- ¿Qué afirma esta nota en una frase?
> Tres cuadernos encadenados por artefactos: NB01 produce, NB02 combina, NB03 congela.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Los cuadernos se encadenan por artefactos con marcas de carga: NB01 deja NB1 OK, NB02 recarga y deja beta 1.0, NB03 recarga y deja el bundle en models con reload idéntico.»

> [!question]- ¿Qué archivo respalda esta nota?
`models/`

> [!question]- ¿Qué archivo respalda esta nota?
`artifacts/`

