# Proposal: Readable order preview, honest hangar countdown, named grids

**Change:** `2026-11-14-orden-legible-y-rejillas-nombradas`
**Status:** Proposed
**Capabilities:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md) (Added)

## Intent

Three defects found by the second live Playwright audit:

1. **The work-order preview leaks internal serialization.** With units blocked at cycle 31 the
   preview shows a raw JSON blob in the «ventana evaluada» column
   (`{"filas":50,"step":2,"ciclo":31,"start_index":3336,"ventanas_en_ciclo":44}`) and uses
   lowercase headers while every other table in the dashboard uses title case
   (`app/lib/ui_data_loader.py:638` builds a dict; `_tab_flota.py` renders it as-is).
2. **The hangar countdown contradicts the state.** At cycle 31 U11 is already grounded
   (L_inf 17 < 20, state HANGAR) yet «Ciclos hasta el umbral de hangar · Unidad 11: 1 ciclos».
   `simulacion.ciclos_hasta_fallo` looks only at crossings strictly after the current cycle,
   so it answers «next time it goes below» instead of «already below».
3. **Data grids carry no name.** Charts expose their description to assistive technology
   («Sparkline de L_inf…»), but no `stDataFrame` container has an accessible name: the
   platform does not publish `st.dataframe(alt=…)` on the grid element (it only surfaces in
   the column-toggle button) and `st.html` scripts do not execute in this build. The
   accommodation is a visible label immediately above every grid that is not already inside
   a titled card or expander.

## Scope

### In scope

- `app/lib/vista_orden.py`: `tabla_orden(blocked)` builds a human-readable preview (title-case
  columns, window metadata as text) without touching the exported JSON/CSV contract.
- `app/lib/simulacion.py`: `resumen_ciclos_hasta_fallo(...)` distinguishes units already
  below the threshold from those approaching it.
- `app/lib/theme.py`: `nombra_grid(descripcion)` renders the visible label; applied to the
  grids that lack one (the batch triage in `Casos`, the order preview in `Flota`).
- Missing `alt` on the SHAP grid in `app/ui/_paneles.py`.

### Out of scope

- The exported JSON/PDF/CSV documents and their field names: they keep the structured
  `ventana_evaluada` object because downstream consumers read it.
- Thresholds, metrics, rules, cache rows and artifact hashes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `ds02-dss-ui`: added requirement «Readable work-order preview and hangar countdown» and
  «Named data grids».

### Added Capabilities

None.

## Approach

Presentation only: one helper owns the preview shape, one helper owns the countdown sentence,
one helper owns grid labels. Unit contracts cover the two pure helpers; the grid naming rule
is pinned by an AST scan over every `st.dataframe` call.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/lib/vista_orden.py` | Add | preview builder |
| `app/lib/simulacion.py` | Add | countdown sentence helper |
| `app/lib/theme.py` | Modify | `nombra_grid` |
| `app/ui/_tab_flota.py` | Modify | preview, countdown wording, label |
| `app/ui/_tab_casos.py` | Modify | label above the batch triage grid |
| `app/ui/_paneles.py` | Modify | missing `alt` |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Changing the preview hides fields the tribunal reads | Medium | the preview keeps every blocking field (estimated RUL, band limits, real RUL, action); the export is untouched |
| The label helper duplicates an existing card title | Low | applied only where no title exists; visual check at 1280 px |
| Source-contract test too strict for future grids | Medium | the rule is «declare alt OR sit under a title»; new grids must satisfy one |

## Rollback Plan

`git revert` the apply commit. Six files, no data change.

## Dependencies

Repository virtualenv, pytest, Streamlit 1.66.0. No new dependency.

## Success Criteria

- [ ] No preview cell contains braces or JSON keys; headers read in title case.
- [ ] A unit already below the hangar threshold never reports a positive countdown.
- [ ] Every read-only grid either declares `alt` or sits directly under a title; the two
      unnamed grids render a visible label.
- [ ] `python -m pytest tests -q` green except the three pre-existing MLflow failures.
