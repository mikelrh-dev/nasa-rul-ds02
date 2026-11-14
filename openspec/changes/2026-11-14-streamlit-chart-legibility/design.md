# Design: Streamlit chart legibility and fixed chrome

## Technical Approach

Single owner for figure layout (`app/lib/theme.py`) and single owner for the Plotly
browser config, adopted by every `st.plotly_chart` call site. `chart_layout` gains real
margins plus `automargin`, the legend moves below the plotting area, axis titles and
series names are shortened (the long wording stays in the existing captions), and the
band table stops duplicating its raw column. No data path, metric or artifact changes.

## Architecture Decisions

| Decision | Alternatives | Choice and rationale |
|---|---|---|
| Margin strategy | bigger margins only / `automargin` only / both | Both. Explicit floors (`l=56, r=16, t=44, b=64`) guarantee room for tick labels and a two-row legend; `automargin` absorbs whatever overflow remains (long titles, wide tick values). `automargin` alone was rejected because it cannot reserve space deterministically. |
| Legend placement | keep above / move below / vertical right | Below (`yanchor="top"`, `y=-0.16`). Measured defect: above it wraps into 4–7 rows and draws over traces. Vertical right was rejected: it steals width from a plot already narrow at 560 px. |
| Floating mode bar | hide / hover / trim buttons | Hide always (`displayModeBar: False`). User decision: it overlaps the top-right corner and adds nothing to a read-only dashboard. |
| Title length vs height | shorten / raise heights / both | Shorten first, raise heights only if a clip survives. Preserves compactness; captions keep the full wording. |
| Band table header | `rename()` / `column_config` alias / drop the column | `rename()`. One source of truth, no duplicated column to drift. |
| Verification layer | runtime DOM assertions / source contract tests | Source/AST contract tests as the gate (fast, deterministic, no browser), plus Playwright captures in `sdd-verify` as visual evidence and regression comparison. |

### Render pipeline

```mermaid
%% accTitle: Chart render pipeline
%% accDescr: Cache parquet to data loader to tab trace builder to shared Plotly layout and browser config, ending in the browser.
flowchart LR
    cache["app_cache_parquet"] --> loader["ui_data_loader"]
    loader --> tab["app_ui_tab_module"]
    tab --> traces["go_figure_traces"]
    traces --> layout["chart_layout_style_axes"]
    layout --> widget["st_plotly_chart_config"]
    widget --> browser["browser"]
    classDef fill:#1e293b,stroke:#38bdf8,color:#e2e8f0;
    class cache,loader,tab,traces,layout,widget,browser;
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/lib/theme.py` | Modify | `chart_layout` margins + `automargin`; new `CHART_CONFIG`; legend below |
| `app/ui/_tab_motor.py` | Modify | three call sites adopt `CHART_CONFIG`; shortened titles/names |
| `app/ui/_tab_flota.py` | Modify | one call site adopts `CHART_CONFIG` |
| `app/ui/_tab_casos.py` | Modify | one call site adopts `CHART_CONFIG` |
| `app/ui/_tab_auditoria.py` | Modify | two call sites adopt `CHART_CONFIG`; band table `rename()` |
| `app/ui/_paneles.py` | Modify | SHAP and force charts adopt `CHART_CONFIG` |
| `app/ui/_sandbox_estres.py` | Modify | stress chart adopts `CHART_CONFIG` |
| `tests/test_ui_chart_chrome.py` | Create | layout, config-owner and table-header contract tests |

## Interfaces / Contracts

```python
# app/lib/theme.py
_MARGEN_L, _MARGEN_R, _MARGEN_T, _MARGEN_B = 56, 16, 44, 120
_LEYENDA_DESPEJE_PX = 65.0

CHART_CONFIG: dict = {"displayModeBar": False}

def chart_layout(**overrides) -> dict:
    # margin=dict(l=_MARGEN_L, r=_MARGEN_R, t=_MARGEN_T, b=_MARGEN_B)
    # xaxis=dict(automargin=False), yaxis=dict(automargin=False)
    # legend: orientation="h", yanchor="top", x=0,
    #         y = -_LEYENDA_DESPEJE_PX / (height - t - b)   # se recalcula tras los overrides
```

Every call site becomes `st.plotly_chart(fig, theme=None, config=CHART_CONFIG, alt=...)`.

`fig_deriva` overrides the top margin to 72 px and renders the legend with the dataset
channel codes only (the full descriptions stay in the glossary and captions).

## Testing Strategy

| Layer | What to test | Approach |
|-------|--------------|----------|
| Unit | `chart_layout` margins and `automargin` values | direct assertion on the returned dict |
| Contract | one config owner, all call sites pass it | AST scan of `app/**/*.py` |
| Contract | band table uses `rename`, not `assign` | AST scan of `app/ui/_tab_auditoria.py` |
| Integration | the app renders headless without exception | existing `AppTest` suite |
| E2E evidence | no clipping, no mode bar, legend below | Playwright captures at 1280 px and 560 px, saved as verify evidence |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification
or process-integration boundary is touched. The change writes no file and spawns no
process.

## Known Limitations

- `automargin` is deliberately disabled on both axes. With it enabled, Plotly shrinks the
  plotting area to make room for the legend, and because the legend offset is a fraction
  of that area, the clearance fed back into itself and the legend overlapped the X axis
  title again (measured 7 px at 1280 px). Explicit margins make the plotting-area height
  deterministic: `height - t - b`.
- The legend names are dataset channel codes; the physical descriptions live in the
  glossary, the paste-grid help text and the chart captions. Evidence: with the full
  descriptions the pressure legend wrapped into 5 rows and Plotly shrank the plot for them.
- At 560 px the trajectory legend ends flush with the figure bottom (0 px spare); nothing
  is clipped.

## Migration / Rollout

No migration required. Single change, one commit, revertible by checkout.

## Open Questions

None. Product decisions were taken in the proposal round: full scope, shorten-first,
legend below, mode bar hidden.
