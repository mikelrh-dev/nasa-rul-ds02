# Verification Report: App fixes 2 — wall dedupe, preset refresh, R9 visibility, thousands format

**Change:** `2026-11-06-app-fixes-2` · **Branch:** `clase-modelo-c` · **Mode:** Strict TDD (`strict_tdd: true`, `.venv/Scripts/python`)
**Date:** 2026-11-06 · **Verdict:** PASS (gate real, 336 passed + 6 skipped)

## Gate completo

- Comando: `.venv/Scripts/python scripts/verify_gate.py` (venv del proyecto, `python -m pytest tests -q`, ~4 min)
- Scopes `--only` previos: `tests/test_app_fixes2.py` 4 passed (12.05 s); `tests/test_app_fixes1.py` 4 passed; `tests/test_live_eval.py` 44 passed (76 s); `tests/test_flota.py` 5 passed; `tests/test_dss_interaction.py` 20 passed; `tests/test_mia_rules.py` 16 passed + 2 skipped — todos `GATE PASSED`.
- Completa: **336 passed, 6 skipped en 243.73 s (exit 0) → GATE PASSED**.
- Los 6 skips son los 6 tests que exigen `_p1_oof_cache.npz` ausente por diseño (mismo conteo que fixes-1: 332 baseline; +4 nuevos de este change).
- Si hubiera fallado por preexistente, stash + re-ejecución en árbol limpio; no fue necesario (gate verde a la primera).

## TDD RED→GREEN (evidencia)

| Fix | RED (antes) | GREEN (después) |
|---|---|---|
| F1 muro dedupe | `test_incorporar_no_duplica_muro` → `AssertionError: muro tras Incorporar: 5 (esperado 4)`; `test_app_fixes1` pinneaba 5 | 4 passed (12.05 s); métrica `Unidades en hangar` 0/4 tras Incorporar, 0/3 tras Reset; `_wall` 4→3 con `twins-altas` |
| F2 preset/correction stale | `test_preset_muestra…` → `AssertionError: preset/toggle sin on_change: banda stale` (source sin `on_change`/`scope="app"`) | 1 passed; `on_change=_rerun_app` en select+2 numbers+toggle con `st.rerun(scope="app")`, `@st.fragment` conservado; Prudente 35/30 y banda R2b+R6 en una pasada |
| F3 R9 evaluada | `test_r9_evaluada…` → `AssertionError: fila R9 evaluada ausente en Motor` | 1 passed; `R9 evaluada: No (L_inf …): evaluada, no dispara` en Motor; `si_R9_HANGAR` 35.2 False, 20 True |
| F4 thousands | `test_fmt_miles` → `AssertionError: fmt_miles ausente` | 1 passed; `fmt_miles(6196)=="6.196"`; `grep f"{n:,}"` en 5 ficheros vacío; `test_live_eval` a punto |

## Matriz de cumplimiento (spec → test runtime)

| Requirement | Scenario | Test que lo cubre | Estado |
|---|---|---|---|
| Fleet reset removes twin and hangar (MODIFIED) | Incorporar then Reset restores 3 (3→4→3) | `test_incorporar_no_duplica_muro` + `test_incorporar_y_reset_muro_3_4_3` | PASSED |
| Fleet reset removes twin and hangar (MODIFIED) | Cache fleet untouched | `test_flota.py` (5 passed, id no reutilizado) | PASSED |
| Preset and correction refresh full app | Preset change shows thresholds and band in one run | `test_preset_muestra…` (35/30 + banda) | PASSED |
| Preset and correction refresh full app | Toggle flips correction in the same pass | mismo test (`R2b` en banda) | PASSED |
| Toggle label hit-area | Label click fires toggle | `set_value(True).run()` + `on_change` estructural (no Playwright manual) | PASSED |
| R9 evaluated row in Motor | APTO shows R9 evaluated but not triggered | `test_r9_evaluada…` (`evaluada, no dispara`, nunca `dispara` en APTO) | PASSED |
| R9 evaluated row in Motor | Hangar shows R9 winning | mismo test (`si_R9_HANGAR` 20 True + `Sí` row) | PASSED |
| Spanish thousands separator | Format uses dot | `test_fmt_miles` + `test_live_eval` a punto | PASSED |
| Spanish thousands in live/batch (ds02-live-evaluation) | Cap message uses dot | `test_live_eval` + `test_fmt_miles` | PASSED |

## Auditoría de no-prohibidos

- `git diff HEAD~5..HEAD --name-only` (nuestros 5 commits): 15 ficheros — `app/dashboard_ds02.py`, `app/ui_modulos/_tab_flota.py`, `_tab_motor.py`, `_tab_auditoria.py`, `ui_data_loader.py`, `ui_batch.py`, `ui_inference.py`, `tests/test_app_fixes2.py`, `test_app_fixes1.py`, `test_live_eval.py`, openspec change (5). **Ningún** `notebooks/`, `models/`, `app/cache/`, `src/ds02_rul/`, `MLProyectVault/90-Archivo`, MLflow, n8n ni respuesta individual. `app/flota.py`, `src/mia/motor.py`, `src/mia/reglas.py` sin tocar por diseño.
- `git status --short` restante (árbol sucio previo, no commiteado aquí): notebooks, `models/ds02_manifest.json`, `n8n/flujo.json`, `MLProyectVault/90-Archivo`, etc. — **no tocados por este change**, quedan a otros changes. Los `M app/api.py`, `app/cache/cache_manifest.json`, etc. también son previos y no se stagearon.
- `grep -rn 'f".*:,"' app/dashboard_ds02.py app/ui_modulos/_tab_flota.py app/ui_modulos/_tab_auditoria.py app/ui_batch.py app/ui_inference.py` → vacío tras los swaps. `fmt_miles(6196)` → `6.196` (venv).

## Desviaciones aceptadas (con evidencia)

- **F2 AppTest ya pasaba por harness:** `preset.set_value(Prudente).run()` ya mostraba 35/30 y el toggle ya actualizaba la banda antes del arreglo (sonda: dashboard re-ejecuta completo en `AppTest`; el stale real es del navegador con `@st.fragment`). El RED real es estructural (`on_change`/`scope="app"` ausentes). El test combina ambos y lo documenta.
- **F5 label no acortado:** el AppTest del toggle pasa con `set_value`+`on_change`; sin evidencia de que el click en el texto falle en Playwright, se conserva `Aplicar corrección de reglas` (la spec y el diseño lo dejan condicional). Sin Playwright manual no hay base para cambiar el label.
- **F1 labels vía métrica:** `_tarjetas_*` no están en `session_state`; el RED/GREEN usa la métrica `Unidades en hangar` (denominador 5→4) + `3+len(altas)` como prueba de disjointness, que es lo que el muro pinta.
- **`_wall` renombrado:** `test_incorporar_y_reset_muro_3_5_3` → `3_4_3` porque el conteo cambió (12 líneas: `_wall`, el test puro y el AppTest). Es corrección de pin, no cambio de comportamiento de `flota.quitar_alta`.
