"""Ingesta de N-CMAPSS DS02.

Si el HDF5 no se resuelve, se lanza un error que dice qué rutas se buscaron. No
se sustituye por otro dataset: un respaldo silencioso podría entrenar un modelo
de otro paradigma y sobrescribir el artefacto DS02 en la misma ruta.
"""
from __future__ import annotations

import logging
import os

import h5py
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Raíz del repo: src/ds02_rul/data.py está tres niveles por debajo.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DS02_CANDIDATE_PATHS = (
    # archive/ (y su CCMaps/) se retiro el 2026-11-09 a un backup externo:
    # solo se mantienen rutas que pueden existir en este repo.
    "data/raw/N-CMAPSS_DS02-006.h5",
    "N-CMAPSS_DS02-006.h5",
)

DEV_KEYS = ("A_dev", "W_dev", "X_s_dev", "Y_dev")
TEST_KEYS = ("A_test", "W_test", "X_s_test", "Y_test")

# Contrato compartido por el bundle C y la evidencia de clase. El dueño es
# este módulo: ni `clase` ni `ds02_rul` vuelven a definir estas listas.
OP_COLS = ["alt", "Mach", "TRA", "T2"]
SENSOR_COLS = [
    "T24", "T30", "T48", "T50", "P15", "P2", "P21", "P24",
    "Ps30", "P40", "P50", "Nf", "Nc", "Wf",
]

FIT_UNITS = [2.0, 5.0, 10.0, 18.0, 20.0]
HOLDOUT_UNITS = [16.0]
TEST_UNITS = [11.0, 14.0, 15.0]
TRAIN_UNITS = FIT_UNITS + HOLDOUT_UNITS


def resolve_ds02(path: str | None = None) -> str:
    """Devuelve la primera ruta DS02 existente o lanza un error explicativo."""
    candidates = (path,) if path else DS02_CANDIDATE_PATHS
    for candidate in candidates:
        if candidate and os.path.exists(candidate):
            return candidate
    raise FileNotFoundError(
        "N-CMAPSS DS02 HDF5 not found. Looked for:\n  "
        + "\n  ".join(str(c) for c in candidates)
        + "\nNo fallback is attempted: substituting another dataset "
        "could overwrite the DS02 artifact with a different-paradigm model."
    )


def load_ds02(path: str | None = None, stride: int = 100) -> dict:
    """Carga y submuestrea las particiones dev y test de DS02.

    Cada array se indexa con `[::stride]` para que unidad, ciclo, `W`, `Xs` y RUL
    sigan alineados por fila. No se aplica el recorte de 125 ciclos: truncaría
    los objetivos DS02 sin avisar.
    """
    resolved = resolve_ds02(path)
    with h5py.File(resolved, "r") as fh:
        missing = [k for k in DEV_KEYS + TEST_KEYS if k not in fh]
        if missing:
            raise KeyError(f"{resolved} is missing required datasets: {missing}")
        data = {k: fh[k][::stride] for k in DEV_KEYS + TEST_KEYS}
        op_names = [v.decode() if isinstance(v, bytes) else str(v) for v in fh["W_var"]]
        sensor_names = [v.decode() if isinstance(v, bytes) else str(v) for v in fh["X_s_var"]]

    # -- Ingestion asserts (shapes alineadas, finito, ciclos no decrecientes) --
    def _check_split(name: str, A: np.ndarray, W: np.ndarray, Xs: np.ndarray, Y: np.ndarray) -> None:
        n = len(A)
        assert len(W) == n and len(Xs) == n and len(Y) == n, (
            f"{name}: shapes no alineados A={A.shape} W={W.shape} Xs={Xs.shape} Y={Y.shape}"
        )
        assert A.ndim == 2 and A.shape[1] >= 2, f"{name}: A debe ser (n, >=2), got {A.shape}"
        assert len(op_names) == W.shape[1], f"{name}: op_names={len(op_names)} vs W ncols={W.shape[1]}"
        assert len(sensor_names) == Xs.shape[1], (
            f"{name}: sensor_names={len(sensor_names)} vs Xs ncols={Xs.shape[1]}"
        )
        # isfinite global: ningún NaN/inf en la telemetría ni en A/Y
        for label, arr in (("A", A), ("W", W), ("Xs", Xs), ("Y", Y)):
            arr_f = np.asarray(arr, dtype=np.float64)
            n_nan = int(np.isnan(arr_f).sum())
            n_inf = int(np.isinf(arr_f).sum())
            if n_nan or n_inf:
                logger.warning("%s: %s tiene nulos=%d inf=%d (de %d)", name, label, n_nan, n_inf, arr_f.size)
            assert np.isfinite(arr_f).all(), (
                f"{name}: {label} contiene no-finitos (nan={n_nan}, inf={n_inf}); ingesta DS02 exige datos finitos"
            )
        logger.info("%s: n=%d nulos=0 (A/W/Xs/Y alineados)", name, n)
        # cycle no decreciente por unidad (A[:,0]=unit, A[:,1]=cycle)
        for unit in np.unique(A[:, 0]):
            cycles = A[A[:, 0] == unit, 1]
            assert np.all(np.diff(cycles) >= 0), (
                f"{name}: cycle decreciente para unit={float(unit)}; el ciclo debe ser no decreciente por unidad"
            )

    _check_split("train", np.asarray(data["A_dev"]), np.asarray(data["W_dev"]), np.asarray(data["X_s_dev"]), np.asarray(data["Y_dev"]))  # type: ignore[arg-type]
    _check_split("test", np.asarray(data["A_test"]), np.asarray(data["W_test"]), np.asarray(data["X_s_test"]), np.asarray(data["Y_test"]))  # type: ignore[arg-type]

    return {
        "path": resolved,
        "stride": stride,
        "op_names": op_names,
        "sensor_names": sensor_names,
        "A_train": data["A_dev"],
        "W_train": data["W_dev"],
        "Xs_train": data["X_s_dev"],
        "y_train": data["Y_dev"].ravel(),
        "A_test": data["A_test"],
        "W_test": data["W_test"],
        "Xs_test": data["X_s_test"],
        "y_test": data["Y_test"].ravel(),
    }


def medianas_train(df_train: pd.DataFrame, columnas: list[str] | None = None) -> pd.Series:
    """Medianas calculadas SOLO en train (sin fuga)."""
    cols = list(columnas) if columnas else list(SENSOR_COLS)
    return df_train[cols].median(numeric_only=True)


def imputar_ffill(
    df: pd.DataFrame,
    medianas: pd.Series | None = None,
    columnas: list[str] | None = None,
) -> tuple[pd.DataFrame, pd.Series]:
    """ffill causal por unidad en orden temporal + mediana de train.

    Si `medianas` es None se calculan sobre el propio df (SOLO válido para
    train; en test DEBEN pasarse las de train).
    """
    cols = list(columnas) if columnas else list(SENSOR_COLS)
    orden = df.sort_values(["unit", "cycle"]).reset_index(drop=True)
    if medianas is None:
        medianas = medianas_train(orden, cols)
    out = orden.copy()
    out[cols] = out.groupby("unit", sort=False)[cols].ffill()
    out[cols] = out[cols].fillna(medianas)
    return out, medianas


def construir_raw_adaptado() -> dict:
    """Parquet MAR-imputado -> dict raw alineado (mismo shape que `load_ds02`).

    Re-imputa con medianas SOLO de fit-units (no las de dev-completo del
    track de clase): es lo que mantiene el protocolo honesto del bundle C.
    Vive aquí porque es el contrato de entrada del bundle, no lógica de clase.
    """
    train_con = pd.read_parquet(
        os.path.join(REPO_ROOT, "data", "processed", "train_con_nulos.parquet")
    )
    test_con = pd.read_parquet(
        os.path.join(REPO_ROOT, "data", "processed", "test_con_nulos.parquet")
    )
    fit_mask = train_con["unit"].isin(FIT_UNITS)
    medianas_fit = medianas_train(train_con.loc[fit_mask], SENSOR_COLS)

    train_imp, _ = imputar_ffill(train_con, medianas_fit, SENSOR_COLS)
    test_imp, _ = imputar_ffill(test_con, medianas_fit, SENSOR_COLS)

    def bloque(df: pd.DataFrame) -> dict:
        """Convierte un parquet imputado al formato crudo adaptado de DS02."""
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
