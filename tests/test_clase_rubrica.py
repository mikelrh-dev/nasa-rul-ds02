"""PIA-2: los alias con nombres de rúbrica existen, funcionan y no divergen."""

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


def test_mejor_modelo_alias_paridad():
    import joblib
    a = joblib.load("models/mejor_modelo_clase.joblib")
    b = joblib.load("models/mejor_modelo.joblib")
    assert type(a.steps[1][1]) is type(b.steps[1][1])
    X = pd.read_parquet("data/processed/X_train.parquet").head(200)
    from src.clase.pipeline_clase import FEATURE_COLS
    np.testing.assert_allclose(a.predict(X[FEATURE_COLS]),
                               b.predict(X[FEATURE_COLS]), rtol=0, atol=0)
