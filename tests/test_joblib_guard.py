"""SEC-JOBLIB-01 RED: los 5 `joblib.load` de clase/scripts van guardados.

Un `joblib.load` sin checksum válido debe rechazarse ANTES de deserializar:
`verify_artifact_sha256` (src/ds02_rul/persistence.py) levanta `RuntimeError`
sin tocar el pickle. Disparadores:

* escaneo estático: cada sitio llama `verify_artifact_sha256` antes del load;
* conductuales: un artefacto sin manifiesto o adulterado levanta `RuntimeError`
  y `joblib.load` nunca se invoca (centinela).
"""

from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "src"))

from ds02_rul.persistence import sha256_of, verify_artifact_sha256  # noqa: E402

SITIOS = {
    "src/clase/shap_clase.py": "clase_xgb_sha256",
    "src/clase/shap_clase_e2.py": "clase_e2_sha256",
    "src/clase/train_mlp.py": "clase_xgb_sha256",
    "scripts/legacy/predict.py": "v3_bundle_sha256",
    "scripts/legacy/repackage_artifact.py": "ensemble_sha256",
}


@pytest.mark.parametrize("fichero,key", list(SITIOS.items()))
def test_sitio_guardado_antes_del_load(fichero, key):
    """Cada sitio verifica el checksum del artefacto antes de `joblib.load`."""
    src = open(os.path.join(ROOT, fichero), encoding="utf-8").read()
    assert "verify_artifact_sha256" in src, f"{fichero} no guarda el load"
    assert key in src, f"{fichero} no usa la clave {key}"
    assert src.index("verify_artifact_sha256") < src.index("joblib.load"), (
        f"{fichero}: verify debe preceder a joblib.load"
    )


def _veneno(path):
    """Bytes que NO son un pickle: si el guard falla, joblib.load revienta."""
    with open(path, "wb") as fh:
        fh.write(b"no-es-un-pickle-" * 8)
    return path


def test_sin_manifiesto_se_rechaza_antes_de_deserializar(tmp_path):
    """Sin checksum válido: RuntimeError, no UnpicklingError (orden pre-deser.)."""
    victim = _veneno(str(tmp_path / "modelo.joblib"))
    with pytest.raises(RuntimeError, match="refusing"):
        verify_artifact_sha256(victim, "clase_xgb_sha256")


def test_checksum_valido_pasa_y_adulterado_se_rechaza(tmp_path):
    """Manifiesto hermano válido → ok; artefacto tocado → RuntimeError."""
    victim = str(tmp_path / "m.joblib")
    import joblib

    joblib.dump({"a": 1}, victim)
    manifiesto = {"artifacts": {"clave_prueba_sha256": sha256_of(victim)}}
    import json

    with open(tmp_path / "ds02_manifest.json", "w", encoding="utf-8") as fh:
        json.dump(manifiesto, fh)
    assert verify_artifact_sha256(victim, "clave_prueba_sha256") == sha256_of(victim)
    with open(victim, "ab") as fh:
        fh.write(b"x")
    with pytest.raises(RuntimeError, match="sha256 mismatch"):
        verify_artifact_sha256(victim, "clave_prueba_sha256")


class _Centinela:
    """joblib.load sustituido: si el guard falla, queda constancia."""

    def __init__(self):
        self.llamado = False

    def load(self, path):  # no debe llamarse nunca tras el guard
        self.llamado = True
        raise AssertionError(f"joblib.load invocado sin guard: {path}")


def test_shap_clase_rechaza_sin_checksum(tmp_path, monkeypatch):
    from src.clase import shap_clase as SC

    victim = _veneno(str(tmp_path / "mejor_modelo_clase.joblib"))
    centinela = _Centinela()
    monkeypatch.setattr(SC, "MODEL_PATH", victim)
    monkeypatch.setattr("joblib.load", centinela.load)
    with pytest.raises(RuntimeError, match="refusing"):
        SC.ejecutar_shap(verbose=False)
    assert not centinela.llamado


def test_shap_e2_rechaza_sin_checksum(tmp_path, monkeypatch):
    from src.clase import shap_clase_e2 as SE2

    victim = _veneno(str(tmp_path / "mejor_modelo_clase_E2.joblib"))
    centinela = _Centinela()
    monkeypatch.setattr("joblib.load", centinela.load)
    with pytest.raises(RuntimeError, match="refusing"):
        SE2.ejecutar_shap(modelo=victim, verbose=False)
    assert not centinela.llamado


def test_train_mlp_rechaza_sin_checksum(tmp_path, monkeypatch):
    from src.clase import train_mlp as TM

    victim = _veneno(str(tmp_path / "mejor_modelo_clase.joblib"))
    centinela = _Centinela()
    monkeypatch.setattr(TM, "CLASE_MODEL_PATH", victim)
    monkeypatch.setattr("joblib.load", centinela.load)
    with pytest.raises(RuntimeError, match="refusing"):
        TM.importancia_mejor_clasico()
    assert not centinela.llamado


def test_predict_rechaza_sin_checksum(tmp_path, monkeypatch):
    sys.path.insert(0, os.path.join(ROOT, "scripts", "legacy"))
    import predict as P

    victim = _veneno(str(tmp_path / "v3_bundle.joblib"))
    centinela = _Centinela()
    monkeypatch.setattr(P, "BUNDLE", victim)
    monkeypatch.setattr("joblib.load", centinela.load)
    with pytest.raises(RuntimeError, match="refusing"):
        P._load()
    assert not centinela.llamado
