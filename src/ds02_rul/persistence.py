"""Artifact persistence: native `.keras` for the graph, `joblib` for the rest.

Two invariants this module enforces:

* the Keras graph is written with `model.save(...)` in the native format and is
  **not** embedded in the joblib payload, so the pickle never carries marshalled
  bytecode;
* every artifact is accompanied by a manifest that records what produced it, so
  a DS02 bundle can never be silently replaced by a differently-shaped one.
"""
from __future__ import annotations

import hashlib
import json
import os

import joblib
import numpy as np

ENSEMBLE_FILE = "ensemble.joblib"
SCALER_FILE = "scaler.joblib"
BILSTM_FILE = "bilstm_ds02.keras"
MANIFEST_FILE = "ds02_manifest.json"

EXPECTED_N_FEATURES = 18
EXPECTED_N_OP = 4


def sha256_of(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_manifest(ensemble, metrics: dict, seed: int, dataset: str = "DS02", **extra) -> dict:
    """Assemble the provenance record for a completed run."""
    import keras
    import lightgbm
    import sklearn
    import tensorflow as tf

    model = ensemble._resolve_model()
    lgb_params = ensemble.lgb_standalone.get_params()
    return {
        "format_version": 1,
        "code_version": extra.pop("code_version", "uncommitted"),
        "dataset": dataset,
        "seed": int(seed),
        "python": extra.pop("python", None),
        "tensorflow": tf.__version__,
        "keras": keras.__version__,
        "sklearn": sklearn.__version__,
        "lightgbm": extra.pop("lightgbm", lightgbm.__version__),
        # The tabular branch's objective is a decision with its own record
        # (ADR-003, and ADR-007 for the rejected median experiment). Read it off
        # the fitted estimator so the shipped bundle can be audited instead of
        # trusted: the label in the notebook is prose, this is the artifact.
        "lgb_objective": {
            "objective": lgb_params.get("objective"),
            "alpha": lgb_params.get("alpha"),
        },
        "unit_partition": extra.pop(
            "unit_partition", {"fit": [2, 5, 10, 18, 20], "holdout": [16], "test": [11, 14, 15]}
        ),
        "model_shape": {
            "scaler_n_features": int(ensemble.scaler.n_features_in_),
            "n_op": int(ensemble.n_op),
            "lgb_n_features": int(ensemble.lgb_standalone.n_features_in_),
            "bilstm_input_shape": [d if d is not None else None for d in model.input_shape],
            "bilstm_params": int(model.count_params()),
            # The meta-learner's width is the whole point of the cycle-ablation
            # revision: 2 columns means [p_lstm, p_lgb], 3 means the clock is back.
            "meta_features": int(ensemble.ridge_meta.n_features_in_),
        },
        # The calibrated prediction band travels with the bundle. The rows that
        # taught the meta-learner are recorded separately as `meta_protocol`,
        # which the notebook passes in.
        "conformal": getattr(ensemble, "conformal", None),
        "inference_contract": {
            "window_size": int(ensemble.window_size),
            "beta": float(ensemble.beta),
            "ema_span": int(ensemble.ema_span),
            "cycle_channel": bool(model.input_shape[-1] == EXPECTED_N_FEATURES + 1),
            "meta_features": int(ensemble.ridge_meta.n_features_in_),
        },
        "scaler_fingerprint_mean_first4": [round(float(v), 4) for v in ensemble.scaler.mean_[:4]],
        "metrics": metrics,
        **extra,
    }


def assert_ds02_artifact(ensemble) -> None:
    """Abort the save if the bundle is not the DS02 shape it claims to be."""
    n_features = int(getattr(ensemble.scaler, "n_features_in_", -1))
    if n_features != EXPECTED_N_FEATURES:
        raise ValueError(
            f"refusing to save: scaler expects {n_features} channels, DS02 requires "
            f"{EXPECTED_N_FEATURES}. An FD001 fallback would have 16."
        )
    if int(ensemble.n_op) != EXPECTED_N_OP:
        raise ValueError(
            f"refusing to save: n_op={ensemble.n_op}, DS02 requires {EXPECTED_N_OP}"
        )


def save_ensemble(ensemble, out_dir: str = ".", manifest: dict | None = None) -> dict:
    """Write the bundle, the scaler and the native Keras model.

    Returns a dict of written paths and their hashes.
    """
    os.makedirs(out_dir, exist_ok=True)
    assert_ds02_artifact(ensemble)

    model = ensemble._resolve_model()
    bilstm_path = os.path.join(out_dir, BILSTM_FILE)
    model.save(bilstm_path)

    scaler_path = os.path.join(out_dir, SCALER_FILE)
    joblib.dump(ensemble.scaler, scaler_path)

    # The graph is referenced by path, never pickled into the bundle.
    detached = _detached_copy(ensemble, bilstm_path)
    ensemble_path = os.path.join(out_dir, ENSEMBLE_FILE)
    joblib.dump(detached, ensemble_path)

    written = {
        "ensemble": ensemble_path,
        "scaler": scaler_path,
        "bilstm": bilstm_path,
        "sha256": {
            "ensemble": sha256_of(ensemble_path),
            "scaler": sha256_of(scaler_path),
            "bilstm": sha256_of(bilstm_path),
        },
    }

    if manifest is not None:
        manifest = dict(manifest)
        manifest["artifacts"] = {
            "ensemble_sha256": written["sha256"]["ensemble"],
            "bilstm_sha256": written["sha256"]["bilstm"],
            "bilstm_bytes": os.path.getsize(bilstm_path),
            "ensemble_bytes": os.path.getsize(ensemble_path),
        }
        manifest_path = os.path.join(out_dir, MANIFEST_FILE)
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        written["manifest"] = manifest_path

    return written


def _detached_copy(ensemble, bilstm_path: str):
    """Clone the ensemble with the Keras model swapped for its path.

    Avoids pickling a live Keras graph (which is what made the legacy artifact
    version-bound) while keeping every fitted estimator.
    """
    from .ensemble import HybridStackingEnsemble

    clone = HybridStackingEnsemble.__new__(HybridStackingEnsemble)
    clone.__dict__.update(ensemble.__dict__)
    clone.bilstm_model = None
    clone.bilstm_path = os.path.abspath(bilstm_path)
    return clone


def load_bilstm(path: str = BILSTM_FILE):
    """Load the native Keras graph, registering the custom pooling layer first.

    Keras resolves a custom layer by name at deserialisation time, so the module
    that defines it must already be imported. Importing `.pooling` here runs its
    `register_keras_serializable` decorator and makes the load order-proof.
    """
    import keras

    from . import pooling  # noqa: F401  (registers LastStepPooling)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"BiLSTM artifact not found at {path!r}. Save it with "
            "ds02_rul.persistence.save_ensemble (writes bilstm_ds02.keras)."
        )
    return keras.models.load_model(path, compile=False)


def load_ensemble(path: str = ENSEMBLE_FILE):
    """Load a bundle and re-attach its native Keras graph."""
    ensemble = joblib.load(path)
    if getattr(ensemble, "bilstm_model", None) is None and getattr(ensemble, "bilstm_path", None):
        candidate = ensemble.bilstm_path
        if not os.path.exists(candidate):
            candidate = os.path.join(os.path.dirname(os.path.abspath(path)), BILSTM_FILE)
        ensemble.bilstm_model = load_bilstm(candidate)
        ensemble.bilstm_path = candidate
    return ensemble


def write_manifest(path: str, manifest: dict) -> None:
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)


def data_fingerprint(arrays: dict) -> str:
    """Stable hash of the ingested shapes plus per-unit boundary rows."""
    digest = hashlib.sha256()
    for key in sorted(arrays):
        value = np.asarray(arrays[key])
        digest.update(key.encode())
        digest.update(str(value.shape).encode())
        digest.update(value[:1].tobytes())
        digest.update(value[-1:].tobytes())
    return digest.hexdigest()
