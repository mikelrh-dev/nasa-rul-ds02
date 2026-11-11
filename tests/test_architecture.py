"""Contrato de dirección: `clase` puede usar `ds02_rul`, nunca al revés.

El bundle C vive en `src/ds02_rul/`; la rúbrica vive en `src/clase/`. Si un
módulo de `ds02_rul` vuelve a importar `clase` (como hacía `shap_c.py` antes de
la reestructuración), el test falla antes de que el acoplamiento se consolide.
"""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DS02 = ROOT / "src" / "ds02_rul"
CLASE = ROOT / "src" / "clase"


def _imports(path: Path):
    """Yield module names imported by `path` (AST, no docstrings/comentarios)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            yield node.module


def _is_clase(module: str) -> bool:
    return module == "clase" or module.startswith("clase.") or \
        module == "src.clase" or module.startswith("src.clase.")


def test_ds02_no_importa_clase():
    offenders = []
    for path in sorted(DS02.rglob("*.py")):
        for module in _imports(path):
            if _is_clase(module):
                offenders.append(f"{path.relative_to(ROOT)} -> {module}")
    assert not offenders, "ds02_rul no puede importar clase:\n" + "\n".join(offenders)


def test_los_tres_modulos_del_bundle_ya_no_viven_en_clase():
    assert not (CLASE / "train_ensemble_adaptado.py").exists()
    assert not (CLASE / "puente_c.py").exists()
    assert not (CLASE / "evaluar_c_multisemilla.py").exists()


def test_las_fachadas_de_rubrica_no_vuelven():
    """`src/reglas.py` y `src/utils.py` se eliminaron: eran dos nombres, no lógica.

    La lógica vive en `src/mia/` y `src/clase/`, y el gate de reglas importa
    `src.mia.reglas` por ruta canónica. Reintroducir una fachada vuelve a dar
    dos nombres para el mismo módulo, y el import desnudo `reglas` se vuelve
    ambiguo según el orden de `sys.path`.
    """
    assert not (ROOT / "src" / "reglas.py").exists()
    assert not (ROOT / "src" / "utils.py").exists()


def test_el_bundle_c_tiene_un_solo_escritor():
    assert (DS02 / "bundle_c.py").exists()
    assert (DS02 / "puente_c.py").exists()
    assert (ROOT / "scripts" / "operativo" / "evaluate_bundle_stability.py").exists()
