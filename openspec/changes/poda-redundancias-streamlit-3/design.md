# Design: pruning redundant Streamlit sections (round 3)

**Change:** `poda-redundancias-streamlit-3`
**Status:** Implemented

## Edit plan

- `app/dashboard_ds02.py` only.
- Convert `Cronología de estado de flota` container into a collapsed expander.
- In `_muro_del_hangar`, drop the `RUL p35 (conservadora)` metric and the
  per-card sparkline, keeping state badge + `L_inf (decide)` metric + button.
- Add `expanded=False` to `Cola de mantenimiento · tabla por unidad` expander.
- Add `expanded=False` to `Qué es cada columna y qué rango es normal` expander.
- Convert `Sandbox de estrés` and `Demo en vivo` containers into expanders with
  `expanded=_vista_tribunal`.

## Risks

- Chart count in `test_every_chart_and_grid_has_an_accessible_name`
  (`>=6` charts, `>=7` grids): the per-card sparklines are removed, but the
  fleet chronology chart and the other tabs keep the count above the floor.
- `L_inf` remains the single decision metric on each hangar card.
- Sandbox tests in `test_live_eval` still render because the expander is open
  in the default Tribunal view.
