"""Regresión: el gate mide `src.mia.reglas`, no un nombre que decida `sys.path`.

Historia: `freeze_rules_evidence._import_mia()` insertaba `src/mia` en
`sys.path` e importaba el nombre desnudo `reglas`. Cuando un import anterior
dejaba `src` delante, ese nombre resolvía a la fachada `src/reglas.py` y el
gate medía un alias en vez del módulo que posee las reglas. La fachada se
eliminó y el gate importa `src.mia.reglas` por ruta canónica, así que el orden
de `sys.path` dejó de ser parte del contrato.

Este test fija las dos mitades: el gate carga el módulo canónico bajo el orden
de `sys.path` que producía el sombreado, y su código no vuelve al import
desnudo.
"""
from __future__ import annotations

import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
MIA = os.path.join(SRC, "mia")
SCRIPTS = os.path.join(ROOT, "scripts", "auditoria")

CANONICO = os.path.join(MIA, "reglas.py")
GATE = os.path.join(SCRIPTS, "freeze_rules_evidence.py")

sys.path.insert(0, ROOT)


def _real(path: str) -> str:
    return os.path.realpath(path)


def test_el_gate_importa_el_modulo_canonico_bajo_sombreado():
    """Con `src` delante de `src/mia`, el gate sigue cargando el canónico."""
    path_original = list(sys.path)
    if SCRIPTS not in sys.path:
        sys.path.insert(0, SCRIPTS)
    try:
        # Orden exacto que producía el sombreado: `src` delante de `src/mia`.
        sys.path.insert(0, ROOT)
        sys.path.insert(0, MIA)
        sys.path.insert(0, ROOT)
        sys.path.insert(0, SRC)

        import freeze_rules_evidence as G

        canonico = G._import_mia()
        assert canonico.__file__ is not None
        assert _real(canonico.__file__) == _real(CANONICO), (
            f"el gate cargó {canonico.__file__}, no el módulo canónico"
        )
        assert canonico is importlib.import_module("src.mia.reglas")
    finally:
        sys.path[:] = path_original


def test_el_gate_no_importa_reglas_por_nombre_desnudo():
    """Guarda: el gate no vuelve a depender de `sys.path` para hallar reglas."""
    with open(GATE, encoding="utf-8") as fh:
        fuente = fh.read()

    assert 'import_module("reglas")' not in fuente, (
        "el gate volvió al import desnudo: una entrada de sys.path decide qué módulo mide"
    )
    assert "import_module('reglas')" not in fuente
    assert 'import_module("src.mia.reglas")' in fuente
