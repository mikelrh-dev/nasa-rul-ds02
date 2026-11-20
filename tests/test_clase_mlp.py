"""RED test Fase 2.3: MLP base + 3 exps + importancia del mejor clásico."""

import pandas as pd


def test_mlp_base_mas_tres_experimentos():
    comp = pd.read_csv("resultados/mlp_comparativa.csv")
    assert set(comp["experimento"]) == {"base", "E1_capacidad", "E2_reg_lr", "E3_batch"}
    for col in ["rmse_train", "mae_train", "r2_train", "tiempo_s", "hipotesis"]:
        assert col in comp.columns, f"falta {col}"
    # Nota de contrato: el test solo vive en el elegido.


def test_mlp_comparativa_trae_validacion():
    comp = pd.read_csv("resultados/mlp_comparativa.csv")
    for col in ["rmse_val", "mae_val", "r2_val"]:
        assert col in comp.columns, f"falta {col} (SAA-8: train y validación)"
    assert comp["rmse_val"].notna().all() and (comp["rmse_val"] > 0).all()
    assert comp["mae_val"].notna().all()
    assert comp["r2_val"].notna().all()


def test_mlp_test_solo_lectura_final_del_elegido():
    comp = pd.read_csv("resultados/mlp_comparativa.csv")
    assert int(comp["rmse_test"].notna().sum()) == 1, "test una sola vez en MLP"


def test_mlp_elegido_por_validacion():
    from src.clase.train_mlp import ORDEN_MLP
    comp = pd.read_csv("resultados/mlp_comparativa.csv")
    clave = {m: (float(comp.loc[comp["experimento"] == m, "rmse_val"].iloc[0]),
                  ORDEN_MLP[m]) for m in comp["experimento"]}
    esperado = sorted(clave, key=lambda m: clave[m])[0]
    con_test = comp.loc[comp["rmse_test"].notna(), "experimento"].tolist()
    assert con_test == [esperado]


def test_importancia_mejor_clasico_existe():
    import os
    assert os.path.exists("resultados/importancia_permutacion.png")
    imp = pd.read_csv("resultados/importancia_permutacion.csv")
    assert len(imp) >= 10 and "peso" in imp.columns
