# Tasks: DS02 Production Hardening

**Change:** `2026-10-19-ds02-production-hardening`
**Status:** Proposed
**Date:** 2026-10-19
**Spec:** [spec.md](spec.md) · [capability delta](specs/rul-prediction-ds02/spec.md) · [design.md](design.md)
**Rollback anchor:** every phase is reversible by restoring the archived baseline artifacts.

> 📌 **Standing constraint:** never hand-edit `02_DS02_ensemble_RUL.ipynb`. Regenerate it from
> `scripts/build_02_notebook.py`. Never touch `scripts/predict.py`, `models/v3_bundle.joblib`,
> `archive/`, or the FD001 pipeline.

---

## Phase 0: Freeze the baseline

Closes the precondition for every later phase: without an archived baseline, no phase can be
proven behaviour-preserving.

- [ ] **0.1** Copy `ensemble.joblib` and `scaler.joblib` (and their `models/` copies) to a
  timestamped baseline directory outside the change scope.
  **Closes:** baseline artifacts exist and are byte-identical to the pre-change state.
- [ ] **0.2** Record the four test rows of
  [§5.6](spec.md#56-reference-metrics-to-reproduce) into a baseline metrics file, together with
  the window counts (`17450` train, `6196` test), the holdout window count (`2535`) and the
  artifact-reload check (`61.25` predicted vs `58.00` true).
  **Closes:** every number this change must not move is written down in one place.
- [ ] **0.3** Record `genesis` - the hash of `02_DS02_ensemble_RUL.ipynb` and of
  `scripts/build_02_notebook.py` - as the reference source revision.
  **Closes:** the reference implementation is pinned by hash.
- [ ] **0.4** Put the repository under version control (`git init` plus a first commit) before
  any phase starts, and record that commit id in the baseline metrics file.
  **Closes:** the baseline is recoverable by checkout rather than only by the manual copy of
  task 0.1, and the lost-module failure mode of limitation 8 cannot recur.
- [ ] **0.5** Register the project virtualenv as a Jupyter kernel and repoint both notebooks at
  it: `python -m ipykernel install --user --name ds02-venv --display-name ".venv (3.12.10)"`,
  then set `kernelspec.name` to `ds02-venv` in `02_DS02_ensemble_RUL.ipynb` and
  `notebook_nasa_fd001.ipynb`. The FD001 notebook's current `display_name` reads
  `.venv (3.12.10)` while its `name` still resolves to the system Python 3.10, so the label
  must be corrected at the same time.
  **Closes:** the root cause of limitation 7 - with no kernelspec for the `.venv`, every
  notebook run resolves to the system Python 3.10.

---

## Phase 1: Extractable module

Move the pipeline into `src/ds02_rul/` with **no behaviour change**. Every line is a
relocation; nothing is refactored, renamed or "improved".

- [ ] **1.1** Create the package skeleton `src/ds02_rul/` with `__init__.py`, `residualizer.py`,
  `ensemble.py`, `smoothing.py`, `metrics.py`.
  **Closes:** each module imports cleanly in isolation.
- [ ] **1.2** Move `SensorResidualizer` to `residualizer.py` verbatim, preserving the attribute
  names `poly`, `ridges`, `res_scaler` and the `transform(W_scaled, Xs_raw)` signature.
  **Closes:** the moved class has an identical signature and produces identical residuals on a
  fixed input.
- [ ] **1.3** Move `HybridStackingEnsemble` to `ensemble.py` verbatim, preserving every
  constructor parameter (`bilstm_model`, `lgb_standalone`, `ridge_meta`, `lgb_meta`,
  `residualizer`, `scaler`, `scaler_w`, `n_op`, `window_size=50`, `beta=1.0`, `ema_span=5`) and
  the `predict(X_raw_windows, cycles, units=None)` signature.
  **Closes:** the moved class exposes the same public surface, including `paradigm`.
- [ ] **1.4** Move `causal_ema_by_unit` to `smoothing.py` and `calculate_nasa_score` plus
  `evaluate_predictions` to `metrics.py`, verbatim.
  **Closes:** `calculate_nasa_score` still returns a **sum** and still applies no 125-cycle
  clamp.
- [ ] **1.5** Export the four public names from `__init__.py` and confirm the object graph
  reachable from a freshly constructed ensemble contains no `__main__` reference.
  **Closes:** `joblib.dump` of the module's ensemble records `ds02_rul.*` class paths.
- [ ] **1.6** Drive the module against the baseline data and reproduce all four recorded rows
  to `1e-6` on RMSE.
  **Closes:** **AC-1 precondition**, **NFR-1** - the relocation is behaviour-preserving.
- [ ] **1.7** Re-package the existing artifact instead of retraining: extract the 20 weight
  arrays and the fitted estimators from the 3.10-written artifact, rebuild the graph with
  `LastStepPooling`, transfer the weights with `set_weights(...)`, and re-pickle the ensemble
  with module-qualified classes. Proven lossless on a proof of concept - the BiLSTM branch and
  the full ensemble both reproduce the 3.10 reference with a max absolute difference of
  `0.000e+00`, the re-pickled artifact contains zero `__main__` references, and it loads in a
  fresh Python 3.12 process with no shims.
  **Closes:** the deployability goal is reached **without a single gradient step**; a genuine
  re-run remains required only for the statistical fixes in Phases 3 and 4.

---

## Phase 2: Persistence

Replace the fragile `Lambda` and the `joblib`-embedded graph with a serializable layer and the
native `.keras` format, and record provenance.

- [ ] **2.1** Implement `LastStepPooling(tf.keras.layers.Layer)` in `pooling.py` with `call`
  returning `inputs[:, -1, :]`, plus `get_config` and `from_config`.
  **Closes:** **AC-3** — output equal to `z[:, -1, :]` on a fixed tensor.
- [ ] **2.2** Swap the bare `Lambda(lambda z: z[:, -1, :], name="last_step")` for
  `LastStepPooling` in the model builder (in the package; the notebook picks it up in Phase 6).
  **Closes:** **AC-3** — pooled head remains 384 wide and the three pooling branches are
  unchanged in count.
- [ ] **2.3** Persist the BiLSTM standalone to `models/bilstm_ds02.keras` and remove the Keras
  model from the `joblib` payload; keep the sklearn and LightGBM estimators in `joblib`.
  **Closes:** **AC-2** — `.keras` round-trip produces identical predictions on a fixed window.
- [ ] **2.4** Implement `save_ensemble` / `load_ensemble` in `persistence.py` as the single
  entry point for both formats.
  **Closes:** callers do not need to know which format holds which object.
- [ ] **2.5** Implement `write_manifest` emitting `models/ds02_manifest.json` with
  `format_version`, `code_version`, `seed`, `dataset` (`DS02` or `FD001`),
  `unit_partition` (`fit [2, 5, 10, 18, 20]`, `holdout [16]`, `test [11, 14, 15]`),
  `data_fingerprint` (ingested shapes plus per-unit boundary rows),
  `model_shape` (`scaler.n_features_in_`, `ensemble.n_op`, `lgb.n_features_in_`,
  `bilstm.input_shape`) and `metrics`.
  **Closes:** **AC-8**.
- [ ] **2.6** Verify artifact loadability in a subprocess whose `__main__` contains only the
  load call, and assert the reloaded ensemble reproduces the `61.25` vs `58.00` sample check.
  **Closes:** **AC-1**, **NFR-5** (first half).
- [ ] **2.7** Check the artifact size budget and record the numbers in the manifest.
  **Closes:** **NFR-4** - `.keras` under 10 MB and the artifact directory under 15 MB, or a
  documented exception.
- [ ] **2.8** Verify the artifact loads under a **different Python minor version** than the one
  that wrote it - concretely, write under Python 3.10 and load under the repository's Python
  3.12 virtualenv, and the reverse. This is the check that the current artifact fails, with
  `ValueError: bad marshal data (unknown type code)` from the `Lambda` layer's marshalled
  bytecode.
  **Closes:** **NFR-5** (second half) - a round-trip inside one interpreter is not evidence.
- [ ] **2.9** Guard the save path: assert the manifest's `dataset` is `DS02`, that
  `scaler.n_features_in_ == 18` and `ensemble.n_op == 4`, and abort the save on any mismatch
  instead of overwriting an existing artifact. The FD001 fallback in `load_rul_dataset()` is
  silent and writes to the same `ensemble.joblib` path with the same `paradigm` metadata
  string, so a 16-feature FD001 model can otherwise replace an 18-feature DS02 one unnoticed.
  **Closes:** limitation 11 of the deployed spec.

---

## Phase 3: Honest stacking

Replace single-unit, in-sample beta selection with grouped out-of-fold selection.

- [ ] **3.1** Implement `select_beta_grouped` in `stacking.py` with **Phase A** (one base-model
  fit per held-out train unit, producing out-of-fold base predictions for all six units) and
  **Phase B** (meta-learners for scoring unit `u` fit only on units `v != u`).
  **Closes:** **AC-4** — the selection runs and returns a beta per fold.
- [ ] **3.2** Add an explicit per-fold assertion that the scored unit is absent from both the
  base-model fit set and the meta-learner fit set, and print the assertion result in the run log.
  **Closes:** **AC-5** — out-of-fold property is machine-verified, not assumed.
- [ ] **3.3** Score the beta grid `linspace(0, 1, 21)` **after** applying
  `causal_ema_by_unit(..., span=5)`, using `criterion(beta) = rmse_val/rmse_ref +
  nasa_val/nasa_ref` with both references computed from the BiLSTM-only fold predictions.
  **Closes:** the criterion matches the deployed contract and `beta = 0` remains in the grid.
- [ ] **3.4** Aggregate with `beta_hat = median(folds)` and emit the full fold vector, the
  spread (min, max, IQR) and the per-fold criterion curves to `models/beta_selection.json`.
  **Closes:** **AC-4** — the spread is reported, and a bimodal distribution is visible.
- [ ] **3.5** Retain the legacy single-unit protocol as a **diagnostic** that reproduces
  `opt_beta = 1.00`, and label it as the in-sample demonstration.
  **Closes:** the in-sample bias is documented with a reproducible artefact rather than prose.
- [ ] **3.6** Re-run the hybrid evaluation with `beta_hat` and record the new test row next to
  the baseline row from Phase 0.
  **Closes:** the effect of honest selection is a measured delta, not a claim.

---

## Phase 4: Evaluation protocol

Turn single-seed point estimates into mean ± std with an explicit compute-budget guard.

- [ ] **4.1** Implement `harness.py` taking a seed list (default `[42, 7, 2024]`), running the
  full pipeline per seed, and recording per-seed metrics for all four models on test units
  `[11, 14, 15]`.
  **Closes:** **AC-6 precondition** — per-seed metrics are recorded.
- [ ] **4.2** Thread one `SEED` value into numpy, TensorFlow and LightGBM, and pass
  `random_state` explicitly into every estimator.
  **Closes:** **NFR-3** — two runs at the same seed produce identical metrics.
- [ ] **4.3** Implement the per-epoch compute-budget guard (`EPOCH_BUDGET_S = 135`, i.e. ten
  times the recorded mean of `147.99 s / 11 epochs ≈ 13.45 s/epoch`), flag any breaching run,
  exclude it from the aggregate, and still record its metrics separately.
  **Closes:** **AC-6** — starved runs are flagged and counted, never silently averaged in.
- [ ] **4.4** Emit the aggregate: mean ± std per metric per model, plus `excluded_count`, to
  `models/multiseed.json`.
  **Closes:** **AC-6** — the reporting obligation is satisfied in machine-readable form.
- [ ] **4.5** Record the multi-seed results and the seed-variance magnitude (seed 42: RMSE
  5.447; seed 7: RMSE 6.564) in the deployed spec's metrics section.
  **Closes:** the single-seed caveat becomes a recorded measurement.

---

## Phase 5: Inference entry point

- [ ] **5.1** Implement `scripts/predict_ds02.py` exposing `--unit`, `--window`, `--h5` and
  `--json`, loading through `ds02_rul.persistence.load_ensemble` and returning a finite RUL.
  **Closes:** **AC-7** — the CLI returns a RUL without importing the notebook.
- [ ] **5.2** Add input validation: reject a window shorter than 50 cycles and reject a missing
  DS02 file with an explicit DS02 error rather than falling back to FD001.
  **Closes:** edge cases 8 and 11 of [spec.md §7](spec.md#7-edge-cases).
- [ ] **5.3** Assert CLI/module parity: the same window scored through both paths returns the
  same RUL.
  **Closes:** **AC-7** — one implementation, two surfaces.
- [ ] **5.4** Verify `scripts/predict.py` is byte-identical to its pre-change state.
  **Closes:** **AC-7** — the FD001 contract is provably untouched.

---

## Phase 6: Documentation

- [ ] **6.1** Update `scripts/build_02_notebook.py` to import from `ds02_rul` instead of
  redefining the classes, keeping it a pure `nbformat` emitter that executes nothing and writes
  no artifacts.
  **Closes:** **NFR-2** precondition.
- [ ] **6.2** Regenerate `02_DS02_ensemble_RUL.ipynb` from the builder, diff it against the
  pinned `genesis` revision, and run it twice to confirm byte-identical output.
  **Closes:** **NFR-2**, and scenario 7 of [spec.md §4](spec.md#4-scenarios).
- [ ] **6.3** Re-execute the regenerated notebook and confirm all four test rows still match
  the Phase 0 baseline (or record the honest beta-selection delta from task 3.6).
  **Closes:** **NFR-1** — the module is now the source of truth and still reproduces the result.
- [ ] **6.4** Update `openspec/specs/rul-prediction-ds02/spec.md`: promoted requirements, the
  new artifact inventory, the multi-seed metrics, and the removal of limitations 1, 2, 3 and 6
  from the known-limitations table (leaving 4 and 5 as recorded).
  **Closes:** the deployed spec describes the module's contract, not the notebook's.
- [ ] **6.5** Update `openspec/project.md` with the `src/ds02_rul/` layout and the DS02 entry
  point.
  **Closes:** bootstrap context points at the real deployable path.
- [ ] **6.6** Archive the change: move `openspec/changes/2026-10-19-ds02-production-hardening/`
  into the archive tree and confirm no destructive delta is applied silently.
  **Closes:** the capability delta has been merged into the deployed spec.

---

## Acceptance traceability

| Criterion | Closed by |
| --- | --- |
| AC-1 | 2.6, 0.1 |
| AC-2 | 2.3 |
| AC-3 | 2.1, 2.2 |
| AC-4 | 3.1, 3.4 |
| AC-5 | 3.2 |
| AC-6 | 4.1, 4.3, 4.4 |
| AC-7 | 5.1, 5.3, 5.4 |
| AC-8 | 2.5 |
| NFR-1 | 1.6, 6.3 |
| NFR-2 | 6.1, 6.2 |
| NFR-3 | 4.2 |
| NFR-4 | 2.7 |
| NFR-5 | 2.6 |

## Review workload

| Phase | Estimated lines | Note |
| --- | --- | --- |
| 0 | ~0 | Artifact copies and a metrics file |
| 1 | ~220 | Mostly moved code; the diff is dominated by relocations |
| 2 | ~180 | New pooling layer, persistence module, manifest |
| 3 | ~160 | Grouped selection plus the legacy diagnostic |
| 4 | ~140 | Harness, guard, aggregation |
| 5 | ~110 | CLI plus validation |
| 6 | ~120 | Builder edits and documentation |
| **Total** | **~930** | Above a 400-line review budget: chained PRs per phase |

Each phase is independently reviewable and independently revertible; Phases 1–6 in order are
the recommended PR chain.
