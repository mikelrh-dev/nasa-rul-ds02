"""Hangar lifecycle as a pure state machine.

The rules engine (`mia/`) answers one question: *is this unit groundable?* This
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


def guardar_disco(registros: dict, ruta: str) -> None:
    """Persiste los registros de hangar en JSON (recargar no los borra)."""
    import json as _json

    with open(ruta, "w", encoding="utf-8") as fh:
        _json.dump(registros, fh, ensure_ascii=False, indent=1)


def cargar_disco(ruta: str) -> dict:
    """Lee los registros persistidos; si no existen, devuelve un dict vacío."""
    import json as _json
    import os as _os

    if not _os.path.exists(ruta):
        return {}
    with open(ruta, encoding="utf-8") as fh:
        return dict(_json.load(fh))
