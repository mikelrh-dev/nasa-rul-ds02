# Spec delta: per-engine metric and calibrated intervals

**Change:** `2026-10-21-ds02-macro-and-conformal`
**Status:** Implemented
**Capability:** [`rul-prediction-ds02`](../../specs/rul-prediction-ds02/spec.md)

---

## ADDED

### Requirement: Report the per-engine metric next to the window-weighted one

The capability SHALL report a macro-RMSE — the unweighted mean of the per-engine
RMSEs — alongside the window-weighted RMSE, and SHALL record both in the artifact
manifest. An engine SHALL weigh `1/n_units` regardless of how many windows it
contributes.

#### Scenario: Both figures are printed and stored

- GIVEN predictions over the test engines 11, 14 and 15
- WHEN the metrics are reported
- THEN the macro-RMSE is the arithmetic mean of the three per-engine RMSEs
- AND the window-weighted RMSE is reported next to it
- AND `manifest["macro_rmse"]["per_unit_rmse"]` and `["macro_rmse"]` hold both

#### Scenario: The gap is visible

- GIVEN an engine with few windows and large error
- WHEN the two figures are compared
- THEN the macro-RMSE is larger than the weighted one
- AND the difference is reported rather than left implicit

## ADDED

### Requirement: Calibrated prediction interval

The capability SHALL expose a prediction band for every window, calibrated by
split conformal on residuals that the meta-learner did not fit, with asymmetric
quantiles per predicted-RUL bin.

The band SHALL be produced by `predict_interval(X, cycles, units)`, and
`predict()` SHALL keep returning the point estimate with its existing signature.

#### Scenario: Band contains the point estimate

- GIVEN a calibrated bundle
- WHEN `predict_interval` is called
- THEN `lower <= point <= upper` for every row
- AND `lower >= 0`

#### Scenario: Calibration rows are out-of-fold

- GIVEN the six development engines
- WHEN the band's quantiles are fitted
- THEN each calibration row was scored by a meta-learner fitted on the *other* engines
- AND the calibration row count is reported in the manifest

#### Scenario: Coverage is reported per engine

- GIVEN the test engines
- WHEN realised coverage is measured
- THEN it is reported per engine, not only pooled
- AND the fraction of truths above the upper bound is reported separately,
  because the NASA penalty is asymmetric

#### Scenario: Over-coverage is described honestly

- GIVEN a band calibrated on fold-model residuals that are pessimistic relative to
  the shipped models
- WHEN realised coverage exceeds the nominal target
- THEN the band is described as a conservative bound, not as a sharp interval
- AND its width is published next to the coverage
- AND it is not narrowed by calibrating against the test set
