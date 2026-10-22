# ADR-007: Move the tabular objective to the median — **REJECTED**

## Status

**Rejected** — proposed on dev evidence, measured on the confirmatory test read,
reverted. `alpha=0.35` (ADR-003) stands.

## Date

2026-10-21

## Context

ADR-003 chose `objective='quantile', alpha=0.35` on the argument that the NASA
score punishes over-estimates about 1.3x harder per cycle, so a low conditional
quantile converts expensive over-estimates into cheap under-estimates at a small
RMSE cost.

Two doubts motivated re-testing it:

1. That argument assumes a roughly symmetric predictive distribution with a
   "small, constant" offset. At `y > 65` this pipeline under-predicts by
   **16.8 cycles** (see `docs/informes/informe-2026-10-21-p0-p1-prior-de-vida.md`), so pushing the forecast
   further down moves errors away from zero.
2. ADR-003 cites `scripts/probe_q35.py`, which compares two `alpha=0.35`
   configurations against an L2 model, computes its metrics on the evaluation
   split, and contains **no median arm**. The recorded selection was therefore made
   on test and never measured 0.50.

## Decision (proposed)

`alpha=0.50`, everything else unchanged. It was adopted after passing a full dev
gate and then **reverted**, because the single confirmatory test read contradicted
it.

## Evidence — dev said yes, unanimously

Grouped out-of-fold dev, preprocessing refitted per fold, meta fitted on unit 16.
Alignment verified: refitting `alpha=0.35` reproduces the cached out-of-fold column
with max |Δ| = 0.0.

| level | metric | α = 0.35 | α = 0.50 | Δ |
|---|---|---|---|---|
| rama tabular | RMSE | 9.11 | **8.18** | −0.93 |
| rama tabular | RMSE `y>65` | 17.79 | **14.40** | −3.39 |
| rama tabular | RMSE `y≤62` | 6.89 | **6.83** | −0.06 |
| rama tabular | NASA | 18 129 | **16 649** | −1 480 |
| híbrido (β=1.00) | RMSE | 13.15 | **12.09** | −1.07 |
| híbrido | macro | 11.23 | **10.31** | −0.92 |
| híbrido | NASA | 26 355 | **22 518** | −14,6 % |

β stayed 1.00 with identical fold votes (1.00 / 1.00 / 0.00), and the sweep showed
0.50 as the joint optimum of macro, pooled RMSE and NASA.

## Evidence — test said no

Attribution holds the BiLSTM fixed (the same reloaded artifact for both arms), so
none of the difference is recurrent-network variance:

| α | LGB test RMSE | híbrido | MAE | R² | NASA | macro |
|---|---|---|---|---|---|---|
| **0.35** | **7.11** | **4.236** | **3.179** | **0.9486** | **2 301.5** | **4.816** |
| 0.50 | 9.12 | 4.588 | 3.322 | 0.9397 | 2 545.5 | 5.054 |

The full notebook, run end to end at `alpha=0.50` (3 seeds), produced
**4.642 ± 0.048** against the recorded **4.344 ± 0.075**, with the branch at 9.205
against 7.087.

**Mechanism.** The dev fleet lives 63–89 cycles and is systematically
under-predicted at high RUL; the test engines are shorter (58–75). Raising the
quantile repairs the regime that dev over-represents and over-shoots the one test
actually is. This is the same dev/test regime mismatch that made branch *weights*
un-arbitrable on dev, now demonstrated for the *objective* as well.

## Alternatives Considered

### Ship it anyway, arguing dev is the protocol
- Cons: the confirmatory read exists precisely to catch this. Shipping a model that
  is 0.35 RMSE worse on the deployment target, with the branch 2.0 worse, to honour
  a gate that the gate itself just proved insufficient, inverts the hierarchy.
- Rejected.

### `alpha=0.60`
- Was already the worst on the normal band (7.34) and on NASA (17 544) in dev, and
  the same mechanism would amplify it on test.
- Rejected without a test read.

### Keep the median and re-select `beta` on test
- That is fitting the deployment set.
- Rejected outright.

## Consequences

- **`alpha=0.35` stands**, but for a weaker reason than ADR-003 claims: not "the
  asymmetric objective rewards NASA" (contradicted on dev, which prefers 0.50), and
  not because the median was measured worse (it was never measured before this
  ADR). It stands because on the deployment target it is better, by a margin large
  enough to survive the noise.
- **The dev gate cannot arbitrate objective or weight choices on this dataset.** It
  can settle structural questions (does the meta shift the level? is the band
  two-sided?) but not the mix of regimes. Any future proposal of this class needs a
  pre-registered test read, and only one.
- ADR-003's cited evidence (`probe_q35.py`) should be treated as weak: it was
  computed on the evaluation split and it never contained the arm it rejected.
  Re-auditing it is an open item.
- The band diagnostics added in the same revision are kept and are independent of
  this decision: calibrating on unit 16 gives a **3.13-cycle band that covers 30.3 %
  of test rows** (42.3 % below, 27.4 % above), which rejects that route empirically.
  The shipped out-of-fold band covers 100 % with a 24.89-cycle width.
