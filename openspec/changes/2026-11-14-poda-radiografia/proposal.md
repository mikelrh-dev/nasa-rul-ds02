# Proposal: Prune the four lowest-value Motor charts

**Change:** `2026-11-14-poda-radiografia`
**Status:** Proposed
**Capabilities:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md) (Modified)

## Intent

The Motor tab carries six Plotly charts. Measured on the frozen cache and scored against
evidentiary value, four of them fall at or below the usefulness threshold: the gauge (2)
duplicates the RUL p35 card and its arc is ambiguous; the per-cycle pressure radiography
(2) is operational noise (sd 5–8 %, correlation with the cycle between −0,07 and −0,02);
the aligned pressure view (3) shows changes at or below the baseline uncertainty
(maximum bin change 2,3 ppt against a ±2,3–3,5 % baseline error); the per-cycle temperature
radiography (5) repeats what the aligned view already shows. Keeping them costs attention
in a fifteen-minute defense without adding a claim. The tab keeps the trajectory with its
conformal band (10), the aligned temperature view (8) and the decision cards (8).

## Scope

### In scope

- Remove the gauge, both per-cycle radiographies and the aligned pressure chart.
- Keep the aligned temperature chart and its caption; keep the measured pressure conclusion
  as one computed text line under it.
- Delete `fig_deriva()` and its plumbing (`AppCtx`, orchestrator wiring) once unused.
- Update the two UI tests that assert the removed surfaces, and the deployed spec.

### Out of scope

- The trajectory chart, the aligned temperature view, thresholds, metrics, rules or any
  artifact. The pressure numbers stay computed, only their presentation changes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `ds02-dss-ui`: the "Physical sensor radiography" requirement drops the per-cycle view,
  keeps the cross-unit aligned view and states why the pressure channels are reported as a
  conclusion instead of a curve.

## Approach

Source-driven: the consolidated card is rebuilt with the badge, the three decision metrics
and the hangar lifecycle; the radiography card renders the aligned temperature figure plus
a `st.caption` whose sentence is built from the same aligned summary. `fig_deriva()` is
removed together with its `AppCtx` field and the orchestrator imports, so no dead helper
survives. Tests are updated first: they must fail while the old surfaces exist.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/ui/_tab_motor.py` | Modify | gauge and per-cycle blocks removed, aligned pressure block removed, pressure note added |
| `app/lib/theme.py` | Modify | `fig_deriva()` deleted; `resumen_criterio()` helper added |
| `app/entrypoints/dashboard_ds02.py`, `app/lib/context.py` | Modify | `fig_deriva` plumbing removed |
| `tests/test_dss_interaction.py`, `tests/test_radioografia_alineada.py` | Modify | assertions for the removed surfaces replaced |
| `app/README.md` | Modify | helper list updated |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| The deployed spec required the per-cycle view | Certain | MODIFIED delta with the measurement that motivated the removal; archive warns before merging |
| A reviewer expects sensor charts | Medium | the aligned temperature view and the pressure conclusion remain; rubric PIA asks for test metrics and real-vs-predicted, both present |
| Removing `fig_deriva` breaks an unnoticed caller | Low | grep shows only `_tab_motor.py`; UI suites run after the change |
| Losing the raw-signal honesty layer | Medium | the pressure note states that no channel meets the criterion and why |

## Rollback Plan

`git revert` the apply commit. Only the Motor tab, `theme.py`, the orchestrator wiring, the
README and the affected tests change.

## Dependencies

Repository virtualenv and pytest. No new dependency.

## Success Criteria

- [ ] The Motor tab renders the trajectory, the aligned temperature view and no other
      Plotly figure; the gauge is gone.
- [ ] The pressure conclusion appears as one computed text line with the measured figures.
- [ ] No reference to `fig_deriva` remains in `app/` outside archived specs.
- [ ] `python -m pytest tests -q` green except the three pre-existing MLflow failures.
