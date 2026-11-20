"""Simulador de avance de turnos: el reloj de la flota y los motores retenidos.

La caché ya guarda una ventana puntuada por ciclo (U11: 59 ciclos, U14: 74,
U15: 66). Avanzar la flota es por tanto una *lectura*, no un cálculo: este módulo
nunca llama al modelo.

Además, volver a puntuar no reproduciría la caché. La estimación puntual se
suaviza con una EMA causal (`ensemble.py:158`, `causal_ema_by_unit(..., span=5)`),
así que una ventana aislada arranca la EMA en frío; y la caché se construyó con
`step=2` mientras el puntuado en vivo usa `step=1`. Medido en U14 en el ciclo 76:
0,6692 en vivo frente a 0,8654 en caché. Que el muro y el gemelo discreparan
sobre el mismo motor costaría la trazabilidad que vende el proyecto.

No es un módulo puro: importa `flota`, que a su vez importa `ui_data_loader`
(Streamlit). El bucle de turnos no escribe y se prueba con el runtime de
Streamlit.
"""
from __future__ import annotations

import pandas as pd


def _peor_ventana(grupo: pd.DataFrame, ciclo: int) -> pd.Series | None:
    """Peor ventana de una unidad en `ciclo` (el límite inferior más bajo).

    Una unidad sin ventana en `ciclo` o antes todavía no ha volado: no se retiene,
    solo se recorta, igual que ya hace `fleet_snapshot`.
    """
    hasta = grupo[grupo["cycle"] <= ciclo]
    if hasta.empty:
        return None
    return hasta.loc[hasta["lower"].idxmin()]


def retenidos(frame: pd.DataFrame, ciclo: int, umbrales: dict) -> set[int]:
    """Motores que no pueden volar: su `L_inf` en `ciclo` está bajo el umbral.

    La regla de decisión es la misma que ya usa la insignia: `L_inf`, nunca la
    estimación puntual. Esta función solo la aplica a las filas cacheadas; no
    vuelve a decidir nada.
    """
    retenidos: set[int] = set()
    for unidad, grupo in frame.groupby("unit"):
        peor = _peor_ventana(grupo, ciclo)
        if peor is not None and float(peor["lower"]) < float(umbrales["hangar"]):
            retenidos.add(int(unidad))
    return retenidos


def ciclos_hasta_fallo(frame: pd.DataFrame, ciclo: int, umbrales: dict) -> dict:
    """Ciclos desde `ciclo` hasta que el `L_inf` de cada motor cruza el umbral.

    Se lee de la caché: responde "qué pasa si sigo volando" sin una sola llamada
    de inferencia. `None` significa que el motor no cruza dentro de la vida
    registrada.
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
