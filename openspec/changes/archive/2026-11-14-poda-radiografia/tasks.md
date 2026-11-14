# Tasks: Prune the four lowest-value Motor charts

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 180–240 (removals dominate; one helper added, tests updated) |
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
| 1 | Prune and report | PR 1 (only) | `pytest tests/test_dss_interaction.py tests/test_radioografia_alineada.py -q` | Playwright render of Motor | revert one commit: `app/ui/_tab_motor.py`, `app/lib/theme.py`, wiring, `tests/` |

## Phase 1: RED tests for the pruned surface

- [x] 1.1 Replace the gauge accessibility assertion with one asserting no plotly chart declares a gauge. Acceptance: RED -> GREEN.
- [x] 1.2 Replace the per-cycle radiography assertion with one asserting the aligned temperature view is present. Acceptance: RED -> GREEN.
- [x] 1.3 Add a contract test: `_tab_motor.py` builds neither a gauge Indicator nor a per-cycle figure. Acceptance: RED -> GREEN.
- [x] 1.4 Add the pressure-note contract: measured magnitude and monotonicity, no causal claim. Acceptance: RED -> GREEN.
- [x] 1.5 Record the failure list with `pytest tests/test_dss_interaction.py tests/test_radioografia_alineada.py -q` — 4 failed, 23 passed.

## Phase 2: Prune the card

- [x] 2.1 Remove the gauge column and the two per-cycle radiography blocks from `_tab_motor.py`.
- [x] 2.2 Render the aligned temperature figure and the pressure note from the same summary.
- [x] 2.3 Acceptance: 1.1–1.4 green — 34 passed in the focused suite.

## Phase 3: Remove the dead helper

- [x] 3.1 Delete `fig_deriva()` from `theme.py` and add `resumen_criterio()`.
- [x] 3.2 Drop the `fig_deriva` import and context construction in `dashboard_ds02.py` and the `AppCtx` field.
- [x] 3.3 Update `app/README.md`; acceptance: no `fig_deriva` reference remains outside archived specs.

## Phase 4: Gate and visual evidence

- [x] 4.1 Run `python -m pytest tests -q` and record exit code and counts — 477 passed, 3 pre-existing MLflow failures.
- [x] 4.2 Capture the Motor tab at 1280 px and 560 px under `scratch/sdd-poda-radiografia/`; confirm which figures render — two captures saved, gauge absent, only T24/T2/T50 traces.

## Phase 5: Verify and archive

- [x] 5.1 Write `verify-report.md` with the gate output, captures and any surviving issue.
- [x] 5.2 Merge the MODIFIED requirement into `openspec/specs/ds02-dss-ui/spec.md` and move the change to `openspec/changes/archive/2026-11-14-poda-radiografia/`.
