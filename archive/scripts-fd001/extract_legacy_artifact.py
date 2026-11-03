"""Migrate the legacy `ensemble.joblib` (written by Python 3.10) to a portable form.

WHY THIS EXISTS
---------------
The shipped artifact was pickled from a notebook, so it records
`__main__.HybridStackingEnsemble` / `__main__.SensorResidualizer`, and its Keras
graph embeds a bare `Lambda(lambda z: z[:, -1, :])`. `marshal`'s code-object
format is Python-minor-version specific, so the graph cannot be unmarshalled by
3.12. Both defects are documented in docs/02_DS02_ensemble_RUL_spec.md §6.1-6.2.

This script MUST be run with Python 3.10 (the interpreter that wrote the file).
It performs no training: it only reads the fitted objects out and writes them as
plain arrays/JSON so a 3.12 process can rebuild the graph with a serializable
pooling layer and `set_weights(...)`.

Usage (from the repo root):
    C:\\Users\\mikel\\AppData\\Local\\Programs\\Python\\Python310\\python.exe \
        scripts/extract_legacy_artifact.py
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np

OUT_DIR = os.path.join('models', 'legacy')
WEIGHTS_NPZ = os.path.join(OUT_DIR, 'bilstm_weights.npz')
META_JSON = os.path.join(OUT_DIR, 'bilstm_reference.json')
X_FIXED_NPY = os.path.join(OUT_DIR, 'bilstm_x_fixed.npy')
Y_REF_NPY = os.path.join(OUT_DIR, 'bilstm_y_ref.npy')


class _Bootstrap:
    """Placeholder class used to resolve `__main__.X` during unpickling.

    Pickle needs *some* object bound to the recorded name; it instantiates via
    `__new__` and then restores `__dict__`, so an empty class is sufficient.
    """


def main() -> int:
    print(f'python {sys.version.split()[0]}')

    import __main__

    __main__.HybridStackingEnsemble = _Bootstrap
    __main__.SensorResidualizer = _Bootstrap

    import joblib

    if not os.path.exists('ensemble.joblib'):
        print('ERROR: ensemble.joblib not found; run from the repo root')
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)

    ens = joblib.load('ensemble.joblib')
    state = ens.__dict__
    print(f'loaded legacy ensemble; attrs={sorted(state)}')

    model = state['bilstm_model']
    cfg = {
        'python': sys.version.split()[0],
        'window_size': int(state['window_size']),
        'n_op': int(state['n_op']),
        'beta': float(state['beta']),
        'ema_span': int(state['ema_span']),
        'paradigm': state['paradigm'],
        'input_shape': [int(d) if d is not None else None for d in model.input_shape],
        'n_params': int(model.count_params()),
        'layer_names': [layer.__class__.__name__ for layer in model.layers],
        'scaler_n_features': int(state['scaler'].n_features_in_),
        'scaler_mean_first4': [float(v) for v in state['scaler'].mean_[:4]],
        'lgb_n_features': int(state['lgb_standalone'].n_features_in_),
        'lgb_objective': str(state['lgb_standalone'].objective),
        'lgb_alpha': float(state['lgb_standalone'].alpha),
        'n_ridges': len(state['residualizer'].ridges),
    }
    print(json.dumps(cfg, indent=2))

    # --- weights: the Lambda carries none, so order is stable across the rebuild
    weights = model.get_weights()
    np.savez_compressed(WEIGHTS_NPZ, *weights)
    print(f'wrote {len(weights)} arrays -> {WEIGHTS_NPZ}')
    print('shapes:', [a.shape for a in weights])

    # --- a deterministic reference prediction so the 3.12 rebuild can be proven equal
    rs = np.random.RandomState(0)
    x_fixed = rs.randn(4, cfg['window_size'], cfg['input_shape'][2]).astype('float32')
    y_ref = model.predict(x_fixed, verbose=0).ravel()
    np.save(X_FIXED_NPY, x_fixed)
    np.save(Y_REF_NPY, y_ref)
    print(f'reference predictions on fixed input: {y_ref.tolist()}')

    with open(META_JSON, 'w', encoding='utf-8') as fh:
        json.dump(cfg, fh, indent=2)
    print(f'wrote {META_JSON}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
