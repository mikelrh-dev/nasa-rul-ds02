# Proposal: One screen, no Vista switch

**Change:** `2026-11-14-una-sola-pantalla`
**Status:** Proposed
**Capabilities:** none (presentation only)

## Intent

The sidebar «Vista» control promises two audiences — its own help text says Turno leaves
only what an operator uses on shift — but measured live it changes almost nothing:

- The Auditoría tab renders identically in both modes (same cards, same rules table, same
  PDF button; 3.241 characters and 8 charts in both cases).
- Casos is identical too, including the SHAP panel and the stress sandbox.
- The only real differences are two blocks inside Flota («Registro de sesión» and «Motor de
  reglas · traza del caso») plus the initial state of the sandbox expander.

A control that appears to switch views but does not is a self-contradiction in the UI, and
the user noticed it. Removing the switch and keeping one full screen is the honest option:
all the content stays available, nothing is promised that the app cannot deliver, and the
sidebar loses one row.

## Scope

### In scope

- Remove the «Vista» segmented control from the sidebar and the `vista_tribunal` flag from
  the context.
- Render the tribunal material unconditionally: the session log and the rule trace in
  Flota, and the sandbox expanded by default in Casos.

### Out of scope

- No metric, threshold, rule, cache row or artifact hash changes.
- The spec has no requirement about two views, so no capability delta is needed.

## Capabilities

None modified. The deployed spec never described the two-view behaviour, so this change
removes an unspec'd feature rather than modifying a requirement.

## Approach

Delete the flag and its three read sites; keep the content. Tests that drove the switch are
rewritten as contracts over the single surface.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/ui/_sidebar.py` | Modify | drop the Vista control |
| `app/entrypoints/dashboard_ds02.py` | Modify | drop `_vista_tribunal` and the context argument |
| `app/lib/context.py` | Modify | drop the field |
| `app/ui/_tab_flota.py` | Modify | render log and rule trace unconditionally |
| `app/ui/_tab_casos.py` | Modify | sandbox expanded by default |
| `tests/test_dss_interaction.py` | Modify | replace the two-view test with a single-surface contract |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| A reader expected two audiences | Low | the two audiences were never delivered; one complete screen is easier to defend |
| Test churn | Low | only one test drives the switch |

## Rollback Plan

`git revert` the apply commit. Six files, presentation only.

## Dependencies

Repository virtualenv, pytest, Streamlit 1.66.0.

## Success Criteria

- [ ] No «Vista» control exists in the sidebar.
- [ ] Session log and rule trace render in the single screen.
- [ ] `python -m pytest tests -q` green except the three pre-existing MLflow failures.
