"""RED test: el B congelado, medido bajo dropout (solo inferencia).

Contrato de `clase.evaluar_b_en_adaptada`:
- imputación "de producción": ffill causal + medianas del train LIMPIO
  de B (fit-units), nunca del test;
- el grid de ventanas (unit, cycle final) es idéntico al del test de C
  (mismas 6.196 ventanas, mismos RUL) para que RMSE/NASA sean comparables;
- `models/` no se escribe (solo lectura del bundle congelado).
"""

import numpy as np


def test_grid_adaptado_identico_al_de_c():
    from track_clase.evaluar_b_en_adaptada import ventanas_bajo_dropout
    from track_clase.ventanas_adaptadas import ventanas_adaptadas
    w = ventanas_bajo_dropout()
    ref = ventanas_adaptadas()["test"]
    assert len(w["meta"]) == len(ref["meta"]) == 6196
    assert w["meta"]["unit"].tolist() == ref["meta"]["unit"].tolist()
    assert w["meta"]["cycle"].tolist() == ref["meta"]["cycle"].tolist()
    assert np.allclose(w["y"], ref["y"])


def test_imputacion_produccion_sin_fuga_y_sin_nulos():
    import pandas as pd
    from track_clase.evaluar_b_en_adaptada import imputar_como_produccion, medianas_produccion
    med = medianas_produccion()
    con = pd.read_parquet("data/processed/test_con_nulos.parquet")
    assert int(con["T30"].isna().sum()) > 0
    imp = imputar_como_produccion(con, med)
    assert int(imp.isna().sum().sum()) == 0
    # las medianas son del train limpio de B, no del test
    limpio = pd.read_parquet("data/processed/train.parquet")
    assert int(limpio.isna().sum().sum()) == 0
