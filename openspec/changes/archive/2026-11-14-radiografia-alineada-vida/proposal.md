# Proposal: Life-aligned sensor radiography across test units

**Change:** `2026-11-14-radiografia-alineada-vida`
**Status:** Proposed
**Capabilities:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md) (Modified)

## Intent

The radiography plots the per-cycle drift of the selected channels for one engine.
Measured on the frozen cache, most channels carry no trend at all (pressures have
`|corr| < 0.06` against the fraction of life); only T50 (+1.54 ppt) and T48 (+1.28 ppt)
drift, averaged over the three test units. As presented, the panel reads as "nothing
moves", which demonstrates nothing and invites the question of why the decision relies on
sensors. This change adds a second, cross-unit view aligned by real RUL so the one real
signal becomes visible, and states the measured finding in the caption instead of letting
the curve speak for itself.

## Scope

### In scope

- Loader helper: per-channel drift relative to each unit's own five-cycle baseline,
  joined to the real RUL of the cycle, aggregated by RUL bins over the three test units.
- Figure helper: drift versus RUL, selected channels, T50/T48 highlighted, critical band
  marked, shared Plotly chrome.
- Wiring in the Motor tab, directly under the existing per-cycle radiography, same card.
- Caption carrying the measured figures, their method and their source.

### Out of scope

- Any change to the per-cycle radiography, still required by the deployed spec.
- Residualisation (removing operating conditions): documented as deferred and blocked by
  TensorFlow being forbidden in render.
- Any metric, threshold, rule, artifact or triage change.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `ds02-dss-ui`: extends "Physical sensor radiography" with the RUL-aligned aggregate view
  and its measured statement.

## Approach

Pure pandas over `app/cache/`, no model load and no TensorFlow: for each test unit, the
per-cycle mean of the selected channels, baseline = mean of its first five cycles, drift =
`(value / baseline - 1) * 100`, joined to the real RUL of that cycle from
`ds02_windows`. Values are binned by RUL and averaged across units, then drawn with the
shared Plotly layout and config. The numbers in the caption are computed from the same
frame at render time, never hardcoded.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/lib/ui_data_loader.py` | Modified | drift/RUL join and aggregate helper |
| `app/lib/theme.py` | Modified | `fig_deriva_vida` figure helper |
| `app/ui/_tab_motor.py` | Modified | second chart plus caption |
| `tests/test_radioografia_alineada.py` | New | behaviour and contract tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| The T50/T48 effect is small (~1.5 ppt) and still reads as weak | Medium | caption states the magnitude honestly instead of overselling it; the per-cycle view stays for context |
| Telemetry covers only the three test units | Low | stated in the caption as "media de las tres unidades test" |
| A cache schema change breaks the helper | Low | tests assert columns and baseline semantics against the frozen cache |

## Rollback Plan

`git revert` the apply commit. Only the two library modules, `_tab_motor.py` and the new
test file are touched; no artifact, cache or registry file is written.

## Dependencies

Repository virtualenv and pytest; the frozen `app/cache/` tables. No new dependency.

## Success Criteria

- [ ] The Motor tab renders a RUL-aligned aggregate view under the per-cycle radiography.
- [ ] T50 and T48 highlighted, critical band marked, no mode bar, no clipped text
      (Playwright at 1280 px and 560 px).
- [ ] The caption carries figures computed from the data, with method and source.
- [ ] `python -m pytest tests -q` green except the three pre-existing MLflow failures.
