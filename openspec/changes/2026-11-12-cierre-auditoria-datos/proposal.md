# Proposal: Cerrar hallazgos de auditoría sin tocar notebooks ni n8n

**Change:** `2026-11-12-cierre-auditoria-datos`
**Branch:** `refactor/estructura-ds02-clase-2026-11-10`
**Date:** 2026-11-12
**Capability:** `ds02-datos-reproducibilidad` (ADDED)

## Intent

Cerrar cuatro hallazgos de la auditoría 2026-11-12 que se pueden resolver sin
tocar ningún `.ipynb` ni `n8n/`:

1. La tabla multisemilla del README no coincide con el CSV vigente.
2. El test de corrección OOF se salta por buscar `_p1_oof_cache.npz`.
3. `auditoria_nulos.json` no guarda la máscara MAR, solo el recuento.
4. No hay manifiesto golden ni comprobación rápida sin cargar el HDF5.

El objetivo es dejar esos cuatro puntos verificables y reversibles, **sin**
reentrenar, sin modificar modelos y sin arreglar los fallos de notebook/n8n que
quedan fuera de alcance.

## Scope

### In Scope

- **Cifras multisemilla:** actualizar la documentación vigente para que la
  media y la tabla salgan del CSV actual (`resultados/bundle_c_multiseed.csv`)
  más la fila 42 del manifiesto. Añadir errata en el ADR histórico, sin
  reescribirlo.
- **Test OOF:** reescribir `tests/test_mia_rules.py::test_la_correccion_mejora_el_nasa_en_el_oof_puro`
  para usar `src/mia/instrumento_oof.npz` (`units`, `cycles`, `y`, `pred_ema`)
  en vez del cache inexistente `_p1_oof_cache.npz`.
- **Máscara MAR:** añadir al JSON de auditoría las posiciones inyectadas
  (`fila`, `unit`, `cycle`, columna), su versión y un SHA-256 canónico; test
  que fija que la máscara tiene exactamente `nulos_inyectados` posiciones.
- **Manifiesto golden:** generar `data/processed/dataset_manifest.json` con
  SHA-256 de bytes, huella de contenido, filas, columnas y versiones de
  pandas/pyarrow; añadir `--fast-check` que verifica el manifiesto sin cargar
  el HDF5.

### Out of Scope

- Cualquier `.ipynb`, incluido `notebooks/00_datos.ipynb`.
- `n8n/` y `n8n/flujo.json`.
- CI, fixtures de `data/processed`, escritura atómica, lock, ablación de
  `cycle`, alias `mejor_modelo.joblib`, rate limiter, poda de `mlruns`,
  refactor de `except`/`sys.path`.
- Reentrenar o modificar cualquier archivo bajo `models/`.

## Decision

**Fuente de verdad multisemilla: el CSV vigente.**

Con `42 = 4.338` (manifiesto), `7 = 4.371` y `123 = 4.291`:

| Métrica | Valor |
|---|---:|
| Media RMSE | **4.333** |
| Std RMSE (muestral, n=3) | **0.040** |
| Media NASA | **2335.1** |
| Std NASA (muestral, n=3) | **28.7** |

La cifra publicada `4.324 ± 0.107 / 2341.0 ± 54.1` se conserva como
**histórica** porque sale del CSV anterior (`72035c3`), no del vigente. No se
restaura el CSV viejo: se documenta la errata.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `README.md`, `README.en.md`, `AGENT.md` | Modified | Tabla y media multisemilla vigentes |
| `src/clase/README.md`, `docs/framework_auditoria.md` | Modified | Cifra vigente y nota de errata |
| `docs/decisions/ADR-011-...md` | Modified | Sección de errata, sin reescribir la decisión |
| `tests/test_mia_rules.py` | Modified | Test OOF contra el instrumento versionado |
| `src/clase/dataset_clase.py` | Modified | Máscara MAR + manifiesto + `--fast-check` |
| `tests/test_clase_dataset.py` | Modified | Tests de máscara y manifiesto |
| `data/processed/auditoria_nulos.json` | Regenerated | Ignorado por git; artefacto local |
| `data/processed/dataset_manifest.json` | New | Ignorado por git; artefacto local |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Elegir mal la fuente multisemilla | Medium | La decisión está escrita arriba; el CSV viejo queda como histórico |
| El test OOF cambia de método | Low | Usa el mismo instrumento congelado y la misma aserción NASA |
| El JSON de máscara crece demasiado | Low | 1.185 triples `[fila, unit, cycle]`; ~60 KB |
| `--fast-check` da falso OK | Low | Verifica SHA de bytes + auditoría; test de parquet manipulado |
| El manifiesto queda obsoleto | Medium | Se regenera en cada build; `--fast-check` lo detecta |

## Rollback Plan

- Revertir los cambios de documentación y el test OOF con `git checkout --`.
- Quitar las claves nuevas del audit y las funciones del manifiesto.
- Borrar `data/processed/dataset_manifest.json` (ignorado).
- Regenerar `data/processed/auditoria_nulos.json` con el builder anterior.
- No hay migración, no hay modelo, no hay notebook.

## Success Criteria

- La tabla multisemilla del README coincide con el CSV vigente y no queda
  ninguna cifra `4.324 ± 0.107` presentada como vigente en documentación
  actual (solo como histórica/errata).
- El test OOF se ejecuta, no se salta, y la corrección baja el NASA Score.
- `auditoria_nulos.json` contiene 1.185 posiciones y `--check` sigue en OK.
- `--fast-check` devuelve 0 con el manifiesto íntegro y 1 tras manipular un
  parquet.
- Ningún `.ipynb` ni `n8n/` aparece en `git diff`.
- Los tests focalizados pasan. La suite completa **sigue roja** por los 4
  fallos de notebook/n8n fuera de alcance; no se afirma lo contrario.

## Open Questions

- Ninguna bloqueante. La única decisión de producto es la fuente multisemilla,
  ya fijada arriba; si se prefiere restaurar el CSV anterior, hay que decirlo
  antes de implementar.
