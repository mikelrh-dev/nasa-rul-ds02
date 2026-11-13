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

from app.lib import n8n_payload as UN  # noqa: E402
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
    assert payload["umbrales"] == {"apto": 25.0, "hangar": 20.0}


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


# --------------------------------------------------------- reintentos / auth
def test_enviar_5xx_reintenta_y_acaba_bien(monkeypatch):
    """Un 5xx se reintenta: el segundo intento puede salvar la notificacion."""
    fallo = urllib.error.HTTPError("http://n8n.invalid/hook", 503, "boom", {}, None)
    monkeypatch.setattr(N8N.time, "sleep", lambda *_: None)
    with mock.patch("urllib.request.urlopen", side_effect=[fallo, _Resp()]) as m:
        r = N8N.enviar_decision("HANGAR", _payload(),
                                webhook_url="http://n8n.invalid/hook")
    assert m.call_count == 2
    assert r == {"ok": True, "status": 200, "decision": "HANGAR"}


def test_enviar_4xx_no_reintenta(monkeypatch):
    """Un 4xx no mejora reenviando: se devuelve con su status al primer intento."""
    fallo = urllib.error.HTTPError("http://n8n.invalid/hook", 400, "bad", {}, None)
    monkeypatch.setattr(N8N.time, "sleep", lambda *_: None)
    with mock.patch("urllib.request.urlopen", side_effect=fallo) as m:
        r = N8N.enviar_decision("HANGAR", _payload(),
                                webhook_url="http://n8n.invalid/hook")
    assert m.call_count == 1
    assert r == {"ok": False, "status": 400, "decision": "HANGAR"}


def test_enviar_manda_token_si_esta_configurado(monkeypatch):
    """Header Auth: el secreto de entorno viaja en X-DS02-Token, nunca en el repo."""
    monkeypatch.setenv("N8N_WEBHOOK_TOKEN", "secreto-de-prueba")
    with mock.patch("urllib.request.urlopen", return_value=_Resp()) as m:
        N8N.enviar_decision("HANGAR", _payload(),
                            webhook_url="http://n8n.invalid/hook")
    req = m.call_args[0][0]
    assert req.get_header("X-ds02-token") == "secreto-de-prueba"


def test_enviar_sin_token_no_manda_header(monkeypatch):
    monkeypatch.delenv("N8N_WEBHOOK_TOKEN", raising=False)
    with mock.patch("urllib.request.urlopen", return_value=_Resp()) as m:
        N8N.enviar_decision("HANGAR", _payload(),
                            webhook_url="http://n8n.invalid/hook")
    req = m.call_args[0][0]
    assert req.get_header("X-ds02-token") is None


def test_apto_tambien_notifica():
    # APTO también notifica: llega a la rama Set log de n8n.
    assert UN.debe_notificar("APTO", "fpA", set()) is True


def test_dashboard_llama_una_vez_tras_decision_en_vivo():
    # La sala de casos se extrajo a `ui/_tab_casos.py` (B1).
    src = open(os.path.join(ROOT, "app", "ui", "_tab_casos.py"),
               encoding="utf-8").read()
    assert "payload_desde_traza" in src
    assert "enviar_decision" in src
    assert src.count("enviar_decision(") == 1


# --------------------------------------------------------------- flujo
def test_flujo_json_valido_con_3_ramas():
    path = os.path.join(ROOT, "n8n", "flujo.json")
    with open(path, encoding="utf-8") as fh:
        flujo = json.load(fh)
    # Exportado inactivo y con Header Auth: no se promete una instancia viva.
    assert flujo["active"] is False
    webhooks = [n for n in flujo["nodes"] if "webhook" in n["type"].lower()]
    assert webhooks and all(
        n["parameters"].get("authentication") == "headerAuth" for n in webhooks
    )
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


# ------------------------------------------------- telegram + fallback
def _flujo():
    path = os.path.join(ROOT, "n8n", "flujo.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _switch(flujo):
    return next(n for n in flujo["nodes"] if "switch" in n["type"].lower())


def _destinos(flujo):
    """Nombres de nodo que aparecen como destino en alguna conexion."""
    destinos = set()
    for conexion in flujo["connections"].values():
        for salida in conexion.get("main", []):
            for destino in salida:
                destinos.add(destino["node"])
    return destinos


RAMA_A_TELEGRAM = {
    0: "APTO Telegram aviso",
    1: "INSPECCION Telegram aviso",
    2: "HANGAR Telegram aviso",
    3: "FALLBACK Telegram alerta",
}
RAMA_A_ACCION = {
    0: "APTO Set log",
    1: "Set INSPECCION flat",
    2: "HANGAR Postgres insert",
    3: "FALLBACK Set no reconocida",
}


def test_switch_fallback_output_extra():
    """SIN_DECISION / decision no reconocida tiene salida propia (indice 3)."""
    switch = _switch(_flujo())
    assert switch["parameters"]["options"]["fallbackOutput"] == "extra"


def test_sin_decision_cae_en_el_fallback_no_en_una_regla():
    """Solo APTO/INSPECCION/HANGAR tienen regla; SIN_DECISION va al extra."""
    switch = _switch(_flujo())
    reglas = switch["parameters"]["rules"]["values"]
    assert [r["outputKey"] for r in reglas] == ["APTO", "INSPECCION", "HANGAR"]
    derechas = [r["conditions"]["conditions"][0]["rightValue"] for r in reglas]
    assert "SIN_DECISION" not in derechas


def test_switch_tiene_4_salidas_conectadas():
    flujo = _flujo()
    salidas = flujo["connections"]["Switch por decision"]["main"]
    assert len(salidas) == 4  # APTO, INSPECCION, HANGAR + fallback


def test_cada_rama_del_switch_avisa_por_telegram():
    """Cada rama conserva su accion y ademas manda el aviso fire-and-forget."""
    flujo = _flujo()
    salidas = flujo["connections"]["Switch por decision"]["main"]
    for indice in range(4):
        destinos = {d["node"] for d in salidas[indice]}
        assert RAMA_A_ACCION[indice] in destinos
        assert RAMA_A_TELEGRAM[indice] in destinos


def test_telegram_fire_and_forget_sin_botones():
    flujo = _flujo()
    nodos = [n for n in flujo["nodes"] if "telegram" in n["type"].lower()]
    assert len(nodos) == 4
    destinos = _destinos(flujo)
    for nodo in nodos:
        assert nodo["name"] in destinos, "el aviso esta conectado"
        assert nodo["parameters"]["resource"] == "message"
        assert nodo["parameters"]["operation"] == "sendMessage"
        assert nodo["parameters"]["additionalFields"] == {}
        assert nodo["parameters"]["text"].startswith("=")
        # Chat ID por entorno: nada identificable queda en el repo.
        assert "$env" in nodo["parameters"]["chatId"]
        params = json.dumps(nodo["parameters"]).lower()
        assert "inlinekeyboard" not in params
        assert "replymarkup" not in params
        credencial = nodo["credentials"]["telegramApi"]
        assert credencial["id"] == "REEMPLAZAR_CREDENCIAL"


def test_telegram_texto_incluye_decision_y_fingerprint():
    cuerpo = io.StringIO()
    json.dump(_flujo(), cuerpo)
    texto = cuerpo.getvalue()
    assert "SIN_DECISION" in texto
    for nodo in (n for n in _flujo()["nodes"]
                 if "telegram" in n["type"].lower()):
        assert "fingerprint" in nodo["parameters"]["text"]


def test_fallback_no_ejecuta_acciones_y_avisa():
    flujo = _flujo()
    salidas = flujo["connections"]["Switch por decision"]["main"]
    destinos = {d["node"] for d in salidas[3]}
    assert destinos == {"FALLBACK Set no reconocida",
                        "FALLBACK Telegram alerta"}
    assert not any("Postgres" in d or "Gmail" in d or "Sheets" in d
                   for d in destinos)


def test_repo_no_guarda_secretos_de_telegram():
    cuerpo = io.StringIO()
    json.dump(_flujo(), cuerpo)
    bruto = cuerpo.getvalue().lower()
    assert "password" not in bruto
    assert "access_token" not in bruto
    assert "accesstoken" not in bruto
    assert "bot_token" not in bruto
    assert "telegramapitoken" not in bruto


# ------------------------------------- H2 / H4 / H5 / H6a (cambio 2026-11-13)
def _nodo(flujo, nombre):
    return next(n for n in flujo["nodes"] if n["name"] == nombre)


def _expresiones_fallback(flujo):
    """(log del Set, texto del Telegram) del fallback."""
    set_fb = _nodo(flujo, "FALLBACK Set no reconocida")
    log = set_fb["parameters"]["assignments"]["assignments"][0]["value"]
    telegram = _nodo(flujo, "FALLBACK Telegram alerta")
    return log, telegram["parameters"]["text"]


# --------------------------------------------------------------- H2: Gmail
def test_gmail_umbrales_por_defecto_25_20():
    """H2: el correo de HANGAR usa 25/20 por defecto, no 30/25."""
    gmail = _nodo(_flujo(), "HANGAR Gmail")
    mensaje = gmail["parameters"]["message"]
    assert "const umA = (um.apto ?? 25)" in mensaje
    assert "const umH = (um.hangar ?? 20)" in mensaje
    assert "(um.apto ?? 30)" not in mensaje
    assert "(um.hangar ?? 25)" not in mensaje


def test_gmail_umbrales_ordenados_y_citados_en_el_texto():
    """TRIANGULATE H2: los defaults respetan ADR-013 y viajan al texto."""
    import re

    mensaje = _nodo(_flujo(), "HANGAR Gmail")["parameters"]["message"]
    m_apto = re.search(r"\(um\.apto \?\? (\d+)\)", mensaje)
    m_hangar = re.search(r"\(um\.hangar \?\? (\d+)\)", mensaje)
    assert m_apto is not None and m_hangar is not None
    apto = int(m_apto.group(1))
    hangar = int(m_hangar.group(1))
    assert (apto, hangar) == (25, 20)
    assert hangar < apto
    # El texto del correo imprime los umbrales recibidos (payload gana).
    assert "Umbrales: apto>=' + fmt(umA)" in mensaje
    assert "' / hangar<' + fmt(umH)" in mensaje


# ------------------------------------------------------------ H4: Calendar
def test_calendar_declara_zona_europe_madrid():
    """H4: el evento de Calendar declara Europe/Madrid y un summary no vacío."""
    cal = _nodo(_flujo(), "HANGAR Google Calendar")
    params = cal["parameters"]
    assert params.get("timeZone") == "Europe/Madrid"
    assert (params.get("summary") or "").strip()


def test_flujo_no_se_queda_con_la_zona_por_defecto():
    """TRIANGULATE H4: ninguna zona de n8n por defecto sigue en el flujo."""
    texto = json.dumps(_flujo())
    assert "America/New_York" not in texto
    assert texto.count("Europe/Madrid") >= 1


# ------------------------------------------------------------- H5: Postgres
def test_postgres_mapea_idempotency_key():
    """H5: el insert guarda la clave de idempotencia del payload."""
    pg = _nodo(_flujo(), "HANGAR Postgres insert")
    columnas = pg["parameters"]["columns"]["value"]
    assert columnas["idempotency_key"] == (
        "={{ $json.body.idempotency_key || $json.idempotency_key }}"
    )


def test_postgres_schema_conoce_idempotency_key():
    """TRIANGULATE H5: la columna existe en el esquema del nodo."""
    pg = _nodo(_flujo(), "HANGAR Postgres insert")
    ids = {c["id"] for c in pg["parameters"]["columns"]["schema"]}
    assert "idempotency_key" in ids
    tipos = {c["id"]: c["type"] for c in pg["parameters"]["columns"]["schema"]}
    assert tipos["idempotency_key"] == "string"


# ------------------------------------------------------ H6a: fallback
def test_fallback_set_distingue_sin_decision():
    """H6a: SIN_DECISION se registra como tal, no como no reconocida."""
    log, _ = _expresiones_fallback(_flujo())
    assert "=== 'SIN_DECISION'" in log
    assert "SIN_DECISION · sin accion" in log
    assert "DECISION NO RECONOCIDA" in log
    # La forma vieja (SIN_DECISION renderizada como no reconocida) desaparece.
    assert "'DECISION NO RECONOCIDA: ' + ($json.body.decision" not in log


def test_fallback_telegram_distingue_sin_decision():
    """TRIANGULATE H6a: el aviso de Telegram también separa ambos casos."""
    _, texto = _expresiones_fallback(_flujo())
    assert "=== 'SIN_DECISION'" in texto
    assert "SIN_DECISION (sin accion" in texto
    assert "DECISION NO RECONOCIDA" in texto
    assert "DECISION NO RECONOCIDA: \"{{" not in texto
    # El aviso conserva la huella: el dedupe por fingerprint sigue leyéndose.
    assert "fingerprint" in texto
