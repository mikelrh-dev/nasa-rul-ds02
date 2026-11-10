"""Freeze the OOF instrument the shipped band was fitted on, as a versioned npz.

`mia/calibracion_banda.json` was re-frozen on 2026-11-04 (commit `d02ff2d`) from
the bundle-C selection stored in `notebooks/artifacts_c/nb2_selection.joblib`.
That joblib is gitignored, so the band's own evidence was invisible to a clone:
`freeze_rules_evidence.py` could only rebuild a *different* instrument from
`_p1_oof_cache.npz` and reported drift that was never in the JSON.

This script derives the calibration rows once and writes them to
`mia/instrumento_oof.npz`, which is tracked. The derivation is not a freedom:

    oof_calib (52 341 step-1 rows; units 2/5/10/16/18/20)
      -> pure units 2/5/10/18/20                       44 737 rows
      -> every third row per unit, in cycle order       14 915 rows
      -> EMA5 over pred_meta, recomputed on that reduced series
      -> stored as `pred_ema`  (the gate applies PAVA itself)

The order matters and is measured, not assumed. Smoothing the step-1 series and
then subsampling gives bins `[5139, 6145, 3084, 547]` and `q_low` `-4.2639` in
bin 0; the reduction and then the smoothing gives `[5125, 6094, 3135, 561]` and
`-4.3621`, which is what `calibracion_banda.json` records. Only the second
reproduces the frozen band at its committed 4 decimals.

    python scripts/freeze_oof_instrument.py --write   # derive and write the npz
    python scripts/freeze_oof_instrument.py --check   # verify it against the JSON

Exit codes: `0` the band reproduces; `2` usage; `3` input (joblib or npz absent);
`4` the derived band disagrees with `calibracion_banda.json`.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import freeze_rules_evidence as G  # noqa: E402  (same band code the gate runs)

JOBLIB = os.path.join(ROOT, "notebooks", "artifacts_c", "nb2_selection.joblib")
OUT = G.INSTRUMENT
SPAN = 5
STEP = 3

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_INPUT = 3
EXIT_DRIFT = 4


def _reduced_grid(units: np.ndarray, order: int = STEP) -> np.ndarray:
    """Positions of every `order`-th row per unit, in the order given."""
    keep = []
    for unit in np.unique(units):
        idx = np.where(units == unit)[0]
        keep.append(idx[::order])
    return np.sort(np.concatenate(keep))


def _ema_by_unit(values: np.ndarray, units: np.ndarray, span: int = SPAN) -> np.ndarray:
    """Causal EMA over each unit's series, exactly as `stacking` computes it."""
    out = np.empty_like(values)
    for unit in np.unique(units):
        idx = np.where(units == unit)[0]
        out[idx] = pd.Series(values[idx]).ewm(span=span, adjust=False).mean().to_numpy()
    return out


def derive(joblib_path: str = JOBLIB) -> dict:
    """Rebuild the 14 915 calibration rows from the bundle-C selection."""
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

    # Cycle order first: the step-3 grid and the EMA are both order-dependent.
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
    """Fit the band from a frozen instrument, applying the shipped correction."""
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
    """Every recorded field of the band must reproduce at its own precision."""
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
