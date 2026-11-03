# Spec delta: pruning redundant Streamlit sections (round 2)

**Change:** `poda-redundancias-streamlit-2`
**Status:** Implemented

## MODIFIED

### Requirement: No "cómo probar" help expander in the sidebar

The sidebar SHALL NOT render the `¿Cómo probar con un caso típico?` expander.
Unit and cycle controls remain the entry point.

### Requirement: Compact screen glossary

The sidebar `Cómo leer esta pantalla` expander SHALL contain at most 4 lines
and SHALL still mention `RUL`, `L_inf`, `Banda 90 %`, `HANGAR/AOG`,
`Ciclo de vuelo` and `Ventana`.

### Requirement: Artifact contract lives in Auditoría

The `Contrato de artefacto congelado` expander SHALL be rendered in the
Auditoría tab, not in the sidebar.

### Requirement: Collapsible provenance surfaces

In Auditoría, `Procedencia verificable` and `Contrato congelado vs. cálculo
en vivo` SHALL be collapsed expanders (not always-open containers).

## Preserved (PIA rubric)

- Test metrics from cached predictions (RMSE, MAE, bias, per-engine, by band).
- Real-vs-predicted chart and conformal band.
- New-case prediction with rule decision and p, in Casos nuevos.
