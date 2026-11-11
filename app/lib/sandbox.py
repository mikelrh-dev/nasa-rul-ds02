"""Puntuación del tramo del sandbox: preflight + score + decisión.

Lógica del sandbox de estrés, separada de la UI (`app/ui/_sandbox_estres.py`)
y del entrypoint. Usa Streamlit solo para cachear el resultado por clave; el
cálculo en sí es pandas + `ui_inference` + `rules`.
"""
from __future__ import annotations

import numpy as np
import streamlit as st

from app.lib import ui_data_loader as L
from app.lib import ui_inference as INF
from app.lib import rules as UR

__all__ = ["_sandbox_puntua_cached"]


@st.cache_data(ttl=3600, show_spinner="Re-puntuando tramo con el artefacto…")
def _sandbox_puntua_cached(
    unit: int, deriva_pct: int, apto: float, hangar: float, tramo_sig: str,
    sensor: str = "T48", *, windows, telemetry,
) -> tuple:
    """Preflight + puntuación + decisión del tramo perturbado (una vez por clave).

    Devuelve `(ok, error, avisos, dec, ventas)`: `dec` es el frame decidido por
    ventana (o `None` si no puntuó). Los errores de validación/puntuación se
    devuelven como valores, no se lanzan, para que el fragment los pinte igual
    que antes.

    `windows`/`telemetry` son los frames crudos de la caché: se pasan como
    parámetro (antes vivían como globales del entrypoint) para que el dueño de
    la lógica sea este módulo. `tramo_sig` sigue identificando la caché.
    """
    _umb = {"apto": float(apto), "hangar": float(hangar)}
    _cur_sbx = L.unit_curve(windows, int(unit))
    _c_inicio = int(_cur_sbx["cycle"].min())
    _bajo = _cur_sbx[_cur_sbx["lower_min"] < _umb["hangar"]]
    _c_fin = (int(_bajo["cycle"].min()) if not _bajo.empty
              else int(_cur_sbx["cycle"].max()))
    _tramo = telemetry[(telemetry["unit"] == int(unit))
                       & (telemetry["cycle"] >= _c_inicio)
                       & (telemetry["cycle"] <= _c_fin)].reset_index(drop=True)
    _tab = _tramo[["cycle"] + INF.channel_order()].copy()
    _deriva = float(int(deriva_pct)) / 100.0
    _tab[sensor] = _tab[sensor].astype(float) * (
        1.0 + _deriva * np.linspace(0.0, 1.0, len(_tab)))
    _pf = INF.preflight(_tab)
    if not _pf["ok"]:
        return (False, _pf["error"], tuple(_pf["avisos"]), None, 0)
    try:
        _win = INF.score_table(_tab, engine_id=f"ESN-SBX-{int(unit)}")["windows"]
    except ValueError as exc:
        return (False, str(exc), tuple(_pf["avisos"]), None, 0)
    return (True, None, tuple(_pf["avisos"]),
            UR.decidir_ventanas(_win, _umb), int(len(_win)))
