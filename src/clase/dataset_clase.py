"""Dataset de clase DS02 (track `src/clase/`, change 2026-11-02-clase-track).

Pipeline congelado (`src/ds02_rul/`, `models/`, `app/cache/`) SOLO lectura.
Este módulo construye el dataset tabular de clase a nivel de fila
downsampleada (`STRIDE=100`, como `load_ds02`).

**Uso real:** `elegibles_mar` lo importa NB01; `construir_artefactos_clase`
es el escritor oficial de `data/processed/` (`python -m src.clase.dataset_clase`).
El resto de funciones son los pasos que encadena el builder y los cubren los
tests. No borrar: el README de `src/clase/` las documenta como pasos.

    unit, cycle, alt, Mach, TRA, T2, 14 sensores, RUL + fase_vuelo

Pasos del proceso:
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
6. `construir_artefactos_clase` — ejecuta 1-5, escribe los 8 parquet +
   `auditoria_nulos.json` (con máscara MAR) + `dataset_manifest.json`; con
   `--check` reconstruye y compara contenido, y con `--fast-check` verifica
   los SHA de bytes sin cargar el HDF5.

Justificación negocio: la pérdida EM llega por ráfagas; el "último valor
conocido del motor" es lo que un ingeniero haría en pista.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile

import numpy as np
import pandas as pd
import pyarrow

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
    # Máscara semántica: [fila, unit, cycle] de cada muestra tocada. `unit` y
    # `cycle` solos NO identifican la fila: hay varias muestras por ciclo. El
    # índice de fila es el del frame de entrada (orden fijado por el builder),
    # y unit/cycle quedan para lectura humana. Ordenada por fila para que el
    # SHA sea estable.
    posiciones = np.flatnonzero(hit)
    pares = [
        [int(i), float(df.iloc[i]["unit"]), int(df.iloc[i]["cycle"])]
        for i in posiciones
    ]
    mascara_columnas = {sensor: pares}
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
        "mascara_version": 1,
        "mascara_columnas": mascara_columnas,
        "mascara_sha256": _sha256_json(mascara_columnas),
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


ARTEFACTOS = (
    "train_con_nulos.parquet",
    "test_con_nulos.parquet",
    "train.parquet",
    "test.parquet",
    "X_train.parquet",
    "X_test.parquet",
    "y_train.parquet",
    "y_test.parquet",
)
MANIFIESTO = "dataset_manifest.json"


def _sha256_fichero(ruta: str) -> str:
    """SHA-256 de los bytes de un fichero, leído por bloques."""
    h = hashlib.sha256()
    with open(ruta, "rb") as fh:
        for bloque in iter(lambda: fh.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _sha256_json(obj) -> str:
    """SHA-256 de un objeto JSON canónico (claves ordenadas, sin espacios)."""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _huella_contenido(df: pd.DataFrame) -> str:
    """SHA-256 del contenido, no de los bytes del parquet.

    Ordena por unidad/ciclo y hashea fila a fila con `hash_pandas_object`.
    Dos parquet equivalentes pueden diferir en metadata/compresión, así que el
    SHA del fichero no sirve como identidad. La huella es estable dentro de la
    versión de pandas que fija el repo.
    """
    claves = [c for c in ("unit", "cycle") if c in df.columns]
    orden = (
        df.sort_values(claves, kind="stable").reset_index(drop=True)
        if claves
        else df.reset_index(drop=True)
    )
    hashed = pd.util.hash_pandas_object(orden, index=False).to_numpy()
    return hashlib.sha256(hashed.tobytes()).hexdigest()


def _json_normalizado(obj: dict) -> dict:
    """Normaliza a JSON para comparar sin depender de formato ni claves float."""
    return json.loads(json.dumps(obj, ensure_ascii=False))


def _escribir_parquet_si_cambia(df: pd.DataFrame, ruta: str) -> bool:
    """Escribe solo si el contenido cambió. Devuelve True si escribió."""
    if os.path.exists(ruta):
        actual = pd.read_parquet(ruta)
        if _huella_contenido(actual) == _huella_contenido(df):
            return False
    df.to_parquet(ruta, index=False)
    return True


def _escribir_json_si_cambia(obj: dict, ruta: str) -> bool:
    """Escribe solo si el contenido cambió. Devuelve True si escribió."""
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as fh:
            if json.load(fh) == _json_normalizado(obj):
                return False
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    return True


def _construir_manifiesto(
    out_dir: str,
    salidas: dict[str, pd.DataFrame],
    audit: dict,
    medianas,
    test_units: list[float],
) -> dict:
    """Manifiesto golden: identidad de bytes + contenido + receta."""
    artefactos = {}
    for nombre, df_out in salidas.items():
        ruta = os.path.join(out_dir, nombre)
        artefactos[nombre] = {
            "sha256": _sha256_fichero(ruta),
            "huella_contenido": _huella_contenido(df_out),
            "filas": int(len(df_out)),
            "columnas": int(df_out.shape[1]),
        }
    return {
        "format_version": 1,
        "pandas": pd.__version__,
        "pyarrow": pyarrow.__version__,
        "artefactos": artefactos,
        "auditoria_sha256": _sha256_fichero(
            os.path.join(out_dir, "auditoria_nulos.json")
        ),
        "mascara_sha256": audit["mascara_sha256"],
        "receta": {
            "seed": int(MAR_SEED),
            "test_units": [float(u) for u in sorted(test_units)],
            "medianas": {c: float(v) for c, v in sorted(medianas.items())},
        },
    }


def verificar_manifiesto(out_dir: str = os.path.join("data", "processed")) -> dict:
    """Verifica el manifiesto y los artefactos sin cargar el HDF5."""
    ruta = os.path.join(out_dir, MANIFIESTO)
    if not os.path.exists(ruta):
        return {"ok": False, "diferencias": [f"{MANIFIESTO}: falta en {out_dir}"]}
    with open(ruta, encoding="utf-8") as fh:
        manifiesto = json.load(fh)

    diferencias: list[str] = []
    if manifiesto.get("format_version") != 1:
        diferencias.append(f"{MANIFIESTO}: format_version distinta de 1")
    artefactos = manifiesto.get("artefactos", {})
    if set(artefactos) != set(ARTEFACTOS):
        diferencias.append(f"{MANIFIESTO}: lista de artefactos distinta")
    for nombre in ARTEFACTOS:
        info = artefactos.get(nombre)
        if not info:
            diferencias.append(f"{nombre}: falta en {MANIFIESTO}")
            continue
        ruta_art = os.path.join(out_dir, nombre)
        if not os.path.exists(ruta_art):
            diferencias.append(f"{nombre}: falta")
            continue
        if _sha256_fichero(ruta_art) != info.get("sha256"):
            diferencias.append(f"{nombre}: sha256 distinto")

    ruta_audit = os.path.join(out_dir, "auditoria_nulos.json")
    if not os.path.exists(ruta_audit):
        diferencias.append("auditoria_nulos.json: falta")
    elif _sha256_fichero(ruta_audit) != manifiesto.get("auditoria_sha256"):
        diferencias.append("auditoria_nulos.json: sha256 distinto")
    else:
        with open(ruta_audit, encoding="utf-8") as fh:
            audit = json.load(fh)
        if audit.get("mascara_sha256") != manifiesto.get("mascara_sha256"):
            diferencias.append("auditoria_nulos.json: mascara_sha256 distinto")

    return {"ok": not diferencias, "diferencias": diferencias, "manifiesto": ruta}


def _comparar_artefactos(nuevo: str, referencia: str) -> dict:
    """Compara una reconstrucción con los artefactos de referencia."""
    diferencias: list[str] = []
    for nombre in ARTEFACTOS:
        ruta_nueva = os.path.join(nuevo, nombre)
        ruta_ref = os.path.join(referencia, nombre)
        if not os.path.exists(ruta_ref):
            diferencias.append(f"{nombre}: falta en {referencia}")
            continue
        try:
            pd.testing.assert_frame_equal(
                pd.read_parquet(ruta_nueva), pd.read_parquet(ruta_ref)
            )
        except AssertionError as exc:
            diferencias.append(f"{nombre}: {exc}")

    ruta_audit_nueva = os.path.join(nuevo, "auditoria_nulos.json")
    ruta_audit_ref = os.path.join(referencia, "auditoria_nulos.json")
    if not os.path.exists(ruta_audit_ref):
        diferencias.append(f"auditoria_nulos.json: falta en {referencia}")
    else:
        with open(ruta_audit_nueva, encoding="utf-8") as fh:
            audit_nuevo = json.load(fh)
        with open(ruta_audit_ref, encoding="utf-8") as fh:
            audit_ref = json.load(fh)
        if audit_nuevo != audit_ref:
            diferencias.append("auditoria_nulos.json: contenido distinto")

    # El manifiesto NO se compara aquí: guarda SHA de bytes y el parquet no es
    # canónico (reescribir el mismo DataFrame cambia los bytes). `--check`
    # compara contenido; `--fast-check` verifica la integridad de bytes.
    return {
        "ok": not diferencias,
        "diferencias": diferencias,
        "referencia": referencia,
    }


def construir_artefactos_clase(
    raw: dict | None = None,
    out_dir: str = os.path.join("data", "processed"),
    escribir: bool = True,
    check: bool = False,
    h5_path: str | None = None,
) -> dict:
    """Ejecuta el pipeline completo y escribe los artefactos de `data/processed/`.

    Orden exacto (el que produjo los parquet actuales):
    build_clase_frame -> inyectar_nulos_mar sobre el frame COMBINADO y ordenado
    -> split_por_unidad -> imputar_ffill con medianas SOLO de train ->
    asignar_fase_vuelo. Cambiar el orden cambia la máscara MAR.

    `check=True` reconstruye en un directorio temporal y compara con `out_dir`
    sin escribir nada. Devuelve un dict con `ok` y `diferencias`.
    """
    if raw is None:
        from ds02_rul.data import load_ds02

        raw = load_ds02(h5_path) if h5_path else load_ds02()

    df = build_clase_frame(raw)
    df_con, audit = inyectar_nulos_mar(df)
    # fase_vuelo también va en los parquet con nulos: se calcula antes del split.
    df_con = asignar_fase_vuelo(df_con)
    train_con, test_con = split_por_unidad(df_con)

    medianas = medianas_train(train_con)
    train, _ = imputar_ffill(train_con, medianas)
    test, _ = imputar_ffill(test_con, medianas)

    salidas = {
        "train_con_nulos.parquet": train_con,
        "test_con_nulos.parquet": test_con,
        "train.parquet": train,
        "test.parquet": test,
        "X_train.parquet": train.drop(columns=["RUL", "split_origen"]),
        "X_test.parquet": test.drop(columns=["RUL", "split_origen"]),
        "y_train.parquet": train[["RUL"]],
        "y_test.parquet": test[["RUL"]],
    }

    if check:
        with tempfile.TemporaryDirectory(prefix="ds02-clase-") as tmp:
            construir_artefactos_clase(raw=raw, out_dir=tmp, escribir=True)
            return _comparar_artefactos(tmp, out_dir)

    os.makedirs(out_dir, exist_ok=True)
    escritos: list[str] = []
    omitidos: list[str] = []
    manifiesto = None
    if escribir:
        for nombre, df_out in salidas.items():
            if _escribir_parquet_si_cambia(df_out, os.path.join(out_dir, nombre)):
                escritos.append(nombre)
            else:
                omitidos.append(nombre)
        if _escribir_json_si_cambia(
            audit, os.path.join(out_dir, "auditoria_nulos.json")
        ):
            escritos.append("auditoria_nulos.json")
        else:
            omitidos.append("auditoria_nulos.json")
        manifiesto = _construir_manifiesto(
            out_dir,
            salidas,
            audit,
            medianas,
            sorted(float(u) for u in test["unit"].unique()),
        )
        if _escribir_json_si_cambia(
            manifiesto, os.path.join(out_dir, MANIFIESTO)
        ):
            escritos.append(MANIFIESTO)
        else:
            omitidos.append(MANIFIESTO)

    return {
        "out_dir": out_dir,
        "filas": {nombre: int(len(df_out)) for nombre, df_out in salidas.items()},
        "unidades": {
            "train": sorted(float(u) for u in train["unit"].unique()),
            "test": sorted(float(u) for u in test["unit"].unique()),
        },
        "medianas": {c: float(v) for c, v in medianas.items()},
        "auditoria": audit,
        "manifiesto": manifiesto,
        "huellas": {nombre: _huella_contenido(df_out) for nombre, df_out in salidas.items()},
        "escritos": escritos,
        "omitidos": omitidos,
    }


def _cli(argv: list[str] | None = None) -> int:
    """CLI del builder: `python -m src.clase.dataset_clase [--check | --fast-check]`."""
    parser = argparse.ArgumentParser(
        description="Genera data/processed/ desde el HDF5 DS02 (idempotente)."
    )
    parser.add_argument(
        "--out-dir", default=os.path.join("data", "processed"),
        help="Directorio de salida (por defecto data/processed).",
    )
    parser.add_argument(
        "--h5", default=None,
        help="Ruta al HDF5; por defecto usa resolve_ds02().",
    )
    grupo = parser.add_mutually_exclusive_group()
    grupo.add_argument(
        "--check", action="store_true",
        help="Reconstruye en temporal y compara; no escribe en out-dir.",
    )
    grupo.add_argument(
        "--fast-check", action="store_true",
        help="Verifica dataset_manifest.json y los artefactos sin cargar el HDF5.",
    )
    args = parser.parse_args(argv)

    if args.fast_check:
        resultado = verificar_manifiesto(args.out_dir)
        if resultado["ok"]:
            print(f"OK: {args.out_dir} coincide con dataset_manifest.json")
            return 0
        print(f"DRIFT: {args.out_dir} no coincide con dataset_manifest.json")
        for diferencia in resultado["diferencias"]:
            print(f"  - {diferencia}")
        return 1

    resultado = construir_artefactos_clase(
        out_dir=args.out_dir, check=args.check, h5_path=args.h5
    )
    if args.check:
        if resultado["ok"]:
            print(f"OK: {args.out_dir} coincide con la reconstrucción")
            return 0
        print(f"DRIFT: {args.out_dir} no coincide con la reconstrucción")
        for diferencia in resultado["diferencias"]:
            print(f"  - {diferencia}")
        return 1

    print(f"artefactos en {resultado['out_dir']}")
    print(f"  escritos: {resultado['escritos'] or 'ninguno (ya estaban al día)'}")
    print(f"  omitidos: {resultado['omitidos'] or 'ninguno'}")
    print(f"  nulos MAR: {resultado['auditoria']['nulos_inyectados']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_cli())
