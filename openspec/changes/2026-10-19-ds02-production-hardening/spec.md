# Spec: DS02 Production Hardening

**Change:** `2026-10-19-ds02-production-hardening`
**Status:** Proposed
**Date:** 2026-10-19
**Capability:** [`rul-prediction-ds02`](../../specs/rul-prediction-ds02/spec.md)

---

## 1. Functional Requirements

### FR-1: Importable pipeline module

`SensorResidualizer` and `HybridStackingEnsemble` MUST live in an importable package
(`src/ds02_rul/`), not inside the notebook. Moving them MUST be a verbatim relocation: no
formula, hyperparameter, attribute name or return value may change. `causal_ema_by_unit` and
`calculate_nasa_score` MUST move with them, so that the object graph reachable from
`ensemble.joblib` contains no reference to `__main__`.

### FR-2: Native Keras persistence with serializable pooling

The Keras sub-model MUST be persisted in the native `.keras` format, and MUST NOT rely on a
`Lambda` layer that wraps a bare Python lambda. The last-step slice MUST be expressed as a
serializable layer (or an equivalent registered function) so the model can be reconstructed
from disk without access to the defining module's runtime state. Persisting the Keras model as
a legacy HDF5 `.h5` file SHALL be treated as non-compliant.

The persisted artifact MUST additionally be loadable by a Python minor version **other** than
the one that wrote it. A `Lambda` that wraps a bare lambda is serialized as marshalled Python
bytecode, and `marshal`'s code-object format is version-specific; the current artifact is
therefore loadable under Python 3.10 but raises
`ValueError: bad marshal data (unknown type code)` under Python 3.12, even when the
`__main__` dependency is shimmed away. A round-trip verified only inside a single interpreter
SHALL NOT be accepted as evidence of this requirement.

### FR-3: Out-of-sample beta selection

`beta` MUST be selected by grouped cross-validation **over the train units**, and the
meta-learners used to score a given unit MUST NOT be fit on that unit's rows. The selection
MUST be aggregated across folds (median) and the spread MUST be reported alongside the
selected value. Selecting `beta` on rows that fitted the meta-learners SHALL be treated as
non-compliant.

### FR-4: Multi-seed evaluation protocol

Model quality MUST be reported across multiple seeds as mean ± standard deviation, not as a
single-seed point estimate. The seed set MUST include at least three seeds and MUST include
`42`. Any run that breaches the per-epoch compute budget MUST be flagged and excluded from the
aggregate, and the number of excluded runs MUST be reported.

### FR-5: DS02 inference entry point

A stable entry point `scripts/predict_ds02.py` MUST return a RUL for a DS02 window without
importing the notebook. It MUST NOT read, modify or depend on `scripts/predict.py`, which
serves the FD001 v3 bundle.

### FR-6: Artifact manifest and provenance

Every persisted artifact MUST be accompanied by a manifest recording at least: an artifact
format version, the code version, the seed, the DS02 unit partition, the training-unit data
fingerprint, and the recorded metrics of the run that produced it.

## 2. Non-Functional Requirements

### NFR-1: Backwards compatibility of predictions

The extracted module MUST reproduce the recorded metrics
([deployed spec](../../specs/rul-prediction-ds02/spec.md#requirement-recorded-sota-results)):
LightGBM standalone RMSE 7.087 / NASA 5768.4, BiLSTM RMSE 5.693 / NASA 3822.2, BiLSTM + EMA
RMSE 5.597 / NASA 3716.8, and hybrid RMSE 5.522 / NASA 3435.1. Any deviation of more than
`1e-6` on RMSE indicates the relocation was not verbatim.

### NFR-2: No notebook hand-edits

`02_DS02_ensemble_RUL.ipynb` MUST NOT be hand-edited. It MUST be regenerated from
`scripts/build_02_notebook.py`. The builder MUST remain a pure `nbformat` emitter that does not
execute the notebook and does not write or load artifacts.

### NFR-3: Deterministic seeding per run

Each evaluation run MUST set `numpy`, TensorFlow and LightGBM seeds from a single `SEED` value.
`random_state` MUST be threaded explicitly into every estimator. Two runs with the same seed
and the same data fingerprint MUST produce identical metrics.

### NFR-4: Artifact and compute budget

The `.keras` artifact SHOULD stay below 10 MB and the total artifact directory below 15 MB.
Grouped beta selection MUST complete within 6 base-model fits — one per held-out unit — and
MUST NOT require a nested refit per fold. A single seed's full pipeline SHOULD complete within
20 minutes on the reference machine.

### NFR-5: No `__main__` dependency at load time, and no interpreter binding

Loading any persisted artifact MUST NOT require any class, function or name to be defined in
`__main__`. This SHALL be verified by loading in a subprocess whose `__main__` contains nothing
but the load call.

Loading any persisted artifact MUST NOT require the Python minor version that wrote it. This
SHALL be verified by loading the artifact under at least one interpreter other than the one
that produced it — concretely, the artifact written under Python 3.10 MUST load under the
repository's Python 3.12 virtualenv.

## 3. Acceptance Criteria

- [ ] **AC-1**: `python -c "import joblib; e = joblib.load('ensemble.joblib')"` succeeds in a fresh process with no notebook and no `__main__` definitions.
- [ ] **AC-2**: The Keras sub-model round-trips through `.keras` and produces predictions identical to the pre-switch model on a fixed input window (max absolute difference `0`).
- [ ] **AC-3**: The serializable last-step layer produces output equal to `z[:, -1, :]` on a fixed tensor, and the pooled head remains 384-dimensional.
- [ ] **AC-4**: Beta is selected by grouped cross-validation; the selected value, the per-fold values, and the spread (min, max, IQR) are all reported.
- [ ] **AC-5**: In the beta selection, no fold's meta-learner is fit on the rows it scores — asserted directly in the harness and printed in the run log.
- [ ] **AC-6**: Multi-seed evaluation reports mean ± std for RMSE, MAE, R² and NASA score over at least three seeds, and reports the count of excluded starved runs.
- [ ] **AC-7**: `python scripts/predict_ds02.py --unit 11 --window 0` returns a finite RUL, and `scripts/predict.py` is byte-identical to its pre-change state.
- [ ] **AC-8**: `models/ds02_manifest.json` exists and contains version, code version, seed, unit partition, data fingerprint and recorded metrics.

## 4. Scenarios

### Scenario 1: Loading the artifact in a clean process

```text
Given a fresh Python interpreter with no notebook and an empty __main__ namespace
When ensemble.joblib is loaded from models/
Then the object is reconstructed successfully
And inference on the recorded sample window returns a RUL of 61.25
```

### Scenario 2: Keras format round-trip

```text
Given a trained BiLSTM sub-model held in memory
When it is saved to model.keras and reloaded in a new process
Then the reloaded model produces predictions identical to the original
And no Lambda-with-bare-lambda layer appears in the reloaded graph
```

### Scenario 3: Beta selection is out-of-fold

```text
Given the six train units and their windowed features
When grouped out-of-fold beta selection runs
Then each fold's meta-learners are fit only on units other than the scored unit
And the reported beta is the median across the six folds
And the selection spread is reported
```

### Scenario 4: Multi-seed reporting

```text
Given the configured seed list
When the evaluation harness runs each seed to completion
Then per-seed metrics are recorded for all four models
And an aggregate mean and standard deviation are reported per metric
And the number of runs excluded by the compute-budget guard is reported
```

### Scenario 5: Compute starvation is flagged, not averaged in

```text
Given a run in which one epoch exceeds the per-epoch budget
When the harness aggregates results
Then that run is marked starved and excluded from the aggregate
And its metrics are still recorded separately for inspection
```

### Scenario 6: Entry point parity with the module

```text
Given the module and the CLI entry point
When the same DS02 window is scored through both
Then both return the same RUL value
And neither imports the notebook
```

### Scenario 7: Notebook regeneration is reproducible

```text
Given the modified scripts/build_02_notebook.py
When it is run
Then it emits the notebook deterministically
And running it twice produces byte-identical output
And no cell executes during generation
```

### Scenario 8: Provenance is recorded

```text
Given a completed hardened run
When the manifest is written
Then it contains the format version, code version, seed, unit partition, data fingerprint and metrics
And the fingerprint changes if the ingested DS02 window count changes
```

## 5. Technical Specification

### 5.1 Target module layout

```text
src/
└── ds02_rul/
    ├── __init__.py        # public exports: SensorResidualizer, HybridStackingEnsemble,
    │                      # causal_ema_by_unit, calculate_nasa_score, evaluate_predictions
    ├── residualizer.py    # SensorResidualizer
    ├── ensemble.py        # HybridStackingEnsemble
    ├── pooling.py         # LastStepPooling (serializable last timestep slice)
    ├── smoothing.py       # causal_ema_by_unit
    ├── metrics.py         # calculate_nasa_score, evaluate_predictions
    ├── stacking.py        # grouped out-of-fold beta selection
    └── persistence.py     # save_ensemble / load_ensemble / write_manifest
```

### 5.2 Function signatures

```python
# residualizer.py
class SensorResidualizer:
    def __init__(self, poly, ridges, res_scaler) -> None: ...
    def transform(self, W_scaled: np.ndarray, Xs_raw: np.ndarray) -> np.ndarray: ...

# pooling.py
class LastStepPooling(tf.keras.layers.Layer):
    """Serializable replacement for Lambda(lambda z: z[:, -1, :])."""
    def call(self, inputs): ...          # returns inputs[:, -1, :]
    def get_config(self) -> dict: ...    # required for native .keras round-trip

# ensemble.py
class HybridStackingEnsemble:
    def __init__(self, bilstm_model, lgb_standalone, ridge_meta, lgb_meta, residualizer,
                 scaler, scaler_w, n_op: int, window_size: int = 50,
                 beta: float = 1.0, ema_span: int = 5) -> None: ...
    def predict(self, X_raw_windows: np.ndarray, cycles: np.ndarray,
                units: np.ndarray | None = None) -> np.ndarray: ...

# smoothing.py
def causal_ema_by_unit(pred, units, cycles, span: int = 5) -> np.ndarray: ...

# metrics.py
def calculate_nasa_score(y_true, y_pred) -> float: ...
def evaluate_predictions(y_true, y_pred, model_name: str = "Model") -> dict: ...

# stacking.py
def select_beta_grouped(units, cycles, y, pred_lstm, pred_lgb,
                        beta_grid=None, span: int = 5) -> dict: ...

# persistence.py
def save_ensemble(ensemble, scaler, out_dir: str) -> dict: ...
def load_ensemble(path: str): ...
def write_manifest(path: str, manifest: dict) -> None: ...
```

### 5.3 Beta selection algorithm

Grouped **out-of-fold** selection. The base models are fit once per held-out unit; the
meta-learners used to score a unit never see that unit's rows.

```text
INPUT   units, cycles, y, X_seq, X_tab over the six train units {2, 5, 10, 16, 18, 20}
OUTPUT  beta_hat, folds[], spread

# Phase A — one base-model fit per held-out unit (6 fits, no nested refit)
for u in sorted(train_units):
    bilstm_u, lgbm_u = fit_base_models(train_units \ {u})
    oof_pred_lstm[u] = bilstm_u.predict(u)          # unit u never seen by either base model
    oof_pred_lgb[u]  = lgbm_u.predict(u)
    rmse_ref[u], nasa_ref[u] = metrics(y_u, oof_pred_lstm[u])

# Phase B — meta-learners for scoring unit u are fit on units v != u only
for u in sorted(train_units):
    Z_other = concat([oof_pred_lstm[v], oof_pred_lgb[v], cyc_norm_v, y_v] for v != u)
    ridge_u     = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(Z_other, y_other)
    lgbm_meta_u = LGBMRegressor(max_depth=3, num_leaves=7, n_estimators=120,
                                learning_rate=0.03, min_child_samples=20).fit(Z_other, y_other)

    Z_u     = column_stack([oof_pred_lstm[u], oof_pred_lgb[u], cyc_norm_u])
    p_meta_u = 0.5 * ridge_u.predict(Z_u) + 0.5 * lgbm_meta_u.predict(Z_u)

    for beta in linspace(0, 1, 21):
        p_raw = oof_pred_lstm[u] + beta * (p_meta_u - oof_pred_lstm[u])
        p     = causal_ema_by_unit(p_raw, units=u, cycles_u, span=5)
        criterion[beta] = rmse(y_u, p) / rmse_ref[u] + nasa(y_u, p) / nasa_ref[u]

    folds[u] = argmin(criterion)

beta_hat = median(folds)
spread   = (min(folds), max(folds), iqr(folds))
```

Invariants the harness MUST assert and print:

- `u` is absent from both the base-model fit set (Phase A) and the meta fit set (Phase B).
- Every fold's criterion is computed on the EMA-smoothed prediction, `span = 5`.
- `beta = 0` is part of the grid, so degrading to the plain BiLSTM stays reachable.

The legacy single-unit protocol is retained as a **diagnostic** only: it reproduces
`opt_beta = 1.00` and exists to demonstrate the in-sample bias, not to select a value.

### 5.4 Persistence call

```python
# Native Keras artifact — replaces the bare-lambda Lambda layer and the joblib-embedded graph
model = build_champion_bilstm(input_shape=(50, 19), dense_units=32, seed=SEED)
model.save("models/bilstm_ds02.keras")     # native format, serializable pooling

# Bundle
joblib.dump(ensemble, "ensemble.joblib")          # references ds02_rul.*, never __main__.*
joblib.dump(scaler, "scaler.joblib")
write_manifest("models/ds02_manifest.json", {
    "format_version": 1,
    "code_version": "<git describe or file hash>",
    "seed": SEED,
    "unit_partition": {"fit": [2, 5, 10, 18, 20], "holdout": [16], "test": [11, 14, 15]},
    "data_fingerprint": "<hash of ingested shapes + first/last rows per unit>",
    "metrics": {...},
})
```

### 5.5 Multi-seed harness

```text
seeds = [42, 7, 2024]                      # 42 and 7 from probe_cyclech.py; 2024 from probe_variants.log
EPOCH_BUDGET_S = 135                       # 10x the recorded mean of 147.99 s / 11 epochs ~= 13.45 s/epoch

for seed in seeds:
    run = execute_pipeline(seed=seed, epochs=22, batch_size=128)
    starved = any(epoch_time > EPOCH_BUDGET_S for epoch_time in run.epoch_times)
    record(seed, run.metrics, starved, run.epoch_times)

valid = [r for r in runs if not r.starved]
report per model: mean +/- std over valid runs for RMSE, MAE, R2, NASA
report excluded_count = len(runs) - len(valid)
```

A starved run is flagged and excluded, never silently averaged in — the recorded 1553 s epoch
is the concrete case a naive comparison would wrongly include.

### 5.6 Reference metrics to reproduce

| Model | RMSE | MAE | R² | NASA score |
| --- | --- | --- | --- | --- |
| LightGBM standalone (quantile 0.35, 93 feat) | 7.087 | 5.584 | 0.8562 | 5768.4 |
| BiLSTM 2-layer, triple pooling | 5.693 | 4.449 | 0.9072 | 3822.2 |
| BiLSTM + causal EMA | 5.597 | 4.331 | 0.9103 | 3716.8 |
| Hybrid stacking (beta=1.00, EMA span=5) | 5.522 | 4.795 | 0.9127 | 3435.1 |

## 6. Test Requirements

No test runner is configured, so verification is **execution-based** and MUST be scripted so
that it is repeatable:

1. **Import isolation test** — load each persisted artifact in a subprocess whose `__main__`
   contains only the load call. Closes AC-1.
2. **Format round-trip test** — save the Keras model to `.keras`, reload, and assert
   prediction equality on a fixed input window. Closes AC-2.
3. **Layer equivalence test** — assert `LastStepPooling()(z) == z[:, -1, :]` on a fixed tensor
   and that the concatenated pooled width is 384. Closes AC-3.
4. **Out-of-fold assertion** — the beta harness MUST assert per fold that the scored unit is
   absent from both fit sets, and print the result. Closes AC-4, AC-5.
5. **Metric reproduction test** — the module MUST reproduce all four rows of §5.6 to `1e-6` on
   RMSE when driven by the recorded artifacts. Closes NFR-1.
6. **Seed determinism test** — two runs at the same seed MUST produce identical metrics.
   Closes NFR-3.
7. **Entry-point parity test** — the CLI and the module MUST return the same RUL for the same
   window; `scripts/predict.py` MUST be unchanged. Closes AC-7.
8. **Manifest test** — the manifest MUST be present and complete, and its fingerprint MUST
   change when the ingested window count changes. Closes AC-8.

## 7. Edge Cases

| # | Edge case | Expected behaviour |
| --- | --- | --- |
| 1 | Artifact loaded in a process where `ds02_rul` is not importable | Raise a clear `ImportError` naming the package and the install path; never a bare `AttributeError: __main__` |
| 2 | `.keras` file written by an older TF version | Refuse to load with an explicit version message rather than partially reconstructing the graph |
| 3 | A fold's held-out unit has fewer rows than the meta-learner needs | Fail the fold loudly; do not silently shrink the meta training set |
| 4 | All folds select `beta = 0` | Report `beta_hat = 0` and note that the ensemble degrades to the BiLSTM; the hybrid row then equals the smoothed BiLSTM row |
| 5 | `beta` selection produces a bimodal fold distribution | Report the full fold vector; a median alone is misleading |
| 6 | Only one seed completes within the compute budget | Report the single seed but state explicitly that no standard deviation is available |
| 7 | A run is starved on the first epoch | Exclude the run and mark the whole seed invalid rather than aggregating a truncated history |
| 8 | Empty or single-cycle window passed to the CLI | Raise a validation error stating the 50-cycle minimum; do not return a prediction |
| 9 | `units=None` supplied to `predict` | Treat all windows as one unit, as today, and note the EMA is then not per-engine |
| 10 | Predictions slightly negative before clipping | Clip at zero and record the pre-clip minimum in the manifest for traceability |
| 11 | The DS02 HDF5 is missing and the FD001 fallback would fire | Abort the DS02 entry point with an explicit error; never fall back to FD001 silently |
| 12 | Manifest exists but the artifact hash does not match | Warn loudly and refuse to treat the manifest as provenance |

## 8. Test Command

No test runner is configured for this project, so verification is notebook- and script-driven:

```bash
# 1. Re-execute the reference notebook and compare the four recorded test rows
jupyter nbconvert --to notebook --execute 02_DS02_ensemble_RUL.ipynb

# 2. Verify artifact loadability in a clean process (closes AC-1)
python -c "import joblib; e = joblib.load('models/ensemble.joblib'); print(e.paradigm)"

# 3. Run grouped out-of-fold beta selection (closes AC-4, AC-5)
python -m ds02_rul.stacking --out models/beta_selection.json

# 4. Multi-seed harness (closes AC-6)
python -m ds02_rul.harness --seeds 42 7 2024 --out models/multiseed.json

# 5. Entry-point smoke test (closes AC-7)
python scripts/predict_ds02.py --unit 11 --window 0
```

## 9. Dependencies

| Dependency | Version | Role |
| --- | --- | --- |
| Python | 3.12 (`.venv`) | Runtime |
| TensorFlow | 2.21.0 | BiLSTM, native `.keras` serialization |
| LightGBM | 4.6.0 | Standalone quantile model, meta-learner |
| scikit-learn | current | `StandardScaler`, `PolynomialFeatures`, `Ridge`, `RidgeCV`, metrics |
| numpy, pandas | current | Array and window handling |
| joblib | current | Bundle persistence |
| h5py | current | DS02 HDF5 ingestion |
| nbformat | current | Notebook generation from `scripts/build_02_notebook.py` |
| matplotlib | current | Diagnostic plots in the notebook |

Internal dependencies: [deployed spec](../../specs/rul-prediction-ds02/spec.md),
[project context](../../project.md), [design](design.md), [tasks](tasks.md).

The change introduces **no new third-party dependency**.

---

## See also

- [Proposal](proposal.md) — why this change exists
- [Capability delta](specs/rul-prediction-ds02/spec.md) — requirement-level changes
- [Design](design.md) — architecture, decisions, migration
- [Tasks](tasks.md) — phased execution
