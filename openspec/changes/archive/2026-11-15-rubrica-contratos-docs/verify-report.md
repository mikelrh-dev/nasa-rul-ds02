# Verification Report — Documentation and rubric contracts

**Change:** `2026-11-15-rubrica-contratos-docs`
**Date:** 2026-11-15
**Scope:** documentation, dependency pins, notebook static contract and the new
regression test. No retraining; no `models/`, `mlruns/` or `data/` writes.

## Evidence

### RED before the fixes

```
python -m pytest tests/test_rubrica_doc_contract.py -q -p no:cacheprovider
6 failed in 0.61s
```

Failures: README anchors, thresholds, multiseed rows, pyarrow pin, dead paths,
vault figures.

### GREEN after the fixes

```
python -m pytest tests/test_rubrica_doc_contract.py tests/test_mlflow_live.py -q -p no:cacheprovider
23 passed in 7.01s
```

### Full gate

```
python scripts/operativo/verify_gate.py
504 passed in 154.96s (0:02:34)
GATE PASSED            (exit 0)
```

Baseline before the change: 495 passed / 3 failed, `GATE FAILED`. The three
failures shared one cause (`notebooks/00_datos.ipynb`); all are closed and the six
new contract tests raise the suite to 504.

### MLflow store

```
python scripts/operativo/backfill_mlflow.py --check
OK: 17 runs (9 fila + 4 ventana + 4 ablacion), export y store coinciden, sin artefactos.
```

## Byte compatibility

No model artifact was touched: `models/ensemble.joblib`, `bilstm_ds02.keras`,
`scaler.joblib`, `mejor_modelo_clase.joblib`, `mejor_modelo_clase_E2.joblib` and
`ds02_manifest.json` keep their SHA-256 values. The notebook is edited but not
executed; no `data/processed/` output is regenerated.

## Limits

1. `MLProyectVault/` is gitignored: the e00 correction is local, and its test skips
   when the vault is absent from a checkout.
2. `data/` is not versioned, so a clean clone cannot run the 21 tests that read
   `data/processed/*.parquet`; out of scope for this change.
3. `n8n/` flows, credentials and auth remain untouched (owner-led).
