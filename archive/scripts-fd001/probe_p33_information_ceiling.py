#!/usr/bin/env python3
"""P3.3 — ¿estamos en el techo de información de las features actuales?

Pregunta del informe P0/P1 (§P3.3): el sesgo de vida alta, ¿lo arregla otro
estimador (meta, capacidad) o la representación ya no contiene más?

Instrumento: la **media condicional** `E[y | features]` estimada por k-NN
(k=50) sobre las filas de ajuste del fold, puntuada en las filas retenidas.
Si `RMSE(p_lgb, y)` ya está pegado a `RMSE(E[y|features], y)`, ningún meta ni
ninguna clase de modelo puede mejorar sin features nuevas: el cuello es de
representación. Si el k-NN gana, el estimador actual deja información en la
mesa.

El k-NN es deliberadamente tonto: no extrapola, no aprende sesgo y no puede
codificar el prior del motor 16. Eso lo hace un **techo**, no un candidato.

Las filas se alinean con `_p1_oof_cache.npz`, que se construyó con el mismo
`oof_base_predictions` (3 folds agrupados, semilla 42): rejilla completa de
ventanas de `dev` y cada fila puntuada por el modelo de su fold. La alineación
se comprueba fila a fila contra el caché antes de comparar nada.

Uso:
    .venv/Scripts/python.exe scripts/probe_p33_information_ceiling.py
"""

from __future__ import annotations

import numpy as np

from ds02_rul.data import load_ds02
from ds02_rul.features import build_windows, fit_preprocessing
from ds02_rul.metrics import calculate_nasa_score

WINDOW = 50
STEP = 3
N_SPLITS = 3
SEED = 42
K = 50


def rmse(a, b) -> float:
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(b)) ** 2)))


def conditional_mean(X_tr, y_tr, X_te, k: int = K) -> np.ndarray:
    """Media de los k vecinos de ajuste, en el espacio estandarizado del fold."""
    from sklearn.neighbors import NearestNeighbors

    mu, sd = X_tr.mean(axis=0), X_tr.std(axis=0)
    sd[sd == 0] = 1.0
    z_tr, z_te = (X_tr - mu) / sd, (X_te - mu) / sd
    nn = NearestNeighbors(n_neighbors=min(k, len(z_tr))).fit(z_tr)
    idx = nn.kneighbors(z_te, return_distance=False)
    return y_tr[idx].mean(axis=1)


def main() -> None:
    raw = load_ds02(stride=100)
    A, W, Xs, Y = raw["A_train"], raw["W_train"], raw["Xs_train"], raw["y_train"]
    units_raw, cyc_raw = A[:, 0], A[:, 1]
    unique_units = np.unique(units_raw)

    # Misma partición que oof_base_predictions: shuffle(seed=42) y reparto i::3.
    shuffled = unique_units.copy()
    np.random.RandomState(SEED).shuffle(shuffled)
    unit_folds = [shuffled[i::N_SPLITS] for i in range(N_SPLITS)]
    print("folds:", [[float(u) for u in f] for f in unit_folds])

    knn_all = knn_clock = None
    cover = None
    for fold_id, held in enumerate(unit_folds):
        train_units = np.setdiff1d(unique_units, held)
        mask = np.isin(units_raw, train_units)
        prep = fit_preprocessing(W[mask], Xs[mask])
        dev = build_windows(
            W, Xs, Y, units_raw, cyc_raw, prep,
            window_size=WINDOW, step=STEP, use_cycle=True,
        )
        wu = dev["meta"]["unit"].values
        y = dev["y"].astype(np.float64)
        X = dev["X_tab"].astype(np.float64)  # columna 0 = ciclo/100

        if knn_all is None:
            knn_all = np.full(len(y), np.nan)
            knn_clock = np.full(len(y), np.nan)
            cover = np.zeros(len(y), dtype=int)
            units_ref, y_ref = wu.copy(), y.copy()

        tr, te = np.isin(wu, train_units), np.isin(wu, held)
        knn_all[te] = conditional_mean(X[tr], y[tr], X[te])
        knn_clock[te] = conditional_mean(X[tr][:, 1:], y[tr], X[te][:, 1:])
        cover[te] += 1
        print(f"fold {fold_id}: retenidos {[float(u) for u in held]} | "
              f"ajuste {tr.sum():5d} | puntuados {te.sum():5d}")

    cache = np.load("_p1_oof_cache.npz", allow_pickle=True)
    if len(cache["y"]) != len(knn_all):
        raise SystemExit(f"desalineado: caché {len(cache['y'])} filas, "
                         f"reconstruido {len(knn_all)}")
    if not np.allclose(cache["y"], y_ref) or not np.array_equal(cache["units"], units_ref):
        raise SystemExit("desalineado: las filas del caché no son estas ventanas")
    if not np.all(np.isfinite(knn_all)) or not np.all(cover == 1):
        raise SystemExit(f"folds sin cobertura exacta: min={cover.min()} max={cover.max()}")
    print(f"alineado con el caché: {len(y_ref)} filas, cobertura exacta 1")

    y_all, u_all, p_lgb = cache["y"].astype(np.float64), cache["units"], cache["p_lgb"]
    hi, lo = y_all > 65, y_all <= 62
    arms = {"p_lgb (enviado)": p_lgb, "k-NN E[y|X] (93 col)": knn_all,
            "k-NN sin reloj (92 col)": knn_clock}
    header = (f"{'brazo':26s} {'macro':>7} {'RMSE':>7} {'RMSE>65':>8} {'sesgo>65':>9} "
              f"{'RMSE<=62':>9} {'NASA':>9}")
    print("\n" + header)
    table = {}
    for name, p in arms.items():
        macro = float(np.mean([rmse(p[u_all == u], y_all[u_all == u])
                               for u in np.unique(u_all)]))
        table[name] = dict(macro=macro, rmse=rmse(p, y_all), hi=rmse(p[hi], y_all[hi]),
                           bias=float(np.mean(p[hi] - y_all[hi])),
                           lo=rmse(p[lo], y_all[lo]),
                           nasa=calculate_nasa_score(y_all, p))
        r = table[name]
        print(f"{name:26s} {r['macro']:7.2f} {r['rmse']:7.2f} {r['hi']:8.2f} "
              f"{r['bias']:9.2f} {r['lo']:9.2f} {r['nasa']:9.0f}")

    print(f"\nfilas {len(y_all)} | y>65 {hi.sum()} | motores {sorted(set(u_all.astype(int)))}")
    base = table["p_lgb (enviado)"]
    for name in ("k-NN E[y|X] (93 col)", "k-NN sin reloj (92 col)"):
        r = table[name]
        print(f"{name}: ΔRMSE {r['rmse'] - base['rmse']:+.2f} | "
              f"ΔRMSE>65 {r['hi'] - base['hi']:+.2f} | Δmacro {r['macro'] - base['macro']:+.2f}")
    print("\nLectura: si el k-NN no baja el RMSE, las features ya no contienen la")
    print("información que falta y el sesgo es de representación, no de estimador.")


if __name__ == "__main__":
    main()
