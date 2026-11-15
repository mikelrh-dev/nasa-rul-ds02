# Verify report: MLflow live in notebooks + timings

**Change:** `mlflow-live-notebooks` · **Date:** 2026-11-09
**Verdict: PASS**

## Evidence
- `pytest tests/test_mlflow_live.py tests/test_mlflow_backfill.py tests/test_clase_bundle_c.py -q` → **30 passed**.
- `pytest tests -q` → **422 passed in 210.04 s** (baseline 406 + 16 new), 0 failed.
- `scripts/backfill_mlflow.py --check` → `OK: 13 runs (9 fila + 4 ventana), export y store coinciden, sin artefactos.`
- `scripts/patch_mlflow_live_notebooks.py` run twice → second run `already patched` ×7 (idempotent).
- Frozen hashes: `ensemble.joblib` d6c70142…, `bilstm_ds02.keras` bf9620a7…,
  `ds02_manifest.json` 1085dd67…, `calibracion_banda.json` 162db707…,
  `instrumento_oof.npz` 04d972ed… — 5/5 unchanged.
- Notebooks: original cells keep their `execution_count`/outputs; appended
  live-log cell has `execution_count=None`, `outputs=[]` → **no notebook was executed**.

## Spec compliance
| Requirement | Evidence | Status |
|---|---|---|
| Live notebook MLflow tracking | `mlflow_live.log_live_run` (log_param/log_metric, NaN skipped); NB01–07 header + log cell (static tests) | COMPLIANT |
| Timing perf_counter + persistence | `pipeline.py` perf_counter + `t_total`/`timing`; `ablation_table` timing cols (fake-run_seed test); `persist_timings` JSON==CSV test | COMPLIANT |
| Historic backfill is historic-only | 13 specs tagged `fuente=historico`; `--check` historic-only; export gains `fuente` | COMPLIANT |
| STEP_TRAIN_OOF rename | NB04 `STEP_TRAIN_OOF=1`, protocol `STEP_TRAIN=3` intact; NB06 OOF literal named | COMPLIANT |

## Issues
- None CRITICAL. Live runs will only appear when the user re-executes
  NB01–07 (out of scope for this change, per instructions).
