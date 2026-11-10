"""Aislamiento de la persistencia de flota entre tests.

El tablero persiste gemelos y registros de hangar en
`app/registros_flota.json` para que recargar la página no borre la flota.
Sin esta limpieza, un test que registre un gemelo contaminaría al siguiente
(AppTest arranca con los registros del disco) y los conteos de widgets
dejarían de ser deterministas.

Cuidado: ese fichero es el mismo que usa la app en producción. `os.remove`
directo borra la flota del usuario al correr la suite — pasó. Ahora el fixture
lo aparta a un directorio temporal **fuera de `app/`**, deja el registro vacío
para el test y lo restaura al terminar.

Reglas del fixture (hallazgo C1 de la auditoría 2026-11-10):

* **Idempotente:** no depende de restos de una pasada anterior; dos
  ejecuciones seguidas dejan el árbol igual que una.
* **Exception-safe:** la restauración va en `finally`, así que un fallo del
  test o del propio setup no se lleva la flota.
* **Sin residuos en `app/`:** el respaldo vive en el directorio temporal de
  pytest. Los `*.hermes-respaldo` que dejaron versiones anteriores se recuperan
  si el registro real falta, y si no se dejan intactos: pueden ser lo único que
  quede de una sesión.
"""

from __future__ import annotations

import os
import shutil

import pytest

_APP = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "app")
)
_REGISTROS = os.path.join(_APP, "registros_flota.json")
_SESIONES = os.path.join(_APP, "registros_sesiones")
# Lo que el fixture aparta antes de cada test: el registro de flota y las
# sesiones (la app no debe leer los registros que dejó otro test).
_APARTADOS = (_REGISTROS, _SESIONES)


def _quitar(ruta: str) -> None:
    """Borra un fichero o un árbol de directorios, si existe."""
    if os.path.isdir(ruta):
        shutil.rmtree(ruta)
    elif os.path.exists(ruta):
        os.remove(ruta)


def _recuperar_restos() -> None:
    """Devuelve a su sitio los `*.hermes-respaldo` huérfanos.

    Una pasada anterior podía morir después de apartar el registro y antes de
    restaurarlo; entonces el respaldo es la única copia buena. Solo se recupera
    cuando el destino no existe: nunca se pisa el fichero vivo.
    """
    for real in _APARTADOS:
        respaldo = real + ".hermes-respaldo"
        if os.path.exists(respaldo) and not os.path.exists(real):
            shutil.move(respaldo, real)


@pytest.fixture(autouse=True)
def _flota_limpia(tmp_path_factory):
    staging = tmp_path_factory.mktemp("flota")
    apartados: list[tuple[str, str]] = []
    _recuperar_restos()
    try:
        for real in _APARTADOS:
            if os.path.exists(real):
                destino = str(staging / os.path.basename(real))
                shutil.move(real, destino)
                apartados.append((real, destino))
        yield
    finally:
        # El registro del usuario vuelve, pase lo que pase: un test no debe
        # poder destruir la flota que alguien registró en la app.
        for real, destino in apartados:
            _quitar(real)  # lo que haya escrito el test durante su turno
            if os.path.exists(destino):
                shutil.move(destino, real)
