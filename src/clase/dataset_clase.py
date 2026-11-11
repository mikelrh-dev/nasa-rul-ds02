"""Dataset de clase DS02 (track `src/clase/`, change 2026-11-02-clase-track).

Pipeline congelado (`src/ds02_rul/`, `models/`, `app/cache/`) SOLO lectura.
Este módulo construye el dataset tabular de clase a nivel de fila
downsampleada (`STRIDE=100`, como `load_ds02`).

**Uso real:** solo `elegibles_mar` lo importa un notebook (NB01). El resto de
funciones son el material didáctico del SAA 5 y las cubren los tests; el modelo
C no las usa. No borrar: el README de `src/clase/` las documenta como pasos.

    unit, cycle, alt, Mach, TRA, T2, 14 sensores, RUL + fase_vuelo

Pasos (documentados para SAA 5):
1. `build_clase_frame(raw)` — DataFrame desde `load_ds02` (train=dev, test=test).
2. `inyectar_nulos_mar` — MAR ~2% SOLO en T30 cuando alt>27_000 y Mach>0.68
   (crucero alto DS02; el 30k/0.8 teorico no existe: Mach max 0.74).
   Simula dropout de sonda por altitud. Seed fija, mask auditable.
   `inyectar_nulos` generica (MCAR) queda como compatibilidad.
   Nunca tocan unit/cycle/RUL/fase_vuelo.
3. `imputar_ffill` — causal por unidad en orden temporal + mediana de TRAIN
   para el primer NaN de cada unidad. Las medianas se calculan SOLO en train.
4. `asignar_fase_vuelo` — SOLO desde `alt`/`Mach` (régimen, no sensores ni RUL).
5. `split_por_unidad` — train/test por motor, nunca aleatorio por fila.

Justificación negocio: la pérdida EM llega por ráfagas; el "último valor
conocido del motor" es lo que un ingeniero haría en pista.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if os.path.join(_ROOT, "src") not in sys.path:
    sys.path.insert(0, os.path.join(_ROOT, "src"))

# Reexportados desde ds02_rul.data: el dueño del esquema y de la imputación es
# el contrato compartido, no el track de clase.
from ds02_rul.data import (  # noqa: E402
    OP_COLS,
    SENSOR_COLS,
    TEST_UNITS,
    TRAIN_UNITS,
    imputar_ffill,
    medianas_train,
)

TASA_DEFECTO = 0.03  # legado MCAR; el flujo oficial usa MAR_T30_* (abajo)
SEED_DEFECTO = 42
MAR_SENSOR = "T30"
MAR_ALT_MIN = 27_000.0
MAR_MACH_MIN = 0.68
MAR_TASA_ELEGIBLE = 0.10  # ~10% de elegibles ~= ~2.1% global en T30
MAR_SEED = 7


def build_clase_frame(raw: dict) -> pd.DataFrame:
    """Une dev+test downsampleados en un DataFrame con RUL."""
    frames = []
    for suf, key in (("train", "train"), ("test", "test")):
        a = raw[f"A_{key}"]
        w = raw[f"W_{key}"]
        xs = raw[f"Xs_{key}"]
        y = raw[f"y_{key}"]
        df = pd.DataFrame(
            np.hstack([a[:, [0, 1]], w, xs]),
            columns=["unit", "cycle"] + OP_COLS + SENSOR_COLS,
        )
        df["RUL"] = np.asarray(y, dtype=float)
        df["split_origen"] = suf
        frames.append(df)
    out = pd.concat(frames, ignore_index=True)
    return out.sort_values(["unit", "cycle"]).reset_index(drop=True)


def inyectar_nulos(
    df: pd.DataFrame,
    columnas: list[str] | None = None,
    tasa: float = TASA_DEFECTO,
    seed: int = SEED_DEFECTO,
) -> tuple[pd.DataFrame, dict]:
    """Inyecta MCAR en sensores. Devuelve (df_inyectado, auditoría)."""
    cols = list(columnas) if columnas else list(SENSOR_COLS)
    rng = np.random.default_rng(seed)
    mask = rng.random((len(df), len(cols))) < float(tasa)
    out = df.copy()
    out[cols] = out[cols].mask(pd.DataFrame(mask, columns=cols, index=df.index))
    audit = {
        "mecanismo": "MCAR-legado",
        "tasa_pedida": float(tasa),
        "tasa_real": float(mask.mean()),
        "seed": int(seed),
        "columnas": cols,
        "nulos_por_col": {c: int(out[c].isna().sum()) for c in cols},
        "filas_con_algun_nulo": int(out[cols].isna().any(axis=1).sum()),
    }
    return out, audit


def elegibles_mar(df: pd.DataFrame, alt_min: float = MAR_ALT_MIN, mach_min: float = MAR_MACH_MIN) -> pd.Series:
    """Filas en crucero alto DS02 donde la sonda T30 puede caer (MAR)."""
    cond = (pd.to_numeric(df["alt"], errors="coerce") > float(alt_min)) & (
        pd.to_numeric(df["Mach"], errors="coerce") > float(mach_min)
    )
    return cond.fillna(False)


def rachas_nulos(df: pd.DataFrame, columna: str = MAR_SENSOR) -> dict:
    """Rachas de nulos consecutivos por unidad (para R1: >3 ciclos seguidos)."""
    out = {}
    for u, g in df.sort_values(["unit", "cycle"]).groupby("unit"):
        v = g[columna].isna().to_numpy()
        best, cur = 0, 0
        for x in v:
            cur = cur + 1 if x else 0
            best = max(best, cur)
        out[float(u)] = int(best)
    return {
        "max_racha_por_unidad": out,
        "unidades_con_mas_de_3_seguidos": int(sum(1 for k, v in out.items() if v > 3)),
    }


def inyectar_nulos_mar(
    df: pd.DataFrame,
    sensor: str = MAR_SENSOR,
    tasa_elegible: float = MAR_TASA_ELEGIBLE,
    seed: int = MAR_SEED,
    alt_min: float = MAR_ALT_MIN,
    mach_min: float = MAR_MACH_MIN,
) -> tuple[pd.DataFrame, dict]:
    """MAR realista: dropout de T30 SOLO en crucero alto (alt/Mach).

    `tasa_elegible` es P(nulo | elegible); la tasa global en T30 sale ~2%.
    Documentado como test de robustez AC 20-170: el modelo debe degradar
    <5% RMSE y activar R1 si faltan >3 ciclos seguidos.
    """
    eleg = elegibles_mar(df, alt_min, mach_min).to_numpy()
    rng = np.random.default_rng(seed)
    hit = (rng.random(len(df)) < float(tasa_elegible)) & eleg
    out = df.copy()
    out.loc[hit, sensor] = np.nan
    rachas = rachas_nulos(out, sensor)
    audit = {
        "mecanismo": "MAR-altitud",
        "sensor": sensor,
        "condicion": f"alt>{alt_min:g} & Mach>{mach_min:g}",
        "tasa_elegible_pedida": float(tasa_elegible),
        "seed": int(seed),
        "filas_elegibles": int(eleg.sum()),
        "nulos_inyectados": int(hit.sum()),
        "tasa_global_T30": float(hit.mean()),
        "tasa_en_elegibles": float(hit[eleg].mean()) if eleg.any() else 0.0,
        "nulos_por_col": {sensor: int(hit.sum())},
        "filas_con_algun_nulo": int(hit.sum()),
        **rachas,
    }
    return out, audit


def asignar_fase_vuelo(df: pd.DataFrame) -> pd.DataFrame:
    """Categórica de régimen SOLO desde alt/Mach (no sensores, no RUL).

    Umbrales calibrados a DS02 downsampleado (alt p25=16.4k, p50=23k,
    p75=27.9k; teoricos 10k/30k dejaban Ascenso en 0% y Crucero en 5%).
    - alt < 18_000 → Ascenso
    - alt > 26_000 y Mach > 0.65 → Crucero
    - resto → Descenso; caída >2000 ft en 3 filas de la misma unidad → Descenso
    """
    out = df.copy()
    alt = pd.to_numeric(out["alt"], errors="coerce").to_numpy(dtype=float)
    mach = pd.to_numeric(out["Mach"], errors="coerce").to_numpy(dtype=float)
    fase = np.where(
        alt < 18_000, "Ascenso",
        np.where((alt > 26_000) & (mach > 0.65), "Crucero", "Descenso"),
    )
    # Caída brusca: override a Descenso (causal, solo pasado de la misma unidad)
    s_alt = pd.Series(alt, index=out.index)
    caida = s_alt.groupby(out["unit"]).diff(3).to_numpy(dtype=float)
    fase = np.where(caida < -2000.0, "Descenso", fase)
    out["fase_vuelo"] = fase
    return out


def split_por_unidad(
    df: pd.DataFrame,
    test_units: list[float] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Partición por motor (sin fuga entre ventanas del mismo motor)."""
    tst = list(test_units) if test_units is not None else list(TEST_UNITS)
    test = df[df["unit"].isin(tst)].reset_index(drop=True)
    train = df[~df["unit"].isin(tst)].reset_index(drop=True)
    return train, test
