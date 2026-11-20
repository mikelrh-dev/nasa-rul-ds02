"""Test de la fase 2.2: 5 clásicos y comparativa auditable."""

import pandas as pd


def test_comparativa_cinco_modelos_con_tiempos():
    comp = pd.read_csv("resultados/comparativa.csv")
    assert set(comp["modelo"]) == {"regresion", "knn", "rf", "xgb", "svm"}
    for col in ["rmse_train", "mae_train", "r2_train", "tiempo_s", "mejores_params"]:
        assert col in comp.columns, f"falta {col}"
    assert (comp["tiempo_s"] > 0).all()
    assert (comp["rmse_train"] > 0).all()
    # Nota de contrato: el test solo vive en la fila
    # del elegido; ver test_test_solo_lectura_final_del_elegido.


def test_comparativa_trae_metricas_de_validacion():
    comp = pd.read_csv("resultados/comparativa.csv")
    for col in ["rmse_val", "mae_val", "r2_val"]:
        assert col in comp.columns, f"falta {col} (SAA-8: train y validación)"
    assert comp["rmse_val"].notna().all() and (comp["rmse_val"] > 0).all()
    assert comp["mae_val"].notna().all() and (comp["mae_val"] > 0).all()
    assert comp["r2_val"].notna().all()


def test_test_solo_lectura_final_del_elegido():
    comp = pd.read_csv("resultados/comparativa.csv")
    n = int(comp["rmse_test"].notna().sum())
    assert n == 1, f"test una sola vez: {n} filas con test, debe ser 1"


def test_mejor_modelo_se_elige_por_validacion():
    import joblib
    from src.clase.train_clasicos import ORDEN_SIMPLE
    comp = pd.read_csv("resultados/comparativa.csv")
    clave = {m: (float(comp.loc[comp["modelo"] == m, "rmse_val"].iloc[0]),
                  ORDEN_SIMPLE[m]) for m in comp["modelo"]}
    esperado = sorted(clave, key=lambda m: clave[m])[0]
    pipe = joblib.load("models/mejor_modelo_clase.joblib")
    reg = pipe.steps[1][1]
    mapa = {"Ridge": "regresion", "KNeighborsRegressor": "knn",
            "RandomForestRegressor": "rf", "XGBRegressor": "xgb", "SVR": "svm"}
    assert mapa[type(reg).__name__] == esperado


def test_mejor_modelo_guarda_pipeline_completo():
    import joblib
    pipe = joblib.load("models/mejor_modelo_clase.joblib")
    assert hasattr(pipe, "predict")
    assert pipe.steps[0][0] == "pre" and pipe.steps[1][0] == "reg"
