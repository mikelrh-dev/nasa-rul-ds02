"""Puente entre la caché del DS02 y la capa de reglas (`src/mia/`).

Toma el frame de ventanas ya cacheado y le aplica las dos reglas de correccion:

* `R2b_ISOTONICO_CAUSAL` — ajuste isotonico causal del prefijo, por unidad y ordenado
  por ciclo. Ojo: el ajuste es no creciente, la serie devuelta no necesariamente
  (ver seccion 13 de `docs/evidencia/informes/informe-2026-10-21-reglas-oof.md`).
* `R6_BANDA` — banda conformal recalibrada sobre el punto corregido, con los
  coeficientes congelados en `src/mia/calibracion_banda.json`.

Despues corre la pasada A (`src.mia.motor`): R1_SEGURIDAD, R9_HANGAR, R8_INSPECCION
y R7_APTO deciden el estado sobre el limite inferior, con los umbrales de la
barra lateral. El estado no se reclasifica aqui: se pregunta al motor, de modo
que la UI y el cuaderno de practica aplican exactamente las mismas reglas.

No carga el modelo, no entrena nada y no escribe en `models/`: todo sale de la
caché y de los coeficientes congelados. El frame de salida conserva las columnas
originales como `pred_enviada` / `lower_enviada` / `upper_enviada` para que la
UI pueda mostrar ambas lecturas sin esconder ninguna.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.mia import motor as M  # noqa: E402
from src.mia import reglas as R  # noqa: E402

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
        posiciones = np.flatnonzero(mascara)[orden]
        puntos[posiciones] = R.pava_causal_no_creciente(serie)

    frame["pred"] = puntos
    lower, upper = R.banda_recalibrada_vector(puntos, R.cargar_calibracion())
    frame["lower"] = lower
    frame["upper"] = upper
    frame["corregida"] = True
    frame["correccion"] = "R2b isotonico causal + R6 banda recalibrada"
    return frame


# ------------------------------------------------- pasada A: decision
def alertas_de_ventana(frame: pd.DataFrame) -> list[list[str]]:
    """Alertas de validez por fila, las que alimentan `R1_SEGURIDAD`.

    La cache congelada no trae filas invalidas, asi que en el tablero la lista
    sale vacia y R1 no dispara: eso es informacion, no un fallo. Las rutas que
    aceptan datos del usuario si pueden producir alertas.
    """
    low = frame["lower"].to_numpy(dtype=np.float64)
    up = frame["upper"].to_numpy(dtype=np.float64)
    punto = frame["pred"].to_numpy(dtype=np.float64)
    alertas: list[list[str]] = []
    for i in range(len(frame)):
        fila = []
        if not np.isfinite([low[i], punto[i], up[i]]).all():
            fila.append("banda no finita en la ventana")
        elif not (low[i] <= punto[i] <= up[i]):
            fila.append("la banda no contiene a su punto")
        if np.isfinite(low[i]) and low[i] < 0.0:
            fila.append("limite inferior negativo")
        alertas.append(fila)
    return alertas


def decidir_ventanas(frame: pd.DataFrame, umbrales: dict,
                     alertas: list[list[str]] | None = None) -> pd.DataFrame:
    """Aplica la pasada A del motor (`src.mia.motor`) a cada ventana.

    Devuelve el frame con `decision`, `regla_decision` y `motivo_decision`. La
    decision se lee del limite inferior y de los umbrales en vigor, no del punto.
    """
    if alertas is None:
        alertas = alertas_de_ventana(frame)
    umbrales = {"apto": float(umbrales["apto"]), "hangar": float(umbrales["hangar"])}
    decisiones, reglas, motivos = [], [], []
    for limite, fila_alertas in zip(frame["lower"].to_numpy(dtype=np.float64), alertas):
        resultado = M.motor(
            {"limite_inferior": float(limite),
             "alertas_datos": list(fila_alertas),
             "umbrales": umbrales},
            [], R.REGLAS_DECISION,
        )
        decisiones.append(resultado["decision"])
        reglas.append(" + ".join(resultado["usadas"]))
        motivos.append(" \u00b7 ".join(resultado["porque"]))

    out = frame.copy()
    out["decision"] = decisiones
    out["regla_decision"] = reglas
    out["motivo_decision"] = motivos
    return out


def estado_por_ciclo(frame: pd.DataFrame) -> pd.DataFrame:
    """Peor decision de cada (unidad, ciclo), leida de la fila mas restrictiva."""
    if "decision" not in frame.columns:
        raise ValueError("el frame no trae la pasada A; llama antes a decidir_ventanas")
    idx = frame.groupby(["unit", "cycle"])["lower"].idxmin()
    return frame.loc[idx, ["unit", "cycle", "lower", "decision",
                          "regla_decision"]].reset_index(drop=True)


def traza_decision(limite_inferior: float, umbrales: dict,
                   alertas: list[str] | None = None) -> dict:
    """Traza legible de la pasada A para una sola ficha."""
    return M.motor(
        {"limite_inferior": float(limite_inferior),
         "alertas_datos": list(alertas or []),
         "umbrales": {"apto": float(umbrales["apto"]),
                      "hangar": float(umbrales["hangar"])}},
        [], R.REGLAS_DECISION,
    )


def decision_en_vivo(result: dict, umbrales: dict) -> dict:
    """Pasada A sobre la última ventana de una evaluación en vivo.

    Es el único sitio que decide sobre una unidad aportada por el usuario, y
    decide con la **invalidez real de la banda** (`alertas_de_ventana`), igual que
    `decidir_ventanas` en la caché, el sandbox, el gemelo y el alta.

    Las cautelas de plausibilidad (`ui_inference.plausibility_warnings`) son
    avisos para el operador, no datos imposibles: su propio texto dice «se puede
    puntuar, pero…». Meterlas en `alertas_datos` activa `R1_SEGURIDAD` y devuelve
    `SIN_DECISION`, que es lo contrario de lo que el aviso afirma. Se pintan como
    advertencia arriba, pero no entran aquí.
    """
    windows = result["windows"]
    ultima = windows.iloc[-1]
    alertas = alertas_de_ventana(windows)[-1]
    return {
        "ventana": ultima,
        "alertas": alertas,
        "traza": traza_decision(float(ultima["lower"]), umbrales, alertas),
    }


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
