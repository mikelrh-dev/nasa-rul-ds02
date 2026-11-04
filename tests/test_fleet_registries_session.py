"""Registros por sesión: aislamiento, atomicidad, backup y migración."""
from __future__ import annotations

import json
import os
import sys
import threading

import pytest

APP = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "app")
sys.path.insert(0, APP)

import hangar as HGR  # noqa: E402


def _reg(twins=None, hangar=None, altas=None):
    return {"twins": twins or {}, "hangar": hangar or {}, "altas": altas or {}}


def test_aislamiento_s1_s2_intercalado(tmp_path):
    p1, p2 = tmp_path / "s1.json", tmp_path / "s2.json"
    HGR.save_session_registry(str(p1), _reg(hangar={"A": {}}))
    HGR.save_session_registry(str(p2), _reg(hangar={"B": {}, "C": {}}))
    HGR.save_session_registry(str(p1), _reg(hangar={"A": {}, "D": {}}))
    assert HGR.load_session_registry(str(p1))["hangar"] == {"A": {}, "D": {}}
    assert HGR.load_session_registry(str(p2))["hangar"] == {"B": {}, "C": {}}


def test_ruta_aislada_por_session_id():
    assert HGR.session_registry_path("s1") != HGR.session_registry_path("s2")
    assert HGR.session_registry_path("s1").endswith("registros_flota_s1.json")


@pytest.mark.parametrize("mal", ["../escape", "", "a/b", "x" * 65, "con espacio"])
def test_id_invalido_sin_fichero(tmp_path, mal):
    with pytest.raises(ValueError):
        HGR.session_registry_path(mal)
    assert not list(tmp_path.iterdir())


def test_schema_intacto_y_fallo_no_toca_fichero(tmp_path):
    p = tmp_path / "r.json"
    bueno = _reg(twins={"E1": {"id": "E1"}}, hangar={"E1": {}}, altas={"M1": {}})
    HGR.save_session_registry(str(p), bueno)
    assert HGR.load_session_registry(str(p)) == bueno
    assert isinstance(HGR.load_session_registry(str(p))["twins"], dict)
    pre = p.read_bytes()
    with pytest.raises(ValueError):
        HGR.save_session_registry(str(p), {"twins": {}, "hangar": {}})
    assert p.read_bytes() == pre


def test_corrupto_cae_a_backup_y_sin_backup_a_vacio(tmp_path):
    p, bak = tmp_path / "r.json", tmp_path / "r.json.bak"
    bak.write_text(json.dumps(_reg(hangar={"K": {}})), encoding="utf-8")
    p.write_text("{no json", encoding="utf-8")
    data, aviso = HGR.load_session_registry_with_status(str(p))
    assert data["hangar"] == {"K": {}} and aviso and "backup" in aviso
    p.write_text("{no json", encoding="utf-8")
    data, aviso = HGR.load_session_registry_with_status(str(p), str(tmp_path / "x.bak"))
    assert data == HGR.empty_registry() and aviso


def test_guardado_atomico_sin_tmp_e_interrumpido_conserva_valido(tmp_path, monkeypatch):
    p = tmp_path / "r.json"
    HGR.save_session_registry(str(p), _reg(hangar={"A": {}, "B": {}}))
    assert not (tmp_path / "r.json.tmp").exists()
    monkeypatch.setattr(os, "replace", lambda *a: (_ for _ in ()).throw(OSError("corte")))
    with pytest.raises(OSError):
        HGR.save_session_registry(str(p), _reg(hangar={"X": {}}))
    assert json.loads(p.read_text(encoding="utf-8"))["hangar"] == {"A": {}, "B": {}}
    assert not (tmp_path / "r.json.tmp").exists()


def test_migracion_copia_no_mueve_5_2_3(tmp_path):
    legacy, ses = tmp_path / "leg.json", tmp_path / "ses.json"
    legacy.write_text(json.dumps(_reg(
        twins={f"T{i}": {} for i in range(5)},
        hangar={f"H{i}": {} for i in range(2)},
        altas={f"A{i}": {} for i in range(3)})), encoding="utf-8")
    pre = legacy.read_bytes()
    n = HGR.migrate_legacy_registry(str(legacy), str(ses))
    assert n == {"twins": 5, "hangar": 2, "altas": 3}
    assert legacy.read_bytes() == pre and (tmp_path / "leg.json.bak").exists()
    assert HGR.load_session_registry(str(ses))["altas"] and len(HGR.load_session_registry(str(ses))["twins"]) == 5


def test_migracion_count_mismatch_aborta_sin_parcial(tmp_path, monkeypatch):
    legacy, ses = tmp_path / "leg.json", tmp_path / "ses.json"
    legacy.write_text(json.dumps(_reg(hangar={"H": {}})), encoding="utf-8")

    def mala(ruta, data):
        with open(ruta, "w", encoding="utf-8") as fh:
            json.dump(_reg(), fh)  # pierde 1 hangar a propósito

    monkeypatch.setattr(HGR, "atomic_save_json", mala)
    with pytest.raises(ValueError, match="migración abortada"):
        HGR.migrate_legacy_registry(str(legacy), str(ses))
    assert not ses.exists() and (tmp_path / "leg.json.bak").exists()


def test_migracion_sin_legacy_empieza_vacio(tmp_path):
    ses = tmp_path / "ses.json"
    assert HGR.migrate_legacy_registry(str(tmp_path / "no.json"), str(ses)) == \
        {"twins": 0, "hangar": 0, "altas": 0}
    assert HGR.load_session_registry(str(ses)) == HGR.empty_registry()


def test_concurrencia_serializada(tmp_path):
    p = tmp_path / "r.json"
    HGR.save_session_registry(str(p), _reg())
    hilos = [threading.Thread(target=lambda i=i: HGR.save_session_registry(
        str(p), _reg(hangar={f"E{i}": {}}))) for i in range(8)]
    [t.start() for t in hilos]; [t.join() for t in hilos]
    assert HGR.load_session_registry(str(p))["hangar"]  # JSON válido, sin tmp
    assert not (tmp_path / "r.json.tmp").exists()
