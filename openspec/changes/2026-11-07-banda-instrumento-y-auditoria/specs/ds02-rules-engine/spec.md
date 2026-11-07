# Spec delta: the shipped rules band MUST be verifiable from a clone

**Change:** `2026-11-07-banda-instrumento-y-auditoria`
**Capability:** `ds02-rules-engine`
**Status:** Applied
**Sources of truth:** `src/mia/calibracion_banda.json`,
`src/mia/instrumento_oof.npz`, `scripts/freeze_rules_evidence.py`,
`scripts/freeze_oof_instrument.py`, `docs/decisions/ADR-012-verify-the-band-against-a-frozen-instrument.md`

## ADDED

### The band's evidence MUST travel with the repository

`mia/calibracion_banda.json` is fitted on 14 915 pure out-of-fold rows (units 2, 5, 10, 18,
20; unit 16 excluded as in-sample) that were selected from
`notebooks/artifacts_c/nb2_selection.joblib`. That joblib is git-ignored, so the rows MUST
be frozen into a tracked instrument, `mia/instrumento_oof.npz`
(`units`, `cycles`, `y`, `pred_ema`), and the derivation MUST be re-runnable from the
joblib by `scripts/freeze_oof_instrument.py`.

The gate MUST NOT require a git-ignored cache to verify the published band.

#### Scenario: the published band is verified with no local cache

- GIVEN a checkout of the repository with no `_p1_oof_cache.npz`
- WHEN `python scripts/freeze_rules_evidence.py` runs with no flags
- THEN it SHALL read `mia/instrumento_oof.npz`
- AND it SHALL exit 0 only if the pure mask has 14 915 rows, the four bins are
  `[5125, 6094, 3135, 561]`, `q_low` is
  `[-4.3621, -9.0949, -24.5658, -24.7372]` and `global_quantiles` is
  `[-21.2129, 19.7804]`
- AND it MUST leave `mia/calibracion_banda.json` byte-identical

#### Scenario: the instrument derives back to the band

- GIVEN the bundle-C selection joblib present on the authoring machine
- WHEN `python scripts/freeze_oof_instrument.py --check` runs
- THEN the derived bins and quantiles SHALL equal the committed band at its recorded
  4 decimals
- AND reducing every third row before smoothing SHALL be the derivation used, because
  smoothing before reducing yields `[5139, 6145, 3084, 547]` and `-4.2639` in bin 0

### Figures the instrument cannot support MUST be reported, not asserted

The monotonicity table of §13 was measured on the 2026-10-26 out-of-fold cache (17 450
rows, step-1), which the instrument cannot reconstruct. On the instrument path that table
MUST be printed as `reported`; a difference in those figures MUST NOT be classified as
band drift.

#### Scenario: refit path is explicit and honest

- GIVEN `_p1_oof_cache.npz` present
- WHEN `python scripts/freeze_rules_evidence.py --cache _p1_oof_cache.npz` runs
- THEN the out-of-fold table MAY be recomputed from it
- AND the run SHALL exit non-zero when the refit does not reproduce the recorded figures,
  because the base refit is not bit-deterministic on CPU

## MODIFIED

### Coverage is measured on the instrument

The rules layer's realised coverage SHALL be measured on the 14 915 frozen rows, not on a
refit. Measured value: **0.901643** (bin 0 0.9048, bin 1 0.8906, bin 2 0.8983, bin 3
0.9533), against a nominal target of 0.90.

#### Scenario: the coverage test does not depend on a refit

- GIVEN the tracked instrument only
- WHEN the coverage test runs
- THEN it SHALL compute the covered fraction on `y >= y - (q_low + correction)` over the
  14 915 rows
- AND it MUST assert the result is within 0.90 ± 0.01

## Related capabilities

Cites, without modifying, `rul-prediction-ds02` (the artifact's internal band, 17 450 rows)
and `ds02-live-evaluation` (the runtime assertions that read the JSON).
