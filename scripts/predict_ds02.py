"""DS02 inference entry point.

Loads `models/ensemble.joblib` through the importable package — no notebook, no
`__main__` shims, no fallback to FD001.

    python scripts/predict_ds02.py --unit 11 --window 0
    python scripts/predict_ds02.py --unit 11 --all --json
    python scripts/predict_ds02.py --list-units
"""
from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ds02_rul.data import load_ds02  # noqa: E402
from ds02_rul.inference import windows_for_unit  # noqa: E402
from ds02_rul.persistence import load_ensemble  # noqa: E402

DEFAULT_ARTIFACT = os.path.join("models", "ensemble.joblib")


def _predict_unit(unit: float, window_index: int | None, h5: str | None, artifact: str) -> dict:
    ensemble = load_ensemble(artifact)
    raw = load_ds02(h5, stride=100)
    X, cycles, units, _ = windows_for_unit(
        raw["W_test"], raw["Xs_test"], raw["A_test"][:, 0], raw["A_test"][:, 1],
        unit, window=ensemble.window_size, step=2,
    )

    if window_index is None:
        preds = ensemble.predict(X, cycles, units)
        return {
            "unit": float(unit),
            "n_windows": int(len(preds)),
            "rul_final": round(float(preds[-1]), 2),
            "rul_first": round(float(preds[0]), 2),
            "cycles": [float(c) for c in cycles],
            "predictions": [round(float(p), 2) for p in preds],
        }

    if not 0 <= window_index < len(X):
        raise IndexError(f"window index {window_index} out of range (0..{len(X) - 1})")
    pred = float(ensemble.predict(X[window_index : window_index + 1],
                                  cycles[window_index : window_index + 1],
                                  units[window_index : window_index + 1])[0])
    return {
        "unit": float(unit),
        "window": int(window_index),
        "cycle": float(cycles[window_index]),
        "rul": round(pred, 2),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="DS02 RUL inference")
    ap.add_argument("--unit", type=float)
    ap.add_argument("--window", type=int, default=0)
    ap.add_argument("--all", action="store_true", help="score every window of the unit")
    ap.add_argument("--h5", default=None, help="path to N-CMAPSS_DS02-006.h5")
    ap.add_argument("--artifact", default=DEFAULT_ARTIFACT)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--list-units", action="store_true")
    args = ap.parse_args()

    if not os.path.exists(args.artifact):
        print(f"ERROR: artifact not found at {args.artifact}", file=sys.stderr)
        return 2

    if args.list_units:
        raw = load_ds02(args.h5, stride=100)
        print("test units:", sorted(np.unique(raw["A_test"][:, 0]).tolist()))
        return 0

    if args.unit is None:
        ap.error("--unit is required unless --list-units is used")

    try:
        payload = _predict_unit(args.unit, None if args.all else args.window, args.h5, args.artifact)
    except (FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(payload, indent=2))
    elif "predictions" in payload:
        print(f"unit {payload['unit']:.0f}: {payload['n_windows']} windows, "
              f"RUL {payload['rul_first']} -> {payload['rul_final']}")
    else:
        print(f"unit {payload['unit']:.0f} window {payload['window']} "
              f"(cycle {payload['cycle']:.0f}): RUL {payload['rul']} ciclos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
