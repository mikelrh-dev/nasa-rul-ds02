"""Contrato del endpoint propio POST /n8n-decision (change 2026-11-10-n8n-accion-propia).

La accion novedosa de MIA-3: la rama HANGAR del flujo n8n llama a la API del
propio proyecto, que registra la decision en `app/registros_n8n.json` y es
idempotente por fingerprint.

Run:  python -m pytest tests/test_n8n_propia.py -q
"""
from __future__ import annotations

import json
import os
import sys

import pytest
from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

import app.services.api as api  # noqa: E402

_TOKEN = "test-n8n-token"
_PAYLOAD = {
    "decision": "HANGAR",
    "fingerprint": "fp-u14-c25-hangar",
    "artefacto_sha256": "d6c70142-demo",
    "unidad": 14,
}


class _FakeLgbStandalone:
    n_features_in_ = 7


class _FakeEnsemble:
    paradigm = "fake-test"
    window_size = 50
    beta = 0.05
    ema_span = 10
    n_op = 6
    lgb_standalone = _FakeLgbStandalone()

    def predict(self, X, cycles, uni):
        return None


@pytest.fixture()
def client(tmp_path, monkeypatch):
    """TestClient sin lifespan, con registro en tmp_path y token configurado."""
    monkeypatch.setitem(api.STATE, "ensemble", _FakeEnsemble())
    monkeypatch.setattr(api, "_rate_hits", {})
    monkeypatch.setattr(api, "_API_KEY", None)
    registro = tmp_path / "registros_n8n.json"
    monkeypatch.setattr(api, "_N8N_REGISTROS_PATH", str(registro))
    monkeypatch.setattr(api, "_n8n_registro_path", lambda: str(registro))
    monkeypatch.setattr(api, "_N8N_TOKEN", _TOKEN)
    return TestClient(api.app, raise_server_exceptions=False)


def _post(client, payload=None, token=_TOKEN):
    body = dict(_PAYLOAD if payload is None else payload)
    body["token"] = token
    return client.post("/n8n-decision", json=body)


# --------------------------------------------------------------- endpoint
def test_decision_valida_se_registra_una_vez(client):
    """Happy path: 200, recorded true y una sola fila en el registro."""
    resp = _post(client)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True, "recorded": True}
    with open(api._n8n_registro_path(), encoding="utf-8") as fh:
        datos = json.load(fh)
    assert isinstance(datos, list) and len(datos) == 1
    fila = datos[0]
    assert fila["decision"] == "HANGAR"
    assert fila["fingerprint"] == "fp-u14-c25-hangar"
    assert fila["artefacto_sha256"] == "d6c70142-demo"
    assert fila["unidad"] == 14
    assert fila["ts"]


def test_fingerprint_duplicado_no_duplica(client):
    """Idempotencia: el segundo POST con el mismo fingerprint no appendea."""
    assert _post(client).json() == {"ok": True, "recorded": True}
    resp = _post(client)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"ok": True, "recorded": False}
    with open(api._n8n_registro_path(), encoding="utf-8") as fh:
        datos = json.load(fh)
    assert len(datos) == 1


def test_token_invalido_o_ausente_es_401(client):
    """Sin token o con token distinto: 401 y el registro no se toca."""
    assert _post(client, token="otro-token").status_code == 401
    assert _post(client, token="").status_code == 401
    assert not os.path.exists(api._n8n_registro_path())


def test_decision_invalida_es_400(client):
    """`decision` fuera de {APTO, INSPECCION, HANGAR}: 400 con mensaje."""
    resp = _post(client, {**_PAYLOAD, "decision": "PARAR"})
    assert resp.status_code == 400, resp.text
    assert resp.json()["detail"]
    assert not os.path.exists(api._n8n_registro_path())


def test_sin_entorno_n8n_webhook_token_es_503(client, monkeypatch):
    """Sin `N8N_WEBHOOK_TOKEN` el endpoint degrada a 503, no rompe el arranque."""
    monkeypatch.setattr(api, "_N8N_TOKEN", None)
    resp = _post(client)
    assert resp.status_code == 503, resp.text
    assert "N8N_WEBHOOK_TOKEN" in resp.json()["detail"]
    assert not os.path.exists(api._n8n_registro_path())


def test_todas_las_decisiones_validas_se_aceptan(client):
    """APTO e INSPECCION tambien son decisiones validas del endpoint."""
    for decision in ("APTO", "INSPECCION"):
        resp = _post(client, {**_PAYLOAD, "decision": decision,
                              "fingerprint": f"fp-{decision}"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["recorded"] is True


def test_el_token_se_compara_con_compare_digest():
    """El token MUST compararse con hmac.compare_digest (patron de src/n8n.py)."""
    src = os.path.join(ROOT, "app", "services", "api.py")
    with open(src, encoding="utf-8") as fh:
        texto = fh.read()
    assert "compare_digest" in texto
    assert "N8N_WEBHOOK_TOKEN" in texto


# --------------------------------------------------------------- flujo n8n
def test_flujo_tiene_accion_novedosa_en_rama_hangar():
    """El flujo gana un httpRequest a la API propia al final de HANGAR."""
    with open(os.path.join(ROOT, "n8n", "flujo.json"), encoding="utf-8") as fh:
        flujo = json.load(fh)
    nodos = {n["name"]: n for n in flujo["nodes"]}
    assert "HANGAR API propia" in nodos
    nodo = nodos["HANGAR API propia"]
    assert nodo["type"] == "n8n-nodes-base.httpRequest"
    url = json.dumps(nodo["parameters"])
    assert "http://127.0.0.1:8000/n8n-decision" in url
    # El token va en la credencial de header (X-DS02-Token), no en headerParameters,
    # asi el JSON exportado no guarda el secreto. En httpRequest v4 el valor valido
    # es predefinedCredentialType + nodeCredentialType (genericHeaderAuth ya no existe).
    assert nodo["parameters"]["authentication"] == "predefinedCredentialType"
    assert nodo["parameters"]["nodeCredentialType"] == "httpHeaderAuth"
    assert nodo["credentials"]["httpHeaderAuth"]["name"] == "DS02 Webhook Header Auth"
    # Conexion: Gmail -> API propia, y Postgres/Calendar/Gmail intactos.
    assert flujo["connections"]["HANGAR Gmail"]["main"][0][0]["node"] == "HANGAR API propia"
    assert flujo["connections"]["HANGAR Google Calendar"]["main"][0][0]["node"] == "HANGAR Gmail"
    assert flujo["connections"]["HANGAR Postgres insert"]["main"][0][0]["node"] == "HANGAR Google Calendar"
    assert flujo["connections"]["Switch por decision"]["main"][2][0]["node"] == "HANGAR Postgres insert"


def test_flujo_sigue_inactivo_y_con_las_tres_ramas():
    """El JSON sigue siendo importable y con las 3 ramas de decision."""
    with open(os.path.join(ROOT, "n8n", "flujo.json"), encoding="utf-8") as fh:
        flujo = json.load(fh)
    assert flujo["active"] is False
    salida_switch = flujo["connections"]["Switch por decision"]["main"]
    assert [b[0]["node"] for b in salida_switch] == [
        "APTO Set log", "Set INSPECCION flat", "HANGAR Postgres insert"]
    tipos = [n["type"] for n in flujo["nodes"]]
    assert "n8n-nodes-base.googleSheets" in tipos
    assert "n8n-nodes-base.postgres" in tipos
    assert "n8n-nodes-base.googleCalendar" in tipos
    assert "n8n-nodes-base.gmail" in tipos
