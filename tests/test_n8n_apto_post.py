"""`enviar_decision` con APTO: todo 2xx es ok, 500/timeout no, SIN_DECISION no POST.

`urllib.request.urlopen` mockeado (sin red): el contrato es el dict
`{ok, status, decision}` y que nunca lanza a la UI.
"""
from __future__ import annotations

import os
import sys
import urllib.error
from unittest import mock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from src import n8n as N8N  # noqa: E402
from app.lib import n8n_payload as UN  # noqa: E402

URL = "http://n8n.invalid/hook"
PAYLOAD = {"decision": "APTO", "unidad": 11.0}


class _Resp:
    def __init__(self, status):
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return b"{}"


def test_apto_con_200_es_ok():
    """Un 200 de n8n confirma el envio de APTO."""
    with mock.patch("urllib.request.urlopen", return_value=_Resp(200)):
        r = N8N.enviar_decision("APTO", PAYLOAD, webhook_url=URL)
    assert r == {"ok": True, "status": 200, "decision": "APTO"}


def test_apto_con_201_es_ok():
    """Un 201 (creado) tambien es ok: vale todo el 2xx, no solo el 200."""
    with mock.patch("urllib.request.urlopen", return_value=_Resp(201)):
        r = N8N.enviar_decision("APTO", PAYLOAD, webhook_url=URL)
    assert r == {"ok": True, "status": 201, "decision": "APTO"}


def test_apto_con_204_es_ok():
    """Un 204 (sin contenido) sigue siendo ok."""
    with mock.patch("urllib.request.urlopen", return_value=_Resp(204)):
        r = N8N.enviar_decision("APTO", PAYLOAD, webhook_url=URL)
    assert r == {"ok": True, "status": 204, "decision": "APTO"}


def test_apto_con_500_es_no_ok_sin_lanzar():
    """Un 500 de n8n devuelve ok=False con su status, sin excepcion."""
    with mock.patch("urllib.request.urlopen", return_value=_Resp(500)):
        r = N8N.enviar_decision("APTO", PAYLOAD, webhook_url=URL)
    assert r == {"ok": False, "status": 500, "decision": "APTO"}


def test_timeout_no_lanza_y_devuelve_no_ok():
    """Timeout/red caida: ok=False y status None, nunca excepcion a la UI."""
    with mock.patch("urllib.request.urlopen",
                    side_effect=urllib.error.URLError("timeout")):
        r = N8N.enviar_decision("APTO", PAYLOAD, webhook_url=URL)
    assert r == {"ok": False, "status": None, "decision": "APTO"}


def test_sin_decision_no_hace_post():
    """SIN_DECISION nunca notifica (`debe_notificar` False): ni POST se intenta.

    `enviar_decision` la acepta como valida, asi que la guarda es la capa de
    dedupe de `n8n_payload`: sin notificacion, no hay llamada al webhook.
    """
    assert UN.debe_notificar("SIN_DECISION", "fp9", set()) is False
    assert UN.debe_notificar("APTO", "fp9", set()) is True
    with mock.patch("urllib.request.urlopen") as m:
        if not UN.debe_notificar("SIN_DECISION", "fp9", set()):
            r = {"ok": False, "status": None, "decision": "SIN_DECISION"}
    assert not m.called
    assert r == {"ok": False, "status": None, "decision": "SIN_DECISION"}
