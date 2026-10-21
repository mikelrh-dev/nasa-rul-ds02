# N-CMAPSS DS02 — Remaining Useful Life

Predicting remaining useful life on the N-CMAPSS DS02 turbofan dataset, packaged
so that it **loads, serves and is honest about what it measures**.

A BiLSTM over ordered windows and a quantile LightGBM over residualised tabular
features are reconciled by a learned meta-learner, shrunk towards the champion by
a factor `beta`, and smoothed with a causal per-unit EMA.

```
docker compose up --build      # http://localhost:8000/docs and http://localhost:8501
```

---

## Results — test units 11 / 14 / 15, 6 196 windows, mean ± std over seeds [42, 7, 123]

### Baseline v4.1.0 (kept for comparison)

| Model | RMSE | MAE | R² | NASA score |
| --- | --- | --- | --- | --- |
| LightGBM quantile 0.35 (standalone) | 7.098 ± 0.034 | 5.572 ± 0.034 | 0.8557 ± 0.0014 | 5772.5 ± 50.1 |
| BiLSTM triple pooling (standalone) | 6.152 ± 0.576 | 4.745 ± 0.332 | 0.8910 ± 0.0205 | 4308.0 ± 595.8 |
| **Hybrid stacking + causal EMA5** | **4.301 ± 0.068** | **3.181 ± 0.021** | **0.9470 ± 0.0017** | **2315.6 ± 20.0** |

The NASA score is a **sum** of asymmetric exponentials, not a mean, so it scales
with the number of scored windows and is only comparable between models evaluated
on these same rows.

**Read the standard deviations before the means.** The BiLSTM swings ±0.58 RMSE
across seeds; the hybrid is stable to ±0.068. The hybrid's spread is now *real*
rather than an artefact: with the cycle counter removed from the meta-learner the
stacking layer actually depends on the two base models, so it inherits their
variance instead of reading a counter (see the ablation section below).

### This revision — 2026-10-21

Same models, same protocol. The additions are two metrics, not extra accuracy.

| Model | RMSE | MAE | R² | NASA score |
| --- | --- | --- | --- | --- |
| LightGBM quantile 0.35 (standalone) | 7.098 ± 0.034 | 5.572 ± 0.034 | 0.8557 ± 0.0014 | 5772.5 ± 50.1 |
| BiLSTM triple pooling (standalone) | 6.337 ± 0.811 | 4.872 ± 0.756 | 0.8837 ± 0.0305 | 4509.9 ± 1051.1 |
| **Hybrid stacking + causal EMA5** | **4.344 ± 0.075** | **3.209 ± 0.058** | **0.9459 ± 0.0019** | **2338.2 ± 49.1** |

The 4.301 → 4.344 difference is TensorFlow CPU non-determinism between runs, not
a change in the model: the base models and the `beta` protocol are untouched.

**Macro-RMSE, which the weighted figure hides.** Per engine: 11 → 3.762,
14 → 8.319, 15 → 2.736. Unweighted mean **4.939**, against a window-weighted
**4.313**. The gap of +0.63 is the cost of engine 14 having both the worst error
and the fewest windows (760 of 6 196, yet 43.7 % of the squared error). The fleet
average is kinder than what a randomly chosen engine suffers.

**Prediction band (split conformal).** Target 90 %, realised **100 %** with a mean
width of **24.8 cycles** — 25.0 / 25.3 / 24.2 per engine, and no truth above the
upper bound. It is calibrated on the out-of-fold residuals of all six development
engines, which come from weaker fold models than the shipped ones, so the band is
**conservative by construction: a bound, not a decision-grade interval**. Narrowing
it would need more engines, not more quantiles. `predict_interval()` returns
`(point, lower, upper)`; `predict()` is unchanged.

---

## What the ablation actually found

The previous revision claimed that dropping the cycle counter costs
`LGBM → 13.349` and `hybrid → ~7.8`. Both numbers were quoted from different
designs and neither was measured on this pipeline. Measured here:

### Base models (seed 42)

| Variant | LGBM RMSE | BiLSTM RMSE | BiLSTM + EMA5 RMSE |
| --- | --- | --- | --- |
| `cyc_norm` ON (baseline) | 7.113 | 5.419 | 5.386 |
| `cyc_norm` OFF | **6.297** | 6.513 | 6.477 |
| `cyc_norm` OFF + baseline delta | 8.667 | 5.998 | 5.955 |
| `cyc_norm` ON + baseline delta | 8.578 | 5.980 | 5.955 |

Removing the counter from the **base models** costs the BiLSTM **+1.094 RMSE** —
three orders of magnitude less than the 13.349 that had been asserted, and it
*improves* LightGBM by 0.82. The counter is a genuinely valuable input for the
BiLSTM, which is why the fix removes it from the stacking layer only.

### Where the cycle counter really acts (seed 42, `scripts/ablate_meta_cycle.py`)

With `beta = 1.0` the final prediction **is** the meta-learner output, and the
meta-learner *as shipped until this revision* put all of its weight on the clock:

```
ridge coef [p_lstm, p_lgb, cyc_norm] = [0.0019, 0.0124, -98.4065]
lgb_meta feature importances          = [0, 0, 720]
```

| Configuration | RMSE | MAE | NASA | meta uses |
| --- | --- | --- | --- | --- |
| cycle available everywhere (previous revision) | 5.522 | 4.795 | 3435.3 | 100 % clock |
| cycle removed from every component | 5.568 | **3.742** | **3233.3** | p_lstm 0.34, p_lgb 0.69 |
| OLS on cycle alone | 14.327 | 13.148 | 20267.6 | — |
| constant | 20.022 | 17.059 | 48840.3 | — |

Four conclusions, all measured:

1. The 5.52 was **not** produced by the clock — a linear model on cycle alone
   scores 14.33. The base models do the work.
2. But when the clock was *available*, the learner preferred it and discarded both
   base models. That is why the hybrid's seed-to-seed variance was 0.001: it was
   not aggregating two noisy learners, it was reading a counter.
3. Removing the clock from the stacking layer — while keeping it in both base
   models, where it is a legitimate input — is the fix, and it is the
   configuration now shipped: **RMSE 4.301 ± 0.068** against the previous
   5.523 ± 0.001, with the meta-learner splitting its weight between the two
   branches instead of betting everything on one counter.
4. Removing it from *every* component instead (5.568) is a different experiment:
   it also re-trains the base models without the clock, which costs the BiLSTM
   more than the stacking layer gains.

The shipped artifact carries the clock in both base models and **not** in the
meta-learner. `models/ablation_meta_cycle.json` and `scripts/ablate_meta_cycle.py`
make the alternative reproducible.

---

## Leakage and calibration

| Property | Before | Now |
| --- | --- | --- |
| Rows behind `scaler`, `poly_w`, the 14 residual ridges | 52 635 (all six dev units, holdout included) | **44 982 (fit units only)** |
| `beta` selection | meta-learners fitted and scored on the same unit-16 rows | grouped **out-of-fold**, 3 folds, transforms refitted per fold |
| Fold `beta` values | single value `1.00` | `[1.00, 1.00, 0.00]` — median 1.00, IQR 0.50 |
| Meta-learning sample | 2 535 unit-16 windows (unchanged) | pooling the 14 915 out-of-fold windows of the five fit engines was **measured and rejected** — it learns a level prior that does not transfer |
| Prediction band | none | split conformal on out-of-fold residuals, asymmetric per predicted-RUL bin |
| Headline metric | window-weighted RMSE only | window-weighted **and** macro-RMSE, both in the manifest |
| Multi-seed | none | 3 seeds, mean ± std |
| Ingestion | silent FD001 fallback to the same artifact path | raises; names the paths it probed |

The fold vector is reported in full because a median alone would hide that one of
three folds selected `beta = 0` — i.e. that fold saw no value in the meta-learner.

---

## Deployability

The first artifact could not be loaded by the repository's own interpreter:

```
AttributeError: Can't get attribute 'HybridStackingEnsemble' on <module '__main__'>
ValueError: bad marshal data (unknown type code)     # even with the shim
```

| Fix | Evidence |
| --- | --- |
| Classes moved to `src/ds02_rul` | `joblib.load` succeeds in a clean 3.12 process |
| Bare `Lambda` → registered `LastStepPooling` | no `Lambda` in the graph; `.keras` round-trip exact |
| Weights migrated from the 3.10 artifact, no retraining | max abs difference **0.000e+00** |
| Graph persisted natively, not pickled in the bundle | `models/bilstm_ds02.keras`, 1.9 MB |
| Manifest with shape, partition, seed, env, fingerprint | `models/ds02_manifest.json` |
| Save-path guard | refuses a bundle whose scaler is not 18-channel / `n_op != 4` |

### Artifacts

| File | Contents |
| --- | --- |
| `models/bilstm_ds02.keras` | native Keras graph, 154 253 params, `(None, 50, 19)` |
| `models/ensemble.joblib` | `ds02_rul.HybridStackingEnsemble` — LightGBM, meta-learners, residualizer, scalers, `beta`, `ema_span` |
| `models/scaler.joblib` | 18-channel `StandardScaler`, DS02 fingerprint `[21930.0, 0.6249, 68.613, 475.0123]` |
| `models/ds02_manifest.json` | provenance, including `meta_features: 2` and the artifact SHA-256 |
| `models/ablation_meta_cycle.json` | the cycle-counter measurement above |
| `models/legacy/` | weights and reference predictions extracted from the original artifact |

---

## Interfaces

```bash
python scripts/predict_ds02.py --unit 11 --window 0        # RUL 60.21 ciclos
python scripts/predict_ds02.py --unit 11 --all --json      # full trajectory
uvicorn app.api:app --port 8000                            # POST /predict, GET /health
streamlit run app/dashboard.py                             # curve per engine
```

```python
from ds02_rul.persistence import load_ensemble
ensemble = load_ensemble("models/ensemble.joblib")
rul = ensemble.predict(raw_windows, cycles, units)   # (n, 50, 18) -> (n,)
```

`units` is warned about if omitted: without it the EMA smooths across engines.

---

## Reproduce

```bash
python -m pip install -r requirements.txt && pip install -e .

# Fase 0 — make the legacy artifact portable, no training (~2 min)
python scripts/extract_legacy_artifact.py     # must run under Python 3.10
python scripts/repackage_artifact.py          # must run under Python 3.10

# Fase 1 — retrain with the honest protocol (~30 min on CPU)
python scripts/build_02_notebook.py
jupyter nbconvert --to notebook --execute 02_DS02_ensemble_RUL.ipynb --inplace

# measurements and checks
python scripts/ablate_meta_cycle.py
python -m pytest tests -q
```

The notebook is a **build output**. Edit `scripts/build_02_notebook.py` and
regenerate; never hand-edit the `.ipynb`.

---

## Layout

```
src/ds02_rul/          importable pipeline (pooling, residualizer, ensemble, stacking, persistence)
scripts/               builder, migration, ablation, CLI, probes
app/                   FastAPI service and Streamlit dashboard
tests/                 artifact contract tests (10)
openspec/              SDD: deployed spec, change proposal, tasks
models/                artifacts + manifest + ablation results
02_DS02_ensemble_RUL.ipynb   executed notebook (generated)
```

---

## Honest limitations

- `beta` is selected on seed 42 only; the metric spread is reported across three
  seeds but the `beta` estimate is not.
- The meta-learner is fitted on a single holdout unit (16). Pooling the five fit
  engines' out-of-fold vector was tried in 2026-10-21 and made things worse, not
  better: predictions on unit 16 averaged 39.9 against a true 31.5, and test RMSE
  rose from 4.04 to 10.17 as `beta` went 0 → 1, because the dev engines outlive
  the test engines. Recorded in `INFORME_motor16_vs_oof.md`.
- The prediction band over-covers (100 % against a 90 % target, ~24.8 cycles
  wide). Its calibration rows come from fold models that are weaker than the
  shipped ones. It is a conservative bound, not a sharp interval.
- The `beta` fold vector still shows one of three folds selecting 0, so the
  shrinkage is poorly determined at the top of its range.
- The BiLSTM is compute-bound on CPU (~165 s per fit) and its seed variance
  (±0.67 RMSE) is larger than most differences the pipeline is asked to resolve.
- Docker images are defined and `docker compose config` parses, but the image was
  not built or run in this environment.
- `STRIDE = 100` means a 50-row window spans **0.44 flight cycles**, not 50
  cycles. The name elsewhere in the code overstates the horizon.
