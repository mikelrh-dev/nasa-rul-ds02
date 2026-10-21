# ADR-009: R2b is an isotonic fit, not a monotonicity rule

## Status

**Accepted** — 2026-10-21. The rule keeps the name `R2b_ISOTONICO_CAUSAL`; no
behaviour changes with this decision, only the claim made about it.

## Date

2026-10-21

## Context

§9 of `INFORME_reglas_oof.md` called R2b "the defensible version of monotonicity".
The label survived into tests, docstrings and UI copy, and it describes a rule
that was never measured.

R2b is the **online isotonic fit of the prefix** (PAVA): at position `t` it
returns the last block of the non-increasing fit of `y_1..t`. Each prefix fit is
non-increasing; the series returned across `t` is not. When the history stops
sustaining the fall, the extremum rises — the measured maximum positive
increment over the 14 915 pure OOF rows is **+1.328848** cycles.

Strict monotonicity is a different rule. The non-increasing envelope of the
R2b output is, by identity, `np.minimum.accumulate(serie)`, i.e. the raw
running-min rule R2. Measured on the same rows and the same split:

| Variant | OOF RMSE | OOF NASA | Test RMSE | Test NASA | rows changed |
| --- | --- | --- | --- | --- | --- |
| R2 running-min | 10.737 | 21053.0 | 3.964 | 1906.6 | 13 000 |
| R2b extremum of the prefix fit | 9.623 | 18713.9 | 4.173 | 2182.9 | 10 715 |
| `min(PAVA)` | 10.737 | 21053.0 | 3.964 | 1906.6 | 13 000 |

## Decision

R2b **is** the extremum of the online prefix PAVA fit. The returned series MAY
rise, and that rise is the mechanism behind its gain, not a defect to be
corrected. The rule is named `R2b_ISOTONICO_CAUSAL` and MUST NOT be described as
a monotonicity rule, a non-increasing series, or `R2b_MONOTONIA`.

Causality remains part of the contract: the value at `t` reads only positions
`<= t`. Strict monotonicity, if wanted, is R2 — a separate decision, not a
relabelling of this one.

## Evidence

* `min(PAVA) == np.minimum.accumulate(raw)` pointwise on all 14 915 pure rows, and
  it reproduces R2 on all four recorded figures (10.737 / 21053.0 OOF,
  3.964 / 1906.6 test).
* Rows changed: R2 13 000, R2b 10 715 — R2b is the gentler correction.
* Maximum positive increment: +1.328848 for R2b, 0.000000 for its envelope.
* The gate reproduces every figure from `_p1_oof_cache.npz`:
  `python scripts/freeze_rules_evidence.py` prints the table above and exits 0.

## Alternatives rejected

| Alternative | Why not |
| --- | --- |
| Call it monotonicity and enforce the envelope | That is R2 exactly; the gain disappears (RMSE 9.623 → 10.737, NASA 18713.9 → 21053.0 OOF). |
| Rename to `R2b_MONOTONIA` and keep the behaviour | The name would assert a property the series does not have; every reader would inherit a false claim. |
| Ship R2 instead | Better on test (4.173 → 3.964 RMSE, 2182.9 → 1906.6 NASA), worse on OOF — a fleet-regime trade-off that needs its own decision, not a silent substitution. |
| Move the correction into the model | RULES-07 forbids it; it would retrain and invalidate `models/ds02_manifest.json`. |

## Consequences

* User-facing copy is constrained (UI-RULES-01): R2b is a *causal isotonic
  adjustment*, the extremum of the online prefix fit. A scan test rejects the
  banned formulations in `app/` and in the live rule strings.
* The gate (`scripts/freeze_rules_evidence.py`) enforces the numbers; a drift in
  RMSE, NASA, rows changed, the increment or the coverage fails with exit 4.
* The R2-vs-R2b trade-off is recorded here instead of argued in prose; if the
  fleet regime changes, the comparison can be re-measured without renaming
  anything.
* Future descriptions inherit the corrected vocabulary, so the mislabel cannot
  quietly return through a docstring.
