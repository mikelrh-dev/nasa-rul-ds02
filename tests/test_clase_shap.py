"""RED SAA-9: SHAP con explainer/masker/fondo explícitos sobre el track de clase."""

import numpy as np


def test_top_shap_ordena_por_media_abs():
    from track_clase.shap_clase import top_shap

    rng = np.random.default_rng(0)
    sv = rng.normal(0, 1, size=(50, 4))
    sv[:, 2] *= 5.0  # feature dominante
    top = top_shap(sv, ["a", "b", "c", "d"], k=3)
    assert list(top.columns) == ["feature", "mean_abs_shap"]
    assert top.iloc[0]["feature"] == "c"
    assert len(top) == 3
    assert float(top.iloc[0]["mean_abs_shap"]) > float(top.iloc[1]["mean_abs_shap"])


def test_nombres_features_coherentes_con_pre():
    import pandas as pd
    from track_clase.pipeline_clase import FEATURE_COLS, make_pre

    df = pd.DataFrame(
        [{c: (1.0 if c != "fase_vuelo" else "Crucero") for c in FEATURE_COLS} for _ in range(5)]
    )
    pre = make_pre().fit(df)
    nombres = list(pre.get_feature_names_out())
    assert len(nombres) == pre.transform(df).shape[1]
    assert any("fase_vuelo" in n for n in nombres)
