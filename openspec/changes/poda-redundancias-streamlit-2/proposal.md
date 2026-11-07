# Proposal: Selective pruning of redundant Streamlit sections (round 2)

**Change:** `poda-redundancias-streamlit-2`
**Status:** Implemented
**Capability:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md), [`ds02-live-evaluation`](../../specs/ds02-live-evaluation/spec.md)

## Why

A second pass of redundancy pruning on `app/dashboard_ds02.py`. The first
pass (`poda-redundancias-streamlit`) removed duplicate KPI blocks and a
second scenario entry point. Four help/provenance surfaces still repeat
information already present elsewhere or can be collapsed without losing
any PIA-rubric content:

1. `¿Cómo probar con un caso típico?` (sidebar) restates what the unit/cycle
   controls already imply.
2. `Cómo leer esta pantalla` (sidebar) is a 7-bullet glossary that can be
   condensed to 4 lines while keeping every rubric term.
3. `Contrato de artefacto congelado` (sidebar) duplicates the provenance
   already shown in Auditoría; moving it there removes sidebar clutter.
4. `Procedencia verificable` and `Contrato congelado vs. cálculo en vivo`
   (Auditoría) are always-expanded containers that can be collapsed into
   expanders.

## What changes

1. Delete the `¿Cómo probar con un caso típico?` expander.
2. Collapse `Cómo leer esta pantalla` to 4 lines (RUL, L_inf/"objetivo nominal 90 % · cobertura medida",
   Ciclo de vuelo/Ventana, Orden de trabajo).
3. Move `Contrato de artefacto congelado` from the sidebar to Auditoría.
4. Convert `Procedencia verificable` and `Contrato congelado vs. cálculo en
   vivo` from always-open containers to collapsed expanders.

## Impact

- Lines removed/collapsed: ~20 in `app/dashboard_ds02.py`.
- No metric, chart contract, rule decision, or PIA-rubric surface is lost.
- `models/`, `app/cache/`, `src/`, `mia/` untouched.

## Rollback

`git checkout -- app/dashboard_ds02.py`.
