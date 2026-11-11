"""Pure helpers for the app-ux-bundle-fix (no Streamlit).

Kept separate from the dashboard so the CSV builders, the queue filter and
the 6-rule view can be unit-tested without launching the app. The thresholds
come from `app/lib/_constantes.py`, so this module stays Streamlit-free.
"""
from __future__ import annotations

import pandas as pd

from app.lib import _constantes
from app.lib import hangar as HGR


def contraste_csv(raw: pd.DataFrame, corrected: pd.DataFrame) -> str:
    """CSV de contraste crudo vs corregido (merge por unit+cycle)."""
    left = raw[["unit", "cycle", "lower"]].rename(
        columns={"lower": "lower_raw"})
    cols = ["unit", "cycle", "lower", "decision"]
    right = corrected[[c for c in cols if c in corrected.columns]].rename(
        columns={"lower": "lower_corregida"})
    frame = left.merge(right, on=["unit", "cycle"], how="left")
    if "decision" not in frame.columns:
        frame["decision"] = ""
    return frame[["unit", "cycle", "lower_raw", "lower_corregida",
                  "decision"]].to_csv(index=False)


def cola_filtrada(registros: dict, estados: set) -> list[dict]:
    """Cola de hangar restringida a `estados` (vacío = ninguna fila)."""
    if not estados:
        return []
    return [r for r in HGR.cola(registros) if r["estado"] in set(estados)]


def trayectoria_csv(curva: pd.DataFrame) -> str:
    """CSV de trayectoria del motor (cycle, pred, lower, upper, decision)."""
    cols = ["cycle", "pred", "lower", "upper", "decision"]
    frame = curva[[c for c in cols if c in curva.columns]].copy()
    for c in cols:
        if c not in frame.columns:
            frame[c] = ""
    return frame[cols].to_csv(index=False)


def reglas_decision_vista() -> list[dict]:
    """Vista de solo lectura de las 6 reglas de decisión (`src/mia/reglas.py`)."""
    from src.mia.reglas import REGLAS_DECISION

    return [{"regla": nombre, "prioridad": prioridad, "porque": porque}
            for nombre, _cond, _ef, prioridad, porque in REGLAS_DECISION]


def probar_n8n() -> dict:
    """Sonda de conexión del panel n8n: POST APTO sintético, nunca lanza.

    Vive aquí (no en el dashboard) para que el dashboard mantenga un único
    `enviar_decision(` en su punto de llamada tras `decision_en_vivo`.
    """
    import pandas as pd

    from src import n8n as N8N

    from app.lib import n8n_payload as UN

    prueba = UN.payload_desde_traza(
        {"ventana": pd.Series({"unit": 14.0, "cycle": 25.0,
                                "pred": 33.1, "lower": 23.9,
                                "upper": 44.2}),
         "alertas": [],
         "traza": {"decision": "APTO", "usadas": ["R7_APTO"],
                   "porque": ["test de conexión del panel n8n"]}},
        {"apto": _constantes.DEFAULT_AIRWORTHY, "hangar": _constantes.DEFAULT_AOG},
        "", "test-panel", unidad=14)
    return N8N.enviar_decision("APTO", prueba)
