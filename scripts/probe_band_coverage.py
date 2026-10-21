#!/usr/bin/env python3
"""Cobertura empírica de la banda conformal del bundle enviado.

Cierra el único número del informe de evaluación que no tenía script propio: el
ancho y la cobertura de `predict_interval()` sobre el test. Se mide contra el
artefacto en disco, sin recalibrar nada.

Uso:
    .venv/Scripts/python.exe scripts/probe_band_coverage.py
"""

from __future__ import annotations

import numpy as np

from ds02_rul.conformal import empirical_coverage
from ds02_rul.data import load_ds02
from ds02_rul.features import build_windows, fit_preprocessing
from ds02_rul.persistence import load_ensemble

WINDOW = 50
STEP = 2
FIT_UNITS = [2, 5, 10, 18, 20]


def main() -> None:
    raw = load_ds02(stride=100)
    fit_rows = np.isin(raw["A_train"][:, 0], FIT_UNITS)
    prep = fit_preprocessing(raw["W_train"][fit_rows], raw["Xs_train"][fit_rows])
    test = build_windows(raw["W_test"], raw["Xs_test"], raw["y_test"],
                         raw["A_test"][:, 0], raw["A_test"][:, 1], prep,
                         window_size=WINDOW, step=STEP, use_cycle=True)
    ens = load_ensemble("models/ensemble.joblib")
    y = test["y"]
    unit = test["meta"]["unit"].values
    _, lo, hi = ens.predict_interval(test["X_raw"], test["meta"]["cycle"].values, unit)

    cov = empirical_coverage(y, lo, hi)
    width = hi - lo
    conf = ens.conformal
    print(f"calibración {conf['n_calibration']} ventanas | objetivo "
          f"{conf['target_coverage']:.0%} ({conf['alpha_each_side']:.0%} por lado)")
    print(f"cuantiles globales {conf['global_quantiles']}")
    print(f"\ncobertura {100 * cov:.1f} % | ancho medio {width.mean():.2f} ciclos | "
          f"mín {width.min():.2f} | máx {width.max():.2f}")
    print(f"por debajo {100 * np.mean(y < lo):.1f} % | por encima {100 * np.mean(y > hi):.1f} %")
    print(f"\n{'motor':>6} {'n':>5} {'cobertura':>10} {'ancho':>7}")
    for u in np.unique(unit):
        m = unit == u
        print(f"{int(u):6d} {m.sum():5d} {100 * empirical_coverage(y[m], lo[m], hi[m]):9.1f}% "
              f"{width[m].mean():7.2f}")
    print("\nUna banda honesta sobre-cubre si se calibra con modelos más débiles que el")
    print("enviado; el ancho es un límite superior, no un intervalo de decisión.")


if __name__ == "__main__":
    main()
