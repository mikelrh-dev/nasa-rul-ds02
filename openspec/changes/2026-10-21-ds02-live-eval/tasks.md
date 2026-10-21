# Tasks: evaluate an aircraft the user brings

**Change:** `2026-10-21-ds02-live-eval`
**Status:** Implemented
**Spec:** [spec.md](spec.md) · [design](design.md) · [proposal](proposal.md)

| # | Task | Status | Acceptance check (measured) |
| --- | --- | --- | --- |
| 1.1 | `app/ui_inference.py` — `channel_order()` from the cache provenance, `window_size()`, `required_columns()` | Done | order is `alt, Mach, TRA, T2, T24 … Wf`, read from `cache_manifest.json`, never typed |
| 1.2 | `example_window(unit, position)` — a real 50-row window lifted from `app/cache/ds02_rows.parquet` | Done | U14, cycles 40→43, rows 812–862, 50 rows × 19 columns |
| 1.3 | `validate_table()` — missing/extra columns, wrong order, short table, non-numeric or NaN cell, decreasing cycles | Done | each rejection names the column, the row or the counts; duplicates allowed (several records per cycle) |
| 1.4 | Lazy bundle + `@st.cache_resource`; `LIVE_UNIT = -1` so the causal EMA never mixes engines | Done | importing the module leaves `tensorflow` and `keras` out of `sys.modules`; second call returns the same object |
| 1.5 | `score_table()` — `raw_windows(step=1)` then `predict_interval()`; returns per-window point/band plus the contract | Done | one window for 50 rows, 11 for 60; `lower <= pred <= upper`, finite, `lower >= 0` |
| 1.6 | `live_work_order()` — separate document, no `rul_real`, provenance of the data | Done | `modo = "evaluación en vivo"`, `sin_ground_truth = true`, artifact hash present |
| 2.1 | Fifth tab `Evaluar unidad nueva` with three inputs inside `st.form` | Done | only executed on submit; the page still renders without TensorFlow |
| 2.2 | Example path: table view + evaluate button, zero typing | Done | AppTest press renders `RUL estimada` |
| 2.3 | Grid path: `st.data_editor(num_rows="dynamic")` seeded with the example, per-column number format | Done | block paste accepted; edited frame goes through the same validator |
| 2.4 | CSV path: `st.file_uploader`, parse errors surfaced, row/column count shown | Done | CSV round-trip of the example scores identically to the direct path |
| 2.5 | Result surface: four KPI cards, badge with state, band chart when > 1 window, contract expander | Done | `35.7 / 30.0 → APTO`, `29.9 / 25.0 → INSPECCIÓN`, `24.9 → HANGAR` use the same `classify()` |
| 2.6 | Work-order download only for a grounded unit | Done | button appears for AOG, absent otherwise |
| 2.7 | Vocabulary: per-column `help` on grid and data view from `CHANNEL_LABELS`, glossary expander with physical meaning + measured DS02 range, `cycle` explained, sidebar *Cómo leer esta pantalla* | Done | 18/18 channels documented; glossary grid carries all six range columns; sidebar defines RUL, `L_inf`, band, states, cycle and window |
| 2.8 | `observed_envelope()` and `plausibility_warnings()` — outside the observed range ±5 % is flagged, never silently scored | Done | real U14 example is clean; `Mach = 49` flags `1/50` and still scores; a single-cycle window is flagged |
| 2.9 | `template_csv()` + download button; paste mode shows `filas → ventanas` and how far the table is from the 50-row minimum | Done | template is 50×19, all cells empty, and the validator rejects it instead of scoring zeros |
| 3.1 | `tests/test_live_eval.py` | Done | 27 tests: import guard, 7 validator cases, scoring, CSV equivalence, trajectory, cache resource, work order, render, button press, 18-column glossary, envelope ordering, plausibility flagging, template shape, sidebar legend |
| 3.2 | Full suite | Done | `pytest tests -q` → **65 passed**, exit 0 |
| 3.3 | Headless render stays TensorFlow-free | Done | fresh process: `5 tabs`, `tensorflow False`, `keras False` |
| 3.4 | Real browser: click the tab, then the button, over CDP | Done | result in **9.1 s** cold (bundle load) and **1.0 s** warm: RUL 30.8, band 17.3–47.8, `DERIVACIÓN A HANGAR (AOG)`; no error on the page |
| 4.1 | `openspec/specs/ds02-live-evaluation/spec.md` deployed capability | Done | 7 requirements, same content as this delta |
| 4.2 | README interfaces + `openspec/specs/ds02-dss-ui/spec.md` tab count | Done | README states the CSV contract and the stride; DSS spec now says five tabs |

## Notes recorded during the build

* The tab can never be "a form with 900 sensor cells": 50 rows × 19 columns is
  the minimum a window needs, and typing that by hand is not a workflow. The
  example exists so the tab is useful on first paint; paste and CSV are the real
  inputs.
* Scoring is gated behind the submit button, so `streamlit run` still starts in
  ~1.4 s and the first evaluation pays the ~8 s Keras load. `st.cache_resource`
  makes every later evaluation ~1 s.
* The band is still the calibration of the development engines. For a unit with
  no ground truth the honest claim is "conservative lower bound", not accuracy;
  the `RUL ≈ 63 − ciclo` bias of long-lived engines is published in the tab, not
  hidden.
* A test asserts the CSV path and the direct path produce identical frames, so
  the three inputs cannot drift apart silently.
