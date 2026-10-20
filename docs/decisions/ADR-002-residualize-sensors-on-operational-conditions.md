# ADR-002: Residualise the sensors on the flight regime with a degree-2 Ridge

## Status

Accepted

## Date

2026-10-19

## Context

N-CMAPSS DS02 records, for every cycle, 4 operational-condition channels `W = [alt, Mach, TRA, T2]` and 14 physical sensors `Xs = [T24, T30, T48, T50, P15, P2, P21, P24, Ps30, P40, P50, Nf, Nc, Wf]`.

A measured sensor value is the superposition of two physically unrelated processes:

- **(a) Unit-specific, monotone degradation** — the only component correlated with the RUL target.
- **(b) The operating point** — altitude, Mach, throttle and total temperature. These move with pilot manoeuvre and flight profile, are essentially uncorrelated with degradation, and change sign and magnitude within a unit's life.

Iterations 1 to 3 each failed to separate the two, in two opposite directions:

| Iteration | Treatment of `W` | Outcome |
|---|---|---|
| 1 | Ignored entirely | The models could not distinguish "degrading" from "being flown differently"; the tabular branch had no way to normalise the regime. BiLSTM RMSE 6.939, LightGBM 10.82. |
| 2 | Fed to the trees as statistics (`mean, max, min, last, std, diff, ema10` over 18 channels, 126 features) | `max/min/std/diff` over `W` injected pilot-manoeuvre noise straight into the split candidates: the tabular branch's MSE became **3.4x worse** than the BiLSTM's, and every direct linear average was contaminated by it. BiLSTM RMSE 6.874, LightGBM 10.917 (NASA 12155.3). |
| 3 | Pruned to `mean` and `last` of `W` plus 5 descriptors of `Xs` (78 features), LightGBM regularised to `max_depth=4, num_leaves=15` | Recovered partially (LightGBM RMSE 13.349) but never beat the BiLSTM: without the accumulated cycle and without physically decoupling `Xs` from `W`, the trees still could not tell manoeuvre from failure. |

## Decision

**Physically separate the two sources before either model sees the sensors.**

For each of the 14 sensors independently, fit a `Ridge(alpha=1.0)` on `PolynomialFeatures(degree=2, include_bias=False)` of the standardised `W` (4 channels → 14 polynomial terms), and subtract the fitted operating-point component:

```
Xs_residual_raw = Xs_raw - Ridge(Poly2(W_standardised))
```

The 14 residuals are then standardised with their own `StandardScaler` (`res_scaler`). The tabular branch reads **only** these residuals; the recurrent branch receives the globally-scaled 18-channel signal plus the normalised cycle as a 19th channel.

**Why degree 2.** The aerodynamic coupling between `Mach` and `T2` is genuinely nonlinear, and a quadratic basis captures the dominant interaction with only 14 terms derived from 4 inputs. `Ridge(alpha=1.0)` shrinks the quadratic terms, so a unit with little manoeuvre diversity cannot overfit its own residual model.

**Why per-sensor and not multivariate.** The physical model is "each sensor responds to the regime through its own gain". A joint multivariate regression would mix the 14 degradation processes back together and defeat the purpose of the separation.

**Why the residual is standardised separately.** The residuals have far lower variance than the raw sensors. Standardising them keeps the 14 channels on a comparable scale so that neither the `Ridge` meta-learner nor the GBDT splits are dominated by whichever sensor happens to have the largest absolute magnitude.

## Alternatives Considered

### Ignore `W` (iteration 1)
- Pros: no noise from manoeuvres at all.
- Cons: discards exactly the information needed to normalise the sensors away; the models cannot tell a healthy engine flown aggressively from a degraded engine flown gently.
- Rejected: the residualisation needs `W` precisely because `W` is the nuisance variable.

### Feed `W` statistics to the trees (iteration 2)
- Pros: the trees can learn the regime–degradation interaction themselves.
- Cons: measured noise injection; the tabular MSE was 3.4x the BiLSTM's, and the regime descriptors became split candidates that fire on pilot behaviour.
- Rejected: empirically disproved on this dataset.

### Prune `W` to `mean`/`last` only (iteration 3)
- Pros: removes the most volatile descriptors; much better than iteration 2.
- Cons: the trees still see the regime, so they still have to *learn* the separation from 17 450 samples instead of being *given* it; and `mean`/`last` of `W` are themselves manoeuvre-dependent.
- Rejected: an improvement, but strictly dominated by the explicit separation.

### Per-sensor linear regression on `W` (degree 1)
- Pros: fewer parameters, less overfitting risk.
- Cons: cannot represent the `Mach`/`T2` interaction, which is the dominant nonlinearity in the regime block.
- Rejected.

### Multivariate PLS or PCA over `[W, Xs]`
- Pros: a single linear projection; the classic way to remove a nuisance direction.
- Cons: mixes the 14 degradation processes back together and produces components with no physical interpretation, so a later change to the sensor set would silently change the meaning of every component.
- Rejected: it collapses the sources instead of separating them.

### Gradient boosting for the residual model
- Pros: could capture nonlinear regime effects.
- Cons: 4 inputs and 14 targets do not justify a non-linear regressor, and it would reintroduce exactly the overfitting surface that caused iteration 2.
- Rejected.

## Consequences

- The standalone tabular branch improved from **RMSE 13.349** (iteration 3) to **7.087** on the test units, and its NASA score (5768.4) is now directly comparable with the Huber-trained BiLSTM (3822.2) inside the stacking layer.
- Residualisation is a **point estimate**: whatever the linear-in-`W` model cannot explain re-enters the tabular features as noise. That is the price of an explicit, inspectable physical separation.
- The scaler, `poly_w`, the 14 Ridge models and the residual scaler are fit on the **full dev set — all six units — before the unit-16 split** (ADR-005). This step is entirely unsupervised: no RUL label is ever seen, and the test units 11, 14 and 15 are never touched. It therefore does **not** leak onto the test units. It does, however, make the unit-16 validation metrics mildly optimistic, and that is stated explicitly in the technical audit rather than left implicit.
- The residualizer must be re-fit whenever the operating-regime population changes. That is the price of making the model transferable across flight profiles.
- `scaler_w` is persisted in the ensemble but is not referenced by the inference path. It is numerically identical to the `W` block of the global 18-column `scaler` (a `StandardScaler` computes per-column statistics, so both produce the same means and scales), so this is redundancy rather than a defect — but it is a trap for a future maintainer who assumes the inference path uses it.
