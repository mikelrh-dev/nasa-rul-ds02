# Tasks: MLflow live in notebooks + timings

**Change:** `mlflow-live-notebooks` · **Branch:** `mlflow-pia4`

## Review Workload Forecast

| Field | Value |
|---|---|
| Estimated changed lines | ~900 (notebooks are generated JSON) |
| 400-line budget risk | High |
| Chained PRs recommended | No (single authorized change) |
| Delivery strategy | single-pr (user-authorized SDD loop) |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: High

## Phase 1: Helper + pipeline timing

- [x] 1.1 RED: `tests/test_mlflow_live.py` (clean_metric, timing, persist, perf_counter source, ablation cols, puente_c NaN, backfill fuente).
  Acceptance: new tests fail on current code.
- [x] 1.2 Create `src/ds02_rul/mlflow_live.py` (`setup_mlflow`, `log_live_run`, `clean_metric`, `timing_from_result`, `persist_timings`).
  Acceptance: 1.1 helper tests green.
- [x] 1.3 Patch `pipeline.py`: `perf_counter` in `run_seed`/`oof_base_predictions`; add `t_total`+`timing`; `ablation_table` timing columns.
  Acceptance: 1.1 timing tests green; no other pipeline behavior changes.
- [x] 1.4 Refresh `puente_c.py`: keep NaN keys, add `timing` dict (`None`s, `fuente=bundle_congelado`) + `clean_timing_value`.
  Acceptance: 1.1 puente_c tests green.

## Phase 2: Notebooks (code only, no execution)

- [x] 2.1 Create `scripts/patch_mlflow_live_notebooks.py` (idempotent nbformat patcher).
  Acceptance: running it twice yields identical files.
- [x] 2.2 Run patcher: NB01–07 cell-0 header (MLflow+early TF env+setup), live-log cell per notebook, remove late `TF_ENABLE_ONEDNN_OPTS`, rename `STEP_TRAIN_OOF` in NB04/NB06-OOF.
  Acceptance: no notebook executed (`execution_count` unchanged); static checks pass.
- [x] 2.3 Sync `scripts/build_07_shap_c_notebook.py` header with NB07.
  Acceptance: regenerating builder output matches NB07 cells.

## Phase 3: Backfill historic-only + tests

- [x] 3.1 Patch `scripts/backfill_mlflow.py`: `fuente=historico` on all 13; `--write`/`--check`/`--export` historic-only; export gains `fuente` column.
  Acceptance: `--check` passes with store as-is.
- [x] 3.2 Update `tests/test_mlflow_backfill.py` (notebooks DO instrument; historic-only; live ignored).
  Acceptance: test file green.
- [x] 3.3 Focused gate: `pytest tests/test_mlflow_live.py tests/test_mlflow_backfill.py tests/test_clase_bundle_c.py -q`
  Acceptance: exit 0, 0 skipped.
- [x] 3.4 Full gate: `pytest tests -q` + frozen hashes + `git status` (no `.ipynb` executed, no `models/` change).
  Acceptance: exit 0; 5/5 hashes match.
