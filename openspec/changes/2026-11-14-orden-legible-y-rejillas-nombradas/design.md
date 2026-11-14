# Design: Readable order preview, honest hangar countdown, named grids

## Technical Approach

Two pure helpers own the two sentences and one owns the preview shape; the tabs only compose
them. Grid naming uses a small label helper because the platform gives no programmatic name
for a dataframe container.

## Architecture Decisions

| Decision | Alternatives | Choice and rationale |
|---|---|---|
| Where the preview shape lives | inline in `_tab_flota.py` / new module | New `app/lib/vista_orden.py::tabla_orden(blocked)`. Testable without rendering, single owner. |
| What the preview keeps | subset of fields / all fields | All blocking fields, human-readable names; the export keeps the structured dict untouched. |
| Countdown wording | change semantics of `ciclos_hasta_fallo` / add a summary helper | Add `resumen_ciclos_hasta_fallo(faltan, actuales, umbral)`. The loader function stays pure (it answers «next crossing»); the sentence answers «what should I read now». |
| Grid naming mechanism | JS injection / visible labels / expanders | Visible labels. Verified that `st.html` scripts do not execute in Streamlit 1.66 (probe on port 8600), and expanders would hide content. Documented as a platform limitation. |
| Which grids get a label | all grids / only unnamed ones | Only grids not already inside a titled card or expander: batch triage in `Casos`, order preview in `Flota`. Avoids duplicating existing titles. |

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/lib/vista_orden.py` | Add | `tabla_orden(blocked)` — readable preview frame |
| `app/lib/simulacion.py` | Modify | `resumen_ciclos_hasta_fallo(...)` |
| `app/lib/theme.py` | Modify | `nombra_grid(descripcion)` |
| `app/ui/_tab_flota.py` | Modify | preview, countdown, label |
| `app/ui/_tab_casos.py` | Modify | label above the batch triage grid |
| `app/ui/_paneles.py` | Modify | `alt` on the SHAP grid |

## Interfaces / Contracts

```python
# app/lib/vista_orden.py
def tabla_orden(bloqueadas: list[dict]) -> pd.DataFrame:
    # columnas en title case; ventana_evaluada como texto

# app/lib/simulacion.py
def resumen_ciclos_hasta_fallo(faltan: dict[int, int | None],
                               actuales: dict[int, float],
                               umbral: float) -> dict[int, str]:
    # "ya por debajo" | "nunca en la vida registrada" | "N ciclos"

# app/lib/theme.py
def nombra_grid(descripcion: str) -> None:
    st.markdown(f"**{descripcion}**")
```

## Testing Strategy

| Layer | What to test | Approach |
|-------|--------------|----------|
| Unit | preview has no braces, title-case headers | frozen order built from the cache |
| Unit | countdown says «ya por debajo» below the threshold | pure helper cases |
| Contract | every `st.dataframe` passes `alt=` | AST scan over `app/ui` |
| Integration | app renders without exception after the changes | existing AppTest suites |
| E2E evidence | preview cells and countdown at cycle 31 | Playwright DOM inspection |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification or
process-integration boundary is touched. The change writes no file and spawns no process.

## Known Limitations

- The grid container still has no programmatic accessible name: Streamlit does not publish
  `alt` on the element and `st.html` does not run scripts here. The visible label is the
  accommodation, not full WCAG naming.
- Sorting on formatted columns remains lexicographic (previous change, unchanged).

## Migration / Rollout

No migration required. Single change, one commit, revertible by checkout.

## Open Questions

None. Scope fixed by the audit findings.
