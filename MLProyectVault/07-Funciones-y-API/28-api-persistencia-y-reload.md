---
title: API — Persistencia y reload
course: DS02-RUL
block: B7 — Funciones y API
node: N28
status: en-curso
tags:
  - api
  - persistencia
  - reload
  - manifest
---

# API — Persistencia y reload

## Idea central

Guardar/cargar el artefacto congelado (`.joblib` + `.keras` + manifest JSON) y verificar que lo que hay en disco coincide con lo que se cargó. `src/ds02_rul/persistence.py`.

> Si el artefacto se sustituye sin reconstruir la caché, la UI avisa (sello roto).

## ¿Qué problema resuelve?

Un modelo entrenado no sirve si no se puede guardar, cargar y verificar. El manifest registra hashes y versiones para que la app detecte sustituciones fraudulentas/accidentales.

## Las piezas del modelo mental

### `sha256_of(path) -> str` (`persistence.py:29`)
- **Firma:** `sha256_of(path: str) -> str`.
- **Qué hace:** SHA-256 de un archivo (bloques de 1 MiB).
- **Retorno:** hexdigest.
- **Llamado desde:** `build_manifest`, `assert_ds02_artifact`, UI (crypto audit).

### `build_manifest(ensemble, metrics, seed, dataset="DS02", **extra) -> dict` (`persistence.py:37`)
- **Firma:** `build_manifest(ensemble, metrics: dict, seed: int, dataset="DS02", **extra) -> dict`.
- **Qué hace:** construye el manifest JSON con métricas, hashes, contrato de inferencia, conformal.
- **Retorno:** dict (luego `write_manifest`).
- **Llamado desde:** NB03 celda 54.

### `assert_ds02_artifact(ensemble) -> None` (`persistence.py:94`)
- **Firma:** `assert_ds02_artifact(ensemble) -> None`.
- **Qué hace:** verifica que el ensamble cargado es DS02 (hashes, shapes). Lanza si no.
- **Retorno:** None o excepción.
- **Llamado desde:** NB03 celda 54/55.

### `save_ensemble(ensemble, out_dir=".", manifest=None) -> dict` (`persistence.py:108`)
- **Firma:** `save_ensemble(ensemble, out_dir: str = ".", manifest: dict | None = None) -> dict`.
- **Qué hace:** guarda `.joblib` + `.keras` + manifest en `out_dir`.
- **Retorno:** dict con rutas.

### `_detached_copy(ensemble, bilstm_path)` (`persistence.py:155`)
- **Firma:** `_detached_copy(ensemble, bilstm_path: str)` (interna).
- **Qué hace:** copia del ensamble con el BiLSTM cargado desde disco (para serializar sin referencias vivas).

### `load_bilstm(path=BILSTM_FILE)` (`persistence.py:170`)
- **Firma:** `load_bilstm(path: str = BILSTM_FILE)`.
- **Qué hace:** carga el `.keras` (con `LastStepPooling` registrado).

### `load_ensemble(path=ENSEMBLE_FILE)` (`persistence.py:189`)
- **Firma:** `load_ensemble(path: str = ENSEMBLE_FILE)`.
- **Qué hace:** carga el `.joblib` y reconstruye el ensamble.
- **Llamado desde:** NB03 celda 55, `dashboard_ds02.py` (Casos nuevos, cached).

### `write_manifest(path, manifest)` (`persistence.py:201`)
- **Firma:** `write_manifest(path: str, manifest: dict) -> None`.
- **Qué hace:** escribe el manifest JSON a disco.

### `data_fingerprint(arrays) -> str` (`persistence.py:206`)
- **Firma:** `data_fingerprint(arrays: dict) -> str`.
- **Qué hace:** SHA-256 del contenido de los arrays (ver N21).

## El proceso completo, sin centrarnos en las cuentas

```mermaid
flowchart LR
    ENS[Ensamble entrenado] --> SAVE[save_ensemble]
    SAVE --> JOB[.joblib + .keras + manifest]
    JOB --> LOAD[load_ensemble]
    LOAD --> ASSERT[assert_ds02_artifact]
    ASSERT --> OK[RELOAD OK]
```

## Qué no debemos confundir

| Concepto | Qué significa | Qué no significa |
|---|---|---|
| manifest | Contrato + hashes del artefacto | Código fuente |
| assert_ds02_artifact | Verificación de integridad | Re-entrenamiento |
| RELOAD OK | recargado == memoria | Bit a bit idéntico al entrenado |

## Conexión con los notebooks del repositorio

- `notebooks/ds02_ensemble/03_evidencia_multisemilla_diagnostico.ipynb` celdas 54, 55.
- `src/ds02_rul/persistence.py:29,37,94,108,155,170,189,201,206`.

## Resumen para recordar

> save_ensemble → .joblib+.keras+manifest. load_ensemble + assert_ds02_artifact → RELOAD OK. Hashes detectan sustituciones.

## Autoevaluación

1. ¿Qué verifica `assert_ds02_artifact`?
2. ¿Por qué `_detached_copy` carga el BiLSTM desde disco?
3. ¿Qué significa RELOAD OK?

## Estado

- [ ] En curso
