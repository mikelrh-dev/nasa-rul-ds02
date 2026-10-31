# Design: interactive "explore by cycle"

**Change:** `2026-10-31-ds02-explorar-por-ciclo`

## Approach

Add a self-contained block inside the live-evaluation tab. It reuses existing
helpers (`example_window`, `window_ending_at`, `score_table`, `DEMO_ROWS`,
`channel_order`) and keeps the slider tick to a cheap Parquet read. Scoring
happens only on an explicit button, storing the result in `session_state`.

## Flow

```mermaid
flowchart TD
    accTitle: Explore by cycle flow
    accDescr: Visitor picks engine and end point; a preview table is generated on each tick without scoring; scoring happens only on the explicit button.
    classDef ui fill:#141d2e,stroke:#26344a,color:#e8eef7
    classDef data fill:#0b1220,stroke:#0369a1,color:#a5f3fc
    start([Tab: Casos nuevos]) --> block[Exploration block]
    block --> sel_engine[selectbox: engine 11/14/15]
    block --> sel_len[selectbox: tramo length 50/300]
    block --> slider[slider: end position 0.0-1.0]
    sel_engine --> gen[example_window / window_ending_at]
    sel_len --> gen
    slider --> gen
    gen --> preview[preview: cycles, rows, estimated state]
    preview --> btn{Evaluar este tramo?}
    btn -- no --> slider
    btn -- yes --> score[score_table]
    score --> result[point + band + triage + work order]
    class block,sel_engine,sel_len,slider,btn ui
    class gen,preview,score,result data
```

## Decisions

- **Control type**: `st.slider` for position (continuous, familiar) plus an
  optional length selectbox. Alternative (number input for end cycle) rejected:
  less visual, worse for demos.
- **Scoring trigger**: explicit button. Alternative (score on tick) rejected:
  2-3 s per tick makes the slider unusable and risks a first-tick TF import.
- **State display**: computed, not promised. Alternative (label positions as
  Sano/Medio/Crítico) rejected: a mismatch would break demo credibility.
- **Placement**: after presets, before the editable-grid path. Alternative
  (separate tab) rejected: fragments the live-eval flow.

## Affected areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/dashboard_ds02.py` | Modified | new exploration block |
| `tests/test_live_eval.py` | Modified | 2-3 new AppTest cases |

## Limitations

- The preview state is an estimate over the generated tramo; it is not a
  second model call.
- `window_ending_at` reads the cached Parquet; if the cache is stale the
  preview is stale (covered by the existing artifact-hash check).
- No new module is introduced, so no shadowing risk with `mia/`.
