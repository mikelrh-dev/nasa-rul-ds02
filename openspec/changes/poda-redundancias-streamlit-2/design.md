# Design: pruning redundant Streamlit sections (round 2)

**Change:** `poda-redundancias-streamlit-2`
**Status:** Implemented

## Edit plan

- `app/dashboard_ds02.py` only.
- Delete the sidebar `¿Cómo probar con un caso típico?` expander.
- Replace the 7-bullet `Cómo leer esta pantalla` body with a 4-line markdown.
- Move the `Contrato de artefacto congelado` expander from the sidebar to
  Auditoría, after `Contrato congelado vs. cálculo en vivo`.
- Convert the `Procedencia verificable` and `Contrato congelado vs. cálculo
  en vivo` containers into collapsed expanders.

## Risks

- Chart/grid counts in `test_every_chart_and_grid_has_an_accessible_name`
  (`>=6` charts, `>=7` grids). Verified green after edits.
- `test_the_sidebar_explains_the_vocabulary_of_the_screen` still requires the
  `Cómo leer esta pantalla` label and the terms RUL, L_inf, Banda 90 %,
  HANGAR/AOG, Ciclo de vuelo, Ventana. The 4-line body keeps all of them.
- Moved block keeps `manifest`/`provenance` references; both are in scope in
  Auditoría.
