#!/usr/bin/env python
"""Puerta de verificación del repositorio N-CMAPSS DS02.

Ejecútala antes de dar por terminado cualquier trabajo en este repositorio.
Lanza la suite de pytest —que incluye los tests de UI con Streamlit AppTest— y,
en modo completo, las tres puertas que exige la documentación al cierre
(evidencia de reglas, instrumento OOF y backfill de MLflow). Sale con código
distinto de cero si algo falla, así que una salida verde es la única prueba de
que el repositorio está limpio.

La ejecución completa tarda varios minutos. Usa --only para comprobaciones
puntuales mientras trabajas y la puerta completa antes de cerrar. Las puertas se
omiten con --only, --list o --skip-gates; necesitan los artefactos versionados y
un mlruns/ local.

Uso:
    python scripts/operativo/verify_gate.py                 # suite + puertas
    python scripts/operativo/verify_gate.py --only tests/test_flota.py
    python scripts/operativo/verify_gate.py --list          # muestra los tests recogidos
    python scripts/operativo/verify_gate.py --skip-gates    # solo pytest
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
