# Proposal: Selective pruning of redundant Streamlit sections (round 3)

**Change:** `poda-redundancias-streamlit-3`
**Status:** Implemented
**Capability:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md), [`ds02-live-evaluation`](../../specs/ds02-live-evaluation/spec.md)

## Why

A third pass of redundancy pruning on `app/dashboard_ds02.py`. Five surfaces still
repeat information already present elsewhere or can be collapsed without losing
any PIA-rubric content:

1. `Cronología de estado de flota` duplicates the per-unit sparklines already
   shown in the hangar cards.
2. The hangar cards carry both `RUL p35` and a sparkline on top of the
   state + `L_inf` that actually decide the triage.
3. `Cola de mantenimiento · tabla por unidad` is an always-open-ish table that
   can stay collapsed by default.
4. `Qué es cada columna y qué rango es normal` (Casos nuevos) is a large
   glossary that can stay collapsed by default.
5. `Sandbox de estrés` and `Demo en vivo` are tribunal material that should be
   collapsed in Turno view.

## What changes

1. Collapse `Cronología de estado de flota` into a collapsed expander by default.
2. Collapse each hangar card to state badge + `L_inf` metric (drop `RUL p35`
   metric and sparkline).
3. Make `Cola de mantenimiento · tabla por unidad` a collapsed expander by default.
4. Make `Qué es cada columna y qué rango es normal` a collapsed expander by default.
5. Make `Sandbox de estrés` and `Demo en vivo` expanders collapsed in Turno view
   (expanded in Tribunal).

## Impact

- Lines removed/collapsed in `app/dashboard_ds02.py`.
- No metric, chart contract, rule decision, or PIA-rubric surface is lost.
- `models/`, `app/cache/`, `src/`, `mia/` untouched.

## Rollback

`git checkout -- app/dashboard_ds02.py`.
