---
tipo: sistema
status: sin-estudiar
tags:
  - datos
  - ds02
  - reparto
---

# Datos DS02 y reparto — HDF5 por motor

> [!abstract] En una frase
> Seis motores desarrollan, tres confirman, y cada fila trae régimen y sensores separados desde el origen.

## Contrato

| Entra | Sale |
|---|---|
| HDF5 DS02 con W, Xs, ciclos y unidades | Diccionario `raw` con dev y test ya separados por motor |
| `stride=100` en carga | 52 635 filas dev y 12 538 filas test |

## Cómo está implementado

La ingesta vive en `src/ds02_rul/data.py:49` y la resolución de ruta en `src/ds02_rul/data.py:35`.

| Pieza | Qué es | Dónde |
|---|---|---|
| W | 4 canales operativos: altitud, Mach, TRA, T2 | `src/ds02_rul/data.py:49` |
| Xs | 14 sensores físicos del motor | `src/ds02_rul/data.py:49` |
| Ciclos y unidades | Identidad temporal y espacial de cada fila | `src/ds02_rul/data.py:49` |
| Stride 100 | Se conserva una fila de cada 100 al cargar | `src/ds02_rul/pipeline.py:88` |
| FD001 | Referencia aparte, nunca mezclada con DS02 | `src/ds02_rul/data.py:81` |

El reparto por motor es el de [[s01-protocolo-honesto]]: ajuste `[2, 5, 10, 18, 20]`, holdout `[16]`, test `[11, 14, 15]`. No hay partición aleatoria: el corte respeta la unidad completa porque las ventanas se solapan un 94 % ([[c02-ventanas-y-horizonte]]).

Conteo vigente ([[e00-cifras-autoritativas]]): dev 17 450 ventanas y 52 635 filas; test 6 196 ventanas y 12 538 filas; ajuste 44 982 filas y 14 915 ventanas; holdout 7 653 filas y 2 535 ventanas.

La ventana de 50 filas no son 50 ciclos: con stride 100 cubre 0,44 ciclos de vuelo. Ese es el horizonte real ([[c02-ventanas-y-horizonte]]).

## La decisión que hay detrás

ADR-002 y ADR-003 fijan que W y Xs viajan separados hasta la residualización. Mezclarlos antes impide quitar el régimen sin contaminar el desgaste.

Se rechazó cargar sin stride: el HDF5 completo no cabe en el flujo de cuadernos y no añade señal, solo filas casi idénticas.

## Qué medimos

Sin medición propia: esta etapa no puntúa, solo entrega filas limpias. Los conteos que importan están en [[e00-cifras-autoritativas]] y el mecanismo del solape en [[c02-ventanas-y-horizonte]].

El scaler posterior ve 18 canales (4 W + 14 Xs) y el BiLSTM recibe `(None, 50, 19)` con el canal de ciclo añadido (`models/ds02_manifest.json`).

## El límite

> [!warning] Lo que esta etapa no garantiza
> El holdout es una sola unidad con RUL máxima de 62 ciclos. Cualquier estadística estimada solo ahí hereda ese techo y no representa colas largas. El test sí cubre el rango completo.

## Di esto en el tribunal

> [!quote]
> «DS02 viene en HDF5 con 4 canales de régimen y 14 sensores. Lo cargamos con stride 100 y lo partimos por motor: cinco ajustan, la 16 valida y 11, 14 y 15 confirman. Una ventana de 50 filas cubre 0,44 ciclos reales, no 50.»

## Flashcards

> [!question]- ¿Qué trae cada fila del HDF5?
> W (4 canales operativos), Xs (14 sensores), ciclo y unidad.

> [!question]- ¿Qué unidades van a cada conjunto?
> Ajuste 2, 5, 10, 18 y 20; holdout 16; test 11, 14 y 15.

> [!question]- ¿Qué hace el stride 100?
> Conserva una fila de cada 100 al cargar para hacer el problema tratable.

> [!question]- ¿Cuánto cubre una ventana de 50 filas?
> 0,44 ciclos de vuelo, no 50 ciclos.

> [!question]- ¿Qué afirma esta nota en una frase?
> Seis motores desarrollan, tres confirman, y cada fila trae régimen y sensores separados desde el origen.

> [!question]- ¿Cómo la contarías en el tribunal?
> «DS02 viene en HDF5 con 4 canales de régimen y 14 sensores. Lo cargamos con stride 100 y lo partimos por motor: cinco ajustan, la 16 valida y 11, 14 y 15 confirman. Una ventana de 50 filas cubre 0,44 ciclos reales, no 50.»

## Conexiones

Antes: [[s01-protocolo-honesto]] · Después: [[s03-preproceso-sin-fuga]] · Mecanismo: [[c02-ventanas-y-horizonte]]
