# Delta: ds02-dss-ui

## ADDED Requirements

### Requirement: Operator thresholds SHALL govern every derived figure

The dashboard SHALL pass the operator's `threshold_aog` to the alarm and to the
critical-zone MAE, and SHALL compute per-unit metrics on the frame currently in
use (raw or corrected).

#### Scenario: moving the hangar threshold

- GIVEN the dashboard with `hangar = 28`
- WHEN the alarm cycle for unit 11 is computed
- THEN it uses 28, not the literal 25.0

#### Scenario: rules layer enabled

- GIVEN the toggle is on
- WHEN per-unit metrics and critical-zone MAE are computed
- THEN they are computed on the corrected frame
- AND the card names the reading it is showing

### Requirement: State, alarm and order SHALL use one criterion

The dashboard SHALL decide and alarm on the same statistic: the lowest lower
bound of the cycle. The chart MAY draw the mean and SHALL label it.

#### Scenario: mean and minimum disagree

- GIVEN a cycle whose mean lower bound is 26 and whose minimum is 24
- WHEN the fleet snapshot and the alarm are computed with hangar 25
- THEN the unit is in HANGAR
- AND the alarm is reported at that cycle

### Requirement: Work orders SHALL name the reading that produced them

Every work order SHALL carry `banda` (source of the calibration) and
`correccion` (correction applied or none), and each unit entry SHALL carry the
rule that decided it. The CSV companion SHALL expose the rule as a column.

#### Scenario: cached fleet order with the rules layer on

- GIVEN the toggle is on and a unit is grounded at cycle 40
- WHEN the order is emitted
- THEN `banda` names `mia/calibracion_banda.json`
- AND `correccion` names the R2b and R6 passes
- AND the unit entry carries `regla = R9_HANGAR`

#### Scenario: live unit scored by the user

- GIVEN a table scored from the UI
- WHEN the order is emitted
- THEN its state comes from `mia.motor`
- AND the entry carries the rule and the motive the motor reported
- AND `banda` names the artifact calibration

### Requirement: The surface SHALL declare the band in use

The dashboard SHALL state, next to the rules toggle, which calibration governs
the numbers currently on screen.

#### Scenario: toggle off

- GIVEN a fresh session
- WHEN the page renders
- THEN a caption names the artifact band as the one in use

#### Scenario: toggle on

- GIVEN the toggle is on
- WHEN the page renders
- THEN a caption names the R6 recalibrated band as the one in use
