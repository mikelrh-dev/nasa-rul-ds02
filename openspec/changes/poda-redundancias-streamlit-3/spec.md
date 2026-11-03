# Spec delta: pruning redundant Streamlit sections (round 3)

**Change:** `poda-redundancias-streamlit-3`
**Status:** Implemented

## MODIFIED

### Requirement: Fleet chronology collapsed by default

`Cronología de estado de flota` SHALL be a collapsed expander by default.

### Requirement: Hangar cards show state + L_inf only

Each hangar card SHALL render the state badge and the `L_inf (decide)` metric;
it SHALL NOT render the `RUL p35 (conservadora)` metric nor the per-card
sparkline.

### Requirement: Maintenance queue collapsed by default

`Cola de mantenimiento · tabla por unidad` SHALL be a collapsed expander.

### Requirement: Column glossary collapsed by default

`Qué es cada columna y qué rango es normal` SHALL be a collapsed expander.

### Requirement: Sandbox and demo collapsed in Turno view

`Sandbox de estrés` and `Demo en vivo` SHALL be expanders whose expanded state
follows `_vista_tribunal` (open in Tribunal, collapsed in Turno).

## Preserved (PIA rubric)

- Test metrics from cached predictions (RMSE, MAE, bias, per-engine, by band).
- Real-vs-predicted chart and conformal band.
- New-case prediction with rule decision and p, in Casos nuevos.
