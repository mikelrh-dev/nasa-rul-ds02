"""RED test Fase 2.3: MLP base + 3 exps + importancia del mejor clásico."""

import pandas as pd


def test_mlp_base_mas_tres_experimentos():
    comp = pd.read_csv("resultados/mlp_comparativa.csv")
    assert set(comp["experimento"]) == {"base", "E1_capacidad", "E2_reg_lr", "E3_batch"}
    for col in ["rmse_test", "mae_test", "r2_test", "tiempo_s", "hipotesis"]:
        assert col in comp.columns, f"falta {col}"


def test_importancia_mejor_clasico_existe():
    import os
    assert os.path.exists("resultados/importancia_permutacion.png")
    imp = pd.read_csv("resultados/importancia_permutacion.csv")
    assert len(imp) >= 10 and "peso" in imp.columns
