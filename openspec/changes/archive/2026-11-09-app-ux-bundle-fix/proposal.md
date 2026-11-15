# Proposal: app-ux-bundle-fix

**Change:** `app-ux-bundle-fix`
**Capability:** `ds02-dss-ui` (modify). No new capability.

## Intent

Close out a bundle of small, independently testable UX defects/fixes in the
Streamlit surface without touching `src/ds02_rul/`, `src/mia/` or `models/`:
wall navigation, n8n visibility, presets, exports, filters, sparklines,
radiography channels, trajectory CSV, second sandbox sensor, 6-rule view, and a
URL-path guard (`/app/terminal` → `/`).

## Scope

### In Scope

- `Ver gemelo` on a wall card sets `selected_unit` + `unit`/`cycle` and routes the
  user to the Motor tab; twin cards keep the twin-detail flow.
- Visible n8n panel: webhook state, last send (decision/ok/status/ts), test-send
  button; no `/app/terminal` string anywhere under `app/`.
- Presets `Conservador` (+10/+10) and `Agresivo` (−10/−10) alongside Normal ±5.
- Contrast CSV (raw vs corrected), hangar-queue state filter, work-order preview
  table before download.
- Wall sparklines, raw/corrected reading indicator, radiography channels
  T24/T2/T50, trajectory CSV download, second sandbox sensor, 6-rule view.

### Out of Scope

- Any change to `src/ds02_rul/`, `src/mia/`, `models/`, notebooks, n8n flow JSON.
- New model behavior, thresholds semantics, or reclassification.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `ds02-dss-ui`: wall→Motor navigation via `selected_unit`, n8n panel, presets,
  contrast/work-order/trajectory exports, queue filter, sparklines, reading
  indicator, T24/T2/T50 radiography, second sandbox sensor, 6-rule view, URL guard.

## Approach

Small, additive edits in `app/dashboard_ds02.py` and `app/ui_modulos/*` only,
reusing existing helpers (`L.work_order_csv`, `UR.catalogo_decision`,
`N8N.enviar_decision`). Each item gets a pure-helper or AppTest assertion in
`tests/test_app_ux_bundle.py`. Verify with `python -m pytest tests -q`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/dashboard_ds02.py` | Modified | presets, n8n panel, last-send, badges, deferred writes |
| `app/ui_modulos/_tab_flota.py` | Modified | Ver gemelo routing, sparkline, queue filter, order preview, contrast CSV |
| `app/ui_modulos/_tab_motor.py` | Modified | T24/T2/T50 radiography, trajectory CSV |
| `app/ui_modulos/_sandbox_estres.py` | Modified | sensor selector (T48 + second) |
| `app/ui_modulos/_tab_auditoria.py` | Modified | 6-rule view |
| `tests/test_app_ux_bundle.py` | New | bundle coverage |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Streamlit widget-key/session-state conflicts | Med | deferred-write pattern; AppTest full runs |
| Sandbox cache signature change | Low | add sensor to cache key; baseline stays T48 |
| Suite time | Low | focused file first, full suite at verify |

## Rollback Plan

`git checkout -- app/dashboard_ds02.py app/ui_modulos/_tab_flota.py
app/ui_modulos/_tab_motor.py app/ui_modulos/_sandbox_estres.py
app/ui_modulos/_tab_auditoria.py` and delete `tests/test_app_ux_bundle.py`.

## Dependencies

n8n webhook URL from env `N8N_WEBHOOK_URL`; panel degrades gracefully without it.

## Success Criteria

- [ ] `python -m pytest tests -q` green; no `/app/terminal` under `app/`.
- [ ] Each bundle item has a passing scenario test.
