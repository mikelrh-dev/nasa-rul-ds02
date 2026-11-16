# ADR-008: Triage on the conformal lower bound with 30 / 25 thresholds

## Status

**Accepted** — 2026-10-21. **Superseded for defaults by ADR-013
(2026-11-12): current defaults are 25 / 20.** The lower-bound reasoning and the
rejection of 50 / 25 remain valid; the 30 / 25 pair is kept here as the
historical decision that ADR-013 revisits with OOF evidence.

## Date

2026-10-21

## Context

The DS02 bundle ships a split-conformal band
(ADR on the calibrated band in the macro-and-conformal change, recorded in the local OpenSpec workspace),
so the maintenance state can be decided on a bound instead of a point estimate.
That is the right direction: the point estimate carries a per-engine bias of
+3.03 (unit 11), −5.19 (unit 14) and −2.27 (unit 15), and a decision rule that
reads the point estimate directly inherits it.

The original UI plan proposed:

| State | Rule |
| --- | --- |
| airworthy | `L_inf >= 50` |
| preventive | `25 <= L_inf < 50` |
| AOG | `L_inf < 25` |

Measured on the shipped bundle, that rule has an unreachable state. Scoring the
three test units with `predict_interval` and aggregating per cycle gives:

| | cycle 1 | AOG crossing (`L_inf < 25`) | true RUL < 25 | lead | true RUL at alarm | life |
| --- | --- | --- | --- | --- | --- | --- |
| unit 11 | `L_inf` 35.7 | cycle 26 | cycle 35 | 9 cycles | 33.0 | 59 |
| unit 14 | `L_inf` 33.0 | cycle 29 | cycle 52 | 23 cycles | 47.0 | 76 |
| unit 15 | `L_inf` 35.8 | cycle 26 | cycle 43 | 17 cycles | 41.0 | 67 |

The band's largest possible lower bound on this split is about 36: the point
estimate saturates near 60.6 and the `[50, 75)` bin subtracts 24.47. No unit can
be airworthy under a `>= 50` rule — a semaphore with a light that never turns on
is decoration, and a demo that starts with the whole fleet amber misrepresents a
model that is, in fact, accurate in the critical band (MAE 1.13 below 25 cycles).

## Decision

Decide the state on `L_inf` only, with defaults calibrated to the band's real
range:

| State | Rule | Operational meaning |
| --- | --- | --- |
| 🟢 airworthy | `L_inf >= 30` | in service |
| 🟡 preventive | `25 <= L_inf < 30` | scheduled inspection, pre-alert |
| 🔴 AOG | `L_inf < 25` | immobilised, work order issued |

Both thresholds are exposed as UI controls so the trade-off can be demonstrated
live rather than asserted.

## Evidence

* All three units start airworthy (35.7 / 33.0 / 35.8), so the fleet view opens
  in a state consistent with a healthy fleet.
* The AOG alarm fires 9, 23 and 17 cycles before the true RUL crosses 25, at a
true RUL of 33, 47 and 41 — conservative, which is the direction the NASA
  penalty rewards, but expensive in availability on unit 14 (grounded with 47
  cycles left). The UI publishes that cost rather than hiding it.
* Cycle-level realised coverage is 1.000 at a 0.90 target, so the lower bound is
  a safety bound rather than a tight interval; using it for AOG is honest, and
  the UI labels it as conservative.
* `L_inf < 25` is the same number as the model's critical band (`[0, 25)`), so the
  decision threshold and the metric band agree; no second, arbitrary cut.

## Alternatives rejected

| Alternative | Why not |
| --- | --- |
| Keep `50 / 25` | The green state is mathematically unreachable on this split; the demo would open with 3 amber units and never show green. |
| Classify on the point estimate | Ignores the per-engine bias the band exists to absorb, and contradicts the risk discipline of a calibrated interval. |
| Recalibrate the band until `L_inf` reaches 50 | Requires refitting the conformal quantiles and would narrow the band on the evaluation split — a model change, out of scope for a UI change. |
| Ratio rule (`L_inf / point`) | Depends on the biased point estimate in the denominator; a low-biased engine turns amber for the wrong reason. |

## Consequences

* The UI's colour is a risk statement, not a prediction statement. A unit can be
  AOG while its point estimate is still above 25; the UI states that the lower
  bound, not the point estimate, made the call.
* Because the thresholds live in the UI, an operator who disagrees can re-run the
  demo with `50 / 25` and watch every unit go amber — the disagreement becomes a
  visible measurement instead of a private opinion.
* If the band is ever recalibrated, the defaults must be revisited; the cache's
  provenance file and this ADR record the scale the numbers were chosen against.
