# Design: evaluate an aircraft the user brings

**Change:** `2026-10-21-ds02-live-eval`
**Status:** Implemented
**Spec:** [spec.md](spec.md) · [proposal](proposal.md)

---

## Flow

```mermaid
%%{init: {'theme': 'neutral'}}%%
flowchart LR
    accTitle: One validated table feeds a single scoring path
    accDescr: The example window, the editable grid and the CSV upload all produce the same table, which is validated and then scored by the frozen bundle on demand.

    subgraph input["Entrada (cualquiera de las tres)"]
        direction TB
        ex[example_window]
        gr[editable_grid]
        cs[csv_upload]
    end

    val[validate_table]
    ord[channel_order]
    score[score_table]
    ens[frozen_bundle]
    out[point_band_state]
    wo[work_order]

    ex --> val
    gr --> val
    cs --> val
    ord --> val
    val --> score
    ens --> score
    score --> out
    out --> wo

    classDef input_node fill:#e8eef6,stroke:#35506f,color:#16202b
    classDef gate_node fill:#fdf1e3,stroke:#8a5a20,color:#2b1a08
    classDef score_node fill:#efe8f7,stroke:#5b3f86,color:#1d1230
    classDef out_node fill:#e9f5ea,stroke:#2f6b3a,color:#142a18
    class ex,gr,cs input_node
    class val,ord gate_node
    class score,ens score_node
    class out,wo out_node
```

## Decision: three inputs, one pipeline

The three paths exist because they answer different moments of use:

| Path | Moment | Cost to the user |
| --- | --- | --- |
| Example | "show me what this does" — first paint, demo | zero |
| Editable grid | a few rows to fix, or a block pasted from a spreadsheet | one paste |
| CSV | a full recording exported from another tool | one upload |

They converge on `validate_table()` and then `score_table()`, so there is one
place where the contract lives and one place where the model is called. A
divergence between paths would be a bug by construction.

**Rejected alternative: a "fill in the sensors" form with 18 inputs.** A window
is 900 numbers; typing them is not a user-friendly flow, it is data entry, and
it would push users to enter one row and expect a prediction — which the model
cannot honour, since it needs 50 downsampled rows of history.

## Decision: the sampling recipe is part of the contract

The model consumes 50 rows taken every 100th recorded row (`STRIDE = 100`), not
50 one-second samples and not 50 cycles. A user who pastes 50 consecutive 1 Hz
readings gives the model a window covering about one minute of flight, and the
prediction is meaningless even though every column is numerically valid.

No validator can detect that from the numbers alone, so the UI states the recipe,
shows the example's source unit and cycles, and lets the reader check it against
the cache. This is a documentation decision made structural: the contract panel
is part of the tab, not a footnote in a README.

## Decision: scoring behind a submit button

The tab body renders on every rerun (tabs always execute), so an unguarded model
load would put TensorFlow back into startup and undo the 1.4 s cold start. The
grid lives inside `st.form`, which batches edits and only reruns on submit; the
score itself runs only after `form_submit_button` returns True. The model is held
by `@st.cache_resource`, so the first score pays the load and later ones do not.

**Rejected alternative: precompute on every render.** It would re-run the BiLSTM
on each slider move elsewhere in the app.

## Decision: the live unit gets a negative identifier

The bundle's EMA smoothing is per unit. A live evaluation uses `unit = -1.0`, a
value no DS02 unit can take, so a user's window can never be smoothed together
with a cached engine — even if the same `st.session_state` outlives several
evaluations.

## Decision: no accuracy claim for user data

There is no ground truth for a user's aircraft. The tab therefore shows the point
estimate, the band and the triage state, and states that no RMSE/MAE can be
attached to it. The conformal band is still reported because it was calibrated on
out-of-fold rows of the development engines, so it is a conservative bound for
the same representation — but not a promise about a different fleet.

## Known limitations

1. **A live window is not a diagnosis.** The model was fitted on six engines;
   a different platform or sampling rate is outside the representation, and the
   UI says so rather than hiding it behind a number.
2. **The life-length prior still applies.** Any unit living longer than ~63
   cycles inherits the under-prediction measured in
   `INFORME_p0_p1_prior_de_vida.md`; the lower bound absorbs part of it.
3. **The example is a real test window.** It is lifted from
   `app/cache/ds02_rows.parquet`, so it demonstrates the flow but is not
   independent evidence of generalisation.
4. **One window at a time.** Scoring is over the rows provided; there is no
   streaming/append loop, and history must be re-submitted to update a curve.
