"""Tests del flujo n8n minimo MIA-3 (change 2026-11-06-ds02-n8n-decision).

RED: payload exacto desde la traza, enviar_decision con urllib mockeado
(sin red), dedupe por fingerprint y flujo JSON valido.

Run:  python -m pytest tests/test_n8n_decision.py -q
"""
from __future__ import annotations

import io
import json
import os
import sys
import urllib.error
from unittest import mock

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "app"))

import ui_n8n as UN  # noqa: E402
from src import n8n as N8N  # noqa: E402

CLAVES_PAYLOAD = {
    "decision", "unidad", "ciclo", "rul_punto", "limite_inferior",
    "limite_superior", "umbrales", "usadas", "porque", "motivo",
    "alertas_datos", "artefacto_sha256", "fingerprint", "idempotency_key",
}


def _en_vivo(decision="HANGAR", unit=14, cycle=25, pred=33.1, lower=23.9,
             upper=44.2, usadas=("R9_HANGAR",), porque=("R9_HANGAR: L_inf...",),
             alertas=()):
    ventana = pd.Series({"unit": float(unit), "cycle": float(cycle),
                         "pred": float(pred), "lower": float(lower),
                         "upper": float(upper)})
    return {"ventana": ventana, "alertas": list(alertas),
            "traza": {"decision": decision, "usadas": list(usadas),
                      "porque": list(porque)}}


# --------------------------------------------------------------- payload
def test_payload_exacto_desde_traza_hangar():
    payload = UN.payload_desde_traza(
        _en_vivo(), {"apto": 30.0, "hangar": 25.0}, "abc", "fp1")
    assert set(payload) == CLAVES_PAYLOAD
    assert "X_raw" not in payload
    assert payload["decision"] == "HANGAR"
    assert payload["unidad"] == 14
    assert payload["ciclo"] == 25
    assert payload["rul_punto"] == 33.1
    assert payload["limite_inferior"] == 23.9
    assert payload["limite_superior"] == 44.2
    assert payload["umbrales"] == {"apto": 30.0, "hangar": 25.0}
    assert payload["usadas"] == ["R9_HANGAR"]
    assert "R9_HANGAR" in payload["motivo"]
    assert payload["alertas_datos"] == []
    assert payload["artefacto_sha256"] == "abc"
    assert payload["fingerprint"] == "fp1"
    assert payload["idempotency_key"] == "fp1"
    json.dumps(payload)  # no lanza: todo JSON-serializable


def test_payload_no_reclasifica():
    # Limite que con otros umbrales seria APTO, pero la traza dice INSPECCION.
    payload = UN.payload_desde_traza(
        _en_vivo(decision="INSPECCION", lower=31.0, usadas=("R8_INSPECCION",)),
        {"apto": 30.0, "hangar": 25.0}, "abc", "fp2")
    assert payload["decision"] == "INSPECCION"


def test_payload_umbrales_por_defecto():
    payload = UN.payload_desde_traza(_en_vivo(), None, "abc", "fp3")
    assert payload["umbrales"] == {"apto": 30.0, "hangar": 25.0}


def test_payload_ventana_en_vivo_sin_columna_unit():
    # Las ventanas de score_table no traen `unit`: la unidad viene del contrato.
    en_vivo = _en_vivo()
    en_vivo["ventana"] = en_vivo["ventana"].drop("unit")
    payload = UN.payload_desde_traza(en_vivo, None, "abc", "fp4", unidad=-1.0)
    assert payload["unidad"] == -1.0
    assert payload["ciclo"] == 25


# --------------------------------------------------------------- enviar
class _Resp:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def read(self):
        return b"{}"


def _payload():
    return UN.payload_desde_traza(_en_vivo(), None, "abc", "fp1")


def test_enviar_post_mockeado_sin_red():
    with mock.patch("urllib.request.urlopen", return_value=_Resp()) as m:
        r = N8N.enviar_decision("HANGAR", _payload(),
                                webhook_url="http://n8n.invalid/hook")
    assert m.called
    req = m.call_args[0][0]
    assert req.get_header("Content-type") == "application/json"
    assert json.loads(req.data)["decision"] == "HANGAR"
    assert m.call_args.kwargs.get("timeout") == 5
    assert r == {"ok": True, "status": 200, "decision": "HANGAR"}


def test_enviar_sin_url_no_hace_post():
    with mock.patch.dict(os.environ, {}, clear=True):
        with mock.patch("urllib.request.urlopen") as m:
            r = N8N.enviar_decision("HANGAR", _payload())
    assert not m.called
    assert r["ok"] is False


def test_enviar_error_red_no_lanza():
    with mock.patch("urllib.request.urlopen",
                    side_effect=urllib.error.URLError("sin red")):
        r = N8N.enviar_decision("INSPECCION", _payload(),
                                webhook_url="http://n8n.invalid/hook")
    assert r == {"ok": False, "status": None, "decision": "INSPECCION"}


def test_enviar_decision_invalida_no_hace_post():
    with mock.patch("urllib.request.urlopen") as m:
        r = N8N.enviar_decision("PARAR", _payload(),
                                webhook_url="http://n8n.invalid/hook")
    assert not m.called
    assert r["ok"] is False


# --------------------------------------------------------------- dedupe
def test_dedupe_mismo_fingerprint_no_reenvia():
    assert UN.debe_notificar("HANGAR", "fp1", set()) is True
    assert UN.debe_notificar("HANGAR", "fp1", {"fp1"}) is False
    assert UN.debe_notificar("INSPECCION", "fp2", {"fp1"}) is True


def test_sin_decision_nunca_notifica():
    assert UN.debe_notificar("SIN_DECISION", "fp9", set()) is False


def test_apto_solo_log_local_sin_post():
    # APTO no notifica por POST (solo log local en la app).
    assert UN.debe_notificar("APTO", "fpA", set()) is False


def test_dashboard_llama_una_vez_tras_decision_en_vivo():
    src = open(os.path.join(ROOT, "app", "dashboard_ds02.py"),
               encoding="utf-8").read()
    assert "payload_desde_traza" in src
    assert "enviar_decision" in src
    assert src.count("enviar_decision(") == 1


# --------------------------------------------------------------- flujo
def test_flujo_json_valido_con_3_ramas():
    path = os.path.join(ROOT, "n8n", "flujo.json")
    with open(path, encoding="utf-8") as fh:
        flujo = json.load(fh)
    nodos = flujo["nodes"]
    tipos = [n["type"].lower() for n in nodos]
    assert any("webhook" in t for t in tipos)
    assert any("switch" in t for t in tipos)
    texto = io.StringIO()
    json.dump(flujo, texto)
    cuerpo = texto.getvalue()
    for rama in ("APTO", "INSPECCION", "HANGAR"):
        assert rama in cuerpo
    assert "ds02/decision" in cuerpo
    # Sin valores de credenciales: solo referencias por nombre.
    assert "credentials" not in cuerpo or "password" not in cuerpo.lower()
