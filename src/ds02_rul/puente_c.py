"""Puente del track de clase hacia el bundle C instalado en `models/`.

Los cuadernos 03–05 necesitaban artefactos intermedios que producía el track de
producción (`notebooks/ds02_ensemble/artifacts/`). Ese track ya no está: su
bundle es el C, instalado en `models/`. Este módulo reconstruye lo que los
cuadernos necesitan **sin entrenar nada**:

1. `raw`      — la base adaptada (MAR T30 + ffill con medianas de fit-units).
2. `ens`      — el bundle C congelado (scaler, residualizer, BiLSTM, LGBM, meta).
3. `dev/test` — ventanas con el mismo `window`/`step` del entrenamiento.
4. `result`   — predicciones de cada rama en dev y test, más los índices
                `fit_idx` / `hold_idx` que usaba el protocolo.

Por qué así y no copiando arrays: un notebook que lee `models/ensemble.joblib`
y vuelve a pasarle las ventanas demuestra que el artefacto **se sostiene solo**
(es el mismo camino que usa la app). `load_ensemble` verifica el SHA-256 antes
de deserializar, así que un bundle manipulado no se carga.

Uso típico en un cuaderno:

    from ds02_rul.puente_c import puente_c
    P = puente_c()
    raw, dev, test = P["raw"], P["dev"], P["test"]
    result = P["result"]              # mismas claves que devolvía el NB1 de B
"""

from __future__ import annotations

import os
import sys
from typing import Any

import numpy as np

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))

from ds02_rul.features import build_windows  # noqa: E402
from ds02_rul.persistence import load_ensemble  # noqa: E402
from ds02_rul.data import (  # noqa: E402
    FIT_UNITS,
    HOLDOUT_UNITS,
    TEST_UNITS,
    construir_raw_adaptado,
)
# Re-export: la implementacion vive en mlflow_live (una sola). Los cuadernos
# siguen haciendo `from ds02_rul.puente_c import clean_timing_value`.
from ds02_rul.mlflow_live import clean_timing_value  # noqa: E402,F401

BUNDLE = os.path.join(_ROOT, "models", "ensemble.joblib")
WINDOW = 50
STEP_TRAIN = 3
STEP_TEST = 2



def _prep_del_bundle(ens) -> dict[str, Any]:
    """Objetos de preproceso ajustados que viajan dentro del artefacto."""
    return {
        "scaler": ens.scaler,
        "scaler_w": ens.scaler_w,
        "residualizer": ens.residualizer,
    }


def _predicciones(ens, bloque: dict, etiqueta: str) -> dict:
    """Predicción de cada rama sobre un bloque de ventanas (sin EMA)."""
    p_lstm = np.asarray(ens.bilstm_model.predict(bloque["X_seq"], verbose=0)).ravel()
    p_lgb = np.asarray(ens.lgb_standalone.predict(bloque["X_tab"])).ravel()
    assert len(p_lstm) == len(p_lgb) == len(bloque["y"]), etiqueta
    return {"p_lstm": p_lstm, "p_lgb": p_lgb}


def puente_c(
    bundle: str = BUNDLE,
    window: int = WINDOW,
    step_train: int = STEP_TRAIN,
    step_test: int = STEP_TEST,
) -> dict[str, Any]:
    """Carga el bundle C y reconstruye ventanas de desarrollo y test.

    Devuelve un dict con `raw`, `ens`, `prep`, `dev`, `test`, `result` (mismas
    claves que usaba el cuaderno puente de B), `fit_idx`, `hold_idx` y los
    vectores de unidades/ciclos del holdout.
    """
    raw = construir_raw_adaptado()
    ens = load_ensemble(bundle)
    prep = _prep_del_bundle(ens)

    dev = build_windows(
        raw["W_train"], raw["Xs_train"], raw["y_train"],
        raw["A_train"][:, 0], raw["A_train"][:, 1], prep,
        window_size=window, step=step_train,
    )
    test = build_windows(
        raw["W_test"], raw["Xs_test"], raw["y_test"],
        raw["A_test"][:, 0], raw["A_test"][:, 1], prep,
        window_size=window, step=step_test,
    )

    dev_units = dev["meta"]["unit"].to_numpy()
    hold_idx = np.where(np.isin(dev_units, HOLDOUT_UNITS))[0]
    fit_idx = np.where(np.isin(dev_units, FIT_UNITS))[0]

    p_dev = _predicciones(ens, dev, "dev")
    p_test = _predicciones(ens, test, "test")

    # Las claves imitan a las del NB1 de B para que los cuadernos no cambien de
    # forma. `history` no se puede recuperar de un `.keras` ya entrenado: se deja
    # vacío y los cuadernos lo declaran en vez de inventarlo.
    result = {
        "bilstm": ens.bilstm_model,
        "lgbm": ens.lgb_standalone,
        "prep": prep,
        "dev": dev,
        "test": test,
        "fit_idx": fit_idx,
        "hold_idx": hold_idx,
        "p_lstm_hold": p_dev["p_lstm"][hold_idx],
        "p_lstm_test": p_test["p_lstm"],
        "p_lgb_hold": p_dev["p_lgb"][hold_idx],
        "p_lgb_test": p_test["p_lgb"],
        "t_lgb": float("nan"),
        "t_lstm": float("nan"),
        # Refreshed NaN handling: clean timings for JSON/MLflow consumers.
        # The legacy NaN keys above stay for back-compat; new code must use
        # this dict (all None, never NaN) or clean_timing_value().
        "timing": {"t_lgb_s": None, "t_bilstm_s": None, "tiempo_s": None,
                   "fuente": "bundle_congelado"},
        "timing_measured": False,
        "history": type("H", (), {"history": {}})(),
    }

    return {
        "raw": raw,
        "ens": ens,
        "prep": prep,
        "dev": dev,
        "test": test,
        "result": result,
        "fit_idx": fit_idx,
        "hold_idx": hold_idx,
        "dev_units": dev_units,
        "hold_units": dev["meta"]["unit"].to_numpy()[hold_idx],
        "hold_cycles": dev["meta"]["cycle"].to_numpy()[hold_idx],
        "y_hold": dev["y"][hold_idx],
        "test_units": test["meta"]["unit"].to_numpy(),
        "test_cycles": test["meta"]["cycle"].to_numpy(),
        "particiones": {
            "fit": [int(u) for u in FIT_UNITS],
            "holdout": [int(u) for u in HOLDOUT_UNITS],
            "test": [int(u) for u in TEST_UNITS],
        },
    }
