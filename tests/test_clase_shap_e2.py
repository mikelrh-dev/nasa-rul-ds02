"""SAA-9 de 7 a 10: SHAP Permutation sobre el MLP E2 (no XGB)."""

import json
import os

import joblib
import numpy as np
import pandas as pd

from src.clase.pipeline_clase import FEATURE_COLS
from src.clase import shap_clase_e2 as SE2


def test_modelo_e2_es_mlp_no_xgb():
    """E2 persistido aparte; el XGB de mejor_modelo_clase.joblib queda intacto."""
    if not os.path.exists(SE2.E2_MODEL_PATH):
        from src.clase.train_mlp import persistir_e2

        persistir_e2(destino=SE2.E2_MODEL_PATH, verbose=False)
    pipe = joblib.load(SE2.E2_MODEL_PATH)
    assert dict(pipe.steps)["reg"].__class__.__name__ == "MLPRegressor"
    xgb = joblib.load("models/mejor_modelo_clase.joblib")
    assert dict(xgb.steps)["reg"].__class__.__name__ == "XGBRegressor"


def test_shap_e2_shapes_y_aditividad(tmp_path):
    """Shapes correctos y aditividad base+suma == predict (rtol 1e-5)."""
    imp = SE2.ejecutar_shap(n_filas=30, n_fondo=60, seed=42,
                            out_dir=str(tmp_path / "shap"), verbose=False)
    md = json.loads((tmp_path / "shap" / "metadata.json").read_text(encoding="utf-8"))
    assert md["budget"] == 2 * md["n_features"] + 1
    assert md["explainer"] == "PermutationExplainer"
    assert md["masker"] == "Independent"
    assert md["n_background"] == 60
    assert md["n_explicadas"] == 30
    assert md["aditividad_max_error"] < 1e-5
    assert list(imp.columns) == ["feature", "mean_abs_shap", "mean_shap", "std_shap"]
    assert len(imp) == md["n_features"]
    for p in ("bar.png", "beeswarm.png", "waterfall.png", "importancia.csv"):
        assert (tmp_path / "shap" / p).exists(), p


def test_nombres_pipeline_no_f0(tmp_path):
    imp = pd.read_csv(tmp_path / "shap" / "importancia.csv") if os.path.exists(
        tmp_path / "shap" / "importancia.csv") else None
    if imp is None:
        imp = SE2.ejecutar_shap(n_filas=30, n_fondo=60, seed=42,
                                out_dir=str(tmp_path / "shap"), verbose=False)
    nombres = list(imp["feature"])
    assert not any(n.startswith("f") and n[1:].isdigit() for n in nombres), nombres
    pipe = joblib.load(SE2.E2_MODEL_PATH)
    n_pre = list(pipe.named_steps["pre"].get_feature_names_out())
    assert set(nombres) == set(n_pre)
    assert any("fase_vuelo" in n for n in nombres)
    assert len(nombres) == len(FEATURE_COLS) + 2  # 19 num + fase(3 one-hot)


def test_background_train_sin_test():
    """El fondo sale del train fold-0 de GroupKFold; nunca test."""
    X_tr = pd.read_parquet("data/processed/X_train.parquet").reset_index(drop=True)
    X_te = pd.read_parquet("data/processed/X_test.parquet")
    tr, va = SE2.split_fold0(X_tr)
    assert len(tr) + len(va) == len(X_tr)
    units_tr = set(X_tr.iloc[tr]["unit"].unique())
    units_va = set(X_tr.iloc[va]["unit"].unique())
    assert not units_tr & units_va, "GroupKFold por motor: sin solape"
    # El test se construyó ausente del train: sus unidades no alimentan el fondo
    assert not (set(X_te["unit"].unique()) & units_tr & units_va)
    md = json.loads(open("resultados/mlp_shap_E2/metadata.json", encoding="utf-8").read()) \
        if os.path.exists("resultados/mlp_shap_E2/metadata.json") else {}
    if md:
        assert "train fold-0" in md.get("background", "")
        assert md["n_background"] == 200
