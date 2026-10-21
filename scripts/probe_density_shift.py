#!/usr/bin/env python3
"""¿La densidad de muestreo es una carta de modelado? (dev, sin test)

Motivo: la ventana es de **50 filas**, no de N ciclos. Con la densidad de los
motores de ajuste (114–125 filas/ciclo) esa ventana cubre **~0,43 ciclos**, es
decir media revolución: el BiLSTM no ve una trayectoria de degradación, ve
oscilación dentro de medio ciclo. El motor 14 de test, en cambio, trae **20,6
filas/ciclo** (2,42 ciclos por ventana), 5,5x más laxo que cualquier motor con el
que se ajustó — y es el motor con el 44,6 % del SSE.

Este sondeo mide si eso importa, en `dev` y sin reentrenar: se toma un motor de
ajuste a densidad natural, se diezma hasta la densidad del motor 14 y se predicen
las dos versiones con **el mismo ensemble enviado**. Si el diezmado degrada el
error, la densidad es una causa real y la solución es rejillar por ciclos, no por
filas. Si no lo degrada, la densidad queda descartada como mecanismo y el sesgo
es solo el prior de vida.

Uso:
    .venv/Scripts/python.exe scripts/probe_density_shift.py
"""

from __future__ import annotations

import numpy as np

from ds02_rul.data import load_ds02
from ds02_rul.features import build_windows, fit_preprocessing
from ds02_rul.metrics import calculate_nasa_score
from ds02_rul.persistence import load_ensemble

WINDOW = 50
STEP = 3
FIT_UNITS = [2, 5, 10, 18, 20]
TARGET_DENSITY = 20.6  # filas/ciclo del motor 14
ENGINES = [2, 5, 10]


def rmse(a, b) -> float:
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def thin(raw: dict, engine: int, target_rpc: float) -> dict:
    """Diezma las filas de un motor hasta la densidad objetivo."""
    out = {}
    for key in ("W_train", "Xs_train", "y_train", "A_train"):
        arr = raw[key]
        keep_rows = raw["A_train"][:, 0] == engine
        own = arr[keep_rows]
        life = float(raw["A_train"][keep_rows][:, 1].max())
        rpc = len(own) / life
        stride = max(1, int(round(rpc / target_rpc)))
        out[key] = own[::stride]
    units = out["A_train"][:, 0]
    cyc = out["A_train"][:, 1]
    return dict(W=out["W_train"], Xs=out["Xs_train"], Y=out["y_train"],
                units=units, cyc=cyc, rpc=len(out["A_train"]) / float(cyc.max()))


def score(ens, W, Xs, Y, units, cyc, prep):
    dev = build_windows(W, Xs, Y, units, cyc, prep, window_size=WINDOW, step=STEP,
                        use_cycle=True)
    if len(dev["y"]) == 0:
        return None
    p = ens.predict(dev["X_raw"], dev["meta"]["cycle"].values,
                    dev["meta"]["unit"].values)
    y = dev["y"]
    return dict(n=len(y), rmse=rmse(p, y), bias=float(np.mean(p - y)),
                nasa=calculate_nasa_score(y, p), pred=p, y=y,
                cycles=dev["meta"]["cycle"].values)


def main() -> None:
    raw = load_ds02(stride=100)
    A = raw["A_train"]
    fit_rows = np.isin(A[:, 0], FIT_UNITS)
    prep = fit_preprocessing(raw["W_train"][fit_rows], raw["Xs_train"][fit_rows])
    ens = load_ensemble("models/ensemble.joblib")

    header = (f"{'motor':>6} {'densidad':>10} {'filas/ciclo':>11} {'ventanas':>9} "
              f"{'RMSE':>7} {'sesgo':>7} {'NASA':>10}")
    print(header)
    rows = []
    for engine in ENGINES:
        natural = {}
        for key in ("W_train", "Xs_train", "y_train", "A_train"):
            m = A[:, 0] == engine
            natural[key] = raw[key][m]
        cyc_n = natural["A_train"][:, 1]
        nat = score(ens, natural["W_train"], natural["Xs_train"], natural["y_train"],
                    natural["A_train"][:, 0], cyc_n, prep)
        nat_rpc = len(cyc_n) / float(cyc_n.max())
        print(f"{engine:6d} {'natural':>10} {nat_rpc:11.1f} {nat['n']:9d} "
              f"{nat['rmse']:7.2f} {nat['bias']:+7.2f} {nat['nasa']:10.0f}")

        th = thin(raw, engine, TARGET_DENSITY)
        t = score(ens, th["W"], th["Xs"], th["Y"], th["units"], th["cyc"], prep)
        if t is None:
            print(f"{engine:6d} {'diezmado':>10} {th['rpc']:11.1f}  sin ventanas")
            continue
        print(f"{engine:6d} {'diezmado':>10} {th['rpc']:11.1f} {t['n']:9d} "
              f"{t['rmse']:7.2f} {t['bias']:+7.2f} {t['nasa']:10.0f}")
        rows.append((engine, nat, t))

    print("\nΔ por motor (diezmado - natural):")
    for engine, nat, t in rows:
        print(f"  motor {engine:2d}: ΔRMSE {t['rmse'] - nat['rmse']:+.2f} | "
              f"Δsesgo {t['bias'] - nat['bias']:+.2f}")

    if rows:
        d_rmse = float(np.mean([t["rmse"] - n["rmse"] for _, n, t in rows]))
        print(f"\nmedia ΔRMSE: {d_rmse:+.2f}")
        print("Si el diezmado a la densidad del 14 degrada el error, la ventana de 50")
        print("filas es una representación dependiente de la densidad y el rejillado")
        print("por ciclos es una carta de modelado; si no, la densidad queda descartada.")


if __name__ == "__main__":
    main()
