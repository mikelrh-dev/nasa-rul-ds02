# Verify report: app-ux-bundle-fix

**Change:** `app-ux-bundle-fix`
**Verdict:** PASS

## Command evidence

| Command | Result |
|---------|--------|
| `.venv/Scripts/python -m pytest tests/test_app_ux_bundle.py -q` | 9 passed |
| `.venv/Scripts/python -m pytest tests/test_n8n_decision.py -q` | 13 passed |
| `.venv/Scripts/python -m pytest tests -q` (re-run 2026-11-09) | 431 passed, 0 failed |
| `.venv/Scripts/python scripts/verify_gate.py` | GATE PASSED (431 passed) |

(Note: `python` without the `.venv` prefix is the Hermes venv without pytest —
the gate must be run with `.venv/Scripts/python`.)

### Edge probes (re-verify 2026-11-09, runtime, sin env)

- `dashboard_helpers.probar_n8n()` sin `N8N_WEBHOOK_URL` →
  `{'ok': False, 'status': None, 'decision': 'APTO'}`: ok=False esperado, sin excepción,
  log local.
- AppTest click en `Probar envío n8n` con URL vacía: `app.exception` vacío tras
  clic y rerun; `session_state['n8n_ultimo']` =
  `{'decision': 'APTO (test)', 'ok': False, 'status': None, 'en': ...}`.
  Panel renderiza estado sin crash.
- `cola_filtrada({}, {'AOG_DERIVADO'})` → `[]` (registros 0, sin crash);
  en UI el filtro vive en el ramo `registros` no vacío, con 0 registros solo
  el caption, sin tabla rota.
- Vista previa de orden: `st.dataframe(pd.DataFrame(blocked), ...)` solo dentro
  de `if blocked:`; con 0 bloqueadas va al ramo `else` (success + parte de
  disponibilidad) y no se crea dataframe de vista previa.
- Sparkline: AppTest render completo sin excepción con el muro (Plotly
  `plotly_chart` con serie `lower` por tarjeta; Plotly dibuja en SVG/canvas
  en el navegador).
- URL guard: `grep /app/terminal` en `app/` → 0 coincidencias textuales
  (path raíz `/`); único conteo `enviar_decision(` en dashboard = 1.

## Spec compliance (runtime-tested)

| Requirement | Test | Result |
|-------------|------|--------|
| selected_unit wall→Motor | `test_app_renders_n8n_panel_without_env` (AppTest) + code review of deferred write | PASS |
| n8n panel state/last-send/test | AppTest render without env URL; `test_n8n_panel_button_via_helper` | PASS |
| URL guard /app/terminal | `test_no_app_terminal_under_app` | PASS |
| Conservador/Agresivo presets | `test_presets_conservador_agresivo_ordered` | PASS |
| Contrast CSV / queue filter / order preview | `test_contrast_csv_columns`, `test_queue_filter_helper` + preview in Flota | PASS |
| Sparkline / cruda-corregida / T24-T2-T50 / trajectory CSV | code + `test_trajectory_csv_parse` | PASS |
| Second sandbox sensor | `test_sandbox_helper_includes_sensor` | PASS |
| Six-rule view | `test_six_decision_rules` | PASS |

## Correctness

- All 431 suite tests pass, including the pre-existing
  `test_dashboard_llama_una_vez_tras_decision_en_vivo` (dashboard keeps exactly
  one `enviar_decision(` call site; the panel probe lives in
  `app/dashboard_helpers.probar_n8n`).
- Este change solo toca `app/dashboard_ds02.py`, `app/ui_modulos/*`,
  `app/dashboard_helpers.py`, `tests/test_app_ux_bundle.py` y
  `openspec/specs/ds02-dss-ui/spec.md`. El árbol trae modificaciones
  preexistentes ajenas de la rama mlflow (`src/`, `notebooks/`, `mlruns/`)
  que el change no toca ni reclama.

## Issues

- CRITICAL: none.
- WARNING: none.
- SUGGESTION: `app/registros_sesiones.hermes-respaldo` leftover from an
  interrupted suite run was repaired before re-running; it is outside this change.

Tools used to inspect the deployed request: none (local repo inspection only).
