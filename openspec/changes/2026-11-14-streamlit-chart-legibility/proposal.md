# Proposal: Streamlit chart legibility and fixed chrome

**Change:** `2026-11-14-streamlit-chart-legibility`
**Status:** Proposed
**Capabilities:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md) (Modified). No new capability.

## Intent

Every Plotly chart in the dashboard shares `chart_layout` (`app/lib/theme.py:76-91`):
margins of 8 px and no `automargin`. Axis ticks and axis titles are drawn outside the
plot area and get clipped or overlapped; the horizontal legend wraps into 4–7 rows and
draws over the plotting region; the floating Plotly mode bar covers the top-right corner
of every chart; and one audit table renders a duplicated raw English column. All of it
was measured in the live app (DOM geometry) and reproduced offline with the repository's
own helpers and cached data. Metrics, thresholds, rules, cache rows and artifact hashes
are untouched: the figures shown match the authoritative bundle C values, so this is a
presentation-only defect.

## Scope

### In scope

- Shared layout owner: margins plus `automargin` in `app/lib/theme.py`.
- Every `st.plotly_chart` call site: one `CHART_CONFIG` constant with
  `displayModeBar: False`, legend below the plot, shortened axis titles and series names.
- Audit band table: rename instead of duplicate; Spanish headers only.

### Out of scope

- Any metric, threshold, rule, cache row, artifact hash or triage change.
- Offline PNG generation under `resultados/` (separate code path, not affected).
- New chart types, new panels, interaction or navigation changes.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `ds02-dss-ui`: adds a chart-chrome legibility contract (clipped or overlapped axis text
  is forbidden, legends must not cover the plotting area) and a table-header contract.

## Approach

One transversal fix in `chart_layout` (margins `l=56, r=16, t=44, b=64` plus
`xaxis`/`yaxis` `automargin`), one exported `CHART_CONFIG = {"displayModeBar": False}`
used by every call site, the legend moved below with `yanchor="top"`, shortened
titles/names, and `rename()` instead of `assign()` in the band table. Verified first in an
offline replica, then with Playwright captures at a fixed viewport.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/lib/theme.py` | Modified | `chart_layout` margins + automargin; new `CHART_CONFIG` |
| `app/ui/_tab_motor.py` | Modified | three call sites: gauge, radiographies, trajectory |
| `app/ui/_tab_flota.py` | Modified | one call site |
| `app/ui/_tab_casos.py` | Modified | one call site |
| `app/ui/_tab_auditoria.py` | Modified | two call sites + band-table rename |
| `app/ui/_paneles.py`, `app/ui/_sandbox_estres.py` | Modified | adopt the shared config |
| `tests/test_ui_chart_chrome.py` | New | layout, config and table-header contract tests |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| `automargin` shrinks the plot area and a new clip appears elsewhere | Medium | before/after captures per chart at fixed viewports; tune margins/heights only if a regression is visible |
| Shortened labels lose descriptive detail | Low | the long wording already lives in the existing captions |
| The change touches every chart at once | Medium | one change, one commit; rollback is a single revert |

## Rollback Plan

`git revert` the apply commit (or `git checkout -- app/ tests/`). Only `app/lib/theme.py`,
the tab modules and the new test file are touched; no artifact, cache or registry file is
written by the UI change.

## Dependencies

Repository virtualenv and pytest; a locally running Streamlit for the Playwright pass. No
new runtime dependency.

## Success Criteria

- [ ] Every Plotly chart renders axis ticks and titles fully inside its viewport at 1280 px
      and 560 px widths, with no overlap.
- [ ] No floating Plotly mode bar is present on any chart.
- [ ] Legends sit below the plotting area and never overlap traces.
- [ ] The audit band table has four columns, Spanish headers, no duplicated column.
- [ ] `python -m pytest tests -q` is green, plus a Playwright before/after capture.
