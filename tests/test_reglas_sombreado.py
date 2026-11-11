"""Regresión: el shim `src/reglas.py` debe sobrevivir al sombreado de imports.

`scripts/auditoria/freeze_rules_evidence.py` carga las reglas con
`_import_mia()`, que solo inserta `src/mia` en `sys.path` si no está ya. Cuando
un test anterior insertó `src/mia` y otro posterior insertó `src` delante, el
`import reglas` del gate resuelve al shim `src/reglas.py` en vez de
`src/mia/reglas.py`. Si al shim le falta un nombre que el gate usa —como
`pava_causal_no_creciente`— el gate falla con `AttributeError` en tiempo de
ejecución, no al importar.

El test simula ese orden de `sys.path` de forma determinista (no depende del
orden de ficheros de pytest), fuerza un import nuevo y afirma que el shim
expone el nombre. Antes del fix reproducía el fallo: 5 tests del gate rojos
solo cuando `test_mia_reglas_directas.py` y `test_api_limites.py` corrían
antes.
"""
from __future__ import annotations

import importlib
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "src")
MIA = os.path.join(SRC, "mia")


def test_el_shim_reglas_expone_pava_causal_bajo_sombreado():
    """Con `src` delante de `src/mia`, `import reglas` da el shim y este basta."""
    path_original = list(sys.path)
    en_cache = sys.modules.pop("reglas", None)
    try:
        # El orden exacto de las inserciones que producen el sombreado:
        # `test_mia_reglas_directas.py` inserta ROOT y `src/mia`; después
        # `test_api_limites.py` inserta ROOT y `src` delante de ambos.
        sys.path.insert(0, ROOT)
        sys.path.insert(0, MIA)
        sys.path.insert(0, ROOT)
        sys.path.insert(0, SRC)

        reglas = importlib.import_module("reglas")

        # El sombreado es real: resuelve al shim, no al módulo de verdad.
        assert reglas.__file__ is not None
        assert os.path.realpath(reglas.__file__) == os.path.realpath(
            os.path.join(SRC, "reglas.py")
        ), f"el sombreado no ocurrió: {reglas.__file__}"
        assert hasattr(reglas, "pava_causal_no_creciente"), (
            "el shim src/reglas.py no re-exporta pava_causal_no_creciente"
        )

        # Y es la misma función congelada, no una copia.
        from src.mia import reglas as reales
        assert reglas.pava_causal_no_creciente is reales.pava_causal_no_creciente
    finally:
        sys.path[:] = path_original
        sys.modules.pop("reglas", None)
        if en_cache is not None:
            sys.modules["reglas"] = en_cache
