# Verification Report: Prune the four lowest-value Motor charts

## Phase 1: RED before touching the card

`pytest tests/test_dss_interaction.py tests/test_radioografia_alineada.py -q`
→ **4 failed, 23 passed**. The new contracts failed while the old surfaces still
existed: the gauge was present, the per-cycle radiography was present,
`_tab_motor.py` still built an Indicator and called `fig_deriva()`, and
`resumen_criterio()` did not exist yet.

## Phase 4: Gate

`python -m pytest tests -q` → **477 passed, 3 failed in 167,30 s**.

The three failures are the pre-existing MLflow ones, identical to the baseline recorded before
this change (475 passed / 3 failed):

- `tests/test_mlflow_backfill.py::test_notebooks_instrument_mlflow_live`
- `tests/test_mlflow_live.py::test_all_notebooks_have_mlflow_header_and_log_cell`
- `tests/test_mlflow_live.py::test_no_late_tf_enable_onednn_opts`

No new failure. Focused suite after the prune: 34 passed.

## Visual evidence (Playwright)

- `http://127.0.0.1:8501/`, server restarted so Streamlit re-imports the edited modules; Vista
  Motor → «Ver gemelo» de Unidad 11.
- Occurrences of the text «RUL restante»: **0** — the gauge is gone.
- Legends rendered on the twin panel: `T24`, `T2`, `T50` in the aligned figure; `RUL predicha`,
  `RUL real`, `Banda 90 %` in the trajectory. No `P15`, `P21`, `Ps30` or `P40` traces anywhere.
- Pressure note rendered verbatim with measured figures:
  «Presiones: Ninguno de estos canales supera el criterio (|corr con el RUL| >= 0,3 y salto >= 0,5 ppt):
  el mayor cambio entre tramos es de 2.3 ppt y la forma no es monótona.»
- Temperature caption rendered: «… Solo T50 +1.31 ppt supera el criterio …».
- Exceptions rendered: **0**.
- Captures: `scratch/sdd-poda-radiografia/final-1280-gemelo.png` (1280 px) and
  `final-560-gemelo.png` (560 px).

## Surviving issues

- The aligned view is wired explicitly to the temperature group. The resolution-floor rule is
  documented in the spec, but if a future cache makes a pressure group resolvable the tab will
  not switch automatically. Out of scope here; recorded as a limitation.

## Deviations from the design

None. `fig_deriva()` and its plumbing were removed exactly as planned; the imports left unused
(`MUTED`, `GRID`, `SURFACE`) were dropped from `_tab_motor.py`.
