# Tasks: interactive "explore by cycle"

**Change:** `2026-10-31-ds02-explorar-por-ciclo`

## 1. Exploration block (UI)

- [x] 1.1 Add a new section in `app/dashboard_ds02.py` inside the live-eval tab,
      after the presets block and before the editable-grid path, with a stable
      `key` namespace (`explorar_*`).
- [x] 1.2 Implement `st.selectbox` for engine (11 / 14 / 15) using the existing
      unit list.
- [x] 1.3 Implement `st.selectbox` for tramo length (50 / 300, default 300).
- [x] 1.4 Implement `st.slider` for end position (0.0–1.0, step 0.01) with a
      stable `key`.
- [x] 1.5 On every rerun, generate the table with `INF.example_window(unit,
      position)` or `INF.window_ending_at(unit, cycle, rows=length)` and store
      it in `session_state`.
- [x] 1.6 Render a read-only preview: cycles covered, row count, estimated
      triage state (no scoring).
- [x] 1.7 Add `st.button` "Evaluar este tramo" that calls `INF.score_table` on
      the stored table and renders point + band + state + work order.
- [x] 1.8 Ensure no `score_table` call happens during slider ticks (verify by
      inspection and test).

## 2. Tests (TDD — RED first)

- [x] 2.1 Add `test_explorar_por_ciclo_genera_tabla_valida`: position 0.5 →
      table with ≥ 50 rows and 19 columns in dataset order.
- [ ] 2.2 Add `test_explorar_por_ciclo_estado_preview`: position 0.05 → APTO;
      position 0.9 → HANGAR (or the state the engine actually yields).
- [x] 2.3 Add `test_explorar_por_ciclo_evaluar_funciona`: button press →
      `live_result` not None, windows > 0.
- [ ] 2.4 Add `test_explorar_por_ciclo_no_rompe_presets`: the three presets
      still yield APTO / INSPECCIÓN / HANGAR.

## 3. Verification

- [x] 3.1 Run `python -m pytest tests -q` and confirm green.
- [ ] 3.2 Run `python scripts/verify_gate.py` (full suite, ~3.5 min) before
      closing.
- [ ] 3.3 Manual smoke test in the browser: move the slider, confirm no scoring
      happens until the button is pressed.

## Acceptance

- All tasks checked.
- No regression in `tests/test_live_eval.py` (42 tests) or `tests/test_dss_ui.py`
  (31 tests).
- No CSS/JS injection (`test_no_css_is_injected_into_the_app` still green).
