# Tasks: DS02 maintenance decision-support surface

**Change:** `2026-10-21-ds02-streamlit-dss`
**Status:** Implemented
**Spec:** [spec.md](spec.md) · [design](design.md) · [proposal](proposal.md)

| # | Task | Status | Acceptance check (measured) |
| --- | --- | --- | --- |
| 1.1 | Add `plotly` to `.venv`, `pyproject.toml` and `requirements.txt` | Done | `plotly 7.1.0` installed; `pyproject` `dependencies` bumped; `requirements.txt` pinned |
| 2.1 | `scripts/build_ui_cache.py` — score the test split, write `app/cache/ds02_windows.parquet` | Done | 6 196 rows; 3 293 / 760 / 2 143; `lower <= point <= upper` for every row |
| 2.2 | Same script writes `app/cache/ds02_rows.parquet` with the 18 real channels | Done | 12 538 rows, `T24 … Wf` + `alt, Mach, TRA, T2` |
| 2.3 | Same script writes `app/cache/cache_manifest.json` (artifact hash, contract, per-unit counts, metric block) | Done | bundle SHA-256 `0acd795b…` equals the manifest's record |
| 2.4 | Idempotence: second run reproduces the same counts and metrics | Done | counts and metric block identical across runs; only `generated_at` moves |
| 3.1 | `app/ui_data_loader.py` — cached reads and `st.cache_data` wrappers | Done | import leaves `tensorflow`/`keras` out of `sys.modules` |
| 3.2 | `classify(lower, apto, aog)` pure policy | Done | 35.7 → APTO · 30.0 → APTO · 29.9 → INSPECCIÓN · 25.0 → INSPECCIÓN · 24.9 → HANGAR |
| 3.3 | `fleet_snapshot(windows, cycle, thresholds)` with per-unit clamping | Done | clock 76 → U11 at 59 (clamped), U14 at 76; clock 1 → U14 `SIN_DATOS` |
| 3.4 | Metrics: window-weighted RMSE, macro-RMSE, per-engine RMSE/MAE/bias, MAE per RUL band | Done | live 4.2892 / 3.179 / macro 4.9026 reproduce the manifest within 5e-3; U14 8.175, bias −5.144 |
| 3.5 | `work_order(...)` serialisation to JSON and CSV | Done | only AOG units; artifact hash and thresholds in the document |
| 4.1 | `app/dashboard_ds02.py` — sidebar: unit selector, cycle slider, threshold controls | Done | AppTest: moving the slider to 40 changes the grounded KPI |
| 4.2 | Tab 1 — fleet KPIs, semaphore queue, work-order download | Done | grounded KPI equals the queue rows; 2 download widgets when blocked |
| 4.3 | Tab 2 — Plotly RUL curve, conformal band, hangar zone, per-engine cards | Done | band filled between `lower` and `upper`; red zone at RUL < 25 |
| 4.4 | Tab 3 — operating conditions + physical channels, critical region shaded | Done | labels are DS02 channel names; no FD001 `s1…s21` |
| 4.5 | Tab 4 — engine-14 audit: live error by band, density measured and refuted, prior-of-life finding | Done | density shown as discarded with −0.93 / −0.03 / +0.34 evidence; lead time 9 / 23 / 17 cycles published |
| 4.6 | Manifest audit card labelled as frozen contract | Done | sidebar expander shows recorded macro per-engine RMSE; tab 4 compares it with the live values |
| 5.1 | `tests/test_dss_ui.py` | Done | 28 tests: policy, cache, work order, isolation, theme, alt, render, interaction |
| 5.2 | `pytest tests -q` | Done | 38 passed (10 pre-existing + 28 new) |
| 5.3 | Headless render via `streamlit.testing.v1.AppTest` | Done | no exception; 4 tabs; JSON + CSV order widgets enabled |
| 5.4 | Real-browser render (headless Chrome against the running server) | Done | 426 KB DOM; title, tab labels and fleet timeline present; `#0b1220` applied |
| 6.1 | `docs/decisions/ADR-008-conformal-lower-bound-triage.md` | Done | thresholds, measured lead times and rejected alternatives recorded |
| 6.2 | `openspec/specs/ds02-dss-ui/spec.md` deployed capability spec | Done | 11 requirements, same delta as the change spec |
| 7.1 | `.streamlit/config.toml` — locked dark theme, fonts, radii, padding, chart palettes | Done | parsed by `tomllib` in a test; `streamlit config show` reflects every key |
| 7.2 | Shared design tokens for Plotly; `theme=None`, transparent surface, theme-colored axes | Done | charts sit on the card surface; state colors match badges and table rows |
| 7.3 | Material icons in tabs, headings, buttons, expanders, alerts and metrics | Done | no emoji-only navigation left |
| 7.4 | Bordered cards (`st.metric(..., border=True)`, `st.container(border=True)`, `st.columns(..., border=True)`) and a fleet-timeline chart | Done | 4 KPI cards, 5 chart cards, 3 audit cards, 1 timeline |
| 7.5 | `alt=` on every chart and grid | Done | 6 charts + 5 dataframes all carry a non-empty accessible name |
| 7.6 | Keep the theme committed while `.streamlit/secrets.toml` stays ignored | Done | `git check-ignore` clears `config.toml` and still matches `secrets.toml` (`.streamlit/*` + negation) |

## Notes recorded during the build

* The cache reproduces `models/ds02_manifest.json` exactly (4.2892 vs 4.289
  weighted; macro 4.9026; NASA 2 310.6), so the live figures and the frozen
  contract agree. The notebook report's `4.315` is a different run and is not
  used anywhere in the UI.
* No test engine reaches 75 cycles of true RUL, so the `[75, ∞)` MAE band has no
  rows; the UI reports that instead of drawing an empty bar or inventing a value.
* Engine 11 ends at cycle 59 while engine 14 lasts 76, so the fleet clock clamps
  the shorter unit rather than extrapolating it.
