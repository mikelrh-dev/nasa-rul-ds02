---
title: API — Datos e ingestión
course: DS02-RUL
block: B7 — Funciones y API
node: N21
status: en-curso
tags:
  - api
  - datos
  - ingestión
---

# API — Datos e ingestión

## Idea central

Entrada del pipeline: localizar el HDF5, cargarlo con stride 100, y preparar la referencia FD001. Cuatro funciones en `src/ds02_rul/data.py`.

> Sin esto no hay nada: todo lo demás consume el dict que devuelve `load_ds02`.

## ¿Qué problema resuelve?

El HDF5 N-CMAPSS DS02 (`archive/CCMaps/N-CMAPSS_DS02-006.h5`) pesa mucho y viene con unidades de desarrollo (2,5,10,16,18,20) y test (11,14,15). Hay que elegir cuáles se usan y a qué resolución.

## Las piezas del modelo mental

### `resolve_ds02(path=None) -> str`
- **Firma:** `resolve_ds02(path: str | None = None) -> str`
- **Qué hace:** devuelve la ruta al HDF5 DS02. Si `path` es None, busca en rutas por defecto (`archive/CCMaps/...`).
- **Retorno:** ruta absoluta al `.h5`.
- **Llamado desde:** notebooks 01/02/03, celda 4/12 (implícito vía `load_ds02()`).
- **Gotcha:** si el archivo no está, lanza; no descarga nada (offline-first).

### `load_ds02(path=None, stride=100) -> dict`
- **Firma:** `load_ds02(path: str | None = None, stride: int = 100) -> dict`
- **Qué hace:** carga el HDF5 y downsamplea 1 de cada `stride` filas por motor. Devuelve dict con `W` (operativos), `Xs` (sensores), `units`, `cycles`, `y` (RUL), `meta`.
- **Retorno:** dict con arrays por motor y metadata. Dev: 52 635 filas (6 motores), test 12 538 (3 motores).
- **Llamado desde:** NB01 celda 9, NB02 celda 4, NB03 celda 4.
- **Gotcha:** `stride=100` es el que hace que 50 filas ≈ 0.4 ciclos, no 50 ciclos reales.

### `load_fd001_reference(root="archive/CMaps") -> dict`
- **Firma:** `load_fd001_reference(root: str = "archive/CMaps") -> dict`
- **Qué hace:** carga el dataset C-MAPSS FD001 clásico (referencia histórica). **No se usa en la UI** (prohibido referenciar FD001 en la app).
- **Retorno:** dict análogo al de DS02.
- **Llamado desde:** solo notebooks/experimentos, nunca `dashboard_ds02.py`.
- **Gotcha:** solo para comparación académica; no mezclar con DS02 en defensa.

### `data_fingerprint(arrays) -> str`
- **Firma:** `data_fingerprint(arrays: dict) -> str`
- **Qué hace:** hash SHA-256 del contenido de los arrays (para detectar si los datos cambiaron).
- **Retorno:** hexdigest.
- **Llamado desde:** `persistence.build_manifest` (N28).
- **Gotcha:** fingerprint de datos, no del modelo.

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    HDF5[HDF5 DS02] --> RESOLVE[resolve_ds02]
    RESOLVE --> LOAD[load_ds02 stride 100]
    LOAD --> RAW[dict W/Xs/units/cycles/y]
    RAW --> PREP[fit_preprocessing]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| stride 100 | 1 de cada 100 filas originales | 100 ciclos de vuelo |
| FD001 | Dataset clásico, solo referencia | Parte del modelo DS02 |
| fingerprint | Huella de datos | Huella del modelo |

## Conexión con los notebooks del repositorio

- `notebooks/ds02_ensemble/01_datos_y_bases.ipynb` celdas 9, 11.
- `notebooks/ds02_ensemble/02_...` celda 4.
- `notebooks/ds02_ensemble/03_...` celda 4.
- `src/ds02_rul/data.py:35,49,81` + `persistence.py:206`.

## Resumen para recordar

> `load_ds02(stride=100)` → dict con W/Xs/units/cycles/y. Ese dict alimenta todo.

## Autoevaluación

1. ¿Qué devuelve `load_ds02` y con qué stride?
2. ¿Por qué no se usa FD001 en la UI?
3. ¿Qué es `data_fingerprint`?

## Estado

- [ ] En curso
