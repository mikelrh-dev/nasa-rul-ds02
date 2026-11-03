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
" path="openspec/changes/poda-redundancias-streamlit/design.md">
