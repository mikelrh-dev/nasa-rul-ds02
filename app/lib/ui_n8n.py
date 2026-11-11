"""Payload n8n y dedupe (MIA-3) — modulo puro, sin Streamlit.

`payload_desde_traza` reutiliza la traza de `decision_en_vivo`
(`app/ui_rules.py`): NO re-clasifica (prohibido `L.classify`) y NO incluye
`X_raw` (numpy, no JSON). `debe_notificar` decide el dedupe por fingerprint:
HANGAR, INSPECCION y APTO notifican por POST (apto llega a la rama Set log
de n8n); SIN_DECISION nunca notifica.
"""
from __future__ import annotations

from app.lib import ui_data_loader as L

UMBRALES_DEFECTO = {"apto": L.DEFAULT_AIRWORTHY, "hangar": L.DEFAULT_AOG}
DECISIONES_QUE_NOTIFICAN = ("HANGAR", "INSPECCION", "APTO")


def payload_desde_traza(en_vivo: dict, umbrales: dict | None = None,
                        artefacto_sha256: str = "",
                        fingerprint: str = "",
                        unidad=None) -> dict:
    """Construye el payload n8n EXACTO desde la traza de `decision_en_vivo`.

    `en_vivo` es el dict `{"ventana", "alertas", "traza"}` de
    `ui_rules.decision_en_vivo`. `decision`, `usadas` y `porque` se leen de
    la traza tal cual; `motivo` se compone como en `decidir_ventanas`.
    `idempotency_key` es el `fingerprint` del contrato. La ventana en vivo
    no trae columna `unit`: la unidad sale del parámetro `unidad` (el
    contrato) o, si falta, de la propia ventana.
    """
    ventana = en_vivo["ventana"]
    traza = en_vivo["traza"]
    porque = [str(p) for p in traza["porque"]]
    umb = umbrales or UMBRALES_DEFECTO
    if unidad is None:
        unidad = ventana["unit"] if "unit" in ventana.index else 0.0
    return {
        "decision": str(traza["decision"]),
        "unidad": float(unidad),
        "ciclo": float(ventana["cycle"]),
        "rul_punto": float(ventana["pred"]),
        "limite_inferior": float(ventana["lower"]),
        "limite_superior": float(ventana["upper"]),
        "umbrales": {"apto": float(umb["apto"]), "hangar": float(umb["hangar"])},
        "usadas": [str(u) for u in traza["usadas"]],
        "porque": porque,
        "motivo": " · ".join(porque),
        "alertas_datos": [str(a) for a in en_vivo["alertas"]],
        "artefacto_sha256": str(artefacto_sha256),
        "fingerprint": str(fingerprint),
        "idempotency_key": str(fingerprint),
    }


def debe_notificar(decision: str, fingerprint: str, enviadas: set) -> bool:
    """¿Hay que enviar esta decisión por webhook en esta sesión?

    HANGAR, INSPECCION y APTO notifican (APTO llega a la rama Set log de
    n8n); SIN_DECISION nunca. Un fingerprint ya en `enviadas` no re-envía.
    """
    if decision not in DECISIONES_QUE_NOTIFICAN:
        return False
    return str(fingerprint) not in {str(f) for f in enviadas}
