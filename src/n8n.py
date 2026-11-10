"""Envio de la decision a n8n (MIA-3).

`enviar_decision` hace POST con `urllib` stdlib (requests no esta en
requirements.txt), timeout 5 s y hasta `REINTENTOS` intentos con backoff
exponencial. Solo reintenta lo que puede mejorar: fallo de red, timeout y 5xx.
Un 4xx no se reintenta (el payload no va a cambiar). Los errores se loguean y se
devuelven como ok=False: nunca se lanza excepcion a la UI.

La URL sale del parametro o del env `N8N_WEBHOOK_URL`. Si el webhook de n8n usa
Header Auth, el secreto se toma de `N8N_WEBHOOK_TOKEN` y viaja en
`X-DS02-Token`; el repo no guarda credenciales.
"""
from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request

log = logging.getLogger(__name__)

DECISIONES_VALIDAS = ("APTO", "INSPECCION", "HANGAR", "SIN_DECISION")
TIMEOUT_S = 5
REINTENTOS = 3
ESPERA_BASE_S = 0.2
HEADER_TOKEN = "X-DS02-Token"


def _post(url: str, datos: bytes, token: str | None) -> int:
    """POST unico; devuelve el status HTTP y deja que urllib eleve el resto."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers[HEADER_TOKEN] = token
    req = urllib.request.Request(url, data=datos, method="POST", headers=headers)
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return int(getattr(resp, "status", 200) or 200)


def enviar_decision(decision: str, payload: dict,
                    webhook_url: str | None = None,
                    reintentos: int = REINTENTOS) -> dict:
    """Envia la decision al webhook de n8n; nunca lanza a la UI.

    Devuelve `{ok, status, decision}`. Reintenta fallo de red y 5xx; un 4xx se
    devuelve de inmediato con su status porque reenviarlo no cambia el contrato.
    """
    if decision not in DECISIONES_VALIDAS:
        log.warning("n8n: decision invalida %r, no se envia", decision)
        return {"ok": False, "status": None, "decision": decision}
    url = webhook_url or os.environ.get("N8N_WEBHOOK_URL")
    if not url:
        log.warning("n8n: sin webhook_url ni N8N_WEBHOOK_URL, no se envia %s",
                    decision)
        return {"ok": False, "status": None, "decision": decision}

    datos = json.dumps(payload).encode("utf-8")
    token = os.environ.get("N8N_WEBHOOK_TOKEN")
    intentos = max(1, int(reintentos))
    ultimo = None
    ultimo_status = None

    for intento in range(intentos):
        try:
            status = _post(url, datos, token)
            ok = 200 <= status < 300
            if ok or status < 500:
                return {"ok": ok, "status": status, "decision": decision}
            ultimo = f"HTTP {status}"
            ultimo_status = status
        except urllib.error.HTTPError as exc:
            status = int(getattr(exc, "code", 0) or 0)
            if 400 <= status < 500:
                log.warning("n8n: 4xx (%s) enviando decision %s, sin reintento",
                            status, decision)
                return {"ok": False, "status": status, "decision": decision}
            ultimo = f"HTTP {status}"
            ultimo_status = status
        except (urllib.error.URLError, OSError, ValueError) as exc:
            ultimo = str(exc)

        if intento + 1 < intentos:
            time.sleep(ESPERA_BASE_S * (2 ** intento))

    log.warning("n8n: %s intentos agotados enviando decision %s: %s",
                intentos, decision, ultimo)
    # Se conserva el ultimo status HTTP visto (5xx) para que la UI pueda
    # distinguir un rechazo del servidor de una caida de red (status None).
    return {"ok": False, "status": ultimo_status, "decision": decision}
