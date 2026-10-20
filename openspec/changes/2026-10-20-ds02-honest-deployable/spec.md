# Spec delta: DS02 honest protocol and deployable artifact

**Change:** `2026-10-20-ds02-honest-deployable`
**Status:** Implemented
**Capability:** [`rul-prediction-ds02`](../../specs/rul-prediction-ds02/spec.md)

---

## ADDED

### Requirement: Importable object graph

`SensorResidualizer`, `HybridStackingEnsemble`, `causal_ema_by_unit` and
`calculate_nasa_score` SHALL live in the `ds02_rul` package. Loading
`models/ensemble.joblib` SHALL NOT require any name to be defined in `__main__`.

#### Scenario: clean process
- GIVEN a Python 3.12 interpreter with an empty `__main__`
- WHEN `joblib.load('models/ensemble.joblib')` runs
- THEN the object is reconstructed and `paradigm`, `n_op`, `window_size`, `beta`
  and `ema_span` are readable

### Requirement: Version-independent serialisation

The Keras graph SHALL be persisted in the native `.keras` format and SHALL NOT
contain a `Lambda` wrapping a bare Python lambda. The last-step slice SHALL be a
registered `Layer` subclass. The graph SHALL NOT be embedded in the joblib
payload.

#### Scenario: no Lambda in the graph
- GIVEN `models/bilstm_ds02.keras`
- WHEN it is loaded
- THEN no layer is a `Lambda`
- AND exactly one layer is a `LastStepPooling`
- AND the model has 154 253 parameters and input shape `(None, 50, 19)`

#### Scenario: weight migration is lossless
- GIVEN the weight arrays extracted from the Python 3.10 artifact
- WHEN they are set on a graph built with `LastStepPooling`
- THEN predictions on a fixed input match the 3.10 reference exactly
  (max absolute difference `0.000e+00`)

### Requirement: Leakage-free preprocessing

Every fitted transform SHALL be estimated on the fit units `[2, 5, 10, 18, 20]`
only. The holdout unit 16 SHALL NOT contribute to `scaler`, `scaler_w`,
`poly_w`, the 14 residual `Ridge` models or `res_scaler`. Inside cross-validation,
the transforms SHALL be refitted on each fold's training units.

#### Scenario: holdout excluded from the transforms
- GIVEN the dev split
- WHEN preprocessing is fitted
- THEN `scaler.n_samples_seen_` equals the fit-unit row count (44 982), not the
  six-unit count (52 635)

#### Scenario: fold isolation
- GIVEN a grouped fold with scored units `S`
- WHEN the fold is evaluated
- THEN no unit in `S` appears in the base-model fit set
- AND no unit in `S` appears in the meta-learner fit set
- AND the assertion is raised, not asserted silently

### Requirement: Out-of-fold beta selection

`beta` SHALL be selected as the median of per-fold optima obtained by grouped
cross-validation, with the per-fold values and their spread reported.

#### Scenario: spread is reported
- GIVEN three grouped folds
- WHEN selection completes
- THEN the median, minimum, maximum and IQR are reported
- AND the full fold vector is emitted, including any fold that selected
  `beta = 0`

### Requirement: Measured ablation

The effect of `cyc_norm` and of the per-engine baseline delta SHALL be measured
on the test units and reported, never quoted from a different design.

#### Scenario: base-model ablation
- GIVEN four variants (cycle on/off, baseline delta on/off)
- WHEN the ablation runs
- THEN each variant reports LGBM, BiLSTM and BiLSTM+EMA5 on the test units

#### Scenario: meta-level ablation
- GIVEN the shipped artifact
- WHEN its meta-learner coefficients are inspected
- THEN the weight share per meta-feature is reported
- AND the effect of removing the cycle counter from every component is measured

### Requirement: Explicit dataset resolution

The DS02 loader SHALL raise when the HDF5 is absent and SHALL name the paths it
probed. It SHALL NOT fall back to C-MAPSS FD001.

#### Scenario: missing dataset
- GIVEN no DS02 file at any candidate path
- WHEN the loader runs
- THEN it raises `FileNotFoundError`
- AND the message states that falling back is refused and why

### Requirement: Artifact provenance and shape guard

Every persisted bundle SHALL be accompanied by a manifest recording format
version, dataset, seed, unit partition, environment versions, model shape,
inference contract and metrics. The save path SHALL refuse a bundle whose scaler
is not 18-channel or whose `n_op` is not 4.

#### Scenario: FD001-shaped bundle refused
- GIVEN a bundle built from the FD001 fallback (16 channels, `n_op = 2`)
- WHEN `save_ensemble` is called
- THEN it raises `ValueError` and writes nothing

---

## MODIFIED

### Requirement: Metric reporting

Metrics SHALL be reported as mean ± standard deviation over at least three seeds,
with per-seed values available.

#### Scenario: three seeds
- GIVEN `SEEDS = [42, 7, 123]`
- WHEN the notebook completes
- THEN each model row shows mean ± std for RMSE, MAE, R² and NASA score
- AND a per-seed table is printed

### Requirement: Artifact reload check

The notebook SHALL reload the written artifacts and score one window through the
public `predict` contract.

#### Scenario: reload parity
- GIVEN the artifacts on disk
- WHEN they are reloaded and the test windows are re-scored
- THEN the reloaded predictions equal the in-memory ones
- AND the single-window value is reported

---

## REMOVED

### Requirement: C-MAPSS FD001 fallback inside the DS02 loader

Removed. FD001 remains available only through `load_fd001_reference`, a separate
explicit entry point that never touches the DS02 artifact path.
