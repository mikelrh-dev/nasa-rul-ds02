# Delta for shap-c-explanation

**Change:** `2026-11-06-app-fixes-1`
**Capability:** `shap-c-explanation` (bundle C, manifest 4.338, seed 42, read-only)

## ADDED Requirements

### Requirement: SHAPC-WF-01

The system MUST build the Plotly waterfall via `shap_waterfall_fig` without raising, passing `totals` as a scalar number (never a list) and carrying top-`max_display` contributions. The NASA score is a SUM of asymmetric exponentials with no 125-cycle clamp on DS02; this requirement changes no metric.

#### Scenario: Waterfall builds with data

- GIVEN a unit with cache rows and the frozen bundle
- WHEN `shap_waterfall_fig(unit)` runs
- THEN no `ValueError` is raised
- AND the figure carries one trace with non-empty `x`/`y`

#### Scenario: Scalar totals

- GIVEN the waterfall inputs `(sv, base, names)`
- WHEN the `go.Waterfall` is constructed
- THEN `totals` is `float(base)`
- AND `measure` is `relative` for each contribution
