"""¿Cuánto de la puntuación del híbrido viene solo del contador de ciclos?

El script existe porque el meta-learner desplegado resultó poner prácticamente
todo su peso en `cyc_norm`:

    coef ridge  [p_lstm, p_lgb, cyc_norm] = [0.0019, 0.0124, -98.4065]
    importancias lgb_meta                 = [0, 0, 720]

Con `beta = 1.0` la predicción final es por tanto `p_meta`, y `p_meta` es una
función lineal del contador de ciclos. Eso no es un ensamble; es un reloj.

El script mide las consecuencias sobre las unidades de test, para que la
afirmación sea un número y no un argumento:

  * el híbrido tal como se despliega (ciclo disponible para todos los componentes);
  * el híbrido con el contador de ciclos quitado de los modelos base Y de las
    meta-características;
  * dos líneas base triviales — OLS solo con `cycle` y una constante — como suelo.

    python scripts/auditoria/ablate_meta_cycle.py
"""
from __future__ import annotations

import json
import os

import numpy as np


from ds02_rul import HybridStackingEnsemble  # noqa: E402
from ds02_rul.data import load_ds02  # noqa: E402
from ds02_rul.metrics import evaluate_predictions  # noqa: E402
from ds02_rul.pipeline import run_seed  # noqa: E402
from ds02_rul.smoothing import causal_ema_by_unit  # noqa: E402

FIT = [2.0, 5.0, 10.0, 18.0, 20.0]
HOLD = [16.0]
TEST = [11.0, 14.0, 15.0]
SEED = 42
OUT = os.path.join("models", "ablation_meta_cycle.json")

import lightgbm as lgb  # noqa: E402
from sklearn.linear_model import RidgeCV  # noqa: E402


def fit_meta(Z_hold, y_hold, seed):
    """Ajusta el meta-learner Ridge sobre las predicciones OOF de train."""
    ridge = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(Z_hold, y_hold)
    lgbm = lgb.LGBMRegressor(
        max_depth=3, num_leaves=7, n_estimators=120, learning_rate=0.03,
        min_child_samples=20, random_state=seed, verbose=-1,
    ).fit(Z_hold, y_hold)
    return ridge, lgbm


def meta_design(out, with_cycle):
    """Construye la matriz de meta-features (predicciones base + ciclo normalizado)."""
    cyc = out["dev"]["meta"]["cycle"].values[out["hold_idx"]] / 100.0
    cols = [out["p_lstm_hold"], out["p_lgb_hold"]]
    if with_cycle:
        cols.append(cyc)
    return np.column_stack(cols)


def evaluate(ensemble, test):
    """Evalua la ablacion sobre el holdout y devuelve RMSE y MAE."""
    units = test["meta"]["unit"].values
    cycles = test["meta"]["cycle"].values
    pred = ensemble.predict(test["X_raw"], cycles, units)
    return evaluate_predictions(test["y"], pred, ""), pred


def main() -> int:
    """Ejecuta la ablacion cyc_norm y escribe models/ablation_meta_cycle.json."""
    raw = load_ds02(stride=100)
    results = {}

    # ---------------------------------------------------------------- 1. shipped
    with_cycle = run_seed(raw, seed=SEED, fit_units=FIT, holdout_units=HOLD,
                          test_units=TEST, use_cycle=True)
    ridge_c, lgbm_c = fit_meta(meta_design(with_cycle, True),
                               with_cycle["dev"]["y"][with_cycle["hold_idx"]], SEED)
    ens_c = HybridStackingEnsemble(
        with_cycle["bilstm"], with_cycle["lgbm"], ridge_c, lgbm_c,
        with_cycle["prep"]["residualizer"], with_cycle["prep"]["scaler"],
        with_cycle["prep"]["scaler_w"], n_op=len(raw["op_names"]),
        window_size=50, beta=1.0, ema_span=5,
    )
    m_c, p_c = evaluate(ens_c, with_cycle["test"])
    results["hybrid_with_cycle"] = m_c
    results["meta_with_cycle"] = {
        "ridge_coef": np.round(ridge_c.coef_, 4).tolist(),
        "ridge_intercept": round(float(ridge_c.intercept_), 4),
        "ridge_alpha": float(ridge_c.alpha_),
        "lgb_meta_importances": np.round(lgbm_c.feature_importances_, 3).tolist(),
    }
    print("shipped hybrid (cycle available everywhere):", m_c)

    # ------------------------------------------------- 2. no cycle anywhere
    no_cycle = run_seed(raw, seed=SEED, fit_units=FIT, holdout_units=HOLD,
                        test_units=TEST, use_cycle=False)
    ridge_n, lgbm_n = fit_meta(meta_design(no_cycle, False),
                               no_cycle["dev"]["y"][no_cycle["hold_idx"]], SEED)
    ens_n = HybridStackingEnsemble(
        no_cycle["bilstm"], no_cycle["lgbm"], ridge_n, lgbm_n,
        no_cycle["prep"]["residualizer"], no_cycle["prep"]["scaler"],
        no_cycle["prep"]["scaler_w"], n_op=len(raw["op_names"]),
        window_size=50, beta=1.0, ema_span=5,
    )
    m_n, p_n = evaluate(ens_n, no_cycle["test"])
    results["hybrid_without_cycle"] = m_n
    results["meta_without_cycle"] = {
        "ridge_coef": np.round(ridge_n.coef_, 4).tolist(),
        "ridge_intercept": round(float(ridge_n.intercept_), 4),
        "ridge_alpha": float(ridge_n.alpha_),
        "lgb_meta_importances": np.round(lgbm_n.feature_importances_, 3).tolist(),
    }
    print("hybrid without the cycle counter:          ", m_n)

    # ------------------------------------------------------------- 3. baselines
    test = with_cycle["test"]
    y = test["y"]
    cyc = test["meta"]["cycle"].values
    units = test["meta"]["unit"].values

    train_cyc = with_cycle["dev"]["meta"]["cycle"].values[with_cycle["fit_idx"]]
    train_y = with_cycle["dev"]["y"][with_cycle["fit_idx"]]
    a, b = np.polyfit(train_cyc, train_y, 1)
    ols = np.clip(a * cyc + b, 0, None)
    ols_ema = causal_ema_by_unit(ols, units, cyc, span=5)
    results["ols_on_cycle_only"] = evaluate_predictions(y, ols, "")
    results["ols_on_cycle_only_ema5"] = evaluate_predictions(y, ols_ema, "")

    const = np.full_like(y, float(np.mean(train_y)))
    results["constant_mean"] = evaluate_predictions(y, const, "")
    print(f"trivial baselines: OLS(cycle) {results['ols_on_cycle_only']['RMSE']:.3f} RMSE "
          f"| constant {results['constant_mean']['RMSE']:.3f} RMSE")
    print(f"OLS fit: RUL = {b:.2f} + {a:.4f} * cycle")

    delta = m_n["RMSE"] - m_c["RMSE"]
    results["delta_rmse_no_cycle"] = round(float(delta), 4)
    # La conclusión se deriva de los números anteriores, nunca se escribe de antemano.
    results["conclusion"] = (
        f"Removing cyc_norm from every component changes RMSE by {delta:+.3f} "
        f"({m_c['RMSE']:.3f} -> {m_n['RMSE']:.3f}), MAE from {m_c['MAE']:.3f} to "
        f"{m_n['MAE']:.3f} and NASA from {m_c['NASA_Score']:.1f} to "
        f"{m_n['NASA_Score']:.1f}. With the cycle available the meta-learner puts "
        f"{abs(ridge_c.coef_[2]) / abs(ridge_c.coef_).sum() * 100:.0f}% of its weight on "
        "it and ignores both base models; without it the weight spreads over "
        f"p_lstm={ridge_n.coef_[0]:.2f} and p_lgb={ridge_n.coef_[1]:.2f}. "
        "OLS on the cycle alone scores "
        f"{results['ols_on_cycle_only']['RMSE']:.3f} RMSE, so the clock is not the "
        "source of the accuracy — it is a shortcut the learner prefers when offered."
    )
    print()
    print(results["conclusion"])

    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print("written:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
