"""Puente entre la caché del DS02 y la capa de reglas (`mia/`).

Toma el frame de ventanas ya cacheado y le aplica las dos reglas de correccion:

* `R2b_ISOTONICO_CAUSAL` — ajuste isotonico causal del prefijo, por unidad y ordenado
  por ciclo. Ojo: el ajuste es no creciente, la serie devuelta no necesariamente
  (ver seccion 13 de `INFORME_reglas_oof.md`).
* `R6_BANDA` — banda conformal recalibrada sobre el punto corregido, con los
  coeficientes congelados en `mia/calibracion_banda.json`.

No carga el modelo, no entrena nada y no escribe en `models/`: todo sale de la
caché y de los coeficientes congelados. El frame de salida conserva las columnas
originales como `pred_enviada` / `lower_enviada` / `upper_enviada` para que la
UI pueda mostrar ambas lecturas sin esconder ninguna.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(APP_DIR)
sys.path.insert(0, os.path.join(ROOT, "mia"))

import reglas as R  # noqa: E402

COLUMNAS_COPIA = {
    "pred": "pred_enviada",
    "lower": "lower_enviada",
    "upper": "upper_enviada",
}


def corregir_ventanas(windows: pd.DataFrame) -> pd.DataFrame:
    """Devuelve el frame con el punto corregido y la banda recalibrada.

    `pred` / `lower` / `upper` pasan a ser la lectura corregida; los valores que
    venian en la caché quedan en `*_enviada`.
    """
    frame = windows.copy()
    for origen, destino in COLUMNAS_COPIA.items():
        frame[destino] = frame[origen]

    puntos = np.empty(len(frame), dtype=np.float64)
    for unit in frame["unit"].unique():
        mascara = (frame["unit"] == unit).to_numpy()
        sub = frame.loc[mascara]
        # Orden lexicografico por (ciclo, start_index): asi el ajuste es causal.
        orden = np.lexsort((sub["start_index"].to_numpy(), sub["cycle"].to_numpy()))
        serie = sub["pred"].to_numpy(dtype=np.float64)[orden]
        posiciones = sub.index.to_numpy()[orden]
        puntos[posiciones] = R.pava_causal_no_creciente(serie)

    frame["pred"] = puntos
    lower, upper = R.banda_recalibrada_vector(puntos, R.cargar_calibracion())
    frame["lower"] = lower
    frame["upper"] = upper
    frame["corregida"] = True
    frame["correccion"] = "R2b isotonico causal + R6 banda recalibrada"
    return frame


def resumen_correccion(windows: pd.DataFrame, corregido: pd.DataFrame) -> dict:
    """Cifras que permiten ver que la correccion movio algo y cuanto."""
    cambiadas = int((corregido["pred"] != corregido["pred_enviada"]).sum())
    return {
        "ventanas": int(len(corregido)),
        "ventanas_corregidas": cambiadas,
        "porcentaje": round(100.0 * cambiadas / max(len(corregido), 1), 1),
        "delta_medio_punto": round(
            float((corregido["pred"] - corregido["pred_enviada"]).mean()), 3
        ),
        "delta_medio_l_inf": round(
            float((corregido["lower"] - corregido["lower_enviada"]).mean()), 3
        ),
    }
