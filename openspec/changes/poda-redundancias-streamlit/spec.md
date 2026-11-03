# Spec delta: pruning redundant Streamlit sections

**Change:** `poda-redundancias-streamlit`
**Status:** Implemented

## MODIFIED

### Requirement: Audit tail merged into audit body

The audit tab SHALL present quality metrics and provenance exactly once, inside
the existing audit body; no second `with tab_auditoria:` block SHALL re-render
them.

### Requirement: Fleet KPIs shown once

The fleet tab SHALL NOT re-render the monitored-units / grounded-units KPIs
already shown in the header; the header remains the single source.

### Requirement: Single MAE in critical zone

`MAE en zona crítica` SHALL be rendered exactly once, in Auditoría. Header and
Flota SHALL NOT render it.

### Requirement: Single operating-conditions visualisation

Operating conditions SHALL be visualised only in Motor (radiography). Auditoría
SHALL NOT duplicate them.

### Requirement: Single scenario entry point

Only `Cargar escenario demo` SHALL remain as the narrative scenario entry point;
`Modo historia` is removed.

## Preserved (PIA rubric)

- Test metrics from cached predictions (RMSE, MAE, bias, per-engine, by band).
- Real-vs-predicted chart and conformal band.
- New-case prediction with rule decision and p, in Casos nuevos.
" path="openspec/changes/poda-redundancias-streamlit/spec.md"><|end|><|start|> assistant to=write_file<|channel|>analysis <|constrain|>xml<|message|><rfl:parameter name="content">
# Design: pruning redundant Streamlit sections

**Change:** `poda-redundancias-streamlit`
**Status:** Implemented

## Edit plan

- `app/dashboard_ds02.py` only.
- Merge audit-tail `Calidad del modelo` (Macro-RMSE + MAE zona crítica) into a
  new container inside the audit body, before `Procedencia verificable`; merge
  `Ventanas en caché` metric + contract caption into `Procedencia verificable`.
- Remove header `MAE en zona crítica` metric from `Primera lectura`.
- Remove fleet footer `with st.container(horizontal=True)` KPI block.
- Remove audit operating-conditions duplicate block.
- Remove `Modo historia` container; keep `Cargar escenario demo`.

## Risks

- Chart/grid counts in `test_every_chart_and_grid_has_an_accessible_name`
  (`>=6` charts, `>=7` grids). Verified green after edits.
- `critical_mae` still computed and used by PDF; variable kept.
" path="openspec/changes/poda-redundancias-streamlit/design.md"><|end|><|start|> assistant to=write_file<|channel|>analysis <|constrain|>xml<|message|><rfl:parameter name="content">
# Tasks: pruning redundant Streamlit sections

**Change:** `poda-redundancias-streamlit`
**Status:** Implemented

| # | Task | Status | Acceptance |
|---|---|---|---|
| 1.1 | Create SDD change dir + artifacts | Done | dir exists |
| 2.1 | Remove audit tail and merge into audit body | Done | no second `with tab_auditoria:` |
| 2.2 | Remove fleet footer metrics | Done | block gone |
| 2.3 | Remove header MAE metric | Done | single MAE in audit |
| 2.4 | Remove audit operating-conditions duplicate | Done | ops plot only in Motor |
| 2.5 | Remove Modo historia, keep demo scenario | Done | one entry point |
| 3.1 | Run pytest target suite | Done | 78 passed, 3 skipped |
" path="openspec/changes/poda-redundancias-streamlit/tasks.md">
