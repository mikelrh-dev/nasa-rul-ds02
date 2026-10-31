# Proposal: interactive "explore by cycle" on the live-evaluation tab

**Change:** `2026-10-31-ds02-explorar-por-ciclo`
**Capability:** [`ds02-live-evaluation`](../../specs/ds02-live-evaluation/spec.md) (modified)

## Why

The three presets are fixed scenarios (Sano / Medio / Crítico) at fixed
positions. A visitor who wants to see *how* the state evolves across one
engine's life must prepare a CSV or edit a grid by hand — not interactive.
The cache already exposes `example_window(unit, position)` and
`window_ending_at(unit, cycle, rows=...)`, so a dynamic tramo can be generated
on demand without new data or retraining. The gap is a UI control, not a model.

## What changes

1. **`app/dashboard_ds02.py`** — a new block inside the live-evaluation tab,
   after the presets and before the editable-grid path:
   - `st.selectbox` for the engine (11 / 14 / 15).
   - `st.slider` for the end point (position 0.0–1.0, or end cycle).
   - optional `st.selectbox` for tramo length (50 vs 300 rows).
   - read-only preview (cycles covered, rows, estimated state).
   - `st.button` "Evaluar este tramo" that calls `score_table` and shows the
     result + work order on block.
2. **No new module** — reuse `ui_inference.example_window`, `window_ending_at`,
   `score_table`, `DEMO_ROWS`, and `ui_data_loader` helpers.
3. **Tests** — 2–3 AppTest cases (valid table generated, preview state,
   evaluate button works) plus a guard that presets are untouched.

## Why not re-score on every slider tick

`score_table` costs 2–3 s per call. Calling it on every rerun would make the
slider unusable and would re-import TensorFlow on first tick. The slider only
regenerates the preview table; scoring happens on the explicit button.

## Impact

| | Value |
|---|---|
| Startup | unchanged (TF still imported only on score) |
| Slider tick | ~ms (Parquet read only) |
| Evaluate | 2–3 s (bundle cached after first) |
| Presets / tests | untouched |
| `models/` | read-only |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| State promised ≠ state computed | Med | Block never labels a position as "Crítico"; it computes and shows |
| Slider tick latency | Low | Preview only, no scoring |
| AppTest slider flakiness | Med | Stable `key`, `set_value` in tests |
| Preset regression | Low | Separate block, distinct keys, no edits to presets |

## Rollback plan

Delete the new block in `app/dashboard_ds02.py` and the 2–3 new tests. Nothing
in `models/`, `src/`, `app/ui_inference.py` or `app/ui_data_loader.py` moves.

## Dependencies

- `app/ui_inference.py` (`example_window`, `window_ending_at`, `score_table`,
  `DEMO_ROWS`, `channel_order`)
- `app/ui_data_loader.py` (`get_rows`, `fleet_snapshot`, `classify`)

## Success criteria

- [ ] Slider generates a valid table (≥ 50 rows, correct columns) for any
      engine and position.
- [ ] Preview shows the computed state without scoring.
- [ ] "Evaluar este tramo" produces a result and, on block, a work order.
- [ ] The three presets still yield APTO / INSPECCIÓN / HANGAR.
- [ ] `python -m pytest tests -q` green.
", "path">
openspec/changes/2026-10-31-ds02-explorar-por-ciclo/proposal.md