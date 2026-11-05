"""CACHE-DRIFT-01: la caché no se reutiliza con un ``manifest_sha256`` stale.

Scenario (spec 2026-11-05-shap-c-arreglos-auditoria, CACHE-DRIFT-01): GIVEN
una copia de ``app/cache/`` cuyo ``artifact.manifest_sha256`` no coincide
con ``models/ds02_manifest.json`` en disco, WHEN se valida la caché o se
pregunta si está disponible, THEN la validación falla ruidoso
(``RuntimeError``) y ``cache_available()`` es ``False``: ningún parquet se
reutiliza bajo un sello roto.

Los tests trabajan sobre copias en ``tmp_path``; el árbol real no se muta.

Run:  python -m pytest tests/test_cache_drift.py -q
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil

import pytest

from app import ui_data_loader as L

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REAL_CACHE = os.path.join(ROOT, "app", "cache")
REAL_MANIFEST_PATH = os.path.join(ROOT, "models", "ds02_manifest.json")


def _sha256(path: str) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _copia_cache(tmp_path) -> str:
    """Copia completa de app/cache (parquets reales) en un directorio temporal."""
    destino = os.path.join(str(tmp_path), "cache")
    shutil.copytree(REAL_CACHE, destino)
    return destino


def _escribir_provenance(cache_dir: str, provenance: dict) -> str:
    ruta = os.path.join(cache_dir, "cache_manifest.json")
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(provenance, fh, indent=2)
    return ruta


def _provenance(cache_dir: str) -> dict:
    with open(os.path.join(cache_dir, "cache_manifest.json"), encoding="utf-8") as fh:
        return json.load(fh)


def test_validacion_falla_ruidoso_con_manifest_stale(tmp_path, monkeypatch):
    """Un digest stale no pasa en silencio: eleva antes de reutilizar nada."""
    cache_dir = _copia_cache(tmp_path)
    provenance = _provenance(cache_dir)
    provenance["artifact"]["manifest_sha256"] = "0" * 64  # stale deliberado
    ruta = _escribir_provenance(cache_dir, provenance)

    monkeypatch.setattr(L, "PROVENANCE_PATH", ruta)
    monkeypatch.setattr(L, "MANIFEST_PATH", REAL_MANIFEST_PATH)
    monkeypatch.setattr(L, "WINDOWS_PATH", os.path.join(cache_dir, "ds02_windows.parquet"))
    monkeypatch.setattr(L, "ROWS_PATH", os.path.join(cache_dir, "ds02_rows.parquet"))

    with pytest.raises(RuntimeError, match="manifest_sha256"):
        L.verify_cache_manifest()

    # Y la puerta de la UI tampoco lo da por bueno: no hay reuse silencioso.
    assert L.cache_available() is False


def test_validacion_acepta_manifest_vigente(tmp_path, monkeypatch):
    """Con el digest real de models/ds02_manifest.json, la validación pasa."""
    cache_dir = _copia_cache(tmp_path)
    provenance = _provenance(cache_dir)
    provenance["artifact"]["manifest_sha256"] = _sha256(REAL_MANIFEST_PATH)
    ruta = _escribir_provenance(cache_dir, provenance)

    monkeypatch.setattr(L, "PROVENANCE_PATH", ruta)
    monkeypatch.setattr(L, "MANIFEST_PATH", REAL_MANIFEST_PATH)

    validado = L.verify_cache_manifest()

    assert validado["artifact"]["manifest_sha256"] == _sha256(REAL_MANIFEST_PATH)


def test_validacion_rechaza_manifest_ausente_del_provenance(tmp_path, monkeypatch):
    """Sin manifest_sha256 registrado no se presume vigencia: falla ruidoso."""
    cache_dir = _copia_cache(tmp_path)
    provenance = _provenance(cache_dir)
    provenance["artifact"].pop("manifest_sha256", None)
    ruta = _escribir_provenance(cache_dir, provenance)

    monkeypatch.setattr(L, "PROVENANCE_PATH", ruta)
    monkeypatch.setattr(L, "MANIFEST_PATH", REAL_MANIFEST_PATH)

    with pytest.raises(RuntimeError, match="manifest_sha256"):
        L.verify_cache_manifest()


def test_cache_real_tiene_manifest_vigente():
    """La caché en disco debe llevar el digest real (regenerada, no stale)."""
    assert L.cache_available() is True
    real = _sha256(REAL_MANIFEST_PATH)
    with open(os.path.join(REAL_CACHE, "cache_manifest.json"), encoding="utf-8") as fh:
        registrado = json.load(fh)["artifact"]["manifest_sha256"]
    assert registrado == real
