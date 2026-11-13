"""Tests del dataset de clase: builder, causalidad del ffill y fase_vuelo."""

import hashlib
import json

import numpy as np
import pandas as pd

from src.clase.dataset_clase import (
    ARTEFACTOS,
    MANIFIESTO,
    asignar_fase_vuelo,
    construir_artefactos_clase,
    elegibles_mar,
    imputar_ffill,
    inyectar_nulos,
    inyectar_nulos_mar,
    rachas_nulos,
    split_por_unidad,
    verificar_manifiesto,
)
from src.ds02_rul.data import SENSOR_COLS


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
    assert audit["mascara_version"] == 1
    pares = audit["mascara_columnas"]["T30"]
    assert len(pares) == audit["nulos_inyectados"] == 4
    assert len({p[0] for p in pares}) == len(pares)
    assert all(len(p) == 3 for p in pares)
    canon = json.dumps(
        audit["mascara_columnas"], sort_keys=True, separators=(",", ":"),
        ensure_ascii=False,
    )
    assert audit["mascara_sha256"] == hashlib.sha256(canon.encode("utf-8")).hexdigest()
    r = rachas_nulos(iny)
    assert r["max_racha_por_unidad"][1.0] >= 2


def test_split_por_unidad_sin_solape():
    df = _toy()
    df["unit"] = [11.0] * 5 + [2.0] * 5
    train, test = split_por_unidad(df, test_units=[11.0])
    assert set(train["unit"].unique()) == {2.0}
    assert set(test["unit"].unique()) == {11.0}


def _raw_toy() -> dict:
    """Dict con la misma forma que `load_ds02`, sin tocar el HDF5."""

    def bloque(units, cycles):
        n = len(units)
        A = np.column_stack(
            [np.asarray(units, dtype=float), np.asarray(cycles, dtype=float)]
        )
        W = np.zeros((n, 4), dtype=float)
        W[:, 0] = 30_000.0  # alt: crucero alto, elegible para MAR
        W[:, 1] = 0.70     # Mach: elegible para MAR
        W[:, 2] = 50.0     # TRA
        W[:, 3] = 500.0    # T2
        Xs = np.full((n, 14), 100.0)
        y = np.arange(n, 0, -1, dtype=float)
        return A, W, Xs, y

    A_tr, W_tr, Xs_tr, y_tr = bloque([1, 1, 1, 2, 2, 2], [0, 1, 2, 0, 1, 2])
    A_te, W_te, Xs_te, y_te = bloque([11, 11, 11], [0, 1, 2])
    return {
        "A_train": A_tr, "W_train": W_tr, "Xs_train": Xs_tr, "y_train": y_tr,
        "A_test": A_te, "W_test": W_te, "Xs_test": Xs_te, "y_test": y_te,
    }


def _hashes(directorio) -> dict:
    return {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in directorio.iterdir()
        if p.is_file()
    }


def test_builder_escribe_artefactos_con_esquema(tmp_path):
    out = tmp_path / "processed"
    res = construir_artefactos_clase(raw=_raw_toy(), out_dir=str(out))

    for nombre in ARTEFACTOS + ("auditoria_nulos.json",):
        assert (out / nombre).exists(), nombre

    train = pd.read_parquet(out / "train.parquet")
    test = pd.read_parquet(out / "test.parquet")
    assert {"fase_vuelo", "RUL", "split_origen"} <= set(train.columns)
    assert set(train["unit"].unique()) == {1.0, 2.0}
    assert set(test["unit"].unique()) == {11.0}
    # La base imputada no debe conservar nulos de sensor.
    assert int(train[SENSOR_COLS].isna().sum().sum()) == 0
    assert int(test[SENSOR_COLS].isna().sum().sum()) == 0
    assert train["fase_vuelo"].notna().all()

    X = pd.read_parquet(out / "X_train.parquet")
    y = pd.read_parquet(out / "y_train.parquet")
    assert list(X.columns) == [
        c for c in train.columns if c not in ("RUL", "split_origen")
    ]
    assert y["RUL"].tolist() == train["RUL"].tolist()
    assert res["auditoria"]["mecanismo"] == "MAR-altitud"


def test_builder_escribe_manifiesto_y_fast_check(tmp_path):
    out = tmp_path / "processed"
    res = construir_artefactos_clase(raw=_raw_toy(), out_dir=str(out))

    ruta = out / MANIFIESTO
    assert ruta.exists()
    manifiesto = json.loads(ruta.read_text(encoding="utf-8"))
    assert manifiesto["format_version"] == 1
    assert set(manifiesto["artefactos"]) == set(ARTEFACTOS)
    assert manifiesto["mascara_sha256"] == res["auditoria"]["mascara_sha256"]
    assert verificar_manifiesto(str(out))["ok"]


def test_fast_check_detecta_parquet_manipulado(tmp_path):
    out = tmp_path / "processed"
    construir_artefactos_clase(raw=_raw_toy(), out_dir=str(out))

    ruta = out / "train.parquet"
    datos = bytearray(ruta.read_bytes())
    datos[-1] ^= 0xFF
    ruta.write_bytes(datos)

    informe = verificar_manifiesto(str(out))
    assert not informe["ok"]
    assert any("train.parquet" in d for d in informe["diferencias"])


def test_fast_check_sin_manifiesto(tmp_path):
    informe = verificar_manifiesto(str(tmp_path))
    assert not informe["ok"]
    assert any(MANIFIESTO in d for d in informe["diferencias"])


def test_builder_es_idempotente(tmp_path):
    out = tmp_path / "processed"
    construir_artefactos_clase(raw=_raw_toy(), out_dir=str(out))
    antes = _hashes(out)

    res = construir_artefactos_clase(raw=_raw_toy(), out_dir=str(out))

    assert res["escritos"] == []
    assert _hashes(out) == antes


def test_check_detecta_drift(tmp_path):
    out = tmp_path / "processed"
    construir_artefactos_clase(raw=_raw_toy(), out_dir=str(out))
    assert construir_artefactos_clase(
        raw=_raw_toy(), out_dir=str(out), check=True
    )["ok"]

    train = pd.read_parquet(out / "train.parquet")
    train.loc[0, "RUL"] = float(train.loc[0, "RUL"]) + 1.0
    train.to_parquet(out / "train.parquet", index=False)

    informe = construir_artefactos_clase(
        raw=_raw_toy(), out_dir=str(out), check=True
    )
    assert not informe["ok"]
    assert any("train.parquet" in d for d in informe["diferencias"])
