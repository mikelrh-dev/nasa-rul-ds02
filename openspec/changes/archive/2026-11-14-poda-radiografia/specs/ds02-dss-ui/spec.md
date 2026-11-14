# Delta for ds02-dss-ui

**Change:** `2026-11-14-poda-radiografia`
**Status:** Proposed
**Capability:** `ds02-dss-ui` (Modified)

Presentation only: no metric, threshold, rule, cache row, artifact hash or triage outcome
changes.

## MODIFIED Requirements

### Requirement: Physical sensor radiography

The sensor tab SHALL use the dataset's real channel names — `T24, T30, T48, T50,
P15, P2, P21, P24, Ps30, P40, P50, Nf, Nc, Wf` for the physical sensors and
`alt, Mach, TRA, T2` for the operating conditions — grouped by physical meaning in the
selector. It SHALL mark the critical band where the true RUL is below the AOG threshold — the
same `[0, 25)` band the metrics use.

It SHALL plot a cross-unit aggregate view, aligned by the real RUL of each cycle and
averaged over every test unit present in the cache, for every channel group whose baseline
uncertainty is smaller than its measured whole-life change. That view SHALL highlight the
channels with a measured sustained drift and SHALL dim the rest. Its caption SHALL state the
measured drift of those channels as percentage points between the first and last RUL bin,
together with the method (cycle value divided by the mean of the unit's first five cycles,
minus one, in percent) and the source (`app/cache/`). The figures in the caption SHALL be
computed from the same frame the chart draws and SHALL NOT be hardcoded literals.

Every channel SHALL keep one colour across the per-cycle view and the aligned view, so a
series can be followed without re-reading the legend. Channels measured as duplicates on
the cache (correlation 1.000 across the test units) SHALL be drawn once, under a label
naming both codes, instead of as two overlapping traces.

A channel group whose baseline uncertainty is not smaller than its measured whole-life
change SHALL be reported as a computed text conclusion — largest change between RUL bins
and whether the shape is monotone — instead of a curve. For this cache the pressure group
falls here: its baseline error is ±2,3–3,5 % and its whole-life change stays at or below
it, so a curve would invite a claim the data does not support. The per-cycle raw view SHALL
NOT be offered when it cannot resolve degradation against the baseline uncertainty.

(Previously: the requirement demanded a per-cycle view for the selected channels and drew
both groups as curves.)

#### Scenario: Names come from the file, not from FD001

- GIVEN the operating-condition and sensor selectors
- WHEN they are populated
- THEN the labels are the DS02 channel names
- AND no FD001 `s1 … s21` label appears

#### Scenario: The critical region is visible

- GIVEN a rendered aggregate view
- WHEN the chart is drawn
- THEN the cycles whose true RUL is below the AOG threshold are shaded

#### Scenario: The life-aligned view is present and aggregated

- GIVEN telemetry rows for every test unit in the cache
- WHEN the sensor tab renders the aggregate view for a resolvable group
- THEN each selected channel is drawn against the real RUL of its cycle
- AND the values are averaged across units within each RUL bin
- AND the channels with a measured sustained drift are visually distinguished from the
  others

#### Scenario: The stated finding matches the drawn data

- GIVEN the aligned frame
- WHEN the caption is composed
- THEN the percentage-point figures equal the difference between the first and last RUL
  bin means of that frame
- AND the caption names the method and the cache as its source

#### Scenario: Duplicated channels are not drawn twice

- GIVEN a channel group that contains a measured duplicate pair
- WHEN the aggregate view renders
- THEN the pair appears as one trace
- AND its label names both channel codes

#### Scenario: One colour per channel in both views

- GIVEN the same channel code visible in more than one rendered view
- WHEN the views render
- THEN the channel carries the same colour in both

#### Scenario: The caption does not assert what it cannot compute

- GIVEN a selection where no channel meets the drift criterion
- WHEN the caption is composed
- THEN it reports the largest measured bin change and whether the shape is monotone
- AND it does not attribute the movement to a cause such as flight conditions

#### Scenario: A group below the resolution floor is reported as text

- GIVEN a channel group whose baseline error is at least its whole-life change
- WHEN the sensor tab renders
- THEN no curve is drawn for that group
- AND a text conclusion states the largest measured bin change and the monotonicity

## ADDED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.

## No delta

- `rul-prediction-ds02`, `ds02-live-evaluation`, `fleet-registries-session`,
  `shap-c-explanation`, `ds02-n8n-decision`: None.
