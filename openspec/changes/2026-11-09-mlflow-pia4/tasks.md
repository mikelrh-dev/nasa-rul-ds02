# Tasks: MLflow experiment tracking for PIA-4

**Change:** `2026-11-09-mlflow-pia4`
**Branch:** `mlflow-pia4`
**Status:** Completed (2026-11-09) — phases 0–7. **No notebook is executed or modified.**

Every task closes with its acceptance check. Commands run from the repository root
with `.venv/Scripts/python.exe` on Windows.

## Review workload guard

```
Decision needed before apply: No (user authorized the SDD loop and the MLflow plan)
Chained PRs recommended: No (one change, phases below)
400-line budget risk: Medium (the new script and test; generated CSV/store excluded)
```

---

## Phase 0 — Preflight

### [x] 0.1 Branch, backups and hash snapshot
Create `mlflow-pia4`; copy `notebooks/artifacts_c`, `resultados/` and
`src/mia/instrumento_oof.npz` to dated backups; write
`.pytest_cache/hashes-pre-notebooks.txt` for the five contract artifacts.
Acceptance: backups exist; hashes match the values in the proposal.
Verify: `sha256sum -c .pytest_cache/hashes-pre-notebooks.txt` (or the equivalent
Python check).

### [x] 0.2 Baseline suite
Run `python -m pytest tests -q -rs`.
Acceptance: 0 failures, 0 skips. Recorded baseline: **395 passed** in 182.68 s.

---

## Phase 1 — Dependency

### [x] 1.1 Pin `mlflow==3.18.0`
Add the pin to `requirements.txt` and `pyproject.toml`; update the requirements
header to say the file now covers tracking as well as the model runtime.
Acceptance: `grep -n "mlflow" requirements.txt pyproject.toml` shows the exact pin.

### [x] 1.2 Lock and install without moving the stack
Run `uv lock`, then `python -m pip install mlflow==3.18.0`.
Acceptance: `pip check` exits 0; numpy 2.5.4, pandas 3.0.6, scikit-learn 1.9.1,
TensorFlow 2.21.0 and LightGBM 4.7.0 keep their versions.
Verify: a Python one-liner prints the five versions; focused tests pass.

### [x] 1.3 Focused regression check
Run `python -m pytest tests/test_artifact_contract.py tests/test_cache_drift.py
tests/test_clase_pipeline.py -q`.
Acceptance: exit 0; no model artifact is written.

---

## Phase 2 — Store policy and experiment

### [x] 2.1 Gitignore the store artifacts and the backups
Add `mlruns/**/artifacts/`, `mlruns/.trash/` and the dated backup patterns.
Acceptance: `git status --short` does not list any binary under `mlruns/` or a
dated backup directory.

### [x] 2.2 Create `ds02-clase`
The backfill creates the experiment if missing and sets its description, the
environment tags (`python`, `sklearn`, `xgboost`, `lightgbm`, `tensorflow`,
`keras`), the data SHAs and `job=reto-1-saa-pia-mia`.
Acceptance: the experiment exists once; no duplicate experiment is created.

---

## Phase 3 — Backfill and 13 runs

### [x] 3.1 Implement `scripts/backfill_mlflow.py`
Read the two class CSVs, the bundle CSV, `bundle_c_train.log` and the manifest.
Define the 13 run specs with `run_key`, params, metrics and tags. Implement
`--write` (idempotent by `run_key`), `--check` (13 active runs, params/metrics/tags)
and `--export` (API-generated CSV).
Acceptance: `--write` exits 0 and creates exactly 13 active runs; `--check`
exits 0; a second `--write` still leaves 13.

### [x] 3.2 Log the production run from the manifest
Log seed 42, beta 1.0, EMA 5, window 50, 93 LGBM features, 18 scaler features,
19 channels, 22 epochs, 15 OOF epochs, step 3/2, conformal target 0.90,
17 450 calibration rows, quantile 0.35 and the four model SHAs. `v3_bundle` is a
tag (`archivado`), not a parameter.
Acceptance: the production run has 4 SHA params and the `reference_row` metrics
4.338 / 3.227 / 0.9461 / 2336.2.

### [x] 3.3 Export the comparison CSV
Write `docs/evidencia/mlflow/comparativa.csv` with one row per run, `run_id`,
`grano`, `familia`, `rol`, `seleccion`, `params_summary`, `params_json`,
train/val/test metrics, `nasa_test`, `tiempo_s`, `macro_rmse`.
Acceptance: 13 rows; the row-grain block has 9 and the window-grain block 4;
`run_id` is present in every row.

---

## Phase 4 — Captures and evidence

### [x] 4.1 Comparison captures
Run `mlflow ui --backend-store-uri ./mlruns` and capture the row-grain runs
(`compare_fila.png`) and the window-grain runs (`compare_ventana.png`), with the
metric and time columns visible.
Acceptance: both files exist under `docs/evidencia/mlflow/`; the row capture does
not show 4.338 and the window capture does not show 7.3404.

### [x] 4.2 Production-run capture
Capture `prod__bundle_c` with its params, four SHAs and metrics.
Acceptance: `run_prod.png` shows 4.338 / 3.227 / 0.9461 / 2336.2 and at least the
four SHA parameter names.

### [x] 4.3 Dashboard capture
Start the Streamlit dashboard and capture the production landing page.
Acceptance: `docs/assets/dashboard_ds02.png` exists and the page shows the
bundle C metrics; the README references it.

---

## Phase 5 — README

### [x] 5.1 Spanish README
Add the dashboard capture, the MLflow section with two separated tables and
explicit `rmse_val` / `rmse_test` columns, the three selected objects, the two
comparison captures and the command to open the store.
Acceptance: the table does not mix row and window grains; the class test table
and the validation table are distinguishable; `docs/evidencia/mlflow/comparativa.csv`
is linked.

### [x] 5.2 English README
Mirror the same section and labels in `README.en.md`.
Acceptance: same 13 runs and same metric labels; no “MLflow out” claim.

---

## Phase 6 — Surfaces and obsolete plan

### [x] 6.1 Update the seven surfaces
`docs/chuleta-defensa.md`, `docs/defensa/guiones-15min.md`,
`docs/presentacion/presentacion-ds02.html`,
`MLProyectVault/10-Conceptos/c27-mlflow.md`,
`MLProyectVault/20-Sistema/s14-app-y-despliegue.md`,
`src/clase/README.md`, `openspec/config.yaml` (plus `README`/`README.en` already
covered in phase 5).
Acceptance: `grep -rn "MLflow fuera\|MLflow queda pendiente\|MLflow pendiente\|sin mlflow"`
over those active files returns no hits (historical audit/plan files excepted).

### [x] 6.2 Supersede the obsolete plan
Add a “SUPERSEDED” header to `docs/pendiente/plan-cierre-rubrica.md`, pointing to
this change and to `docs/plans/plan-mlflow-pia4-10.md`.
Acceptance: the header is present; the file is not cited as current.

---

## Phase 7 — Test and gate

### [x] 7.1 Store test
`tests/test_mlflow_backfill.py` reads the store from disk (no server), asserts
13 active runs, 9/4 by grain, unique `run_key`, the production SHAs, the absence
of `tiempo_s` for EMA5, the export/store agreement and the absence of artifacts.
Acceptance: `python -m pytest tests/test_mlflow_backfill.py -q -rs` → 0 failed,
0 skipped.

### [x] 7.2 Full suite and gates
Run `python -m pytest tests -q -rs`, `python scripts/freeze_rules_evidence.py`
and `python scripts/freeze_oof_instrument.py --check`.
Acceptance: all exit 0; the coverage is still 0.901643; the five contract hashes
match the preflight snapshot.

### [x] 7.3 Final tree
`git status --short`; confirm no `.ipynb` is modified or executed and no binary is
staged under `mlruns/`.
Acceptance: no notebook in the diff; no binary in the store.

---

## Stop condition

Phase 8 from the plan — executing the seven notebooks — is **not** part of this
change. The user runs it separately. This change closes at phase 7.

---

## Verification (2026-11-09)

- `python scripts/backfill_mlflow.py --check`: 13 runs (9 fila + 4 ventana), export == store, no artifacts.
- `python -m pytest tests/test_mlflow_backfill.py -q -rs`: 11 passed.
- `python -m pytest tests -q -rs`: **406 passed** in 212.12 s.
- `python scripts/freeze_rules_evidence.py`: exit 0; coverage **0.901643**; 14 915 pure OOF rows.
- `python scripts/freeze_oof_instrument.py --check`: exit 0; 14 915 rows; band reproduces.
- `sha256sum -c .pytest_cache/hashes-pre-notebooks.txt`: 5/5 OK.
- `git status --short -- '*.ipynb'`: empty; no model or notebook was modified.

Detailed evidence: [`verify-report.md`](verify-report.md).
