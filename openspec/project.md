# Project: C-MAPSS / N-CMAPSS Remaining-Useful-Life Prediction

_Bootstrap context for SDD: goal, datasets, layout, pipelines, artifact inventory and metric conventions._

**Status:** Active
**Date:** 2026-10-19

---

## Goal

Predict the **remaining useful life (RUL)** of turbofan engines from multivariate sensor
telemetry, and do it in a way that is deployable: an artifact that can be loaded and
queried outside the authoring notebook.

The project runs two independent pipelines over two datasets and keeps a documented
record of four design iterations, so that every architectural choice can be traced back
to the measurement that motivated it.

## Datasets

| Dataset | Format | Location | Shape |
| --- | --- | --- | --- |
| N-CMAPSS **DS02** | HDF5 | `archive/CCMaps/N-CMAPSS_DS02-006.h5` | keys `A_dev`, `W_dev`, `X_s_dev`, `Y_dev` and `A_test`, `W_test`, `X_s_test`, `Y_test` |
| C-MAPSS **FD001** | whitespace text | `archive/CMaps/train_FD001.txt` (+ `test_FD001.txt`, `RUL_FD001.txt`) | 21 sensors + 3 operational settings, one failure mode |

DS02 declares its channel names in the file itself: `W_var` carries the 4 operational
conditions `alt, Mach, TRA, T2`, and `X_s_var` carries the 14 physical sensors
`T24, T30, T48, T50, P15, P2, P21, P24, Ps30, P40, P50, Nf, Nc, Wf`.

The DS02 loader probes candidate paths and **raises** if no HDF5 resolves
(`resolve_ds02` names every path it probed). The old FD001 fallback was removed
by the `2026-10-20-ds02-honest-deployable` change; FD001 is only reachable
through the separate, explicit `load_fd001_reference`, which never touches the
DS02 artifact path.

## Repository layout

```text
.
├── 02_DS02_ensemble_RUL.ipynb     # DS02 pipeline — executed source of truth
├── notebook_nasa_fd001.ipynb      # FD001 pipeline
├── src/ds02_rul/                  # importable DS02 pipeline (pooling, residualizer,
│                                  #   ensemble, features, stacking, persistence, pipeline)
├── app/                           # FastAPI service + Streamlit dashboard
├── mia/                           # rules layer (opt-in post-processing)
├── docs/decisions/                # ADR-001 … ADR-009
├── docs/informes/                 # measurement reports and audits (one per question)
├── docs/plans/                    # design plans (UI/DSS, external evolution plan)
├── tests/                         # pytest suite: artifact contract, DSS, rules layer
├── scripts/
│   ├── build_02_notebook.py        # generator for the DS02 notebook (pure nbformat)
│   ├── build_ui_cache.py           # DSS cache builder (app/cache)
│   ├── freeze_rules_evidence.py    # gate for the rules-layer figures (RULES-06)
│   ├── extract_legacy_artifact.py  # weight extraction (must run under Python 3.10)
│   ├── repackage_artifact.py       # portable bundle from legacy weights (Python 3.10)
│   ├── ablate_meta_cycle.py        # measures what the cycle counter buys
│   ├── predict_ds02.py             # DS02 CLI entry point
│   ├── predict.py                  # FD001 v3 bundle inference entry point
│   ├── v3_*.py                     # FD001 v3 feature/model/run/finalize modules
│   ├── probe_*.py                  # experiment probes (evidence behind decisions)
│   └── verify_blend.py             # EMA + blend verification probe
├── models/                         # persisted artifacts (never hand-edited)
├── archive/                        # datasets (read-only inputs)
├── ensemble.joblib                 # DS02 full pipeline (copy under models/)
└── scaler.joblib                   # DS02 18-channel StandardScaler (copy under models/)
```

## Pipelines

### FD001 — `notebook_nasa_fd001.ipynb`

Classical C-MAPSS single-failure-mode pipeline. Its deployable form is the v3 bundle
(`models/v3_bundle.joblib`) plus a policy and a PSI reference, served by
`scripts/predict.py`, which returns a point RUL, an 80 % interval, a traffic-light alarm
and a PSI-based drift report. This pipeline is **out of scope** for the
`ds02-production-hardening` change.

### DS02 — `02_DS02_ensemble_RUL.ipynb`

Champion/challenger hybrid stacking ensemble:

1. **Ingestion** of the HDF5, downsampled with `STRIDE = 100`.
2. **Physical residualization**: each sensor is regressed on a degree-2 polynomial of the
   operational regime (`Ridge(alpha=1.0)`) and the residual is standardized, so the tabular
   model learns degradation rather than pilot manoeuvres.
3. **BiLSTM champion** over 50-cycle windows of 19 channels (18 scaled signals plus a
   normalized-cycle channel), aggregating the sequence with last step + average + max.
4. **LightGBM challenger** over 93 residualized tabular features with a quantile objective.
5. **Stacking meta-learner** (RidgeCV + a light LightGBM) fit on a held-out unit.
6. **Beta shrinkage** toward the BiLSTM and **causal EMA** smoothing per unit.

Only the BiLSTM is trained on GPU/CPU-heavy compute; the tabular branch is seconds.

### Rules layer — `mia/` (opt-in)

Post-processing over an existing prediction, in two passes: correction
(`R2b_ISOTONICO_CAUSAL`, `R6_BANDA`) then decision (`R1_SEGURIDAD`, `R9_HANGAR`,
`R8_INSPECCION`, `R7_APTO`). Nothing is retrained and no artifact is written.
The toggle in `app/dashboard_ds02.py` is **off by default**, and the raw cached
reading remains the one that reproduces `models/ds02_manifest.json`.

The calibration (`mia/calibracion_banda.json`) is frozen on 14 915 pure OOF rows
(units 2, 5, 10, 18, 20; unit 16 excluded as in-sample), with coverage 0.9012 in
OOF and 1.0000 on the test panel. `python scripts/freeze_rules_evidence.py`
recomputes every figure and exits non-zero on drift. See
[ADR-009](../docs/decisions/ADR-009-r2b-is-an-isotonic-fit-not-a-monotonicity-rule.md)
and the [rules-engine spec](changes/2026-10-21-ds02-rules-layer/specs/ds02-rules-engine/spec.md).

## How to run

```bash
# 1. Activate the project virtualenv (Python 3.12)
.venv\Scripts\activate

# 2. Execute the DS02 notebook (regenerates models/ensemble.joblib + models/scaler.joblib)
jupyter nbconvert --to notebook --execute 02_DS02_ensemble_RUL.ipynb

# 3. FD001 inference (v3 bundle)
python scripts/predict.py --fd FD001 --engine 12 --cut 80
python scripts/predict.py --fd FD001 --report
```

```bash
# 4. Run the pytest suite
python -m pytest tests -q
```

The suite never retrains and never writes under `models/`. Pipeline correctness is still
established by re-executing the notebook and comparing the recorded metrics against
[the deployed DS02 spec](specs/rul-prediction-ds02/spec.md).

## Notebook generation convention

> 📌 **The `.ipynb` files are build outputs, not source.**

`scripts/build_*.py` are pure `nbformat` builders: they emit every code and markdown cell as
a verbatim triple-quoted string and write the `.ipynb`. `scripts/build_02_notebook.py`
(754 lines) does **not** execute the notebook and writes or loads no artifacts — it only
serializes cells.

Consequences:

- To change a cell, edit the builder and regenerate. Hand-editing the notebook creates a
  divergence that the next regeneration silently destroys.
- The builder is reviewable as ordinary Python; the notebook is not. Review diffs in the
  builder.

## DS02 artifact contract (after 2026-10-20)

Loading any DS02 artifact MUST NOT require any name defined in `__main__`, and MUST
NOT require the Python minor version that wrote it. The graph lives in
`models/bilstm_ds02.keras` (native format, `LastStepPooling`, no bare lambda); the
bundle holds only fitted scikit-learn / LightGBM objects plus a path to the graph.
`models/ds02_manifest.json` records shape, partition, seed, environment and metrics.

Every transform is fitted on the fit units `[2, 5, 10, 18, 20]` only, and `beta` is
selected by grouped out-of-fold cross-validation. See
[the change](changes/2026-10-20-ds02-honest-deployable/proposal.md).

The rules layer in `mia/` is post-processing over the frozen prediction: it never
retrains and is **not** part of this artifact contract.

## Artifact inventory

| Artifact | Produced by | Contents |
| --- | --- | --- |
| `ensemble.joblib` | DS02 notebook cell 15 | `HybridStackingEnsemble`: BiLSTM (Keras), `lgb_standalone`, `ridge_meta`, `lgb_meta`, `residualizer` (`poly_w` + 14 Ridge models + `res_scaler`), `scaler`, `scaler_w`, `n_op=4`, `window_size=50`, `beta=1.0`, `ema_span=5` |
| `scaler.joblib` | DS02 notebook cell 15 | `StandardScaler` fit on the 18-dimensional `X_train_full` |
| `models/ensemble.joblib`, `models/scaler.joblib` | same cell | identical copies of the two above |
| `models/v3_bundle.joblib` | FD001 v3 pipeline | FD001 model + `q10`/`q90` quantile models + `window` + `features` + `version` |
| `models/alarm_policy.json`, `models/psi_reference.json` | FD001 v3 pipeline | alarm thresholds and drift reference distribution |

The DS02 notebook closes with an artifact-reload check: it reloads both `joblib` files and
runs one sample through `predict()`, printing a predicted RUL of **61.25** against a true
value of **58.00**.

> ⚠️ **Known limitation:** both `HybridStackingEnsemble` and `SensorResidualizer` are defined
> *inside* the notebook, so the pickle references `__main__`. Loading `ensemble.joblib` in a
> fresh process requires those classes to be importable first. See
> [the hardening change](changes/2026-10-19-ds02-production-hardening/proposal.md).

## Metric conventions

Four metrics are reported side by side:

| Metric | Formula | Direction |
| --- | --- | --- |
| RMSE | `sqrt(mean_squared_error(y_true, y_pred))` | lower is better |
| MAE | `mean_absolute_error(y_true, y_pred)` | lower is better |
| R² | `r2_score(y_true, y_pred)` | higher is better |
| NASA score | see below | lower is better |

```python
def calculate_nasa_score(y_true, y_pred):
    d = np.asarray(y_pred).ravel() - np.asarray(y_true).ravel()
    score = np.where(d < 0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)
    return float(np.sum(score))
```

Two conventions are easy to get wrong and are therefore stated explicitly:

1. **The NASA score is a SUM, not a mean.** Its magnitude therefore scales with the number
   of windows (6196 on the DS02 test split). It is only comparable across models evaluated
   on the *same* rows — never across datasets or splits.
2. **The DS02 path applies no 125-cycle clamp.** `RUL.clip(upper=125)` appears only in the
   FD001 fallback branch of the loader. DS02 RUL targets are used as recorded.

The asymmetry is deliberate: underestimating RUL is penalized more gently
(`exp(-d/13)`) than overestimating it (`exp(d/10)`), because predicting *more* life than
remains is the dangerous error.

## Experiment history

Four iterations, each kept because the previous one failed in a measurable way:

| # | Iteration | Change | Test outcome | Lesson |
| --- | --- | --- | --- | --- |
| 1 | Baseline | Only the 14 sensors `X_s`; LightGBM with 4 statistics (`mean, max, min, last`); fixed weights `0.6*LGBM + 0.4*BiLSTM`; BiLSTM stalled in the first 5 epochs | LGBM RMSE 10.82; BiLSTM RMSE 6.939 (NASA 5278); fixed ensemble RMSE 8.091 (NASA 6747) | The ensemble **destroyed** the BiLSTM — averaging is not free |
| 2 | Regime integration | `W + X_s` concatenated (18 channels); LightGBM to 126 features (7 statistics over 18 channels); BiLSTM with BatchNorm + `Huber(delta=10.0)`; weights by inverse validation variance (`0.23 LGBM + 0.77 BiLSTM`) | LGBM 10.917 (NASA 12155.3); BiLSTM 6.874 (NASA 5055.2); dynamic ensemble 7.180 (NASA 5542.1) | `max/min/std/diff` over `W` injected pilot-manoeuvre noise and overfit the trees (MSE 3.4× worse than the BiLSTM); any direct linear average contaminated the BiLSTM |
| 3 | Champion-challenger + noise pruning | Pruned noisy `W` statistics (kept `mean` and `last` of `W` + 5 descriptors of `X_s` = 78 features); hard regularisation (`max_depth=4, num_leaves=15`); residual corrector attempt | LGBM 13.349; BiLSTM 5.701 (R² 0.9069, NASA 3522.6); hybrid 5.701 (NASA 3522.6) | Without accumulated cycle, and without physically decoupling `X_s` from `W`, standalone LightGBM degraded to 13.349 RMSE; a corrector trained on overfitted train residuals made the grid pick `alpha = 0.00` |
| 4 | **Current SOTA** | Thermodynamic polynomial residualization + dual temporal pooling + out-of-fold stacking + causal EMA | LGBM 7.087 / NASA 5768.4; BiLSTM 5.693 / NASA 3822.2; hybrid **5.522 / NASA 3435.1** | See [the deployed spec](specs/rul-prediction-ds02/spec.md) |

The probes that produced the evidence are scripts, not notebooks:
`scripts/probe_q35.py` (recovered the quantile-0.35 LightGBM recipe),
`scripts/probe_cyclech.py` (BiLSTM with/without the cycle channel),
`scripts/probe_variants2.py` (pooling variants),
`scripts/probe_variants.log` (which selected unit 16 as the validation unit),
`scripts/verify_blend.py` (EMA + blend construction).

## Known limitations

Six items are recorded as technical debt. They are the subject of
[the 2026-10-19 hardening change](changes/2026-10-19-ds02-production-hardening/proposal.md):

1. `ensemble.joblib` depends on the execution context (`__main__`-defined classes).
2. The Keras `Lambda` layer wrapping a bare Python lambda is fragile across processes.
3. Beta calibration is in-sample with respect to the meta-learner.
4. Preprocessing objects are fit on all six train units, unit 16 included.
5. BiLSTM results vary materially across seeds (seed 42: RMSE 5.447; seed 7: RMSE 6.564).
6. Compute starvation invalidated some probe comparisons (one epoch took 1553 s).

---

## References

- Saxena, A. et al. "Damage propagation modeling for aircraft engine run-to-failure
  simulation." _PHM 2008_. https://doi.org/10.1109/PHM.2008.4711414
- Chao, M. A. et al. "Aircraft Engine Run-to-Failure Dataset under Real Flight
  Conditions." _PHM Asia-Pacific 2021_ (N-CMAPSS). https://doi.org/10.36001/phmap.2021.v2i1.1372
