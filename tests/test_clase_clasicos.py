"""RED test Fase 2.2: 5 clásicos + comparativa auditable (SAA 6/8/9-parcial)."""

import pandas as pd


def test_comparativa_cinco_modelos_con_tiempos():
    comp = pd.read_csv("resultados/comparativa.csv")
    assert set(comp["modelo"]) == {"regresion", "knn", "rf", "xgb", "svm"}
    for col in ["rmse_train", "rmse_test", "mae_test", "r2_test", "tiempo_s", "mejores_params"]:
        assert col in comp.columns, f"falta {col}"
    assert (comp["tiempo_s"] > 0).all()
    assert (comp["rmse_test"] > 0).all()


def test_mejor_modelo_guarda_pipeline_completo():
    import joblib
    pipe = joblib.load("models/mejor_modelo_clase.joblib")
    assert hasattr(pipe, "predict")
    assert pipe.steps[0][0] == "pre" and pipe.steps[1][0] == "reg"
