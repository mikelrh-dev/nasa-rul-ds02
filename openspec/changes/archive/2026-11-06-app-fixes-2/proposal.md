# Proposal: App fixes 2 — wall dedupe, preset refresh, R9 visibility, thousands format

**Change:** `2026-11-06-app-fixes-2`
**Origin:** `docs/plans/coste-arreglos-app.md` (remaining 5 defects after `app-fixes-1` re-audit)
**Capabilities:** modifies `ds02-dss-ui` and `ds02-live-evaluation`
**Deployed spec:** `openspec/specs/ds02-dss-ui/spec.md`
**Status:** Proposed

## Intent

Fix five living defects without touching notebooks, models, or excluded work (MLflow, n8n, respuesta individual, SHAP waterfall and multisemilla already done in app-fixes-1):

1. Incorporar double-counts the wall: `_tarjetas_gemelos` adds a second card for the same alta already in `_tarjetas_cache` via `frame_con_altas` (3→5 instead of 3→4).
2. Preset/correction is stale inside `@st.fragment`: module-frozen arguments keep the band and thresholds visible stale when preset/toggle change.
3. R9 is invisible in Motor when APTO: only the winning rule is rendered, so evaluated-but-not-triggered R9 is never shown.
4. Thousands separator uses `f"{n:,}"`: Spanish UI shows `6,196` instead of `6.196` at ~18 call sites.
5. Fragile toggle label hit-area: absorbed by fix 2's `on_change`; shorten label only if click on text still fails.

## Scope

### In Scope
- F1: `app/dashboard_ds02.py:823-862` filter twins in `_altas()`; correct `openspec/specs/ds02-dss-ui/spec.md:425` (MODIFIED, same requirement name) and `tests/test_app_fixes1.py:51-53,104-114` (`_wall` 5→4→3, disjoint labels).
- F2+F5: `app/ui_modulos/_tab_flota.py:392-423` inside `@st.fragment` (`:139`); `on_change` on select+toggle (+number_input if needed) calling `st.rerun(scope="app")`; keep fragment and pagination; shorten label to `Correccion reglas (R2b+R6)` only if needed.
- F3: `app/ui_modulos/_tab_motor.py:225-230` render `R9 evaluada: No` via `src/mia/reglas.py:if_R9_HANGAR` on `L_inf`; wording `evaluada, no dispara`, never `dispara` in APTO. View-only.
- F4: `fmt_miles` in `app/ui_data_loader.py` (`f"{n:,}".replace(",",".")`) replacing `f"{n:,}"` in `dashboard_ds02.py`, `_tab_flota.py:532`, `_tab_auditoria.py:313`, `ui_batch.py:50,60`, `ui_inference.py:59,60,499,500`; update `tests/test_live_eval.py:79-80`.

### Out of Scope
- MLflow, n8n, respuesta individual, SHAP waterfall, multisemilla (done in app-fixes-1).
- Notebooks, saved outputs, `execution_count`, joblibs, keras, `models/ds02_manifest.json`, `MLProyectVault/90-Archivo`, `app/cache/**`, `src/ds02_rul/**`.
- Git push without explicit order.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `ds02-dss-ui`: wall dedupe (MODIFIED Fleet reset), preset/correction full refresh, R9 evaluated row, Spanish thousands format, toggle hit-area.
- `ds02-live-evaluation`: Spanish thousands format in live/batch messages (same `fmt_miles` helper).

## Approach

Strict TDD (`.venv/Scripts/python -m pytest tests -q`, `strict_tdd: true`): RED test first per fix, then GREEN. F1 filter-only (no `frame_con_altas`/`quitar_alta` change); F2 module callbacks + full-scope rerun, fragment kept; F3 predicate evaluated separately, view-only; F4 single helper + call-site swap; F5 verify toggle AppTest, shorten only if needed. Gate per phase with `scripts/verify_gate.py` (venv python).

## Affected Areas

| Area | Action | Description |
|---|---|---|
| `app/dashboard_ds02.py` | Modify | F1 twin filter; F4 `fmt_miles` imports/usages |
| `app/ui_modulos/_tab_flota.py` | Modify | F2 callbacks; F4 format |
| `app/ui_modulos/_tab_motor.py` | Modify | F3 R9 row |
| `app/ui_data_loader.py`, `ui_batch.py`, `ui_inference.py`, `_tab_auditoria.py` | Modify | F4 helper + swaps |
| `tests/test_app_fixes1.py`, `tests/test_app_fixes2.py` (new), `tests/test_live_eval.py` | Create/Modify | RED→GREEN per fix |
| `openspec/specs/ds02-dss-ui/spec.md:425` | Modify at archive | Same requirement name, wall 5→4 (MODIFIED) |

Byte-compatible and unchanged: `models/*`, notebooks, `app/cache/*`, `src/ds02_rul/*`, bundle C seed 42 (RMSE 4.338), NASA SUM no 125-cycle clamp on DS02.

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Full rerun on every keystroke loops | Med | Callbacks only on select/toggle; no number_input callback unless needed; AppTest proves one run |
| Filtering twins hides legitimate gemelos | Low | Filter keyed by `_altas()` matricula set; Gemelos registrados table untouched |
| `fmt_miles` changes error text breaking regex | Low | Update `test_live_eval.py` to dot format; keep message substrings identical |

## Rollback Plan

Revert commit(s) without push. `models/` and `app/cache/` stay byte-identical by construction; `frame_con_altas`, `quitar_alta`, `src/mia/motor.py` and `src/mia/reglas.py` are not modified. If F2 full rerun loops, revert to stale view rather than shipping a loop.

## Success Criteria

- [ ] After Incorporar, wall 4 with disjoint cache/gemelos labels; after Reset, 3; gate `GATE PASSED`.
- [ ] `preset.set_value(Prudente)` + one run shows 35/30 and updated band; toggle flips band in same pass.
- [ ] APTO shows `R9 evaluada: No` and never `dispara`; `L_inf=20` shows R9 winning.
- [ ] `fmt_miles(6196)=="6.196"` and no `6,196` in Spanish UI; live-eval regex updated.
- [ ] No notebook, manifest, joblib, keras, MLflow/n8n, or individual-answer file in the diff.
