"""Bundle C: híbrido completo sobre la base adaptada (MAR T30 + ffill causal).

Desde 2026-11-04 el bundle C es el **campeón desplegado**. Este script entrena y
versiona en `models/` el ensamble (BiLSTM + LightGBM + stacking + EMA) usando la
base imputada, y escribe `models/ds02_manifest.json` con lo que hizo.

La base adaptada entra POR ARRIBA del pipeline honesto: `construir_raw_adaptado`
mapea los parquet a un dict raw (A/W/Xs/y alineados) y a partir de ahí se usan
SIN CAMBIOS las funciones del paquete congelado:

    run_seed + oof_base_predictions + select_beta_grouped
    + fit_meta_learners + HybridStackingEnsemble + fit_conformal

Qué aporta sobre el pipeline congelado:
- imputación con medianas SOLO de fit-units, nunca con estadísticos del test;
- `dataset='DS02'` satisface el contrato de forma, y `dataset_variant` declara
  sin ambigüedad que se entrenó sobre la base imputada;
- el manifiesto guarda, junto a la métrica agregada, el reparto macro por motor:
  el error se audita desde el artefacto y no desde un documento.

No reentrenar sin querer: TensorFlow en CPU no es determinista, así que una
corrida nueva puede dar otra cifra y dejar el manifiesto desalineado con los
notebooks. El manifiesto es la fuente de verdad del bundle instalado.
"""

from __future__ import annotations

import os
import sys
import time

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))

from ds02_rul.conformal import fit_conformal  # noqa: E402
from ds02_rul.ensemble import HybridStackingEnsemble  # noqa: E402
from ds02_rul.metrics import evaluate_predictions, macro_rmse  # noqa: E402
from ds02_rul.persistence import build_manifest, save_ensemble  # noqa: E402
from ds02_rul.pipeline import oof_base_predictions, run_seed  # noqa: E402
from ds02_rul.smoothing import causal_ema_by_unit  # noqa: E402
from ds02_rul.stacking import (  # noqa: E402
    fit_meta_learners,
    select_beta_grouped,
)
from src.clase.dataset_clase import OP_COLS, SENSOR_COLS, imputar_ffill  # noqa: E402

FIT_UNITS = [2.0, 5.0, 10.0, 18.0, 20.0]
HOLDOUT_UNITS = [16.0]
TEST_UNITS = [11.0, 14.0, 15.0]
SEED = 42
EPOCHS = 22
EPOCHS_OOF = 15

OUT_DIR = os.path.join(_ROOT, "models")


def construir_raw_adaptado() -> dict:
    """Parquet MAR-imputado -> dict raw alineado (mismo shape que `load_ds02`).

    Re-imputa con medianas SOLO de fit-units (no las de dev-completo del
    track de clase): es lo que mantiene el protocolo honesto.
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


def evaluar_semilla(seed: int = SEED, epochs: int = EPOCHS, verbose: bool = False) -> dict:
    """Entrena el ensemble completo de una semilla y lo mide. No escribe nada.

    Es la pieza que reutiliza `evaluar_c_multisemilla.py`: separar el cálculo de
    la persistencia evita que una corrida de estabilidad sobrescriba el bundle
    desplegado.
    """
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

    macro = macro_rmse(test["y"], p_ens, units_te)
    per_unit = pd.DataFrame(
        [{"motor": int(k), "RMSE": v, "n_ventanas": int((units_te == k).sum())}
         for k, v in macro["per_unit_rmse"].items()]).sort_values("motor")

    ensemble.conformal = fit_conformal(selection["oof_calib"]["y"],
                                       selection["oof_calib"]["pred_ema"], target=0.90)

    if verbose:
        print(f"total {time.time() - t00:.0f}s")
    return {
        "seed": seed,
        "ensemble": ensemble,
        "comp": comp,
        "rows": rows,
        "macro": macro,
        "per_unit": per_unit,
        "beta": beta,
        "selection": selection,
        "test": test,
        "p_ens": p_ens,
        "out": out,
    }


def entrenar(seed: int = SEED, epochs: int = EPOCHS, verbose: bool = True) -> dict:
    """Entrena, escribe el bundle en `models/` y deja la comparativa en `resultados/`."""
    r = evaluar_semilla(seed=seed, epochs=epochs, verbose=verbose)
    comp, rows, macro = r["comp"], r["rows"], r["macro"]

    comp.to_csv(os.path.join(_ROOT, "resultados", "comparativa_bundle_c.csv"), index=False)
    r["per_unit"].to_csv(os.path.join(_ROOT, "resultados", "bundle_c_por_motor.csv"),
                         index=False)

    fig, ax = plt.subplots(figsize=(8, 5))
    test = r["test"]
    ax.scatter(test["y"], r["p_ens"], s=4, alpha=0.35)
    lims = [float(test["y"].min()), float(test["y"].max())]
    ax.plot(lims, lims, "r--", lw=1)
    ax.set_xlabel("RUL real")
    ax.set_ylabel("RUL predicho (bundle C)")
    ax.set_title(f"Real vs predicho — bundle C seed {seed} "
                 f"(RMSE {rows[3]['RMSE']:.3f}, NASA {rows[3]['NASA_Score']:.1f})")
    fig.tight_layout()
    fig.savefig(os.path.join(_ROOT, "resultados", "real_vs_predicho_bundle_c.png"), dpi=120)
    plt.close(fig)

    selection = r["selection"]
    manifest = build_manifest(
        r["ensemble"],
        metrics={"reference_row": rows[3], "beta": r["beta"],
                 "macro_rmse": macro["macro_rmse"]},
        seed=seed, dataset="DS02", code_version="clase-bundle-C",
        dataset_variant="DS02-adaptada (MAR T30 + ffill causal, medianas de fit-units)",
        unit_partition={"fit": [int(u) for u in FIT_UNITS],
                        "holdout": [int(u) for u in HOLDOUT_UNITS],
                        "test": [int(u) for u in TEST_UNITS]},
        meta_protocol={"fitted_on": "holdout unit 16 (adaptada)",
                       "rows": int(len(r["out"]["hold_idx"])),
                       "beta": "grouped out-of-fold sobre adaptada"},
        protocol={"preprocessing": "fit units only + ffill fit-units",
                  "seed": seed, "window": 50, "stride": "parquet-clase"},
    )
    os.makedirs(OUT_DIR, exist_ok=True)
    written = save_ensemble(r["ensemble"], OUT_DIR, manifest)

    rmse_c, nasa_c = float(rows[3]["RMSE"]), float(rows[3]["NASA_Score"])
    if verbose:
        print(comp.to_string(index=False))
        print()
        print(f"macro-RMSE C: {macro['macro_rmse']:.3f}")
        print(f"RMSE {rmse_c:.3f} | NASA {nasa_c:.1f}")
        print(f"bundle en {written['ensemble']}")
    return {**r, "written": written}


if __name__ == "__main__":
    entrenar()
