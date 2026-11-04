"""Evidencia multisemilla del bundle C (seeds 42, 7 y 123).

Dos decisiones que conviene entender antes de leer el CSV:

1. **La semilla 42 no se reentrena por defecto.** El bundle instalado en
   `models/` *es* esa corrida, y su fila vive en `models/ds02_manifest.json`.
   TensorFlow en CPU no es determinista, así que reentrenarla daría otra cifra y
   dejaría el manifiesto (y los cuadernos que lo citan) desalineados. Con
   `--reentrenar-primaria` se fuerza.
2. **Las semillas 7 y 123 sí se entrenan**: son la evidencia de estabilidad que
   el bundle congelado no puede dar por sí solo.

Salida: `resultados/comparativa_c_multisemilla.csv` (una fila por semilla) y un
resumen media ± desviación por consola.

Uso:
    python -m src.clase.evaluar_c_multisemilla
    python -m src.clase.evaluar_c_multisemilla --reentrenar-primaria
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))

SEEDS = (42, 7, 123)
MANIFEST = os.path.join(_ROOT, "models", "ds02_manifest.json")
OUT_CSV = os.path.join(_ROOT, "resultados", "comparativa_c_multisemilla.csv")


def fila_desde_manifest() -> dict:
    """Fila de métricas del bundle instalado (semilla 42), leída de su manifiesto."""
    with open(MANIFEST, encoding="utf-8") as fh:
        fila = json.load(fh)["metrics"]["reference_row"]
    return {
        "seed": int(json.load(open(MANIFEST, encoding="utf-8"))["seed"]),
        "RMSE": float(fila["RMSE"]),
        "MAE": float(fila["MAE"]),
        "R2": float(fila["R2"]),
        "NASA_Score": float(fila["NASA_Score"]),
        "origen": "manifest",
    }


def evaluar_seed(seed: int) -> dict:
    """Entrena y mide una semilla; no escribe artefactos."""
    from src.clase.train_ensemble_adaptado import evaluar_semilla

    r = evaluar_semilla(seed=seed, verbose=False)
    fila = r["rows"][3]
    return {
        "seed": int(seed),
        "RMSE": float(fila["RMSE"]),
        "MAE": float(fila["MAE"]),
        "R2": float(fila["R2"]),
        "NASA_Score": float(fila["NASA_Score"]),
        "origen": "entrenada",
    }


def agregar_semillas(filas: list[dict]) -> dict:
    """Media ± desviación (muestral) de las métricas entre semillas.

    Es una función pura: el test la ejercita con datos sintéticos, sin entrenar.
    """
    if not filas:
        raise ValueError("se necesita al menos una fila para agregar")
    rmse = np.array([f["RMSE"] for f in filas], dtype=float)
    nasa = np.array([f["NASA_Score"] for f in filas], dtype=float)
    ddof = 1 if len(filas) > 1 else 0
    return {
        "n_semillas": len(filas),
        "seeds": [int(f["seed"]) for f in filas],
        "rmse_media": float(rmse.mean()),
        "rmse_std": float(rmse.std(ddof=ddof)),
        "nasa_media": float(nasa.mean()),
        "nasa_std": float(nasa.std(ddof=ddof)),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reentrenar-primaria", action="store_true",
                        help="reentrena también la semilla 42 (rompe la alineación con el manifiesto)")
    args = parser.parse_args(argv)

    filas: list[dict] = []
    for seed in SEEDS:
        if seed == 42 and not args.reentrenar_primaria:
            fila = fila_desde_manifest()
            print(f"seed  42: {fila['RMSE']:.3f} / {fila['NASA_Score']:.1f} (del manifiesto)")
        else:
            fila = evaluar_seed(seed)
            print(f"seed {seed:3d}: {fila['RMSE']:.3f} / {fila['NASA_Score']:.1f} (entrenada)")
        filas.append(fila)

    tabla = pd.DataFrame(filas)
    os.makedirs(os.path.dirname(OUT_CSV), exist_ok=True)
    tabla.to_csv(OUT_CSV, index=False)

    resumen = agregar_semillas(filas)
    print()
    print(tabla.to_string(index=False))
    print()
    print(f"C (semillas {resumen['seeds']}): "
          f"RMSE {resumen['rmse_media']:.3f} ± {resumen['rmse_std']:.3f} | "
          f"NASA {resumen['nasa_media']:.1f} ± {resumen['nasa_std']:.1f}")
    print(f"CSV: {os.path.relpath(OUT_CSV, _ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
