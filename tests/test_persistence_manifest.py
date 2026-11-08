"""Persistencia DS02 sin modelos pesados: manifiesto, sha, allowlist y huella.

`save_ensemble`/`build_manifest` de verdad exigen TF/Keras, asi que aqui solo
se ejercita su guarda de entrada (el bundle equivocado se rechaza antes de
escribir nada) y las funciones puras de verificacion con `tmp_path`.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys

import joblib
import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from ds02_rul.persistence import (  # noqa: E402
    assert_ds02_artifact,
    data_fingerprint,
    resolve_within_repo,
    save_ensemble,
    sha256_of,
    verify_artifact_sha256,
    write_manifest,
)


def _victima(tmp_path):
    p = str(tmp_path / "m.joblib")
    joblib.dump({"a": 1}, p)
    return p


def _manifiesto_hermano(tmp_path, victima, clave="clave_prueba_sha256"):
    manifiesto = {"artifacts": {clave: sha256_of(victima)}}
    write_manifest(str(tmp_path / "ds02_manifest.json"), manifiesto)
    return manifiesto


def test_write_manifest_hace_roundtrip_en_tmp(tmp_path):
    """El manifiesto escrito se lee de vuelta identico (JSON indentado)."""
    manifiesto = {"formato": 1, "semilla": 42, "anidado": {"a": [1, 2, 3]}}
    ruta = str(tmp_path / "ds02_manifest.json")
    write_manifest(ruta, manifiesto)
    with open(ruta, encoding="utf-8") as fh:
        assert json.load(fh) == manifiesto


def test_sha256_of_coincide_con_hashlib_por_bloques(tmp_path):
    """El hash del fichero es el sha256 hexadecimal de sus bytes."""
    ruta = str(tmp_path / "x.bin")
    with open(ruta, "wb") as fh:
        fh.write(b"hola-ds02" * 1000)
    esperado = hashlib.sha256(b"hola-ds02" * 1000).hexdigest()
    assert sha256_of(ruta) == esperado
    assert len(sha256_of(ruta)) == 64


def test_verify_acepta_artefacto_con_manifiesto_hermano(tmp_path):
    """Con checksum correcto en el manifiesto hermano, la verificacion pasa."""
    victima = _victima(tmp_path)
    _manifiesto_hermano(tmp_path, victima)
    assert verify_artifact_sha256(victima, "clave_prueba_sha256") == sha256_of(victima)


def test_verify_rechaza_artefacto_adulterado(tmp_path):
    """Un byte de mas rompe el sha: RuntimeError antes de deserializar."""
    victima = _victima(tmp_path)
    _manifiesto_hermano(tmp_path, victima)
    with open(victima, "ab") as fh:
        fh.write(b"x")
    with pytest.raises(RuntimeError, match="sha256 mismatch"):
        verify_artifact_sha256(victima, "clave_prueba_sha256")


def test_resolve_within_repo_acepta_dentro_y_rechaza_traversal(tmp_path):
    """Allowlist: dentro del repo pasa; `../` o ruta externa, RuntimeError."""
    dentro = resolve_within_repo(os.path.join("models", "ensemble.joblib"),
                                 base=str(tmp_path))
    assert dentro.startswith(os.path.abspath(str(tmp_path)))
    with pytest.raises(RuntimeError, match="outside"):
        resolve_within_repo("../fuera.joblib", base=str(tmp_path))
    with pytest.raises(RuntimeError, match="outside"):
        resolve_within_repo("/etc/passwd", base=str(tmp_path))


def test_assert_ds02_artifact_rechaza_bundle_equivocado_antes_de_escribir(tmp_path):
    """Scaler de 16 canales o n_op distinto: ValueError y ningun fichero escrito."""

    class _Scaler:
        n_features_in_ = 16

    class _Mal:
        scaler = _Scaler()
        n_op = 4

    with pytest.raises(ValueError, match="16"):
        assert_ds02_artifact(_Mal())
    with pytest.raises(ValueError, match="16"):
        save_ensemble(_Mal(), out_dir=str(tmp_path))
    assert list(tmp_path.iterdir()) == []


def test_data_fingerprint_estable_orden_independiente_y_sensible(tmp_path):
    """La huella no depende del orden de claves y cambia si cambian los datos."""
    a = {"W": np.array([[1.0, 2.0], [3.0, 4.0]]), "y": np.array([10.0, 20.0])}
    b = {"y": np.array([10.0, 20.0]), "W": np.array([[1.0, 2.0], [3.0, 4.0]])}
    assert data_fingerprint(a) == data_fingerprint(b)
    assert len(data_fingerprint(a)) == 64
    c = {"W": np.array([[9.0, 2.0], [3.0, 4.0]]), "y": np.array([10.0, 20.0])}
    assert data_fingerprint(a) != data_fingerprint(c)
