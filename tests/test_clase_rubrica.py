"""PIA-2: los alias con nombres de rúbrica existen, funcionan y no divergen."""

import os

import pytest

import numpy as np
import pandas as pd


def test_src_utils_reexporta_y_documenta():
    import src.utils as U
    from src.clase.pipeline_clase import FEATURE_COLS, make_pipeline
    assert U.FEATURE_COLS == FEATURE_COLS
    assert U.make_pipeline is make_pipeline
    assert U.__doc__ and "rúbrica" in U.__doc__
    assert callable(U.make_pre) and callable(U.predict_caso_nuevo)
    assert callable(U.evaluate_predictions)


def test_streamlit_app_delega_en_dashboard():
    import pathlib
    p = pathlib.Path("app/streamlit_app.py")
    assert p.exists()
    texto = p.read_text(encoding="utf-8")
    assert "dashboard_ds02" in texto  # router fino, sin lógica duplicada


def test_el_campeon_desplegado_es_el_bundle_c():
    """El artefacto que se defiende es C, y su error es menor que el de clase.

    Antes este fichero solo comparaba el alias XGB contra el XGB: pasaba aunque
    el campeón desplegado fuera otro. Ahora fija el bundle C y lo contrasta con
    el mejor modelo de clase leído de su CSV.
    """
    import json
    with open("models/ds02_manifest.json", encoding="utf-8") as fh:
        manifest = json.load(fh)
    assert manifest["code_version"] == "clase-bundle-C"
    assert manifest["seed"] == 42
    assert manifest["metrics"]["reference_row"]["RMSE"] == 4.338

    ruta_mlp = "resultados/mlp_comparativa.csv"
    if not os.path.exists(ruta_mlp):
        pytest.skip("mlp_comparativa.csv no generado: no se puede contrastar con E2")
    e2 = pd.read_csv(ruta_mlp)
    e2 = e2.loc[e2["experimento"] == "E2_reg_lr", "rmse_test"].iloc[0]
    assert manifest["metrics"]["reference_row"]["RMSE"] < float(e2)


def test_tres_campeones_no_se_confunden():
    """SAA-9: el alias es el mejor clásico, E2 el mejor de fila y C el desplegado."""
    import json

    import joblib
    from sklearn.pipeline import Pipeline

    xgb = joblib.load("models/mejor_modelo_clase.joblib")
    alias = joblib.load("models/mejor_modelo.joblib")
    e2 = joblib.load("models/mejor_modelo_clase_E2.joblib")

    assert isinstance(xgb, Pipeline)
    assert type(xgb.steps[-1][1]).__name__ == "XGBRegressor"
    assert type(alias.steps[-1][1]) is type(xgb.steps[-1][1])
    assert type(e2.steps[-1][1]).__name__ == "MLPRegressor"

    with open("models/ds02_manifest.json", encoding="utf-8") as fh:
        manifest = json.load(fh)
    assert manifest["code_version"] == "clase-bundle-C"
    assert manifest["metrics"]["reference_row"]["RMSE"] == 4.338


def test_mejor_modelo_alias_paridad():
    import joblib
    a = joblib.load("models/mejor_modelo_clase.joblib")
    b = joblib.load("models/mejor_modelo.joblib")
    assert type(a.steps[1][1]) is type(b.steps[1][1])
    X = pd.read_parquet("data/processed/X_train.parquet").head(200)
    from src.clase.pipeline_clase import FEATURE_COLS
    np.testing.assert_allclose(a.predict(X[FEATURE_COLS]),
                               b.predict(X[FEATURE_COLS]), rtol=0, atol=0)
