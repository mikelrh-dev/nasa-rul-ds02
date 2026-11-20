"""Formateadores que convierten columnas numéricas en texto de presentación.

El Streamlit 1.66.0 instalado ignora ``NumberColumn(format=...)`` (verificado con
una prueba mínima en un servidor de scratch), así que cada rejilla de solo
lectura formatea sus valores aquí y declara la columna como texto. Las rejillas
editables conservan su dtype numérico y no pasan por este módulo.
"""
from __future__ import annotations

import pandas as pd


def _es_nulo(valor) -> bool:
    if valor is None:
        return True
    try:
        return bool(pd.isna(valor))
    except (TypeError, ValueError):
        return False


def _aplica(serie: pd.Series, fn) -> pd.Series:
    return serie.map(lambda v: "" if _es_nulo(v) else fn(float(v)))


def entero(serie: pd.Series) -> pd.Series:
    """Conteos sin decimales: «2521»."""
    return _aplica(serie, lambda v: f"{int(round(v))}")


def un_decimal(serie: pd.Series) -> pd.Series:
    return _aplica(serie, lambda v: f"{v:.1f}")


def dos_decimales(serie: pd.Series) -> pd.Series:
    return _aplica(serie, lambda v: f"{v:.2f}")


def tres_decimales(serie: pd.Series) -> pd.Series:
    return _aplica(serie, lambda v: f"{v:.3f}")


def cuatro_decimales(serie: pd.Series) -> pd.Series:
    return _aplica(serie, lambda v: f"{v:.4f}")


def con_signo_3(serie: pd.Series) -> pd.Series:
    """Bias y tasas con signo explícito: «+0.722»."""
    return _aplica(serie, lambda v: f"{v:+.3f}")


def con_signo_4(serie: pd.Series) -> pd.Series:
    return _aplica(serie, lambda v: f"{v:+.4f}")


def cuatro_sig(serie: pd.Series) -> pd.Series:
    """Límites de envolvente observada: cuatro dígitos significativos."""
    return _aplica(serie, lambda v: f"{v:.4g}")


def formatea(frame: pd.DataFrame, spec: dict[str, callable]) -> pd.DataFrame:
    """Copia del frame con las columnas mapeadas convertidas en texto de presentación."""
    salida = frame.copy()
    for columna, fn in spec.items():
        salida[columna] = fn(salida[columna])
    return salida
