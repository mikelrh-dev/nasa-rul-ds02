# Design: UI WOW bundle

**Change:** `2026-10-31-ds02-ui-wow-bundle`

## Decisions

- **PDF generation** lives in a new module `app/pdf_partes.py` (`parte_trabajo_pdf(order)`) to keep `dashboard_ds02.py` from growing; reuses the fpdf2 pattern of `_informe_auditoria_pdf` (latin-1 sanitization, A4 portrait).
- **Crypto audit** is a button-gated, session_state-cached computation inside the existing contract expander; only `bilstm_ds02.keras` is hashed (the artifact already covered by `artifact_hash_check`).
- **Heatmap** is a collapsed expander on the Motor tab using `plotly.express.imshow` over z-scored per-channel history grouped by cycle; import of `plotly.express` is local to avoid a new top-level import.

## Files touched

- `app/pdf_partes.py` (new)
- `app/dashboard_ds02.py` (import + 3 blocks)
- `tests/test_dss_ui.py` (assertion 2 → 3 downloads)
- `openspec/changes/2026-10-31-ds02-ui-wow-bundle/*`

## Tests

- `tests/test_dss_ui.py`: 31 passed.
- `tests/test_live_eval.py`: 44 passed.
- `tests/test_ui_rules.py`, `tests/test_engine_flow.py`: 23 passed.