"""Casos de prueba (MIA). Cada caso es una ficha con la decision esperada.

Los casos de estado salen de la particion de test congelada: la ventana que
termina en `(unidad, ciclo)` se corta de la cache de telemetria
(`app/cache/ds02_rows.parquet`) y el historial son las ventanas anteriores de
esa misma unidad (`app/cache/ds02_windows.parquet`), en orden de ciclo. El
historial es lo que hace posible la regla de monotonía: sin pasado no hay
restriccion que imponer.

El caso de seguridad es sintetico a proposito: lleva un dato imposible y un
punto valido, de modo que si la regla de seguridad no ganara, las de estado
decidirian igual.

`probar_casos(reglas_correccion, reglas_decision, predecir, motor)` pasa cada
caso por el modelo y por el motor y escribe BIEN o MAL.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd

from modelo import COLUMNAS, predecir  # noqa: F401  (se reexporta para el notebook)

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROWS_PATH = os.path.join(RAIZ, "app", "cache", "ds02_rows.parquet")
WINDOWS_PATH = os.path.join(RAIZ, "app", "cache", "ds02_windows.parquet")
UMBRAL_APTO = 30.0
UMBRAL_HANGAR = 25.0

# (nombre, unidad, ciclo, decision esperada). `unidad=None` -> caso de seguridad.
CASOS = [
    ("U11 ciclo 1 (inicio de vida)", 11, 1, "APTO"),
    ("U11 ciclo 21 (inspeccion)", 11, 21, "INSPECCION"),
    ("U11 ciclo 26 (hangar)", 11, 26, "HANGAR"),
    ("U14 ciclo 3 (inicio de vida)", 14, 3, "APTO"),
    ("U14 ciclo 30 (inspeccion)", 14, 30, "INSPECCION"),
    ("U14 ciclo 60 (hangar)", 14, 60, "HANGAR"),
    ("U15 ciclo 20 (pleno servicio)", 15, 20, "APTO"),
    ("U15 ciclo 26 (hangar)", 15, 26, "HANGAR"),
    ("Dato imposible", None, None, "SIN_DECISION"),
]

_rows = None
_windows = None


def _datos():
    global _rows, _windows
    if _rows is None:
        _rows = pd.read_parquet(ROWS_PATH)
        _windows = pd.read_parquet(WINDOWS_PATH)
    return _rows, _windows


def hay_cache() -> bool:
    return os.path.exists(ROWS_PATH) and os.path.exists(WINDOWS_PATH)


def ventana(unidad: int, ciclo: int):
    """Corta la ventana que termina en `ciclo` y devuelve `(X_raw, historial, ciclo_real)`."""
    rows, windows = _datos()
    filas = rows[rows["unit"] == int(unidad)].reset_index(drop=True)
    anteriores = windows[(windows["unit"] == int(unidad))
                        & (windows["cycle"] <= int(ciclo))]
    if anteriores.empty or filas.empty:
        return None
    orden = anteriores.sort_values(["cycle", "start_index"], kind="stable")
    actual = orden.iloc[-1]
    inicio = int(actual["start_index"])
    if inicio + len(COLUMNAS) > len(filas) or inicio + 50 > len(filas):
        return None
    X = (filas.iloc[inicio:inicio + 50][COLUMNAS]
         .to_numpy(dtype=np.float32).reshape(1, 50, len(COLUMNAS)))
    historial = [
        (float(c), float(p))
        for c, p in zip(orden["cycle"].iloc[:-1], orden["pred"].iloc[:-1])
    ]
    return X, historial, float(actual["cycle"])


def ficha_de(nombre: str, unidad: int, ciclo: int) -> dict:
    """Ficha de un motor real: ventana + historial, sin decision todavia."""
    recorte = ventana(unidad, ciclo)
    if recorte is None:
        raise ValueError(f"no hay ventana para U{unidad} en el ciclo {ciclo}")
    X, historial, ciclo_real = recorte
    return {
        "nombre": nombre,
        "unidad": float(unidad),
        "ciclo": ciclo_real,
        "X_raw": X,
        "historial": historial,
        "alertas_datos": [],
        "umbrales": {"apto": UMBRAL_APTO, "hangar": UMBRAL_HANGAR},
    }


def ficha_invalida() -> dict:
    """Caso de seguridad: dato imposible con un punto valido que decidiria igual."""
    return {
        "nombre": "Dato imposible",
        "unidad": 11.0,
        "ciclo": 42.0,
        "X_raw": np.zeros((1, 50, len(COLUMNAS)), dtype=np.float32),
        "historial": [],
        "alertas_datos": [
            "canal T48 fuera de rango fisico (temperatura < 0 R)",
            "la columna ciclo disminuye dentro de la ventana",
        ],
        "umbrales": {"apto": UMBRAL_APTO, "hangar": UMBRAL_HANGAR},
        "rul_punto": 40.0,
        "limite_inferior": 15.0,
        "limite_superior": 65.0,
    }


def probar_casos(reglas_correccion: list, reglas_decision: list,
                 predecir_fn, motor_fn, ver: bool = False) -> list[dict]:
    """Pasa cada caso por el modelo y por el motor; devuelve una fila por caso."""
    filas = []
    for nombre, unidad, ciclo, esperada in CASOS:
        if unidad is None:
            caso = ficha_invalida()
        else:
            if not hay_cache():
                continue
            caso = ficha_de(nombre, unidad, ciclo)
            predecir_fn(caso)
        r = motor_fn(caso, reglas_correccion, reglas_decision, ver=ver)
        filas.append({
            "caso": nombre,
            "unidad": caso.get("unidad"),
            "ciclo": caso.get("ciclo"),
            "punto": caso.get("rul_punto"),
            "L_inf": caso.get("limite_inferior"),
            "reglas usadas": " -> ".join(r["usadas"]),
            "decision": r["decision"],
            "esperada": esperada,
            "bien": "BIEN" if r["decision"] == esperada else "MAL",
        })
    return filas


def main() -> None:
    from motor import motor, resumen
    from reglas import REGLAS_CORRECCION, REGLAS_DECISION

    print(f"Hay {len(REGLAS_CORRECCION) + len(REGLAS_DECISION)} reglas en mia/reglas.py")
    for caso in probar_casos(REGLAS_CORRECCION, REGLAS_DECISION, predecir, motor):
        marca = "OK " if caso["bien"] == "BIEN" else "!! "
        print(f"{marca}{caso['caso']:32s} -> {str(caso['decision']):14s} "
              f"(esperada {caso['esperada']})  [{caso['reglas usadas']}]")


if __name__ == "__main__":
    main()
