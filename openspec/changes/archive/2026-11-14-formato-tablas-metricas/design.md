# Design: Numeric precision in the grids and the missing quality metrics

## Technical Approach

One shared presentation helper formats numeric columns into display strings before they
reach `st.dataframe`; each tab declares those columns as text columns. The new quality
metrics come from the loader, not from literals.

## Architecture Decisions

| Decision | Alternatives | Choice and rationale |
|---|---|---|
| Where formatting happens | rely on `column_config` / pre-format in pandas / custom component | Pre-format. Verified that Streamlit 1.66.0 ignores `NumberColumn.format` even in a minimal probe, so the declared format is dead configuration today. |
| One helper vs per-tab code | per-tab lambdas / shared module | Shared `app/lib/ui_format.py`. The requirement says the contract has one owner; nineteen declarations across three tabs would otherwise drift again. |
| Declared column type after formatting | keep `NumberColumn` without format / switch to `TextColumn` | Switch to `TextColumn`. Keeping `NumberColumn` would re-introduce the silent mismatch this change removes. |
| Where R2 comes from | read the manifest / compute from cache | Compute from the cache with `global_metrics`, exactly like RMSE and MAE. Verified equal to the manifest (0.9461), so no hardcoded figure and no second source of truth. |
| Sorting after formatting | leave floats hidden in a parallel frame / accept lexicographic order | Accept lexicographic order: the grids are read-only decision support and the alternative is unreadable numbers. Recorded as a limitation. |
| Metric placement | new section / extend the existing quality card | Extend "Calidad del modelo" in `Auditoría`: it already owns macro-RMSE and critical-zone MAE. |

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/lib/ui_format.py` | Add | `entero`, `un_decimal`, `dos_decimales`, `tres_decimales`, `con_signo_3`, `cuatro_sig`, `formatea(df, spec)` |
| `app/lib/ui_data_loader.py` | Modify | `global_metrics` gains `r2` |
| `app/ui/_tab_auditoria.py` | Modify | tramos grid (windows/mae/bias) and alarma grid formatted; Δ/Prioridad grid formatted; MAE ponderado, NASA score and R2 cards added |
| `app/ui/_tab_casos.py` | Modify | lote grid, tramo grid (cycle + sensors, keeping `help`), envelope grid, editor grid formatted |
| `app/ui/_tab_flota.py` | Modify | trayectoria, registro and hangar grids formatted |

## Interfaces / Contracts

```python
# app/lib/ui_format.py
def entero(serie: pd.Series) -> pd.Series: ...
def tres_decimales(serie: pd.Series) -> pd.Series: ...
def con_signo_3(serie: pd.Series) -> pd.Series: ...
def cuatro_sig(serie: pd.Series) -> pd.Series: ...
def formatea(frame: pd.DataFrame, spec: dict[str, callable]) -> pd.DataFrame:
    # copia del frame con las columnas mapeadas convertidas en texto
```

## Testing Strategy

| Layer | What to test | Approach |
|-------|--------------|----------|
| Unit | formatters round, sign and blank out NaN | pure tests against small series |
| Contract | `global_metrics` includes `r2` matching the manifest value | frozen cache |
| Source | the three tabs format through the shared helper and declare no number format | AST/text scan, like the earlier chrome contracts |
| Integration | Auditoría renders MAE ponderado, NASA score and R2 | AppTest on the dashboard entrypoint |
| E2E evidence | no grid cell shows raw float64 at 1280 px | Playwright DOM inspection |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification or
process-integration boundary is touched. The change writes no file and spawns no process.

## Known Limitations

- Formatted columns become strings, so grid sorting is lexicographic. Accepted for read-only
  grids; if numeric sorting becomes a requirement later, the values must stay numeric and the
  presentation move to a custom renderer.
- Tests that inspect `app.dataframe` values as numbers will be updated where the
  presentation intentionally changed; their intent (columns present, metadata intact) is
  preserved.

## Migration / Rollout

No migration required. Single change, one commit, revertible by checkout.

## Open Questions

None. Scope was fixed in the proposal round: formatting in the three tabs, and the three
missing metrics in Auditoría.
