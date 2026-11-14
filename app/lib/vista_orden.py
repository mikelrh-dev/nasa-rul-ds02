"""Vista previa legible de la orden de mantenimiento.

El documento exportado (JSON/PDF/CSV) conserva el objeto estructurado
`ventana_evaluada`; la vista previa lo convierte en texto para que nadie tenga que
leer una serializacion interna.
"""
from __future__ import annotations

import pandas as pd


def tabla_orden(bloqueadas: list[dict]) -> pd.DataFrame:
    """Frame de lectura con columnas en title case y metadatos como texto."""
    columnas = ["Unidad", "Estado", "Regla", "Ventana evaluada", "Ciclo simulado",
                "Ciclo evaluado", "RUL estimada", "L_inf", "L_sup", "RUL real",
                "Acción"]
    filas = []
    for u in bloqueadas:
        ventana = u.get("ventana_evaluada") or {}
        filas.append({
            "Unidad": int(u["unidad"]),
            "Estado": str(u.get("estado", "")),
            "Regla": str(u.get("regla", "")),
            "Ventana evaluada": (
                f"ciclo {int(ventana.get('ciclo', -1))} · "
                f"{int(ventana.get('filas', 0))} filas · paso "
                f"{int(ventana.get('step', 0))}"
            ),
            "Ciclo simulado": int(u.get("ciclo_simulado", -1)),
            "Ciclo evaluado": int(u.get("ciclo_evaluado", -1)),
            "RUL estimada": round(float(u.get("rul_estimada", float("nan"))), 2),
            "L_inf": round(float(u.get("limite_inferior", float("nan"))), 2),
            "L_sup": round(float(u.get("limite_superior", float("nan"))), 2),
            "RUL real": ("" if u.get("rul_real") is None else float(u["rul_real"])),
            "Acción": str(u.get("accion", "")),
        })
    return pd.DataFrame(filas, columns=columnas)
