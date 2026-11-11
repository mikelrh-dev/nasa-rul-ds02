"""RED test Fase 6 (NB05/bundle C): parquet adaptado -> raw honesto.

El bundle C se entrena con las mismas funciones del pipeline congelado
(`run_seed`, `oof_base_predictions`), que consumen un dict raw. Este test
fija el contrato del adaptador `construir_raw_adaptado`: arrays alineados,
sin NaN (MAR ya imputado con medianas de fit-units), particiones congeladas
y RUL saneado. Sin este adaptador no hay bundle C comparable con B.
"""

import numpy as np


def test_raw_adaptado_alineado_sin_nulos():
    from ds02_rul.data import construir_raw_adaptado
    raw = construir_raw_adaptado()
    n_tr = len(raw["y_train"])
    assert raw["A_train"].shape == (n_tr, 2)
    assert raw["W_train"].shape == (n_tr, 4)
    assert raw["Xs_train"].shape == (n_tr, 14)
    n_te = len(raw["y_test"])
    assert raw["A_test"].shape == (n_te, 2)
    assert raw["W_test"].shape == (n_te, 4)
    assert raw["Xs_test"].shape == (n_te, 14)
    for k in ("W_train", "Xs_train", "W_test", "Xs_test"):
        assert int(np.isnan(raw[k]).sum()) == 0, k
    assert bool((raw["y_train"] >= 0).all())
    assert bool((raw["y_test"] >= 0).all())


def test_raw_adaptado_particiones_congeladas():
    from ds02_rul.data import construir_raw_adaptado
    raw = construir_raw_adaptado()
    assert set(np.unique(raw["A_train"][:, 0])) <= {2.0, 5.0, 10.0, 18.0, 20.0, 16.0}
    assert {2.0, 5.0, 10.0, 18.0, 20.0, 16.0} <= set(np.unique(raw["A_train"][:, 0]))
    assert set(np.unique(raw["A_test"][:, 0])) == {11.0, 14.0, 15.0}


def test_raw_adaptado_medianas_solo_fit_units():
    import pandas as pd
    from ds02_rul.data import SENSOR_COLS, construir_raw_adaptado
    raw = construir_raw_adaptado()
    train_con = pd.read_parquet("data/processed/train_con_nulos.parquet")
    fit = train_con[train_con["unit"].isin([2.0, 5.0, 10.0, 18.0, 20.0])]
    esperado = fit[SENSOR_COLS].median(numeric_only=True)
    pd.testing.assert_series_equal(raw["medianas_fit"], esperado)
