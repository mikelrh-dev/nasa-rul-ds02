# Delta: ds02-dss-ui

## ADDED Requirements

### Requirement: The fleet KPI SHALL read the frame in use

The macro-RMSE card SHALL be computed from the same frame as the per-unit cards
and the coverage figure. With the rules layer on, both SHALL show the corrected
reading; with it off, both SHALL show the raw one.

#### Scenario: rules layer enabled

- GIVEN the toggle is on
- WHEN the fleet cards render
- THEN the macro-RMSE equals the value computed on the corrected frame

### Requirement: Work orders SHALL identify the evaluated window

Each unit entry in a work order SHALL carry the window that produced the
decision: size, step, cycle, `start_index` and the window index within the cycle.

#### Scenario: a grounded unit

- GIVEN a unit is grounded at cycle 40
- WHEN the order is emitted
- THEN its entry names `start_index` and the cycle of the worst window

### Requirement: The surface SHALL list registered twins

The fleet tab SHALL show every registered twin with its cycle, lower bound,
current state, rule, band source and truth status, derived on read.

#### Scenario: a twin after a threshold change

- GIVEN a registered twin and the hangar threshold raised
- WHEN the fleet tab renders
- THEN the twin's state is recomputed with the new threshold
- AND its stored series is unchanged

### Requirement: The twin panel SHALL replace, document and delete

The fleet tab SHALL refuse to overwrite a twin silently, offer an explicit
replace that keeps the reported real RUL, emit a work order per twin from the
stored series, and allow deleting a twin without touching its hangar record.

#### Scenario: second window of the same engine

- GIVEN a twin `ESN-DEMO-01` already in the registry
- WHEN the user scores another window and opens the registration panel
- THEN the panel says the twin exists and offers a replace checkbox
- AND only the checked path overwrites the series

#### Scenario: documenting a twin

- GIVEN a registered twin
- WHEN the user picks it under «Documentar un gemelo»
- THEN both download buttons emit the document for that engine
- AND the caption states the state with today's thresholds, computed on read

#### Scenario: deleting a twin

- GIVEN a registered twin with an open hangar record
- WHEN the user deletes the twin
- THEN the twin leaves the registry
- AND the hangar record stays, because they are different books

### Requirement: The hangar SHALL be a state machine with a frozen entry

The dashboard SHALL expose the hangar lifecycle, SHALL reject transitions not in
the allowed set, and SHALL keep the decision that opened a record with the
thresholds in force at that moment.

#### Scenario: illegal transition

- GIVEN a record in `AOG_DERIVADO`
- WHEN the user tries to move it straight to `EN_SERVICIO`
- THEN the move is rejected naming the allowed next states

#### Scenario: the threshold moved after entry

- GIVEN a record opened with `hangar = 25` at `L_inf = 24`
- WHEN the threshold becomes 20
- THEN the record still reports the frozen entry decision
- AND it reports that today's policy would not ground the unit
