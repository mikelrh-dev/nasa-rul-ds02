"""N-CMAPSS DS02 ingestion.

The previous loader silently fell back to the C-MAPSS FD001 text files when the
HDF5 was missing, then trained and saved an FD001 model to the same
`ensemble.joblib` path with the same `paradigm` string. A 16-feature FD001 model
could therefore replace an 18-feature DS02 one unnoticed. The fallback is gone:
if the HDF5 is not resolvable this raises, and says what it looked for.
"""
from __future__ import annotations

import os

import h5py
import numpy as np
import pandas as pd

DS02_CANDIDATE_PATHS = (
    "archive/CCMaps/N-CMAPSS_DS02-006.h5",
    "N-CMAPSS_DS02-006.h5",
    "archive/N-CMAPSS_DS02-006.h5",
    "../archive/CCMaps/N-CMAPSS_DS02-006.h5",
)

FD001_CANDIDATE_PATHS = (
    "archive/CMaps/train_FD001.txt",
    "train_FD001.txt",
    "archive/train_FD001.txt",
    "../archive/CMaps/train_FD001.txt",
)

DEV_KEYS = ("A_dev", "W_dev", "X_s_dev", "Y_dev")
TEST_KEYS = ("A_test", "W_test", "X_s_test", "Y_test")


def resolve_ds02(path: str | None = None) -> str:
    """Return the first existing DS02 path, or raise a descriptive error."""
    candidates = (path,) if path else DS02_CANDIDATE_PATHS
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(
        "N-CMAPSS DS02 HDF5 not found. Looked for:\n  "
        + "\n  ".join(str(c) for c in candidates)
        + "\nRefusing to fall back to C-MAPSS FD001: that would train a "
        "16-feature model and overwrite the 18-feature DS02 artifact."
    )


def load_ds02(path: str | None = None, stride: int = 100) -> dict:
    """Load and downsample the DS02 dev and test splits.

    Every array is indexed `[::stride]` so unit, cycle, `W`, `Xs` and RUL stay
    row-aligned. No 125-cycle clamp is applied: that clamp belongs to the FD001
    loader only, and importing it here would silently truncate DS02 targets.
    """
    resolved = resolve_ds02(path)
    with h5py.File(resolved, "r") as fh:
        missing = [k for k in DEV_KEYS + TEST_KEYS if k not in fh]
        if missing:
            raise KeyError(f"{resolved} is missing required datasets: {missing}")
        data = {k: fh[k][::stride] for k in DEV_KEYS + TEST_KEYS}
        op_names = [v.decode() if isinstance(v, bytes) else str(v) for v in fh["W_var"]]
        sensor_names = [v.decode() if isinstance(v, bytes) else str(v) for v in fh["X_s_var"]]

    return {
        "path": resolved,
        "stride": stride,
        "op_names": op_names,
        "sensor_names": sensor_names,
        "A_train": data["A_dev"],
        "W_train": data["W_dev"],
        "Xs_train": data["X_s_dev"],
        "y_train": data["Y_dev"].ravel(),
        "A_test": data["A_test"],
        "W_test": data["W_test"],
        "Xs_test": data["X_s_test"],
        "y_test": data["Y_test"].ravel(),
    }


def load_fd001_reference(root: str = "archive/CMaps") -> dict:
    """Load the C-MAPSS FD001 text files as a *separate, explicit* dataset.

    Exposed for the FD001 pipeline only. It is never invoked by the DS02 path
    and never written to the DS02 artifact location.
    """
    cols = ["engine_id", "cycle", "setting1", "setting2", "setting3"] + [f"s{i}" for i in range(1, 22)]
    train = pd.read_csv(f"{root}/train_FD001.txt", sep=r"\s+", header=None, names=cols)
    test = pd.read_csv(f"{root}/test_FD001.txt", sep=r"\s+", header=None, names=cols)
    rul = pd.read_csv(f"{root}/RUL_FD001.txt", sep=r"\s+", header=None, names=["RUL"])

    train["RUL"] = (
        train.groupby("engine_id")["cycle"].transform("max") - train["cycle"]
    ).clip(upper=125)
    rul_map = dict(zip(range(1, len(rul) + 1), rul["RUL"].values))
    true_max = test.groupby("engine_id")["cycle"].transform("max") + test["engine_id"].map(rul_map)
    test["RUL"] = (true_max - test["cycle"]).clip(upper=125)

    return {"train": train, "test": test, "rul": rul, "n_sensors": 21}
