# Proposal: close the non-retraining audit findings

## Why

The 2026-10-21 audit of the DS02 rule layer (`AUDITORIA_ds02_2026-10-21.md`)
found eighteen issues; none of them requires retraining the frozen artifacts.
This change closes the ones that are pure code, calibration arithmetic, or
provenance. The two items that need a model decision (unifying the two
calibrations numerically, and improving accuracy in the critical zone) are
deliberately left out and stay recorded as open decisions.

## What changes

| # | Finding | Fix |
| --- | --- | --- |
| 1 | `--write` re-freezes the JSON before checking figure drift | check first, write only when nothing drifted |
| 2 | Alarm and critical-zone MAE hardcode `25.0`; per-unit metrics read the uncorrected frame | pass `threshold_aog` and the frame actually in use |
| 3 | State uses `lower.min()`, the alarm uses the mean `lower` | one criterion: the worst window of the cycle |
| 4 | Work orders do not state which reading produced them | `banda`, `correccion` and per-unit `regla` in JSON and CSV |
| 5 | The live order decides with `classify`, not `mia.motor` | decide with the motor and serialise its rule and motive |
| 6 | The two calibrations are used silently | the surface declares which band governs the numbers |
| 7 | Crossing 75 cycles collapses the upper bound by 19.8 cycles | a small-sample bin may only widen the band |

## Non-goals

- Numerically unifying the artifact band and the R6 recalibration. The raw
  reading is a frozen contract (`models/ds02_manifest.json`); changing it is a
  new experiment.
- Improving critical-zone accuracy.
- Retraining, re-executing the notebook, or writing under `models/`.

## Byte-compatible artifacts

`models/ensemble.joblib`, `models/bilstm_ds02.keras`,
`models/ds02_manifest.json`, `app/cache/*`, `mia/calibracion_banda.json` and
`_p1_oof_cache.npz` are unchanged. The four recorded metric rows stay exactly
as measured. The gate keeps its four exit codes.

## Rollback

Every change is behind a function signature that a caller can ignore: revert the
seven files listed in `tasks.md` and the suite returns to its previous state.
No data or artifact migration is involved.
