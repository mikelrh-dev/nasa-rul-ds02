# Proposal: evaluate an aircraft the user brings to the UI

**Change:** `2026-10-21-ds02-live-eval`
**Status:** Implemented
**Capability:** [`ds02-live-evaluation`](../../specs/ds02-live-evaluation/spec.md)

---

## Why

The DSS can only replay the three frozen test engines. A visitor cannot answer
the question they actually came with — *"what would this model say about my
aircraft?"* — because `app/cache/` holds pre-scored windows and nothing in the
UI accepts new telemetry.

The model itself does not need retraining to answer that: `predict_interval()`
takes **raw** `(n, 50, 18)` windows and performs its own scaling and
residualisation from the frozen bundle. The gap is an input path, not a model.

## What changes

1. **`app/ui_inference.py`** — the missing seam: channel order derived from the
   cache provenance, contract validation with actionable errors, an example
   window lifted from the cached telemetry, and on-demand scoring through
   `load_ensemble(...).predict_interval(...)`.
2. **A fifth tab, "Evaluar unidad nueva"** — a `st.form` with three input paths
   that all feed the same pipeline:
   * **ejemplo** (default): a real 50-row window from unit 14, so the tab works
     on first paint with zero typing;
   * **editar tabla**: a 50-row `st.data_editor` grid where a block pasted from
     Excel/Sheets is accepted;
   * **subir CSV**: a file with `cycle` plus the 18 channels.
3. **Tests** — the contract validator, the example window, the triage of a live
   score, and an end-to-end render that presses the evaluate button.

The model, `models/` and `src/ds02_rul/` are untouched. Scoring is gated behind
the form's submit button, so the app still starts without importing TensorFlow.

## Why not a plain "fill in the sensors" form

A window is 50 rows × 18 channels = 900 numbers. Manual entry is not
user-friendly, it is a data-entry job. The UI therefore offers a paste-ready
grid and a CSV upload, states the sampling recipe explicitly, and pre-fills a
real window so the flow is demonstrated before anyone types anything.

## Impact

| | Value |
| --- | --- |
| Startup | unchanged (TF is imported only when a score is requested) |
| First score | one-time model load (~8 s on this machine), then cached |
| Inputs accepted | 50+ rows, exact channel order, numeric, no NaN |
| Output | point RUL, conformal band, triage state, optional work order |
| `models/` | read-only; hashes unchanged |

## Rollback plan

Delete `app/ui_inference.py`, `tests/test_live_eval.py` and the fifth tab; the
rest of the change set is unaffected. Nothing in `models/` or `src/` moves.

## Artifacts that stay byte-compatible

`models/ensemble.joblib`, `models/bilstm_ds02.keras`, `models/scaler.joblib`,
`models/ds02_manifest.json`, `app/cache/*`, `app/dashboard.py`, `app/api.py` and
every file under `src/ds02_rul/`.
