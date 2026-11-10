#!/usr/bin/env python3
"""¿Cómo de bueno es el modelo enviado? Un informe de precisión, no una métrica.

Cubre lo que un RMSE solo no dice:

1. métricas de regresión, globales y por motor (RMSE, MAE, mediana del error
   absoluto, R², NASA, sesgo);
2. exactitud por tolerancia (±5 / ±10 / ±15 / ±20 ciclos), que es lo que un
   planificador puede usar;
3. matriz de confusión para umbrales de alarma 10..60 y dónde se rompe;
4. la misma matriz sobre ventanas **no solapadas**, para no contar la misma
   información 25 veces;
5. intervalos por bloque bootstrap, que respetan la autocorrelación temporal;
6. calibración por tramo de RUL predicha (¿"30" significa 30?).

Aviso que se imprime y que hay que leer: las ventanas se solapan y salen de
3 motores. El n efectivo es 3, no 6 196; los intervalos de §5 son la única
medida honesta de cuánto puede moverse cada cifra.

Uso:
    .venv/Scripts/python.exe scripts/evaluate_model_quality.py
"""

from __future__ import annotations

import numpy as np

from ds02_rul.data import load_ds02
from ds02_rul.features import build_windows, fit_preprocessing
from ds02_rul.metrics import calculate_nasa_score
from ds02_rul.persistence import load_ensemble

WINDOW = 50
STEP = 2
FIT_UNITS = [2, 5, 10, 18, 20]
NON_OVERLAP_STRIDE = WINDOW // STEP  # 25 ventanas = 50 filas: sin solape
SWEEP = list(range(10, 65, 5))
PRIMARY = 30
BLOCK_CYCLES = 5
BOOT = 2000
SEED = 12345


def regression_metrics(y: np.ndarray, p: np.ndarray) -> dict:
    """Calcula RMSE, MAE y R2 de un par verdad/prediccion."""
    e = p - y
    ae = np.abs(e)
    ss_res = float(np.sum(e ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return dict(
        n=len(y), rmse=float(np.sqrt(np.mean(e ** 2))), mae=float(ae.mean()),
        medae=float(np.median(ae)), p90=float(np.percentile(ae, 90)),
        p95=float(np.percentile(ae, 95)), worst=float(ae.max()),
        r2=1.0 - ss_res / ss_tot, nasa=calculate_nasa_score(y, p),
        bias=float(e.mean()),
    )


def confusion(p: np.ndarray, y: np.ndarray, t: int) -> dict:
    """Matriz de confusion con umbral sobre la clase positiva."""
    a, b = p <= t, y <= t
    tp = int(np.sum(a & b)); fp = int(np.sum(a & ~b))
    fn = int(np.sum(~a & b)); tn = int(np.sum(~a & ~b))
    n = tp + fp + fn + tn
    prec = tp / (tp + fp) if tp + fp else float("nan")
    rec = tp / (tp + fn) if tp + fn else float("nan")
    f1 = 2 * prec * rec / (prec + rec) if (tp + fp) and (tp + fn) else float("nan")
    fpr = fp / (fp + tn) if fp + tn else float("nan")
    spec = tn / (tn + fp) if tn + fp else float("nan")
    denom = np.sqrt(float(tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    mcc = (tp * tn - fp * fn) / denom if denom else float("nan")
    acc = (tp + tn) / n
    po = acc
    pe = (((tp + fp) * (tp + fn)) + ((fn + tn) * (fp + tn))) / (n * n)
    kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, acc=acc, prec=prec, rec=rec, f1=f1,
                fpr=fpr, bal=(rec + spec) / 2, mcc=mcc, kappa=kappa)


def tolerance_accuracy(y: np.ndarray, p: np.ndarray) -> list[dict]:
    """Acierto dentro de una tolerancia en ciclos."""
    ae = np.abs(p - y)
    return [dict(tol=k, share=float(np.mean(ae <= k)),
                 misses=int(np.sum(ae > k))) for k in (5, 10, 15, 20)]


def blocks_by_engine(cyc: np.ndarray, unit: np.ndarray, span: int) -> list[np.ndarray]:
    """Bloques contiguos de `span` ciclos por motor, como índices de fila."""
    out = []
    for u in np.unique(unit):
        m = unit == u
        idx = np.where(m)[0]
        order = idx[np.argsort(cyc[idx])]
        cycles = np.unique(np.round(cyc[order]))
        for start in range(0, len(cycles), span):
            chunk = cycles[start:start + span]
            sel = order[np.isin(np.round(cyc[order]), chunk)]
            if len(sel):
                out.append(sel)
    return out


def bootstrap(y, p, unit, cyc, rng, draws=BOOT) -> dict:
    """Bootstrap por bloques, estratificado por motor: respeta la autocorrelación."""
    blocks = blocks_by_engine(cyc, unit, BLOCK_CYCLES)
    engines = np.unique(unit)
    own = {u: [b for b in blocks if np.isin(unit[b[0]], [u])] for u in engines}
    rmse_s, mae_s, rec_s, prec_s = [], [], [], []
    for _ in range(draws):
        idx = np.concatenate([
            np.concatenate([own[u][j] for j in rng.integers(0, len(own[u]), len(own[u]))])
            for u in engines
        ])
        yb, pb = y[idx], p[idx]
        e = pb - yb
        rmse_s.append(np.sqrt(np.mean(e ** 2)))
        mae_s.append(np.mean(np.abs(e)))
        a, b = pb <= PRIMARY, yb <= PRIMARY
        tp, fp, fn = np.sum(a & b), np.sum(a & ~b), np.sum(~a & b)
        rec_s.append(tp / (tp + fn) if tp + fn else np.nan)
        prec_s.append(tp / (tp + fp) if tp + fp else np.nan)
    q = lambda v: (float(np.nanpercentile(v, 2.5)), float(np.nanpercentile(v, 97.5)))
    return dict(rmse=q(rmse_s), mae=q(mae_s), rec=q(rec_s), prec=q(prec_s),
                blocks=len(blocks))


def main() -> None:
    """Evalua el bundle contra el test y escribe el informe de calidad."""
    raw = load_ds02(stride=100)
    fit_rows = np.isin(raw["A_train"][:, 0], FIT_UNITS)
    prep = fit_preprocessing(raw["W_train"][fit_rows], raw["Xs_train"][fit_rows])
    test = build_windows(raw["W_test"], raw["Xs_test"], raw["y_test"],
                         raw["A_test"][:, 0], raw["A_test"][:, 1], prep,
                         window_size=WINDOW, step=STEP, use_cycle=True)
    ens = load_ensemble("models/ensemble.joblib")
    y = test["y"].astype(np.float64)
    unit = test["meta"]["unit"].values
    cyc = test["meta"]["cycle"].values
    p = ens.predict(test["X_raw"], cyc, unit).astype(np.float64)

    print("=== 0. Qué se está midiendo ===")
    print(f"ventanas {len(y)} | motores {sorted(int(u) for u in np.unique(unit))} | "
          f"ciclos únicos {len(np.unique(cyc))}")
    print(f"RUL real: min {y.min():.0f} | mediana {np.median(y):.0f} | max {y.max():.0f}")
    for u in np.unique(unit):
        m = unit == u
        print(f"  motor {int(u):2d}: {m.sum():4d} ventanas | "
              f"{len(np.unique(cyc[m])):4d} ciclos únicos | RUL {y[m].min():.0f}-{y[m].max():.0f}")

    g = regression_metrics(y, p)
    print("\n=== 1. Regresión, pooled ===")
    print(f"RMSE {g['rmse']:.3f} | MAE {g['mae']:.3f} | mediana AE {g['medae']:.3f} | "
          f"p90 {g['p90']:.2f} | p95 {g['p95']:.2f} | peor {g['worst']:.1f}")
    print(f"R² {g['r2']:.4f} | NASA {g['nasa']:.1f} | sesgo {g['bias']:+.3f}")

    print("\n=== 2. Por motor ===")
    print(f"{'motor':>6} {'n':>5} {'RMSE':>7} {'MAE':>7} {'medAE':>7} {'p95':>7} "
          f"{'sesgo':>7} {'R²':>8} {'NASA':>9}")
    for u in np.unique(unit):
        m = unit == u
        r = regression_metrics(y[m], p[m])
        print(f"{int(u):6d} {r['n']:5d} {r['rmse']:7.2f} {r['mae']:7.2f} "
              f"{r['medae']:7.2f} {r['p95']:7.2f} {r['bias']:+7.2f} {r['r2']:8.3f} "
              f"{r['nasa']:9.0f}")

    print("\n=== 3. Exactitud por tolerancia (qué % de ventanas acierta dentro de ±k) ===")
    for row in tolerance_accuracy(y, p):
        print(f"  ±{row['tol']:2d} ciclos: {100 * row['share']:5.1f} % "
              f"({row['misses']:4d} ventanas fuera)")

    print("\n=== 4. Barrido de umbral de alarma (ventanas solapadas) ===")
    print(f"{'umbral':>7} {'TP':>5} {'FP':>5} {'FN':>5} {'TN':>5} {'acierta':>8} "
          f"{'recall':>7} {'prec':>6} {'F1':>6} {'FPR':>6} {'kappa':>6}")
    for t in SWEEP:
        c = confusion(p, y, t)
        print(f"{t:7d} {c['tp']:5d} {c['fp']:5d} {c['fn']:5d} {c['tn']:5d} "
              f"{100 * c['acc']:7.1f}% {c['rec']:7.2f} {c['prec']:6.2f} {c['f1']:6.2f} "
              f"{c['fpr']:6.2f} {c['kappa']:6.2f}")

    print("\n=== 5. Ventanas NO solapadas (una de cada 25, 50 filas sin solape) ===")
    sub = np.arange(0, len(y), NON_OVERLAP_STRIDE)
    ys, ps, us = y[sub], p[sub], unit[sub]
    r = regression_metrics(ys, ps)
    print(f"n {r['n']} | RMSE {r['rmse']:.2f} | MAE {r['mae']:.2f} | sesgo {r['bias']:+.2f} "
          f"| R² {r['r2']:.3f}")
    for t in (20, 30, 40):
        c = confusion(ps, ys, t)
        print(f"  umbral {t:2d}: TP {c['tp']:3d} FP {c['fp']:3d} FN {c['fn']:3d} TN {c['tn']:3d} "
              f"| acierta {100 * c['acc']:5.1f}% | recall {c['rec']:.2f} | prec {c['prec']:.2f}")

    print("\n=== 6. Intervalos por bloque bootstrap (motor estratificado, bloques de "
          f"{BLOCK_CYCLES} ciclos) ===")
    rng = np.random.default_rng(SEED)
    bs = bootstrap(y, p, unit, cyc, rng)
    print(f"bloques {bs['blocks']} | remuestreos {BOOT}")
    print(f"  RMSE  {g['rmse']:.2f}  IC95 [{bs['rmse'][0]:.2f}, {bs['rmse'][1]:.2f}]")
    print(f"  MAE   {g['mae']:.2f}  IC95 [{bs['mae'][0]:.2f}, {bs['mae'][1]:.2f}]")
    c30 = confusion(p, y, PRIMARY)
    print(f"  recall@{PRIMARY} {c30['rec']:.2f}  IC95 [{bs['rec'][0]:.2f}, {bs['rec'][1]:.2f}]")
    print(f"  prec@{PRIMARY}   {c30['prec']:.2f}  IC95 [{bs['prec'][0]:.2f}, {bs['prec'][1]:.2f}]")

    print("\n=== 7. Calibración: ¿lo que predice es lo que hay? ===")
    bins = [(0, 20), (20, 40), (40, 60), (60, 200)]
    print(f"{'predicho':>10} {'n':>5} {'real medio':>11} {'sesgo':>7} "
          f"{'medAE':>7} {'%|e|>10':>8}")
    for lo, hi in bins:
        m = (p >= lo) & (p < hi)
        if not m.any():
            print(f"{f'{lo}-{hi}':>10} {0:5d} {'-':>11}")
            continue
        e = p[m] - y[m]
        print(f"{f'{lo}-{hi}':>10} {m.sum():5d} {y[m].mean():11.1f} "
              f"{e.mean():+7.2f} {np.median(np.abs(e)):7.2f} "
              f"{100 * np.mean(np.abs(e) > 10):7.1f}%")

    print("\n=== 8. Aviso ===")
    print("6 196 ventanas solapadas de 3 motores: el n efectivo es 3.")
    print("§4 cuenta la misma información decenas de veces; §5 es el subconjunto")
    print("sin solape y §6 el único intervalo honesto de cuánto puede moverse.")


if __name__ == "__main__":
    main()
