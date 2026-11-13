# Tasks: Cierre de auditoría de datos (sin notebooks ni n8n)

**Change:** `2026-11-12-cierre-auditoria-datos`
**Capability:** `ds02-datos-reproducibilidad`

Decision needed before apply: **No** (fuente multisemilla fijada: CSV vigente)
Chained PRs recommended: **No**
400-line budget risk: **Low**

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | ~220 (docs ~80, tests ~70, builder ~70) |
| 400-line budget risk | Low |
| Suggested split | Un solo cambio, 4 unidades |
| Runtime harness | `pytest` focalizado + `--check` + `--fast-check` |
| Rollback boundary | Docs, test OOF, claves de audit, manifiesto |

### Suggested Work Units

| Unit | Goal | Focused test command | Rollback boundary |
|---|---|---|---|
| 1 | Cifras multisemilla | `pytest tests/test_clase_dataset.py -q` (no toca tests de docs; revisión manual) | README/EN/AGENT/src README/framework + errata ADR |
| 2 | Test OOF | `pytest tests/test_mia_rules.py -q` | `tests/test_mia_rules.py` |
| 3 | Máscara MAR | `pytest tests/test_clase_dataset.py -q` | `src/clase/dataset_clase.py`, `tests/test_clase_dataset.py` |
| 4 | Manifiesto + fast-check | `pytest tests/test_clase_dataset.py -q` + CLI | `src/clase/dataset_clase.py`, `tests/test_clase_dataset.py` |

## Phase 1 — Cifras multisemilla (solo documentación)

- [x] **1.1** Actualizar la tabla y la media en `README.md`.
  - Acceptance: `7=4.371`, `123=4.291`, `42=4.338`, media `4.333 ± 0.040`,
    NASA `2335.1 ± 28.7`; `4.324 ± 0.107` solo como histórica.
  - Verify: `grep -n "4.333\|4.324\|4.371\|4.291" README.md`.
  - Files: `README.md`.

- [x] **1.2** Actualizar `README.en.md` con los mismos valores.
  - Acceptance: tabla y media coherentes con 1.1.
  - Verify: `grep -n "4.333\|4.324\|4.371\|4.291" README.en.md`.
  - Files: `README.en.md`.

- [x] **1.3** Actualizar `AGENT.md`, `src/clase/README.md` y
  `docs/framework_auditoria.md`.
  - Acceptance: ninguna cifra `4.324` presentada como vigente.
  - Verify: `grep -RIn "4.324" AGENT.md src/clase/README.md docs/framework_auditoria.md`.
  - Files: `AGENT.md`, `src/clase/README.md`, `docs/framework_auditoria.md`.

- [x] **1.4** Añadir `## Errata 2026-11-12` al final de `ADR-011`.
  - Acceptance: la decisión original no se reescribe; la errata explica que
    `4.324 ± 0.107` sale del CSV anterior `72035c3` y que el vigente da
    `4.333 ± 0.040`.
  - Verify: `tail -30 docs/decisions/ADR-011-deploy-bundle-c-archive-bundle-b.md`.
  - Files: `docs/decisions/ADR-011-deploy-bundle-c-archive-bundle-b.md`.

- [x] **1.5** Comprobar que no se tocó ningún notebook.
  - Acceptance: `git diff --name-only` no contiene `.ipynb`.
  - Verify: `git diff --name-only | grep -c "\.ipynb$"` devuelve 0.

## Phase 2 — Test OOF

- [x] **2.1** Reescribir el test para cargar `src/mia/instrumento_oof.npz`.
  - Acceptance: usa `units`, `cycles`, `y`, `pred_ema`; elimina
    `select_beta_grouped` y `_p1_oof_cache.npz`; mantiene la aserción NASA.
  - Verify: `pytest tests/test_mia_rules.py::test_la_correccion_mejora_el_nasa_en_el_oof_puro -q -p no:cacheprovider`.
  - Files: `tests/test_mia_rules.py`.

- [x] **2.2** Eliminar el skip por `_p1_oof_cache.npz` o sustituirlo por un
  guard del instrumento.
  - Acceptance: el test se ejecuta, no se salta.
  - Verify: `pytest tests/test_mia_rules.py -q -rs -p no:cacheprovider`.
  - Files: `tests/test_mia_rules.py`.

## Phase 3 — Máscara MAR

- [x] **3.1** Añadir `mascara_version`, `mascara_columnas` y
  `mascara_sha256` al audit de `inyectar_nulos_mar`.
  - Acceptance: solo columnas tocadas; pares `[unit, cycle]`; SHA canónico.
  - Verify: test unitario con `_toy()` o frame sintético.
  - Files: `src/clase/dataset_clase.py`.

- [x] **3.2** Añadir tests de máscara en `tests/test_clase_dataset.py`.
  - Acceptance: longitud == `nulos_inyectados`; sin duplicados; SHA coincide;
    `--check` OK.
  - Verify: `pytest tests/test_clase_dataset.py -q -p no:cacheprovider`.
  - Files: `tests/test_clase_dataset.py`.

- [x] **3.3** Regenerar `data/processed/auditoria_nulos.json` con el builder.
  - Acceptance: 1.185 posiciones; JSON válido; parquet sin cambios de hash.
  - Verify: `python -m src.clase.dataset_clase --check`.
  - Files: `data/processed/auditoria_nulos.json` (ignorado por git).

## Phase 4 — Manifiesto golden y `--fast-check`

- [x] **4.1** Implementar `_construir_manifiesto` y la escritura idempotente
  de `dataset_manifest.json`.
  - Acceptance: incluye los 8 parquet, auditoría, máscara, versiones y receta.
  - Verify: build y `json.load` del manifiesto.
  - Files: `src/clase/dataset_clase.py`.

- [x] **4.2** Implementar `--fast-check` sin cargar el HDF5.
  - Acceptance: 0 con manifiesto íntegro; 1 con artefacto manipulado o
    manifiesto ausente; mensaje que nombra el artefacto.
  - Verify: CLI contra copia temporal con un parquet alterado.
  - Files: `src/clase/dataset_clase.py`.

- [x] **4.3** Añadir tests de manifiesto y fast-check.
  - Acceptance: build + fast-check OK; tamper detectado; manifiesto ausente
    detectado.
  - Verify: `pytest tests/test_clase_dataset.py -q -p no:cacheprovider`.
  - Files: `tests/test_clase_dataset.py`.

## Phase 5 — Verificación y cierre

- [x] **5.1** Ejecutar tests focalizados y CLI.
  - Commands:
    ```bash
    python -m pytest tests/test_mia_rules.py tests/test_clase_dataset.py -q -p no:cacheprovider
    python -m src.clase.dataset_clase --check
    python -m src.clase.dataset_clase --fast-check
    git diff --check
    ```
  - Acceptance: todo en 0; sin `.ipynb`, `n8n/` ni `models/` en el diff.

- [x] **5.2** Comprobar que la suite completa sigue igual (4 fallos fuera de
  alcance) y documentarlo.
  - Acceptance: no se afirma suite verde; se listan los 4 fallos conocidos.
  - Verify: `pytest tests -q -rs -p no:cacheprovider` (solo lectura; no se
    arreglan los fallos de notebook/n8n).

- [x] **5.3** Escribir `verify-report.md` con comandos, exit codes y
  resultados.
  - Files: `openspec/changes/2026-11-12-cierre-auditoria-datos/verify-report.md`.
