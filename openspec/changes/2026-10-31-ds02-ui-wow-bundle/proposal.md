# Proposal: UI WOW bundle (PDF download, crypto audit, sensor heatmap)

**Change:** `2026-10-31-ds02-ui-wow-bundle`
**Capability:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md) (modified)

## Why

Three low-risk, high-value enhancements that need no new modules and no layout
change: (1) export the live work order as PDF (CSV/JSON already exist),
(2) an on-demand SHA-256 audit of the frozen artifact, (3) a sensor
degradation heatmap in an expander on the Motor tab. All are additive and live
behind existing surfaces or collapsed expanders, so they do not saturate the UI.

## What changes

1. `app/dashboard_ds02.py`:
   - Add "Descargar parte (PDF)" button next to the existing JSON/CSV buttons
     (~line 1606), reusing the fpdf2 pattern at ~975.
   - Add a SHA-256 audit button inside the contract expander (~595), hashing
     `ds02_manifest.json` and the `.keras` binary on demand, cached in
     `session_state`.
   - Add a `px.imshow` sensor heatmap inside an expander on the Motor tab,
     using z-score over the engine's full cached history (50-row window).
2. `tests/test_dss_ui.py` / `tests/test_live_eval.py`: 2-3 AppTest cases.

## Impact

Startup, model loading, cache and `models/` untouched. No CSS/JS. No new modules
(no shadowing risk with `mia/`).

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| PDF parity with CSV/JSON | Low | Mirror the existing audit-PDF pattern |
| Hashing 1.85 MiB on every render | Low | Gate behind button + cache in session_state |
| Heatmap too heavy | Low | 50 rows × 18 channels, z-score on cached history |
| AppTest grid count | Low | Add `alt=` to the new dataframe |

## Rollback plan

Revert the three blocks in `app/dashboard_ds02.py` and the new tests. Nothing
else moves.

## Success criteria

- [ ] PDF download button produces a valid PDF mirroring the CSV/JSON content.
- [ ] Crypto audit button shows green check when hashes match.
- [ ] Heatmap renders in an expander on the Motor tab without error.
- [ ] `python -m pytest tests -q` green.
- [ ] `test_no_css_is_injected_into_the_app` still green.
