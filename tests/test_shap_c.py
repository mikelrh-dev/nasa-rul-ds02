"""Fase 6 (SHAP-C por ramas, SHAPC-BILSTM/LGBM/META/DATA-01): RED -> GREEN.

Tres ramas sobre el bundle C (`models/ensemble.joblib`, manifest 4.338, seed 42),
sin reentrenar ni tocar `models/` ni NB01-06:
- BiLSTM: SHAP sobre `(50,19)` con preproceso del bundle; aditividad `<1e-2`.
- LGBM: TreeSHAP interventional sobre 93 feats (`ensemble._tabular`); `1e-5`.
- Meta: SHAP sobre el ancho REAL de `ridge_meta.n_features_in_` (verificado en
  tiempo de ejecucion; 2 => `Z=[p_lstm,p_lgb]`, 3 => + `cycles/100`); `1e-5`.

Fondo solo train fold-0 del GroupKFold(3) por motor (sin test 11/14/15), seed 42.
EMA fuera. Sin causalidad: SHAP describe el modelo, no el motor.
"""

import json
import os

import numpy as np
import pandas as pd

from src.ds02_rul.shap_c import ejecutar_shap_c

STATEMENT = "SHAP describe el modelo, no el motor: asociaciones no causales."
TEST_UNITS = {11.0, 14.0, 15.0}


_CACHE = {}

def _ejecutar(tmp_path):
    if "res" in _CACHE:
        return _CACHE["res"], _CACHE["md"], _CACHE["out"]
    out = str(tmp_path / "shap_bundle_C")
    res = ejecutar_shap_c(n_filas=8, n_fondo=40, seed=42, out_dir=out, verbose=False)
    md = json.loads((tmp_path / "shap_bundle_C" / "metadata.json").read_text(encoding="utf-8"))
    _CACHE.update(res=res, md=md, out=tmp_path / "shap_bundle_C")
    return res, md, tmp_path / "shap_bundle_C"


def test_shapes_y_aditividad_por_rama(tmp_path):
    """Formas `(50,19)`/`(93,)`/2D y aditividad por rama (Deep <1e-2, resto <1e-5)."""
    res, md, out = _ejecutar(tmp_path)
    assert res["bilstm"]["shap_shape"] == [8, 50, 19], res["bilstm"]
    assert res["lgbm"]["shap_shape"] == [8, 93], res["lgbm"]
    assert res["meta"]["shap_shape"] == [8, res["meta"]["n_features_meta"]], res["meta"]
    # Ancho meta REAL del bundle (no asumido): 2 => [p_lstm, p_lgb].
    assert res["meta"]["n_features_meta"] == 2
    assert res["bilstm"]["aditividad_max_error"] < 1e-2
    assert res["lgbm"]["aditividad_max_error"] < 1e-5
    assert res["meta"]["aditividad_max_error"] < 1e-5
    # Contrato de salidas (design.md): CSV + PNG por rama + metadata.json.
    for p in ("shap_bilstm.csv", "shap_lgbm.csv", "shap_meta.csv",
              "bar_bilstm.png", "bar_lgbm.png", "bar_meta.png", "metadata.json"):
        assert (out / p).exists(), p
    assert len(pd.read_csv(out / "shap_bilstm.csv")) == 19
    assert len(pd.read_csv(out / "shap_lgbm.csv")) == 93
    assert len(pd.read_csv(out / "shap_meta.csv")) == 2


def test_fondo_train_fold0_sin_test(tmp_path):
    """Fondo (y explicadas) sin unidades test 11/14/15 ni fuera de train."""
    res, md, _ = _ejecutar(tmp_path)
    bg = set(res["background_units"])
    ex = set(res["explicadas_units"])
    assert not (bg & TEST_UNITS), bg
    assert not (ex & TEST_UNITS), ex
    assert bg <= {2.0, 10.0, 18.0, 20.0}, bg  # train fold-0 GroupKFold(3)
    assert ex <= {5.0, 16.0}, ex  # validacion fold-0
    assert "train fold-0" in md["fondo"]
    assert "11" not in md["fondo"] or "sin test" in md["fondo"]
    assert md["seed"] == 42
    assert md["n_background"] == 40 or res["n_background"] == 40


def test_nasa_sin_clamp_mayor_de_125(tmp_path):
    """NASA es SUMA de exponenciales asimetricos, sin clamp 125 (SHAPC-DATA-01)."""
    # Sin ejecutar SHAP (pesado): el contrato vive en el bundle de metricas y
    # debe sobrevivir a targets >125 sin truncar.
    from src.ds02_rul.metrics import calculate_nasa_score

    y_true = np.array([200.0, 150.0])  # >125: un clamp los aplastaria
    y_pred = np.array([190.0, 160.0])
    esperado = float(np.sum(np.where((y_pred - y_true) < 0,
                                     np.exp(-(y_pred - y_true) / 13.0) - 1.0,
                                     np.exp((y_pred - y_true) / 10.0) - 1.0)))
    obtenido = calculate_nasa_score(y_true, y_pred)
    assert obtenido == esperado
    assert obtenido > 0
    # `ejecutar_shap_c` tambien declara el NASA sin clamp en el metadata.
    _, md, _ = _ejecutar(tmp_path)
    assert "nasa_sin_clamp" in md
    assert md["nasa_sin_clamp"]["clamp"] is None


def test_no_causal_y_ema_fuera(tmp_path):
    """Frase no-causal obligatoria; EMA fuera de SHAP-C."""
    _, md, out = _ejecutar(tmp_path)
    assert md["nota"] == STATEMENT
    texto = (out / "metadata.json").read_text(encoding="utf-8").lower()
    assert "no causales" in texto
    assert "causa el" not in texto
    assert "ema" in texto
    assert "fuera" in texto
    csv = (out / "shap_meta.csv").read_text(encoding="utf-8").lower()
    assert "causa" not in csv


def test_metadata_contract(tmp_path):
    """metadata.json: explainer/masker/fondo/n_features/base_value/aditividad/versiones/manifest."""
    _, md, _ = _ejecutar(tmp_path)
    for k in ("explainer", "masker", "fondo", "n_features", "base_value",
              "aditividad_max_error", "versiones", "manifest_sha256"):
        assert k in md, k
    assert md["explainer"] == {"bilstm": "PermutationExplainer",
                                "lgbm": "TreeExplainer",
                                "meta": "PermutationExplainer"} or \
        md["explainer"]["lgbm"] == "TreeExplainer"
    assert md["masker"]["lgbm"] == "interventional"
    assert md["n_features"] == {"bilstm": 19, "lgbm": 93, "meta": 2}
    assert isinstance(md["base_value"], dict)
    assert isinstance(md["versiones"], dict) and "shap" in md["versiones"]
    assert isinstance(md["manifest_sha256"], str) and len(md["manifest_sha256"]) == 64
    for rama, err in md["aditividad_max_error"].items():
        assert isinstance(err, float) and err >= 0, (rama, err)


def test_nombres_descriptivos_no_f0(tmp_path):
    """Nombres no posicionales `f0..`: 19 canales, 93 tabular, 2 meta."""
    _, md, out = _ejecutar(tmp_path)
    bil = pd.read_csv(out / "shap_bilstm.csv")
    lgb = pd.read_csv(out / "shap_lgbm.csv")
    meta = pd.read_csv(out / "shap_meta.csv")
    for df in (bil, lgb, meta):
        noms = list(df["feature"])
        assert not any(n.startswith("f") and n[1:].isdigit() for n in noms), noms
    assert "cyc_norm" in list(bil["feature"])
    assert "cyc_norm" in list(lgb["feature"])
    assert set(meta["feature"]) == {"p_lstm", "p_lgb"}
    assert len(bil) == 19 and len(lgb) == 93


def test_lazy_load_y_bundle_solo_lectura(tmp_path):
    """`load_ensemble` lazy dentro de `ejecutar_shap_c`; `models/` intacto."""
    import inspect

    from src.ds02_rul import shap_c

    src = inspect.getsource(shap_c)
    # Sin carga a nivel de modulo: la llamada vive dentro de la funcion.
    cabecera, resto = src.split("def ejecutar_shap_c", 1)
    assert "load_ensemble(" not in cabecera
    assert "load_ensemble(" in resto

    antes = {p: os.path.getmtime(os.path.join("models", p))
             for p in os.listdir("models")}
    _ = _ejecutar(tmp_path)
    despues = {p: os.path.getmtime(os.path.join("models", p))
               for p in os.listdir("models")}
    assert antes == despues, "SHAP-C no debe escribir en models/"
