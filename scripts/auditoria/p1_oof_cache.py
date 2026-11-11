"""Build the honest dev gate instrument: grouped out-of-fold base predictions.

`oof_base_predictions` refits the scalers, the polynomial basis, the 14 sensor
ridges and both base models inside each of the 3 grouped folds, so every dev row
is scored by base models that never saw its engine. That is the instrument the
dev gate needs; in-sample base predictions make any meta layer look catastrophic
because the trees have memorised the scored engines.

Writes `_p1_oof_cache.npz` (units, cycles, y, pred_lstm, pred_lgb, folds).

Run:  python scripts/auditoria/p1_oof_cache.py
"""
from __future__ import annotations

import json
import time

import numpy as np

from ds02_rul.data import load_ds02
from ds02_rul.pipeline import oof_base_predictions

OUT = "_p1_oof_cache.npz"


def main():
    """Genera el cache OOF usado por los experimentos P1."""
    raw = load_ds02(stride=100)
    dev_units = np.unique(raw["A_train"][:, 0])
    t0 = time.time()
    oof = oof_base_predictions(
        raw, dev_units, n_splits=3, seed=42, window=50, step_train=3, epochs=15,
        use_cycle=True,
    )
    np.savez_compressed(
        OUT,
        units=oof["units"], cycles=oof["cycles"], y=oof["y"],
        p_lstm=oof["pred_lstm"], p_lgb=oof["pred_lgb"],
    )
    print(json.dumps({
        "seconds": round(time.time() - t0, 1),
        "folds": oof["unit_folds"],
        "timing": oof["timing"],
        "rows": int(len(oof["y"])),
        "nan_free": bool(np.isfinite(oof["pred_lstm"]).all() and np.isfinite(oof["pred_lgb"]).all()),
    }, indent=2))


if __name__ == "__main__":
    main()
