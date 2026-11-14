# Delta for ds02-dss-ui

**Change:** `2026-11-14-formato-tablas-metricas`
**Status:** Proposed
**Capability:** `ds02-dss-ui` (Modified + Added)

Presentation and metric coverage only: no metric value, threshold, rule, cache row or
artifact hash changes. The new cards compute the same quantities the frozen manifest
records.

## MODIFIED Requirements

### Requirement: Live metrics from cached predictions

Every metric shown SHALL be computed from the cached predictions and their
ground truth: window-weighted RMSE, macro-RMSE, per-engine RMSE, MAE and bias, the
MAE per true-RUL band `[0, 25)`, `[25, 50)`, `[50, 75)`, the NASA score and the
coefficient of determination R2. The UI SHALL NOT hardcode any metric value.

The quality card SHALL present the window-weighted MAE, the NASA score and R2 together
with the macro and weighted RMSE, each labelled as a live computation from the cache so a
reader never confuses them with a recorded figure.

The manifest SHALL be displayed separately, clearly labelled as the frozen
artifact contract, so a reader can tell a live computation from a recorded one.

#### Scenario: Per-engine cards agree with the cache

- GIVEN the cached windows of unit 14
- WHEN its RMSE card is rendered
- THEN the value equals `sqrt(mean((pred - y_true)**2))` over those rows
- AND it is not taken from a literal in the source

#### Scenario: The quality contract is readable at a glance

- GIVEN the cached windows of the three test units
- WHEN the quality card renders
- THEN it shows window-weighted MAE, NASA score and R2 next to the macro and weighted RMSE
- AND each value equals the same quantity computed from `app/cache/` within rounding

#### Scenario: Manifest figures are labelled as recorded

- GIVEN the manifest audit card
- WHEN it shows the macro per-engine RMSEs
- THEN the values are the ones stored in `models/ds02_manifest.json`
- AND the card states that they come from the frozen contract, not from the cache

#### Scenario: The bands do not silently disagree

- GIVEN the live per-engine RMSE and the manifest's macro per-engine RMSE for the
  same unit
- WHEN both are visible
- THEN the difference, if any, is explained as regeneration drift
- AND neither figure is edited to match the other

## ADDED Requirements

### Requirement: Numeric precision in data grids

Every numeric cell rendered by a data grid SHALL show bounded precision: at most three
decimals for errors and sensor quantities, four significant digits for observed-envelope
limits, one decimal for cycles and RUL when so declared, thousands-free integers for
counts, and an explicit sign for bias and delta columns. A raw float64 artifact such as
«1.2472739948605471» SHALL NOT reach a grid.

A grid column whose values have been pre-formatted for display SHALL be declared as a
text column, so the declared type matches what is actually rendered. The presentation
contract SHALL live in one shared helper used by every tab, not in per-tab literals.

#### Scenario: The precision-by-band grid is readable

- GIVEN the MAE and bias per true-RUL band
- WHEN the grid renders
- THEN the MAE cell reads «1.247» and the Sesgo cell reads «+0.722»
- AND no cell in that grid shows more than three decimals

#### Scenario: One owner for the presentation contract

- GIVEN the three tabs that render numeric grids
- WHEN the grids render
- THEN every formatted column is produced by the shared helper
- AND no tab declares a number format that the grid engine cannot apply

## REMOVED Requirements

None.

## RENAMED Requirements

None.

## No delta

- `rul-prediction-ds02`, `ds02-live-evaluation`, `fleet-registries-session`,
  `shap-c-explanation`: None.
