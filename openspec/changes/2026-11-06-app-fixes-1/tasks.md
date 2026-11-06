# Tasks: App fixes 1 — SHAP waterfall, fleet reset, preset restore, multiseed

**Change:** `2026-11-06-app-fixes-1`
**Estado:** pending (strict TDD, venv `.venv/Scripts/python`)

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | ~180–260 (docs + 1-line fix + flota/dashboard + RED tests) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single change, one apply commit (shared `dashboard_ds02.py`) |
| Delivery strategy | single-pr (no push) |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|
| 1 | F1–F3 code + RED tests | `.venv/Scripts/python scripts/verify_gate.py --only tests/test_app_fixes1.py` | AppTest dashboard (needs cache) | `app/ui_shap.py`, `app/flota.py`, `app/dashboard_ds02.py` |
| 2 | F4 CSV + citations | `.venv/Scripts/python -m pytest tests/test_clase_c_multisemilla.py -q` | `python -m src.clase.evaluar_c_multisemilla --desde-csv` | 5 docs; CSV is gitignored |

### [ ] 1. RED tests (strict TDD, run before any fix)

#### [x] 1.1 SHAP waterfall RED
Write `tests/test_app_fixes1.py::test_waterfall_builds_with_data` calling `ui_shap.shap_waterfall_fig` (mock `shap_waterfall_data` to stay fast) and assert no `ValueError` plus non-empty `x`/`y`.
Acceptance: test is RED on current code (`ValueError: Invalid value of type 'builtins.list' for 'totals'`), captured as evidence. Command: `.venv/Scripts/python -m pytest tests/test_app_fixes1.py::test_waterfall_builds_with_data -q`.

#### [x] 1.2 Fleet Reset RED
Add pure test: build a registry with 1 alta + 1 twin + 1 hangar for the matricula, call `flota.quitar_alta`, assert all three sections lack the matricula (wall-equivalent 3→5→3 logic).
Acceptance: RED (twins/hangar still hold the matricula). Command: `--only tests/test_app_fixes1.py -k reset -q`.

#### [x] 1.3 Preset restore RED
Add AppTest test: run dashboard, set `preset` to `Prudente (+5)` then back to `Normal`, read the two spinbuttons and assert 35/30 then 30/25. Needs cache; skip if `cache_available()` is False.
Acceptance: RED (Normal reads contaminated 35/20 after history/preset cycle). Command: `--only tests/test_app_fixes1.py -k preset -q`.

#### [x] 1.4 Multiseed baseline
Run `.venv/Scripts/python -m pytest tests/test_clase_c_multisemilla.py -q` and record pass/skip; confirm `comparativa_c_multisemilla.csv` has 3 rows with row 42 = manifest (already true, pins F4 regression).
Acceptance: green or explicit skip recorded; CSV row-42 assert shown.

### [ ] 2. Implementation GREEN

#### [x] 2.1 F1 scalar totals
`app/ui_shap.py:258`: `totals=[float(base)]` → `totals=float(base)`. No other line changes.
Acceptance: 1.1 GREEN; `go.Waterfall` docs satisfied; no new dependency.

#### [x] 2.2 F2 Reset symmetry
`app/flota.py::quitar_alta`: also remove normalized matricula from `twins` and `hangar` when present. `app/dashboard_ds02.py:738-743`: pass full `_registro()`, write back `altas`+`twins`+`hangar` to `session_state`, then `_guardar_registros()`. Keep `tests/test_flota.py` green (id never reused).
Acceptance: 1.2 GREEN; AppTest wall 3→5→3; `conftest` session isolation respected (assert counts, not files).

#### [x] 2.3 F3 preset resync
`app/dashboard_ds02.py` before the `_umbrales_pendientes` consume (≈ line 584): track `_preset_prev`; on preset change overwrite `th_apto_{preset}`/`th_aog_{preset}` with `_preset_vals`. Verify `_tab_flota.py:392-410` needs no change (widget reads synced `session_state`).
Acceptance: 1.3 GREEN; history step 4 no longer sticks after preset cycle; manual per-preset edits are reset by design (design D3).

### [ ] 3. Multiseed closure (no retrain)

#### [x] 3.1 Regenerate CSV
Run `.venv/Scripts/python -m src.clase.evaluar_c_multisemilla --desde-csv` from the repo root; confirm `resultados/comparativa_c_multisemilla.csv` is 3 rows, 4.368±0.053 / 2355.2±24.6. Do not edit `bundle_c_multiseed.csv`, manifest, or notebooks.
Acceptance: CSV row-42 equals `models/ds02_manifest.json` reference row within 1e-9; `test_csv_multisemilla_coincide_con_el_manifest_si_existe` passes (or skips with the CSV absent, never hides a mismatch).

#### [x] 3.2 Homogenize citations (docs only)
Set 4.368±0.053 (NB06) in `README.md`, `AGENT.md`, `README.en.md`, `docs/decisions/ADR-011-deploy-bundle-c-archive-bundle-b.md` (was 4.347±0.012), `MLProyectVault/LEARNING_LOG.md` (was 4.322±0.064). Keep NB05 4.330±0.053 labelled OOF where present. Do not touch `MLProyectVault/90-Archivo`, notebooks, MLflow/n8n.
Acceptance: `grep -rn "4\.347\|4\.322" README.md AGENT.md README.en.md docs/decisions/ADR-011*.md MLProyectVault/LEARNING_LOG.md` empty for the superseded citations; `grep -rn "4\.368" ` shows all five.

### [ ] 4. Verify and archive prep

#### [x] 4.1 Scopes then full gate
Run `.venv/Scripts/python scripts/verify_gate.py --only tests/test_app_fixes1.py` then `.venv/Scripts/python scripts/verify_gate.py` (full). On pre-existing failure, stash and re-run on a clean tree to distinguish (record both exits).
Acceptance: `GATE PASSED` on full suite (or a `GATE FAILED` proven pre-existing by the clean-tree re-run, with a named test).

#### [x] 4.2 No-forbidden-diff audit
`git status --short` + `git diff --stat` show only: openspec change, `app/ui_shap.py`, `app/flota.py`, `app/dashboard_ds02.py`, new RED test, F4 docs. No notebooks, `models/`, joblibs, keras, `MLProyectVault/90-Archivo`, MLflow, n8n, individual answer.
Acceptance: audit output pasted into `verify-report.md`.

---
Deltas: `specs/ds02-dss-ui/spec.md`, `specs/shap-c-explanation/spec.md`, `specs/rul-prediction-ds02/spec.md` (all ADDED; no REMOVED/RENAMED).
