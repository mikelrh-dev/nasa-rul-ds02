"""Re-package the legacy DS02 artifact into a portable bundle (no training).

Run with **Python 3.10** — the interpreter that wrote the original file. It:

1. loads the legacy `ensemble.joblib` through a `__main__` shim,
2. rebuilds the BiLSTM graph with `LastStepPooling` and transfers the weights,
3. asserts the rebuilt graph predicts identically to the legacy model,
4. wraps the legacy fitted estimators in the module-qualified
   `ds02_rul.HybridStackingEnsemble` and writes the portable bundle
   (`ensemble.joblib` without the graph, `bilstm_ds02.keras`, `scaler.joblib`,
   `ds02_manifest.json`),
5. records reference predictions so a 3.12 process can prove parity.

    python310 scripts/repackage_artifact.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

LEGACY = "ensemble.joblib"
LEGACY_DIR = os.path.join("models", "legacy")
OUT_DIR = "models"
REF_JSON = os.path.join(LEGACY_DIR, "ensemble_reference.json")
X_RAW_NPY = os.path.join(LEGACY_DIR, "ensemble_x_raw.npy")
Y_LSTM_NPY = os.path.join(LEGACY_DIR, "ensemble_y_lstm.npy")
Y_ENS_NPY = os.path.join(LEGACY_DIR, "ensemble_y_ens.npy")


class _Bootstrap:
    """Placeholder so pickle can resolve `__main__.HybridStackingEnsemble`."""


def main() -> int:
    print(f"python {sys.version.split()[0]}")

    import __main__

    __main__.HybridStackingEnsemble = _Bootstrap
    __main__.SensorResidualizer = _Bootstrap

    import keras
    import joblib

    from ds02_rul import HybridStackingEnsemble, SensorResidualizer
    from ds02_rul.model import build_champion_bilstm
    from ds02_rul.persistence import build_manifest, save_ensemble, verify_artifact_sha256

    os.makedirs(LEGACY_DIR, exist_ok=True)
    # SEC-JOBLIB-01: checksum verificado ANTES de deserializar.
    verify_artifact_sha256(LEGACY, "ensemble_sha256")
    legacy = joblib.load(LEGACY)
    state = legacy.__dict__
    n_op = int(state["n_op"])
    window = int(state["window_size"])
    n_channels = int(state["bilstm_model"].input_shape[-1])
    print(f"legacy: n_op={n_op} window={window} channels={n_channels} params={state['bilstm_model'].count_params()}")

    # --- 1. rebuild the graph without the Lambda and transfer weights
    rebuilt = build_champion_bilstm(input_shape=(window, n_channels), dense_units=32, seed=42)
    rebuilt.set_weights(state["bilstm_model"].get_weights())
    print(f"rebuilt: params={rebuilt.count_params()} layers={[l.__class__.__name__ for l in rebuilt.layers]}")
    assert not any(l.__class__.__name__ == "Lambda" for l in rebuilt.layers), "Lambda still present"

    x_fixed = np.load(os.path.join(LEGACY_DIR, "bilstm_x_fixed.npy"))
    y_ref = np.load(os.path.join(LEGACY_DIR, "bilstm_y_ref.npy"))
    y_new = rebuilt.predict(x_fixed, verbose=0).ravel()
    diff = float(np.max(np.abs(y_new - y_ref)))
    print(f"BiLSTM parity vs legacy: {y_new.tolist()} max|diff|={diff:.3e}")
    assert diff < 1e-5, f"weights did not transfer losslessly (max diff {diff})"

    # --- 2. wrap the legacy fitted estimators in the portable class
    # `residualizer` was pickled as `__main__.SensorResidualizer`, so it unpickled
    # as the bootstrap stub; re-wrap its state in the real class.
    legacy_res = state["residualizer"].__dict__
    residualizer = SensorResidualizer(
        legacy_res["poly"], legacy_res["ridges"], legacy_res["res_scaler"]
    )
    print(
        f"residualizer re-wrapped: {len(residualizer.ridges)} ridges, "
        f"poly {residualizer.poly.n_features_in_}->{residualizer.poly.n_output_features_}"
    )

    ensemble = HybridStackingEnsemble(
        bilstm_model=rebuilt,
        lgb_standalone=state["lgb_standalone"],
        ridge_meta=state["ridge_meta"],
        lgb_meta=state["lgb_meta"],
        residualizer=residualizer,
        scaler=state["scaler"],
        scaler_w=state["scaler_w"],
        n_op=n_op,
        window_size=window,
        beta=float(state["beta"]),
        ema_span=int(state["ema_span"]),
    )

    # --- 3. reference predictions through the public predict() contract
    rng = np.random.RandomState(1)
    mean, scale = state["scaler"].mean_, state["scaler"].scale_
    x_raw = (rng.randn(6, window, mean.shape[0]) * scale + mean).astype(np.float32)
    cycles = np.array([10.0, 20.0, 30.0, 12.0, 22.0, 32.0])
    units = np.array([11.0, 11.0, 11.0, 14.0, 14.0, 14.0])
    y_lstm = rebuilt.predict(
        np.concatenate(
            [x_raw, np.repeat((cycles / 100.0).reshape(-1, 1, 1), window, axis=1)], axis=2
        ).astype(np.float32),
        verbose=0,
    ).ravel()
    y_ens = ensemble.predict(x_raw, cycles, units)
    print(f"reference ensemble predictions: {np.round(y_ens, 6).tolist()}")

    np.save(X_RAW_NPY, x_raw)
    np.save(Y_LSTM_NPY, y_lstm)
    np.save(Y_ENS_NPY, y_ens)
    with open(REF_JSON, "w", encoding="utf-8") as fh:
        json.dump(
            {
                "cycles": cycles.tolist(),
                "units": units.tolist(),
                "y_lstm": y_lstm.tolist(),
                "y_ens": y_ens.tolist(),
                "python": sys.version.split()[0],
            },
            fh,
            indent=2,
        )

    # --- 4. persist the portable bundle
    metrics = {"repackage": "legacy_weights_transferred", "max_abs_diff_bilstm": diff}
    manifest = build_manifest(
        ensemble,
        metrics=metrics,
        seed=42,
        dataset="DS02",
        code_version="legacy-repackaged",
        python=sys.version.split()[0],
        provenance={
            "source": "ensemble.joblib written by Python 3.10 notebook",
            "method": "weights extracted and re-attached; no gradient steps",
            "note": "preprocessing still fitted on all six dev units; see Phase 1 retrain",
        },
    )
    written = save_ensemble(ensemble, OUT_DIR, manifest)
    print(json.dumps(written, indent=2))

    # root-level copies keep the documented artifact locations valid
    import shutil

    shutil.copyfile(os.path.join(OUT_DIR, "ensemble.joblib"), "ensemble.joblib")
    shutil.copyfile(os.path.join(OUT_DIR, "scaler.joblib"), "scaler.joblib")
    print("copied ensemble.joblib and scaler.joblib to the repo root")

    # --- 5. keras native round-trip inside this interpreter
    reloaded = keras.models.load_model(os.path.join(OUT_DIR, "bilstm_ds02.keras"), compile=False)
    y_rt = reloaded.predict(x_fixed, verbose=0).ravel()
    rt_diff = float(np.max(np.abs(y_rt - y_ref)))
    print(f".keras round-trip (3.10): max|diff|={rt_diff:.3e} params={reloaded.count_params()}")
    assert rt_diff < 1e-5, "native .keras round-trip changed the predictions"
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
