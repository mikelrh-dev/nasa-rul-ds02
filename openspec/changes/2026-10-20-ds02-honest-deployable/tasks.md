# Tasks: DS02 honest protocol and deployable artifact

**Change:** `2026-10-20-ds02-honest-deployable`
**Status:** Implemented
**Spec:** [spec.md](spec.md) · [proposal](proposal.md)

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 0.1 | Register the `.venv` as the `ds02-venv` kernel and point the notebook at it | Done | `jupyter kernelspec list` shows `ds02-venv`; notebook `kernelspec.name == "ds02-venv"` |
| 0.2 | `git init` + `.gitignore` covering `archive/` (15 GB) and `.venv/` | Done | `git status` does not list the dataset |
| 0.3 | Extract legacy weights under Python 3.10 (`scripts/extract_legacy_artifact.py`) | Done | 20 arrays, 154 253 params, reference predictions written |
| 1.1 | Create `src/ds02_rul/` package with the four public names | Done | `import ds02_rul` in 3.12; `__version__ == 4.1.0` |
| 1.2 | `LastStepPooling` registered layer replacing the bare `Lambda` | Done | `LastStepPooling()(z) == z[:, -1, :]`; no `Lambda` in the graph |
| 1.3 | Transfer legacy weights into a rebuilt graph | Done | max abs difference **0.000e+00** on a fixed input |
| 1.4 | Re-package the bundle with module-qualified classes, graph detached | Done | `joblib.load` in a clean 3.12 process; 0 `__main__` references |
| 1.5 | Native `models/bilstm_ds02.keras` + `scaler.joblib` + `ds02_manifest.json` | Done | `.keras` round-trip inside 3.10 also `0.000e+00` |
| 2.1 | Split the units **before** any `.fit()` | Done | `scaler.n_samples_seen_ == 44 982` (5 fit units), not 52 635 (6) |
| 2.2 | `fit_preprocessing` fitted on fit units only, refit per CV fold | Done | holdout unit contributes 0 rows to every transform |
| 2.3 | Grouped out-of-fold `beta` selection (`GroupKFold`, 3 folds) | Done | per-fold assertion that no unit crosses fit/score; spread reported |
| 2.4 | Legacy in-sample protocol retained as a labelled diagnostic | Done | reproduces the 13x signature |
| 2.5 | `cyc_norm` ablation **measured**, plus per-engine baseline delta | Done | table computed on test units, incl. BiLSTM variants |
| 3.1 | Three seeds, mean ± std, with per-seed detail | Done | `seed_summary` output in the notebook |
| 3.2 | Remove the silent C-MAPSS FD001 fallback | Done | `resolve_ds02` raises and names the probed paths |
| 3.3 | Save-path guard: refuse non-DS02 shaped bundles | Done | `assert_ds02_artifact` |
| 4.1 | Contract tests | Done | 10/10 in `tests/test_artifact_contract.py` |
| 4.2 | `scripts/predict_ds02.py` CLI, independent of the notebook | Done | `--unit 11 --window 0` returns a finite RUL |
| 4.3 | FastAPI `/health`, `/units`, `/predict` | Done | `app/api.py` |
| 4.4 | Streamlit dashboard for units 11/14/15 | Done | `app/dashboard.py` |
| 4.5 | Dockerfile + docker-compose | Done (not built) | `docker compose config` parses; image build not exercised here |
| 5.1 | Regenerate the notebook from the builder, never by hand | Done | `scripts/build_02_notebook.py` is a pure `nbformat` emitter |
| 5.2 | Execute the notebook and keep the outputs | Done | `02_DS02_ensemble_RUL.ipynb` carries executed outputs |
| 5.3 | Update the deployed spec's known-limitations table | Done | limitations 1, 2, 4, 7, 9 closed; 3, 5, 10 restated |

## Deviations from the original plan

| Planned | Actual | Reason |
| --- | --- | --- |
| `STRIDE = 20` with `WINDOW_SIZE = 50` | `STRIDE = 100`, `WINDOW = 50` | Measured: 114 rows per flight cycle at STRIDE=100, so STRIDE=20/W=50 spans **0.088** cycles — a 5× *reduction* in horizon, the opposite of the stated intent |
| Recover `ds02_ensemble.py` from the `.pyc` | `npz` weight extraction under 3.10 | A `.pyc` yields module `ds02_ensemble`, but the pickle records `__main__`; and the 3.10-written `Lambda` cannot be unmarshalled by 3.12 at all |
| Assert `cyc_norm` costs 13.349 RMSE | Measured on this design | 13.349 belongs to iteration 3 (78 features, no residualisation) |
| 6-fold GroupKFold × 3 seeds | 3-fold, `beta` on seed 42, metrics on 3 seeds | 21 base fits would be ~5 h on CPU |
