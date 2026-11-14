# Verification Report: One screen, no Vista switch

## Phase 1: RED

The rewritten contract failed while the «Vista» segmented control still existed
(`test_hay_una_sola_pantalla_y_no_conmutador_de_vista`). The sandbox guard already passed,
because the default mode was Tribunal.

## Phase 3: Gate

`python -m pytest tests -q` -> **495 passed, 3 failed in 206,97 s**.

Baseline before the change: 494 passed / 3 failed. The old switch-driven test became two
contracts (+1). The three failures are the pre-existing MLflow ones:
`test_mlflow_backfill.py::test_notebooks_instrument_mlflow_live`,
`test_mlflow_live.py::test_all_notebooks_have_mlflow_header_and_log_cell`,
`test_mlflow_live.py::test_no_late_tf_enable_onednn_opts`.

Suites that render the sidebar and Flota after the apply commit: **52 passed**
(`test_dss_interaction`, `test_vista_orden`, `test_ui_format`, `test_engine_flow`,
`test_ux_round3`).

## Visual evidence (Playwright)

- Sidebar after a fresh load: the panel starts «Guardia operativa» followed directly by
  «Unidad de test»; no Vista control exists, and the only sidebar radios are the three unit
  pills. Capture: `scratch/sdd-formato-metricas/reauditoria-sin-vista-sidebar.png`.
- Flota: «Motor de reglas · traza del caso» and «Registro de sesión» are both present in the
  single screen.
- Casos: the stress sandbox starts expanded (asserted through AppTest `proto.expanded`).
- Zero exceptions in all checks.

## Surviving issues

None introduced. The known platform limitations stay recorded: grid containers have no
programmatic accessible name (visible labels are the accommodation) and numeric editors keep
full precision.

## Deviations from the design

None. The spec carries no delta because no capability described the two modes.
