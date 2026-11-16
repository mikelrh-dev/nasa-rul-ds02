"""Re-derive the rules-layer evidence and fail on any drift (RULES-06).

    python scripts/auditoria/freeze_rules_evidence.py [--check | --write] [--instrument | --cache PATH]

By default it verifies the shipped band against `mia/instrumento_oof.npz`, the
tracked 14 915-row instrument the band was fitted on (see ADR-012): pure units
`[2, 5, 10, 18, 20]`, the shipped causal isotonic correction, the conformal band
and the recorded quantiles, compared at the precision
`mia/calibracion_banda.json` records — never at the DSS's live-rerun tolerance.
The OOF table is *reported* on this path, not asserted: it was measured on a
cache git ignores, so printing it as a contract would assert a figure nobody can
reproduce.

`--cache PATH` is the development path: rebuild the instrument from that
out-of-fold cache (step-1 rows), which is where the table comes from. On the
current tree it exits 5 — the base refit is not bit deterministic, and saying so
is the point. `--instrument` forces the default path explicitly.

Exit codes, so CI can tell the three failures apart:

* `0` every check passed and the table was printed;
* `2` usage error (`--check` with `--write`; argparse's own code, not remapped);
* `3` input error — cache absent, unreadable, incomplete or non-finite;
* `4` drift — a figure, the pure-mask size or a rows-changed count moved;
* `5` contract — a shipped function lost a parameter or a key, or the frozen
  JSON no longer satisfies RULES-05.

`--check` is the default and `--write` is explicit: a verification command that
mutates a frozen artifact by accident is a trap. `--write` re-freezes
`mia/calibracion_banda.json` only, from the module constant, and only for fields
outside tolerance; on a matching tree it prints `no change` and opens no file.
When a **recorded figure** drifted it exits 4 and opens no file at all: freezing
first and reporting afterwards would leave the artifact repaired on a run that
failed.

The word "skip" never appears in the output. A missing instrument is a failure,
not a reason to pass — the test suite takes the opposite policy on purpose.

The package `ds02_rul` imports Keras at import time through `pooling.py`, so the
three submodules the gate needs are loaded against an explicit namespace
package: same shipped code, no TensorFlow in a process that only reads a cache.
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
# The band in `calibracion_banda.json` was fitted on a selection that git
# ignores (`nb2_selection.joblib`), so the rows are frozen here instead: the
# band's own evidence must survive a clone.
INSTRUMENT_KEYS = ("units", "cycles", "y", "pred_ema")
INSTRUMENT = os.path.join(MIA, "instrumento_oof.npz")
# What the frozen instrument can speak for by itself. The OOF table below was
# measured on a different, absent cache and cannot be re-derived from these
# rows, so it is reported, not asserted, on this path.
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

# Recorded evidence. The test columns are NOT recomputed: the cache holds
# development/OOF rows only, so they stay anchored by the manifest and app/cache.
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

# Half-unit-in-the-last-place from the committed decimals, plus 1e-9. Integers
# and the envelope identity are exact. `5e-3` belongs to the non-deterministic
# BiLSTM path and would hide a real drift here.
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
    """A cache that cannot be verified: absent, unreadable, incomplete, non-finite."""

    def __init__(self, kind: str, detail: str):
        super().__init__(f"{kind}: {detail}")
        self.kind = kind
        self.detail = detail


class ContractError(Exception):
    """The shipped code or the frozen JSON no longer honours its contract."""


# --------------------------------------------------------------- imports
def _submodule(name: str):
    """Import `ds02_rul.<name>` without running the package `__init__`.

    `ds02_rul/__init__.py` pulls `pooling`, which imports Keras. The gate needs
    only `stacking`, `conformal` and `metrics`, so the package namespace is
    registered explicitly and the `__init__` never executes.
    """
    if "ds02_rul" not in sys.modules:
        package = types.ModuleType("ds02_rul")
        package.__path__ = [os.path.join(SRC, "ds02_rul")]
        sys.modules["ds02_rul"] = package
    return importlib.import_module(f"ds02_rul.{name}")


def _import_mia():
    """Load `mia/reglas.py` by its canonical dotted path, from the repo root.

    This used to insert `src/mia` on `sys.path` and import the bare name
    `reglas`. That name is ambiguous: whichever of `src` and `src/mia` sits
    first wins, so the gate could measure a different module depending on the
    import order (it did, through a facade that has since been deleted).
    Importing `src.mia.reglas` makes the canonical module win regardless of
    `sys.path` order, and keeps one module object per process instead of one
    per import style.
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
    """Load and validate the five OOF arrays.

    Every failure is an `InputError`, never an empty result: the caller reports
    the named cause and exits 3. Finite values and equal lengths are part of the
    contract — a NaN would silently poison every figure downstream.
    """
    if not os.path.exists(path):
        raise InputError("missing instrument", path)
    try:
        with np.load(path) as data:
            present = set(data.keys())
            # Base predictions rebuild the instrument; a frozen instrument is
            # the rebuilt rows themselves, production-ready for the band.
            keys = REQUIRED_KEYS if set(REQUIRED_KEYS) <= present else INSTRUMENT_KEYS
            missing = [key for key in keys if key not in present]
            arrays = {key: np.asarray(data[key]) for key in keys if key in present}
    except Exception as exc:  # corrupt zip, wrong dtype, permission denied
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
    """Say what is missing, how to rebuild it and which rule makes it fatal."""
    print("freeze-rules-evidence: cannot verify", file=stream)
    print(f"  {error.kind}: {error.detail}", file=stream)
    print(f"  rebuild it with:    {REBUILD}", file=stream)
    print(f"  policy:             {POLICY}", file=stream)


# ------------------------------------------------------------- recompute
def _ordered_positions(units, cycles):
    """Per-unit positions ordered by `cycles`, stable so ties keep row order.

    The OOF cache has no `start_index`; imitating the UI's `(cycle, start_index)`
    lexsort would pretend to a granularity this artifact does not carry.
    """
    positions = {}
    for unit in np.unique(units):
        idx = np.where(units == unit)[0]
        positions[float(unit)] = idx[np.argsort(cycles[idx], kind="stable")]
    return positions


def _per_unit(positions, serie, fn):
    """Apply `fn` to each unit's ordered series, scattering back to row order."""
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
    """Exit 5 if the shipped functions lost a parameter or a key."""
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
    """Rebuild the instrument and every figure RULES-06 makes checkable."""
    if cache.get("_mode") == "instrument":
        # The rows arrive already reduced and smoothed. Re-deriving them here
        # would build a different instrument, which is the defect this path
        # exists to remove, not to repeat.
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
    """Structural violations of RULES-05 — always exit 5, never a tolerance."""
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
    """Numeric drift of the recomputed quantiles, at 5e-5."""
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
    """Re-freeze every recomputable calibration field; report what moved."""
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
    """Compare only the figures this instrument can speak for."""
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


# ------------------------------------------------------------------ run
def run(expected: dict | None = None, cache: str | None = None,
        write: bool = False, stream=None, instrument: bool = False) -> int:
    """Run the gate and return its exit code (never raises on bad input).

    `instrument=True` verifies the frozen band from `mia/instrumento_oof.npz`
    instead of the OOF cache. The two paths answer different questions: the
    cache re-derives an instrument, the frozen npz repeats the derivation the
    shipped band actually came from.
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
        # Verify before freezing: a gate that repairs the file it validates turns
        # a failed check into a passing one on the second run.
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
    # Default: the tracked instrument. A clone must verify the band without the
    # notebook artifact and without re-running a nondeterministic base refit.
    if os.path.exists(INSTRUMENT):
        return run(instrument=True, write=args.write)
    return run(write=args.write)


if __name__ == "__main__":
    raise SystemExit(main())
