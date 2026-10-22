"""Aislamiento de la persistencia de flota entre tests.

El tablero persiste gemelos y registros de hangar en
`app/registros_flota.json` para que recargar la página no borre la flota.
Sin esta limpieza, un test que registre un gemelo contaminaría al siguiente
(AppTest arranca con los registros del disco) y los conteos de widgets
dejarían de ser deterministas.
"""

from __future__ import annotations

import os

import pytest

_REGISTROS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "app", "registros_flota.json"
)


@pytest.fixture(autouse=True)
def _flota_limpia():
    if os.path.exists(_REGISTROS):
        os.remove(_REGISTROS)
    yield
    if os.path.exists(_REGISTROS):
        os.remove(_REGISTROS)
