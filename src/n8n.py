"""Envio de la decision a n8n (MIA-3).

`enviar_decision` hace POST con `urllib` stdlib (requests no esta en
requirements.txt), timeout 5 s, y devuelve {ok,status,decision}. Los
errores se loguean y se devuelven como ok=False: nunca se lanza
excepcion a la UI. La URL sale del parametro o del env N8N_WEBHOOK_URL.
"""
from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

DECISIONES_VALIDAS = ("APTO", "INSPECCION", "HANGAR", "SIN_DECISION")
TIMEOUT_S = 5


def enviar_decision(decision: str, payload: dict,
                    webhook_url: str | None = None) -> dict:
    """Envia la decision al webhook de n8n; nunca lanza a la UI."""
    if decision not in DECISIONES_VALIDAS:
        log.warning("n8n: decision invalida %r, no se envia", decision)
        return {"ok": False, "status": None, "decision": decision}
    url = webhook_url or os.environ.get("N8N_WEBHOOK_URL")
    if not url:
        log.warning("n8n: sin webhook_url ni N8N_WEBHOOK_URL, no se envia %s",
                    decision)
        return {"ok": False, "status": None, "decision": decision}
    datos = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=datos, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            status = int(getattr(resp, "status", 200) or 200)
    except (urllib.error.URLError, OSError, ValueError) as exc:
        log.warning("n8n: error enviando decision %s: %s", decision, exc)
        return {"ok": False, "status": None, "decision": decision}
    return {"ok": 200 <= status < 300, "status": status, "decision": decision}
