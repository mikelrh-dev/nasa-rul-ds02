# ADR-006: Apply a causal per-unit exponential moving average to the final prediction

## Status

Accepted

## Date

2026-10-19

## Context

RUL is monotonically non-increasing in cycle within a unit. A windowed predictor is not: its output jumps with local sensor noise, and each jump is a fresh opportunity to overshoot. Under the NASA scoring function every overshoot is amplified exponentially, so that discontinuity noise is expensive — a single 20-cycle overshoot costs `exp(2) - 1 ≈ 6.4`, more than thirty perfect predictions.

The correction must be **causal**: the artefact is intended to be usable on a live engine that has not failed yet, so no filter may consume future samples.

## Decision

After stacking and before clipping, smooth the prediction with a per-unit exponential moving average ordered by cycle:

```python
def causal_ema_by_unit(pred, units, cycles, span=5):
    pred = np.asarray(pred, dtype=np.float64)
    out = np.zeros_like(pred)
    for u in np.unique(units):
        idx = np.where(units == u)[0]
        idx = idx[np.argsort(cycles[idx])]
        out[idx] = pd.Series(pred[idx]).ewm(span=span, adjust=False).mean().values
    return out
```

`span = 5`, `adjust=False` — a causal recursion in which each smoothed value depends only on the current and previous predictions of that unit. The smoothed output is then clipped at 0.

The smoother is applied **after** the blend, to the final prediction, so it corrects the output of the whole stack rather than perturbing either base model's learning problem.

## Alternatives Considered

### No smoothing
- Pros: no lag, no assumption about the cycle ordering.
- Cons: measured. The BiLSTM branch improves from RMSE 5.693 / NASA 3822.2 to **5.597 / 3716.8** with the EMA applied; the hybrid reaches 5.522 / 3435.1.
- Rejected.

### A centred moving average or a Savitzky-Golay filter
- Pros: better noise suppression than an EMA for a stationary signal; Savitzky-Golay preserves peaks.
- Cons: centred filters consume **future** samples and are therefore not deployable on a live stream. The whole point of the artefact is a per-cycle RUL for an engine that is still running.
- Rejected on causality.

### A median filter
- Pros: removes isolated spikes without smearing edges.
- Cons: a median filter is not a level estimator. It removes one-off outliers but leaves the step structure that the exponential penalty punishes, and it is not a causal recursion in the same sense.
- Rejected.

### Isotonic regression per unit
- Pros: enforces exact monotonicity, which is the strongest possible version of this idea.
- Cons: it fits the whole series, including future points, so it is not causal and is undefined for a live stream. It is also a global fit, so it cannot be updated incrementally.
- Rejected.

### Smoothing the training targets instead of the predictions
- Pros: the base models would learn to output a smooth signal directly.
- Cons: it changes the learning problem rather than the output, and it would blur exactly the transient thermal events that the max-pooling branch of the BiLSTM is designed to capture.
- Rejected.

### Smoothing the sensor inputs
- Pros: the noise would be removed before the models see it.
- Cons: it adds latency to the inference path and destroys the transient structure the recurrent branch exists to model.
- Rejected.

## Consequences

- The hybrid result improves to **RMSE 5.522 / MAE 4.795 / R² 0.9127 / NASA 3435.1**, strictly better than the BiLSTM alone on RMSE and on the NASA score.
- The smoother is only valid if the cycle index arrives in **strict per-unit order**. The deployable inference entry point must guarantee that, and the `units` argument must become mandatory rather than optional — the current notebook implementation defaults `units=None` to a single pseudo-unit, which silently disables per-unit smoothing for a whole batch. This is carried as production debt.
- `span = 5` was selected empirically. Because an EMA has a lag of roughly `span` cycles, it introduces a small optimistic bias at the start of each unit's life. That is acceptable for RUL, where the first cycles are far from failure, but it would not be acceptable for any metric requiring exact cycle alignment.
- The smoother is applied to the final prediction only. It therefore does not change what the base models learn, and it can be added or removed without retraining — which is what makes it cheap to re-tune.
- A consequence worth stating explicitly: the EMA makes the pipeline's output **dependent on the order in which windows are presented**. Scoring a shuffled batch of windows produces a different result from scoring them in cycle order. Any evaluation harness must therefore sort by `(unit, cycle)` before calling `predict`.
