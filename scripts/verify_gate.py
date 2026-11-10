#!/usr/bin/env python
"""Verification gate for the N-CMAPSS DS02 repo.

Run this before declaring any work in this repo done. It runs the pytest
suite — which includes the Streamlit AppTest UI tests — and exits non-zero
when anything fails, so a green exit code is the only evidence the repo is
clean.

The suite takes about 3.5 minutes. Use --only for a targeted check while
you work, and the full gate before you close.

Usage:
    python scripts/verify_gate.py                 # full suite (~3.5 min)
    python scripts/verify_gate.py --only tests/test_flota.py
    python scripts/verify_gate.py --list          # show collected tests
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    """Comprueba las puertas del repo y devuelve 0 solo si todas pasan."""
    ap = argparse.ArgumentParser(description="DS02 verification gate")
    ap.add_argument("--only", metavar="PATH", help="run a single test file or directory")
    ap.add_argument("--list", action="store_true", help="list collected tests and exit")
    args = ap.parse_args()

    if args.list:
        cmd = [sys.executable, "-m", "pytest", "tests", "--collect-only", "-q"]
    else:
        target = args.only if args.only else "tests"
        cmd = [sys.executable, "-m", "pytest", target, "-q", "--no-header"]

    print("=== VERIFICATION GATE ===")
    if not args.list:
        print("target:", args.only if args.only else "tests (full suite)")
    print("cwd   :", ROOT)
    print()

    proc = subprocess.run(cmd, cwd=ROOT)

    print()
    if args.list:
        return proc.returncode
    if proc.returncode == 0:
        print("GATE PASSED")
    else:
        print(f"GATE FAILED (exit {proc.returncode})")
    return proc.returncode


if __name__ == "__main__":
    sys.exit(main())
