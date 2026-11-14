# Delta for ds02-dss-ui

**Change:** `2026-11-14-streamlit-chart-legibility`
**Status:** Proposed
**Capability:** `ds02-dss-ui` (Modified)

This change alters presentation only. No metric, threshold, rule, cache row, artifact
hash or triage outcome changes. The NASA score remains a SUM of asymmetric exponentials
and the DS02 path keeps applying no 125-cycle clamp.

## ADDED Requirements

### Requirement: Chart text stays inside its viewport

Every Plotly figure rendered by the dashboard SHALL draw its axis tick labels, axis
titles and annotations fully inside the figure viewport, and SHALL NOT overlap them with
each other or with the plotting area. The legend SHALL be placed below the plotting area
and SHALL NOT cover any trace.

#### Scenario: Axis titles and ticks are fully visible

- GIVEN any chart of the dashboard at a 1280 px and at a 560 px viewport width
- WHEN the chart finishes rendering
- THEN every axis title and every tick label is fully contained in the figure viewport
- AND no axis text overlaps another element

#### Scenario: The legend does not cover the traces

- GIVEN a chart with several named series
- WHEN the legend is drawn
- THEN the legend sits below the plotting area
- AND no legend line intersects a trace

#### Scenario: A shortened axis title keeps its meaning

- GIVEN an axis whose descriptive title was shortened for space
- WHEN the chart is displayed
- THEN the full wording remains available in the adjacent caption text

### Requirement: Shared Plotly chrome configuration

The dashboard SHALL define exactly one Plotly config constant owned by
`app/lib/theme.py`, with the floating mode bar disabled. Every `st.plotly_chart` call
SHALL pass that constant and SHALL NOT rely on the Streamlit default config.

#### Scenario: No floating mode bar

- GIVEN any chart of the dashboard
- WHEN the page is inspected in a real browser
- THEN no Plotly mode bar element is present over the chart area

#### Scenario: One config owner

- GIVEN the application source
- WHEN the `st.plotly_chart` calls are inspected
- THEN each one passes the shared config constant
- AND no second Plotly config literal exists

### Requirement: Audit band table headers

The audit tab SHALL render the MAE-by-band table with exactly four columns, all with
Spanish display headers, and SHALL NOT duplicate a raw DataFrame column under its
untranslated name.

#### Scenario: Four Spanish columns

- GIVEN the cached windows
- WHEN the band table renders
- THEN the columns are Tramo, Ventanas, MAE and Sesgo
- AND no column header shows a raw field name such as `band`

#### Scenario: Values are unchanged

- GIVEN the same cache before and after the change
- WHEN the table values are compared
- THEN every cell equals its previous value

## MODIFIED Requirements

None. No existing requirement is violated today: none of them asserts clipped text, an
overlapping legend or a duplicated column.

## REMOVED Requirements

None.

## RENAMED Requirements

None.

## No delta

- `rul-prediction-ds02`, `ds02-live-evaluation`, `fleet-registries-session`,
  `shap-c-explanation`, `ds02-n8n-decision`: None. The change writes no artifact and
  touches no contract they own.
