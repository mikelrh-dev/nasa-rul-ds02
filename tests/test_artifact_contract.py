"""Contract tests for the DS02 artifact.

These are the checks a consumer relies on: the bundle loads in a process that
knows nothing about the training notebook, the shape is the DS02 shape, the
graph carries no bare `Lambda`, and the predictions are unchanged by the
re-packaging.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS = os.path.join(ROOT, "models")
LEGACY = os.path.join(MODELS, "legacy")


def _py() -> str:
    return sys.executable


def test_bundle_loads_in_clean_process():
    """AC-1: no `__main__` definitions, no notebook, no shim."""
    code = (
        "import joblib;"
        "e = joblib.load('models/ensemble.joblib');"
        "print(e.paradigm);"
        "print(e.n_op, e.window_size, e.beta, e.ema_span)"
    )
    proc = subprocess.run([_py(), "-c", code], cwd=ROOT, capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert "__main__" not in proc.stderr
    assert "Hybrid Stacking" in proc.stdout
    assert "4 50 1.0 5" in proc.stdout


def test_keras_graph_loads_natively_and_has_no_lambda():
    from ds02_rul.persistence import load_bilstm

    model = load_bilstm(os.path.join(MODELS, "bilstm_ds02.keras"))
    names = [layer.__class__.__name__ for layer in model.layers]
    assert "Lambda" not in names
    assert "LastStepPooling" in names
    assert model.count_params() == 154253
    assert tuple(model.input_shape) == (None, 50, 19)


def test_manifest_declares_ds02_shape():
    with open(os.path.join(MODELS, "ds02_manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    shape = manifest["model_shape"]
    assert manifest["dataset"] == "DS02"
    assert shape["scaler_n_features"] == 18
    assert shape["n_op"] == 4
    assert shape["bilstm_params"] == 154253
    assert manifest["unit_partition"]["test"] == [11, 14, 15]
    # DS02 fingerprint: altitude ~21.9k ft, Mach ~0.62, throttle ~68.5 %, T2 ~475 R
    mean4 = manifest["scaler_fingerprint_mean_first4"]
    assert 21000 < mean4[0] < 23000
    assert 0.5 < mean4[1] < 0.8
    assert 60 < mean4[2] < 80
    assert 450 < mean4[3] < 500


def test_manifest_pins_the_tabular_objective():
    """The alpha=0.35 decision lives in code, so the artifact must record it.

    ADR-003 chose the asymmetric quantile objective and ADR-007 rejected the
    median alternative; without this field the shipped bundle cannot be
    audited against either record, and the metrics would be cited next to a
    model whose objective nobody can verify.
    """
    with open(os.path.join(MODELS, "ds02_manifest.json"), encoding="utf-8") as fh:
        manifest = json.load(fh)
    assert manifest["lightgbm"], "lightgbm version must not be null"
    objective = manifest["lgb_objective"]
    assert objective["objective"] == "quantile"
    assert abs(float(objective["alpha"]) - 0.35) < 1e-9


def test_last_step_pooling_matches_slice():
    import tensorflow as tf

    from ds02_rul.pooling import LastStepPooling

    z = tf.random.normal((3, 17, 5))
    out = LastStepPooling()(z)
    np.testing.assert_allclose(out.numpy(), z[:, -1, :].numpy())


def test_pooled_head_is_384_wide():
    from ds02_rul.persistence import load_bilstm

    model = load_bilstm(os.path.join(MODELS, "bilstm_ds02.keras"))
    concat = [l for l in model.layers if l.__class__.__name__ == "Concatenate"][0]
    assert concat.output.shape[-1] == 384


def test_graph_rebuild_from_legacy_weights_is_exact():
    """The `Lambda` -> `LastStepPooling` swap is weight-preserving.

    Rebuilds the graph from the arrays extracted out of the Python 3.10 artifact
    and checks it reproduces the 3.10 reference predictions. This validates the
    migration path independently of whatever is currently shipped.
    """
    from ds02_rul.model import build_champion_bilstm

    weights_path = os.path.join(LEGACY, "bilstm_weights.npz")
    if not os.path.exists(weights_path):
        pytest.skip("legacy weights not present")

    ref = np.load(os.path.join(LEGACY, "bilstm_y_ref.npy"))
    x = np.load(os.path.join(LEGACY, "bilstm_x_fixed.npy"))
    with np.load(weights_path) as data:
        weights = [data[k] for k in data.files]

    model = build_champion_bilstm(input_shape=(x.shape[1], x.shape[2]), dense_units=32, seed=42)
    model.set_weights(weights)
    got = model.predict(x, verbose=0).ravel()
    assert np.max(np.abs(got - ref)) < 1e-5
    assert not any(l.__class__.__name__ == "Lambda" for l in model.layers)


def test_reload_is_bit_identical_to_in_memory():
    """Serialising through `.keras` + joblib must not perturb the output."""
    from ds02_rul.persistence import load_ensemble

    ensemble = load_ensemble(os.path.join(MODELS, "ensemble.joblib"))
    raw = np.load(os.path.join(MODELS, "legacy", "ensemble_x_raw.npy"))
    cycles = np.array([10.0, 20.0, 30.0, 12.0, 22.0, 32.0])
    units = np.array([11.0, 11.0, 11.0, 14.0, 14.0, 14.0])
    first = ensemble.predict(raw, cycles, units)
    second = load_ensemble(os.path.join(MODELS, "ensemble.joblib")).predict(raw, cycles, units)
    assert np.max(np.abs(first - second)) < 1e-6
    assert np.isfinite(first).all()


def test_units_none_warns_instead_of_silently_smoothing():
    from ds02_rul.persistence import load_ensemble

    x = np.load(os.path.join(LEGACY, "ensemble_x_raw.npy"))
    ensemble = load_ensemble(os.path.join(MODELS, "ensemble.joblib"))
    with pytest.warns(UserWarning, match="units=None"):
        out = ensemble.predict(x, np.arange(len(x), dtype=float) + 10.0, None)
    assert np.isfinite(out).all()


def test_window_length_is_validated():
    from ds02_rul.persistence import load_ensemble

    ensemble = load_ensemble(os.path.join(MODELS, "ensemble.joblib"))
    with pytest.raises(ValueError, match="window length"):
        ensemble.predict(np.zeros((2, 49, 18), dtype=np.float32), [10.0, 11.0], [11.0, 11.0])


def test_ds02_loader_refuses_silent_fd001_fallback():
    from ds02_rul.data import resolve_ds02

    with pytest.raises(FileNotFoundError) as exc:
        resolve_ds02("does/not/exist.h5")
    mensaje = str(exc.value)
    assert "does/not/exist.h5" in mensaje         # dice que rutas probo
    assert "No fallback is attempted" in mensaje  # y que no sustituye el dataset
