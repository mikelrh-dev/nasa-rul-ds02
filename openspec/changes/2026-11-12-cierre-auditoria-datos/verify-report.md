# Verify report — Cierre de auditoría de datos

**Change:** `2026-11-12-cierre-auditoria-datos`
**Date:** 2026-11-12
**Scope:** 4 unidades (docs multisemilla, test OOF, máscara MAR, manifiesto/fast-check)
**Out of scope:** cualquier `.ipynb`, `n8n/`, `models/`, CI, escritura atómica, ablación de `cycle`.

## Comandos y resultados

| Comando | Exit | Resultado |
|---|---:|---|
| `pytest tests/test_mia_rules.py tests/test_clase_dataset.py -q -rs -p no:cacheprovider` | 0 | **29 passed** |
| `python -m src.clase.dataset_clase --check` | 0 | `OK: data\processed coincide con la reconstrucción` |
| `python -m src.clase.dataset_clase --fast-check` | 0 | `OK: data\processed coincide con dataset_manifest.json` |
| `pytest tests -q -rs -p no:cacheprovider` | 1 | **455 passed, 4 failed, 0 skipped** (4:24) |
| `git diff --check` (solo archivos del cambio) | 0 | limpio |
| `git diff --name-only -- '*.ipynb'` | 0 | vacío (ningún notebook tracked modificado) |
| `git status --porcelain models/` | 0 | vacío (ningún modelo modificado) |

## Suite completa: 4 fallos fuera de alcance

Los 4 fallos son los ya conocidos y **no** se han tocado:

1. `test_notebooks_instrument_mlflow_live` — `00_datos.ipynb` sin cabecera MLflow.
2. `test_all_notebooks_have_mlflow_header_and_log_cell` — 8 notebooks vs 7 esperados.
3. `test_no_late_tfenable_onednn_opts` — `TF_ENABLE_ONEDNN_OPTS` en celda 1 del 00.
4. `test_flujo_tiene_accion_novedosa_en_rama_hangar` — `n8n/flujo.json` sin `HANGAR API propia`.

El skip `_p1_oof_cache.npz missing` **ha desaparecido**: el test OOF corre contra
`src/mia/instrumento_oof.npz`.

## Evidencia de las unidades

### Multisemilla

Con `42 = 4.338`, `7 = 4.371`, `123 = 4.291`:

- RMSE: media `4.333`, std muestral `0.040`.
- NASA: media `2335.1`, std muestral `28.7`.

Actualizados: `README.md`, `README.en.md`, `AGENT.md`, `src/clase/README.md`,
`docs/framework_auditoria.md`, y errata al final de `ADR-011`. La cifra
`4.324 ± 0.107 / 2341.0 ± 54.1` queda marcada como histórica (`72035c3`).

### Test OOF

`test_la_correccion_mejora_el_nasa_en_el_oof_puro` carga el instrumento
congelado, filtra unidades puras, aplica PAVA causal y comprueba que el NASA
Score baja. Pasa y ya no se salta.

### Máscara MAR

`data/processed/auditoria_nulos.json` contiene:

- `mascara_version: 1`
- `mascara_columnas.T30`: **1.185** posiciones `[fila, unit, cycle]`
- **1.185** filas únicas; 273 pares `(unit, cycle)` únicos (hay varias muestras
  por ciclo, por eso `fila` es necesaria)
- `mascara_sha256` verificado contra el JSON canónico

### Manifiesto

`data/processed/dataset_manifest.json` incluye los 8 parquet, SHA-256 de bytes,
huella de contenido, filas, columnas, auditoría, máscara, versiones
(pandas 3.0.6 / pyarrow 26.0.1) y receta.

`--fast-check` verifica sin HDF5. Tests añadidos:

- manifiesto presente y coherente;
- parquet manipulado → drift con el nombre del artefacto;
- manifiesto ausente → drift.

## Nota de diseño

`--check` compara **contenido**, no bytes. El parquet no es canónico: una
reconstrucción del mismo DataFrame cambia los bytes. Por eso `--check` no
compara el manifiesto; la integridad de bytes es de `--fast-check`. Esto se
descubrió en la primera ejecución de `--check` y se corrigió antes de cerrar.

## Rollback

1. `git checkout -- README.md README.en.md AGENT.md src/clase/README.md docs/framework_auditoria.md docs/decisions/ADR-011-...md src/clase/dataset_clase.py tests/test_clase_dataset.py tests/test_mia_rules.py`
2. Borrar `openspec/changes/2026-11-12-cierre-auditoria-datos/`.
3. Borrar `data/processed/dataset_manifest.json`.
4. Regenerar `data/processed/auditoria_nulos.json` con el builder anterior.

No hay cambios en modelos, notebooks ni n8n.
