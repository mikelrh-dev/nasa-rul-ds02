# Tasks: Life-aligned sensor radiography across test units

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 230–280 (two helpers ~100, wiring ~30, new test file ~120) |
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
| 1 | Aligned frame from the cache | PR 1 (only) | `python -m pytest tests/test_radioografia_alineada.py -q` | Playwright render of the Motor tab | revert one commit: `app/lib/ui_data_loader.py`, `app/lib/theme.py`, `app/ui/_tab_motor.py`, `tests/` |
| 2 | Figure and caption with measured figures | PR 1 (only) | same plus `tests/test_ui_chart_chrome.py` | same render at 1280/560 px | same single commit |

## Phase 1: RED tests

- [x] 1.1 Create `tests/test_radioografia_alineada.py`: `drift_por_rul` returns unit, cycle, rul, canal, deriva with baseline equal to each unit's first five cycles. Acceptance: RED.
- [x] 1.2 Assert the measured finding holds on this cache: T50 and T48 move more than 0.5 ppt between the first and last RUL bin; every pressure channel moves less than 0.5 ppt. Acceptance: RED.
- [x] 1.3 Assert the highlight set is exactly the channels with `abs(corr(deriva, rul)) >= 0.3`. Acceptance: RED.
- [x] 1.4 Assert `fig_deriva_vida` draws one trace per selected channel, marks the critical band and highlights the flagged channels. Acceptance: RED.
- [x] 1.5 Record the failure list with `pytest tests/test_radioografia_alineada.py -q`.

## Phase 2: Aligned frame loader

- [x] 2.1 `app/lib/ui_data_loader.py`: add `drift_por_rul(channels, bin_width=10)` computing per-unit per-cycle drift against its own baseline and joining the real RUL.
- [x] 2.2 Aggregate by RUL bin across units and compute the summary (first/last bin means, correlation, highlight flag).
- [x] 2.3 Acceptance: `pytest tests/test_radioografia_alineada.py -q` green for 1.1–1.3.

## Phase 3: Figure helper

- [x] 3.1 `app/lib/theme.py`: add `fig_deriva_vida(frame, summary, threshold_aog, height)` using `chart_layout` and `CHART_CONFIG`.
- [x] 3.2 Mark the critical band `RUL < threshold_aog` and highlight the flagged channels.
- [x] 3.3 Acceptance: 1.4 green.

## Phase 4: Wiring and caption

- [x] 4.1 `app/ui/_tab_motor.py`: render the aligned view under the per-cycle radiography, for the selected channel group, with no extra selector.
- [x] 4.2 Caption built from the summary: figures in percentage points, method and source, never literals.
- [x] 4.3 Acceptance: all new tests green plus the existing UI suites.

## Phase 5: Gate and visual evidence

- [x] 5.1 Run `python -m pytest tests -q` and record exit code and counts — 471 passed, 3 pre-existing MLflow failures (baseline 465 passed / 3 failed).
- [x] 5.2 Capture Motor tab at 1280 px and 560 px under `scratch/sdd-radiografia-alineada/` and measure clipping, mode bar and legend clearance on the new chart — `final-1280-motor.png`; both viewports measured, mode bar 0.

## Phase 6: Verify and archive

- [x] 6.1 Write `verify-report.md` with the gate output, the measured geometry and any surviving clip.
- [x] 6.2 Merge the MODIFIED requirement into `openspec/specs/ds02-dss-ui/spec.md` and move the change to `openspec/changes/archive/2026-11-14-radiografia-alineada-vida/`.
