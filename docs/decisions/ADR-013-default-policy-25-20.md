# ADR-013: Default triage policy 25 / 20

## Status

**Accepted** — 2026-11-12. Supersedes the default pair of ADR-008; the
lower-bound reasoning and the rejection of 50/25 remain.

## Context

ADR-008 set the defaults to `30/25` because the conformal lower bound never rises
above about 36 on this split, so a `50/25` rule would leave the fleet permanently
amber. That decision is still sound, but it is very conservative in practice:
on the five OOF development engines, `30/25` leaves 56–83 % of the healthy
cycles outside APTO.

The question is not whether the model predicts well enough to lower the APTO
cut; it is whether a lower cut still separates critical cycles from healthy
ones. The available read-only evidence is the frozen OOF instrument
(`src/mia/instrumento_oof.npz`, 14,915 rows, units 2/5/10/18/20), evaluated
leave-one-unit-out: the band is fitted on four engines and applied to the fifth.
This keeps the test units 11/14/15 out of the threshold decision.

## Decision

Use **25 / 20** as the default policy:

| State | Rule | Operational meaning |
| --- | --- | --- |
| APTO | `L_inf >= 25` | in service |
| INSPECCIÓN | `20 <= L_inf < 25` | scheduled inspection |
| HANGAR | `L_inf < 20` | immobilised, work order issued |

The `25` cut is the change that resolves the original false inspection at
`L_inf` 27.6. The `20` cut is not a cosmetic margin: it preserves a five-cycle
inspection band and keeps HANGAR below the critical RUL boundary.

`20/15` remains available only as an explicitly experimental scenario
(`Permisivo`), not as the default. `15/10` is removed from the presets: on the
same OOF validation it puts 19/125 critical cycles in APTO (15.2 %).

## Evidence

Leave-one-unit-out, cycle level (`lower_min`, the statistic the fleet uses):

| Policy | Critical <25 in APTO | Critical <25 in INSPECCIÓN | Minimum true RUL in APTO |
| --- | ---: | ---: | ---: |
| 30/25 | 0/125 | 0 | 29 |
| **25/20** | **0/125** | **6** | **28** |
| 20/15 | 6/125 (4.8 %) | 19 | 17 |
| 15/10 | 19/125 (15.2 %) | — | 15 |

Window level tells the same story: `25/20` leaves 0/4,916 critical windows in
APTO; `20/15` leaves 343 (7.0 %); `15/10` leaves 1,023 (20.8 %).

On the frozen test cache, `25/20` also leaves 0/75 critical cycles in APTO and
reduces false inspections from 49.9/72.7/64.7 % (U11/U14/U15) to
18.1/43.6/34.7 %. The test was already inspected, so it is confirmation, not
selection evidence.

The honest limitation is coverage: leave-one-unit-out coverage is only 0.76
globally, and U20 falls to 0.11 when excluded from calibration. The production
band fitted on all five OOF units covers 0.902 globally, but U20 individually
covers 0.732. `25/20` is the best-supported default, not a guarantee that the
band transfers to any new engine.

## Alternatives rejected

| Alternative | Why not |
| --- | --- |
| Keep 30/25 | Safe, but 56–83 % of healthy OOF cycles remain outside APTO; the availability cost is not justified by the validation evidence. |
| 20/15 | Excellent availability, but 6/125 critical cycles become APTO in OOF, concentrated in U20; the test-only result was optimistic. |
| 15/10 | 19/125 critical cycles become APTO; below the empirical cliff. |
| Retrain or recalibrate | Not required: the model and conformal band are unchanged. Only the post-processing cut moves. |

## Consequences

* `app/lib/_constantes.py`, `app/cache/cache_manifest.json` and the cache builder
  record `25/20`.
* The presets are Normal `25/20`, Prudente `30/25`, Conservador `35/30` and
  Permisivo `20/15` (experimental). The old `−10` preset is removed so a base
  change cannot silently produce `15/10`.
* No retraining, no re-scoring and no recalibration are needed. The cache keeps
  the same `pred/lower/upper`; decisions are recomputed on load.
* Existing twins and hangar records keep the policy they were created with.
* The next policy review should improve per-engine band coverage before making
  the threshold more permissive than `25/20`.
