#!/usr/bin/env python3
"""Matriz de confusión del artefacto enviado, leída como alarma de mantenimiento.

La RUL es una regresión, así que "confusión" exige un umbral de decisión. Aquí el
positivo es **fallo inminente**: `RUL <= umbral`. En mantenimiento:

* falso negativo (FN) — se declara sano y el motor está a menos de `umbral` ciclos
  del fallo: parada no planificada, el lado caro de la penalización NASA.
* falso positivo (FP) — se declara fallo inminente y no lo está: mantenimiento
  innecesario.

Aviso estadístico que se imprime al final: las 6 196 ventanas se solapan (paso 2,
ventana 50) y salen de **3 motores**. La matriz por ventana mide bien la cobertura
temporal, pero su `n` es pseudorreplicación: el tamaño de muestra real es 3. Por
eso se informa también por motor y con tiempo de antelación.

Uso:
    .venv/Scripts/python.exe scripts/probe_alarm_confusion.py
"""

from __future__ import annotations

import numpy as np

from ds02_rul.data import load_ds02
from ds02_rul.features import build_windows, fit_preprocessing
from ds02_rul.persistence import load_ensemble

WINDOW = 50
STEP = 2
FIT_UNITS = [2, 5, 10, 18, 20]
THRESHOLDS = [20, 30, 40, 50]


def matrix(pred_alarm: np.ndarray, true_alarm: np.ndarray) -> dict:
    tp = int(np.sum(pred_alarm & true_alarm))
    fp = int(np.sum(pred_alarm & ~true_alarm))
    fn = int(np.sum(~pred_alarm & true_alarm))
    tn = int(np.sum(~pred_alarm & ~true_alarm))
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else float("nan")
    fpr = fp / (fp + tn) if fp + tn else float("nan")
    spec = tn / (tn + fp) if tn + fp else float("nan")
    denom = np.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = ((tp * tn - fp * fn) / denom) if denom else float("nan")
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, prec=prec, rec=rec, f1=f1, fpr=fpr,
                spec=spec, mcc=mcc, bal=(rec + spec) / 2)


def main() -> None:
    raw = load_ds02(stride=100)
    fit_rows = np.isin(raw["A_train"][:, 0], FIT_UNITS)
    prep = fit_preprocessing(raw["W_train"][fit_rows], raw["Xs_train"][fit_rows])
    test = build_windows(raw["W_test"], raw["Xs_test"], raw["y_test"],
                         raw["A_test"][:, 0], raw["A_test"][:, 1], prep,
                         window_size=WINDOW, step=STEP, use_cycle=True)
    ens = load_ensemble("models/ensemble.joblib")
    y = test["y"].astype(np.float64)
    p = ens.predict(test["X_raw"], test["meta"]["cycle"].values,
                    test["meta"]["unit"].values).astype(np.float64)
    unit = test["meta"]["unit"].values
    cyc = test["meta"]["cycle"].values

    print(f"ventanas {len(y)} | motores {sorted(int(u) for u in np.unique(unit))}")
    print(f"RUL real: min {y.min():.0f} | mediana {np.median(y):.0f} | max {y.max():.0f}")
    print(f"positivos reales por umbral: " +
          " | ".join(f"<={t}: {int((y <= t).sum())}" for t in THRESHOLDS))

    print("\n=== Matriz por ventana ===")
    hdr = (f"{'umbral':>7} {'TP':>5} {'FP':>5} {'FN':>5} {'TN':>6} {'prec':>6} "
           f"{'recall':>7} {'F1':>6} {'FPR':>6} {'balAcc':>7} {'MCC':>6}")
    print(hdr)
    best = {}
    for t in THRESHOLDS:
        m = matrix(p <= t, y <= t)
        best[t] = m
        print(f"{t:7d} {m['tp']:5d} {m['fp']:5d} {m['fn']:5d} {m['tn']:6d} "
              f"{m['prec']:6.2f} {m['rec']:7.2f} {m['f1']:6.2f} {m['fpr']:6.2f} "
              f"{m['bal']:7.2f} {m['mcc']:6.2f}")

    print("\n=== Por motor, umbral 30 ===")
    t = 30
    print(f"{'motor':>6} {'n':>5} {'reales+':>8} {'TP':>4} {'FP':>4} {'FN':>4} "
          f"{'TN':>5} {'recall':>7} {'prec':>6}")
    for u in np.unique(unit):
        m = unit == u  # subconjunto del motor: TN se cuenta solo dentro de él
        r = matrix(p[m] <= t, y[m] <= t)
        print(f"{int(u):6d} {m.sum():5d} {int((y[m] <= t).sum()):8d} {r['tp']:4d} "
              f"{r['fp']:4d} {r['fn']:4d} {r['tn']:5d} {r['rec']:7.2f} {r['prec']:6.2f}")

    print("\n=== Dónde vive el error: sesgo y RMSE por tramo de RUL real ===")
    bands = [(0, 20), (20, 40), (40, 60), (60, 200)]
    print(f"{'motor':>6} " + " ".join(f"{'%d-%d' % b:>16}" for b in bands))
    print(f"{'':>6} " + " ".join(f"{'n   sesgo   RMSE':>16}" for _ in bands))
    for u in np.unique(unit):
        m = unit == u
        cells = []
        for lo, hi in bands:
            b = m & (y >= lo) & (y < hi)
            if b.sum() == 0:
                cells.append(f"{'-':>16}")
                continue
            e = p[b] - y[b]
            cells.append(f"{b.sum():4d} {e.mean():+6.1f} {np.sqrt((e**2).mean()):6.2f}")
        print(f"{int(u):6d} " + " ".join(cells))

    print("\n=== Fracción de ventanas en alarma (umbral 30) ===")
    for u in np.unique(unit):
        m = unit == u
        print(f"  motor {int(u):2d}: real {100 * (y[m] <= t).mean():5.1f} % | "
              f"modelo {100 * (p[m] <= t).mean():5.1f} % | "
              f"ventanas {m.sum():4d}")

    print("\n=== Antelación de la alarma (umbral 30) ===")
    print(f"{'motor':>6} {'cruce real':>11} {'1er aviso':>10} {'antelación':>11} {'veredicto':>12}")
    for u in np.unique(unit):
        m = unit == u
        cyc_u, y_u, p_u = cyc[m], y[m], p[m]
        order = np.argsort(cyc_u)
        cyc_u, y_u, p_u = cyc_u[order], y_u[order], p_u[order]
        true_cross = cyc_u[np.argmax(y_u <= t)] if (y_u <= t).any() else np.nan
        hit = p_u <= t
        model_cross = cyc_u[np.argmax(hit)] if hit.any() else np.nan
        lead = true_cross - model_cross if hit.any() else float("nan")
        verdict = "sin aviso" if not hit.any() else ("tarde" if lead < 0 else "a tiempo")
        print(f"{int(u):6d} {true_cross:11.0f} {model_cross:10.0f} {lead:11.0f} {verdict:>12}")

    print("\n=== Gravedad del fallo cuando falla ===")
    for t in (20, 30, 40):
        fn_mask = (y <= t) & (p > t)
        fp_mask = (y > t) & (p <= t)
        if fn_mask.any():
            err = p[fn_mask] - y[fn_mask]
            print(f"umbral {t}: FN {fn_mask.sum():4d} ventanas | RUL real media "
                  f"{y[fn_mask].mean():5.1f} | predicha {p[fn_mask].mean():5.1f} | "
                  f"error medio {err.mean():+5.1f} | peor {err.max():+5.1f} | "
                  f"FN con error >10: {int((err > 10).sum())}")
        if fp_mask.any():
            print(f"umbral {t}: FP {fp_mask.sum():4d} ventanas | RUL real media "
                  f"{y[fp_mask].mean():5.1f} | predicha {p[fp_mask].mean():5.1f} | "
                  f"error medio {np.mean(p[fp_mask] - y[fp_mask]):+5.1f}")

    print("\nAVISO: 6 196 ventanas de 3 motores, solapadas (paso 2, ventana 50).")
    print("La matriz por ventana mide cobertura temporal, no muestra independiente:")
    print("el n real es 3 motores. Leerla junto a la tabla por motor y la antelación.")


if __name__ == "__main__":
    main()
