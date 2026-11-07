# ADR-012: Verify the conformal band against a frozen instrument, not against a refit

## Status

**Accepted** — 2026-11-07. Changes what the gate checks; no figure, band or
artifact changes with this decision.

## Date

2026-11-07

## Context

`mia/calibracion_banda.json` was re-frozen on **2026-11-04** (commit `d02ff2d`,
"recalibration banda R6 a bundle C") from the step-3 selection stored in
`notebooks/artifacts_c/nb2_selection.joblib`. That file is git-ignored, so the
only rows the band was actually fitted on were invisible to a clone and to CI.

The gate (`scripts/freeze_rules_evidence.py`) rebuilt its own instrument from
`_p1_oof_cache.npz` — the step-1 out-of-fold rows — and compared that against
the JSON. Those are not the same rows:

| Instrument | Rows | Paired with |
| --- | --- | --- |
| `_p1_oof_cache.npz` (step-1 cache, 2026-10-26) | 17 450 | the OOF table quoted in §13 |
| `nb2_selection.joblib` → reduced pure series | 14 915 | the band currently shipped |

So the gate reported **drift that did not exist in the JSON**: it compared a
band fitted on one selection with figures measured on another, and labelled the
mismatch "the numbers moved". Five tests failed for that reason. A red gate that
is red for a bookkeeping error teaches the team to ignore the gate.

The real question is narrower than "does the model reproduce": it is **"does the
published band correspond to the rows it claims to be calibrated on?"** The base
refit is not bit-deterministic on CPU, so a test that re-trains cannot answer it
at any fixed tolerance.

## Decision

1. The calibration rows become a **tracked artifact**: `src/mia/instrumento_oof.npz`
   (115 225 bytes, 14 915 rows, columns `units`, `cycles`, `y`, `pred_ema`),
   derived and re-verifiable by `scripts/freeze_oof_instrument.py`
   (`--write` / `--check`).
2. The gate's **default path reads that instrument** and verifies the band
   against it: pure-mask units `[2, 5, 10, 18, 20]`, 14 915 rows, bins
   `[5125, 6094, 3135, 561]`, `q_low` `[-4.3621, -9.0949, -24.5658, -24.7372]`,
   `global_quantiles` `[-21.2129, 19.7804]`.
3. The **OOF table is `reported`, not asserted**, on that path. It was measured
   on a cache that git ignores and cannot be re-derived from these rows; printing
   it as a contract would be asserting a number nobody can reproduce.
4. `--cache PATH` keeps the re-derivation path for development. On this tree it
   **exits 5** (the refit does not reproduce the 2026-10-26 figures). That is the
   honest statement, and it is now confined to an explicit flag instead of being
   the default.
5. The tests point at the instrument: the five that failed on the instrument
   mismatch now run in `--instrument` mode, and the coverage test measures
   **0.901643** on the frozen rows instead of a refit.
6. The UI line that said `Banda 90 %` now says
   `objetivo nominal 90 % · cobertura medida empíricamente` (and
   `objetivo 90 % · cobertura medida` in the chart legend), with
   `tests/test_live_eval.py` and the three documents under
   `openspec/changes/poda-redundancias-streamlit-2/` updated to match.

## Evidence

* `scripts/freeze_oof_instrument.py --write` reproduces the committed band at its
  4 recorded decimals, then `--check` exits 0.
* `python scripts/freeze_rules_evidence.py` (no flags) exits **0**; coverage
  **0.901643** on the instrument (bin 0 0.9048, bin 1 0.8906, bin 2 0.8983,
  bin 3 0.9533).
* `python scripts/freeze_rules_evidence.py --cache _p1_oof_cache.npz` exits **5**.
* The derivation is a measurement, not a preference: smoothing the step-1 series
  and *then* subsampling gives bins `[5139, 6145, 3084, 547]` and `-4.2639` in
  bin 0; subsampling and *then* smoothing gives `[5125, 6094, 3135, 561]` and
  `-4.3621`, which is what the JSON records. Only the second reproduces it.
* `pytest -q` → **345 passed, 0 failed, 0 skipped** (2 min 55 s). Before this
  decision: 336 passed, 6 skipped, and 5 failures on the instrument mismatch.

## Alternatives rejected

| Alternative | Why not |
| --- | --- |
| Re-freeze `EXPECTED` to today's measurements (9.491 → 10.90 RMSE) | Would republish a headline figure and force edits to §13, ADR-009 and the rules-engine spec to accommodate a mismatch that is not a finding about the band. |
| Version `nb2_selection.joblib` and fit the band in CI | A 14 915-row opaque joblib of fitted pipeline objects versus 4 columns of numbers; and the band would be re-fitted on every run, so the artifact under test would move. |
| Leave the gate red and documented as "known stale" | A gate that is expected to fail is not a gate. The failure was bookkeeping, and documenting it would preserve the bookkeeping error. |
| Fix the base refit's non-determinism | Out of scope and a different problem (TF/CPU float ordering). This decision scopes the nondeterminism to `--cache` instead of hiding it. |
| Unilateral band widening because the tail bin looked thin | Withdrawn before acting: measured on the frozen rows, bin 3 is **over**-covered (0.9533), not under. The 76.4 % that motivated it belonged to another subset. |

## Consequences

* **What the test proves, stated plainly.** It proves the published band is the
  quantiles of *those* 14 915 rows, at the precision the JSON records. It does
  **not** prove those rows are the right calibration set — that is carried by the
  derivation (units, size, exact bins and global quantiles) and by
  `calibracion_banda.json#procedencia`. Two guarantees, neither redundant.
* The band, `models/ds02_manifest.json` and the margin guard are untouched.
* A clone can verify the band with no notebook artifact and no TF in the process.
* Anyone auditing the *model* rather than the *band* still has `--cache`, and its
  exit 5 says in the open that last month's table is not reproducible by refit.
* `reported` is a weaker verb than `asserted`; it is used where the alternative
  would be a false contract.

## Verification

* `pytest tests -q` green (345 passed).
* Gate default exits 0; `--cache` exits 5; `--instrument` exits 0.
* `git check-ignore src/mia/instrumento_oof.npz` returns 1 (tracked, not ignored).
* `git status` shows the npz as the only new binary artifact.
