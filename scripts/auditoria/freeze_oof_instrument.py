"""Congela como npz versionado el instrumento OOF con el que se ajustó la banda desplegada.

`mia/calibracion_banda.json` se volvió a congelar el 2026-11-04 (commit `d02ff2d`)
a partir de la selección de bundle C guardada en
`notebooks/artifacts_c/nb2_selection.joblib`. Ese joblib está en gitignore, así
que la evidencia de la banda era invisible en un clon:
`freeze_rules_evidence.py` solo podía reconstruir un instrumento *distinto* desde
`_p1_oof_cache.npz` e informaba una deriva que nunca estuvo en el JSON.

Este script deriva una vez las filas de calibración y las escribe en
`mia/instrumento_oof.npz`, que sí está versionado. La derivación no es libre:

    oof_calib (52 341 filas de paso 1; unidades 2/5/10/16/18/20)
      -> unidades puras 2/5/10/18/20                   44 737 filas
      -> una de cada tres filas por unidad, en orden de ciclo   14 915 filas
      -> EMA5 sobre pred_meta, recalculada sobre esa serie reducida
      -> se guarda como `pred_ema`  (la puerta aplica PAVA por su cuenta)

El orden importa y está medido, no supuesto. Suavizar la serie de paso 1 y luego
submuestrear da bins `[5139, 6145, 3084, 547]` y `q_low` `-4.2639` en el bin 0;
reducir y después suavizar da `[5125, 6094, 3135, 561]` y `-4.3621`, que es lo
que registra `calibracion_banda.json`. Solo la segunda reproduce la banda
congelada con sus 4 decimales registrados.

    python scripts/auditoria/freeze_oof_instrument.py --write   # deriva y escribe el npz
    python scripts/auditoria/freeze_oof_instrument.py --check   # lo verifica contra el JSON

Códigos de salida: `0` la banda se reproduce; `2` uso; `3` entrada (falta el
joblib o el npz); `4` la banda derivada no coincide con `calibracion_banda.json`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts", "auditoria"))

import freeze_rules_evidence as G  # noqa: E402  (el mismo código de banda que ejecuta la puerta)

JOBLIB = os.path.join(ROOT, "notebooks", "artifacts_c", "nb2_selection.joblib")
OUT = G.INSTRUMENT
SPAN = 5
STEP = 3

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_INPUT = 3
EXIT_DRIFT = 4


def _reduced_grid(units: np.ndarray, order: int = STEP) -> np.ndarray:
    """Posiciones de cada fila múltiplo de `order` por unidad, en el orden recibido."""
    keep = []
    for unit in np.unique(units):
        idx = np.where(units == unit)[0]
        keep.append(idx[::order])
    return np.sort(np.concatenate(keep))


def _ema_by_unit(values: np.ndarray, units: np.ndarray, span: int = SPAN) -> np.ndarray:
    """EMA causal sobre la serie de cada unidad, igual que la calcula `stacking`."""
    out = np.empty_like(values)
    for unit in np.unique(units):
        idx = np.where(units == unit)[0]
        out[idx] = pd.Series(values[idx]).ewm(span=span, adjust=False).mean().to_numpy()
    return out


def derive(joblib_path: str = JOBLIB) -> dict:
    """Reconstruye las 14 915 filas de calibración desde la selección de bundle C."""
    if not os.path.exists(joblib_path):
        raise G.InputError("missing notebook artifact",
                           f"{joblib_path} (bundle C selection)")
    payload = joblib.load(joblib_path)
    calib = payload.get("oof_calib") if isinstance(payload, dict) else None
    if not isinstance(calib, dict):
        raise G.InputError("incomplete notebook artifact", f"{joblib_path} — no oof_calib")

    for key in ("units", "cycles", "y", "pred_meta"):
        if key not in calib:
            raise G.InputError("incomplete notebook artifact",
                               f"{joblib_path} — oof_calib missing {key}")

    units = np.asarray(calib["units"], dtype=np.float64)
    cycles = np.asarray(calib["cycles"], dtype=np.float64)
    y_true = np.asarray(calib["y"], dtype=np.float64)
    meta = np.asarray(calib["pred_meta"], dtype=np.float64)

    pure = np.isin(units, G.PURE_UNITS)
    if not pure.any():
        raise G.InputError("empty instrument", "no rows in the pure unit mask")

    # Primero el orden de ciclo: tanto la rejilla de paso 3 como la EMA dependen del orden.
    order = np.lexsort((cycles[pure], units[pure]))
    units, cycles = units[pure][order], cycles[pure][order]
    y_true, meta = y_true[pure][order], meta[pure][order]

    grid = _reduced_grid(units)
    units, cycles = units[grid], cycles[grid]
    y_true, meta = y_true[grid], meta[grid]

    if np.isin(16.0, units):
        raise G.InputError("invalid instrument", "unit 16 leaked into the pure mask")

    return {
        "units": units,
        "cycles": cycles,
        "y": y_true,
        "pred_ema": _ema_by_unit(meta, units),
        "beta": np.float64(1.0),
    }


def fit_from(arrays: dict) -> dict:
    """Ajusta la banda desde un instrumento congelado aplicando la corrección desplegada."""
    positions = G._ordered_positions(arrays["units"], arrays["cycles"])
    corrected = G._per_unit(positions, arrays["pred_ema"], G.REGLAS.pava_causal_no_creciente)
    return G.CONFORMAL.fit_conformal(
        arrays["y"], corrected, target=0.90,
        edges=G.CONFORMAL.DEFAULT_EDGES, min_rows=100,
    )


def _committed() -> dict:
    with open(G.CALIBRACION, encoding="utf-8") as fh:
        return json.load(fh)


def compare(fit: dict, committed: dict) -> list[str]:
    """Cada campo registrado de la banda debe reproducirse con su propia precisión."""
    problems = []
    for have, want in zip(committed.get("bins", []), fit["bins"]):
        if have.get("n") != want["n"]:
            problems.append(f"bins[{want['index']}].n: frozen {have.get('n')}, derived {want['n']}")
        for key in ("q_low", "q_high"):
            if float(have.get(key, np.nan)) != float(want[key]):
                problems.append(f"bins[{want['index']}].{key}: "
                                f"frozen {have.get(key)}, derived {want[key]}")
    if committed.get("global_quantiles") != fit["global_quantiles"]:
        problems.append("global_quantiles: frozen "
                        f"{committed.get('global_quantiles')}, derived {fit['global_quantiles']}")
    if committed.get("n_calibration") != fit["n_calibration"]:
        problems.append("n_calibration: frozen "
                        f"{committed.get('n_calibration')}, derived {fit['n_calibration']}")
    return problems


def main(argv=None) -> int:
    """Congela el instrumento OOF versionado en src/mia/instrumento_oof.npz."""
    ap = argparse.ArgumentParser(
        description="Freeze the OOF instrument behind mia/calibracion_banda.json.")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true",
                       help="verify the npz reproduces the frozen band (the default)")
    group.add_argument("--write", action="store_true",
                       help="derive from the joblib and write mia/instrumento_oof.npz")
    group.add_argument("--from-joblib", action="store_true",
                       help="derive only: print the band, write nothing")
    args = ap.parse_args(argv)

    try:
        if args.check:
            if not os.path.exists(OUT):
                raise G.InputError("missing frozen instrument",
                                   f"{OUT} — rebuild it with --write")
            with np.load(OUT) as data:
                arrays = {key: np.asarray(data[key], dtype=np.float64)
                          for key in ("units", "cycles", "y", "pred_ema")}
            source = OUT
        else:
            arrays = derive()
            source = JOBLIB
    except G.InputError as error:
        print("freeze-oof-instrument: cannot continue", file=sys.stderr)
        print(f"  {error.kind}: {error.detail}", file=sys.stderr)
        return EXIT_INPUT

    fit = fit_from(arrays)
    problems = compare(fit, _committed())

    print(f"instrument: {os.path.relpath(source, ROOT)}")
    print(f"rows       : {len(arrays['y'])}")
    print(f"units      : {sorted({int(u) for u in np.unique(arrays['units'])})}")
    print(f"bins       : {[b['n'] for b in fit['bins']]}")
    print(f"global     : {fit['global_quantiles']}")

    if args.write:
        np.savez_compressed(OUT, **arrays)
        print(f"wrote      : {os.path.relpath(OUT, ROOT)}")
    if args.from_joblib and not problems:
        print("band       : reproduces the frozen JSON")

    if problems:
        print("freeze-oof-instrument: the frozen band does not reproduce", file=sys.stderr)
        for problem in problems:
            print(f"  {problem}", file=sys.stderr)
        return EXIT_DRIFT

    print("band       : reproduces mia/calibracion_banda.json")
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
