"""RED: la tabla final declara el grano y nunca mezcla fila con ventana."""

import pandas as pd


def test_construir_tabla_declara_grano_y_tiempo():
    from src.clase.tabla_final import construir_tabla

    clas = pd.DataFrame([{"modelo": "svm", "rmse_test": 9.0, "mae_test": 8.0,
                          "r2_test": 0.7, "tiempo_s": 1.5}])
    mlp = pd.DataFrame([{"experimento": "E1", "rmse_test": 7.7, "mae_test": 5.5,
                         "r2_test": 0.83, "tiempo_s": 56.0}])
    vent = pd.DataFrame([{"modelo": "lgbm_adaptada", "grano": "ventana",
                          "rmse_test": 7.0, "mae_test": 5.5, "r2_test": 0.85,
                          "nasa_test": 5731.0, "tiempo_s": 0.4, "n_test": 6196}])
    bc = pd.DataFrame([{"Modelo": "Híbrido-C", "RMSE": 4.3, "MAE": 3.2,
                        "R2": 0.94, "NASA_Score": 2340.0, "grano": "ventana"}])
    tab = construir_tabla(clas, mlp, vent, bc)
    assert set(tab["grano"].unique()) <= {"fila", "ventana"}
    assert "tiempo_s" in tab.columns
    assert (tab["grano"] == "fila").sum() == 2
    assert (tab["grano"] == "ventana").sum() == 2
    assert "svm" in tab["modelo"].tolist() and "Híbrido-C" in tab["modelo"].tolist()
