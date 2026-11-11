"""Hangar lifecycle as a pure state machine.

The rules engine (`src/mia/`) answers one question: *is this unit groundable?* This
module answers the next one: *what happened to it afterwards?* Keeping them apart
matters — the rule engine's figures are reproduced by the evidence gate, while the
hangar is operational bookkeeping that no gate measures.

A record stores the decision that **opened** it, with the thresholds in force at
that moment. Moving a slider later must not rewrite history, so `revision()` can
say both things at once: what the record says, and what today's policy would say.

No Streamlit here: the module is imported by the dashboard and asserted by tests.
"""
from __future__ import annotations

from datetime import datetime, timezone

import json as _json
import os as _os
import re as _re
import shutil as _shutil
import threading as _threading

from app import _paths

EN_SERVICIO = "EN_SERVICIO"
INSPECCION = "INSPECCION_PROGRAMADA"
AOG = "AOG_DERIVADO"
TALLER = "EN_TALLER"
BANCO = "PRUEBA_EN_BANCO"

ESTADOS = (EN_SERVICIO, INSPECCION, AOG, TALLER, BANCO)
ABIERTOS = (INSPECCION, AOG, TALLER, BANCO)

TRANSICIONES = {
    EN_SERVICIO: (INSPECCION, AOG),
    INSPECCION: (AOG, EN_SERVICIO),
    AOG: (TALLER,),
    TALLER: (BANCO,),
    BANCO: (EN_SERVICIO, AOG),
}

ETIQUETAS = {
    EN_SERVICIO: "En servicio",
    INSPECCION: "Inspección programada",
    AOG: "Derivado a hangar",
    TALLER: "En taller",
    BANCO: "Prueba en banco",
}

# Lo que más urge, primero. Una unidad derivada manda sobre una en banco.
RANGO = {AOG: 0, TALLER: 1, BANCO: 2, INSPECCION: 3, EN_SERVICIO: 4}


def _ahora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def permitidas(estado: str) -> tuple[str, ...]:
    """Estados a los que se puede pasar desde `estado`."""
    return TRANSICIONES.get(estado, ())


def abrir(unidad: str, ciclo: int, lower: float, umbrales: dict,
          regla: str, estado: str = AOG, nota: str = "", ahora: str | None = None) -> dict:
    """Abre un registro con la decisión de entrada congelada.

    `estado` tiene que ser el que la decisión produce; se acepta como parámetro
    para poder registrar una inspección programada con el mismo mecanismo.
    """
    if estado not in ESTADOS:
        raise ValueError(f"estado desconocido: {estado}")
    return {
        "unidad": str(unidad),
        "estado": estado,
        "entrada": {
            "ciclo": int(ciclo),
            "lower": float(lower),
            "umbrales": {"apto": float(umbrales["apto"]),
                         "hangar": float(umbrales["hangar"])},
            "regla": str(regla),
        },
        "eventos": [{
            "estado": estado,
            "ciclo": int(ciclo),
            "at": ahora or _ahora(),
            "nota": nota,
        }],
    }


def avanzar(registro: dict, destino: str, ciclo: int, nota: str = "",
            ahora: str | None = None) -> dict:
    """Devuelve una copia del registro en `destino`; rechaza transiciones ilegales."""
    actual = registro["estado"]
    if destino not in permitidas(actual):
        validas = ", ".join(permitidas(actual)) or "(ninguna)"
        raise ValueError(
            f"transición no permitida: {actual} → {destino}; desde aquí solo "
            f"se puede ir a {validas}"
        )
    nuevo = {**registro, "estado": destino,
             "eventos": list(registro["eventos"]) + [{
                 "estado": destino,
                 "ciclo": int(ciclo),
                 "at": ahora or _ahora(),
                 "nota": nota,
             }]}
    return nuevo


def cola(registros: dict) -> list[dict]:
    """Registros abiertos, de mayor a menor urgencia.

    Ordena por estado y, dentro de él, por el límite inferior congelado: lo que
    entró más cerca del fallo se atiende antes.
    """
    abiertos = [r for r in registros.values() if r["estado"] in ABIERTOS]
    return sorted(abiertos, key=lambda r: (RANGO.get(r["estado"], 9),
                                           r["entrada"]["lower"],
                                           r["unidad"]))


def revision(registro: dict, umbrales: dict, decision_hoy: str) -> dict:
    """Contrasta la decisión congelada con la que tomaría la política de hoy."""
    congelada = registro["entrada"]
    congelado = ("HANGAR" if congelada["lower"] < congelada["umbrales"]["hangar"]
                 else ("APTO" if congelada["lower"] >= congelada["umbrales"]["apto"]
                       else "INSPECCION"))
    return {
        "congelada": congelado,
        "hoy": decision_hoy,
        "cambia": decision_hoy != congelado,
        "lower": congelada["lower"],
        "umbrales_entrada": dict(congelada["umbrales"]),
        "umbrales_hoy": {"apto": float(umbrales["apto"]),
                         "hangar": float(umbrales["hangar"])},
    }


def reiniciar(registro: dict, ciclo: int, nota: str = "",
              ahora: str | None = None) -> dict:
    """Devuelve el registro a servicio tras un replay de la vida registrada.

    No pasa por `avanzar` porque no es una transicion legal del ciclo: es la
    salida del taller, y la cache no tiene datos de un motor reparado. Lo que
    vuelve a volar es la vida grabada desde el principio, y el evento lo dice
    en sus propias palabras para que el documento no claima una reparacion.
    """
    eventos = list(registro["eventos"]) + [{
        "estado": EN_SERVICIO,
        "ciclo": int(ciclo),
        "at": ahora or _ahora(),
        "nota": nota or ("replay de la vida registrada: la cache no tiene "
                         "datos de un motor reparado"),
    }]
    return {**registro, "estado": EN_SERVICIO, "eventos": eventos,
            "replay_desde": int(ciclo)}


def resumen(registros: dict) -> dict:
    """Cuántas unidades hay en cada estado y cuántas siguen abiertas."""
    por_estado = {estado: 0 for estado in ESTADOS}
    for registro in registros.values():
        por_estado[registro["estado"]] = por_estado.get(registro["estado"], 0) + 1
    return {
        "total": len(registros),
        "abiertos": sum(por_estado[e] for e in ABIERTOS),
        "por_estado": por_estado,
    }


_SESSION_ID_RE = _re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_REGISTRY_LOCK = _threading.Lock()
_REGISTRY_KEYS = ("twins", "hangar", "altas")


def empty_registry() -> dict:
    """Registro vacío con la forma que espera el tablero."""
    return {k: {} for k in _REGISTRY_KEYS}


def validate_session_id(session_id) -> str:
    """Id seguro para fichero (`^[A-Za-z0-9_-]{1,64}$`); si no, ValueError."""
    texto = str(session_id or "")
    if not _SESSION_ID_RE.match(texto):
        raise ValueError(f"session_id inválido: {texto!r}")
    return texto


def session_registry_path(session_id) -> str:
    """Ruta del registro de una sesión, derivada solo del id validado."""
    sid = validate_session_id(session_id)
    base = _os.path.dirname(str(_paths.REGISTROS_PATH))
    return _os.path.join(base, "registros_sesiones", f"registros_flota_{sid}.json")


def validate_registry_schema(data) -> dict:
    """Exige un mapeo con `twins`/`hangar`/`altas`; intacto si es válido."""
    if not isinstance(data, dict):
        raise ValueError("el registro debe ser un mapeo con twins/hangar/altas")
    for clave in _REGISTRY_KEYS:
        if clave not in data:
            raise ValueError(f"al registro le falta la colección {clave!r}")
        if not isinstance(data[clave], (dict, list)):
            raise ValueError(f"la colección {clave!r} debe ser dict o lista")
    return data


def atomic_save_json(path: str, data) -> None:
    """Escribe `{path}.tmp`, fsync y renombra atómico; con lock compartido."""
    tmp = f"{path}.tmp"
    with _REGISTRY_LOCK:
        _os.makedirs(_os.path.dirname(_os.path.abspath(path)), exist_ok=True)
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                _json.dump(data, fh, ensure_ascii=False, indent=1)
                fh.flush()
                _os.fsync(fh.fileno())
            _os.replace(tmp, path)
        finally:
            if _os.path.exists(tmp):
                _os.remove(tmp)


def save_session_registry(path: str, data: dict) -> None:
    """Valida primero; si el esquema falla, el fichero no se toca."""
    validate_registry_schema(data)
    atomic_save_json(path, data)


def load_json_dict(path: str, backup_path: str | None = None) -> dict:
    """Lee un dict JSON; ausente o corrupto cae a backup o a `{}`."""
    if not _os.path.exists(path):
        return {}
    try:
        with open(path, encoding="utf-8") as fh:
            valor = _json.load(fh)
        return dict(valor) if isinstance(valor, dict) else {}
    except (OSError, ValueError):
        backup = backup_path or f"{path}.bak"
        if backup and _os.path.exists(backup):
            try:
                with open(backup, encoding="utf-8") as fh:
                    valor = _json.load(fh)
                return dict(valor) if isinstance(valor, dict) else {}
            except (OSError, ValueError):
                pass
        return {}


def load_session_registry_with_status(
    path: str, backup_path: str | None = None
) -> tuple[dict, str | None]:
    """Carga el registro; corrupto/schema cae a backup o a vacío con aviso."""
    if not _os.path.exists(path):
        return empty_registry(), None
    try:
        with open(path, encoding="utf-8") as fh:
            data = _json.load(fh)
        validate_registry_schema(data)
        return data, None
    except (OSError, ValueError) as exc:
        backup = backup_path or f"{path}.bak"
        if backup and _os.path.exists(backup):
            try:
                with open(backup, encoding="utf-8") as fh:
                    data = _json.load(fh)
                validate_registry_schema(data)
                return data, f"registro corrupto ({exc}); recuperado del backup"
            except (OSError, ValueError):
                pass
        return empty_registry(), f"registro corrupto ({exc}); se empieza vacío"


def load_session_registry(path: str, backup_path: str | None = None) -> dict:
    """Carga el registro con fallback a backup; nunca rompe el tablero."""
    data, _aviso = load_session_registry_with_status(path, backup_path)
    return data


def migrate_legacy_registry(
    legacy_path: str, session_path: str, bak_path: str | None = None
) -> dict:
    """Copia (nunca mueve) el legacy a la sesión; .bak + count-check, aborta sin parcial."""
    bak = bak_path or f"{legacy_path}.bak"
    if not _os.path.exists(legacy_path):
        vacio = empty_registry()
        atomic_save_json(session_path, vacio)
        return {k: 0 for k in _REGISTRY_KEYS}
    _shutil.copy2(legacy_path, bak)
    with open(legacy_path, encoding="utf-8") as fh:
        data = _json.load(fh)
    validate_registry_schema(data)
    antes = {k: len(data[k]) for k in _REGISTRY_KEYS}
    atomic_save_json(session_path, data)
    with open(session_path, encoding="utf-8") as fh:
        despues_data = validate_registry_schema(_json.load(fh))
    despues = {k: len(despues_data[k]) for k in _REGISTRY_KEYS}
    if despues != antes:
        if _os.path.exists(session_path):
            _os.remove(session_path)
        raise ValueError(
            f"migración abortada: conteo {despues} != legacy {antes}; "
            "sin datos parciales, legacy restorable desde el .bak"
        )
    return despues


def guardar_disco(registros: dict, ruta: str) -> None:
    """Persiste los registros de hangar en JSON (atómico, con lock)."""
    atomic_save_json(ruta, registros)


def cargar_disco(ruta: str) -> dict:
    """Lee los registros; ausente o corrupto cae a backup o a `{}`."""
    return load_json_dict(ruta)
