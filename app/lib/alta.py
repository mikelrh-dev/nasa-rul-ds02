"""Alta rápida y estado demo: mapeo puro perfil -> (unidad, ciclo), sin Streamlit.

Este módulo no importa Streamlit para poder probarlo sin levantar la app
(misma convención que `twin.py` y `hangar.py`). Los umbrales salen de
`app/lib/_constantes.py`, que tampoco importa Streamlit.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from app.lib import _constantes
from app.lib import rules as UR

# Rango negativo reservado: nunca colisiona con caché (11/14/15),
# evaluación en vivo (-1) ni gemelos (0).
# Dueño único de PREFIJO_ALTA; `flota` lo re-exporta (sin redefinir).
PREFIJO_ALTA = -1000

# Perfil -> (unidad cacheada, ciclo hasta el que se toma la historia).
# Medido: U11 empieza en ciclo 1, U14 en 3, U15 en 2.
PERFILES = {
    "Recién salido de revisión": (11, 1),
    "Recién salido de revisión (U15)": (15, 2),
    "Desgaste operativo medio": (11, 20),
    "Desgaste operativo medio (U14)": (14, 20),
    "Fin de vida / crítico": (14, 29),
    "Fin de vida / crítico (U11)": (11, 23),  # C: U11 L_inf<25 desde el ciclo 23
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
    return {"umbrales": (_constantes.DEFAULT_AIRWORTHY, _constantes.DEFAULT_AOG),
            "ciclo": 29, "unidad": 14}


def estado_historia(windows: pd.DataFrame, umbrales: dict) -> list[dict]:
    """Modo historia: cuatro pasos que cuentan la narrativa, derivados de la caché.

    Cada paso deja la app en un estado (unidad, ciclo, umbrales) y dice qué cuenta.
    Los ciclos salen de la caché — el primer ciclo puntuado, la primera inspección
    y la primera derivación a hangar — y el «motor problemático» es el de mayor
    RMSE. No hay constantes esparcidas: si la caché cambia, el modo historia cambia
    con ella y un test lo detecta.

    `windows` es el frame de `ui_data_loader.get_windows()` (una fila por ventana
    ya puntuada) y `umbrales` el par en vigor, del que sale el cuarto paso.
    """
    idx = windows.groupby(["unit", "cycle"])["lower"].idxmin()
    por_ciclo = (windows.loc[idx, ["unit", "cycle", "lower"]]
                 .sort_values(["unit", "cycle"]).reset_index(drop=True))

    def banda(v: float) -> str:
        """Clasifica un límite inferior con los umbrales en vigor."""
        if v >= umbrales["apto"]:
            return "APTO"
        if v >= umbrales["hangar"]:
            return "INSPECCION"
        return "HANGAR"

    def primer_ciclo(unit: int, en_banda: str | None = None) -> int:
        """Primer ciclo de un motor, o primero en un estado dado."""
        sub = por_ciclo[por_ciclo["unit"] == unit]
        if en_banda is None:
            return int(sub["cycle"].iloc[0])
        es = sub["lower"].map(banda).to_numpy()
        return int(sub["cycle"].iloc[int((es == en_banda).nonzero()[0][0])])

    rmse = {}
    for unit, grupo in windows.groupby("unit"):
        residuo = grupo["pred"].to_numpy() - grupo["y_true"].to_numpy()
        rmse[int(unit)] = float(np.sqrt(np.mean(residuo ** 2)))
    motor = max(rmse, key=rmse.get)

    base = dict(umbrales)
    blandos = {"apto": float(umbrales["apto"]) + 5.0,
               "hangar": float(umbrales["hangar"]) - 5.0}
    ciclo_hangar = primer_ciclo(motor, "HANGAR")
    return [
        {"paso": 1, "titulo": "El hangar esta mañana",
         "cuenta": "Toda la flota en verde.",
         "unidad": int(por_ciclo["unit"].iloc[0]),
         "ciclo": int(por_ciclo["cycle"].iloc[0]),
         "umbrales": base},
        {"paso": 2, "titulo": "El motor problemático",
         "cuenta": "Primera inspección programada.",
         "unidad": motor, "ciclo": primer_ciclo(motor, "INSPECCION"),
         "umbrales": base},
        {"paso": 3, "titulo": "La decisión difícil",
         "cuenta": "Derivado a hangar con la predicción puntual por encima del umbral.",
         "unidad": motor, "ciclo": ciclo_hangar, "umbrales": base},
        {"paso": 4, "titulo": "¿Y si aflojamos la política?",
         "cuenta": "Cómo cambia la flota con otros umbrales.",
         "unidad": motor, "ciclo": ciclo_hangar, "umbrales": blandos},
    ]
