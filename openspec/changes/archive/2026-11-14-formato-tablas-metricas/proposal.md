# Proposal: Numeric precision in the grids and the missing quality metrics

**Change:** `2026-11-14-formato-tablas-metricas`
**Status:** Proposed
**Capabilities:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md) (Modified + Added)

## Intent

Two defects found by the live Playwright audit:

1. Every numeric cell in the data grids prints full float64 precision: the Auditoría
   tables show «1.2472739948605471» and «0.7224958552224399». The tabs declare
   `st.column_config.NumberColumn(format="%.3f")` and siblings, but the installed
   Streamlit 1.66.0 ignores the `format` field. Verified with a minimal probe (a one-row
   `st.dataframe` with `format="%.3f"` on port 8599): the DOM shows «1.23456789». Nineteen
   `NumberColumn(format=…)` declarations are affected across `Auditoría`, `Casos` and
   `Flota`. Fixing this at the source of truth means formatting the values before they
   reach `st.dataframe`.
2. The headline quality contract is absent from the UI: the frozen manifest records
   RMSE 4.338, MAE 3.227, R2 0.9461 and NASA score 2336.2, and `ui_data_loader` can compute
   all of them from the cache, but the screen only shows macro-RMSE (5.02 / ponderado
   4.34), the per-engine RMSE bars, per-engine MAE, the critical-zone MAE and the band
   coverage. MAE ponderado, R2 and NASA score are nowhere. A tribunal member asking for
   them gets nothing at one click. They will be added to the "Calidad del modelo" card,
   computed live from the cache like every other metric.

## Scope

### In scope

- New `app/lib/ui_format.py` with small formatters (`entero`, `un_decimal`,
  `dos_decimales`, `tres_decimales`, `con_signo_3`, `cuatro_sig`) and a `formatea(df, spec)`
  helper that returns a copy with the mapped columns turned into display strings.
- Apply it to every grid that declares a number format: the tramos and alarma tables in
  `Auditoría`, the lote/tramo/envolvente/editor tables in `Casos`, and the trayectoria,
  registro and hangar tables in `Flota`; switch those columns to `TextColumn` so the
  declared type matches what is rendered.
- Add `r2` to `global_metrics()` and render MAE ponderado, NASA score and R2 in Auditoría.

### Out of scope

- No metric value, threshold, rule, cache row, artifact hash or triage outcome changes.
- The grids remain read-only; sorting becomes lexicographic on the formatted strings, an
  accepted trade-off recorded in the design.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `ds02-dss-ui`: "Live metrics from cached predictions" also covers MAE ponderado, NASA
  score and R2.

### Added Capabilities

- `ds02-dss-ui`: "Numeric precision in data grids" — bounded decimals, sign where declared,
  no raw float64 artifacts.

## Approach

Source-driven: one formatting helper owns the presentation contract, each tab calls it
before `st.dataframe`, and the new metrics come from the same loader the rest of the page
uses. Nothing hardcoded: the NASA and R2 cards read `global_metrics(windows)`.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/lib/ui_format.py` | Add | shared formatters |
| `app/lib/ui_data_loader.py` | Modify | `r2` in `global_metrics` |
| `app/ui/_tab_auditoria.py` | Modify | two grids formatted; three metric cards added |
| `app/ui/_tab_casos.py` | Modify | grids formatted, keeping `help` metadata |
| `app/ui/_tab_flota.py` | Modify | grids formatted |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Tests that inspect `app.dataframe` expect numbers | Medium | the suite runs right after the change; tests updated only where the presentation intentionally changed |
| Lexicographic sorting on formatted strings | Certain | accepted: grids are read-only decision support, and the alternative (raw floats) is worse |
| `NumberColumn` without format silently printing raw floats | Certain | every declared format is migrated; a contract test scans the three tabs for leftover `format=` declarations |

## Rollback Plan

`git revert` the apply commit. One commit touches the helper, the loader, three tabs and
the affected tests.

## Dependencies

Repository virtualenv, pytest, Streamlit 1.66.0. No new dependency.

## Success Criteria

- [ ] No grid cell shows more than the declared precision in any of the three tabs.
- [ ] Auditoría shows MAE ponderado 3.227, NASA score 2336.2 and R2 0.9461 computed from the cache.
- [ ] `python -m pytest tests -q` green except the three pre-existing MLflow failures.
