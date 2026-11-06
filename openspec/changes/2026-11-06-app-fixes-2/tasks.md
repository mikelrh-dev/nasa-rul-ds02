# Tasks: App fixes 2 — wall dedupe, preset refresh, R9 visibility, thousands format

**Change:** `2026-11-06-app-fixes-2`
**Estado:** pending (strict TDD, venv `.venv/Scripts/python`)

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | ~220–320 (docs + 4 UI fixes + RED tests) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single change, one apply commit (shared `dashboard_ds02.py`/`_tab_flota.py`) |
| Delivery strategy | single-pr (no push) |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Focused test command | Runtime harness | Rollback boundary |
|---|---|---|---|---|
| 1 | F1–F4 code + RED tests | `.venv/Scripts/python scripts/verify_gate.py --only tests/test_app_fixes2.py` | AppTest dashboard (needs cache) | `app/dashboard_ds02.py`, `_tab_flota.py`, `_tab_motor.py`, `ui_data_loader.py` |
| 2 | F1 pin update + F4 regex | `.venv/Scripts/python scripts/verify_gate.py --only tests/test_app_fixes1.py tests/test_live_eval.py` | `pytest tests/test_app_fixes1.py tests/test_live_eval.py -q` | 2 test files only |

### [x] 1. RED tests (strict TDD, run before any fix)

#### [x] 1.1 F1 wall dedupe RED
Write `tests/test_app_fixes2.py::test_incorporar_no_duplica_muro` AppTest: run dashboard, click Incorporar, assert `set(cache labels) ∩ set(gemelos labels) == ∅` and `len(cache)+len(gemelos)==4`; after Reset `==3`. Update `tests/test_app_fixes1.py:_wall` and its 5→3 asserts to 4→3 RED.
Acceptance: RED (intersection non-empty, wall 5). Command: `.venv/Scripts/python -m pytest tests/test_app_fixes2.py::test_incorporar_no_duplica_muro -q`.

#### [x] 1.2 F2 preset/toggle stale RED
Add `tests/test_app_fixes2.py::test_preset_muestra_umbrales_y_banda_en_una_pasada`: `preset.set_value("Prudente (+5)").run()` once, assert `th_apto_Prudente (+5)==35.0`, `th_aog_Prudente (+5)==30.0` and band caption updated; toggle-on flips band in same pass.
Acceptance: RED (band stale after one run). Command: `--only tests/test_app_fixes2.py -k preset`.

#### [x] 1.3 F3 R9 RED
Add `tests/test_app_fixes2.py::test_r9_evaluada_visible_en_motor`: Motor view with `L_inf=35.2` shows `R7` winning and `R9 evaluada: No` with `evaluada, no dispara` and never a `dispara` claim in APTO; `L_inf=20` shows `R9` winning (via `si_R9_HANGAR`).
Acceptance: RED (no R9 row in Motor). Command: `--only tests/test_app_fixes2.py -k r9`.

#### [x] 1.4 F4 thousands RED
Add `tests/test_app_fixes2.py::test_fmt_miles` asserting `fmt_miles(6196)=="6.196"` and no `6,196` in preflight/band text.
Acceptance: RED (`ImportError: fmt_miles`). Command: `--only tests/test_app_fixes2.py -k miles`.

### [x] 2. Implementation GREEN

#### [x] 2.1 F1 twin filter
`app/dashboard_ds02.py::_tarjetas_gemelos`: `matriculas = {a["matricula"] for a in _altas()}`; `if gemelo_id in matriculas: continue` before card build. No `frame_con_altas`/`quitar_alta` change; gemelo stays in Gemelos registrados.
Acceptance: 1.1 GREEN; `_wall` 4→3; `tests/test_flota.py` untouched.

#### [x] 2.2 F2+F5 callbacks (fragment kept)
`app/ui_modulos/_tab_flota.py`: module-level `def _rerun_app(): st.rerun(scope="app")`; wire `on_change=_rerun_app` on `preset` select and `aplicar_reglas` toggle (+number_input only if 1.2 needs it). Keep `@st.fragment`. Shorten toggle label to `Correccion reglas (R2b+R6)` only if AppTest click fails.
Acceptance: 1.2 GREEN; one `run()` shows 35/30 + band; pagination unchanged.

#### [x] 2.3 F3 R9 row
`app/ui_modulos/_tab_motor.py` after `Regla que decide`: `r9 = R.si_R9_HANGAR({"limite_inferior": _lo_g, "alertas_datos": [], "umbrales": umbrales})`; `st.caption(f"R9 evaluada: Sí/No ...")` with `evaluada, no dispara` wording; `src/mia/*` untouched.
Acceptance: 1.3 GREEN; APTO never claims `dispara`; 20 shows R9 winning.

#### [x] 2.4 F4 helper + swaps
`app/ui_data_loader.py`: `def fmt_miles(n): return f"{int(n):,}".replace(",",".")`. Swap `f"{n:,}"` in `dashboard_ds02.py` (245,247,757,758,930,944,1750,1751,1756), `_tab_flota.py:532`, `_tab_auditoria.py:313`, `ui_batch.py:50,60`, `ui_inference.py:59,60,499,500`. Update `tests/test_live_eval.py:79-80` to dot.
Acceptance: 1.4 GREEN; `grep -rn "{.*:,}" app/*.py app/ui_modulos/*.py` empty for counts; no metric change.

### [ ] 3. Verify and archive prep

#### [ ] 3.1 Scopes then full gate
Run `.venv/Scripts/python scripts/verify_gate.py --only tests/test_app_fixes2.py` then `.venv/Scripts/python scripts/verify_gate.py` (full). On pre-existing failure, stash and re-run on a clean tree to distinguish (record both exits).
Acceptance: `GATE PASSED` on full suite (or a `GATE FAILED` proven pre-existing by the clean-tree re-run, with a named test).

#### [ ] 3.2 No-forbidden-diff audit
`git status --short` + `git diff --stat` show only: openspec change, F1–F4 app files, new RED test + `test_app_fixes1.py`/`test_live_eval.py` pins. No notebooks, `models/`, joblibs, keras, `MLProyectVault/90-Archivo`, MLflow, n8n, individual answer.
Acceptance: audit output pasted into `verify-report.md`.

---
Deltas: `specs/ds02-dss-ui/spec.md` (MODIFIED Fleet reset 3→4→3 + ADDED preset refresh/toggle hit-area/R9/thousands), `specs/ds02-live-evaluation/spec.md` (ADDED thousands). MODIFIED is same requirement name; report it as MODIFIED at archive.
