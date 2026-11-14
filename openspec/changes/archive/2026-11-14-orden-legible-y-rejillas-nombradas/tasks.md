# Tasks: Readable order preview, honest hangar countdown, named grids

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 90–140 |
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
| 1 | Three presentation fixes | PR 1 (only) | `pytest tests/test_vista_orden.py -q` | Playwright render of Flota y Casos | revert one commit: six files, `tests/` |

## Phase 1: RED contracts

- [x] 1.1 Assert `tabla_orden` returns title-case headers and no braces in any cell. Acceptance: RED -> GREEN.
- [x] 1.2 Assert `tabla_orden` keeps every blocking field (estimated RUL, both limits, action). Acceptance: RED -> GREEN.
- [x] 1.3 Assert `resumen_ciclos_hasta_fallo` says «ya por debajo» for a unit already under the threshold and never returns a positive number for it. Acceptance: RED -> GREEN.
- [x] 1.4 Assert `resumen_ciclos_hasta_fallo` keeps «nunca…» and «N ciclos» for the other cases. Acceptance: RED -> GREEN.
- [x] 1.5 Assert every `st.dataframe(` call in `app/ui` passes `alt=`. Acceptance: RED (`_paneles.py`) -> GREEN.
- [x] 1.6 Record the failure list — collection error (module absent), then 5 passed after the helpers landed.

## Phase 2: Helpers

- [x] 2.1 Add `app/lib/vista_orden.py` and `simulacion.resumen_ciclos_hasta_fallo`.
- [x] 2.2 Add `theme.nombra_grid`.
- [x] 2.3 Acceptance: 1.1–1.4 green.

## Phase 3: Wire the UI

- [x] 3.1 Use `tabla_orden` in the Flota order preview.
- [x] 3.2 Use the countdown summary in the fleet caption.
- [x] 3.3 Label the batch triage grid and the order preview; add `alt` to the SHAP grid.
- [x] 3.4 Acceptance: 1.5 green — affected suites 101 passed.

## Phase 4: Gate and visual evidence

- [x] 4.1 Run `python -m pytest tests -q` and record exit code and counts — 494 passed, 3 pre-existing MLflow failures.
- [x] 4.2 Capture Flota at cycle 31 (blocked units) and Casos; confirm readable preview, honest countdown and labels — capture saved, no braces, «ya por debajo» for U11/U15, label verified live (Flota) and by integration test (Casos).

## Phase 5: Verify and archive

- [x] 5.1 Write `verify-report.md` with the gate output, captures and any surviving issue.
- [x] 5.2 Merge the added requirements into `openspec/specs/ds02-dss-ui/spec.md` and move the change to `openspec/changes/archive/2026-11-14-orden-legible-y-rejillas-nombradas/`.
