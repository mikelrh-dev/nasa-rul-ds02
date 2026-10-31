# Spec delta: interactive "explore by cycle" on live evaluation

**Change:** `2026-10-31-ds02-explorar-por-ciclo`
**Capability:** `ds02-live-evaluation` (modified)

## MODIFIED

### Requirement: interactive exploration by cycle

The live-evaluation surface SHALL let the visitor pick an engine and an end point
and generate a tramo on demand, without preparing a CSV or editing a grid, and
SHALL show the computed state for that tramo before any scoring.

The block SHALL reuse `example_window` / `window_ending_at` and SHALL NOT call
`score_table` while the control moves; scoring SHALL happen only on an explicit
button.

#### Scenario: a valid table is generated for any engine and position

- GIVEN the exploration block
- WHEN the visitor selects engine 14 and position 0.5
- THEN a table with at least `window_size` rows and the 19 columns (cycle + 18
  channels) in dataset order is produced
- AND no scoring has happened yet

#### Scenario: the preview shows the computed state

- GIVEN a generated tramo
- WHEN the preview renders
- THEN it shows the cycles covered, the row count and the triage state computed
  from that tramo
- AND no RMSE/MAE figure is shown

#### Scenario: evaluating the tramo works

- GIVEN a generated tramo
- WHEN "Evaluar este tramo" is pressed
- THEN a point estimate, a conformal band and a triage state appear
- AND, on block, a work order is available

#### Scenario: the presets are untouched

- GIVEN the three canonical presets
- WHEN the exploration block is used
- THEN Sano still yields APTO, Medio INSPECCIÓN and Crítico HANGAR
- AND their tests still pass

#### Scenario: nothing is persisted

- GIVEN an exploration and an evaluation
- WHEN they finish
- THEN no file under `models/` or `app/cache/` has changed
", "path">
openspec/changes/2026-10-31-ds02-explorar-por-ciclo/spec.md