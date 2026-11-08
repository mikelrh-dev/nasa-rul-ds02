"""Limites de la API sin artefacto real: IP, expiracion, /units, /predict, lifespan.

Ensemble y datos falsos en memoria (como `test_security_api.py`): sin HDF5,
sin modelo, sin red. Solo contratos de borde.
"""
from __future__ import annotations

import asyncio
import os
import sys
import time
from types import SimpleNamespace

import numpy as np
import pytest
from fastapi.testclient import TestClient

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

import app.api as api  # noqa: E402

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
    """TestClient sin lifespan, ensemble falso y rate limiter vacio."""
    monkeypatch.setitem(api.STATE, "ensemble", _FakeEnsemble())
    monkeypatch.setattr(api, "_rate_hits", {})
    monkeypatch.setattr(api, "_API_KEY", None)
    monkeypatch.setattr(
        api, "_raw",
        lambda: {
            "W_test": np.zeros((1, 50, 19)),
            "Xs_test": np.zeros((1, 50, 19)),
            "A_test": np.array([[11.0, 100.0], [14.0, 200.0]]),
        },
    )
    monkeypatch.setattr(
        api, "windows_for_unit",
        lambda *a, **k: (
            np.zeros((1, 50, 19)),
            np.array([100.0]),
            np.array([11.0]),
            None,
        ),
    )
    return TestClient(api.app, raise_server_exceptions=False)


def _req(ip):
    return SimpleNamespace(client=SimpleNamespace(host=ip) if ip else None)


def test_client_ip_devuelve_host_o_unknown():
    """`_client_ip` lee `request.client.host`; sin cliente, `unknown`."""
    assert api._client_ip(_req("1.2.3.4")) == "1.2.3.4"
    assert api._client_ip(_req(None)) == "unknown"


def test_rate_limit_expira_despues_de_la_ventana(client, monkeypatch):
    """Hits de hace 61 s ya no cuentan: la IP vuelve a pasar."""
    monkeypatch.setattr(
        api, "_rate_hits", {"9.9.9.9": [time.monotonic() - 61.0] * 10})
    api._check_rate_limit(_req("9.9.9.9"))  # no lanza
    assert len(api._rate_hits["9.9.9.9"]) == 1  # solo el hit nuevo


def test_rate_limit_separa_cubos_por_ip(client, monkeypatch):
    """Una IP saturada (429) no bloquea a otra IP distinta."""
    monkeypatch.setattr(
        api, "_rate_hits", {"1.1.1.1": [time.monotonic()] * 10})
    with pytest.raises(Exception) as exc:
        api._check_rate_limit(_req("1.1.1.1"))
    assert exc.value.status_code == 429
    api._check_rate_limit(_req("2.2.2.2"))  # otra IP: pasa
    assert "2.2.2.2" in api._rate_hits


def test_units_sin_key_200_y_con_key_mala_401_y_buena_200(client, monkeypatch):
    """/units: sin key configurada pasa; con key mala 401, con buena 200."""
    resp = client.get("/units")
    assert resp.status_code == 200, resp.text
    assert resp.json()["test_units"] == [11.0, 14.0]
    monkeypatch.setattr(api, "_API_KEY", _SECRET)
    assert client.get("/units").status_code == 401
    assert client.get("/units", headers={"X-API-Key": "mala"}).status_code == 401
    assert client.get("/units", headers={"X-API-Key": _SECRET}).status_code == 200


def test_predict_ventana_fuera_de_rango_es_422(client):
    """/predict con janela inexistente (1 sola ventana, pidio la 5) es 422."""
    resp = client.post("/predict", json={"unit": 11, "window": 5})
    assert resp.status_code == 422, resp.text
    assert "out of range" in resp.text


def test_lifespan_carga_en_startup_y_limpia_en_shutdown(monkeypatch):
    """El lifespan guarda el ensemble verificado al entrar y limpia al salir."""
    fake = _FakeEnsemble()
    monkeypatch.setattr(api, "load_ensemble", lambda p: fake)
    api.STATE.clear()

    async def _ciclo():
        async with api.lifespan(api.app):
            assert api.STATE["ensemble"] is fake
            assert api.STATE["raw"] is None
            dentro = True
        return dentro

    assert asyncio.run(_ciclo()) is True
    assert api.STATE == {}
