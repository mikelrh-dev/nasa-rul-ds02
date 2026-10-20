# Proposal: DS02 Production Hardening

**Change:** `2026-10-19-ds02-production-hardening`
**Status:** Proposed
**Date:** 2026-10-19
**Capability:** [`rul-prediction-ds02`](../../specs/rul-prediction-ds02/spec.md)

---

## Why

The DS02 hybrid stacking pipeline is the best model this project has produced. On the test
units `[11, 14, 15]` it reaches **RMSE 5.522** and a **NASA score of 3435.1**, beating both
its own champion and every earlier iteration:

| Model | RMSE | MAE | R² | NASA score |
| --- | --- | --- | --- | --- |
| LightGBM standalone (quantile 0.35, 93 features) | 7.087 | 5.584 | 0.8562 | 5768.4 |
| BiLSTM 2-layer, triple pooling | 5.693 | 4.449 | 0.9072 | 3822.2 |
| BiLSTM + causal EMA | 5.597 | 4.331 | 0.9103 | 3716.8 |
| **Hybrid stacking (beta=1.00, EMA span=5)** | **5.522** | 4.795 | **0.9127** | **3435.1** |

The problem is not accuracy. It is that **the result is not deployable, and one of its claims
is not honest**.

**Three artifacts do not survive the notebook process.**

1. `HybridStackingEnsemble` and `SensorResidualizer` are defined *inside* the notebook
   (cells 11). `joblib.dump(ensemble, 'ensemble.joblib')` therefore writes a pickle whose
   class references point at `__main__`. Loading that artifact in a fresh process fails unless
   the caller happens to have defined the same classes with the same module path first. The
   artifact is a file, but it is not an artifact.
2. The Keras sub-model contains `layers.Lambda(lambda z: z[:, -1, :], name="last_step")` — a
   `Lambda` layer wrapping a bare Python lambda. Bare lambdas are not serializable by name, so
   the layer is reconstructed from bytecode or not at all, depending on the deserialization
   path. It is the single most fragile object in the pipeline.
3. Nothing records *which* data, *which* seed and *which* code version produced the artifact.
   Reproducing a number requires reading the notebook by hand.

**One claim is overstated.** The spec says the stacking is out-of-sample. That is true of the
**base models** — unit 16 is excluded from the BiLSTM and LightGBM fits, so its predictions are
genuine out-of-fold predictions. It is **not** true of the **beta selection**: `ridge_meta` and
`lgb_meta` are fit on the unit-16 rows, and the beta grid is then scored on those same unit-16
rows. Unit-16 validation RMSE collapses to **0.308** against the BiLSTM's **4.221**, the
criterion is dominated by that in-sample advantage, and the grid is pushed to its maximum:
`opt_beta = 1.00`. The selection is not a measurement of generalization; it is a measurement of
the meta-learner memorizing 2535 rows.

**Two further facts make the current reporting unsafe.** BiLSTM quality swings materially with
the seed (seed 42: RMSE 5.447; seed 7: RMSE 6.564), so a single-seed number is not an estimate
of anything. And at least one probe run was compute-starved — a single epoch took 1553 s — which
silently invalidates comparisons against better-funded runs.

## What Changes

| # | Change | Addresses |
| --- | --- | --- |
| 1 | Extract `SensorResidualizer`, `HybridStackingEnsemble`, `causal_ema_by_unit` and `calculate_nasa_score` into an importable `src/ds02_rul/` package | Limitation 1 (context-dependent pickle) |
| 2 | Replace the bare-lambda `Lambda` with a serializable last-step pooling layer, and persist the Keras model as a native `.keras` artifact instead of embedding it in a `joblib` pickle | Limitation 2 (fragile `Lambda`) |
| 3 | Select `beta` by **grouped leave-one-unit-out cross-validation over the train units**, aggregating by median and reporting the selection spread | Limitation 3 (in-sample beta) |
| 4 | Add a **multi-seed evaluation harness** reporting mean ± std, plus a compute-budget guard that flags a starved run instead of silently comparing it | Limitations 5 and 6 |
| 5 | Add `scripts/predict_ds02.py` as the stable DS02 inference entry point | Deployability gap |
| 6 | Emit an **artifact manifest** recording version, seed, and a data fingerprint alongside every persisted artifact | Reproducibility gap |

Explicitly **not** changed: the model family, the residualization math, the 93-feature contract,
the BiLSTM architecture, the EMA operator, or the metric definitions. This is a hardening
change, not a modelling change. See
[the change spec](spec.md) for FR-1..FR-6 and [the design](design.md) for the decisions.

## Impact

### Affected specs

- [`rul-prediction-ds02`](../../specs/rul-prediction-ds02/spec.md) — modified requirements:
  **Beta shrinkage is selected out-of-sample** (strengthened), **Artifact persistence and
  reload** (strengthened), **Recorded SOTA results** (the single-seed caveat becomes a
  reporting obligation). New requirements are listed in
  [the capability delta](specs/rul-prediction-ds02/spec.md).

### Affected code

| Path | Action | Note |
| --- | --- | --- |
| `src/ds02_rul/__init__.py` | Create | Public exports |
| `src/ds02_rul/residualizer.py` | Create | `SensorResidualizer`, moved verbatim |
| `src/ds02_rul/ensemble.py` | Create | `HybridStackingEnsemble`, moved verbatim |
| `src/ds02_rul/pooling.py` | Create | `LastStepPooling`, serializable replacement |
| `src/ds02_rul/smoothing.py` | Create | `causal_ema_by_unit` |
| `src/ds02_rul/metrics.py` | Create | `calculate_nasa_score`, `evaluate_predictions` |
| `src/ds02_rul/stacking.py` | Create | Grouped-CV beta selection |
| `src/ds02_rul/persistence.py` | Create | `save` / `load` + artifact manifest |
| `scripts/predict_ds02.py` | Create | DS02 inference entry point |
| `scripts/build_02_notebook.py` | Modify | Import from the package instead of redefining classes |
| `02_DS02_ensemble_RUL.ipynb` | Regenerate | **Never edited by hand** — rebuilt from the builder |

> 🚫 `scripts/predict.py` serves the FD001 v3 bundle and MUST NOT be touched. It is a different
> dataset, a different feature contract and a different artifact.

### Affected artifacts

| Artifact | Before | After |
| --- | --- | --- |
| `ensemble.joblib` | Class refs point at `__main__` | Class refs point at `ds02_rul`; loads in any process |
| Keras model | Embedded in the `joblib` pickle, `.h5`-style graph with a bare `Lambda` | Persisted standalone in native `.keras` with a serializable pooling layer |
| Artifact manifest | None | `models/ds02_manifest.json` with version, seed, data fingerprint, metrics |

The **learned weights are unchanged**. Only their container and their import path change.

## Scope

### In scope

- The extractable `src/ds02_rul/` module, with no behaviour change and identical recorded metrics.
- Native `.keras` persistence plus a serializable last-step pooling layer.
- Honest, grouped cross-validated beta selection over the train units.
- A multi-seed evaluation harness with mean ± std reporting and a compute-budget guard.
- `scripts/predict_ds02.py` as the DS02 inference entry point.
- An artifact manifest recording version, seed and data fingerprint.

### Out of scope (non-goals)

- Retraining from scratch, or any attempt to improve on RMSE 5.522 / NASA 3435.1.
- Changing the model family, the 93-feature contract, the residualization math, or the
  metrics — including any temptation to clamp RUL at 125 on the DS02 path.
- New datasets, new splits, or re-tuning any hyperparameter.
- The FD001 pipeline, `notebook_nasa_fd001.ipynb`, `scripts/predict.py` and the v3 bundle.
- Serving infrastructure (HTTP API, container, scheduler). This change produces a *loadable
  artifact and a callable entry point*, not a service.
- Fixing limitation 4 (preprocessing fit on all six train units). It is documented and
  deliberately deferred: correcting it changes the learned numbers, which would make this
  change indistinguishable from a new experiment.

## Risks / Rollback

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Extraction changes a learned number | Low | Move code verbatim; the acceptance test is reproducing all four recorded rows exactly |
| Native `.keras` round-trip alters inference | Medium | Assert bit-equality of the pooled features and prediction on the same window before and after the format switch |
| Serializable pooling changes the 384-dim head semantics | Low | Replace `z[:, -1, :]` with an equivalent last-step slice; assert output equality on a fixed input tensor |
| Grouped-CV beta selection yields a different beta and different reported metrics | High (expected) | This is the point of the change; the new beta and its spread are *reported*, and the previous beta=1.00 result is retained as the recorded baseline |
| Multi-seed runs exceed the compute budget | Medium | The harness runs seeds sequentially with a per-seed wall-clock guard and marks starved runs invalid rather than including them |
| Regenerating the notebook diverges from the current `.ipynb` | Medium | Diff the regenerated notebook against the committed one before replacing it; keep the notebook as the reference implementation until the module reproduces the recorded metrics |

### Rollback

The change is additive at the artifact level. Rollback:

1. Keep the existing `ensemble.joblib` and `models/ensemble.joblib` — they are not overwritten
   until the module reproduces the recorded metrics.
2. Keep `02_DS02_ensemble_RUL.ipynb` as the reference implementation; the module is verified
   *against* it, not in place of it.
3. Delete `src/ds02_rul/`, `scripts/predict_ds02.py` and `models/ds02_manifest.json`.
4. Restore `scripts/build_02_notebook.py` and regenerate the notebook.

No data migration, no schema change, no change to the FD001 pipeline.

## Success criteria

1. `ensemble.joblib` loads in a **fresh Python process** with no notebook present, and
   `predict()` on the recorded sample window returns 61.25 (true value 58.00).
2. The Keras sub-model round-trips through native `.keras` and produces identical predictions
   before and after the format switch.
3. Beta is selected by grouped cross-validation over the train units, and both the selected
   value and its spread across folds are reported.
4. Multi-seed evaluation reports mean ± std for RMSE, MAE, R² and NASA score.
5. `python scripts/predict_ds02.py` returns a RUL for a DS02 window without importing the notebook.
6. The module reproduces the recorded test rows exactly, so the extraction is proven behaviour-preserving.

---

## See also

- [Change specification](spec.md) — FR-1..FR-6, NFR-1..NFR-5, AC-1..AC-8
- [Capability delta](specs/rul-prediction-ds02/spec.md)
- [Design](design.md) — architecture, decisions, migration plan
- [Tasks](tasks.md) — phased execution plan
- [Deployed spec](../../specs/rul-prediction-ds02/spec.md) — the current accepted truth
