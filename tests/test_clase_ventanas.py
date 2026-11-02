"""RED test Fase 5 (NB04): la adaptada entra por arriba del pipeline honesto."""

import numpy as np


def test_preprocesado_fit_solo_en_fit_units():
    from track_clase.ventanas_adaptadas import ventanas_adaptadas
    v = ventanas_adaptadas()
    assert v["prep"]["scaler"].n_samples_seen_ == v["n_fit_rows"]
    assert v["n_fit_rows"] < len(v["dev_units_raw"])


def test_particion_y_contrato_ventanas():
    from track_clase.ventanas_adaptadas import ventanas_adaptadas
    v = ventanas_adaptadas()
    assert set(np.unique(v["dev"]["meta"]["unit"].to_numpy())) >= {2.0, 5.0, 16.0}
    assert set(np.unique(v["test"]["meta"]["unit"].to_numpy())) == {11.0, 14.0, 15.0}
    assert v["dev"]["X_tab"].shape[1] == 93
    assert v["test"]["X_tab"].shape[1] == 93
    assert int(np.isnan(v["dev"]["X_tab"]).sum()) == 0
    assert "fase_vuelo" not in v["columnas_tab"]


def test_holdout_16_reservado_para_beta():
    from track_clase.ventanas_adaptadas import ventanas_adaptadas
    v = ventanas_adaptadas()
    assert 16.0 in set(np.unique(v["dev"]["meta"]["unit"].to_numpy()))
    assert 16.0 not in set(np.unique(v["test"]["meta"]["unit"].to_numpy()))
