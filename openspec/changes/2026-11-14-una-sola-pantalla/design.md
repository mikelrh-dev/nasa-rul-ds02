# Design: One screen, no Vista switch

## Technical Approach

Delete the flag and its three consumers; the content those consumers gated becomes
unconditional. No layout restructure.

## Architecture Decisions

| Decision | Alternatives | Choice and rationale |
|---|---|---|
| Which mode survives | keep Tribunal content / keep Turno content / merge | Keep everything: the full screen is what the defense needs and what the page already showed most of the time. |
| Where the flag dies | branch per tab / context flag / session widget | Remove at the source: sidebar widget, entrypoint computation, context field. No dead code left. |
| Sandbox default | expanded / collapsed | Expanded: it was the Tribunal default and it is the demo lever. |

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/ui/_sidebar.py` | Modify | remove the Vista segmented control and its comment |
| `app/entrypoints/dashboard_ds02.py` | Modify | remove `_vista_tribunal` and the `vista_tribunal=` argument |
| `app/lib/context.py` | Modify | remove the field |
| `app/ui/_tab_flota.py` | Modify | drop the two `if _vista_tribunal:` gates (content stays, dedented) |
| `app/ui/_tab_casos.py` | Modify | `expanded=True` for the sandbox |
| `tests/test_dss_interaction.py` | Modify | replace the switch-driven test with a single-surface contract |

## Testing Strategy

| Layer | What to test | Approach |
|-------|--------------|----------|
| Contract | no Vista control exists | AppTest scans segmented controls |
| Integration | session log and rule trace always present; sandbox expanded | AppTest |
| Regression | the rest of the suite unchanged | full gate |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation or process-integration boundary.

## Known Limitations

None new. The grid-name platform limitation and the editor precision trade-off are
unchanged.

## Migration / Rollout

No migration required. Single change, revertible by checkout.

## Open Questions

None. The user decided to remove the switch after seeing it changed almost nothing.
