"""Engine registry: one key and one label per engine, everywhere.

Four views used to key the same engine four different ways: the wall used the
display label, the twins the `engine_id`, the hangar `U<unit>` for cache and
alta but the `engine_id` for twins, and the work orders `motor` or `"externa"`.
An alta added in the sidebar was keyed `U-1000` and vanished on reload.

This module is the single source of names. Every view resolves an engine
through it, so the wall, the twin store, the hangar and the orders all agree.

Named `flota`, not `motor`: `mia/motor.py` is the rules engine and
`app/ui_rules.py` imports it as `import motor as M`. Both modules sit on
`sys.path` when the app runs, so the name would shadow the rules engine and the
dashboard would import the registry where it expects `motor.motor`.

Pure: no Streamlit import, so it can be tested without a server — the same
convention as `twin.py`, `hangar.py` and `ui_alta.py`.
"""
from __future__ import annotations

import json
import os

import twin as T
import ui_alta as A
import ui_data_loader as L

ALTAS_KEY = "altas"
# Negative and reserved: it never collides with the cache units (11/14/15),
# the live evaluation unit (-1) or the twins (0).
PREFIJO_ALTA = -1000


def normalizar_matricula(texto) -> str:
    """Matricula normalizada; vacia o corta es un error, no un valor por defecto.

    Reuses `twin.normalizar_id` rather than defining a second normaliser: two
    normalisers are two places to fix the same bug.
    """
    return T.normalizar_id(texto)


def etiqueta(clave, registro: dict | None = None) -> str:
    """Human label for a registry key.

    Cache keys delegate to `L.UNIT_LABELS` and are never retyped here. Any other
    key — an alta matricula or a twin id — is its own label, because the
    operator typed it and that is what they recognise.
    """
    clave = str(clave)
    if clave.startswith("U") and clave[1:].isdigit():
        unidad = int(clave[1:])
        return L.UNIT_LABELS.get(unidad, f"Unidad {unidad}")
    return clave


def clave_de(unidad_float, registro: dict | None = None) -> str:
    """Float unit -> registry key.

    Degrades to `f"U{int(u)}"` for any float absent from the registry, so the
    cache keeps working without explicit entries: unit 14 becomes `U14`, which
    is what the hangar already used. An alta's negative id resolves back to its
    matricula, which is the whole point of the registry.
    """
    unidad = float(unidad_float)
    if registro:
        for clave, alta in (registro.get(ALTAS_KEY) or {}).items():
            if float(alta.get("unit_id", 0)) == unidad:
                return str(clave)
    return f"U{int(unidad)}"


def unidad_de(clave, registro: dict | None = None) -> float:
    """Registry key -> float unit. Inverse of `clave_de`."""
    clave = str(clave)
    if registro:
        alta = (registro.get(ALTAS_KEY) or {}).get(clave)
        if alta:
            return float(alta["unit_id"])
    if clave.startswith("U") and clave[1:].isdigit():
        return float(clave[1:])
    return float("nan")


def _proximo_indice(registro: dict) -> int:
    """Counter that only grows, so a removed id is never handed out again.

    `len(altas)` was the old source and it collided: remove the first of two and
    the next alta reuses the second one's id. The counter is an explicit,
    non-negative integer kept per alta, so removing one cannot move it back.
    """
    altas = registro.get(ALTAS_KEY) or {}
    if not altas:
        return 0
    return max(int(alta["indice"]) for alta in altas.values()) + 1


def registrar_alta(registro: dict, matricula: str, unidad_cache: int,
                   ciclo: int) -> dict:
    """Adds an alta with a fresh id and creates its twin.

    The twin is built from windows the cache already scored — `ventanas_de_alta`
    plus `twin.make_twin` — so the engine appears in "Gemelos registrados" with
    a saved series. No model call: the alta takes history that already exists.

    Raises `ValueError` when the unit has no windows up to `ciclo`, naming the
    first scored cycle, and when the matricula is already registered.
    """
    clave = normalizar_matricula(matricula)
    altas = dict(registro.get(ALTAS_KEY) or {})
    if clave in altas:
        raise ValueError(f"ya hay una aeronave de alta con la matricula {clave}")
    ventanas = A.ventanas_de_alta(
        L.get_windows(), int(unidad_cache), int(ciclo), 0.0)
    indice = _proximo_indice(registro)
    altas[clave] = {
        "unit_id": float(PREFIJO_ALTA - indice),
        "indice": indice,
        "unidad_cache": int(unidad_cache),
        "ciclo": int(ciclo),
        "ventanas": int(len(ventanas)),
    }
    nuevo = dict(registro)
    nuevo[ALTAS_KEY] = altas
    return nuevo


def quitar_alta(registro: dict, matricula: str) -> dict:
    """Removes an alta. The id it held is not recycled."""
    clave = normalizar_matricula(matricula)
    altas = {k: v for k, v in (registro.get(ALTAS_KEY) or {}).items() if k != clave}
    nuevo = dict(registro)
    nuevo[ALTAS_KEY] = altas
    return nuevo


def serializar(registro: dict) -> str:
    """JSON text, so the dashboard writes the same shape it reads."""
    return json.dumps(registro, ensure_ascii=False, indent=1)


def cargar(ruta: str) -> dict:
    """Reads the registry; a missing file is an empty registry, not an error."""
    if not os.path.exists(ruta):
        return {}
    with open(ruta, encoding="utf-8") as fh:
        return dict(json.load(fh))
