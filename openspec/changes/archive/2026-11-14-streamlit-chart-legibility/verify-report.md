# Verify report: Streamlit chart legibility and fixed chrome

**Change:** `2026-11-14-streamlit-chart-legibility`
**Verified:** 2026-11-14
**Mode:** Strict TDD (pytest)

## Gate

Command: `python -m pytest tests -q`

| Run | Passed | Failed |
|---|---|---|
| Baseline before the change | 458 | 3 |
| After the change | 465 | 3 |

Exit code 1 comes from three **pre-existing** failures unrelated to this change, about
MLflow headers in notebooks: `test_mlflow_backfill.py::test_notebooks_instrument_mlflow_live`,
`test_mlflow_live.py::test_all_notebooks_have_mlflow_header_and_log_cell`,
`test_mlflow_live.py::test_no_late_tfenable_onednn_opts`. The failure set is identical
before and after; the delta is +7 passed (the new contract test file). No new failures.

Focused runs:

| Command | Result |
|---|---|
| `pytest tests/test_ui_chart_chrome.py -q` | 7 passed |
| `pytest tests/test_dss_ui.py tests/test_app_ux_bundle.py tests/test_mejoras_streamlit.py tests/test_ui_rules.py tests/test_ui_batch.py tests/test_dss_interaction.py tests/test_hangar.py tests/test_fleet_registries_session.py -q` | 117 passed |
| `pytest tests/test_live_eval.py tests/test_dss_ui.py tests/test_dss_interaction.py -q` | 105 passed |

## Visual verification (Playwright, live app on http://127.0.0.1:8501/)

An independent delegated verifier passed the four defect classes but compared the legend
only against the plotting area. The parent re-measured and found two residual defects,
both fixed afterwards:

- legend overlapping the X axis title by 17 / 17 / 14 px;
- the rotated Y title of the pressures chart extending 9 px above the SVG top.

Final geometry measured by the parent with Playwright (bounding boxes, CSS pixels):

Viewport 1280x900:

| Chart | plot height | legend rows | gap legend-to-plot | legend vs X title | legend vs ticks | legend inside figure | Y title inside | X title inside |
|---|---|---|---|---|---|---|---|---|
| Motor radiografía presiones | 88 | 2 | 65 | 0 px | 0 px | yes (-26) | yes | yes |
| Motor radiografía temperaturas | 88 | 2 | 65 | 0 px | 0 px | yes (-26) | yes | yes |
| Motor trayectoria RUL | 266 | 2 | 65 | 0 px | 0 px | yes (-26) | yes | yes |

Viewport 560x900:

| Chart | plot height | legend rows | gap legend-to-plot | legend vs X title | legend vs ticks | legend inside figure | Y title inside | X title inside |
|---|---|---|---|---|---|---|---|---|
| Motor radiografía presiones | 85 | 3 | 68 | 0 px | 0 px | yes (-7) | yes | yes |
| Motor radiografía temperaturas | 88 | 2 | 65 | 0 px | 0 px | yes (-26) | yes | yes |
| Motor trayectoria RUL | 247 | 5 | 72 | 0 px | 0 px | yes (0) | yes | yes |

Other checks on every tab, both viewports:

- Mode bar: `document.querySelectorAll('.modebar').length = 0`; `.modebar-btn` count 0.
- Streamlit exception banners: 0.
- Audit band table: headers exactly `Tramo`, `Ventanas`, `MAE`, `Sesgo`, three rows
  (`[0, 25)`, `[25, 50)`, `[50, 75)`); zero occurrences of the raw name `band` in the DOM.
- Title: `DS02 · Soporte a la decisión`; the four tabs present.

## TDD cycle evidence

| Task | Test file | Layer | Safety net | RED | GREEN | TRIANGULATE | REFACTOR |
|---|---|---|---|---|---|---|---|
| 1.1–1.4 | `tests/test_ui_chart_chrome.py` | Unit | 458 passed / 3 failed baseline | ✅ 7 written, 7 failed | ✅ 7 passed | ✅ defaults + overrides, config value + adoption, rename vs assign | ✅ assertions kept behavioural |
| 2.1–2.4 | same | Unit | previous file green | ➖ covered by 1.1–1.2 | ✅ passed | ✅ legend distance computed from final margins | ✅ margins hoisted to constants |
| 3.1–3.4 | same | Unit + AST contract | previous file green | ➖ covered by 1.2–1.3 | ✅ passed | ✅ scans every `st.plotly_chart` under `app/` | ➖ None needed |
| 4.1 | suite | Integration | — | — | ✅ 465 passed | — | — |
| 4.2 | Playwright | E2E evidence | — | — | ✅ see tables above | ✅ two viewports, two passes | — |

Total tests written: 7. Passing: 7. Layers: unit 4, contract/AST 2, integration 1.
Approval tests: none — no existing behaviour was refactored beyond the shared layout
owner, whose consumers are covered by the existing UI suites.

## Deviations from design

1. **`automargin` removed instead of added.** The design specified
   `xaxis=dict(automargin=True), yaxis=dict(automargin=True)`. In implementation,
   `automargin` reserves space for the legend by shrinking the plotting area, and since
   the legend offset is a fraction of that area, the clearance fed back into itself:
   the legend moved back up and overlapped the X axis title again (measured 7 px).
   Final approach: explicit margins only, with the legend pinned 65 px below the plot
   computed from the final `margin` and `height`.
2. **Legend uses the dataset channel code only** (`CHANNEL_LABELS[...].split(" · ")[0]`).
   The long physical descriptions wrapped the pressure legend into 5 rows and Plotly
   shrank the plotting area to make room for them. The full descriptions remain in the
   glossary, the captions and the paste-grid `help` text, which keep the
   `CODIGO · descripción` contract asserted by `tests/test_live_eval.py`.
3. **Radiography heights raised 220 → 280 px** so the rotated Y title fits inside the
   figure with the legend below.

## Known limitations

- At 560 px the trajectory legend (five entries) ends flush with the bottom edge of its
  figure (`legendBottom - svgBottom = 0`). Nothing is clipped; there is no spare padding.
- The gauge keeps its own margin override (`l=18, r=18, t=46, b=8`), tuned earlier and
  verified non-clipped; it is the only chart outside `chart_layout` margins.

## Evidence

- `scratch/sdd-chart-legibility/final-1280-motor.png`
- `scratch/sdd-chart-legibility/final-1280-flota.png`
- `scratch/sdd-chart-legibility/final-1280-auditoria.png`
- `scratch/sdd-chart-legibility/final-1280-casos.png`
- Superseded intermediate captures: `after-*.png`, `defect-ytitle-*.png`

## Verdict

**PASS** — gate has no new failures, the four visual defect classes are gone at both
viewports, and the two deviations are documented above.
