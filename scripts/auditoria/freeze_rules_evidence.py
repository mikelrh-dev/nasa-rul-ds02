"""Recalcula la evidencia de la capa de reglas y falla ante cualquier deriva (RULES-06).

    python scripts/auditoria/freeze_rules_evidence.py [--check | --write] [--instrument | --cache PATH]

Por defecto verifica la banda desplegada contra `mia/instrumento_oof.npz`, el
instrumento versionado de 14 915 filas con el que se ajustó la banda (ver
ADR-012): unidades puras `[2, 5, 10, 18, 20]`, la corrección isotónica causal
desplegada, la banda conforme y los cuantiles registrados, comparados con la
precisión que guarda `mia/calibracion_banda.json`, nunca con la tolerancia de
reejecución en vivo del DSS. En esta ruta la tabla OOF se *informa*, no se
exige: se midió sobre una caché que git ignora, así que imprimirla como
contrato afirmaría una cifra que nadie puede reproducir.

`--cache PATH` es la ruta de desarrollo: reconstruye el instrumento desde esa
caché out-of-fold (filas de paso 1), que es de donde sale la tabla. Sobre el
árbol actual sale con 5 porque el reajuste base no es determinista bit a bit, y
señalarlo es justamente el objetivo. `--instrument` fuerza explícitamente la
ruta por defecto.

Códigos de salida, para que CI distinga los tres fallos:

* `0` todas las comprobaciones pasan y la tabla se imprime;
* `2` error de uso (`--check` con `--write`; código propio de argparse, sin remapear);
* `3` error de entrada — caché ausente, ilegible, incompleta o con no finitos;
* `4` deriva — cambió una cifra, el tamaño de la máscara pura o un recuento de filas;
* `5` contrato — una función desplegada perdió un parámetro o una clave, o el JSON
  congelado ya no cumple RULES-05.

`--check` es el modo por defecto y `--write` es explícito: un comando de
verificación que muta un artefacto congelado por accidente es una trampa.
`--write` vuelve a congelar solo `mia/calibracion_banda.json`, desde la constante
del módulo y únicamente en los campos fuera de tolerancia; sobre un árbol que
coincide imprime `no change` y no abre ningún fichero. Si deriva una **cifra
registrada**, sale con 4 y no abre nada: congelar primero e informar después
dejaría el artefacto reparado en una ejecución fallida.

La palabra "skip" nunca aparece en la salida. Un instrumento ausente es un
fallo, no un motivo para pasar; la suite de tests toma la política contraria a
propósito.

El paquete `ds02_rul` importa Keras en tiempo de importación a través de
`pooling.py`, así que los tres submódulos que necesita la puerta se cargan contra
un paquete de espacio de nombres explícito: el mismo código desplegado, sin
TensorFlow en un proceso que solo lee una caché.
"""
from __future__ import annotations

import argparse
import copy
import importlib
import json
import os
import sys
import types

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CACHE = os.path.join(ROOT, "_p1_oof_cache.npz")
CALIBRACION = os.path.join(ROOT, "src", "mia", "calibracion_banda.json")
SRC = os.path.join(ROOT, "src")
MIA = os.path.join(SRC, "mia")

REQUIRED_KEYS = ("units", "cycles", "y", "p_lstm", "p_lgb")
PURE_UNITS = (2.0, 5.0, 10.0, 18.0, 20.0)
# La banda de `calibracion_banda.json` se ajustó sobre una selección que git
# ignora (`nb2_selection.joblib`), así que las filas se congelan aquí: la
# evidencia de la propia banda debe sobrevivir a un clon.
INSTRUMENT_KEYS = ("units", "cycles", "y", "pred_ema")
INSTRUMENT = os.path.join(MIA, "instrumento_oof.npz")
# Lo que el instrumento congelado puede afirmar por sí solo. La tabla OOF de
# abajo se midió sobre otra caché ausente y no se puede recalcular desde estas
# filas, así que en esta ruta se informa y no se exige.
INSTRUMENT_EXPECTED = {"pure_rows": 14915}
PROCEDENCIA_FIELDS = ("metodo", "filas_calibracion", "unidades_calibracion",
                      "excluida", "instrumento", "cache_origen", "regla_correccion")

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_INPUT = 3
EXIT_DRIFT = 4
EXIT_CONTRACT = 5

REBUILD = "python scripts/auditoria/p1_oof_cache.py   (needs the DS02 HDF5 and the base models)"
POLICY = "RULES-06 — a missing instrument fails the gate; it never degrades to a no-op"

# Evidencia registrada. Las columnas de test NO se recalculan: la caché solo
# contiene filas de desarrollo/OOF, así que quedan ancladas al manifiesto y a app/cache.
EXPECTED = {
    "rmse_baseline": 9.491,
    "nasa_baseline": 19257.1,
    "rmse_r2": 10.737,
    "nasa_r2": 21053.0,
    "rows_r2": 13000,
    "rmse_r2b": 9.623,
    "nasa_r2b": 18713.9,
    "rows_r2b": 10715,
    "max_inc_r2b": 1.328848,
    "max_inc_envelope": 0.0,
    "coverage": 0.9012,
    "pure_rows": 14915,
}

# Media unidad del último decimal de los valores registrados, más 1e-9. Los
# enteros y la identidad de la envolvente son exactos. `5e-3` corresponde a la
# ruta BiLSTM no determinista y ocultaría una deriva real aquí.
TOLERANCE = {
    "rmse_baseline": 5e-4,
    "nasa_baseline": 5e-2,
    "rmse_r2": 5e-4,
    "nasa_r2": 5e-2,
    "rows_r2": 0.0,
    "rmse_r2b": 5e-4,
    "nasa_r2b": 5e-2,
    "rows_r2b": 0.0,
    "max_inc_r2b": 5e-7,
    "max_inc_envelope": 5e-7,
    "coverage": 5e-5,
    "pure_rows": 0.0,
}

LABELS = {
    "rmse_baseline": "baseline OOF RMSE",
    "nasa_baseline": "baseline OOF NASA",
    "rmse_r2": "R2 OOF RMSE",
    "nasa_r2": "R2 OOF NASA",
    "rows_r2": "R2 rows changed",
    "rmse_r2b": "R2b OOF RMSE",
    "nasa_r2b": "R2b OOF NASA",
    "rows_r2b": "R2b rows changed",
    "max_inc_r2b": "R2b max positive increment",
    "max_inc_envelope": "envelope max positive increment",
    "coverage": "OOF coverage (corrected point)",
    "pure_rows": "pure OOF rows",
}

QUANTILE_TOLERANCE = 5e-5

TABLE = """\
variant                       OOF RMSE   OOF NASA   Test RMSE*  Test NASA*  rows changed  max +inc
Baseline (raw EMA5)              9.491    19257.1       4.289      2310.6             0          —
V1 running-min                  10.737    21053.0       3.964      1906.6         13000     0.000000
V2 prefix PAVA                   9.623    18713.9       4.173      2182.9         10715    +1.328848
V3 min(prefix PAVA)             10.737    21053.0       3.964      1906.6         13000     0.000000
* (recorded) in docs/evidencia/informes/informe-2026-10-21-reglas-oof.md §13 and models/ds02_manifest.json — not recomputed:
  _p1_oof_cache.npz holds development rows only (RULES-06)."""


class InputError(Exception):
    """Una caché que no se puede verificar: ausente, ilegible, incompleta o con no finitos."""

    def __init__(self, kind: str, detail: str):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


class ContractError(Exception):
    """El código desplegado o el JSON congelado ya no cumple su contrato."""


# --------------------------------------------------------------- imports
def _submodule(name: str):
    """Importa `ds02_rul.<name>` sin ejecutar el `__init__` del paquete.

    `ds02_rul/__init__.py` arrastra `pooling`, que importa Keras. La puerta solo
    necesita `stacking`, `conformal` y `metrics`, así que el espacio de nombres
    del paquete se registra explícitamente y el `__init__` nunca se ejecuta.
    """
    if "ds02_rul" not in sys.modules:
        package = types.ModuleType("ds02_rul")
        package.__path__ = [os.path.join(SRC, "ds02_rul")]
        sys.modules["ds02_rul"] = package
    return importlib.import_module(f"ds02_rul.{name}")


def _import_mia():
    """Carga `mia/reglas.py` por su ruta canónica, desde la raíz del repo.

    Antes se insertaba `src/mia` en `sys.path` y se importaba el nombre desnudo
    `reglas`. Ese nombre es ambiguo: gana el primero que aparezca entre `src` y
    `src/mia`, así que la puerta podía medir un módulo distinto según el orden de
    importación (así ocurrió, a través de una fachada ya eliminada). Importar
    `src.mia.reglas` hace que gane siempre el módulo canónico, sea cual sea el
    orden de `sys.path`, y mantiene un solo objeto de módulo por proceso en vez
    de uno por estilo de importación.
    """
    if ROOT not in sys.path:
        sys.path.insert(0, ROOT)
    return importlib.import_module("src.mia.reglas")


STACKING = _submodule("stacking")
CONFORMAL = _submodule("conformal")
METRICS = _submodule("metrics")
REGLAS = _import_mia()


# ---------------------------------------------------------------- input
def load_cache(path: str) -> dict:
    """Carga y valida los cinco arrays OOF.

    Todo fallo es un `InputError`, nunca un resultado vacío: quien llama informa
    la causa concreta y sale con 3. Los valores finitos y las longitudes iguales
    forman parte del contrato; un NaN envenenaría en silencio todas las cifras
    posteriores.
    """
    if not os.path.exists(path):
        raise InputError("missing instrument", path)
    try:
        with np.load(path) as data:
            present = set(data.keys())
            # Las predicciones base reconstruyen el instrumento; un instrumento
            # congelado son las propias filas reconstruidas, listas para la banda.
            keys = REQUIRED_KEYS if set(REQUIRED_KEYS) <= present else INSTRUMENT_KEYS
            missing = [key for key in keys if key not in present]
            arrays = {key: np.asarray(data[key]) for key in keys if key in present}
    except Exception as exc:  # zip corrupto, dtype incorrecto, permiso denegado
        raise InputError("unreadable instrument", f"{path}: {exc}") from exc

    if missing:
        raise InputError("incomplete instrument", f"{path} — missing key {missing[0]}")
    for key in keys:
        if not np.all(np.isfinite(arrays[key])):
            raise InputError("invalid instrument", f"{path} — non-finite values in {key}")
    lengths = {key: int(arrays[key].size) for key in keys}
    if len(set(lengths.values())) != 1:
        raise InputError("invalid instrument", f"{path} — unequal lengths {lengths}")
    arrays["_mode"] = "oof" if keys is REQUIRED_KEYS else "instrument"
    return arrays


def report_input_error(error: InputError, stream) -> None:
    """Indica qué falta, cómo reconstruirlo y qué regla lo hace fatal."""
    print("freeze-rules-evidence: cannot verify", file=stream)
    print(f"  {error.kind}: {error.detail}", file=stream)
    print(f"  rebuild it with:    {REBUILD}", file=stream)
    print(f"  policy:             {POLICY}", file=stream)


# ------------------------------------------------------------- recompute
def _ordered_positions(units, cycles):
    """Posiciones por unidad ordenadas por `cycles`, estables para conservar el orden de fila en empates.

    La caché OOF no tiene `start_index`; imitar el lexsort `(cycle, start_index)`
    de la UI fingiría una granularidad que este artefacto no tiene.
    """
    positions = {}
    for unit in np.unique(units):
        idx = np.where(units == unit)[0]
        positions[float(unit)] = idx[np.argsort(cycles[idx], kind="stable")]
    return positions


def _per_unit(positions, serie, fn):
    """Aplica `fn` a la serie ordenada de cada unidad y devuelve al orden de fila."""
    out = np.empty(len(serie), dtype=np.float64)
    for idx in positions.values():
        out[idx] = fn(serie[idx])
    return out


def _metrics(y_true, pred) -> tuple[float, float]:
    rmse = float(np.sqrt(np.mean((y_true - pred) ** 2)))
    return rmse, float(METRICS.calculate_nasa_score(y_true, pred))


def _max_positive_increment(positions, serie) -> float:
    peak = 0.0
    for idx in positions.values():
        if idx.size >= 2:
            peak = max(peak, float(np.diff(serie[idx]).max()))
    return peak


def _require_api() -> None:
    """Sale con 5 si las funciones desplegadas perdieron un parámetro o una clave."""
    import inspect

    needed = {
        "select_beta_grouped": ("units", "cycles", "y", "pred_lstm", "pred_lgb",
                                "span", "use_cycle_feature"),
        "fit_conformal": ("y_true", "pred", "target", "edges", "min_rows"),
    }
    modules = {"select_beta_grouped": STACKING, "fit_conformal": CONFORMAL}
    for name, params in needed.items():
        fn = getattr(modules[name], name, None)
        if fn is None:
            raise ContractError(f"{modules[name].__name__}.{name} is missing")
        present = set(inspect.signature(fn).parameters)
        lost = [p for p in params if p not in present]
        if lost:
            raise ContractError(f"{name} lost parameter(s): {', '.join(lost)}")


def recompute(cache: dict) -> dict:
    """Reconstruye el instrumento y cada cifra que RULES-06 hace comprobable."""
    if cache.get("_mode") == "instrument":
        # Las filas llegan ya reducidas y suavizadas. Recalcularlas aquí
        # construiría otro instrumento, que es el defecto que esta ruta existe
        # para eliminar, no para repetir.
        calib, beta, folds = cache, float(cache.get("beta", 1.0)), 0
    else:
        _require_api()
        try:
            selection = STACKING.select_beta_grouped(
                cache["units"], cache["cycles"], cache["y"],
                cache["p_lstm"], cache["p_lgb"], span=5, use_cycle_feature=False,
            )
        except TypeError as exc:
            raise ContractError(f"select_beta_grouped rejected the shipped call: {exc}") from exc
        calib = selection.get("oof_calib")
        if calib is None:
            raise ContractError("select_beta_grouped returned no 'oof_calib'")
        beta = float(selection["beta"])
        folds = int(selection.get("spread", {}).get("n_folds", 0))
    for key in ("units", "cycles", "y", "pred_ema"):
        if key not in calib:
            raise ContractError(f"oof_calib lost key {key!r}")

    units = np.asarray(calib["units"], dtype=np.float64)
    cycles = np.asarray(calib["cycles"], dtype=np.float64)
    y_true = np.asarray(calib["y"], dtype=np.float64)
    raw = np.asarray(calib["pred_ema"], dtype=np.float64)

    pure = np.isin(units, PURE_UNITS)
    if np.isin(16.0, units[pure]):
        raise ContractError("unit 16 leaked into the pure calibration mask")
    units, cycles, y_true, raw = units[pure], cycles[pure], y_true[pure], raw[pure]

    positions = _ordered_positions(units, cycles)
    r2 = _per_unit(positions, raw, np.minimum.accumulate)
    r2b = _per_unit(positions, raw, REGLAS.pava_causal_no_creciente)
    envelope = _per_unit(positions, r2b, np.minimum.accumulate)
    if not np.allclose(envelope, r2):
        raise ContractError("min(PAVA) no longer equals the running minimum")

    rmse_base, nasa_base = _metrics(y_true, raw)
    rmse_r2, nasa_r2 = _metrics(y_true, r2)
    rmse_r2b, nasa_r2b = _metrics(y_true, r2b)

    try:
        fit = CONFORMAL.fit_conformal(y_true, r2b, target=0.90,
                                      edges=CONFORMAL.DEFAULT_EDGES, min_rows=100)
    except TypeError as exc:
        raise ContractError(f"fit_conformal rejected the shipped call: {exc}") from exc

    observed = {
        "beta": beta,
        "folds": folds,
        "rmse_baseline": rmse_base,
        "nasa_baseline": nasa_base,
        "rmse_r2": rmse_r2,
        "nasa_r2": nasa_r2,
        "rows_r2": int((r2 != raw).sum()),
        "rmse_r2b": rmse_r2b,
        "nasa_r2b": nasa_r2b,
        "rows_r2b": int((r2b != raw).sum()),
        "max_inc_r2b": _max_positive_increment(positions, r2b),
        "max_inc_envelope": _max_positive_increment(positions, envelope),
        "pure_rows": int(y_true.size),
        "fit": fit,
    }
    committed = _load_committed()
    lower, upper = CONFORMAL.apply_conformal(r2b, committed)
    observed["coverage"] = float(CONFORMAL.empirical_coverage(y_true, lower, upper))
    return observed


# ---------------------------------------------------------------- frozen
def _load_committed() -> dict:
    try:
        with open(CALIBRACION, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise ContractError(f"frozen calibration missing: {CALIBRACION}") from exc
    except json.JSONDecodeError as exc:
        raise ContractError(f"frozen calibration is not JSON: {exc}") from exc


def _check_frozen_contract(committed: dict, fit: dict) -> list[str]:
    """Violaciones estructurales de RULES-05: siempre exit 5, nunca una tolerancia."""
    problems = []
    for key, want in (("method", fit["method"]), ("debias", fit["debias"]),
                      ("target_coverage", fit["target_coverage"]),
                      ("alpha_each_side", fit["alpha_each_side"]),
                      ("edges", fit["edges"])):
        if committed.get(key) != want:
            problems.append(f"{key}: expected {want!r}, observed {committed.get(key)!r}")

    bins = committed.get("bins")
    if not isinstance(bins, list) or len(bins) != len(fit["bins"]):
        problems.append(f"bins: expected {len(fit['bins'])}, observed {len(bins or [])}")
        bins = []
    for index, (have, want) in enumerate(zip(bins, fit["bins"])):
        for key in ("index", "pred_range", "n", "source"):
            if have.get(key) != want[key]:
                problems.append(
                    f"bins[{index}].{key}: expected {want[key]!r}, observed {have.get(key)!r}")
    if bins and sum(int(b.get("n", 0)) for b in bins) != int(committed.get("n_calibration", -1)):
        problems.append("bins[].n: does not sum to n_calibration")
    if committed.get("n_calibration") != fit["n_calibration"]:
        problems.append(
            f"n_calibration: expected {fit['n_calibration']}, "
            f"observed {committed.get('n_calibration')}")

    provenance = committed.get("procedencia")
    if not isinstance(provenance, dict):
        problems.append("procedencia: missing block")
        return problems
    for field in PROCEDENCIA_FIELDS:
        value = provenance.get(field)
        if value in (None, "", [], {}):
            problems.append(f"procedencia.{field}: empty or missing")
    if provenance.get("filas_calibracion") != fit["n_calibration"]:
        problems.append(
            f"procedencia.filas_calibracion: expected {fit['n_calibration']}, "
            f"observed {provenance.get('filas_calibracion')}")
    units = provenance.get("unidades_calibracion")
    if units is not None and sorted(units) != sorted(int(u) for u in PURE_UNITS):
        problems.append(f"procedencia.unidades_calibracion: expected "
                        f"{sorted(int(u) for u in PURE_UNITS)}, observed {units}")
    return problems


def _quantile_drifts(committed: dict, fit: dict) -> list[tuple[str, float, float]]:
    """Deriva numérica de los cuantiles recalculados, a 5e-5."""
    drifts = []
    for index, (have, want) in enumerate(zip(committed.get("bins", []), fit["bins"])):
        for key in ("q_low", "q_high"):
            if abs(float(have.get(key, np.nan)) - float(want[key])) > QUANTILE_TOLERANCE:
                drifts.append((f"bins[{index}].{key}", float(want[key]), float(have.get(key, np.nan))))
    have_global = committed.get("global_quantiles", [np.nan, np.nan])
    for index, key in enumerate(("global_quantiles[0]", "global_quantiles[1]")):
        if abs(float(have_global[index]) - float(fit["global_quantiles"][index])) > QUANTILE_TOLERANCE:
            drifts.append((key, float(fit["global_quantiles"][index]), float(have_global[index])))
    return drifts


def _write_frozen(committed: dict, fit: dict) -> list[str]:
    """Vuelve a congelar los campos recalculables de calibración e informa lo que cambió."""
    payload = copy.deepcopy(committed)
    changes = []
    for key, want in (("method", fit["method"]), ("debias", fit["debias"]),
                      ("target_coverage", fit["target_coverage"]),
                      ("alpha_each_side", fit["alpha_each_side"]),
                      ("edges", fit["edges"]),
                      ("global_quantiles", fit["global_quantiles"]),
                      ("n_calibration", fit["n_calibration"])):
        if payload.get(key) != want:
            changes.append(f"  {key}: {payload.get(key)!r} → {want!r}")
            payload[key] = want
    for have, want in zip(payload.get("bins", []), fit["bins"]):
        for key in ("pred_range", "n", "source", "q_low", "q_high"):
            if have.get(key) != want[key]:
                changes.append(f"  bins[{want['index']}].{key}: {have.get(key)!r} → {want[key]!r}")
                have[key] = want[key]
    if not changes:
        return []
    with open(CALIBRACION, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(payload, fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    return changes


# -------------------------------------------------------------- compare
def _compare(observed: dict, expected: dict) -> list[str]:
    """Compara solo las cifras de las que este instrumento puede responder."""
    failures = []
    for field, tolerance in TOLERANCE.items():
        if field not in expected:
            continue
        want = float(expected[field])
        have = float(observed[field])
        if tolerance == 0.0:
            ok = int(want) == int(have)
        else:
            ok = abs(want - have) <= tolerance + 1e-9
        if not ok:
            failures.append(f"{field}: expected {want!r}, observed {have!r}")
    return failures


def _print_check_block(observed: dict, expected: dict, stream) -> None:
    print("", file=stream)
    if observed["folds"]:
        print(f"beta (median of {observed['folds']} folds): {observed['beta']}", file=stream)
    else:
        print(f"beta: {observed['beta']} (frozen instrument, not re-selected)", file=stream)
    print(f"{'check':38s} {'expected':>12s} {'observed':>14s}  verdict", file=stream)
    for field in TOLERANCE:
        have = float(observed[field])
        if field not in expected:
            print(f"{LABELS[field]:38s} {'-':>12s} {have:>14.6f}  reported", file=stream)
            continue
        want = float(expected[field])
        tolerance = TOLERANCE[field]
        ok = (int(want) == int(have) if tolerance == 0.0
              else abs(want - have) <= tolerance + 1e-9)
        print(f"{LABELS[field]:38s} {want:>12.6g} {have:>14.6f}  "
              f"{'ok' if ok else 'DRIFT'}", file=stream)


# ----------------------------------------------------------------- ejecución
def run(expected: dict | None = None, cache: str | None = None,
        write: bool = False, stream=None, instrument: bool = False) -> int:
    """Ejecuta la puerta y devuelve su código de salida (nunca lanza por entrada inválida).

    `instrument=True` verifica la banda congelada desde `mia/instrumento_oof.npz`
    en lugar de la caché OOF. Las dos rutas responden preguntas distintas: la
    caché recalcula un instrumento y el npz congelado repite la derivación de la
    que salió realmente la banda desplegada.
    """
    stream = sys.stdout if stream is None else stream
    if instrument:
        path = INSTRUMENT if cache is None else cache
        expected = INSTRUMENT_EXPECTED if expected is None else expected
    else:
        path = DEFAULT_CACHE if cache is None else cache
        expected = EXPECTED if expected is None else expected

    try:
        arrays = load_cache(path)
        observed = recompute(arrays)
        committed = _load_committed()
        contract = _check_frozen_contract(committed, observed["fit"])
    except InputError as error:
        report_input_error(error, stream)
        return EXIT_INPUT
    except ContractError as error:
        print("freeze-rules-evidence: contract broken", file=stream)
        print(f"  {error}", file=stream)
        print(f"  policy:             {POLICY}", file=stream)
        return EXIT_CONTRACT

    if not instrument:
        print(TABLE, file=stream)
    _print_check_block(observed, expected, stream)

    if contract:
        print("", file=stream)
        print("freeze-rules-evidence: the frozen JSON violates RULES-05", file=stream)
        for problem in contract:
            print(f"  {problem}", file=stream)
        return EXIT_CONTRACT

    drifts = _quantile_drifts(committed, observed["fit"])
    failures = _compare(observed, expected)

    if write and failures:
        # Verificar antes de congelar: una puerta que repara el fichero que valida
        # convierte una comprobación fallida en aprobada a la segunda ejecución.
        print("", file=stream)
        print("freeze-rules-evidence: recorded figures drift; refusing to re-freeze",
              file=stream)
        for failure in failures:
            print(f"  {failure}", file=stream)
        print(f"  untouched:          {CALIBRACION}", file=stream)
        return EXIT_DRIFT

    if write:
        changes = _write_frozen(committed, observed["fit"])
        if changes:
            print("", file=stream)
            print(f"freeze-rules-evidence: re-froze {CALIBRACION}", file=stream)
            for line in changes:
                print(line, file=stream)
        else:
            print("", file=stream)
            print("freeze-rules-evidence: no change", file=stream)
        return EXIT_OK

    if drifts:
        print("", file=stream)
        print("freeze-rules-evidence: frozen calibration drifted", file=stream)
        for field, want, have in drifts:
            print(f"  {field}: expected {want!r}, observed {have!r}", file=stream)
        print(f"  re-freeze deliberately with: python scripts/auditoria/freeze_rules_evidence.py --write",
              file=stream)
    if failures:
        print("", file=stream)
        print("freeze-rules-evidence: recorded evidence drifted", file=stream)
        for failure in failures:
            print(f"  {failure}", file=stream)
    if drifts or failures:
        return EXIT_DRIFT
    return EXIT_OK


def main(argv=None) -> int:
    """Congela la evidencia de reglas y escribe el JSON de calibracion."""
    ap = argparse.ArgumentParser(
        description="Verify the DS02 rules-layer evidence (RULES-06).")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true",
                       help="verify only (the default; spelling it states intent)")
    group.add_argument("--write", action="store_true",
                       help="re-freeze mia/calibracion_banda.json if a field drifted")
    group.add_argument("--instrument", action="store_true",
                       help="verify the band from mia/instrumento_oof.npz")
    ap.add_argument("--cache", default=None,
                    help="out-of-fold cache: re-derive the instrument instead of "
                         "reading the frozen one (development path)")
    args = ap.parse_args(argv)
    if args.instrument:
        return run(instrument=True, write=args.write)
    if args.cache is not None:
        return run(cache=args.cache, write=args.write)
    # Por defecto, el instrumento versionado. Un clon debe verificar la banda sin
    # el artefacto del notebook y sin repetir un reajuste base no determinista.
    if os.path.exists(INSTRUMENT):
        return run(instrument=True, write=args.write)
    return run(write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
