# Proposal: Adopción del bundle C (B queda fuera)

**Change:** `2026-11-04-adopcion-bundle-c`
**Status:** Proposed
**Capability:** modifica `rul-prediction-ds02` (campeón desplegado) y `clase-track` (fuente de verdad de notebooks)
**Rama:** `clase-modelo-c`
**Fecha:** 2026-11-04

---

## Why

La entrega se defiende como **un** modelo, no como dos. Hoy conviven:

- **B** (híbrido sobre HDF5 limpio, `models/`, 4.251 / 2305.1, evidence en `notebooks/ds02_ensemble/01–03`).
- **C** (mismo pipeline sobre la base adaptada MAR T30 + ffill, `src/clase/models/`, manifest 4.338 / 2336.2, media multiseed 4.314 ± 0.042).

La rúbrica pide nulos tratados con criterio (patrón + imputación) y el modelo que se presenta debe ser el que se explica. Mantener B como campeón obliga a defender un modelo que **no** usa la imputación que el alumno ha construido, y deja el bundle de clase como "experimento perdedor". Se invierte la decisión: **C es el campeón desplegado; B sale del repo activo y queda archivado como historia medida**.

No se reentrena nada: los artefactos de C ya existen y sus SHA-256 casan con su manifiesto (verificado 2026-11-04).

## Scope

**In scope**

1. Artefactos: copia de seguridad de B en `archive/models_b/`, instalación de C en `models/` y ajuste del manifiesto al contrato DS02 (`dataset: "DS02"`, procedencia de la base adaptada declarada).
2. Código: `src/clase/train_ensemble_adaptado.py` escribe en `models/`, declara `dataset` correcto y usa el **umbral preestablecido** en lugar de la puerta D11; nuevo `src/clase/evaluar_c_multisemilla.py` (sustituye al evaluador de B); test que valida la agregación multiseed.
3. Caché de la app: `scripts/build_ui_cache.py` construye desde la **base imputada** (no del HDF5 limpio), para que lo que muestra la UI sea lo que firma el manifiesto.
4. Notebooks 03/04/05: dejan de depender de `notebooks/ds02_ensemble/artifacts/` (cadena de B) y toman el bundle C como fuente.
5. Notebook 06: veredicto reescrito (C desplegado y cumple umbral), tabla multiseed por semilla, recarga bit-idéntica y nota de no-determinismo de TensorFlow.
6. Archivo (sin borrar carpetas): `notebooks/ds02_ensemble/`, `scripts/build_02_notebook.py`, `src/clase/evaluar_b_en_adaptada.py`, `tests/test_clase_b_robusto.py` → `archive/`.
7. Documentación: ADR-011 (cambio de campeón), `AGENT.md`, README raíz y de clase, banner de cifras históricas.

**Out of scope**

- **Reentrenar** B o C. El bundle C se copia, no se reproduce: TF en CPU no es determinista y reentrenar movería la media 4.314 ± 0.042 y el veredicto (4.229 sí cumple el umbral, 4.338 no).
- Recalibrar la capa de reglas (`mia/calibracion_banda.json` sigue calibrada sobre OOF de B). Se declara como limitación conocida; `scripts/freeze_rules_evidence.py` ya no era verificable en este entorno (exit 3 por instrumento ausente `_p1_oof_cache.npz`).
- Limpieza del legado FD001 (`models/*_FD001_*`, `scripts/predict.py`): es anterior a este change y no depende de B vs C.
- Ejecutar celdas de notebook. Las modificaciones dejan los `.ipynb` sin re-ejecutar; la ejecución la lanza el autor.

## Qué cambia, en una tabla

| Pieza | Antes | Después |
|---|---|---|
| `models/{ensemble,bilstm_ds02,scaler,ds02_manifest}` | B, 4.251 / 2305.1 | C, 4.338 / 2336.2 (media 4.314 ± 0.042) |
| `app/cache/` | ventanas del HDF5 limpio | ventanas de la base imputada, mismo grid 6.196 |
| `src/clase/train_ensemble_adaptado.py` | escribe `src.clase/models/`, `dataset="DS02-adaptada"`, puerta D11 | escribe `models/`, `dataset="DS02"` + `dataset_variant`, umbral 4.25 |
| `src/clase/evaluar_b_en_adaptada.py` | mide B bajo dropout | **archivado**; entra `evaluar_c_multisemilla.py` |
| `notebooks/03,04,05` | puente a `notebooks/ds02_ensemble/artifacts/` | puente al bundle C (`models/ensemble.joblib`) |
| `notebooks/06` | veredicto "D11 no superada, B sigue" | "C desplegado, cumple el umbral 4.25" |
| `notebooks/ds02_ensemble/` | evidencia de B | `archive/notebooks-ds02-ensemble/` |

## Gate de aceptación (este change)

1. `models/ds02_manifest.json` declara `dataset == "DS02"` y sus hashes de artefacto casan con los ficheros copiados.
2. `pytest tests/test_artifact_contract.py -q` verde con el bundle C.
3. `app/cache/cache_manifest.json` referencia el SHA del ensemble C y el del manifiesto C.
4. Ningún `.py` ni `.ipynb` activo referencia `notebooks/ds02_ensemble/` ni `src/clase/models/` como ruta de producción.
5. Los notebooks 01→06 conservan el orden didáctico y no se han ejecutado en este change.

## Riesgos

1. **Banda de reglas desalineada** (R6 usa la calibración de B): se documenta; recalibrar exige OOF de C y está fuera de alcance.
2. **Cifras históricas dispersas**: ~80 ficheros citan 4.251. Mitigación: banner de histórico + actualización de los documentos canónicos (README, AGENT.md, ADR).
3. **No-determinismo**: reejecutar el entreno de C puede dar otra cifra que la manifestada. Mitigación: el manifiesto es la fuente de verdad; los notebooks citan el artefacto, no una corrida nueva.

## Rollback

`archive/models_b/` guarda los cuatro ficheros de B con sus hashes; restaurarlos en `models/` y regenerar `app/cache/` devuelve el repo al estado anterior. Los `.py`/`.ipynb` archivados se recuperan con `git mv` inverso.
