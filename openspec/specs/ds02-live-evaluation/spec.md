# Capability spec: live evaluation of a user-supplied unit

**Capability:** `ds02-live-evaluation`
**Origin change:** [`2026-10-21-ds02-live-eval`](../../changes/2026-10-21-ds02-live-eval/proposal.md)
**Depends on:** [`rul-prediction-ds02`](../rul-prediction-ds02/spec.md) (the frozen bundle) and
[`ds02-dss-ui`](../ds02-dss-ui/spec.md) (the surface that hosts the tab)

The DSS replays three frozen engines. This capability answers the other question —
*"what would this model say about this aircraft?"* — by accepting telemetry through
the UI and scoring it with the same frozen artifact, on demand and read-only.

## Requirements

### Requirement: Input through the UI, not the filesystem

The surface SHALL accept a new unit's telemetry without requiring the DS02 HDF5,
through three paths that converge on one pipeline:

1. an example window lifted from the cached telemetry, usable on first paint;
2. an editable grid where a block can be pasted from a spreadsheet;
3. a CSV upload.

All three SHALL produce the same validated table before any scoring happens.

#### Scenario: The tab works without typing

- GIVEN a first visit
- WHEN the evaluation tab is opened
- THEN the example window is already loaded
- AND pressing evaluate returns a prediction

#### Scenario: Paste and upload are equivalent

- GIVEN the same 50 rows entered through the grid and uploaded as CSV
- WHEN both are scored
- THEN the point estimate and the band are identical

### Requirement: Contract validation with actionable errors

The system SHALL validate the table before scoring and SHALL reject, naming the
problem: fewer than `window_size` rows, missing or extra channel columns, a wrong
channel order, non-numeric values, NaN, or cycles that do not increase.

The channel order SHALL be the dataset's own (`alt, Mach, TRA, T2` then
`T24 … Wf`), derived from the cache provenance rather than typed by hand.

#### Scenario: Too few rows

- GIVEN a table with 20 rows
- WHEN it is submitted
- THEN the request is rejected
- AND the message states how many rows are required and how many arrived

#### Scenario: Wrong column order

- GIVEN the 18 channels in a different order
- WHEN the table is submitted
- THEN the request is rejected
- AND the message names the expected order

#### Scenario: Non-numeric cell

- GIVEN one cell containing text
- WHEN the table is submitted
- THEN the request is rejected with the offending column and row named

### Requirement: Scoring on demand, never at startup

The model SHALL be loaded only when a score is requested, and SHALL be cached for
later requests. Rendering the page SHALL NOT import TensorFlow or Keras.

#### Scenario: Startup stays light

- GIVEN the app is opened and no score is requested
- WHEN the page renders
- THEN TensorFlow and Keras are absent from `sys.modules`

#### Scenario: The model loads once

- GIVEN two consecutive evaluations
- WHEN the second one runs
- THEN the model is not reloaded

### Requirement: Honest reporting of a live score

A live score SHALL report the point estimate, the conformal lower and upper
bounds, the triage state under the operator's thresholds, and the contract used
(window size, channel order, artifact hash, unit identifier).

Because the user's data has no ground truth, the surface SHALL state that no
accuracy metric can be claimed for it, and that the band is a conservative bound
calibrated on the development engines.

#### Scenario: No accuracy is invented

- GIVEN a live evaluation
- WHEN the result is displayed
- THEN no RMSE/MAE figure appears for that unit
- AND the caption explains that there is no ground truth

#### Scenario: Provenance travels with the result

- GIVEN a live score
- WHEN the result is inspected
- THEN it records the artifact hash, the window size and the fact that the data
  came from the user

#### Scenario: The triage rule is the same one

- GIVEN a live `L_inf` of 24.9 with thresholds 30/25
- WHEN the state is computed
- THEN it is AOG, exactly as for a cached unit

### Requirement: The sampling contract is explained

The surface SHALL state that a window is 50 **downsampled rows** (`STRIDE = 100`
over the recorded data), not 50 consecutive records and not 50 flight cycles, and
SHALL show the example's source so the recipe is verifiable.

#### Scenario: The recipe is visible

- GIVEN the evaluation tab
- WHEN the contract panel is opened
- THEN it states the stride, the window length and the channel order
- AND it names the unit and cycles the example window came from

### Requirement: Every input is named and explained

The surface SHALL NOT present a channel as a bare acronym. Each of the 18 channels
SHALL carry its physical meaning as a per-column tooltip and in a glossary panel,
together with the range observed in DS02, measured from the cache rather than
quoted from documentation. `cycle` SHALL be explained as the flight cycle of a
record, including why it repeats across rows of one window.

A blank, contract-shaped CSV template SHALL be downloadable, so the header and
column order never have to be reproduced from memory.

#### Scenario: The glossary covers the contract

- GIVEN the evaluation tab
- WHEN the glossary panel is opened
- THEN all 18 channels are listed with a physical description
- AND every column of the editable grid carries that description as a tooltip
- AND the `cycle` help states that several rows share a flight cycle

#### Scenario: The template is shapeless but valid

- GIVEN the template download
- WHEN the file is opened
- THEN it has `cycle` plus the 18 channels in dataset order and 50 empty rows
- AND submitting it unedited is rejected instead of scored as zeros

### Requirement: Out-of-domain values are flagged, not hidden

A numeric value outside the range observed in DS02 (plus a 5 % margin) SHALL
produce a visible note naming the column, the number of rows and the expected
range. The evaluation SHALL still run, and the note SHALL say the result falls
outside the training domain and suggest checking the units. A window covering a
single flight cycle SHALL be flagged separately.

#### Scenario: A unit slip is caught

- GIVEN a window whose `Mach` cell reads 49 instead of 0.49
- WHEN the unit is evaluated
- THEN the result is shown
- AND a warning names `Mach`, counts the offending rows and gives the DS02 range

#### Scenario: In-domain data stays quiet

- GIVEN a real window taken from the test engines
- WHEN it is evaluated
- THEN no plausibility warning is raised

### Requirement: The screen's vocabulary is defined

The surface SHALL offer a help panel that defines RUL, the conformal lower bound,
the 90 % band, the three maintenance states and their thresholds, the flight
cycle, the window, and the work order.

#### Scenario: A reader can interpret the numbers

- GIVEN the DSS with no prior knowledge of the model
- WHEN the help panel is opened
- THEN every KPI and every state on the page is defined there

### Requirement: No writes, no retraining

The capability SHALL reuse the frozen bundle read-only and SHALL NOT write to
`models/`, `app/cache/` or `src/`.

#### Scenario: Nothing is persisted

- GIVEN an evaluation
- WHEN it finishes
- THEN no file under `models/` or `app/cache/` has changed
- AND no artifact has been rewritten

### Requirement: Verification

The capability SHALL be covered by tests for the validator, the example window,
the live score, the CSV equivalence, the glossary, the plausibility warnings, the
template and the end-to-end evaluation, and SHALL keep the existing suite green.

#### Scenario: The suite passes

- GIVEN the repository virtualenv
- WHEN `pytest tests -q` runs
- THEN every pre-existing test still passes
- AND the live-evaluation tests pass (27 at the time of writing)

#### Scenario: A real user can score a unit

- GIVEN the server running and a browser
- WHEN the evaluation tab is opened and the evaluate button is pressed
- THEN a point estimate, a band and a triage state appear on the page
- AND no error is shown

---

## Requirements (2026-11-06-app-fixes-2)

### Requirement: Spanish thousands separator in live and batch text

Live and batch validation messages (`app/ui_inference.py`, `app/ui_batch.py`) MUST format thousands with `.` via `fmt_miles` so a cap of 5000 reads `5.000`, never `5,000`. The NASA score remains a SUM with no 125-cycle clamp on DS02; formatting changes no validation outcome.

#### Scenario: Cap message uses dot

- GIVEN `MAX_FILAS` 5000
- WHEN `preflight` rejects an over-cap table
- THEN the error contains `5.000` and not `5,000`
