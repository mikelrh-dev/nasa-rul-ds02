"""P1: mide variantes de la capa meta solo sobre `dev`, sin leer filas de test.

Los modelos base están congelados: sus predicciones de dev se calculan una vez y
se cachean, así que cada variante cambia *solo* en la capa de stacking. El meta
se ajusta siempre sobre las filas de la unidad 16, igual que el protocolo
desplegado.

Advertencia explícita: los motores 2/5/10/18/20 están dentro de muestra para los
modelos base (son las unidades de fit). Es el instrumento correcto para comparar
*capa meta* — el meta nunca vio esas filas y tanto la base como el candidato
reciben las mismas predicciones base — pero no mide cómo generalizan los modelos
base.

Ejecutar:  python scripts/auditoria/p1_meta_support.py [--rebuild-cache]
"""
from __future__ import annotations

import argparse
import os

import numpy as np

from ds02_rul.data import load_ds02
from ds02_rul.metrics import calculate_nasa_score
from ds02_rul.persistence import load_ensemble
from ds02_rul.smoothing import causal_ema_by_unit
from ds02_rul.stacking import MetaSpec, fit_meta, meta_design, predict_meta, select_beta_grouped

CACHE = "_p1_dev_cache.npz"
OOF_CACHE = "_p1_oof_cache.npz"
WINDOW = 50
STEP = 2
HOLDOUT = 16.0


def build_cache():
    """Calcula y guarda el cache P1 de soporte del meta-learner."""
    raw = load_ds02(stride=100)
    ens = load_ensemble("models/ensemble.joblib")
    A, W, Xs, Y = raw["A_train"], raw["W_train"], raw["Xs_train"], raw["y_train"]
    X, y, units, cycles = [], [], [], []
    for unit in np.unique(A[:, 0]):
        m = A[:, 0] == unit
        S = np.hstack([W[m], Xs[m]])
        for i in range(0, len(S) - WINDOW + 1, STEP):
            X.append(S[i : i + WINDOW])
            y.append(float(Y[m][i + WINDOW - 1]))
            cycles.append(float(A[m, 1][i + WINDOW - 1]))
            units.append(float(unit))
    X = np.asarray(X, dtype=np.float32)
    units = np.asarray(units)
    cycles = np.asarray(cycles)
    Xs_scaled = ens.scaler.transform(
        X.reshape(-1, X.shape[2]).astype(np.float64)
    ).reshape(X.shape).astype(np.float32)
    p_lstm = np.asarray(
        ens._resolve_model().predict(
            ens._sequence(Xs_scaled, cycles, ens.bilstm_model.input_shape), verbose=0
        )
    ).ravel()
    p_lgb = np.asarray(ens.lgb_standalone.predict(ens._tabular(Xs_scaled, cycles))).ravel()
    np.savez_compressed(
        CACHE, y=np.asarray(y), units=units, cycles=cycles, p_lstm=p_lstm, p_lgb=p_lgb
    )


def load_cache(rebuild: bool, source: str = "insample"):
    """Carga el cache P1 o devuelve None si no existe."""
    path = OOF_CACHE if source == "oof" else CACHE
    if source == "insample" and (rebuild or not os.path.exists(path)):
        print(f"building {path} (one BiLSTM pass over dev) ...")
        build_cache()
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} missing; run scripts/auditoria/p1_oof_cache.py first")
    d = np.load(path)
    return {k: d[k] for k in ("y", "units", "cycles", "p_lstm", "p_lgb")}


def rmse(a, b):
    """RMSE entre verdad y prediccion."""
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def evaluate(tag, p_meta, d, sel):
    """Evalua el soporte del meta-learner sobre el holdout."""
    y, units, cycles = d["y"][sel], d["units"][sel], d["cycles"][sel]
    ema = causal_ema_by_unit(p_meta, units, cycles, span=5)
    hi, lo = y > 65, y <= 62
    # macro: cada motor pesa igual, para que un motor de vida larga no domine
    # la cifra agrupada (u5 sola concentra el 65 % de las filas dev con y>65).
    macro = float(np.mean([rmse(ema[units == u], y[units == u]) for u in np.unique(units)]))
    return {
        "spec": tag,
        "macro": macro,
        "rmse_raw": rmse(p_meta, y),
        "rmse_ema": rmse(ema, y),
        "rmse_hi": rmse(ema[hi], y[hi]),
        "bias_hi": float(np.mean(ema[hi] - y[hi])),
        "rmse_lo": rmse(ema[lo], y[lo]),
        "bias_lo": float(np.mean(ema[lo] - y[lo])),
        "nasa": calculate_nasa_score(y, ema),
        "per_unit": {
            float(u): (
                rmse(ema[units == u], y[units == u]),
                float(np.mean(ema[(units == u) & hi] - y[(units == u) & hi]))
                if ((units == u) & hi).any()
                else float("nan"),
            )
            for u in np.unique(units)
        },
    }


def main():
    """CLI del experimento P1."""
    ap = argparse.ArgumentParser()
    ap.add_argument("--rebuild-cache", action="store_true")
    ap.add_argument("--preds", choices=("insample", "oof"), default="insample",
                    help="insample = base models applied to their own fit units; "
                         "oof = grouped out-of-fold base predictions (honest gate)")
    args = ap.parse_args()

    d = load_cache(args.rebuild_cache, args.preds)
    print(f"=== instrumento: {args.preds} ===")
    hold = d["units"] == HOLDOUT
    sel = ~hold
    y_hold = d["y"][hold]
    Z_hold = np.column_stack([d["p_lstm"][hold], d["p_lgb"][hold]])

    # tasa de disparo de la puerta de soporte: filas donde el ancla supera el soporte
    anchor = np.maximum(d["p_lstm"][sel], d["p_lgb"][sel])
    print(
        f"dev (5 motores): {sel.sum()} ventanas | soporte del meta = {y_hold.max():.0f} "
        f"| filas con max(p_lstm,p_lgb) > soporte: {(anchor > y_hold.max()).sum()} "
        f"({(anchor > y_hold.max()).mean() * 100:.1f} %)"
    )
    print(f"RUL real > 65: {(d['y'][sel] > 65).sum()} ventanas\n")

    specs = {
        "M0 free 50/50 (enviado)": MetaSpec(),
        "M1 sum_to_one 50/50": MetaSpec(level_mode="sum_to_one"),
        "M2 sum_to_one solo ridge": MetaSpec(level_mode="sum_to_one", blend_lgb=0.0),
        "M3 M1 + gate 2": MetaSpec(level_mode="sum_to_one", support_gate=2.0),
        "M4 M1 + discrepancia": MetaSpec(level_mode="sum_to_one", use_discrepancy=True),
        "M5 free + gate 2": MetaSpec(support_gate=2.0),
        "M6 p_lgb passthrough": None,
        "M7 convex": MetaSpec(level_mode="convex"),
        "M8 convex + gate 2": MetaSpec(level_mode="convex", support_gate=2.0),
    }

    rows = []
    for tag, spec in specs.items():
        if spec is None:
            p = d["p_lgb"][sel]
        else:
            meta = fit_meta(meta_design(d["p_lstm"][hold], d["p_lgb"][hold], spec),
                            y_hold, spec=spec)
            p = predict_meta(meta, d["p_lstm"][sel], d["p_lgb"][sel])
        rows.append(evaluate(tag, p, d, sel))
        if spec is not None:
            coef = np.asarray(meta["ridge"].coef_)
            print(f"{tag:28s} coefs={np.round(coef, 4).tolist()} suma={coef.sum():.3f}")

    print()
    header = (f"{'spec':30s} {'macro':>6} {'RMSE':>6} {'RMSEema':>8} {'RMSE>65':>8} {'bias>65':>8} "
              f"{'RMSE<=62':>9} {'bias<=62':>9} {'NASA':>9}")
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r['spec']:30s} {r['macro']:6.2f} {r['rmse_raw']:6.2f} {r['rmse_ema']:8.2f} "
            f"{r['rmse_hi']:8.2f} {r['bias_hi']:+8.2f} {r['rmse_lo']:9.2f} {r['bias_lo']:+9.2f} "
            f"{r['nasa']:9.1f}"
        )

    print("\nRMSE por motor (bias en y>65 entre paréntesis):")
    units = sorted(rows[0]["per_unit"])
    print(f"{'spec':30s} " + " ".join(f"{int(u):>14d}" for u in units))
    for r in rows:
        cells = " ".join(
            f"{r['per_unit'][u][0]:6.2f} ({r['per_unit'][u][1]:+5.1f})" for u in units
        )
        print(f"{r['spec']:30s} {cells}")

    # ---- reselección de beta bajo la especificación ganadora, con el protocolo OOF agrupado
    print("\nbeta fuera de fold con la nueva especificación del meta:")
    for tag in ("M0 free 50/50 (enviado)", "M1 sum_to_one 50/50", "M7 convex",
                "M8 convex + gate 2"):
        spec = specs[tag]
        res = select_beta_grouped(
            d["units"], d["cycles"], d["y"], d["p_lstm"], d["p_lgb"],
            span=5, use_cycle_feature=False, meta_spec=spec,
        )
        folds = " | ".join(
            f"fold {f['fold']}: {f['scored_units']} beta={f['beta']:.2f} rmse={f['rmse_val']:.2f}"
            for f in res["folds"]
        )
        print(f"  {tag:28s} beta_hat={res['beta']:.2f}  spread={res['spread']}")
        print(f"    {folds}")


if __name__ == "__main__":
    main()
