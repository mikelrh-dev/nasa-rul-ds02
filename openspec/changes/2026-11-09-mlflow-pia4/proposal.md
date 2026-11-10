# Proposal: MLflow experiment tracking for PIA-4

**Change:** `2026-11-09-mlflow-pia4`
**Status:** Implemented — verified 2026-11-09; extended 2026-11-10 with the 4 `cyc_norm` ablation runs
**Capability:** `rul-prediction-ds02` (ADDED: experiment tracking)
**Branch:** `mlflow-pia4`
**Date:** 2026-11-09

---

## Why

PIA-4 (“Registra los experimentos en MLflow”, 20 % of PIA) is at 0: `mlflow` is not
installed, there is no `mlruns/` store and there are no captures. SAA additionally
requires a comparison table “taken from MLflow”, with a capture, in the README.
The models and metrics already exist in `resultados/` and `models/ds02_manifest.json`,
so the gap is evidence, not training.

The project MUST NOT retrain, move a defended figure, touch `models/`, the manifest,
the calibration band or the bundle. A backfill from already-measured CSVs is the only
approach that satisfies both the rubric and the byte-compatibility contract.

## Scope

**In scope**

- One experiment, `ds02-clase`, with **17 runs**:
  - `grano=fila` (9): 5 classical models (`regresion`, `knn`, `rf`, `svm`, `xgb`)
    and 4 MLPs (`base`, `E1_capacidad`, `E2_reg_lr`, `E3_batch`).
  - `grano=ventana` (4): `bundle__lgbm_c`, `bundle__bilstm_c`,
    `bundle__bilstm_ema5`, `prod__bundle_c`.
  - `familia=ablacion_cycnorm` (4): `ablacion__off__bilstm_ema5`,
    `ablacion__off_delta__bilstm_ema5`, `ablacion__on__bilstm_ema5` and
    `ablacion__on_delta__bilstm_ema5` (2×2 over BiLSTM+EMA5, test 11/14/15, seed 42,
    registered without retraining from `resultados/ablacion_cycnorm.csv`).
- A text-only file store under `mlruns/`, versioned; artifacts and `.trash/` ignored.
- `scripts/backfill_mlflow.py` with `--write`, `--check` and `--export`.
  `--write` is idempotent by the `run_key` tag; `--check` asserts exactly 17 active
  runs, one per key, with the expected params, metrics and tags.
- `docs/evidencia/mlflow/comparativa.csv`, generated from the MLflow API, with
  `run_id` per row (17 rows).
- Two comparison captures (one per grain) and one production-run capture in
  `docs/evidencia/mlflow/`; one dashboard capture in `docs/assets/`.
- README / README.en: the MLflow table with explicit `rmse_val` and `rmse_test`
  columns, the three selected objects and the capture.
- Update every active surface that still says “MLflow fuera”:
  `docs/chuleta-defensa.md`, `docs/defensa/guiones-15min.md`,
  `docs/presentacion/presentacion-ds02.html`,
  `MLProyectVault/10-Conceptos/c27-mlflow.md`,
  `MLProyectVault/20-Sistema/s14-app-y-despliegue.md`,
  `src/clase/README.md` and `openspec/config.yaml`.
- Mark `docs/pendiente/plan-cierre-rubrica.md` as superseded: it explicitly plans
  “sin MLflow”.

**Out of scope**

- Re-executing the notebooks. The user will do that separately; this change MUST NOT
  modify or execute any `.ipynb`.
- n8n / MIA-3, retraining, refitting, recalibration.
- `mlflow.log_model`, the Model Registry, `autolog`, model signatures,
  `mlflow.data` dataset copies, a tracking server, SQLite, nested runs or per-run
  figures. They add binaries, state or duplication without adding rubric evidence.
- Any change to `models/`, `src/mia/calibracion_banda.json`,
  `src/mia/instrumento_oof.npz`, `app/cache/` or the deployed bundle.

## Capability

`rul-prediction-ds02` — **ADDED** requirement: the experiment-tracking contract.
No delta in `ds02-dss-ui`, `ds02-rules-engine` or `ds02-live-evaluation`: MLflow
records evidence, it does not change inference, the rules layer or the UI.

## Artifacts that stay byte-compatible

| Artifact | SHA-256 that MUST remain |
| --- | --- |
| `models/ensemble.joblib` | `d6c701429eed8623a9d900d922aca1922427d08ff8b4ec00604b8116c1a952dd` |
| `models/bilstm_ds02.keras` | `bf9620a7de3bf9f8efa65c1993a96d8a95b903dc6fde72c772aa316f4c042219` |
| `models/ds02_manifest.json` | `1085dd67aed8179174996f3939bd7715f757f954a822d440a093dd847d3eb8c9` |
| `src/mia/calibracion_banda.json` | `162db707034ac7029aef9d8876d60d03580a109a1d8c58536dcfa780989dfd41` |
| `src/mia/instrumento_oof.npz` | `04d972ed2f30d8c1b1c5e42f1592ba6c474bcf3300deaa2dfd8402479f3629b2` |

Coverage of the R6 band MUST remain `0.901643`.

## Rollback plan

- Remove `mlflow==3.18.0` from `requirements.txt` and `pyproject.toml`; run `uv lock`.
- Delete `scripts/backfill_mlflow.py`, `tests/test_mlflow_backfill.py`,
  `mlruns/` and `docs/evidencia/mlflow/`.
- Remove the dashboard capture and revert the README / README.en sections.
- Revert the seven surface edits and `docs/pendiente/plan-cierre-rubrica.md`.
- No data migration, no model artifact and no cache is involved; rollback risk is ~0.

## Success criteria

- [x] Exactly 17 active runs in `ds02-clase`: 9 `grano=fila`, 4 `grano=ventana`
      and 4 `familia=ablacion_cycnorm`.
- [x] Every run has a unique `run_key`, a `grano`, a `familia`, an `origen` and its
      measured params/metrics; `tiempo_s` is present except for `bundle__bilstm_ema5`,
      which was never timed (blank, not zero).
- [x] `scripts/backfill_mlflow.py --check` exits 0; the pytest test reads the store
      from disk with 0 skips.
- [x] `docs/evidencia/mlflow/comparativa.csv` has 17 rows, one `run_id` per row, and
      matches the store.
- [x] README / README.en contain the two separated tables, with `rmse_val` and
      `rmse_test` explicitly labelled, and the captures.
- [x] No active surface says MLflow is out or pending.
- [x] No file under `mlruns/**/artifacts/`; the five hashes above do not move.
- [x] No notebook is modified or executed by this change.

Detailed evidence: [`verify-report.md`](verify-report.md).
