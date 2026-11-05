"""Genera los checksums SHA-256 de los artefactos joblib de clase/scripts.

SEC-JOBLIB-01: `src/ds02_rul/persistence.py::verify_artifact_sha256` busca las
claves en `models/ds02_manifest.json` (bloque `artifacts`). Este generador
registra ahí los digests de los modelos de clase y del bundle v3 que cargan
`src/clase/shap_clase.py`, `src/clase/shap_clase_e2.py`,
`src/clase/train_mlp.py`, `scripts/predict.py` y
`scripts/repackage_artifact.py`.

Orden padre (enmienda): los checksums se crean ANTES del guard, para que las
cargas válidas sigan funcionando y `test_clase_shap*` no se rompa. Es
idempotente: relanzarlo tras reentrenar actualiza los digests. Conserva el
formato CRLF/indent-2 del manifiesto canónico para no inflar el diff.

Uso (desde la raíz del repo)::

    .venv/Scripts/python.exe scripts/make_clase_checksums.py
"""

from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))

from ds02_rul.persistence import sha256_of  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "models", "ds02_manifest.json")

# artefacto relativo a la raíz -> clave en manifest["artifacts"]
ARTEFACTOS = {
    "models/mejor_modelo_clase.joblib": "clase_xgb_sha256",
    "models/mejor_modelo_clase_E2.joblib": "clase_e2_sha256",
    "models/v3_bundle.joblib": "v3_bundle_sha256",
}


def main() -> int:
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)
    artifacts = manifest.setdefault("artifacts", {})
    for rel, key in ARTEFACTOS.items():
        path = os.path.join(ROOT, rel)
        if not os.path.exists(path):
            print(f"omitido (no existe): {rel}")
            continue
        digest = sha256_of(path)
        artifacts[key] = digest
        print(f"{key}  {rel}  {digest}")
    texto = json.dumps(manifest, indent=2, ensure_ascii=False)
    with open(MANIFEST, "wb") as fh:  # CRLF como el manifiesto canónico
        fh.write(texto.replace("\n", "\r\n").encode("utf-8"))
    print(f"manifest actualizado: {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
