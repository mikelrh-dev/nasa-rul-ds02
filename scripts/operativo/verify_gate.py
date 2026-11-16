#!/usr/bin/env python
"""Verification gate for the N-CMAPSS DS02 repo.

Run this before declaring any work in this repo done. It runs the pytest
suite — which includes the Streamlit AppTest UI tests — and, in full mode,
the three gates the docs require at close (rules evidence, OOF instrument
and MLflow backfill). It exits non-zero when anything fails, so a green exit
code is the only evidence the repo is clean.

The full run takes several minutes. Use --only for a targeted check while
you work, and the full gate before you close. Gates are skipped with --only,
--list or --skip-gates; they need the tracked artifacts and a local mlruns/.

Usage:
    python scripts/operativo/verify_gate.py                 # suite + gates
    python scripts/operativo/verify_gate.py --only tests/test_flota.py
    python scripts/operativo/verify_gate.py --list          # show collected tests
    python scripts/operativo/verify_gate.py --skip-gates    # pytest only
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Gates documentados en openspec/project.md y src/mia/reglas.py. Orden: el más
# barato primero, para que un fallo evidente no espere a los pesados.
GATES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("reglas (banda congelada)", ("scripts/auditoria/freeze_rules_evidence.py",)),
    ("instrumento OOF", ("scripts/auditoria/freeze_oof_instrument.py", "--check")),
    ("MLflow backfill", ("scripts/operativo/backfill_mlflow.py", "--check")),
)


def _run(label: str, argv: tuple[str, ...]) -> int:
    """Ejecuta un script con el intérprete actual y devuelve su código de salida."""
    print(f"=== {label} ===", flush=True)
    print("cmd   :", " ".join(argv), flush=True)
    print(flush=True)
    return subprocess.run([sys.executable, *argv], cwd=ROOT).returncode


def main() -> int:
    """Comprueba las puertas del repo y devuelve 0 solo si todas pasan."""
    ap = argparse.ArgumentParser(description="DS02 verification gate")
    ap.add_argument("--only", metavar="PATH", help="run a single test file or directory")
    ap.add_argument("--list", action="store_true", help="list collected tests and exit")
    ap.add_argument("--skip-gates", action="store_true",
                    help="run only pytest, without the rules/OOF/MLflow gates")
    args = ap.parse_args()

    if args.list:
        cmd = [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"]
    else:
        target = args.only if args.only else "tests"
        cmd = [sys.executable, "-m", "pytest", target, "-q", "--no-header"]

    print("=== VERIFICATION GATE ===", flush=True)
    if not args.list:
        print("target:", args.only if args.only else "tests (full suite)", flush=True)
    print("cwd   :", ROOT, flush=True)
    print(flush=True)

    failures: list[tuple[str, int]] = []

    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode != 0:
        failures.append(("pytest", proc.returncode))

    run_gates = not (args.list or args.only or args.skip_gates)
    if run_gates:
        for label, argv in GATES:
            if _run(label, argv) != 0:
                failures.append((label, 1))
    elif not args.list:
        print("gates : skipped (targeted run)", flush=True)

    print(flush=True)
    if args.list:
        return proc.returncode
    if not failures:
        print("GATE PASSED")
        return 0

    for label, rc in failures:
        print(f"GATE FAILED: {label} (exit {rc})")
    return 1


if __name__ == "__main__":
    sys.exit(main())
