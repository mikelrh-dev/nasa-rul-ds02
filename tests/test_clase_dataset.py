"""Tests del dataset de clase: causalidad del ffill y pureza de fase_vuelo."""

import numpy as np
import pandas as pd

from src.clase.dataset_clase import (
    asignar_fase_vuelo,
    elegibles_mar,
    imputar_ffill,
    inyectar_nulos,
    inyectar_nulos_mar,
    rachas_nulos,
    split_por_unidad,
)


def _toy() -> pd.DataFrame:
    return pd.DataFrame({
        "unit": [1.0] * 5 + [2.0] * 5,
        "cycle": [1, 2, 3, 4, 5] * 2,
        "alt": [5000.0] * 10,
        "Mach": [0.4] * 10,
        "TRA": [50.0] * 10,
        "T2": [500.0] * 10,
        "T24": [100.0, 101.0, 102.0, 103.0, 104.0, 200.0, 201.0, 202.0, 203.0, 204.0],
        "RUL": [50, 49, 48, 47, 46, 60, 59, 58, 57, 56],
    })


def test_ffill_no_mira_futuro_ni_otras_unidades():
    df = _toy()
    df.loc[2, "T24"] = np.nan  # unidad 1, ciclo 3 → debe valer 101.0 (anterior)
    df.loc[5, "T24"] = np.nan  # unidad 2, ciclo 1 → sin pasado, usa mediana train
    out, med = imputar_ffill(df, columnas=["T24"])
    assert out.loc[2, "T24"] == 101.0
    assert out.loc[5, "T24"] == float(med["T24"])
    # No contamina la otra unidad
    assert out.loc[6, "T24"] == 201.0


def test_inyeccion_no_toca_unit_cycle_rul():
    df = _toy()
    iny, audit = inyectar_nulos(df, columnas=["T24"], tasa=0.5, seed=0)
    assert iny["unit"].equals(df["unit"])
    assert iny["cycle"].equals(df["cycle"])
    assert iny["RUL"].equals(df["RUL"])
    assert audit["filas_con_algun_nulo"] > 0


def test_fase_vuelo_solo_regimen():
    df = pd.DataFrame({
        "unit": [1.0, 1.0, 1.0],
        "alt": [5000.0, 35000.0, 20000.0],
        "Mach": [0.4, 0.8, 0.5],
    })
    out = asignar_fase_vuelo(df)
    assert list(out["fase_vuelo"]) == ["Ascenso", "Crucero", "Descenso"]


def test_mar_solo_en_crucero_alto_y_solo_t30():
    df = pd.DataFrame({
        "unit": [1.0] * 6,
        "cycle": [1, 2, 3, 4, 5, 6],
        "alt": [35000.0, 35000.0, 15000.0, 15000.0, 35000.0, 35000.0],
        "Mach": [0.72, 0.72, 0.5, 0.5, 0.72, 0.72],
        "T30": [100.0] * 6,
        "T48": [200.0] * 6,
    })
    iny, audit = inyectar_nulos_mar(df, tasa_elegible=1.0, seed=0,
                                     alt_min=27000.0, mach_min=0.68)
    # Solo filas elegibles (crucero alto) quedan a NaN, y solo T30
    assert iny["T48"].isna().sum() == 0
    assert iny.loc[2, "T30"] == 100.0 and iny.loc[3, "T30"] == 100.0
    assert audit["nulos_inyectados"] == 4
    assert audit["tasa_global_T30"] > 0
    r = rachas_nulos(iny)
    assert r["max_racha_por_unidad"][1.0] >= 2


def test_split_por_unidad_sin_solape():
    df = _toy()
    df["unit"] = [11.0] * 5 + [2.0] * 5
    train, test = split_por_unidad(df, test_units=[11.0])
    assert set(train["unit"].unique()) == {2.0}
    assert set(test["unit"].unique()) == {11.0}
