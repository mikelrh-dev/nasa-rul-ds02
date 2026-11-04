"""Reglas de negocio (MIA) — re-export para el reto de clase.

La lógica vive en `mia/reglas.py` + `mia/motor.py` (pipeline congelado,
no duplicar). Este módulo existe porque la rúbrica pide `src/reglas.py`
con 6+ reglas, prioridad, decisión y seguridad.
"""

from src.mia.motor import motor, resumen  # noqa: F401
from src.mia.reglas import (  # noqa: F401
    APTO,
    CALIBRACION_PATH,
    HANGAR,
    INSPECCION,
    REGLAS_CORRECCION,
    REGLAS_DECISION,
    SIN_DECISION,
    banda_recalibrada,
    banda_recalibrada_vector,
    cargar_calibracion,
    reglas,
)

__all__ = [
    "motor",
    "resumen",
    "reglas",
    "REGLAS_CORRECCION",
    "REGLAS_DECISION",
    "APTO",
    "INSPECCION",
    "HANGAR",
    "SIN_DECISION",
    "cargar_calibracion",
    "banda_recalibrada",
    "banda_recalibrada_vector",
    "CALIBRACION_PATH",
]
