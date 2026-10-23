"""Alta rápida y estado demo: mapeo puro perfil -> (unidad, ciclo), sin Streamlit.

Este módulo no importa Streamlit para poder probarlo sin levantar la app
(misma convención que `twin.py` y `hangar.py`).
"""
from __future__ import annotations

import pandas as pd

import ui_rules as UR

# Rango negativo reservado: nunca colisiona con caché (11/14/15),
# evaluación en vivo (-1) ni gemelos (0).
PREFIJO_ALTA = -1000

# Perfil -> (unidad cacheada, ciclo hasta el que se toma la historia).
# Medido: U11 empieza en ciclo 1, U14 en 3, U15 en 2.
PERFILES = {
    "Recién salido de revisión": (11, 1),
    "Recién salido de revisión (U15)": (15, 2),
    "Desgaste operativo medio": (11, 20),
    "Desgaste operativo medio (U14)": (14, 20),
    "Fin de vida / crítico": (14, 29),
    "Fin de vida / crítico (U11)": (11, 22),
    "Caso atípico (U14)": (14, 3),
}


def unidad_alta(indice: int) -> float:
    """Id sintético de aeronave de alta. Negativo y reservado."""
    return float(PREFIJO_ALTA - int(indice))


def ventanas_de_alta(
    windows: pd.DataFrame, unidad: int, ciclo_hasta: int, unit_id: float
) -> pd.DataFrame:
    """Ventanas ya puntuadas de `unidad` hasta `ciclo_hasta`, con id sintético.

    Conserva pred/lower/upper/y_true de la caché: no se repuntúa nada.
    Solo cambia `unit`, la clave de agrupación de `unit_curve`/`fleet_snapshot`.
    """
    recorte = windows[
        (windows["unit"] == int(unidad)) & (windows["cycle"] <= int(ciclo_hasta))
    ].copy()
    if recorte.empty:
        del_cache = windows[windows["unit"] == int(unidad)]
        primero = (
            int(del_cache["cycle"].min()) if not del_cache.empty else "¿unidad inexistente?"
        )
        raise ValueError(
            f"la unidad {unidad} no tiene ventanas hasta el ciclo {ciclo_hasta}; "
            f"su primer ciclo puntuado es el {primero}"
        )
    recorte["unit"] = float(unit_id)
    return recorte


def frame_con_altas(
    frame_cache: pd.DataFrame,
    windows: pd.DataFrame,
    altas: list[dict],
    aplicar_reglas: bool,
    umbrales: dict,
) -> pd.DataFrame:
    """`frame_cache` más las aeronaves de alta, con su decisión aplicada.

    Función pura: no lee session_state, recibe `altas` como parámetro.
    Métricas y telemetría usan `frame_cache` para no contar doble.
    """
    if not altas:
        return frame_cache
    extras = pd.concat(
        [
            ventanas_de_alta(windows, alta["unidad"], alta["ciclo"], alta["unit_id"])
            for alta in altas
        ],
        ignore_index=True,
    )
    if aplicar_reglas:
        extras = UR.corregir_ventanas(extras)
    extras = UR.decidir_ventanas(extras, umbrales)
    return pd.concat([frame_cache, extras], ignore_index=True)


def estado_demo() -> dict:
    """Estado exacto desde el que se cuenta la historia: 30/25, ciclo 29, U14."""
    return {"umbrales": (30.0, 25.0), "ciclo": 29, "unidad": 14}
