# Tasks: Streamlit chart legibility and fixed chrome

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 150–230 (one new test file ~110 plus nine small edits) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | single commit |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Shared layout and config owners in `theme.py` | PR 1 (only) | `python -m pytest tests/test_ui_chart_chrome.py -q` | Playwright capture at 1280/560 px | revert one commit: `app/lib/theme.py` + `tests/` |
| 2 | Adopt the owners in every tab and shorten labels | PR 1 (only) | `python -m pytest tests/test_ui_chart_chrome.py tests/test_app_ux_bundle.py -q` | same captures | same single commit |

## Phase 1: RED contract tests

- [x] 1.1 Create `tests/test_ui_chart_chrome.py` asserting `chart_layout()` returns margins `l >= 56` and `b >= 64` and `xaxis`/`yaxis` `automargin=True`. Acceptance: RED against current `theme.py`.
- [x] 1.2 Add an AST test: `app/lib/theme.py` defines `CHART_CONFIG` with `displayModeBar=False`, and every `st.plotly_chart` call under `app/` passes it. Acceptance: RED.
- [x] 1.3 Add an AST test: `app/ui/_tab_auditoria.py` renames the band column and contains no `assign(Tramo=...)`. Acceptance: RED.
- [x] 1.4 Record the failure list with `python -m pytest tests/test_ui_chart_chrome.py -q`.

## Phase 2: Shared layout owner

- [x] 2.1 `app/lib/theme.py`: `margin=dict(l=56, r=16, t=44, b=64)` and legend `orientation="h", yanchor="top", y=-0.16, x=0`.
- [x] 2.2 `app/lib/theme.py`: `xaxis=dict(automargin=True)`, `yaxis=dict(automargin=True)` inside `chart_layout`.
- [x] 2.3 `app/lib/theme.py`: export `CHART_CONFIG = {"displayModeBar": False}`.
- [x] 2.4 Acceptance: `python -m pytest tests/test_ui_chart_chrome.py -q` green for 1.1 and the `CHART_CONFIG` half of 1.2.

## Phase 3: Adoption and labels

- [x] 3.1 `app/ui/_tab_motor.py`: pass `config=CHART_CONFIG`; shorten the radiography `y_title` and the series names in the trajectory legend.
- [x] 3.2 `app/ui/_tab_flota.py`, `app/ui/_tab_casos.py`, `app/ui/_paneles.py`, `app/ui/_sandbox_estres.py`: pass `config=CHART_CONFIG`.
- [x] 3.3 `app/ui/_tab_auditoria.py`: pass `config=CHART_CONFIG`; use `rename(columns={"band": "Tramo"})` and drop the duplicated column.
- [x] 3.4 Acceptance: 1.2 and 1.3 green.

## Phase 4: GREEN gate and visual evidence

- [x] 4.1 Run `python -m pytest tests -q` and record exit code and counts — 465 passed, 3 pre-existing MLflow failures (identical to the pre-change baseline of 458 passed / 3 failed).
- [ ] 4.2 Capture before/after screenshots at 1280 px and 560 px for the Motor, Flota and Auditoría tabs under `scratch/sdd-chart-legibility/`.

## Phase 5: Verify and archive

- [ ] 5.1 Write `verify-report.md` with the gate output, the capture paths and any surviving clip.
- [ ] 5.2 Merge the delta into `openspec/specs/ds02-dss-ui/spec.md` and move the change to `openspec/changes/archive/2026-11-14-streamlit-chart-legibility/`.
