"""Contrato de seguridad de la API DS02.

Comportamiento fijado:
- ``/health`` es público: 200 sin credenciales, incluso si ``DS02_API_KEY``
  está configurada.
- Los endpoints protegidos rechazan una clave API errónea o ausente con 401.
- Las claves API se comparan con :func:`hmac.compare_digest`.
- El limitador de ventana fija también se aplica a las escrituras autenticadas
  (``POST /predict``): la undécima escritura autenticada en un minuto devuelve 429.
"""

from __future__ import annotations

import os

import numpy as np
import pytest
from fastapi.testclient import TestClient

import app.services.api as api

_SECRET = "test-secret-key"


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
        return np.array([123.0])


@pytest.fixture()
def client(monkeypatch):
    """TestClient without lifespan; fake ensemble + empty rate limiter."""
    fake = _FakeEnsemble()
    monkeypatch.setitem(api.STATE, "ensemble", fake)
    monkeypatch.setattr(api, "_rate_hits", {})
    # El lifespan no se ejecuta con un TestClient sin contexto, así que _raw() no toca el disco.
    monkeypatch.setattr(
        api,
        "_raw",
        lambda: {
            "W_test": np.zeros((1, 50, 19)),
            "Xs_test": np.zeros((1, 50, 19)),
            "A_test": np.array([[11.0, 100.0]]),
        },
    )
    monkeypatch.setattr(
        api,
        "windows_for_unit",
        lambda *a, **k: (
            np.zeros((1, 50, 19)),
            np.array([100.0]),
            np.array([11.0]),
            None,
        ),
    )
    return TestClient(api.app, raise_server_exceptions=False)


def test_health_is_public_without_auth(client, monkeypatch):
    """`/health` devuelve 200 sin credenciales aunque haya una clave configurada."""
    monkeypatch.setattr(api, "_API_KEY", _SECRET)
    resp = client.get("/health")
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "ok"


def test_wrong_api_key_is_rejected_with_401(client, monkeypatch):
    """Una clave API errónea en un endpoint de escritura devuelve 401 (nunca 200/429)."""
    monkeypatch.setattr(api, "_API_KEY", _SECRET)
    resp = client.post(
        "/predict",
        json={"unit": 11, "window": 0},
        headers={"X-API-Key": "wrong-key"},
    )
    assert resp.status_code == 401, resp.text


def test_rate_limit_applies_even_with_valid_api_key(client, monkeypatch):
    """Las escrituras autenticadas también tienen límite: la undécima devuelve 429."""
    monkeypatch.setattr(api, "_API_KEY", _SECRET)
    payload = {"unit": 11, "window": 0}
    headers = {"X-API-Key": _SECRET}
    first = client.post("/predict", json=payload, headers=headers)
    assert first.status_code == 200, first.text
    statuses = [
        client.post("/predict", json=payload, headers=headers).status_code
        for _ in range(api._RATE_LIMIT_PER_MIN)
    ]
    assert 429 in statuses, statuses
    assert statuses[-1] == 429


def test_api_key_comparison_uses_compare_digest():
    """`_protect` debe comparar las claves con hmac.compare_digest, no con `!=`."""
    src_path = api.__file__
    with open(src_path, encoding="utf-8") as fh:
        src = fh.read()
    assert "compare_digest" in src, "hmac.compare_digest not used for API key check"
    assert "import hmac" in src, "hmac module not imported in app/services/api.py"
