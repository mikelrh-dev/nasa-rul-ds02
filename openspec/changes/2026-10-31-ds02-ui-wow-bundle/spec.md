# Specification: UI WOW bundle (PDF download, crypto audit, sensor heatmap)

**Change:** `2026-10-31-ds02-ui-wow-bundle`

## Requirements

### R1 — PDF download of the work order (A.8)
- GIVEN a grounded fleet (at least one unit in hangar) WHEN the operator clicks "Descargar orden (PDF)" THEN a valid PDF is produced whose content mirrors the JSON/CSV already generated (units, RUL, L_inf, L_sup, action, motive, artifact hash).
- The button appears next to the existing JSON/CSV buttons in the same horizontal container.
- No model recompute; reuses `L.work_order()` output.

### R2 — On-demand crypto audit (A.7)
- GIVEN the contract expander is open WHEN the operator clicks "Auditar hashes del artefacto" THEN the SHA-256 of `models/bilstm_ds02.keras` is computed and compared with `manifest.artifacts.bilstm_sha256`.
- The hash is computed only on click (not every render) and cached in `session_state`.
- A green check is shown on match; red cross on mismatch; warning on IO error.

### R3 — Sensor degradation heatmap (A.3)
- GIVEN the Motor tab is open WHEN the operator expands "Mapa de calor · degradación sensorial (z-score)" THEN a Plotly `imshow` heatmap renders with sensors on Y and flight cycles on X, values z-scored per channel.
- The expander is collapsed by default (no front saturation).
- The chart carries an `alt=` attribute (guard test).

## Non-functional
- No CSS/JS injection (`test_no_css_is_injected_into_the_app`).
- No model loading in render path.
- Tests: 31 + 44 green; new count of order download buttons = 3.