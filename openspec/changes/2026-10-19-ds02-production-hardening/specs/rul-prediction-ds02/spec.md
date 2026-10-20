# rul-prediction-ds02 delta — deployable artifacts, honest beta selection and seeded reporting

**Change:** [`2026-10-19-ds02-production-hardening`](../../proposal.md)
**Capability:** `rul-prediction-ds02`
**Date:** 2026-10-19
**Deployed spec:** [`openspec/specs/rul-prediction-ds02/spec.md`](../../../../specs/rul-prediction-ds02/spec.md)

This delta strengthens three requirements of the deployed spec and adds three new ones. The
requirement name **Beta shrinkage is selected out-of-sample** is shared deliberately with the
deployed spec: it is the same requirement, tightened from *"out-of-sample with respect to the
base models"* to *"out-of-sample with respect to the meta-learner as well"*.

---

### Requirement: Artifacts are loadable outside the notebook process

Every persisted DS02 artifact SHALL be reconstructible in a fresh Python process in which no
notebook has been executed and in which `__main__` contains nothing but the loading code.
`HybridStackingEnsemble`, `SensorResidualizer` and every other class or function reachable from
the persisted object graph SHALL be importable from an installed module, and MUST NOT be
resolved from `__main__`. When the defining package is unavailable, loading SHALL fail with an
explicit error naming that package.

#### Scenario: Reload in a clean interpreter

- GIVEN a fresh Python process with an empty `__main__` namespace and no notebook executed
- WHEN the persisted ensemble bundle is loaded
- THEN the object is reconstructed successfully
- AND inference on the recorded sample window returns a RUL of 61.25 against a true value of 58.00

#### Scenario: The defining module is recorded in the artifact

- GIVEN a persisted bundle
- WHEN its class references are inspected
- THEN every class path resolves to the `ds02_rul` package
- AND no class path resolves to `__main__`

#### Scenario: Missing package yields a diagnosable error

- GIVEN an environment where the defining package is not installed
- WHEN the bundle is loaded
- THEN loading fails with an error message naming the missing package
- AND the failure is not reported as a bare attribute error on `__main__`

---

### Requirement: Persisted Keras model uses a native format and a serializable pooling

The Keras sub-model SHALL be persisted in the native `.keras` format. It MUST NOT be persisted
as a legacy HDF5 `.h5` file, and MUST NOT be embedded inside a `joblib` pickle. The
last-timestep pooling operation SHALL be expressed as a layer or registered function that is
reconstructible from its configuration alone, so the graph MUST NOT contain a `Lambda` layer
wrapping a bare Python lambda. The pooled representation SHALL remain the concatenation of the
last timestep, the temporal average and the temporal maximum, yielding 384 dimensions.

#### Scenario: Round-trip through the native format

- GIVEN a trained Keras sub-model held in memory
- WHEN it is saved to the native format and reloaded in a new process
- THEN the reloaded model produces predictions identical to the original on a fixed input window
- AND the reload requires no access to the defining notebook

#### Scenario: No bare lambda survives serialization

- GIVEN the persisted Keras artifact
- WHEN its layer graph is inspected
- THEN no layer wraps a bare Python lambda
- AND the last-timestep slice is performed by a layer carrying a serializable configuration

#### Scenario: Pooled head width is unchanged

- GIVEN a serialized last-timestep layer replacing the previous lambda form
- WHEN the three pooling outputs are concatenated
- THEN the concatenated width is still 384
- AND the total parameter count remains 154,253 (154,215 trainable)

#### Scenario: The artifact crosses a Python minor version

- GIVEN an artifact written under one Python minor version
- WHEN it is loaded under a different Python minor version
- THEN the load succeeds
- AND the reloaded model produces predictions identical to the original on a fixed input window
- AND no marshalled bytecode from the writing interpreter is required, which is what the
  current artifact fails on: it loads under Python 3.10 and raises
  `ValueError: bad marshal data (unknown type code)` under Python 3.12

---

### Requirement: Beta shrinkage is selected out-of-sample

The shrinkage factor `beta` SHALL be selected by grouped cross-validation over the train units,
and the meta-learners used to score a given unit MUST NOT have been fit on that unit's rows.
The grid SHALL be `linspace(0, 1, 21)`, each candidate SHALL be scored after causal EMA
smoothing with span 5, and the criterion SHALL be the sum of the normalized RMSE and normalized
NASA score, so that `beta = 0` remains a legal and reachable outcome. Selection SHALL aggregate
the per-fold choices by median and SHALL report the fold values and their spread. Selecting
`beta` on the rows that fitted the meta-learners SHALL be treated as non-compliant and MUST NOT
be used to justify the ensemble's reported advantage.

#### Scenario: Meta-learner never sees the scored unit

- GIVEN the six train units and their windowed features
- WHEN grouped out-of-fold beta selection runs
- THEN each fold's meta-learners are fit only on units other than the scored unit
- AND the harness asserts and reports that absence for every fold

#### Scenario: Selection spread is reported

- GIVEN a completed selection
- WHEN the result is emitted
- THEN the selected beta is the median of the per-fold values
- AND the fold values, their minimum, maximum and interquartile range are all reported

#### Scenario: Beta zero remains reachable

- GIVEN a fold in which the meta-learner does not improve on the BiLSTM
- WHEN the criterion is minimized over the grid
- THEN `beta = 0` is a candidate and may be selected
- AND selecting it degrades the ensemble safely to the smoothed BiLSTM

---

### Requirement: Model quality is reported across seeds

DS02 model quality SHALL be reported as a mean together with a standard deviation across at
least three seeds, and the seed set MUST include 42. A single-seed figure SHALL NOT be presented
as an estimate of expected performance. Any run that breaches the per-epoch compute budget SHALL
be flagged and excluded from the aggregate, and the number of excluded runs SHALL be reported
alongside the results rather than omitted.

#### Scenario: Multi-seed aggregate is produced

- GIVEN a configured seed list containing at least three seeds, one of which is 42
- WHEN the evaluation harness runs each seed to completion
- THEN per-seed metrics are recorded for all four models on the test units
- AND an aggregate mean and standard deviation are reported for RMSE, MAE, R² and NASA score

#### Scenario: Starved run is flagged, not averaged

- GIVEN a run in which one epoch exceeds the per-epoch compute budget
- WHEN results are aggregated
- THEN that run is marked starved and excluded from the aggregate
- AND its metrics are retained separately and the excluded count is reported

#### Scenario: Insufficient valid runs are stated plainly

- GIVEN a seed list in which fewer than two runs complete within budget
- WHEN the aggregate is reported
- THEN the surviving single-seed result is reported without a standard deviation
- AND the report states explicitly that no variance estimate is available

---

### Requirement: DS02 inference is exposed through a stable entry point

The DS02 capability SHALL expose inference through `scripts/predict_ds02.py`, callable without
executing the notebook, accepting a DS02 window and returning a finite RUL. The entry point
SHALL NOT read, write, import or otherwise depend on `scripts/predict.py`, the FD001 v3 bundle,
or the FD001 feature contract. A missing DS02 dataset SHALL produce an explicit error rather
than a silent fallback to another dataset.

#### Scenario: CLI returns a RUL for a DS02 window

- GIVEN a valid DS02 window of at least 50 cycles
- WHEN the entry point is invoked
- THEN it returns a finite RUL value
- AND it does not import or execute the notebook

#### Scenario: Validation rejects an undersized window

- GIVEN a window shorter than 50 cycles
- WHEN the entry point is invoked
- THEN it raises a validation error stating the 50-cycle minimum
- AND it does not return a prediction

#### Scenario: FD001 pipeline is provably untouched

- GIVEN the change has been applied
- WHEN `scripts/predict.py` is compared against its pre-change revision
- THEN the file is byte-identical
- AND no FD001 artifact has been read or written by the DS02 entry point

---

### Requirement: The notebook remains the reference implementation until the module is verified

Until the extracted module reproduces the recorded test rows, the notebook SHALL remain the
authoritative implementation and the module SHALL be verified against it, not the reverse.
The notebook MUST be regenerated from `scripts/build_02_notebook.py` and MUST NOT be edited in
place. Promotion of the module to the source of truth SHALL require all four recorded test rows
to be reproduced within `1e-6` on RMSE.

#### Scenario: Module is verified against the notebook

- GIVEN the extracted module and the pinned reference notebook revision
- WHEN both are driven over the same data
- THEN the module reproduces the LightGBM standalone, BiLSTM, BiLSTM + EMA and hybrid rows
- AND the RMSE values agree to `1e-6`

#### Scenario: Notebook is regenerated, not edited

- GIVEN a change intended for the notebook
- WHEN it is applied
- THEN `scripts/build_02_notebook.py` is modified and the notebook is regenerated from it
- AND running the builder twice produces byte-identical output

#### Scenario: Promotion requires reproduction

- GIVEN a module that does not yet reproduce the recorded rows
- WHEN documentation is updated
- THEN the notebook is still documented as the reference implementation
- AND the deployed spec does not yet name the module as the source of truth
