"""LEGACY dashboard for the DS02 artifact (superseded by app/dashboard_ds02.py).

Do not run as the challenge: it loads the 2.3 GB HDF5 and Keras at render.
Kept for reference only.

    streamlit run app/dashboard.py

Shows the predicted degradation curve against ground truth for the three test
engines, per-window error, and the artifact manifest.
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import streamlit as st

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ds02_rul.data import load_ds02  # noqa: E402
from ds02_rul.inference import windows_for_unit  # noqa: E402
from ds02_rul.metrics import evaluate_predictions  # noqa: E402
from ds02_rul.persistence import load_ensemble  # noqa: E402
from ds02_rul.smoothing import causal_ema_by_unit  # noqa: E402

ARTIFACT = os.path.join("models", "ensemble.joblib")
MANIFEST = os.path.join("models", "ds02_manifest.json")

st.set_page_config(page_title="DS02 RUL", layout="wide")


@st.cache_resource(show_spinner="Cargando artefacto…")
def get_ensemble():
    return load_ensemble(ARTIFACT)


@st.cache_resource(show_spinner="Cargando N-CMAPSS DS02 (2.3 GB)…")
def get_data():
    return load_ds02(stride=100)


@st.cache_data(show_spinner="Puntuando ventanas…")
def score_unit(unit: float):
    ensemble = get_ensemble()
    raw = get_data()
    X, cycles, units, _ = windows_for_unit(
        raw["W_test"], raw["Xs_test"], raw["A_test"][:, 0], raw["A_test"][:, 1],
        unit, window=ensemble.window_size, step=2,
    )
    pred = ensemble.predict(X, cycles, units)
    return cycles, pred


st.title("N-CMAPSS DS02 — Remaining Useful Life")
st.caption(
    "BiLSTM (triple pooling) + LightGBM cuantílico sobre sensores residualizados "
    "+ meta-learner + EMA causal por motor."
)

if not os.path.exists(ARTIFACT):
    st.error(f"No encuentro `{ARTIFACT}`. Ejecuta el notebook o `scripts/repackage_artifact.py`.")
    st.stop()

ensemble = get_ensemble()
raw = get_data()
available = sorted(float(u) for u in np.unique(raw["A_test"][:, 0]))

with st.sidebar:
    st.header("Artefacto")
    st.write(f"**paradigma**: {ensemble.paradigm}")
    st.write(f"**ventana**: {ensemble.window_size} muestras (STRIDE=100)")
    st.write(f"**beta**: {ensemble.beta:.2f}")
    st.write(f"**EMA span**: {ensemble.ema_span}")
    st.write(f"**features tabulares**: {getattr(ensemble.lgb_standalone, 'n_features_in_', '?')}")
    st.write(f"**n_op**: {ensemble.n_op}")
    unit = st.selectbox("Motor de test", available, index=0)
    st.divider()
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as fh:
            man = json.load(fh)
        st.caption("Manifest")
        st.json(
            {
                "dataset": man.get("dataset"),
                "seed": man.get("seed"),
                "tensorflow": man.get("tensorflow"),
                "sklearn": man.get("sklearn"),
                "partición": man.get("unit_partition"),
                "fingerprint scaler": man.get("scaler_fingerprint_mean_first4"),
            }
        )

cycles, pred = score_unit(unit)
raw_unit = raw["A_test"][:, 0] == unit
true_cycles = raw["A_test"][raw_unit, 1]
true_rul = raw["y_test"][raw_unit]

# ground truth at each window end, to match the prediction grid
truth = pd.DataFrame({"cycle": true_cycles, "rul": true_rul})
truth = truth.set_index("cycle").reindex(cycles)["rul"].values

frame = pd.DataFrame({"cycle": cycles, "RUL_pred": pred, "RUL_real": truth})
frame["error"] = frame.RUL_pred - frame.RUL_real

m = evaluate_predictions(frame.RUL_real.values, frame.RUL_pred.values, f"Motor {int(unit)}")

c1, c2, c3, c4 = st.columns(4)
c1.metric("RMSE", f"{m['RMSE']:.2f}")
c2.metric("MAE", f"{m['MAE']:.2f}")
c3.metric("R²", f"{m['R2']:.4f}")
c4.metric("NASA score (suma)", f"{m['NASA_Score']:.1f}")

st.line_chart(frame.set_index("cycle")[["RUL_real", "RUL_pred"]], height=380)

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Error por ciclo")
    st.bar_chart(frame.set_index("cycle")["error"], height=260)
with col_b:
    st.subheader("Ficha")
    st.write(f"Ventanas puntuadas: **{len(frame)}**")
    st.write(f"RUL inicial predicho: **{frame.RUL_pred.iloc[0]:.1f}**")
    st.write(f"RUL final predicho: **{frame.RUL_pred.iloc[-1]:.1f}**")
    st.write(f"Sesgo medio (pred − real): **{frame.error.mean():+.2f}**")
    st.write("Predicción suavizada causalmente: cada punto depende solo de ciclos anteriores.")

st.divider()
st.caption(
    "El score NASA es una **suma** de exponenciales asimétricas, no una media: "
    "solo es comparable entre modelos evaluados sobre las mismas filas."
)
