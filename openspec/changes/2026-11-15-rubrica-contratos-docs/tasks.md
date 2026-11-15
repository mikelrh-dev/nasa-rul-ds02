# Tasks: Documentation and rubric contracts (no n8n)

**Change:** `2026-11-15-rubrica-contratos-docs`

## Phase 1 — Regression contract (RED first)

### 1.1 New contract test
- **Task:** create `tests/test_rubrica_doc_contract.py` asserting the README anchors ("Qué hemos construido", "IA fuerte", "no supervisado", time column), threshold consistency with `app/lib/_constantes.py` (`25.0 / 20.0`) and the pyarrow pin in both dependency manifests.
- **Acceptance:** `python -m pytest tests/test_rubrica_doc_contract.py -q` exits non-zero on the current tree (RED).

### 1.2 Notebook count
- **Task:** update `tests/test_mlflow_live.py` count from `7` to `8`.
- **Acceptance:** `python -m pytest tests/test_mlflow_live.py -q` reports the count mismatch as the only remaining cause once 1.1 is in place.

## Phase 2 — Notebook contract

### 2.1 Header and TF order
- **Task:** rewrite `notebooks/00_datos.ipynb` cell 0 so it sets `MLFLOW_ALLOW_FILE_STORE`, `TF_ENABLE_ONEDNN_OPTS`, thread variables and calls `setup_mlflow()` before any TensorFlow import; move the late `os.environ.setdefault("TF_ENABLE_ONEDNN_OPTS", "0")` out of cell 1.
- **Acceptance:** cell 0 contains the three markers; no other cell mentions `TF_ENABLE_ONEDNN_OPTS`.

### 2.2 Live-log cell
- **Task:** append a code cell that logs `live__nb00_datos` via `log_live_run` with measured params (seed) and metrics (row counts), importing `persist_timings` per the NB01 pattern.
- **Acceptance:** the notebook body references `log_live_run` and `persist_timings`; the static contract tests pass for `00_datos.ipynb`.

## Phase 3 — Documentation alignment

### 3.1 Root README
- **Task:** restore "Qué hemos constructed" anchors (weak vs strong AI, supervised vs unsupervised), add the training-time column, align thresholds to `25/20`, publish the vigente multiseed (`4.333 ± 0.040`, seed rows `4.338 / 4.371 / 4.291`), mark `4.324 ± 0.107` historical and `4.368` obsolete, and document the MLflow view command.
- **Acceptance:** task 1.1 assertions on `README.md` pass.

### 3.2 English README
- **Task:** align `README.en.md` thresholds and multiseed figures to the same values.
- **Acceptance:** no `≥30 -> APTO` instruction and no `4.368` cited as vigente.

### 3.3 Class-track README
- **Task:** fix dead paths (`app/ui_shap.py` -> `app/lib/ui_shap.py`, `app/dashboard_ds02.py` -> `app/entrypoints/dashboard_ds02.py`, `scripts/evaluate_bundle_stability.py` -> `scripts/operativo/...`), replace "~35 tests" with the real count and "15 nodos / 3 ramas" with "20 nodos / 4 salidas".
- **Acceptance:** every cited path exists; counts match the current suite and flow.

### 3.4 Vault evidence note
- **Task:** correct `e00-cifras-autoritativas.md`: current CSV rows `4.371 / 4.291`, vigente mean `4.333 ± 0.040`, coverage `0.901643`, thresholds `25/20`.
- **Acceptance:** figures match `bundle_c_multiseed.csv`, the manifest and `freeze_rules_evidence.py --check`.

## Phase 4 — Dependency pins

### 4.1 PyArrow
- **Task:** add `pyarrow==<installed version>` to `requirements.txt` and mirror it in `pyproject.toml`.
- **Acceptance:** task 1.1 pin assertion passes; `python -m pip check` stays clean.

## Phase 5 — Verification

### 5.1 Full gate
- **Task:** run `python scripts/verify_gate.py` and capture the output.
- **Acceptance:** `GATE PASSED` with zero failures.

### 5.2 MLflow store check
- **Task:** run `python scripts/operativo/backfill_mlflow.py --check`.
- **Acceptance:** exits 0 with `OK: 17 runs`.

## Budget forecast

Decision needed before apply: No
Chained PRs recommended: No
400-line budget risk: Low
