"""Reglas del motor (MIA). Dos pasadas: corrección (B) y decisión (A).
Ocho reglas en total: 2 de corrección + 6 de decisión (MIA-2 exige 6 o más).

Cada regla es una tupla de cinco datos, siempre en este orden:

    (nombre, condicion, efecto, prioridad, porque)

* `condicion(caso) -> bool` — ¿se cumple?
* `efecto` — diccionario de campos a escribir en la ficha, o una función
  `caso -> dict` cuando el efecto se calcula (las reglas de corrección).
* `prioridad` — gana la de número más alto; se aplica una sola vez por pasada.
* `porque` — frase corta que explica la regla a quien pregunte.

Los números `R2b` y `R6` conservan la numeración del informe de medición
(`docs/informes/informe-2026-10-21-reglas-oof.md`); `R1` es la regla de seguridad y `R7/R8/R9` son los
umbrales conformales 25/20 documentados en ADR-013.

Los números de esta capa los reproduce scripts/auditoria/freeze_rules_evidence.py; si
divergen, el gate falla (ADR-009).
"""
from __future__ import annotations

import json
import os

import numpy as np

CALIBRACION_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "calibracion_banda.json")

# Un tramo con menos filas que esto no puede estrechar la banda global.
MIN_FILAS_TRAMO = 500

APTO = "APTO"
INSPECCION = "INSPECCION"
HANGAR = "HANGAR"
SIN_DECISION = "SIN_DECISION"

_calibracion = None


# ------------------------------------------------------------------ helpers
def cargar_calibracion() -> dict:
    """Banda recalibrada sobre el punto corregido (14 915 filas OOF puras)."""
    global _calibracion
    if _calibracion is None:
        with open(CALIBRACION_PATH, encoding="utf-8") as fh:
            _calibracion = json.load(fh)
    return _calibracion


def pava_causal_no_creciente(serie) -> np.ndarray:
    """Ajuste isotonico no creciente de cada prefijo (PAVA en linea).

    Devuelve, para cada posicion `t`, el valor del extremo del ajuste monotono
    del prefijo `1..t`. Dos propiedades y una limitacion, dichas sin rodeos:

    * **Es causal**: el valor en `t` depende solo de las posiciones `<= t`.
    * **El ajuste de cada prefijo es no creciente**: la tendencia estimada no
      sube con el ciclo, que es la restriccion fisica del desgaste.
    * **La secuencia devuelta NO es estrictamente no creciente**: el extremo del
      ajuste puede subir unos decimos cuando llega un punto alto. La envolvente
      estrictamente monótona de esta secuencia es, por identidad,
      `np.minimum.accumulate(serie)` — es decir, exactamente la regla R2
      (running-min) que se midio y se descarto. Asi que si lo que se quiere es
      monotonia estricta, la regla es R2 y no esta.
    """
    valores: list[float] = []
    pesos: list[float] = []
    out = np.empty(len(serie), dtype=np.float64)
    for i, v in enumerate(np.asarray(serie, dtype=np.float64)):
        valores.append(float(v))
        pesos.append(1.0)
        while len(valores) >= 2 and valores[-2] < valores[-1]:
            v2, w2 = valores.pop(), pesos.pop()
            v1, w1 = valores.pop(), pesos.pop()
            valores.append((v1 * w1 + v2 * w2) / (w1 + w2))
            pesos.append(w1 + w2)
        out[i] = valores[-1]
    return out



def banda_recalibrada_vector(puntos, calibracion: dict) -> tuple[np.ndarray, np.ndarray]:
    """Vectoriza `banda_recalibrada` para un array de puntos.

    Los bordes no cruzan el punto y el inferior no baja de cero, igual que la
    banda enviada: un intervalo que excluyera a su propio centro seria un bug.

    **Guarda de muestra pequena.** Un tramo con menos de `MIN_FILAS_TRAMO` filas
    no puede estrechar la banda: toma el cuantil mas conservador de los dos, el
    del tramo y el global. El tramo `[75, inf)` tiene 419 filas y `q_high`
    negativo; sin la guarda el limite superior se hundia ~19.8 ciclos al cruzar
    75 y el intervalo quedaba de una sola cara. La regla solo ensancha, asi que
    la cobertura no puede bajar.
    """
    puntos = np.asarray(puntos, dtype=np.float64).ravel()
    edges = np.asarray(calibracion["edges"], dtype=np.float64)
    idx = np.clip(np.searchsorted(edges, puntos, side="right") - 1, 0, len(edges) - 2)
    bins = calibracion["bins"]
    q_low = np.asarray([b["q_low"] for b in bins], dtype=np.float64)[idx]
    q_high = np.asarray([b["q_high"] for b in bins], dtype=np.float64)[idx]
    filas = np.asarray([b.get("n", 0) for b in bins], dtype=np.float64)[idx]
    globales = calibracion.get("global_quantiles")
    if globales:
        escaso = filas < MIN_FILAS_TRAMO
        q_low = np.where(escaso, np.minimum(q_low, float(globales[0])), q_low)
        q_high = np.where(escaso, np.maximum(q_high, float(globales[1])), q_high)
    lower = np.minimum(puntos + q_low, puntos)
    upper = np.maximum(puntos + q_high, puntos)
    lower = np.where(puntos >= 0.0, np.clip(lower, 0.0, None), lower)
    return lower, upper


def banda_recalibrada(punto: float, calibracion: dict) -> tuple[float, float]:
    """Banda sobre un unico punto, con los cuantiles de la recalibracion."""
    lower, upper = banda_recalibrada_vector([punto], calibracion)
    return float(lower[0]), float(upper[0])


def _datos_validos(caso: dict) -> bool:
    return not caso.get("alertas_datos")


def _umbrales_validos(caso: dict) -> bool:
    """Hay límite inferior y umbrales, y vienen ordenados (`hangar < apto`).

    Sin límite o sin umbrales no se puede clasificar: las condiciones de
    decisión devuelven `False` y el motor cierra en `SIN_DECISION`. Con
    `hangar >= apto` pasa lo mismo, documentado: `ui_data_loader.classify`
    lanza `ValueError` en la UI, pero una regla no debe romper la pasada del
    motor, así que aquí la guarda es no decidir, nunca una decisión silenciosa
    ni dos reglas contradictorias a la vez.
    """
    if caso.get("limite_inferior") is None:
        return False
    u = caso.get("umbrales")
    if not isinstance(u, dict) or u.get("apto") is None or u.get("hangar") is None:
        return False
    try:
        return bool(u["hangar"] < u["apto"])
    except TypeError:
        return False


# ------------------------------------------------- pasada B: correccion
def si_R2b_ISOTONICO(caso: dict) -> bool:
    """Hay historial de la misma unidad y un punto que corregir."""
    return bool(caso.get("historial")) and "rul_punto" in caso


def efecto_R2b_ISOTONICO(caso: dict) -> dict:
    """Sustituye el punto por el extremo del ajuste isotonico del prefijo."""
    serie = [float(r) for _, r in caso["historial"]] + [float(caso["rul_punto"])]
    corregido = float(pava_causal_no_creciente(serie)[-1])
    return {"rul_punto": corregido, "corregido_por_isotonico": True}


def si_R6_BANDA(caso: dict) -> bool:
    """Hay punto (corregido o no) al que trasladar la banda."""
    return "rul_punto" in caso


def efecto_R6_BANDA(caso: dict) -> dict:
    """Recalibra la banda sobre el punto corregido."""
    lower, upper = banda_recalibrada(float(caso["rul_punto"]), cargar_calibracion())
    return {
        "limite_inferior": lower,
        "limite_superior": upper,
        "banda_recalibrada": True,
    }


# -------------------------------------------------- pasada A: decision
def si_R1_SEGURIDAD(caso: dict) -> bool:
    """Un dato imposible invalida la decision, tenga el riesgo que tenga."""
    return bool(caso.get("alertas_datos"))


def efecto_R1_SEGURIDAD(caso: dict) -> dict:
    """Anula la decisión y deja el motivo legible en la ficha."""
    motivo = "; ".join(str(a) for a in caso["alertas_datos"])
    return {
        "decision": SIN_DECISION,
        "motivo": f"dato imposible, no se decide: {motivo}",
    }


def si_R7_APTO(caso: dict) -> bool:
    """Datos y umbrales válidos y `L_inf` por encima del umbral de apto."""
    return _datos_validos(caso) and _umbrales_validos(caso) and caso["limite_inferior"] >= caso["umbrales"]["apto"]


def si_R8_INSPECCION(caso: dict) -> bool:
    """`L_inf` entre los dos umbrales: inspección programada."""
    if not _datos_validos(caso) or not _umbrales_validos(caso):
        return False
    u = caso["umbrales"]
    return u["hangar"] <= caso["limite_inferior"] < u["apto"]


def si_R9_HANGAR(caso: dict) -> bool:
    """`L_inf` por debajo del umbral de hangar: la unidad no vuela."""
    return _datos_validos(caso) and _umbrales_validos(caso) and caso["limite_inferior"] < caso["umbrales"]["hangar"]


def si_R10_DATOS_INSUFICIENTES(caso: dict) -> bool:
    """Faltan el límite inferior o los umbrales: no hay nada que clasificar.

    No es lo mismo que un dato imposible (R1): aquí los datos son sanos, pero
    la ficha llega incompleta. Antes de esta regla el motor caía en
    `SIN_DECISION` por defecto, sin decirlo en la traza.
    """
    if not _datos_validos(caso):
        return False
    u = caso.get("umbrales")
    return (caso.get("limite_inferior") is None
            or not isinstance(u, dict)
            or u.get("apto") is None or u.get("hangar") is None)


def si_R11_UMBRALES_INCOHERENTES(caso: dict) -> bool:
    """Los umbrales vienen desordenados (`hangar >= apto`): error de configuración.

    Con la escalera invertida cualquier clasificación sería arbitraria, así que
    no se decide. `ui_data_loader.classify` lanza `ValueError` en la UI; una
    regla no debe romper la pasada del motor.
    """
    if not _datos_validos(caso):
        return False
    u = caso.get("umbrales")
    if not isinstance(u, dict) or u.get("apto") is None or u.get("hangar") is None:
        return False
    try:
        return bool(u["hangar"] >= u["apto"])
    except TypeError:
        return False


# ------------------------------------------------------------- las listas
REGLAS_CORRECCION = [
    ("R2b_ISOTONICO_CAUSAL", si_R2b_ISOTONICO, efecto_R2b_ISOTONICO, 2,
     "la tendencia del desgaste no sube con el ciclo: se toma el extremo del "
     "ajuste isotonico causal del historial"),
    ("R6_BANDA", si_R6_BANDA, efecto_R6_BANDA, 1,
     "la banda se recalibra sobre el punto ya corregido, no sobre el crudo"),
]

REGLAS_DECISION = [
    ("R1_SEGURIDAD", si_R1_SEGURIDAD, efecto_R1_SEGURIDAD, 10,
     "con un dato imposible no se decide nada, tenga el riesgo que tenga"),
    ("R10_DATOS_INSUFICIENTES", si_R10_DATOS_INSUFICIENTES,
     {"decision": SIN_DECISION,
      "motivo": "faltan limite inferior o umbrales: no se clasifica"}, 9,
     "sin ficha completa no hay decision posible, y se dice en vez de callarlo"),
    ("R11_UMBRALES_INCOHERENTES", si_R11_UMBRALES_INCOHERENTES,
     {"decision": SIN_DECISION,
      "motivo": "umbrales incoherentes (hangar >= apto): no se clasifica"}, 8,
     "con la escalera de umbrales invertida cualquier decision seria arbitraria"),
    ("R9_HANGAR", si_R9_HANGAR, {"decision": HANGAR}, 3,
     "L_inf por debajo del umbral de hangar: la unidad no vuela"),
    ("R8_INSPECCION", si_R8_INSPECCION, {"decision": INSPECCION}, 2,
     "L_inf entre los dos umbrales: inspeccion programada"),
    ("R7_APTO", si_R7_APTO, {"decision": APTO}, 1,
     "L_inf por encima del umbral de apto: sigue en servicio"),
]

reglas = REGLAS_CORRECCION + REGLAS_DECISION
