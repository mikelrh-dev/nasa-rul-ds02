# Tasks: One screen, no Vista switch

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 60–90 |
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
| 1 | Remove the switch | PR 1 (only) | `pytest tests/test_dss_interaction.py -q` | Playwright render of the sidebar | revert one commit: six files, `tests/` |

## Phase 1: RED contracts

- [x] 1.1 Replace the switch-driven test with one asserting no «Vista» segmented control exists. Acceptance: RED -> GREEN.
- [x] 1.2 Assert session log and rule trace are always present in the single screen. Acceptance: RED while gated -> GREEN.
- [x] 1.3 Assert the sandbox expander starts expanded. Acceptance: guard against regression (ya pasaba por el modo por defecto).
- [x] 1.4 Record the failure list — 1 failed (el control seguía existiendo), 52 passed tras aplicar.

## Phase 2: Remove the switch

- [x] 2.1 Drop the widget, the flag, the context field and the three read sites.
- [x] 2.2 Dedent the gated Flota blocks; set the sandbox default.
- [x] 2.3 Acceptance: 1.1–1.3 green — 52 passed en las suites afectadas.

## Phase 3: Gate and visual evidence

- [x] 3.1 Run `python -m pytest tests -q` and record exit code and counts — 495 passed, 3 pre-existing MLflow failures.
- [x] 3.2 Capture the sidebar and confirm no Vista control and all sections present — capture saved, sidebar starts at «Unidad de test», rule trace and session log visible.

## Phase 4: Verify and archive

- [ ] 4.1 Write `verify-report.md` with the gate output, captures and any surviving issue.
- [ ] 4.2 Archive the change under `openspec/changes/archive/2026-11-14-una-sola-pantalla/`.
