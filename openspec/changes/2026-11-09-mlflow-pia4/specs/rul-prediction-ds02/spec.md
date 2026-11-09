# Spec delta: experiment tracking for the class track and bundle C

**Change:** `2026-11-09-mlflow-pia4`
**Capability:** `rul-prediction-ds02` (ADDED requirement)
**Status:** Proposed
**Sources of truth:** `resultados/comparativa.csv`,
`resultados/mlp_comparativa.csv`, `resultados/comparativa_bundle_c.csv`,
`resultados/bundle_c_train.log`, `models/ds02_manifest.json`

---

## ADDED

### Requirement: Experiment tracking

The system SHALL record every model of the class track and every component of the
deployed bundle C as an MLflow run in the `ds02-clase` experiment. Each run SHALL
carry its measured hyperparameters, its train / validation / test metrics and its
training time when one was measured. The run SHALL be identified by a unique
`run_key` tag and SHALL carry `grano`, `familia`, `origen` and `rol` tags.

The system SHALL use a text-only file store under `mlruns/`. Model binaries,
datasets, per-run figures and `.trash/` entries MUST NOT be versioned. The system
MUST NOT call `mlflow.log_model`, `mlflow.autolog`, the Model Registry, or write a
model signature / input example: the deployed artifacts remain under `models/`
and are identified by their SHA-256 parameters.

The comparison table SHALL be generated from the MLflow API and SHALL carry the
`run_id` of every run. A hand-written CSV MUST NOT be presented as an MLflow table.

#### Scenario: Thirteen runs, two grains

- GIVEN the backfill has completed
- WHEN the active runs of `ds02-clase` are counted
- THEN there are exactly 13 runs
- AND 9 have `grano=fila` (5 classical + 4 MLP)
- AND 4 have `grano=ventana` (LGBM, BiLSTM, BiLSTM+EMA5, production bundle C)
- AND every `run_key` is unique

#### Scenario: Every run carries measured parameters

- GIVEN any of the 13 runs
- WHEN its parameters are read
- THEN it has at least one measured hyperparameter
- AND its `rmse_val` or `rmse_test` metric is present
- AND `tiempo_s` is present except for `bundle__bilstm_ema5`, which was not timed
- AND no missing time is replaced by zero

#### Scenario: The production run is traceable to the manifest

- GIVEN the `prod__bundle_c` run
- WHEN its parameters and metrics are compared with `models/ds02_manifest.json`
- THEN it records seed 42, beta 1.0, EMA 5, window 50, 93 LGBM features,
  18 scaler features, 19 channels, 22 epochs, 15 OOF epochs, step 3/2,
  conformal target 0.90 and 17 450 calibration rows
- AND it records the four SHA-256 values `ensemble_sha256`, `bilstm_sha256`,
  `clase_xgb_sha256` and `clase_e2_sha256`
- AND `v3_bundle` is a tag with value `archivado`, not a parameter
- AND its metrics are 4.338 / 3.227 / 0.9461 / 2336.2

#### Scenario: Row and window grains are not compared

- GIVEN the comparison table
- WHEN the row-grain block and the window-grain block are read
- THEN the two blocks are separate
- AND the README labels `rmse_val` and `rmse_test` explicitly
- AND no single table or capture mixes 7.3404 (row validation) with 4.338
  (window test) as if they were the same measurement

#### Scenario: The backfill is idempotent

- GIVEN a store with the 13 runs
- WHEN `scripts/backfill_mlflow.py --write` runs again
- THEN the active run count remains 13
- AND each `run_key` still has exactly one active run
- AND `--check` exits 0

#### Scenario: The store is text-only

- GIVEN the `mlruns/` directory
- WHEN it is inspected
- THEN it contains `meta.yaml`, `params/`, `metrics/` and `tags/` text files
- AND no file exists under `mlruns/**/artifacts/`
- AND no model binary is written by the backfill

#### Scenario: The export comes from the API

- GIVEN `docs/evidencia/mlflow/comparativa.csv`
- WHEN it is compared with `MlflowClient.search_runs`
- THEN it has one row per active run
- AND every row carries its `run_id`
- AND every metric in the CSV equals the store value

#### Scenario: Notebook execution cannot duplicate the store

- GIVEN the seven notebooks, which do not import MLflow
- WHEN any notebook is re-executed
- THEN no run is created in `ds02-clase`
- AND the active run count remains 13
