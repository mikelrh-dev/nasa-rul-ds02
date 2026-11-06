# Verification Report: App fixes 1 — SHAP waterfall, fleet reset, preset restore, multiseed

**Change:** `2026-11-06-app-fixes-1` · **Branch:** `clase-modelo-c` · **Mode:** Strict TDD (`strict_tdd: true`, `.venv/Scripts/python`)
**Date:** 2026-11-06 · **Verdict:** PASS (gate real, 332 passed + 6 skipped)

## Gate completo

- Comando: `.venv/Scripts/python scripts/verify_gate.py` (venv del proyecto, `python -m pytest tests -q`, ~3 min)
- Scopes `--only` previos: `tests/test_app_fixes1.py` 4 passed (6.78 s); `tests/test_flota.py` 5 passed; `tests/test_clase_c_multisemilla.py` 4 passed; `tests/test_dss_interaction.py` 20 passed; `tests/test_mejoras_streamlit.py` 11 passed; `tests/test_ui_alta.py` 7 passed — todos `GATE PASSED`.
- Completa: **332 passed, 6 skipped en 179.83 s (exit 0) → GATE PASSED**.
- Los 6 skips son los 6 tests que exigen `_p1_oof_cache.npz` ausente por diseño (mismo conteo que BL-01…BL-09, 315 passed baseline; +17 por tests ajenos en el árbol + 4 nuevos de este change).
- Si hubiera fallado por preexistente, stash + re-ejecución en árbol limpio; no fue necesario (gate verde a la primera).

## TDD RED→GREEN (evidencia)

| Fix | RED (antes) | GREEN (después) |
|---|---|---|
| F1 `ui_shap` | `test_waterfall_builds_with_data` → `ValueError: Invalid value of type 'builtins.list' for 'totals'` (4 failed) | 1 passed (1.27 s); figura con `x`/`y` no vacíos |
| F2 `flota`+`dashboard` | `test_quitar_alta…` → `AssertionError: 'EC-MKR' not in twins` (wall 5→4); AppTest → `Reset deja el gemelo: muro 5→4, no 3` | 3 passed (pura + AppTest 3→5→3) |
| F3 preset+historia | `test_preset_historia…` → `{'th_apto_Normal': 35.0, 'th_aog_Normal': 20.0} == 30.0` (paso 1 tras paso 4) | 1 passed (30/25 → 35/20 → 30/25 → 35/30 → 30/25) |
| F4 multisemilla | Baseline `test_clase_c_multisemilla` 4 passed (fila 42 = manifiesto, 3 filas); CSV regenerado sin entrenar | 4 passed tras `--desde-csv` (4.368±0.053 / 2355.2±24.6) |

## Matriz de cumplimiento (spec → test runtime)

| Requirement | Scenario | Test que lo cubre | Estado |
|---|---|---|---|
| SHAPC-WF-01 | Waterfall builds with data | `test_waterfall_builds_with_data` | PASSED |
| SHAPC-WF-01 | No totals kwarg (Plotly 7.1.0 `Totals` ≠ número) | mismo test (construcción sin `totals`) | PASSED |
| Fleet reset removes twin and hangar | Incorporar then Reset restores 3 | `test_quitar_alta…` + `test_incorporar_y_reset_muro_3_5_3` | PASSED |
| Fleet reset removes twin and hangar | Cache fleet untouched | `test_flota.py` (5 passed, id no reutilizado) | PASSED |
| Preset thresholds restore | Prudente then Normal restores 30/25 | `test_preset_historia_restores_normal` (ciclo presets) | PASSED |
| Preset thresholds restore | History step does not stick | mismo test (historia 4→historia 1 restaura base) | PASSED |
| Multiseed evidence reconciliation | Three-row table matches manifest | `test_clase_c_multisemilla::test_csv…` + `--desde-csv` (3 filas, 4.368) | PASSED |
| Multiseed evidence reconciliation | Citations agree (5 docs 4.368) | `grep -rn "4\.347\|4\.322"` en 5 docs vacío; `4\.368` en los 5 | PASSED |

## Auditoría de no-prohibidos

- `git diff HEAD~5..HEAD --name-only` (nuestros 5 commits): 16 ficheros — `app/ui_shap.py`, `app/flota.py`, `app/dashboard_ds02.py`, `app/ui_modulos/_tab_flota.py`, `tests/test_app_fixes1.py`, `src/clase/evaluar_c_multisemilla.py`, `README.md`, `AGENT.md`, `README.en.md`, ADR-011, `LEARNING_LOG.md`, openspec change (5). **Ningún** `notebooks/`, `models/`, `MLProyectVault/90-Archivo`, MLflow, n8n ni respuesta individual.
- `resultados/comparativa_c_multisemilla.csv` es gitignored (`resultados/`); regenerado localmente, no commiteado. `resultados/bundle_c_multiseed.csv` y `models/ds02_manifest.json` sin modificar (seed 42 manda).
- `git status --short` restante (árbol sucio previo, no commiteado aquí): notebooks, `models/ds02_manifest.json`, `n8n/flujo.json`, `MLProyectVault/90-Archivo`, etc. — **no tocados por este change**, quedan a otros changes. Ver nota de hunks previos en el commit `ef6f87b`.
- `grep -rn "4\.347\|4\.322" README.md AGENT.md README.en.md docs/decisions/ADR-011*.md MLProyectVault/LEARNING_LOG.md` → vacío (sustituidas por 4.368). NB05 4.330±0.053 sigue etiquetado OOF, no sobrescrito.

## Desviaciones aceptadas (con evidencia)

- **D1 corregida:** `totals=float(base)` también es inválido — Plotly 7.1.0 `Totals` es objeto de estilo (`marker`), ni lista ni float validan (sondas directas en venv, ambas `ValueError`). El arreglo válido (primera alternativa del plan) es **omitir `totals`**. Spec/design enmendados antes de archive.
- **`waterfallgap` también era inválido en la traza** (`Invalid property … 'waterfallgap'` tras quitar `totals`): movido a `layout=dict(waterfallgap=0.25)`. Mismo defecto, misma función; sin esto la figura no construye.
- **D3 ampliada:** el resync al cambiar de preset no basta para que la historia 1 restaure tras la 4 (base derivada de umbrales contaminados 35/20 vía `estado_historia`). `_tab_flota` ahora pasa la base del preset (`_preset_vals`) a `estado_historia`, no los umbrales en vigor. Los tests puros de `ui_alta.estado_historia` no cambian (función intacta, solo el llamador).
- **AppTest purga widgets no renderizados:** el ciclo Prudente→Normal **ya** restauraba 30/25 antes del arreglo por purga de `session_state` (sonda ejecutada). El RED real es historia 4→historia 1 (35/20 en vez de 30/25, ejecutado). El resync explícito queda como intención y para navegador real con retención distinta.
