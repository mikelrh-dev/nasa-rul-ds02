# Spec delta: remove the cycle counter from the stacking layer

**Change:** `2026-10-20-ds02-cycle-free-stacking`
**Status:** Implemented
**Capability:** [`rul-prediction-ds02`](../../specs/rul-prediction-ds02/spec.md)

---

## MODIFIED

### Requirement: Out-of-sample stacking contract

The capability SHALL build meta-features `Z = [pred_lstm, pred_lgb]` and SHALL fit
two meta-learners on the validation holdout rows:

- a `RidgeCV(alphas=np.logspace(-2, 3, 20))`
- a `LGBMRegressor(max_depth=3, num_leaves=7, n_estimators=120, learning_rate=0.03, min_child_samples=20)`

The meta prediction SHALL be the equal blend `p_meta = 0.5 * ridge_meta.predict(Z) + 0.5 * lgb_meta.predict(Z)`,
which reduces the variance of the stacked estimate relative to either meta-learner alone.

The out-of-sample property SHALL hold for the **base models**: unit 16 SHALL never appear in
the fitting data of the BiLSTM or the standalone LightGBM, so its predictions are genuine
out-of-fold predictions. The property SHALL NOT be claimed for the meta-learner fit itself.

`cyc_norm` SHALL be offered to both base models — channel 19 of the BiLSTM sequence and
feature 93 of the LightGBM tabular summary — because a fleet does know how many cycles an
engine has flown. It SHALL NOT be offered to the stacking layer: when it was, the meta-learner
put ~100 % of its weight on it (ridge coef `[0.0019, 0.0124, -98.4065]`, LightGBM importances
`[0, 0, 720]`) and discarded both base models, so the "ensemble" was reading a counter. That
shortcut is also what made the hybrid's seed spread collapse to ±0.001 RMSE.

#### Scenario: Meta-features are the two predictions

- GIVEN validation predictions from both base models
- WHEN `Z` is assembled
- THEN it has exactly two columns, in the order `[pred_lstm, pred_lgb]`
- AND `cyc_norm` is not among them

#### Scenario: Meta prediction is an equal blend

- GIVEN a fitted `ridge_meta` and a fitted `lgb_meta`
- WHEN the meta prediction is produced
- THEN it is the arithmetic mean of the two meta-learner outputs

## MODIFIED

### Requirement: Beta shrinkage is selected out-of-sample

The capability SHALL reconcile the meta prediction with the BiLSTM through a shrinkage factor
`beta` in `[0, 1]`:

```text
p_raw = p_lstm + beta * (p_meta - p_lstm)
```

The `beta` selection SHALL fit its own meta-learners on the **same design** the production
meta-learner is fitted on. When `use_cycle_feature=True` was passed while the production
meta-features were `[pred_lstm, pred_lgb]`, the grid was scored on a model that did not exist,
which is a mismatch between the selection procedure and the artefact.

#### Scenario: Selection and artefact share the design

- GIVEN the production meta-features are `[pred_lstm, pred_lgb]`
- WHEN `select_beta_grouped` is called for `beta` selection
- THEN `use_cycle_feature` is `False`
- AND the fold-level meta-learners are fitted on two columns

## ADDED

### Requirement: Manifest records the meta-learner width

The capability SHALL record the meta-learner's input width in the artifact manifest, so the
stacking design is verifiable from the manifest alone rather than by unpickling the bundle.

#### Scenario: Width is declared

- GIVEN a saved DS02 bundle
- WHEN `models/ds02_manifest.json` is read
- THEN `model_shape.meta_features` and `inference_contract.meta_features` are both present
- AND they equal `int(ensemble.ridge_meta.n_features_in_)`

#### Scenario: Width matches the artifact

- GIVEN a saved DS02 bundle
- WHEN the bundle is loaded and `ridge_meta.n_features_in_` is read
- THEN it equals the declared `meta_features`
