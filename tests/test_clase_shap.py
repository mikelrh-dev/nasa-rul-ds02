"""SHAP con explainer, masker y fondo explícitos sobre el track de clase."""

import numpy as np


def test_top_shap_ordena_por_media_abs():
    from src.clase.shap_clase import top_shap

    rng = np.random.default_rng(0)
    sv = rng.normal(0, 1, size=(50, 4))
    sv[:, 2] *= 5.0  # feature dominante
    top = top_shap(sv, ["a", "b", "c", "d"], k=3)
    assert list(top.columns) == ["feature", "mean_abs_shap"]
    assert top.iloc[0]["feature"] == "c"
    assert len(top) == 3
    assert float(top.iloc[0]["mean_abs_shap"]) > float(top.iloc[1]["mean_abs_shap"])


def test_mascara_validacion_es_determinista_y_sin_test():
    import pandas as pd
    from src.clase.train_clasicos import grupos_validacion
    X_tr = pd.read_parquet("data/processed/X_train.parquet")
    g = X_tr["unit"].to_numpy()
    va1 = grupos_validacion(g)
    va2 = grupos_validacion(g)
    assert (va1 == va2).all(), "la partición de validación debe ser determinista"
    assert not set(X_tr.iloc[va1]["unit"].unique()) & {11.0, 14.0, 15.0}
    assert 0.2 < len(va1) / len(X_tr) < 0.5, "~1/3 del train"


def test_shap_por_defecto_usa_validacion():
    import joblib
    import pandas as pd
    from src.clase import shap_clase as SC
    SC.ejecutar_shap(n_filas=30, png="resultados/_t.png",
                     csv="resultados/_t.csv", verbose=False)
    import os as _os
    _p = "src/clase/models/shap_xgb_top.joblib"
    if not _os.path.exists(_p):
        _p = "src/clase/models/shap_xgb.joblib"  # legado
    d = joblib.load(_p)
    assert d.get("fuente", "").startswith("validacion"), d.get("fuente")
    assert not set(d.get("unidades", [])) & {11.0, 14.0, 15.0}
    import os
    for p in ("resultados/_t.png", "resultados/_t.csv"):
        os.remove(p)


def test_nombres_features_coherentes_con_pre():
    import pandas as pd
    from src.clase.pipeline_clase import FEATURE_COLS, make_pre

    df = pd.DataFrame(
        [{c: (1.0 if c != "fase_vuelo" else "Crucero") for c in FEATURE_COLS} for _ in range(5)]
    )
    pre = make_pre().fit(df)
    nombres = list(pre.get_feature_names_out())
    assert len(nombres) == pre.transform(df).shape[1]
    assert any("fase_vuelo" in n for n in nombres)
