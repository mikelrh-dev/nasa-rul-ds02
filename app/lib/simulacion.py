"""Turn-advance simulator: the fleet clock and the held engines.

The cache already holds a scored window per cycle (U11: 59 cycles, U14: 74,
U15: 66). Advancing the fleet is therefore a *read*, not a computation: this
module never calls the model.

Re-scoring would not reproduce the cache anyway. The point estimate is
EMA-smoothed causally (`ensemble.py:158`, `causal_ema_by_unit(..., span=5)`), so
an isolated window starts the EMA cold; and the cache is built at `step=2`
while live scoring uses `step=1`. Measured on U14 at cycle 76: 0,6692 live
against 0,8654 cached. Making the wall and the twin disagree about the same
engine would cost the traceability this project sells.

No es un módulo puro: importa `flota`, que a su vez importa `ui_data_loader`
(Streamlit). El bucle de turnos no escribe y se testea con el runtime de
Streamlit.
"""
from __future__ import annotations

import pandas as pd


def _peor_ventana(grupo: pd.DataFrame, ciclo: int) -> pd.Series | None:
    """Worst window of a unit at `ciclo` (the lowest lower bound).

    A unit with no window at or before `ciclo` has not flown yet: it is not
    held, it is simply clamped, exactly as `fleet_snapshot` already does.
    """
    hasta = grupo[grupo["cycle"] <= ciclo]
    if hasta.empty:
        return None
    return hasta.loc[hasta["lower"].idxmin()]


def retenidos(frame: pd.DataFrame, ciclo: int, umbrales: dict) -> set[int]:
    """Engines that may not fly: their `L_inf` at `ciclo` is below the threshold.

    The decision rule is the same one the badge already uses — `L_inf`, never
    the point estimate. This function only asks it of the cached rows; it does
    not re-decide anything.
    """
    retenidos: set[int] = set()
    for unidad, grupo in frame.groupby("unit"):
        peor = _peor_ventana(grupo, ciclo)
        if peor is not None and float(peor["lower"]) < float(umbrales["hangar"]):
            retenidos.add(int(unidad))
    return retenidos


def ciclos_hasta_fallo(frame: pd.DataFrame, ciclo: int, umbrales: dict) -> dict:
    """Cycles from `ciclo` until each engine's `L_inf` crosses the threshold.

    Read from the cache: it answers "what happens if I keep flying" without a
    single inference call. `None` means the engine never crosses inside the
    recorded life.
    """
    faltan: dict[int, int | None] = {}
    for unidad, grupo in frame.groupby("unit"):
        cruce = grupo[grupo["lower"] < float(umbrales["hangar"])]
        cruce = cruce[cruce["cycle"] > ciclo]
        faltan[int(unidad)] = (int(cruce["cycle"].min() - ciclo)
                               if not cruce.empty else None)
    return faltan


def resumen_ciclos_hasta_fallo(faltan: dict, actuales: dict, umbral: float) -> dict:
    """Frase por unidad para la cuenta atras del panel de flota.

    `ciclos_hasta_fallo` responde «cuando vuelve a cruzar»; esta funcion responde
    «que debe leer el operador ahora»: una unidad ya por debajo no es que se acerque.
    """
    resumen = {}
    for unidad, falta in faltan.items():
        actual = actuales.get(unidad)
        if actual is not None and float(actual) < float(umbral):
            resumen[unidad] = "ya por debajo del umbral"
        elif falta is None:
            resumen[unidad] = "nunca en la vida registrada"
        else:
            resumen[unidad] = f"{falta} ciclos"
    return resumen
