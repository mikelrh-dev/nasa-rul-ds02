# Spec delta: DS02 pre-defense hardening — `ds02-live-evaluation`

**Change:** `2026-10-26-ds02-pre-defense-hardening`
**Status:** Proposed
**Capability:** `ds02-live-evaluation` (modification)

---

## ADDED

None.

## MODIFIED

### Requirement: Contract validation with actionable errors (deployed)

The system SHALL validate the table before scoring and SHALL reject, naming the
problem: fewer than `window_size` rows, missing or extra channel columns, a wrong
channel order, non-numeric values, NaN, **non-finite values (`±inf`)**, or cycles
that do not increase.

A non-finite value SHALL be rejected in the same pass as NaN and SHALL name the
offending column and row, because an `inf` is not a value the frozen bundle can
consume honestly: it reaches the scaler, the residualizer and the network, and
the causal EMA propagates it to every later window of the unit.

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

#### Scenario: Infinite value

- GIVEN a window whose `T48` column holds `inf` in one row
- WHEN the table is submitted
- THEN the request is rejected with the offending column and row named
- AND the value is not scored

#### Scenario: Negative infinity is rejected too

- GIVEN a window whose `Ps30` column holds `-inf`
- WHEN the table is submitted
- THEN the request is rejected exactly as for `inf`

## REMOVED

None.

## Related capabilities

[`ds02-dss-ui`](../ds02-dss-ui/spec.md) hosts this surface and adds the cache
hash check in the same change. The rejection added here is stricter than the
surface's out-of-domain note, which is non-blocking by design: an out-of-range
finite value is scoreable and flagged, an infinite one is not scoreable at all.
