# Delta: ds02-rules-engine

## ADDED Requirements

### Requirement: Gate SHALL NOT freeze calibration on figure drift

`scripts/freeze_rules_evidence.py --write` SHALL evaluate the recorded figures
before touching `mia/calibracion_banda.json`. When a recorded figure drifts, the
script SHALL exit `4` and SHALL leave the file byte-identical.

#### Scenario: drifted figures with --write

- GIVEN a copy of the tree whose expected figures are one order above their HULP
- WHEN `freeze_rules_evidence.py --write` runs
- THEN the script exits `4`
- AND the SHA-256 of `mia/calibracion_banda.json` is unchanged

#### Scenario: clean tree with --write

- GIVEN the recorded figures match the recomputation
- WHEN `freeze_rules_evidence.py --write` runs
- THEN the script prints `no change`
- AND the SHA-256 of the frozen file is unchanged

### Requirement: Small-sample calibration bins SHALL NOT narrow the band

`mia.reglas.banda_recalibrada_vector` SHALL treat a bin with fewer than 500 rows
conservatively: `q_low` SHALL be the smaller of the bin and the global lower
quantile, and `q_high` the larger of the two. Every other bin SHALL use its own
quantiles unchanged.

#### Scenario: crossing the 75-cycle edge

- GIVEN the frozen calibration with 419 rows in the `[75, ∞)` bin
- WHEN the band is computed at 74.999 and at 75.0 cycles
- THEN both intervals contain their point
- AND the upper bound drops by less than 3 cycles across the crossing

#### Scenario: a well-populated bin is untouched

- GIVEN a point at 30.8385 cycles, inside the 5 283-row `[25, 50)` bin
- WHEN the band is computed
- THEN the result is the bin's own `q_low` and `q_high` applied to the point

## MODIFIED Requirements

### Requirement: The recalibrated band SHALL be the one the engine declares

`mia.reglas.R6_BANDA` SHALL keep writing `lower` and `upper` from the frozen
coefficients, and every consumer SHALL be able to name the source it used.

#### Scenario: source is available to the caller

- GIVEN a corrected frame produced by `app.ui_rules.corregir_ventanas`
- WHEN a work order is emitted
- THEN the document names `mia/calibracion_banda.json` as the band source
