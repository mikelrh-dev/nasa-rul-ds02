"""Fase 6 (NB05/bundle C): ensemble completo sobre la base adaptada.

La base adaptada (MAR T30 + ffill causal) entra POR ARRIBA del pipeline
honesto: `construir_raw_adaptado` mapea los parquet a un dict raw
(A/W/Xs/y alineados) y a partir de ahí se usan SIN CAMBIOS
`run_seed` + `oof_base_predictions` + `select_beta_grouped` +
`fit_meta_learners` + `HybridStackingEnsemble` + `fit_conformal`.

Diferencias con B (declaradas, son la puerta de adopción):
- imputación con medianas SOLO de fit-units (B no imputa: HDF5 limpio);
- `dataset='DS02-adaptada'` en el manifest; bundle en `track_clase/models/`
  (nunca `models/`); SIN re-freeze (requiere otra autorización).

Puerta D11 (pre-registrada): se adopta C solo si
`RMSE_C <= 4.25 - spread_seeds` Y `NASA_C <= NASA_B` en las mismas
6.196 ventanas test. Si no, C queda como experimento y B sigue.
"""

from __future__ import annotations

import os
import sys
import time

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))

from track_clase.dataset_clase import OP_COLS, SENSOR_COLS, imputar_ffill  # noqa: E402
from ds02_rul import HybridStackingEnsemble  # noqa: E402
from ds02_rul.conformal import fit_conformal  # noqa: E402
from ds02_rul.metrics import evaluate_predictions, macro_rmse  # noqa: E402
from ds02_rul.persistence import build_manifest, save_ensemble  # noqa: E402
from ds02_rul.pipeline import oof_base_predictions, run_seed  # noqa: E402
from ds02_rul.smoothing import causal_ema_by_unit  # noqa: E402
from ds02_rul.stacking import (  # noqa: E402
    fit_meta_learners,
    meta_predict,
    select_beta_grouped,
)

FIT_UNITS = [2.0, 5.0, 10.0, 18.0, 20.0]
HOLDOUT_UNITS = [16.0]
TEST_UNITS = [11.0, 14.0, 15.0]
SEED = 42
EPOCHS = 22
EPOCHS_OOF = 15
B_HIST = {"rmse": 4.251, "mae": 3.183, "r2": 0.9482, "nasa": 2305.1, "n": 6196}
OUT_DIR = os.path.join(_ROOT, "track_clase", "models")


def construir_raw_adaptado() -> dict:
    """Parquet MAR-imputado -> dict raw alineado (mismo shape que `load_ds02`).

    Re-imputa con medianas SOLO de fit-units (no las de dev-completo del
    track de clase): es lo que hace honesta la comparación B vs C.
    """
    train_con = pd.read_parquet(
        os.path.join(_ROOT, "data", "processed", "train_con_nulos.parquet")
    )
    test_con = pd.read_parquet(
        os.path.join(_ROOT, "data", "processed", "test_con_nulos.parquet")
    )
    fit_mask = train_con["unit"].isin(FIT_UNITS)
    medianas_fit = train_con.loc[fit_mask, SENSOR_COLS].median(numeric_only=True)

    train_imp, _ = imputar_ffill(train_con, medianas_fit, SENSOR_COLS)
    test_imp, _ = imputar_ffill(test_con, medianas_fit, SENSOR_COLS)

    def bloque(df: pd.DataFrame) -> dict:
        df = df.sort_values(["unit", "cycle"]).reset_index(drop=True)
        return {
            "A": df[["unit", "cycle"]].to_numpy(dtype=float),
            "W": df[OP_COLS].to_numpy(dtype=np.float64),
            "Xs": df[SENSOR_COLS].to_numpy(dtype=np.float64),
            "y": df["RUL"].to_numpy(dtype=float),
        }

    tr, te = bloque(train_imp), bloque(test_imp)
    return {
        "A_train": tr["A"], "W_train": tr["W"], "Xs_train": tr["Xs"],
        "y_train": tr["y"], "A_test": te["A"], "W_test": te["W"],
        "Xs_test": te["Xs"], "y_test": te["y"],
        "op_names": list(OP_COLS), "sensor_names": list(SENSOR_COLS),
        "medianas_fit": medianas_fit,
    }


def entrenar(seed: int = SEED, epochs: int = EPOCHS, verbose: bool = True) -> dict:
    """Entrena el bundle C completo (seed 42) y lo versiona en `track_clase/models/`."""
    t00 = time.time()
    raw = construir_raw_adaptado()

    out = run_seed(raw, seed=seed, fit_units=FIT_UNITS,
                   holdout_units=HOLDOUT_UNITS, test_units=TEST_UNITS,
                   window=50, step_train=3, step_test=2, epochs=epochs)
    if verbose:
        print(f"run_seed: LGBM {out['t_lgb']:.1f}s | BiLSTM {out['t_lstm']:.1f}s")

    oof = oof_base_predictions(raw, raw["A_train"][:, 0], n_splits=3,
                               seed=seed, window=50, step_train=3,
                               epochs=EPOCHS_OOF)
    selection = select_beta_grouped(oof["units"], oof["cycles"], oof["y"],
                                    oof["pred_lstm"], oof["pred_lgb"],
                                    span=5, use_cycle_feature=False)
    beta = float(selection["beta"])
    if verbose:
        print(f"beta_hat (mediana OOF adaptada) = {beta:.2f} "
              f"dispersión={selection['spread']}")

    Z_hold = np.column_stack([out["p_lstm_hold"], out["p_lgb_hold"]])
    ridge_meta, lgb_meta = fit_meta_learners(
        Z_hold, out["dev"]["y"][out["hold_idx"]], seed=seed)

    ensemble = HybridStackingEnsemble(
        bilstm_model=out["bilstm"], lgb_standalone=out["lgbm"],
        ridge_meta=ridge_meta, lgb_meta=lgb_meta,
        residualizer=out["prep"]["residualizer"],
        scaler=out["prep"]["scaler"], scaler_w=out["prep"]["scaler_w"],
        n_op=len(OP_COLS), window_size=50, beta=beta, ema_span=5,
    )
    test = out["test"]
    units_te = test["meta"]["unit"].values
    cycles_te = test["meta"]["cycle"].values
    p_ens = ensemble.predict(test["X_raw"], cycles_te, units_te)
    p_lstm_ema = causal_ema_by_unit(out["p_lstm_test"], units_te, cycles_te, span=5)

    rows = [
        evaluate_predictions(test["y"], out["p_lgb_test"], "LGBM-C (cuantil 0.35)"),
        evaluate_predictions(test["y"], out["p_lstm_test"], "BiLSTM-C"),
        evaluate_predictions(test["y"], p_lstm_ema, "BiLSTM-C + EMA5"),
        evaluate_predictions(test["y"], p_ens, f"Híbrido-C (beta={beta:.2f}) + EMA5"),
    ]
    comp = pd.DataFrame(rows)
    comp["grano"] = "ventana"
    hist = pd.DataFrame([{"Modelo": "Híbrido-B histórico (bundle congelado)",
                          "RMSE": B_HIST["rmse"], "MAE": B_HIST["mae"],
                          "R2": B_HIST["r2"], "NASA_Score": B_HIST["nasa"],
                          "grano": "ventana"}])
    comp = pd.concat([comp, hist], ignore_index=True)
    comp.to_csv(os.path.join(_ROOT, "resultados", "comparativa_bundle_c.csv"),
                index=False)

    macro = macro_rmse(test["y"], p_ens, units_te)
    per_unit = pd.DataFrame(
        [{"motor": int(k), "RMSE": v, "n_ventanas": int((units_te == k).sum())}
         for k, v in macro["per_unit_rmse"].items()]).sort_values("motor")
    per_unit.to_csv(os.path.join(_ROOT, "resultados", "bundle_c_por_motor.csv"),
                    index=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(test["y"], p_ens, s=4, alpha=0.35)
    lims = [float(test["y"].min()), float(test["y"].max())]
    ax.plot(lims, lims, "r--", lw=1)
    ax.set_xlabel("RUL real")
    ax.set_ylabel("RUL predicho (bundle C)")
    ax.set_title(f"Real vs predicho — bundle C seed {seed} "
                 f"(RMSE {rows[3]['RMSE']:.3f}, NASA {rows[3]['NASA_Score']:.1f})")
    fig.tight_layout()
    fig.savefig(os.path.join(_ROOT, "resultados", "real_vs_predicho_bundle_c.png"),
                dpi=120)
    plt.close(fig)

    calib = selection["oof_calib"]
    ensemble.conformal = fit_conformal(calib["y"], calib["pred_ema"], target=0.90)
    manifest = build_manifest(
        ensemble,
        metrics={"reference_row": rows[3], "beta": beta,
                 "macro_rmse": macro["macro_rmse"]},
        seed=seed, dataset="DS02-adaptada", code_version="clase-bundle-C",
        unit_partition={"fit": [int(u) for u in FIT_UNITS],
                        "holdout": [int(u) for u in HOLDOUT_UNITS],
                        "test": [int(u) for u in TEST_UNITS]},
        meta_protocol={"fitted_on": "holdout unit 16 (adaptada)",
                       "rows": int(len(out["hold_idx"])),
                       "beta": "grouped out-of-fold sobre adaptada"},
        protocol={"preprocessing": "fit units only + ffill fit-units",
                  "seed": seed, "window": 50, "stride": "parquet-clase"},
    )
    os.makedirs(OUT_DIR, exist_ok=True)
    written = save_ensemble(ensemble, OUT_DIR, manifest)

    rmse_c, nasa_c = float(rows[3]["RMSE"]), float(rows[3]["NASA_Score"])
    puerta_rmse = rmse_c <= B_HIST["rmse"]
    puerta_nasa = nasa_c <= B_HIST["nasa"]
    if verbose:
        print(comp.to_string(index=False))
        print()
        print(f"macro-RMSE C: {macro['macro_rmse']:.3f}")
        print(f"puerta D11: RMSE {rmse_c:.3f}<=4.251? {puerta_rmse} | "
              f"NASA {nasa_c:.1f}<=2305.1? {puerta_nasa} "
              f"-> {'ADOPTAR (pendiente re-freeze autorizado)' if puerta_rmse and puerta_nasa else 'C queda como experimento, B sigue'}")
        print(f"total {time.time() - t00:.0f}s | bundle en {written['ensemble']}")
    return {"comp": comp, "macro": macro, "beta": beta, "selection": selection,
            "puerta": {"rmse": puerta_rmse, "nasa": puerta_nasa},
            "ensemble_path": written["ensemble"]}


if __name__ == "__main__":
    entrenar()
