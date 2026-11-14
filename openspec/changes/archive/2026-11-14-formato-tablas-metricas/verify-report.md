# Verification Report: Numeric precision in the grids and the missing quality metrics

## Phase 1: RED

`pytest tests/test_ui_format.py -q` failed at collection (the helper module did not exist),
and once the module landed the AppTest contract failed on the missing metric labels until
`global_metrics` grew `r2`. After the implementation: **11 passed**.

## Phase 5: Gate

`python -m pytest tests -q` -> **488 passed, 3 failed in 255,05 s**.

The baseline before this change was 477 passed / 3 failed; the eleven new contracts account
for the difference exactly. The three failures are the pre-existing MLflow ones:
`test_mlflow_backfill.py::test_notebooks_instrument_mlflow_live`,
`test_mlflow_live.py::test_all_notebooks_have_mlflow_header_and_log_cell`,
`test_mlflow_live.py::test_no_late_tf_enable_onednn_opts`.

Suites that inspect grids ran before the apply commit: **131 passed**
(`test_audit_fixes`, `test_dss_ui`, `test_engine_flow`, `test_live_eval`, `test_ux_round3`,
`test_dss_interaction`).

## Visual evidence (Playwright)

- Server restarted so the new `app/lib/ui_format.py` is imported.
- Auditoría tramos grid: MAE reads «1.247», «4.155», «5.395» and Sesgo «+0.722», «+1.226»,
  «-2.906» -- exactly the scenario pinned in the spec.
- Auditoría alarma grid: integers (27/40/13, 34/57/23, 27/48/21); the rules grid header now
  matches its column («Prioridad», 10/9/8).
- Raw-precision scan over every `td`/`th`: **0 cells** with more than four decimals in
  Auditoría and Flota. Casos shows 64, all of them inside the editable `data_editor` grid
  (an input, see limitations).
- New quality cards measured in the DOM: Macro-RMSE 5,02 / ponderado 4,34,
  MAE ponderado 3,227, NASA score 2336,2, R² 0,9461 -- two rows (y=1318 and y=1447), no
  clipped card, widths inside the 1280 px viewport.
- Captures: `scratch/sdd-formato-metricas/auditoria-1280.png`, `flota-1280.png`,
  `casos-1280.png`, `motor-1280.png`, `calidad-1280.png`.

## Surviving issues

- Editable grids keep full float precision: pre-formatting them would turn the cells into
  text and break numeric editing, and Streamlit ignores declared formats anyway. Recorded as
  a limitation, not a regression: they looked like that before.
- Sorting a formatted column is lexicographic, because the displayed values are strings.
  Accepted for read-only grids (recorded in the design).

## Deviations from the design

- The rules view returns lowercase keys (`regla`, `prioridad`, `porque`); the previous
  declaration used «Prioridad» and silently matched nothing. It is now keyed correctly.
- Envelope limits render in scientific notation for large magnitudes (`3.103e+04`), which
  is what `%.4g` produces and keeps four significant digits as specified.
