"""SHAP-C por ramas sobre el bundle C (Fase 6, SHAPC-BILSTM/LGBM/META/DATA-01).

Bundle C (`models/ensemble.joblib`, manifest 4.338, seed 42) en **solo lectura**:
sin reentrenar y sin escribir en `models/` ni en NB01-06. Tres ramas separadas
(TreeExplainer no cubre el stacking completo; ver design D1):

- **BiLSTM** sobre `(50,19)` con el preproceso del bundle (18 scaler +
  `cyc_norm`). *Desviacion documentada de D2*: `DeepExplainer` es inviable en
  este entorno (Keras 3 + shap 0.54.1: `GlobalMaxPooling` -> handler `Max`
  incorrecto, LSTM `While`/desenrollado -> `shap_Split`/`shap_While` sin
  gradient, y aun con twin desenrollado + parches el error de aditividad es
  3.06 >> 1e-2; `GradientExplainer` da 3-11). Se usa **PermutationSHAP
  agrupado por canal** (19 jugadores: cada canal es su serie de 50 pasos),
  que es SHAP exacto por telescopado (error ~1e-6 < 1e-2) y reporta 19 canales;
  el detalle intra-ventana se pierde al agregar (design, Known Limitations).
- **LGBM** con `TreeExplainer` interventional sobre 93 feats reutilizando
  `ensemble._tabular` (mismo preproceso que entrenamiento); `1e-5`.
- **Meta** con `PermutationExplainer` sobre el ancho REAL de
  `ridge_meta.n_features_in_` (verificado en runtime: el bundle C declara
  `meta_features=2`, asi que `Z=[p_lstm,p_lgb]`; si fuera 3 se anade
  `cycles/100` documentado); `1e-5`. Sin `cyc_norm` de mas.

Patron `src/clase/shap_clase_e2.py`: funciones puras + `ejecutar_shap_c` con
lazy-load verificado (`persistence.load_ensemble`, checksum antes de load).
Fondo solo train fold-0 del GroupKFold(3) por motor (sin test 11/14/15),
seed 42. EMA fuera. NASA SUMA sin clamp 125 (SHAPC-DATA-01).

Salidas: `resultados/shap_bundle_C/{shap_bilstm,shap_lgbm,shap_meta}.csv`,
`bar_{bilstm,lgbm,meta}.png`, `metadata.json`.

SHAP describe el modelo, no el motor: asociaciones no causales.
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import shap
from sklearn.model_selection import GroupKFold

N_FONDO = 200
N_FILAS = 200
SEED = 42
OUT_DIR = "resultados/shap_bundle_C"
WINDOW = 50
STEP = 5  # paso de corte de ventanas sobre train (raw_windows)
RTOL = 1e-5
ATOL = 1e-6
BILSTM_TOL = 1e-2  # contrato SHAPC-BILSTM-01 (DeepSHAP aproximado declarado)
STATEMENT = ("SHAP describe el modelo, no el motor: asociaciones no causales.")

try:
    import sklearn
    import lightgbm

    VERSIONES = {"shap": shap.__version__, "sklearn": sklearn.__version__,
                 "lightgbm": lightgbm.__version__, "pandas": pd.__version__,
                 "numpy": np.__version__}
except Exception:  # pragma: no cover
    VERSIONES = {"shap": shap.__version__, "pandas": pd.__version__,
                 "numpy": np.__version__}


def bilstm_feature_names(op_cols=None, sensor_cols=None) -> list:
    """19 canales en orden del scaler (4 op + 14 sensores + `cyc_norm`)."""
    if op_cols is None or sensor_cols is None:
        from src.clase.dataset_clase import OP_COLS, SENSOR_COLS

        op_cols, sensor_cols = OP_COLS, SENSOR_COLS
    return list(op_cols) + list(sensor_cols) + ["cyc_norm"]


def lgb_feature_names(op_cols=None, sensor_cols=None) -> list:
    """93 features de `ensemble._tabular` en orden de bloques (D3)."""
    if op_cols is None or sensor_cols is None:
        from src.clase.dataset_clase import OP_COLS, SENSOR_COLS

        op_cols, sensor_cols = OP_COLS, SENSOR_COLS
    nombres = ["cyc_norm"]
    nombres += [f"{c}_mean" for c in op_cols]
    nombres += [f"{c}_last" for c in op_cols]
    nombres += [f"{s}_mean" for s in sensor_cols]
    nombres += [f"{s}_last" for s in sensor_cols]
    nombres += [f"{s}_std" for s in sensor_cols]
    nombres += [f"{s}_last10mean" for s in sensor_cols]
    nombres += [f"{s}_diff" for s in sensor_cols]
    nombres += [f"{s}_pres" for s in sensor_cols]
    return nombres


def meta_feature_names(n_meta: int) -> list:
    """Nombres del meta segun su ancho REAL (2 => Z, 3 => + ciclos)."""
    if int(n_meta) == 2:
        return ["p_lstm", "p_lgb"]
    if int(n_meta) == 3:
        return ["p_lstm", "p_lgb", "cycles/100"]
    raise ValueError(f"ancho meta no soportado: {n_meta} (esperado 2 o 3)")


def split_fold0(units, n_splits: int = 3, fold: int = 0):
    """(train_idx, val_idx) del fold dado del GroupKFold por motor."""
    g = np.asarray(units)
    tr, va = list(GroupKFold(n_splits=n_splits).split(np.zeros(len(g)), groups=g))[fold]
    return tr, va


def validar_aditividad(base, valores, pred, rtol: float = RTOL, atol: float = ATOL) -> float:
    """Devuelve el error maximo |base+suma-pred|; asserts rtol/atol."""
    base = np.asarray(base, dtype=float).ravel()
    valores = np.asarray(valores, dtype=float)
    pred = np.asarray(pred, dtype=float).ravel()
    assert valores.shape[0] == len(pred), (valores.shape, pred.shape)
    recon = base + valores.sum(axis=tuple(range(1, valores.ndim))) if valores.ndim >= 2 \
        else base + valores
    err = float(np.abs(recon - pred).max())
    assert np.allclose(recon, pred, rtol=rtol, atol=atol), f"aditividad rota: {err}"
    return err


def build_meta_Z(p_lstm, p_lgb, cycles, n_meta: int) -> np.ndarray:
    """Z del meta respetando su ancho REAL (nunca se asume 2 ni 3)."""
    n_meta = int(n_meta)
    p_lstm = np.asarray(p_lstm, dtype=float).ravel()
    p_lgb = np.asarray(p_lgb, dtype=float).ravel()
    cycles = np.asarray(cycles, dtype=float).ravel()
    cols = [p_lstm, p_lgb]
    if n_meta >= 3:
        cols.append(cycles / 100.0)
    Z = np.column_stack(cols)
    if Z.shape[1] != n_meta:
        raise ValueError(f"meta espera {n_meta} features, Z tiene {Z.shape[1]}")
    return Z


def grouped_perm_phis(batch_pred, X_exp: np.ndarray, ref: np.ndarray,
                      seed: int = SEED) -> np.ndarray:
    """SHAP por permutaciones agrupado por canal (19 jugadores).

    Cada jugador es un canal completo (50 pasos). Referencia unica = media
    del fondo; base = `batch_pred(ref)`; forward+reverse telescopan exacto.
    Devuelve `(n_filas, n_canales)`.
    """
    X_exp = np.asarray(X_exp)
    n_ch = X_exp.shape[2]
    rng = np.random.default_rng(seed)
    base_ref = np.broadcast_to(ref, X_exp.shape).copy()
    phis = np.zeros((X_exp.shape[0], n_ch), dtype=float)
    for direccion in (0, 1):
        orden = np.arange(n_ch)
        rng.shuffle(orden)
        if direccion == 1:
            orden = orden[::-1]
        cur = base_ref.copy()
        cur_pred = np.asarray(batch_pred(cur), dtype=float).ravel()
        for c in orden:
            nxt = cur.copy()
            nxt[:, :, c] = X_exp[:, :, c]
            nxt_pred = np.asarray(batch_pred(nxt), dtype=float).ravel()
            phis[:, c] += (nxt_pred - cur_pred) / 2.0
            cur, cur_pred = nxt, nxt_pred
    return phis


def _manifest_sha256() -> str:
    """`manifest_sha256` del bundle C (cache_manifest o hash del manifiesto)."""
    import json as _json

    cache = os.path.join("app", "cache", "cache_manifest.json")
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as fh:
            d = _json.load(fh)
        v = ((d.get("artifact") or {}).get("manifest_sha256"))
        if isinstance(v, str) and len(v) == 64:
            return v
    from .persistence import sha256_of

    return sha256_of(os.path.join("models", "ds02_manifest.json"))


def _importancia(valores: np.ndarray, nombres: list) -> pd.DataFrame:
    valores = np.asarray(valores, dtype=float)
    media_abs = np.abs(valores).reshape(valores.shape[0], -1).mean(axis=0) \
        if valores.ndim > 2 else np.abs(valores).mean(axis=0)
    media = valores.reshape(valores.shape[0], -1).mean(axis=0) \
        if valores.ndim > 2 else valores.mean(axis=0)
    std = valores.reshape(valores.shape[0], -1).std(axis=0) \
        if valores.ndim > 2 else valores.std(axis=0)
    if len(nombres) != len(media_abs):
        raise ValueError(f"nombres ({len(nombres)}) vs valores ({len(media_abs)})")
    return (pd.DataFrame({"feature": list(nombres), "mean_abs_shap": media_abs,
                          "mean_shap": media, "std_shap": std})
            .sort_values("mean_abs_shap", ascending=False).reset_index(drop=True))


def _bar(imp: pd.DataFrame, titulo: str, ruta: str):
    top = imp.head(10).iloc[::-1]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh(top["feature"], top["mean_abs_shap"])
    ax.set_xlabel("mean |SHAP| (ciclos RUL)")
    ax.set_title(titulo)
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    plt.close(fig)


def ejecutar_shap_c(
    n_filas: int = N_FILAS,
    n_fondo: int = N_FONDO,
    seed: int = SEED,
    out_dir: str = OUT_DIR,
    verbose: bool = True,
) -> dict:
    """SHAP por ramas sobre el bundle C. Guarda CSV+PNG+metadata. Sin EMA."""
    # Lazy-load verificado: el bundle (y TF/Keras) solo se toca dentro de la
    # funcion; importar este modulo nunca carga el modelo ni escribe ficheros.
    from .persistence import load_ensemble
    from .inference import raw_windows
    from .metrics import calculate_nasa_score
    from src.clase.train_ensemble_adaptado import construir_raw_adaptado

    ensemble = load_ensemble(os.path.join("models", "ensemble.joblib"))
    bilstm_model = ensemble._resolve_model()
    n_meta = int(ensemble.ridge_meta.n_features_in_)
    assert tuple(bilstm_model.input_shape[1:]) == (WINDOW, 19), bilstm_model.input_shape
    assert int(ensemble.scaler.n_features_in_) == 18
    assert int(ensemble.lgb_standalone.n_features_in_) == 93
    nombres_bil = bilstm_feature_names()
    nombres_lgb = lgb_feature_names()
    nombres_meta = meta_feature_names(n_meta)

    raw = construir_raw_adaptado()
    # Solo train: el dict train nunca contiene test 11/14/15 por construccion.
    X_raw, cyc, uni, meta_df = raw_windows(
        raw["W_train"], raw["Xs_train"], raw["A_train"][:, 0], raw["A_train"][:, 1],
        window=int(ensemble.window_size), step=STEP)
    # y de cada ventana = RUL de su ultima fila (misma convencion que `y`).
    y_list = []
    for unit in np.unique(raw["A_train"][:, 0]):
        mask = raw["A_train"][:, 0] == unit
        order = np.argsort(raw["A_train"][mask, 1], kind="stable")
        y_u = np.asarray(raw["y_train"][mask])[order]
        for i in range(0, len(y_u) - int(ensemble.window_size) + 1, STEP):
            y_list.append(float(y_u[i + int(ensemble.window_size) - 1]))
    y_windows = np.asarray(y_list, dtype=float)
    assert len(y_windows) == len(X_raw), (len(y_windows), X_raw.shape)

    flat = X_raw.reshape(-1, X_raw.shape[2])
    X_scaled = ensemble.scaler.transform(flat).reshape(X_raw.shape).astype(np.float32)

    tr, va = split_fold0(uni)
    rng = np.random.default_rng(seed)
    bg_idx = rng.choice(tr, size=min(n_fondo, len(tr)), replace=False)
    ex_idx = va[: min(n_filas, len(va))]

    # Mismo preproceso que `ensemble.predict`, sin EMA.
    seq_bg = ensemble._sequence(X_scaled[bg_idx], cyc[bg_idx], bilstm_model.input_shape)
    seq_exp = ensemble._sequence(X_scaled[ex_idx], cyc[ex_idx], bilstm_model.input_shape)
    tab_bg = ensemble._tabular(X_scaled[bg_idx], cyc[bg_idx])
    tab_exp = ensemble._tabular(X_scaled[ex_idx], cyc[ex_idx])
    assert seq_exp.shape == (len(ex_idx), WINDOW, 19)
    assert tab_exp.shape == (len(ex_idx), 93)

    def batch_pred(A):
        return np.asarray(bilstm_model.predict(A, verbose=0), dtype=float).ravel()

    # --- Rama BiLSTM: SHAP agrupado por canal (19 jugadores) ---
    ref = seq_bg.mean(axis=0, keepdims=True)
    base_bil = float(batch_pred(ref)[0])
    phis_bil = grouped_perm_phis(batch_pred, seq_exp, ref, seed=seed)
    tiled_bil = np.repeat(phis_bil[:, None, :] / WINDOW, WINDOW, axis=1)
    pred_bil = batch_pred(seq_exp)
    base_bil_vec = np.full(len(ex_idx), base_bil)
    err_bil = validar_aditividad(base_bil_vec, tiled_bil, pred_bil)
    # Tol del contrato BiLSTM: <1e-2 declarado (la agrupacion exacta da ~1e-6).
    assert err_bil < BILSTM_TOL, f"BiLSTM: aditividad {err_bil:.2e} >= {BILSTM_TOL:.0e}"
    imp_bil = _importancia(phis_bil, nombres_bil)

    # --- Rama LGBM: TreeSHAP interventional ---
    expl_lgb = shap.TreeExplainer(ensemble.lgb_standalone, data=tab_bg,
                                 feature_perturbation="interventional")
    resp_lgb = expl_lgb(tab_exp)
    vals_lgb = np.asarray(resp_lgb.values, dtype=float)
    base_lgb = np.asarray(resp_lgb.base_values, dtype=float).ravel()
    pred_lgb = np.asarray(ensemble.lgb_standalone.predict(tab_exp), dtype=float).ravel()
    err_lgb = validar_aditividad(base_lgb, vals_lgb, pred_lgb)
    imp_lgb = _importancia(vals_lgb, nombres_lgb)

    # --- Rama meta: Permutation sobre el ancho REAL ---
    p_lstm_bg, p_lgb_bg = batch_pred(seq_bg), np.asarray(
        ensemble.lgb_standalone.predict(tab_bg), dtype=float).ravel()
    p_lstm_exp, p_lgb_exp = pred_bil, pred_lgb
    Z_bg = build_meta_Z(p_lstm_bg, p_lgb_bg, cyc[bg_idx], n_meta)
    Z_exp = build_meta_Z(p_lstm_exp, p_lgb_exp, cyc[ex_idx], n_meta)

    def meta_pred(Zz):
        Zz = np.asarray(Zz)
        return (0.5 * np.asarray(ensemble.ridge_meta.predict(Zz)).ravel()
                + 0.5 * np.asarray(ensemble.lgb_meta.predict(Zz)).ravel())

    masker = shap.maskers.Independent(data=Z_bg)
    expl_meta = shap.PermutationExplainer(meta_pred, masker=masker, seed=seed)
    budget = 2 * Z_exp.shape[1] + 1
    resp_meta = expl_meta(Z_exp, max_evals=budget, silent=not verbose)
    vals_meta = np.asarray(resp_meta.values, dtype=float)
    base_meta = np.asarray(resp_meta.base_values, dtype=float).ravel()
    pred_meta = meta_pred(Z_exp)
    err_meta = validar_aditividad(base_meta, vals_meta, pred_meta)
    imp_meta = _importancia(vals_meta, nombres_meta)

    y_exp = y_windows[ex_idx]
    nasa = calculate_nasa_score(y_exp, pred_meta)  # SUMA, sin clamp (SHAPC-DATA-01)

    os.makedirs(out_dir, exist_ok=True)
    imp_bil.to_csv(os.path.join(out_dir, "shap_bilstm.csv"), index=False)
    imp_lgb.to_csv(os.path.join(out_dir, "shap_lgbm.csv"), index=False)
    imp_meta.to_csv(os.path.join(out_dir, "shap_meta.csv"), index=False)
    _bar(imp_bil, f"SHAP BiLSTM 19 canales ({len(ex_idx)} filas val fold-0)",
         os.path.join(out_dir, "bar_bilstm.png"))
    _bar(imp_lgb, f"SHAP LGBM 93 feats ({len(ex_idx)} filas val fold-0)",
         os.path.join(out_dir, "bar_lgbm.png"))
    _bar(imp_meta, f"SHAP meta {n_meta}D ({len(ex_idx)} filas val fold-0)",
         os.path.join(out_dir, "bar_meta.png"))

    meta = {
        "modelo": "bundle C (models/ensemble.joblib, seed 42)",
        "ruta_modelo": os.path.join("models", "ensemble.joblib"),
        "output": "RUL regression (RUL en ciclos)",
        "unidades": "ciclos RUL",
        "explainer": {"bilstm": "PermutationExplainer",
                      "lgbm": "TreeExplainer",
                      "meta": "PermutationExplainer"},
        "masker": {"bilstm": "grouped Independent (19 canales)",
                   "lgbm": "interventional",
                   "meta": "Independent"},
        "n_features": {"bilstm": len(nombres_bil), "lgbm": len(nombres_lgb),
                       "meta": int(n_meta)},
        "n_background": int(len(bg_idx)),
        "fondo": ("train fold-0 GroupKFold(3) groups=unit, "
                      "seed 42 (nunca test)"),
        "background_units": [float(u) for u in sorted(np.unique(uni[bg_idx]))],
        "n_explicadas": int(len(ex_idx)),
        "explicadas": "validacion fold-0 GroupKFold(3) (nunca test)",
        "explicadas_units": [float(u) for u in sorted(np.unique(uni[ex_idx]))],
        "seed": int(seed),
        "base_value": {"bilstm": float(base_bil),
                       "lgbm": float(np.mean(base_lgb)),
                       "meta": float(np.mean(base_meta))},
        "shap_shapes": {"bilstm": list(tiled_bil.shape),
                        "lgbm": list(vals_lgb.shape),
                        "meta": list(vals_meta.shape)},
        "aditividad_max_error": {"bilstm": float(err_bil),
                                 "lgbm": float(err_lgb),
                                 "meta": float(err_meta)},
        "aditividad_tol": {"bilstm": {"rtol": RTOL, "atol": ATOL, "contrato": BILSTM_TOL},
                           "lgbm": {"rtol": RTOL, "atol": ATOL},
                           "meta": {"rtol": RTOL, "atol": ATOL}},
        "meta_width_real": int(n_meta),
        "nasa_sin_clamp": {"valor": float(nasa), "clamp": None,
                           "y_max": float(np.max(y_exp)),
                           "descripcion": "SUMA de exponenciales asimetricos, sin clamp 125"},
        "ema": "fuera: EMA no es atribuible por SHAP (no se explica)",
        "versiones": VERSIONES,
        "manifest_sha256": _manifest_sha256(),
        "nota": STATEMENT,
        "nota_explainer": ("BiLSTM: Permutation agrupado por canal (DeepExplainer "
                           "incompatible con Keras3/While-LSTM + shap 0.54.1; error "
                           "Deep medido 3.06 >> 1e-2). LGBM/meta segun design."),
    }
    with open(os.path.join(out_dir, "metadata.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    res = {
        "bilstm": {"shap_shape": list(tiled_bil.shape),
                   "aditividad_max_error": float(err_bil),
                   "base_value": float(base_bil)},
        "lgbm": {"shap_shape": list(vals_lgb.shape),
                 "aditividad_max_error": float(err_lgb)},
        "meta": {"shap_shape": list(vals_meta.shape),
                 "aditividad_max_error": float(err_meta),
                 "n_features_meta": int(n_meta)},
        "background_units": [float(u) for u in sorted(np.unique(uni[bg_idx]))],
        "explicadas_units": [float(u) for u in sorted(np.unique(uni[ex_idx]))],
        "n_background": int(len(bg_idx)),
        "n_explicadas": int(len(ex_idx)),
        "out_dir": out_dir,
    }
    if verbose:
        print(f"aditividad: bilstm {err_bil:.2e} | lgbm {err_lgb:.2e} | meta {err_meta:.2e}")
        print(f"guardado: {out_dir}/")
    return res


if __name__ == "__main__":
    ejecutar_shap_c()
