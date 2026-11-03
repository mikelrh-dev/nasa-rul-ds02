# Proposal: Streamlit P0+P1+P2 improvements

**Change:** `mejoras-streamlit`
**Status:** Implemented
**Capability:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md), [`ds02-live-evaluation`](../../specs/ds02-live-evaluation/spec.md)

## Why

The dashboard renders all four tabs on every interaction, hashes the BiLSTM
artifact and builds the audit PDF on every render, and duplicates SHAP
explanation code in two tabs. It also writes a fixed `/tmp` path for the SHAP
waterfall, keeps a stale test twin (`PRUEBAHANGAR`) in the local registry, and
shows a hangar counter on the banner that counts a different denominator than
the wall cards. P2 polish (widget help, reproducibility surface, scoring
timeout, friendly message when SHAP is not installed) is missing.

## What changes

### P0 — caching and fragments

1. Cache the artifact-audit hash and the audit PDF with `@st.cache_data`
   (file-hash helper keyed by path/size/mtime; PDF builder keyed by
   thresholds, SHA and cache signature).
2. Fragment each tab body with `@st.fragment` so interactions rerun only the
   affected tab.

### P1 — SHAP unification, temp path, test data, banner

3. Replace the two SHAP blocks with a single `shap_panel(unit)` used in both
   `Motor` and `Casos nuevos`.
4. Remove the `/tmp/shap_waterfall.png` default: `ui_shap` uses `tempfile` and
   exposes a Plotly waterfall figure consumed directly by the dashboard.
5. Remove the `PRUEBAHANGAR` twin from the local registry and align the
   `Primera lectura` hangar counter with the wall cards (same numerator and
   denominator: cached fleet + registered twins).
6. Generate the audit PDF only after the user presses download (generate
   button + cached builder), not on every render.

### P2 — help, reproducibility, timeout, missing SHAP

7. Ensure every `multiselect`/`slider` (and stray `selectbox` without help)
   carries `help=`.
8. Surface reproducibility artefacts (artifact SHA-256, window/step contract)
   next to the new-case prediction.
9. Add a timeout budget to `ui_inference.score_table` for the 5 000-row cap,
   failing fast with the existing row-cap message.
10. Show a friendly, actionable message when `ui_shap`/`shap` is not installed.

## Impact

- Touches `app/dashboard_ds02.py`, `app/ui_shap.py`, `app/ui_inference.py`,
  `app/ui_data_loader.py` (hash caching) and the local `app/registros_flota.json`.
- No metric, chart contract, rule decision, or PIA-rubric surface is lost
  (test metrics, real-vs-predicted chart, new-case decision + p).
- `models/`, `app/cache/`, `src/`, `mia/` stay byte-identical.

## Rollback

`git checkout -- app/dashboard_ds02.py app/ui_shap.py app/ui_inference.py app/ui_data_loader.py`
