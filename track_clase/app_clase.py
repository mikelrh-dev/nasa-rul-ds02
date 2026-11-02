"""App de clase DS02 (Fase 3, sin MLflow/n8n).

`streamlit run track_clase/app_clase.py` desde la raíz.

Muestra métricas test del mejor clásico + MLP, predice 1 caso nuevo con el
`Pipeline` guardado y decide con `mia/motor` (R1 seguridad si el formulario
trae vacíos o imposibles). Sin `POST` a n8n (techo PIA 5 = 7 declarado).
"""

from __future__ import annotations

import os
import sys

import pandas as pd
import streamlit as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import joblib  # noqa: E402

from track_clase.pipeline_clase import FEATURE_COLS, NUM_COLS  # noqa: E402
from mia.motor import motor  # noqa: E402
from mia.reglas import REGLAS_DECISION  # noqa: E402

st.set_page_config(page_title="DS02 clase · RUL + decisión", layout="wide")
st.title("DS02 clase · predicción de RUL y decisión")
st.caption(
    "Track de clase sobre filas (sin historia). Producción: híbrido 4.25. "
    "Comparativa de clase: mejor clásico SVM 9.06, mejor MLP E1 7.70."
)


@st.cache_resource(show_spinner=False)
def _cargar():
    pipe = joblib.load(os.path.join(ROOT, "models", "mejor_modelo_clase.joblib"))
    comp = pd.read_csv(os.path.join(ROOT, "resultados", "comparativa.csv"))
    mlp = pd.read_csv(os.path.join(ROOT, "resultados", "mlp_comparativa.csv"))
    return pipe, comp, mlp


pipe, comp, mlp = _cargar()

st.subheader("Métricas en test (uds 11/14/15, 1 sola lectura)")
st.dataframe(comp.sort_values("rmse_test"), use_container_width=True)
st.dataframe(mlp.sort_values("rmse_test"), use_container_width=True)
st.caption(
    "RMSE = coste de fallos gordos; MAE = error medio; R² = varianza explicada. "
    "El clásico ordena el desgaste; sin historia no alcanza al híbrido (4.25)."
)

st.divider()
st.subheader("Caso nuevo: RUL + decisión de reglas")
st.caption("Rellena las 19 numéricas y la fase. Vacíos o imposibles → R1 SIN_DECISIÓN.")

X_tr = pd.read_parquet(os.path.join(ROOT, "data", "processed", "X_train.parquet"))
rangos = {c: (float(X_tr[c].min()), float(X_tr[c].max())) for c in NUM_COLS}

with st.form("caso"):
    cols = st.columns(3)
    vals: dict = {}
    for i, c in enumerate(NUM_COLS):
        lo, hi = rangos[c]
        vals[c] = cols[i % 3].text_input(c, value="", placeholder=f"{lo:.2g} … {hi:.2g}")
    vals["fase_vuelo"] = st.selectbox("fase_vuelo", ["Ascenso", "Crucero", "Descenso"])
    um_apto = st.number_input("Umbral apto (RUL ≥)", value=30.0, step=1.0)
    um_hangar = st.number_input("Umbral hangar (RUL <)", value=25.0, step=1.0)
    enviar = st.form_submit_button("Predecir y decidir", type="primary")

if enviar:
    alertas, caso = [], {}
    for c in NUM_COLS:
        t = str(vals[c]).strip().replace(",", ".")
        try:
            v = float(t)
        except ValueError:
            alertas.append(f"{c}: vacío o no numérico ({vals[c]!r})")
            continue
        lo, hi = rangos[c]
        m = 0.05 * (hi - lo)
        if not (lo - m <= v <= hi + m):
            alertas.append(f"{c}: {v} fuera del dominio DS02 ({lo:.3g}–{hi:.3g})")
        caso[c] = v
    caso["fase_vuelo"] = vals["fase_vuelo"]
    if alertas:
        ficha = {"alertas_datos": alertas, "limite_inferior": -1.0,
                 "umbrales": {"apto": float(um_apto), "hangar": float(um_hangar)}}
        res = motor(ficha, [], list(REGLAS_DECISION))
        st.error("SIN_DECISIÓN (R1 seguridad): " + "; ".join(alertas))
        st.json({"decision": res["decision"], "usadas": res["usadas"], "porque": res["porque"]})
    else:
        import numpy as np  # noqa: E402

        fila = pd.DataFrame([{c: caso[c] for c in FEATURE_COLS}])
        rul = round(float(np.ravel(pipe.predict(fila))[0]), 2)
        ficha = {"rul_punto": rul, "limite_inferior": rul,
                 "umbrales": {"apto": float(um_apto), "hangar": float(um_hangar)}}
        res = motor(ficha, [], list(REGLAS_DECISION))
        st.metric("RUL estimada", f"{rul} ciclos")
        st.success(f"Decisión: {res['decision']}")
        st.json({"regla": res["usadas"], "porque": res["porque"]})
