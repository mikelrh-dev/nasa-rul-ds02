"""La recepcionista que aplica las reglas (MIA): dos pasadas limpias.

Es el mismo motor del E2, con una diferencia estructural: las reglas de
**correccion** y las de **decision** escriben campos distintos de la ficha, y
mezclarlas en una sola pasada hace que la traza deje de explicar nada. Asi que
el motor recorre primero la pasada B (correccion) y despues la pasada A
(decision).

Cada pasada aplica, en rondas, la regla de mayor prioridad que se cumpla; una
regla se aplica una sola vez por pasada, de modo que el encadenado termina
siempre. `ver=True` cuenta lo que hace en cada vuelta.

Devuelve `{"decision", "usadas", "porque"}`.
"""
from __future__ import annotations

MAX_VUELTAS = 32


def motor(caso: dict, reglas_correccion: list, reglas_decision: list,
          ver: bool = False) -> dict:
    """Aplica la pasada B y luego la pasada A sobre la ficha del caso."""
    usadas: list[str] = []
    porque: list[str] = []

    for pasada, reglas in (("B", reglas_correccion), ("A", reglas_decision)):
        restantes = list(reglas)
        vuelta = 0
        while restantes and vuelta < MAX_VUELTAS:
            candidatas = [r for r in restantes if r[1](caso)]
            if not candidatas:
                break
            regla = max(candidatas, key=lambda r: r[3])
            restantes.remove(regla)

            efecto = regla[2](caso) if callable(regla[2]) else dict(regla[2])
            caso.update(efecto)
            usadas.append(regla[0])
            porque.append(f"{regla[0]}: {regla[4]}")
            vuelta += 1
            if ver:
                nombres = [r[0] for r in candidatas]
                print(f"Pasada {pasada} · vuelta {vuelta}: se cumplen {nombres} "
                      f"-> se aplica {regla[0]} -> apunta {efecto}")

    return {
        "decision": caso.get("decision"),
        "usadas": usadas,
        "porque": porque,
    }


def resumen(caso: dict, resultado: dict) -> str:
    """Linea legible del resultado, para imprimir o pintar."""
    reglas = " -> ".join(resultado["usadas"]) or "(ninguna)"
    return f"{caso.get('nombre', 'caso')}: {resultado['decision']}   (reglas: {reglas})"
