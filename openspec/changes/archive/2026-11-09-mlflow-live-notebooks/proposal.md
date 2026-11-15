# Proposal: MLflow live in notebooks + timings

**Change:** `mlflow-live-notebooks`
**Capability:** `rul-prediction-ds02` (ADDED: live tracking + timing persistence)
**Branch:** `mlflow-pia4` · **Date:** 2026-11-09

## Intent

PIA-4 backfill stored 13 historical runs, but NB01–07 still do not instrument
MLflow: re-executing them creates no run, timings are ad-hoc `time.time()` in
cells, `ablation_table` drops branch times, and `puente_c` timings are bare
`NaN` that downstream code can log as metrics. Live re-execution must produce
traceable runs and persisted timings without retraining in this change.

## Scope

### In Scope
- `src/ds02_rul/mlflow_live.py`: setup, `log_live_run` (`log_param`/`log_metric`,
  NaN skipped), `persist_timings` (JSON+CSV).
- `pipeline.py`: `run_seed` with `time.perf_counter()` + `t_total`/`timing`;
  `ablation_table` gains `t_lgb_s`/`t_bilstm_s`/`tiempo_s` per row;
  `oof_base_predictions` also `perf_counter`.
- NB01–07 header (cell 0): `MLFLOW_ALLOW_FILE_STORE`, early `TF_*` env
  (incl. `TF_ENABLE_ONEDNN_OPTS=0` before TF), MLflow setup; one live-log
  cell per notebook; late `TF_ENABLE_ONEDNN_OPTS` lines removed.
- `STEP_TRAIN` shadowing in NB04 OOF renamed `STEP_TRAIN_OOF` (value 1).
- `puente_c`: NaN timings refreshed — legacy NaN kept, plus `timing` dict
  with `None`s and `fuente=bundle_congelado`, clean helper.
- `backfill_mlflow.py`: historic-only — every run tagged `fuente=historico`;
  `--check`/`--write`/`--export` ignore live runs.
- Tests updated (notebooks DO instrument MLflow; new live-helper suite).

### Out of Scope
- Executing any notebook (heavy; user runs separately).
- Retraining, changing metrics, hashes, `models/`, bundle, manifest, band.
- `log_model`/`autolog`/registry/server — text-only store stays.

## Capabilities
### New Capabilities
- None (extends `rul-prediction-ds02`).
### Modified Capabilities
- `rul-prediction-ds02`: ADDED live-tracking + timing requirements.

## Approach
Code-only patch via `scripts/patch_mlflow_live_notebooks.py` (idempotent
nbformat edit, no execution). `mlflow_live` is the single logging path so
notebooks stay thin; NaN/inf metrics are never logged.

## Affected Areas
| Area | Impact | Description |
|---|---|---|
| `src/ds02_rul/mlflow_live.py` | New | setup/log/persist helpers |
| `src/ds02_rul/pipeline.py` | Modified | perf_counter, timing keys, ablation cols |
| `src/clase/puente_c.py` | Modified | timing dict + clean helper |
| `scripts/backfill_mlflow.py` | Modified | `fuente=historico`, historic-only |
| `scripts/patch_mlflow_live_notebooks.py` | New | nbformat patcher (no exec) |
| `notebooks/0*.ipynb`, `scripts/build_07_*.py` | Modified | header + log cell, rename, env cleanup |
| `tests/test_mlflow_*.py` | Modified/New | live + historic contract |

## Risks
| Risk | Likelihood | Mitigation |
|---|---|---|
| Live runs break backfill `--check` (13-run assert) | High | filter by `fuente=historico`; tests cover |
| NaN logged as metric | Med | `clean_metric` skips NaN/inf; tests |
| Notebook edit diverges from builder | Med | patch script is the source; builder 07 synced |

## Rollback Plan
Delete `mlflow_live.py` + patch script; revert `pipeline.py`, `puente_c.py`,
`backfill_mlflow.py`, notebooks and tests (`git checkout --`). No store data
migration: live runs are extra runs in `mlruns/` only.

## Success Criteria
- [ ] 13 historic runs carry `fuente=historico`; `--check` passes ignoring live runs.
- [ ] `run_seed`/`oof` use `perf_counter`; `ablation_table` rows carry timings.
- [ ] NB01–07 cell 0 sets MLflow + early TF env; no late `TF_ENABLE_ONEDNN_OPTS`.
- [ ] Timing JSON+CSV persisted by helper; NaN never logged.
- [ ] Frozen hashes unchanged; no notebook executed.
