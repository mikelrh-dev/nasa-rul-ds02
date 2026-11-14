# Delta for ds02-dss-ui

**Change:** `2026-11-14-radiografia-paleta-duplicados`
**Status:** Proposed
**Capability:** `ds02-dss-ui` (Modified)

Presentation only: no metric, threshold, rule, cache row, artifact hash or triage outcome
changes.

## MODIFIED Requirements

### Requirement: Physical sensor radiography

The sensor tab SHALL use the dataset's real channel names — `T24, T30, T48, T50,
P15, P2, P21, P24, Ps30, P40, P50, Nf, Nc, Wf` for the physical sensors and
`alt, Mach, TRA, T2` for the operating conditions — grouped by physical meaning in
the selector. It SHALL plot the per-cycle evolution of the selected channels and
SHALL mark the critical band where the true RUL is below the AOG threshold — the
same `[0, 25)` band the metrics use.

It SHALL also plot, under the per-cycle view, a cross-unit aggregate view of the same
selected channels aligned by the real RUL of each cycle and averaged over every test unit
present in the cache. That view SHALL highlight the channels with a measured sustained
drift and SHALL dim the rest. Its caption SHALL state the measured drift of those
channels as percentage points between the first and last RUL bin, together with the
method (cycle value divided by the mean of the unit's first five cycles, minus one, in
percent) and the source (`app/cache/`). The figures in the caption SHALL be computed from
the same frame the chart draws and SHALL NOT be hardcoded literals.

Every channel SHALL keep one colour across the per-cycle view and the aligned view, so a
series can be followed without re-reading the legend. Channels measured as duplicates on
the cache (correlation 1.000 across the test units) SHALL be drawn once, under a label
naming both codes, instead of as two overlapping traces. For a selection in which no
channel meets the drift criterion, the caption SHALL state the largest measured change
between RUL bins and whether the shape is monotone, and SHALL NOT attribute the movement
to a cause the view does not compute.

(Previously: the requirement covered the per-cycle view and the aligned aggregate but had
no channel-identity rule, drew duplicated pairs twice and allowed a caption to contradict
its own curve.)

#### Scenario: Names come from the file, not from FD001

- GIVEN the operating-condition and sensor selectors
- WHEN they are populated
- THEN the labels are the DS02 channel names
- AND no FD001 `s1 … s21` label appears

#### Scenario: The critical region is visible

- GIVEN a selected sensor series
- WHEN the chart is drawn
- THEN the cycles whose true RUL is below the AOG threshold are shaded
- AND the drift of the signal into that region is readable

#### Scenario: The life-aligned view is present and aggregated

- GIVEN telemetry rows for every test unit in the cache
- WHEN the sensor tab renders the aligned view
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
- WHEN the radiography renders
- THEN the pair appears as one trace
- AND its label names both channel codes

#### Scenario: One colour per channel in both views

- GIVEN the same channel code visible in the per-cycle view and in the aligned view
- WHEN both charts render
- THEN the channel carries the same colour in both

#### Scenario: The caption does not assert what it cannot compute

- GIVEN a selection where no channel meets the drift criterion
- WHEN the caption is composed
- THEN it reports the largest measured bin change and whether the shape is monotone
- AND it does not attribute the movement to a cause such as flight conditions

## ADDED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.

## No delta

- `rul-prediction-ds02`, `ds02-live-evaluation`, `fleet-registries-session`,
  `shap-c-explanation`, `ds02-n8n-decision`: None.
