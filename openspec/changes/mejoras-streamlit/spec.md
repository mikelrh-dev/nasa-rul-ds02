# Spec delta: Streamlit P0+P1+P2 improvements

**Change:** `mejoras-streamlit`
**Status:** Implemented

## ADDED

### Requirement: Audit hash is cached

The audit SHA-256 SHALL be computed through a `@st.cache_data` helper keyed by
path, file size and mtime, and SHALL NOT be rehashed on every render.

### Requirement: Audit PDF is cached and on demand

The audit PDF SHALL be built through a `@st.cache_data` builder keyed by
policy thresholds, artifact SHA and cache signature. It SHALL be generated
only after the user asks to download (generate button), never on every render.

### Requirement: Each tab reruns as a fragment

Each of the four tab bodies SHALL be executed inside its own `@st.fragment`,
so widget interactions rerun only that tab.

### Requirement: Single SHAP panel

A single `shap_panel(unit)` function SHALL render the SHAP explanation (top
features + waterfall) and SHALL replace the duplicated SHAP blocks. It SHALL
use distinct button keys per call site.

### Requirement: No fixed temp path for SHAP waterfall

`ui_shap` SHALL NOT default to `/tmp/shap_waterfall.png`. The PNG helper SHALL
use `tempfile` when no path is given, and a Plotly figure helper SHALL be the
preferred in-app path (no file on disk).

### Requirement: Test twin removed and banner aligned with the wall

The `PRUEBAHANGAR` entry SHALL be removed from the local fleet registry. The
`Primera lectura` hangar metric SHALL count the same units as the wall cards
(cached fleet plus registered twins) in numerator and denominator; no separate
`Además, N motores...` count SHALL describe a different set.

### Requirement: Widget help

Every `st.multiselect` and `st.slider` (and every `st.selectbox` in the
dashboard) SHALL carry `help=`.

### Requirement: Reproducibility is visible next to new-case prediction

The new-case result SHALL show the artifact SHA-256 and the window/step
contract next to the prediction (metrics or equivalent).

### Requirement: Scoring timeout for 5 000 rows

`ui_inference.score_table` SHALL enforce a wall-clock timeout budget and SHALL
reject tables above `MAX_FILAS` (5 000) before loading the model, with the
row-cap message.

### Requirement: Friendly message when SHAP is not installed

When `ui_shap` or the `shap` package is missing, the UI SHALL show a friendly,
actionable message (`pip install shap` or equivalent) instead of a raw
exception string.

## Preserved (PIA rubric)

- Test metrics from cached predictions (RMSE, MAE, bias, per-engine, by band).
- Real-vs-predicted chart and conformal band.
- New-case prediction with rule decision and p, in Casos nuevos.
