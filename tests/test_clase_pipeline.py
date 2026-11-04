"""Tests del pipeline compartido (PIA 3): mismo pre para todos, 1 caso nuevo."""

import pandas as pd
from sklearn.linear_model import Ridge

from src.clase.pipeline_clase import CAT_COLS, FEATURE_COLS, NUM_COLS, make_pipeline, predict_caso_nuevo


def test_mismo_pre_para_todos_y_columnas():
    assert "unit" not in NUM_COLS + CAT_COLS
    assert len(NUM_COLS) == 19 and CAT_COLS == ["fase_vuelo"]
    assert len(FEATURE_COLS) == 20


def test_pipeline_entrena_y_predice_un_caso():
    df = pd.read_parquet("data/processed/X_train.parquet").sample(300, random_state=0)
    y = pd.read_parquet("data/processed/y_train.parquet").loc[df.index].values.ravel()
    pipe = make_pipeline(Ridge(alpha=1.0))
    pipe.fit(df, y)
    caso = {c: df.iloc[0][c] for c in FEATURE_COLS}
    # fase_vuelo ya es str en el parquet
    rul = predict_caso_nuevo(pipe, caso)
    assert isinstance(rul, float) and rul >= 0
    # categoría no vista no rompe (handle_unknown=ignore)
    caso2 = dict(caso)
    caso2["fase_vuelo"] = "Órbita"
    assert predict_caso_nuevo(pipe, caso2) >= 0
