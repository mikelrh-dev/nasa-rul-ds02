"""Artifact persistence: native `.keras` for the graph, `joblib` for the rest.

Two invariants this module enforces:

* the Keras graph is written with `model.save(...)` in the native format and is
  **not** embedded in the joblib payload, so the pickle never carries marshalled
  bytecode;
* every artifact is accompanied by a manifest that records what produced it, so
  a DS02 bundle can never be silently replaced by a differently-shaped one.
* **never deserialize before verifying**: `load_ensemble` / `load_bilstm`
  compute the SHA-256 of the file and compare it against the manifest
  (`models/ds02_manifest.json` and `app/cache/cache_manifest.json`) *before*
  any `joblib.load` / `keras.models.load_model`. On mismatch they raise
  `RuntimeError` without touching the pickle. No `eval`/`exec` is used.
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

# Repo root: src/ds02_rul/persistence.py -> repo root is three levels up.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MANIFEST_CANDIDATES_DS02 = [
    os.path.join(REPO_ROOT, "models", MANIFEST_FILE),
    os.path.join(REPO_ROOT, "app", "cache", "cache_manifest.json"),
]


def sha256_of(path: str) -> str:
    """SHA-256 hexadecimal de un fichero, leído por bloques de 1 MiB."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_hashes(path: str, key: str) -> tuple[list[str], list[str]]:
    """Collect expected SHA-256 values for `key` from repo/sibling manifests.

    Returns (hashes, manifest_paths_found). No deserialization happens here:
    manifests are plain JSON, read with `json.load` only.
    """
    candidates: list[str] = []
    sibling = os.path.join(os.path.dirname(os.path.abspath(path)), MANIFEST_FILE)
    candidates.append(sibling)
    candidates.extend(_MANIFEST_CANDIDATES_DS02)
    # cache_manifest.json may sit next to the artifact too (app/cache layout).
    sibling_cache = os.path.join(os.path.dirname(os.path.abspath(path)), "cache_manifest.json")
    candidates.append(sibling_cache)

    hashes: list[str] = []
    found: list[str] = []
    seen: set[str] = set()
    for manifest_path in candidates:
        if not os.path.exists(manifest_path) or manifest_path in seen:
            continue
        seen.add(manifest_path)
        try:
            with open(manifest_path, encoding="utf-8") as fh:
                manifest = json.load(fh)
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"refusing to load {path!r}: cannot read manifest {manifest_path!r}: {exc}") from exc
        found.append(manifest_path)
        # ds02_manifest.json stores `artifacts.<key>_sha256`; cache_manifest.json
        # stores `artifact.<key>_sha256`. Accept both layouts.
        for container in (manifest.get("artifacts") or {}, manifest.get("artifact") or {}):
            value = container.get(key)
            if isinstance(value, str) and value:
                hashes.append(value.strip())
    return hashes, found


def verify_artifact_sha256(path: str, key: str) -> str:
    """Verify `path` against the manifest BEFORE any deserialization.

    Raises `RuntimeError` (without deserializing) when no manifest is found or
    when the computed hash does not match *every* expected hash recorded.
    Returns the verified digest.
    """
    hashes, found = _expected_hashes(path, key)
    if not found:
        raise RuntimeError(
            f"refusing to load {path!r}: no manifest found to verify sha256 against "
            f"(looked for {MANIFEST_FILE} and cache_manifest.json in the repo and "
            f"next to the artifact). Refusing to deserialize unverified pickle."
        )
    if not hashes:
        raise RuntimeError(
            f"refusing to load {path!r}: manifest(s) {found} record no `{key}` sha256. "
            "Refusing to deserialize unverified pickle."
        )
    actual = sha256_of(path)
    mismatched = [h for h in hashes if h.lower() != actual.lower()]
    if mismatched:
        raise RuntimeError(
            f"refusing to deserialize {path!r}: sha256 mismatch "
            f"(actual={actual}, expected={hashes}). Artifact was not loaded. "
            f"Verified against manifests: {found}."
        )
    return actual


def resolve_within_repo(path: str, base: str | None = None) -> str:
    """Allowlist: `path` must resolve inside the repo (or `base`).

    Used for externally configured artifact paths (e.g. `DS02_ARTIFACT`) so an
    environment variable cannot point the loader at an arbitrary host file.
    """
    root = os.path.abspath(base or REPO_ROOT)
    candidate = os.path.abspath(path if os.path.isabs(path) else os.path.join(root, path))
    if os.path.commonpath([root]) != os.path.commonpath([root, candidate]):
        raise RuntimeError(
            f"artifact path {path!r} resolves outside the repository root {root!r}; refusing to load."
        )
    return candidate


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
            f"{EXPECTED_N_FEATURES}. A wrong-paradigm artifact would have 16."
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
    # SHA-256 verified BEFORE any deserialization: refuse tampered graphs.
    verify_artifact_sha256(path, "bilstm_sha256")
    return keras.models.load_model(path, compile=False)


def load_ensemble(path: str = ENSEMBLE_FILE):
    """Load a bundle and re-attach its native Keras graph.

    Security (P1): the SHA-256 of `path` is verified against
    `models/ds02_manifest.json` and `app/cache/cache_manifest.json`
    (plus a sibling manifest next to the artifact) **before** `joblib.load`.
    On mismatch `RuntimeError` is raised and the pickle is never
    deserialized. No `eval`/`exec` is used. This check is what
    `app/ui_inference.get_ensemble` and `app/api.py` rely on — they both
    go through this function.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"ensemble artifact not found at {path!r}")
    verify_artifact_sha256(path, "ensemble_sha256")
    ensemble = joblib.load(path)
    if getattr(ensemble, "bilstm_model", None) is None and getattr(ensemble, "bilstm_path", None):
        candidate = ensemble.bilstm_path
        if not os.path.exists(candidate):
            candidate = os.path.join(os.path.dirname(os.path.abspath(path)), BILSTM_FILE)
        ensemble.bilstm_model = load_bilstm(candidate)
        ensemble.bilstm_path = candidate
    return ensemble


def write_manifest(path: str, manifest: dict) -> None:
    """Guarda un manifiesto JSON con indentación estable."""
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
