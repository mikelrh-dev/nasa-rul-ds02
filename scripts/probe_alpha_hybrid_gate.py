"""Dev gate for the tabular objective, measured at HYBRID level.

`probe_quantile_sweep.py` shows quantile 0.50 beats 0.35 on the tabular branch
alone. That is not enough: the shipped decision surface is
`p_lstm + beta * (p_meta - p_lstm)` with `p_meta` fitted on unit 16, so a better
branch can still produce a worse hybrid through the meta and `beta`.

`alpha` does not touch the BiLSTM, so its out-of-fold predictions are reused from
`_p1_oof_cache.npz` and only the tabular branch is refitted per fold. The
alignment is *verified*, not assumed: the alpha=0.35 refit must reproduce the
cached column exactly, otherwise the comparison would be between different rows.

dev only. No test row is read.

Run:  python scripts/probe_alpha_hybrid_gate.py
"""
from __future__ import annotations

import numpy as np
from lightgbm import LGBMRegressor

from ds02_rul.data import load_ds02
from ds02_rul.features import build_windows, fit_preprocessing
from ds02_rul.metrics import calculate_nasa_score
from ds02_rul.smoothing import causal_ema_by_unit
from ds02_rul.stacking import MetaSpec, fit_meta, meta_design, predict_meta, select_beta_grouped

FOLDS = ((2.0, 10.0), (5.0, 18.0), (16.0, 20.0))
ALPHAS = (0.35, 0.50)


def rmse(a, b):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def lgb(alpha: float) -> LGBMRegressor:
    return LGBMRegressor(
        objective="quantile", alpha=alpha, n_estimators=300, learning_rate=0.02,
        num_leaves=15, max_depth=4, min_child_samples=50, reg_alpha=1.0,
        reg_lambda=5.0, colsample_bytree=0.8, subsample=0.8, verbose=-1,
        random_state=42,
    )


def main():
    cache = np.load("_p1_oof_cache.npz")
    y_c, u_c, c_c, pl_c, pg_c = (
        cache["y"], cache["units"], cache["cycles"], cache["p_lstm"], cache["p_lgb"]
    )

    raw = load_ds02(stride=100)
    A, W, Xs, Y = raw["A_train"], raw["W_train"], raw["Xs_train"], raw["y_train"]
    units_raw, cyc_raw = A[:, 0], A[:, 1]

    # `cycle` is too coarse to identify a window (a cycle spans ~116 rows at
    # stride 100, the window step is 3). Windows are generated per unit in
    # ascending start row, so the ordinal of a window *within its unit* is the
    # stable key - and the alpha=0.35 refit below proves the alignment.
    from collections import defaultdict

    index, counter = {}, defaultdict(int)
    for i, u in enumerate(u_c):
        index[(float(u), counter[float(u)])] = i
        counter[float(u)] += 1
    total = sum(counter.values())
    if total != len(y_c):
        raise SystemExit("ordinal index did not cover the cache")
    seen = defaultdict(int)

    # refit the tabular branch per fold at both alphas; keep the cache order
    rebuilt = {a: np.full(len(y_c), np.nan) for a in ALPHAS}
    for held in FOLDS:
        train_units = np.setdiff1d(np.unique(units_raw), np.asarray(held))
        mask = np.isin(units_raw, train_units)
        prep = fit_preprocessing(W[mask], Xs[mask])
        dev = build_windows(
            W, Xs, Y, units_raw, cyc_raw, prep, window_size=50, step=3, use_cycle=True
        )
        wu = dev["meta"]["unit"].values
        wc = dev["meta"]["cycle"].values
        sel = np.isin(wu, held)
        rows = np.where(sel)[0]
        # same rows as the cache, in the cache's own order
        key = []
        for i in rows:
            u = float(wu[i])
            key.append(index[(u, seen[u])])
            seen[u] += 1
        key = np.array(key)
        tr = ~sel
        for a in ALPHAS:
            model = lgb(a).fit(dev["X_tab"][tr], dev["y"][tr].astype(np.float64))
            rebuilt[a][key] = model.predict(dev["X_tab"][sel])

    assert np.isfinite(rebuilt[0.35]).all(), "rebuilt alpha=0.35 has gaps"
    drift = float(np.max(np.abs(rebuilt[0.35] - pg_c)))
    print(f"alineación: max|p_lgb(0.35) reconstruido - caché| = {drift:.3e}")
    if drift > 1e-6:
        raise SystemExit("alignment check failed: refusing to compare different rows")

    hold = u_c == 16.0
    y_hold = y_c[hold]
    results = {}
    for a in ALPHAS:
        p_lgb = rebuilt[a]
        meta = fit_meta(meta_design(pl_c[hold], p_lgb[hold], MetaSpec()), y_hold, MetaSpec())
        sel_beta = select_beta_grouped(
            u_c, c_c, y_c, pl_c, p_lgb, span=5, use_cycle_feature=False, meta_spec=MetaSpec()
        )
        beta = sel_beta["beta"]
        p_meta = predict_meta(meta, pl_c, p_lgb)
        eval_rows = ~hold
        blend = pl_c + beta * (p_meta - pl_c)
        ema = causal_ema_by_unit(blend[eval_rows], u_c[eval_rows], c_c[eval_rows], span=5)
        yy, uu = y_c[eval_rows], u_c[eval_rows]
        hi, lo = yy > 65, yy <= 62
        results[a] = {
            "beta": beta,
            "rmse": rmse(ema, yy),
            "macro": float(np.mean([rmse(ema[uu == u], yy[uu == u]) for u in np.unique(uu)])),
            "rmse_hi": rmse(ema[hi], yy[hi]),
            "bias_hi": float(np.mean(ema[hi] - yy[hi])),
            "rmse_lo": rmse(ema[lo], yy[lo]),
            "nasa": calculate_nasa_score(yy, ema),
            "folds": [(f["scored_units"], round(f["beta"], 2)) for f in sel_beta["folds"]],
        }

    print(f"\n{'alpha':>6} {'beta':>5} {'macro':>6} {'RMSE':>6} {'RMSE>65':>8} "
          f"{'bias>65':>8} {'RMSE<=62':>9} {'NASA':>9}  folds")
    for a, r in results.items():
        print(
            f"{a:6.2f} {r['beta']:5.2f} {r['macro']:6.2f} {r['rmse']:6.2f} {r['rmse_hi']:8.2f} "
            f"{r['bias_hi']:+8.2f} {r['rmse_lo']:9.2f} {r['nasa']:9.1f}  {r['folds']}"
        )

    base, cand = results[0.35], results[0.50]
    print("\ngate (hibrido, dev OOF):")
    for key, label, lower_is_better in (
        ("rmse", "RMSE global", True), ("macro", "macro", True),
        ("rmse_hi", "RMSE y>65", True), ("rmse_lo", "RMSE y<=62", True),
        ("nasa", "NASA", True),
    ):
        d = cand[key] - base[key]
        ok = (d < 0) if lower_is_better else (d > 0)
        print(f"  {label:12s} {base[key]:8.2f} -> {cand[key]:8.2f}  ({d:+7.2f})  {'PASA' if ok else 'FALLA'}")


if __name__ == "__main__":
    main()
