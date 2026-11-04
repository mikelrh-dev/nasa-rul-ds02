"""Aislamiento de la persistencia de flota entre tests.

El tablero persiste gemelos y registros de hangar en
`app/registros_flota.json` para que recargar la página no borre la flota.
Sin esta limpieza, un test que registre un gemelo contaminaría al siguiente
(AppTest arranca con los registros del disco) y los conteos de widgets
dejarían de ser deterministas.

Cuidado: ese fichero es el mismo que usa la app en producción. `os.remove`
directo borra la flota del usuario al correr la suite — pasó. Ahora el fixture
lo aparta, deja el registro vacío para el test y lo restaura al terminar.
"""

from __future__ import annotations

import os
import shutil

import pytest

_REGISTROS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "app", "registros_flota.json"
)
# Copia del registro real, a un nombre que la app no lee.
_RESPALDO = _REGISTROS + ".hermes-respaldo"
# Registros por sesión: mismo trato. Se apartan enteros antes del test y
# vuelven al terminar; la app no debe leer ficheros de otros tests.
_SESIONES = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app",
                 "registros_sesiones"))
_SESIONES_RESPALDO = _SESIONES + ".hermes-respaldo"


@pytest.fixture(autouse=True)
def _flota_limpia():
    if os.path.exists(_REGISTROS):
        shutil.copy2(_REGISTROS, _RESPALDO)
        os.remove(_REGISTROS)
    aparta_sesiones = os.path.exists(_SESIONES)
    if aparta_sesiones:
        shutil.move(_SESIONES, _SESIONES_RESPALDO)
    yield
    # El registro del usuario vuelve, pase lo que pase: un test no debe poder
    # destruir la flota que alguien registró en la app.
    if os.path.exists(_RESPALDO):
        shutil.move(_RESPALDO, _REGISTROS)
    if aparta_sesiones and os.path.exists(_SESIONES_RESPALDO):
        if os.path.exists(_SESIONES):
            shutil.rmtree(_SESIONES)
        shutil.move(_SESIONES_RESPALDO, _SESIONES)
