# Delta for rul-prediction-ds02

**Change:** `mlflow-live-notebooks`

## ADDED Requirements

### Requirement: Live notebook MLflow tracking

The system SHALL record each notebook's live execution as MLflow runs in
`ds02-clase` with tag `fuente=live_notebook`. Every live run SHALL carry a
unique `run_key`, a `notebook` tag, measured params via `log_param` and
measured metrics via `log_metric`. NaN/inf metrics SHALL be skipped, never
logged. Model binaries MUST NOT be logged (no `log_model`/autolog).

#### Scenario: NB01-07 header sets up MLflow before TF

- GIVEN any of NB01–07 cell 0
- WHEN the notebook starts
- THEN `MLFLOW_ALLOW_FILE_STORE=true` and `TF_ENABLE_ONEDNN_OPTS=0` are set
- AND `setup_mlflow()` points at `<root>/mlruns`, experiment `ds02-clase`
- AND no later cell sets `TF_ENABLE_ONEDNN_OPTS`

#### Scenario: Train cell logs live run with params and metrics

- GIVEN a notebook has produced its main objects in memory
- WHEN its live-log cell runs
- THEN one run per measured object is created with `log_param` + `log_metric`
- AND the run carries `fuente=live_notebook` and its notebook tag

#### Scenario: NaN timing is never logged as a metric

- GIVEN `puente_c()` result with `t_lgb=float("nan")`
- WHEN `log_live_run` logs its timings
- THEN no `tiempo_s`/`t_lgb_s` metric is created from the NaN
- AND the run still records its other measured metrics

### Requirement: Timing with perf_counter and persistence

`run_seed` and `oof_base_predictions` SHALL measure branch times with
`time.perf_counter()`. `run_seed` SHALL return `t_lgb`, `t_lstm`, `t_total`
and a `timing` dict. `ablation_table` SHALL add `t_lgb_s`, `t_bilstm_s` and
`tiempo_s` per row (LGBM row: `t_lgb`; BiLSTM row: `t_lstm`; EMA row: none).
The live helper SHALL persist timings to `resultados/tiempos_<stem>.json`
and `.csv` with `run_key`, `t_lgb_s`, `t_bilstm_s`, `tiempo_s`, `fuente`.

#### Scenario: run_seed returns perf_counter timings

- GIVEN `run_seed(raw, seed=42, ...)` returns
- WHEN `t_lgb`, `t_lstm`, `t_total` are read
- THEN all are finite floats and `t_total >= max(t_lgb, t_lstm)`

#### Scenario: ablation_table carries per-row times

- GIVEN `ablation_table(raw, seeds=(42,), ...)`
- WHEN a row is read
- THEN it has `t_lgb_s`, `t_bilstm_s`, `tiempo_s` columns
- AND the LGBM row has `t_lgb_s>0` and the BiLSTM row has `t_bilstm_s>0`

#### Scenario: Timings persist as JSON and CSV

- GIVEN a list of timing rows
- WHEN `persist_timings(rows, stem)` runs
- THEN `resultados/tiempos_<stem>.json` and `.csv` both exist
- AND both contain the same rows

### Requirement: Historic backfill is historic-only

The 13 backfill runs SHALL carry tag `fuente=historico`. Backfill
`--write`/`--check`/`--export` SHALL manage only historic runs and MUST NOT
count, delete or overwrite live runs (`fuente=live_notebook`).

#### Scenario: Backfill check ignores live runs

- GIVEN the store has 13 historic + any live runs
- WHEN `scripts/backfill_mlflow.py --check` runs
- THEN it exits 0 counting exactly the 13 historic runs

#### Scenario: `STEP_TRAIN_OOF` does not shadow the protocol

- GIVEN NB04 protocol `STEP_TRAIN=3`
- WHEN the OOF cell runs
- THEN it uses `STEP_TRAIN_OOF=1` for `oof_base_predictions`
- AND `STEP_TRAIN` remains 3
