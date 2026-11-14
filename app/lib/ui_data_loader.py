"""Read-only data layer for the DS02 decision-support surface.

Everything the UI draws comes from `app/cache/` (`scripts/build/build_ui_cache.py`) and
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

import hashlib
import json
import os

import numpy as np
import pandas as pd
import streamlit as st

from app import _paths
from app.lib import _constantes

ROOT = str(_paths.ROOT)
CACHE_DIR = str(_paths.CACHE_DIR)
WINDOWS_PATH = str(_paths.WINDOWS_PATH)
ROWS_PATH = str(_paths.ROWS_PATH)
PROVENANCE_PATH = str(_paths.PROVENANCE_PATH)
MANIFEST_PATH = str(_paths.MANIFEST_PATH)
ARTIFACT_PATH = str(_paths.ARTIFACT_PATH)

# El sello se compara en bloques: el artefacto pesa decenas de MB y leerlo entero
# para hashearlo duplicaria la memoria del proceso.
HASH_CHUNK = 1 << 20  # 1 MiB

AIRWORTHY = "APTO"
PREVENTIVE = "INSPECCION"
AOG = "HANGAR"
NO_DATA = "SIN_DATOS"
# Estado que emite `R1_SEGURIDAD` cuando el dato es imposible: no es "sin datos",
# es "no se decide". Se mantiene distinto para que la UI no los confunda.
SIN_DECISION = "SIN_DECISION"

# Dueño único de los umbrales: `app/lib/_constantes.py`. Se re-exportan aquí
# para que `L.DEFAULT_AIRWORTHY` / `L.DEFAULT_AOG` sigan funcionando.
DEFAULT_AIRWORTHY = _constantes.DEFAULT_AIRWORTHY
DEFAULT_AOG = _constantes.DEFAULT_AOG

# Símbolo por estado: el color nunca va solo (daltónicos y pantallas malas).
STATE_SYMBOLS = {
    AIRWORTHY: "circle",
    PREVENTIVE: "square",
    AOG: "x",
    NO_DATA: "diamond",
    SIN_DECISION: "cross",
}

STATE_LABELS = {
    AIRWORTHY: "🟢 APTO PARA VUELO",
    PREVENTIVE: "🟡 INSPECCIÓN PROGRAMADA",
    AOG: "🔴 DERIVACIÓN A HANGAR (AOG)",
    NO_DATA: "⏳ EN ESPERA DE CICLO (aún sin vuelo)",
    SIN_DECISION: "⛔ SIN DECISIÓN (dato imposible)",
}

ACTIONS = {
    AIRWORTHY: "Continúa en servicio. Sin acción.",
    PREVENTIVE: "Inspección borescópica programada en la próxima escala.",
    AOG: "Orden de desmontaje HPT/LPT enviada a taller.",
    NO_DATA: "Sin telemetría evaluable en este ciclo.",
    SIN_DECISION: "No se decide: corrige el dato imposible y vuelve a evaluar.",
}

# The dataset declares these names in the HDF5 (`W_var`, `X_s_var`). They are
# N-CMAPSS names, not the FD001 `s1 … s21` labels — mixing the two would be a
# silent dataset swap in a presentation about DS02.
CHANNEL_LABELS = {
    "alt": "alt · altitud (ft)",
    "Mach": "Mach · adimensional",
    "TRA": "TRA · acelerador (%)",
    "T2": "T2 · entrada fan (°R)",
    "T24": "T24 · salida LPC (°R)",
    "T30": "T30 · salida HPC (°R)",
    "T48": "T48 · salida HPT (°R)",
    "T50": "T50 · salida LPT (°R)",
    "P15": "P15 · sangrado (psia)",
    "P2": "P2 · entrada fan (psia)",
    "P21": "P21 · salida LPC (psia)",
    "P24": "P24 · salida HPC (psia)",
    "Ps30": "Ps30 · estatica HPC (psia)",
    "P40": "P40 · total HPT (psia)",
    "P50": "P50 · total LPT (psia)",
    "Nf": "Nf · fan (rpm)",
    "Nc": "Nc · nucleo (rpm)",
    "Wf": "Wf · combustible (pps)",
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


def fmt_miles(n: int | float) -> str:
    """Entero con separador de miles español: `6196` → `6.196`.

    `f"{n:,}"` usa coma sin locale; la UI en español debe usar punto.
    """
    return f"{int(n):,}".replace(",", ".")


# Umbral de correlacion con el RUL real para que un canal se destaque en la vista
# alineada. Se calcula, no es una lista fija: si la cache cambia, el resaltado sigue
# a los datos.
# Umbrales de destaque, iguales para todos los canales: correlacion de la deriva
# media por tramo de RUL con el tramo, y salto minimo en puntos porcentuales.
DRIFT_DESTACO_CORR = 0.3
DRIFT_SALTO_MIN = 0.5
# Minimo de observaciones para que un tramo de RUL entre en el resumen.
MIN_MUESTRAS_BIN = 5


def drift_por_rul(channels: list[str], bin_width: int = 10):
    """Deriva % de cada canal respecto a la baseline de su unidad, alineada por RUL real.

    Para cada unidad y canal: media por ciclo, baseline = media de sus 5 primeros
    ciclos (la misma definicion que `fig_deriva`), deriva = (valor / baseline - 1) * 100.
    El RUL del ciclo es el minimo de las ventanas que empiezan en ese ciclo.

    Devuelve `(frame, resumen)`:
      frame   -> unit, cycle, rul, canal, deriva, bin, rul_centro
      resumen -> por canal: inicio_vida, fin_vida, salto, corr_rul, resaltar
    """
    columnas = ["unit", "cycle", "rul", "canal", "deriva", "bin", "rul_centro"]
    resumen_vacio = pd.DataFrame(
        columns=["inicio_vida", "fin_vida", "salto", "corr_rul", "resaltar"]
    )
    filas = get_rows()
    ventanas = get_windows()
    if filas.empty or ventanas.empty:
        return pd.DataFrame(columns=columnas), resumen_vacio

    rul_de_ciclo = ventanas.groupby(["unit", "cycle"], as_index=False)["y_true"].min()
    trozos = []
    for unidad, grupo in filas.groupby("unit"):
        por_ciclo = (
            grupo.groupby("cycle", as_index=False)[list(channels)]
            .mean(numeric_only=True)
            .sort_values("cycle")
        )
        baseline = por_ciclo.head(5)[list(channels)].mean()
        deriva = por_ciclo.copy()
        deriva[list(channels)] = (por_ciclo[list(channels)] / baseline - 1.0) * 100.0
        largo = deriva.melt(id_vars=["cycle"], value_vars=list(channels),
                            var_name="canal", value_name="deriva")
        largo.insert(0, "unit", int(unidad))
        trozos.append(largo)

    frame = (pd.concat(trozos, ignore_index=True) if trozos
             else pd.DataFrame(columns=["unit", "cycle", "canal", "deriva"]))
    frame["cycle"] = frame["cycle"].astype(int)
    frame = frame.merge(
        rul_de_ciclo.rename(columns={"y_true": "rul"}),
        on=["unit", "cycle"], how="left",
    ).dropna(subset=["rul", "deriva"]).copy()
    frame["rul"] = frame["rul"].astype(float)
    frame["bin"] = (frame["rul"] // bin_width).astype(int)
    frame["rul_centro"] = frame["bin"] * bin_width + bin_width / 2.0
    frame = frame[columnas].sort_values(["canal", "unit", "cycle"]).reset_index(drop=True)

    # Tramos con menos de MIN_MUESTRAS_BIN observaciones no son fiables: el extremo
    # de RUL alto solo lo alcanzan las unidades mas longevas y con 4 filas el
    # promedio es ruido.
    agregado = (
        frame.groupby(["bin", "canal"], as_index=False)
        .agg(media=("deriva", "mean"), n=("deriva", "size"))
    )
    validos = agregado[agregado["n"] >= MIN_MUESTRAS_BIN]
    filas_resumen = []
    for canal in channels:
        serie = validos[validos["canal"] == canal].sort_values("bin")
        puntos = frame.loc[frame["canal"] == canal]
        if serie.empty or puntos.empty:
            continue
        # Bins en RUL ascendente: el mas alto es el inicio de vida y el mas bajo el
        # final. Salto positivo = el sensor sube al acercarse el fallo.
        inicio = float(serie["media"].iloc[-1])
        fin = float(serie["media"].iloc[0])
        corr = float(puntos["deriva"].corr(puntos["rul"]))
        salto = fin - inicio
        filas_resumen.append({
            "canal": canal, "inicio_vida": inicio, "fin_vida": fin,
            "salto": salto, "corr_rul": corr,
            "resaltar": abs(corr) >= DRIFT_DESTACO_CORR
            and abs(salto) >= DRIFT_SALTO_MIN,
        })
    tabla = pd.DataFrame(
        filas_resumen,
        columns=["canal", "inicio_vida", "fin_vida", "salto", "corr_rul", "resaltar"],
    )
    if tabla.empty:
        return frame, resumen_vacio
    return frame, tabla.set_index("canal")


# --------------------------------------------------------------------- readers
@st.cache_data(ttl=3600, show_spinner=False)
def get_windows() -> pd.DataFrame:
    """One row per scored window, straight from the cache (no model load)."""
    frame = pd.read_parquet(WINDOWS_PATH)
    frame["unit"] = frame["unit"].astype(int)
    frame["cycle"] = frame["cycle"].astype(int)
    return frame


@st.cache_data(ttl=3600, show_spinner=False)
def get_rows() -> pd.DataFrame:
    """One row per downsampled telemetry row, with the real DS02 channel names."""
    frame = pd.read_parquet(ROWS_PATH)
    frame["unit"] = frame["unit"].astype(int)
    frame["cycle"] = frame["cycle"].astype(int)
    return frame


@st.cache_data(ttl=3600, show_spinner=False)
def get_provenance() -> dict:
    """Provenance de `app/cache/cache_manifest.json`: dataset, ventana y hashes.

    La UI la usa para saber qué artefacto está mostrando y sellar la
    coherencia caché-manifest-bundle.
    """
    with open(PROVENANCE_PATH, encoding="utf-8") as fh:
        return json.load(fh)


@st.cache_data(ttl=3600, show_spinner=False)
def get_manifest() -> dict:
    """The frozen artifact contract, read for display only."""
    with open(MANIFEST_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def verify_cache_manifest(provenance_path: str | None = None,
                          manifest_path: str | None = None) -> dict:
    """Valida que `app/cache/cache_manifest.json` no esté stale (CACHE-DRIFT-01).

    Compara `artifact.manifest_sha256` registrado en el provenance con el
    SHA-256 real de `models/ds02_manifest.json` en disco. Si falta el campo,
    si el digest no coincide o si el manifest no se puede leer, eleva
    `RuntimeError` con el par registrado/leído: una caché con el sello roto
    no se reutiliza en silencio. Devuelve el provenance validado.
    """
    prov_path = PROVENANCE_PATH if provenance_path is None else provenance_path
    man_path = MANIFEST_PATH if manifest_path is None else manifest_path

    try:
        with open(prov_path, encoding="utf-8") as fh:
            provenance = json.load(fh)
    except (OSError, ValueError) as exc:
        raise RuntimeError(
            f"cache manifest unreadable at {prov_path!r}: {exc}. "
            "Refusing to reuse the cache."
        ) from exc

    esperado = str(((provenance or {}).get("artifact") or {}).get("manifest_sha256") or "").strip()
    if not esperado:
        raise RuntimeError(
            f"cache manifest at {prov_path!r} records no artifact.manifest_sha256. "
            "Regenerate it with scripts/build/build_ui_cache.py --base adaptada."
        )

    try:
        man_stat = os.stat(man_path)
    except OSError as exc:
        raise RuntimeError(
            f"cannot verify cache manifest: {man_path!r} unreadable: {exc}"
        ) from exc
    leido = _sha256_cached(man_path, int(man_stat.st_size), int(man_stat.st_mtime_ns))
    if leido is None:
        raise RuntimeError(
            f"cannot verify cache manifest: {man_path!r} unreadable."
        )
    leido = str(leido).strip()
    if leido != esperado:
        raise RuntimeError(
            f"cache manifest stale: manifest_sha256 recorded={esperado} but "
            f"{man_path!r} on disk has sha256={leido}. "
            "Regenerate the cache with scripts/build/build_ui_cache.py --base adaptada."
        )
    return provenance


def cache_available() -> bool:
    """True si existen los tres ficheros de caché (ventanas, filas, provenance).

    La app lo consulta al arrancar para mostrar un mensaje útil en vez de
    romper si la caché no se generó (`scripts/build/build_ui_cache.py`).

    Verificación: cuando el manifest registra hashes (source.h5_sha256 y
    counts.windows_sha256/rows_sha256), los compara con los ficheros en
    disco; si difieren, la caché está corrupta o sustituida y devuelve
    False. Manifests antiguos sin hashes siguen valiendo con la sola
    existencia de ficheros (compatibilidad hacia atrás).
    """
    if not all(os.path.exists(p) for p in (WINDOWS_PATH, ROWS_PATH, PROVENANCE_PATH)):
        return False
    try:
        with open(PROVENANCE_PATH, encoding="utf-8") as fh:
            provenance = json.load(fh)
    except (OSError, ValueError):
        return False
    # CACHE-DRIFT-01: un manifest_sha256 stale cierra la puerta sin reutilizar.
    try:
        verify_cache_manifest()
    except RuntimeError:
        return False
    counts = provenance.get("counts") or {}
    # Orden estable ya garantizado al construir; aquí solo se firma contenido.
    for path, key in ((WINDOWS_PATH, "windows_sha256"), (ROWS_PATH, "rows_sha256")):
        esperado = counts.get(key)
        if not esperado:
            continue
        try:
            actual = _sha256_cached(path, int(os.path.getsize(path)), int(os.stat(path).st_mtime_ns))
        except OSError:
            return False
        # _sha256_cached es un cache_data: en tests sin runtime de Streamlit
        # devuelve la función envuelta; asegurar comparación robusta.
        try:
            actual_str = str(actual).strip()
        except Exception:
            return False
        if actual_str != str(esperado).strip():
            return False
    return True


# ------------------------------------------------------- cache / artifact seal
@st.cache_data(ttl=3600, show_spinner=False)
def _sha256_cached(path: str, _size: int, _mtime_ns: int) -> str | None:
    """SHA-256 de un fichero, cacheado y atado a su contenido.

    La clave incluye tamaño y mtime: si el artefacto se sustituye en disco, la
    clave cambia y el hash se recalcula; si no, cada render reutiliza el digest
    en vez de releer el fichero.
    """
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(HASH_CHUNK), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def artifact_hash_check(provenance: dict) -> dict:
    """Compare the recorded ensemble hash with models/ensemble.joblib on disk.

    Returns {"checked": bool, "ok": bool, "esperado": str|None, "leido": str|None}
    with the full hex digests. Any unreadable input (missing artifact, truncated
    manifest, unreadable file) returns checked=False instead of raising, because
    a stale cache must warn the operator, never crash the render.

    Why this exists: `app/cache/cache_manifest.json` records
    `artifact.ensemble_sha256` and the surface displays it, but nothing compared
    it with the bundle actually on disk. Retrain and replace
    `models/ensemble.joblib` without rebuilding the cache and the screen keeps
    showing predictions of the new bundle under the seal of the old one.
    """
    try:
        artifact = (provenance or {}).get("artifact") or {}
        esperado = artifact.get("ensemble_sha256") or ""
    except AttributeError:
        # Un `provenance` que no es un dict (None incluido) no es un sello roto,
        # es una procedencia que no se puede leer: avisa, no tira la pagina.
        return {"checked": False, "ok": False, "esperado": None, "leido": None}
    esperado = str(esperado).strip()
    if not esperado:
        return {"checked": False, "ok": False, "esperado": None, "leido": None}

    try:
        st_file = os.stat(ARTIFACT_PATH)
    except OSError:
        return {"checked": False, "ok": False, "esperado": esperado, "leido": None}
    leido = _sha256_cached(
        ARTIFACT_PATH, int(st_file.st_size), int(st_file.st_mtime_ns)
    )
    if leido is None:
        return {"checked": False, "ok": False, "esperado": esperado, "leido": None}
    return {"checked": True, "ok": leido == esperado,
            "esperado": esperado, "leido": leido}


# ---------------------------------------------------------------------- policy
def classify(lower: float, airworthy: float = DEFAULT_AIRWORTHY,
             aog: float = DEFAULT_AOG) -> str:
    """Maintenance state from the conformal LOWER bound, never the point estimate.

    The threshold pair is a decision, not a default: see ADR-013. A rule whose
    airworthy band starts above the largest achievable lower bound (≈ 36 on this
    split) would never turn green, which is why the defaults are 25 / 20.
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



# ---------------------------------------------------------------------- curves
def unit_curve(windows: pd.DataFrame, unit: int) -> pd.DataFrame:
    """Per-cycle series for one engine.

    The model scores a window every `step` rows, so a cycle carries many
    predictions. The chart draws the mean and the panel decides on the worst
    (lowest) lower bound; both are kept so the difference stays visible.
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


def _state_at_cycle(at_cycle: pd.DataFrame, lower: float,
                   airworthy: float, aog: float) -> tuple[str, str]:
    """Estado del ciclo y la regla que lo decidio.

    Cuando el frame trae la pasada A (`decision` / `regla_decision`, de
    `rules.decidir_ventanas`), el estado se toma del motor `mia/` en la fila
    mas restrictiva del ciclo. Si no la trae, se reclasifica el limite inferior
    como siempre: el cargador sigue siendo usable sin la capa de reglas.
    """
    if "decision" in at_cycle.columns and len(at_cycle):
        fila = at_cycle.loc[at_cycle["lower"].idxmin()]
        estado = str(fila["decision"])
        if estado in STATE_LABELS:
            return estado, str(fila.get("regla_decision", ""))
    return classify(lower, airworthy, aog), ""


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
                "rule": "", "start_index": None, "life": last,
            })
            continue
        scored = min(int(cycle), last)
        at_cycle = frame[frame["cycle"] == scored]
        lower = float(at_cycle["lower"].min())
        state, rule = _state_at_cycle(at_cycle, lower, airworthy, aog)
        # La ventana que decide es la de menor limite inferior: se guarda su
        # posicion para que la orden pueda citar el dato, no solo el ciclo.
        peor = at_cycle.loc[at_cycle["lower"].idxmin()]
        start_index = (int(peor["start_index"]) if "start_index" in at_cycle.columns
                       else -1)
        rows.append({
            "unit": int(unit), "cycle": int(cycle), "scored_cycle": scored,
            "clamped": scored != int(cycle), "reached": True,
            "y_true": float(at_cycle["y_true"].mean()),
            "pred": float(at_cycle["pred"].mean()),
            "lower": lower,
            "upper": float(at_cycle["upper"].max()),
            "state": state,
            "action": ACTIONS[state],
            "rule": rule,
            "start_index": start_index,
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


def first_alarm_cycle(curve: pd.DataFrame, aog: float = DEFAULT_AOG,
                      statistic: str = "lower_min") -> tuple[int | None, int | None]:
    """Cycles where the lower bound crosses AOG, and where truth crosses it.

    Reported together so a reader can see how early the alarm fires rather than
    being told the band is "conservative".

    The statistic defaults to the cycle's **lowest** lower bound, which is the
    same one `fleet_snapshot` uses to decide: the alarm and the state must not
    answer "did it cross?" with different numbers. The mean is still available
    for a chart line, but a mean that stays above the threshold while the worst
    window is below it would hide the decision the operator is looking at.
    """
    column = statistic if statistic in curve.columns else "lower"
    below = curve[curve[column] < aog]
    alarm = int(below["cycle"].iloc[0]) if not below.empty else None
    truth_below = curve[curve["y_true"] < aog]
    truth = int(truth_below["cycle"].iloc[0]) if not truth_below.empty else None
    return alarm, truth


# ------------------------------------------------------------------ work order
def work_order(snapshot: pd.DataFrame, provenance: dict,
               airworthy: float = DEFAULT_AIRWORTHY,
               aog: float = DEFAULT_AOG,
               banda: str = "artefacto (models/ds02_manifest.json)",
               correccion: str | None = None) -> dict:
    """JSON-ready order for the units grounded at the simulated cycle.

    The document states which reading produced it: `banda` names the calibration
    that set the limits and `correccion` the passes that moved the point. Without
    them an order built with the rules layer on is indistinguishable from one
    built on the raw cache.
    """
    blocked = snapshot[snapshot["state"] == AOG]
    units = []
    for _, row in blocked.iterrows():
        units.append({
            "unidad": int(row["unit"]),
            "estado": AOG,
            "regla": str(row.get("rule", "")),
            "ventana_evaluada": {
                "filas": int(provenance["source"]["window"]),
                "step": int(provenance["source"]["step"]),
                "ciclo": int(row["scored_cycle"]),
                "start_index": int(row.get("start_index", -1)),
                "ventanas_en_ciclo": int(row.get("windows", 0)),
            },
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
        "banda": banda,
        "correccion": correccion or "ninguna (lectura cruda de la caché)",
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
    columns = ["unidad", "estado", "regla", "ciclo_simulado", "ciclo_evaluado",
               "rul_estimada", "limite_inferior", "limite_superior", "rul_real",
               "motivo", "accion"]
    if not order["unidades"]:
        return ",".join(columns) + "\n"
    frame = pd.DataFrame(order["unidades"])
    # La orden de una unidad externa no trae `rul_real` (no hay verdad): la
    # columna se emite vacía en vez de romper el documento.
    for column in columns:
        if column not in frame.columns:
            frame[column] = ""
    return frame[columns].to_csv(index=False)


def parte_disponibilidad(snapshot: pd.DataFrame, provenance: dict,
                        airworthy: float = DEFAULT_AIRWORTHY,
                        aog: float = DEFAULT_AOG) -> dict:
    """Parte firmable cuando ninguna unidad está en hangar (también se audita).

    La orden solo lista bloqueos; este parte deja constancia de que se miró la
    flota entera y no había nada que derivar, con los mismos umbrales, banda y
    huella que una orden. JSON-serializable, como `work_order`.
    """
    filas = []
    for _, row in snapshot.iterrows():
        filas.append({
            "unidad": int(row["unit"]),
            "estado": str(row["state"]),
            "regla": str(row.get("rule", "")),
            "ciclo_simulado": int(row["cycle"]),
            "ciclo_evaluado": (None if pd.isna(row["scored_cycle"])
                                else int(row["scored_cycle"])),
            "rul_estimada": (None if pd.isna(row["pred"])
                              else round(float(row["pred"]), 2)),
            "limite_inferior": (None if pd.isna(row["lower"])
                                 else round(float(row["lower"]), 2)),
            "limite_superior": (None if pd.isna(row["upper"])
                                 else round(float(row["upper"]), 2)),
        })
    return {
        "documento": "Parte de disponibilidad — flota sin derivaciones",
        "generado_en": pd.Timestamp.now().isoformat(timespec="seconds"),
        "dataset": "DS02",
        "artefacto_sha256": provenance["artifact"]["ensemble_sha256"],
        "umbrales": {"apto_si_limite_inferior_ge": airworthy,
                     "hangar_si_limite_inferior_lt": aog},
        "unidades": filas,
    }


def thresholds_from(airworthy: float, aog: float) -> dict:
    """Validate the operator's thresholds before they reach the policy."""
    if not (0.0 <= aog < airworthy):
        raise ValueError(
            f"umbral inválido: se requiere 0 <= hangar < apto, recibido "
            f"hangar={aog}, apto={airworthy}"
        )
    return {"airworthy": float(airworthy), "aog": float(aog)}
