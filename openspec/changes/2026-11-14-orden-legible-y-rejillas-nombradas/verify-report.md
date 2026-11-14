# Verification Report: Readable order preview, honest hangar countdown, named grids

## Phase 1: RED

`pytest tests/test_vista_orden.py -q` failed at collection (`app.lib.vista_orden` did not
exist), and the AST contract failed on `app/ui/_paneles.py`: the SHAP grid called
`st.dataframe` without `alt=`.

## Phase 4: Gate

`python -m pytest tests -q` -> **494 passed, 3 failed in 144,46 s**.

The baseline before this change was 488 passed / 3 failed; the six new contracts account for
the difference. The three failures are the pre-existing MLflow ones:
`test_mlflow_backfill.py::test_notebooks_instrument_mlflow_live`,
`test_mlflow_live.py::test_all_notebooks_have_mlflow_header_and_log_cell`,
`test_mlflow_live.py::test_no_late_tf_enable_onednn_opts`.

Suites that render Flota/Casos before the apply commit: **101 passed**.

## Visual evidence (Playwright)

- Flota advanced to cycle 31 (three presses of «Avanzar 10 ciclos de flota»). The countdown
  line now reads: «Ciclos hasta el umbral de hangar · Unidad 11 — degradación estándar: ya
  por debajo del umbral · Unidad 14 — caso atípico / régimen compuesto: 3 ciclos · Unidad 15
  — degradación nominal / alta precisión: ya por debajo del umbral». No grounded unit is
  counted as approaching.
- The order preview table shows title-case headers (Unidad, Estado, Regla, Ventana evaluada,
  Ciclo simulado, Ciclo evaluado, RUL estimada, L_inf, L_sup, …) and the window cell reads
  «ciclo 31 · 50 filas · paso 2». A scan over every `td`/`th` found **no braces**.
- The visible label «Vista previa de la orden» renders directly above the preview grid.
- Capture: `scratch/sdd-formato-metricas/flota-orden-ciclo31.png`.
- The batch-triage label in `Casos` lives inside the results card, which only renders after
  scoring a batch; it was verified with an AppTest integration test that pastes a real
  50-row block and scores it: after scoring, the page markdown contains
  «Triage del lote · una fila por motor».

## Surviving issues

- The grid container still has no programmatic accessible name: Streamlit 1.66 does not
  publish `alt` on the element and `st.html` does not execute JavaScript here (probe on port
  8600: the injected marker never ran). Visible labels are the accommodation, not full WCAG
  naming, and this stays recorded as a platform limitation.
- Sorting on pre-formatted columns remains lexicographic (previous change, unchanged).

## Deviations from the design

None. The Casos label verification moved from manual Playwright to an integration test
because the batch card needs a scored batch to render.
