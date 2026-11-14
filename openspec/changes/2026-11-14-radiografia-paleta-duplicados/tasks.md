# Tasks: One palette per channel, duplicate collapse, honest pressure caption

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 120–170 (one module, one test file) |
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
| 1 | Channel identity and collapse | PR 1 (only) | `pytest tests/test_radioografia_alineada.py -q` | Playwright render of Motor | revert one commit: `app/lib/theme.py` + `tests/` |
| 2 | Honest caption | PR 1 (only) | same | same render at 1280/560 px | same single commit |

## Phase 1: RED tests

- [ ] 1.1 Assert `canales_unicos(["P15", "P21", "Ps30", "P40"])` returns four unique bases with labels `P15 · P21` and `Ps30 · P40`, in both input orders. Acceptance: RED.
- [ ] 1.2 Assert the palette assigns a distinct colour to every visible channel code. Acceptance: RED.
- [ ] 1.3 Assert both figures draw one trace per unique channel. Acceptance: RED.
- [ ] 1.4 Assert the pressure caption reports the largest bin change and says the shape is not monotone, and never contains the phrase about flight conditions. Acceptance: RED.
- [ ] 1.5 Record the failure list with `pytest tests/test_radioografia_alineada.py -q`.

## Phase 2: Identity and collapse

- [ ] 2.1 Add `COLOR_CANAL`, `CANALES_DUPLICADOS` and `canales_unicos()` to `theme.py`.
- [ ] 2.2 Apply the palette and the collapse in `fig_deriva`.
- [ ] 2.3 Apply the palette and the collapse in `fig_deriva_vida`.
- [ ] 2.4 Acceptance: 1.1–1.3 green.

## Phase 3: Caption honesty

- [ ] 3.1 Add a `monotono` flag to the aligned summary computed from the bin series sign changes.
- [ ] 3.2 Rebuild the no-drift branch of `caption_deriva_vida` with the largest measured bin change, the monotonicity and the criterion; drop the unsupported causal claim.
- [ ] 3.3 Acceptance: 1.4 green.

## Phase 4: Gate and visual evidence

- [ ] 4.1 Run `python -m pytest tests -q` and record exit code and counts.
- [ ] 4.2 Capture the Motor tab at 1280 px and 560 px under `scratch/sdd-paleta-duplicados/`; confirm five pressure traces, matching colours across views and no clipped text.

## Phase 5: Verify and archive

- [ ] 5.1 Write `verify-report.md` with the gate output, captures and any surviving issue.
- [ ] 5.2 Merge the MODIFIED requirement into `openspec/specs/ds02-dss-ui/spec.md` and move the change to `openspec/changes/archive/2026-11-14-radiografia-paleta-duplicados/`.
