"""Read-only data layer for the DS02 decision-support surface.

Everything the UI draws comes from `app/cache/` (`scripts/build_ui_cache.py`) and
`models/ds02_manifest.json`. This module imports pandas and streamlit only —
never TensorFlow — so the app starts in milliseconds and runs on a machine that
has neither the 2.3 GB HDF5 nor a GPU.

Two rules this module exists to enforce:

* `models/` is opened read-only. The only files read there are the manifest and
  (through the cache's provenance) the recorded artifact hash.
* No metric is hardcoded. Every figure is recomputed from the cached predictions
  and their ground truth; the manifest is surfaced separately, as the frozen
  contract it is.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd
import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(APP_DIR)
CACHE_DIR = os.path.join(APP_DIR, "cache")
WINDOWS_PATH = os.path.join(CACHE_DIR, "ds02_windows.parquet")
ROWS_PATH = os.path.join(CACHE_DIR, "ds02_rows.parquet")
PROVENANCE_PATH = os.path.join(CACHE_DIR, "cache_manifest.json")
MANIFEST_PATH = os.path.join(ROOT, "models", "ds02_manifest.json")

AIRWORTHY = "APTO"
PREVENTIVE = "INSPECCION"
AOG = "HANGAR"
NO_DATA = "SIN_DATOS"

DEFAULT_AIRWORTHY = 30.0
DEFAULT_AOG = 25.0

STATE_LABELS = {
    AIRWORTHY: "🟢 APTO PARA VUELO",
    PREVENTIVE: "🟡 INSPECCIÓN PROGRAMADA",
    AOG: "🔴 DERIVACIÓN A HANGAR (AOG)",
    NO_DATA: "⚪ SIN DATOS (aún sin vuelo)",
}

ACTIONS = {
    AIRWORTHY: "Continúa en servicio. Sin acción.",
    PREVENTIVE: "Inspección borescópica programada en la próxima escala.",
    AOG: "Orden de desmontaje HPT/LPT enviada a taller.",
    NO_DATA: "Sin telemetría evaluable en este ciclo.",
}

# The dataset declares these names in the HDF5 (`W_var`, `X_s_var`). They are
# N-CMAPSS names, not the FD001 `s1 … s21` labels — mixing the two would be a
# silent dataset swap in a presentation about DS02.
CHANNEL_LABELS = {
    "alt": "alt · altitud (ft)",
    "Mach": "Mach · número de Mach",
    "TRA": "TRA · ángulo del acelerador (%)",
    "T2": "T2 · temperatura total a la entrada del fan (°R)",
    "T24": "T24 · temperatura salida LPC (°R)",
    "T30": "T30 · temperatura salida HPC (°R)",
    "T48": "T48 · temperatura salida HPT (°R)",
    "T50": "T50 · temperatura salida LPT (°R)",
    "P15": "P15 · presión conducto de sangrado (psia)",
    "P2": "P2 · presión entrada del fan (psia)",
    "P21": "P21 · presión salida LPC (psia)",
    "P24": "P24 · presión salida HPC (psia)",
    "Ps30": "Ps30 · presión estática salida HPC (psia)",
    "P40": "P40 · presión total salida HPT (psia)",
    "P50": "P50 · presión total salida LPT (psia)",
    "Nf": "Nf · velocidad del fan (rpm)",
    "Nc": "Nc · velocidad del núcleo (rpm)",
    "Wf": "Wf · caudal de combustible (pps)",
}

CHANNEL_GROUPS = {
    "Condiciones de vuelo": ["alt", "Mach", "TRA", "T2"],
    "Temperaturas": ["T24", "T30", "T48", "T50", "T2"],
    "Presiones": ["P15", "P2", "P21", "P24", "Ps30", "P40", "P50"],
    "Velocidades de rotor": ["Nf", "Nc"],
    "Combustible": ["Wf"],
}

UNIT_LABELS = {
    11: "Unidad 11 — degradación estándar",
    14: "Unidad 14 — caso atípico / régimen compuesto",
    15: "Unidad 15 — degradación nominal / alta precisión",
}


# --------------------------------------------------------------------- readers
@st.cache_data(show_spinner=False)
def get_windows() -> pd.DataFrame:
    """One row per scored window, straight from the cache (no model load)."""
    frame = pd.read_parquet(WINDOWS_PATH)
    frame["unit"] = frame["unit"].astype(int)
    frame["cycle"] = frame["cycle"].astype(int)
    return frame


@st.cache_data(show_spinner=False)
def get_rows() -> pd.DataFrame:
    """One row per downsampled telemetry row, with the real DS02 channel names."""
    frame = pd.read_parquet(ROWS_PATH)
    frame["unit"] = frame["unit"].astype(int)
    frame["cycle"] = frame["cycle"].astype(int)
    return frame


@st.cache_data(show_spinner=False)
def get_provenance() -> dict:
    with open(PROVENANCE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


@st.cache_data(show_spinner=False)
def get_manifest() -> dict:
    """The frozen artifact contract, read for display only."""
    with open(MANIFEST_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def cache_available() -> bool:
    return all(os.path.exists(p) for p in (WINDOWS_PATH, ROWS_PATH, PROVENANCE_PATH))


# ---------------------------------------------------------------------- policy
def classify(lower: float, airworthy: float = DEFAULT_AIRWORTHY,
             aog: float = DEFAULT_AOG) -> str:
    """Maintenance state from the conformal LOWER bound, never the point estimate.

    The threshold pair is a decision, not a default: see ADR-008. A rule whose
    airworthy band starts above the largest achievable lower bound (≈ 36 on this
    split) would never turn green, which is why the defaults are 30 / 25.
    """
    if not aog < airworthy:
        raise ValueError(
            f"thresholds must satisfy aog < airworthy, got aog={aog}, airworthy={airworthy}"
        )
    if lower >= airworthy:
        return AIRWORTHY
    if lower >= aog:
        return PREVENTIVE
    return AOG


def classify_series(lower, airworthy: float = DEFAULT_AIRWORTHY,
                    aog: float = DEFAULT_AOG) -> pd.Series:
    values = np.asarray(lower, dtype=float)
    return pd.Series(
        [classify(v, airworthy, aog) for v in values],
        index=getattr(lower, "index", None),
        dtype=object,
    )


# ---------------------------------------------------------------------- curves
def unit_curve(windows: pd.DataFrame, unit: int) -> pd.DataFrame:
    """Per-cycle series for one engine.

    The model scores a window every `step` rows, so a cycle carries many
    predictions; the chart shows their mean and their worst (lowest) lower
    bound, which is what the triage uses.
    """
    frame = windows[windows["unit"] == int(unit)]
    if frame.empty:
        raise ValueError(f"no scored windows for unit {unit}")
    grouped = (
        frame.groupby("cycle", as_index=False)
        .agg(
            y_true=("y_true", "mean"),
            pred=("pred", "mean"),
            lower=("lower", "mean"),
            upper=("upper", "mean"),
            lower_min=("lower", "min"),
            windows=("pred", "size"),
        )
        .sort_values("cycle")
        .reset_index(drop=True)
    )
    return grouped


def fleet_snapshot(windows: pd.DataFrame, cycle: int,
                   airworthy: float = DEFAULT_AIRWORTHY,
                   aog: float = DEFAULT_AOG) -> pd.DataFrame:
    """Every unit at the simulated cycle, clamped to its own scored range.

    Clamping is not extrapolation: an engine that stopped at cycle 59 is reported
    at 59 when the fleet clock reads 76, and an engine whose first scored cycle
    is later than the clock is reported as having no data yet rather than being
    given a state it has not earned.
    """
    rows = []
    for unit in sorted(windows["unit"].unique()):
        frame = windows[windows["unit"] == unit]
        first, last = int(frame["cycle"].min()), int(frame["cycle"].max())
        if cycle < first:
            rows.append({
                "unit": int(unit), "cycle": int(cycle), "scored_cycle": None,
                "clamped": False, "reached": False, "y_true": np.nan,
                "pred": np.nan, "lower": np.nan, "upper": np.nan,
                "state": NO_DATA, "action": ACTIONS[NO_DATA], "windows": 0,
                "life": last,
            })
            continue
        scored = min(int(cycle), last)
        at_cycle = frame[frame["cycle"] == scored]
        lower = float(at_cycle["lower"].min())
        rows.append({
            "unit": int(unit), "cycle": int(cycle), "scored_cycle": scored,
            "clamped": scored != int(cycle), "reached": True,
            "y_true": float(at_cycle["y_true"].mean()),
            "pred": float(at_cycle["pred"].mean()),
            "lower": lower,
            "upper": float(at_cycle["upper"].max()),
            "state": classify(lower, airworthy, aog),
            "action": ACTIONS[classify(lower, airworthy, aog)],
            "windows": int(len(at_cycle)),
            "life": last,
        })
    snapshot = pd.DataFrame(rows)
    snapshot["scored_cycle"] = snapshot["scored_cycle"].astype("Int64")
    snapshot["state_label"] = snapshot["state"].map(STATE_LABELS)
    return snapshot


# --------------------------------------------------------------------- metrics
def per_unit_metrics(windows: pd.DataFrame) -> pd.DataFrame:
    """RMSE / MAE / bias per engine, recomputed from the cached windows."""
    rows = []
    for unit in sorted(windows["unit"].unique()):
        frame = windows[windows["unit"] == unit]
        y, p = frame["y_true"].to_numpy(), frame["pred"].to_numpy()
        rows.append({
            "unit": int(unit),
            "windows": int(len(frame)),
            "life": int(frame["cycle"].max()),
            "rmse": float(np.sqrt(np.mean((p - y) ** 2))),
            "mae": float(np.mean(np.abs(p - y))),
            "bias": float(np.mean(p - y)),
        })
    return pd.DataFrame(rows)


def global_metrics(windows: pd.DataFrame) -> dict:
    """Window-weighted metrics plus the per-engine macro-RMSE."""
    y = windows["y_true"].to_numpy()
    p = windows["pred"].to_numpy()
    per_unit = per_unit_metrics(windows)
    return {
        "windows": int(len(windows)),
        "units": int(per_unit["unit"].nunique()),
        "rmse": float(np.sqrt(np.mean((p - y) ** 2))),
        "mae": float(np.mean(np.abs(p - y))),
        "bias": float(np.mean(p - y)),
        "macro_rmse": float(per_unit["rmse"].mean()),
        "nasa_score": float(
            np.sum(np.where(p - y < 0, np.exp(-(p - y) / 13.0) - 1.0,
                            np.exp((p - y) / 10.0) - 1.0))
        ),
    }


BAND_EDGES = (0.0, 25.0, 50.0, 75.0, np.inf)


def mae_by_band(windows: pd.DataFrame) -> pd.DataFrame:
    """MAE per TRUE-RUL band — the cut the reports use, not the predicted one."""
    y = windows["y_true"].to_numpy()
    p = windows["pred"].to_numpy()
    rows = []
    for lo, hi in zip(BAND_EDGES[:-1], BAND_EDGES[1:]):
        mask = (y >= lo) & (y < hi)
        rows.append({
            "band": f"[{lo:.0f}, {hi:.0f})" if np.isfinite(hi) else f"[{lo:.0f}, ∞)",
            "windows": int(mask.sum()),
            "mae": float(np.mean(np.abs(p[mask] - y[mask]))) if mask.any() else np.nan,
            "bias": float(np.mean(p[mask] - y[mask])) if mask.any() else np.nan,
        })
    return pd.DataFrame(rows)


def critical_zone_mae(windows: pd.DataFrame, threshold: float = DEFAULT_AOG) -> float:
    """MAE where the true RUL is below the AOG threshold — the decision zone."""
    mask = windows["y_true"] < threshold
    if not mask.any():
        return float("nan")
    y = windows.loc[mask, "y_true"].to_numpy()
    p = windows.loc[mask, "pred"].to_numpy()
    return float(np.mean(np.abs(p - y)))


def first_alarm_cycle(curve: pd.DataFrame,
                      aog: float = DEFAULT_AOG) -> tuple[int | None, int | None]:
    """Cycles where the lower bound crosses AOG, and where truth crosses it.

    Reported together so a reader can see how early the alarm fires rather than
    being told the band is "conservative".
    """
    below = curve[curve["lower"] < aog]
    alarm = int(below["cycle"].iloc[0]) if not below.empty else None
    truth_below = curve[curve["y_true"] < aog]
    truth = int(truth_below["cycle"].iloc[0]) if not truth_below.empty else None
    return alarm, truth


# ------------------------------------------------------------------ work order
def work_order(snapshot: pd.DataFrame, provenance: dict,
               airworthy: float = DEFAULT_AIRWORTHY,
               aog: float = DEFAULT_AOG) -> dict:
    """JSON-ready order for the units grounded at the simulated cycle."""
    blocked = snapshot[snapshot["state"] == AOG]
    units = []
    for _, row in blocked.iterrows():
        units.append({
            "unidad": int(row["unit"]),
            "estado": AOG,
            "ciclo_simulado": int(row["cycle"]),
            "ciclo_evaluado": int(row["scored_cycle"]),
            "rul_estimada": round(float(row["pred"]), 2),
            "limite_inferior": round(float(row["lower"]), 2),
            "limite_superior": round(float(row["upper"]), 2),
            "rul_real": round(float(row["y_true"]), 2),
            "motivo": f"L_inf < {aog:.1f} ciclos (el estimador puntual puede estar por encima)",
            "accion": ACTIONS[AOG],
        })
    return {
        "documento": "Orden de mantenimiento — derivación a hangar",
        "generado_en": pd.Timestamp.now().isoformat(timespec="seconds"),
        "dataset": "DS02",
        "artefacto_sha256": provenance["artifact"]["ensemble_sha256"],
        "ventana": {
            "size": provenance["source"]["window"],
            "step": provenance["source"]["step"],
            "stride": provenance["source"]["stride"],
        },
        "umbrales": {"apto_si_limite_inferior_ge": airworthy,
                     "hangar_si_limite_inferior_lt": aog},
        "unidades": units,
    }


def work_order_csv(order: dict) -> str:
    """Flat CSV companion to the JSON order (header only when nothing is blocked)."""
    columns = ["unidad", "estado", "ciclo_simulado", "ciclo_evaluado", "rul_estimada",
               "limite_inferior", "limite_superior", "rul_real", "motivo", "accion"]
    if not order["unidades"]:
        return ",".join(columns) + "\n"
    return pd.DataFrame(order["unidades"])[columns].to_csv(index=False)


def thresholds_from(airworthy: float, aog: float) -> dict:
    """Validate the operator's thresholds before they reach the policy."""
    if not (0.0 <= aog < airworthy):
        raise ValueError(
            f"umbral inválido: se requiere 0 <= hangar < apto, recibido "
            f"hangar={aog}, apto={airworthy}"
        )
    return {"airworthy": float(airworthy), "aog": float(aog)}
