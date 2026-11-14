# Tasks: Numeric precision in the grids and the missing quality metrics

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 160–220 |
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
| 1 | Format and metrics | PR 1 (only) | `pytest tests/test_ui_format.py tests/test_dss_ui.py -q` | Playwright render of Auditoría | revert one commit: `ui_format.py`, loader, three tabs, `tests/` |

## Phase 1: RED tests

- [x] 1.1 Assert the formatters round, add the sign and blank out NaN (`entero`, `tres_decimales`, `con_signo_3`, `cuatro_sig`). Acceptance: RED -> GREEN.
- [x] 1.2 Assert `formatea` replaces the mapped columns and leaves the rest untouched. Acceptance: RED -> GREEN.
- [x] 1.3 Assert `global_metrics(windows)` includes `r2` equal to the manifest value within rounding. Acceptance: RED -> GREEN.
- [x] 1.4 Assert the three tabs contain no leftover `format=` declaration for a numeric column and route formatting through the shared helper. Acceptance: RED -> GREEN.
- [x] 1.5 Assert Auditoría renders MAE ponderado, NASA score and R2 labels. Acceptance: RED -> GREEN.
- [x] 1.6 Record the failure list with the focused command — collection error (module absent), then 11 passed after the helper landed.

## Phase 2: Shared formatter

- [x] 2.1 Add `app/lib/ui_format.py` with the formatters and `formatea`.
- [x] 2.2 Acceptance: 1.1 and 1.2 green.

## Phase 3: Metrics

- [x] 3.1 Add `r2` to `global_metrics`.
- [x] 3.2 Render MAE ponderado, NASA score and R2 in the quality card of Auditoría.
- [x] 3.3 Acceptance: 1.3 and 1.5 green.

## Phase 4: Apply to the grids

- [x] 4.1 Format the Auditoría grids (tramos, alarma, Δ/Prioridad).
- [x] 4.2 Format the Casos grids (lote, tramo, envolvente), preserving `help`; the editable editors keep their numeric dtype so values stay typable.
- [x] 4.3 Format the Flota grids (trayectoria, registro, hangar).
- [x] 4.4 Acceptance: 1.4 green; affected suites 131 passed with no collateral updates needed.

## Phase 5: Gate and visual evidence

- [x] 5.1 Run `python -m pytest tests -q` and record exit code and counts — 488 passed, 3 pre-existing MLflow failures.
- [x] 5.2 Capture Auditoría, Casos and Flota at 1280 px under `scratch/sdd-formato-metricas/`; confirm no raw float64 cell and the three new cards — five captures saved, zero raw cells in read-only grids, three cards measured.

## Phase 6: Verify and archive

- [x] 6.1 Write `verify-report.md` with the gate output, captures and any surviving issue.
- [x] 6.2 Merge the MODIFIED and ADDED requirements into `openspec/specs/ds02-dss-ui/spec.md` and move the change to `openspec/changes/archive/2026-11-14-formato-tablas-metricas/`.
