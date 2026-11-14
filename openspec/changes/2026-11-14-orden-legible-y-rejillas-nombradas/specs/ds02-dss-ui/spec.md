# Delta for ds02-dss-ui

**Change:** `2026-11-14-orden-legible-y-rejillas-nombradas`
**Status:** Proposed
**Capability:** `ds02-dss-ui` (Added)

Presentation only: the exported documents and every metric stay untouched.

## ADDED Requirements

### Requirement: Readable work-order preview and honest hangar countdown

The work-order preview SHALL present human-readable columns in title case. It SHALL NOT
expose internal serialization: the evaluated-window metadata SHALL be rendered as text
(cycle, rows, step) instead of a raw object. The preview SHALL keep every field that
justifies the grounding — estimated RUL, band limits, real RUL when recorded, and the
assigned action — and SHALL state an alt text describing it.

The fleet panel SHALL tell an engine already below the hangar threshold apart from one
approaching it: for a unit whose current lower bound is below the threshold, the countdown
SHALL read «ya por debajo del umbral» and SHALL NOT report a positive number of cycles.
For a unit approaching the threshold, the countdown SHALL report whole cycles; for a unit
that never crosses inside the recorded life, it SHALL say so.

#### Scenario: No internal serialization reaches the preview

- GIVEN a blocked unit with its evaluated-window metadata
- WHEN the preview renders
- THEN the window column shows cycle, rows and step as text
- AND no cell contains braces or JSON keys
- AND the headers are title case

#### Scenario: A grounded unit is not counted as approaching

- GIVEN a unit whose current `L_inf` is below the hangar threshold
- WHEN the countdown line renders
- THEN it states the unit is already below the threshold
- AND it does not report a positive number of cycles

### Requirement: Named data grids

Every read-only data grid SHALL be announced by a name. The dashboard SHALL declare an alt
text on each grid; because Streamlit 1.66 does not publish that alt on the grid container,
every grid that is not already inside a titled card or expander SHALL render a visible label
immediately above it. Editable grids are inputs, not read-only grids, and follow their own
contract.

#### Scenario: An unnamed grid gets a visible label

- GIVEN a read-only grid rendered outside a titled card or expander
- WHEN it renders
- THEN a bold label sits immediately above it
- AND the grid declares an alt text

#### Scenario: Every grid declares its description

- GIVEN any `st.dataframe` call in the dashboard
- WHEN the source is reviewed
- THEN the call passes an `alt` argument

## REMOVED Requirements

None.

## RENAMED Requirements

None.

## MODIFIED Requirements

None.

## No delta

- `rul-prediction-ds02`, `ds02-live-evaluation`, `fleet-registries-session`,
  `shap-c-explanation`: None.
