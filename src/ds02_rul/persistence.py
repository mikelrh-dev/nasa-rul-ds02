"""Persistencia de artefactos: `.keras` nativo para el grafo y `joblib` para el resto.

Este módulo garantiza tres cosas:

* el grafo Keras se guarda con `model.save(...)` en formato nativo y **no** se
  mete dentro del joblib, así que el pickle no lleva bytecode serializado;
* cada artefacto tiene un manifiesto que registra qué lo produjo, para que un
  bundle DS02 no pueda sustituirse por otro con distinta forma sin avisar;
* **nunca se deserializa sin verificar**: `load_ensemble` y `load_bilstm`
  calculan el SHA-256 del fichero y lo comparan con el manifiesto
  (`models/ds02_manifest.json` y `app/cache/cache_manifest.json`) *antes* de
  llamar a `joblib.load` o `keras.models.load_model`. Si no coincide, lanzan
  `RuntimeError` sin tocar el pickle. No se usa `eval` ni `exec`.
"""
from __future__ import annotations

import hashlib
import json
import os

import joblib
import numpy as np

ENSEMBLE_FILE = "ensemble.joblib"
SCALER_FILE = "scaler.joblib"
BILSTM_FILE = "bilstm_ds02.keras"
MANIFEST_FILE = "ds02_manifest.json"

EXPECTED_N_FEATURES = 18
EXPECTED_N_OP = 4

# Raíz del repo: src/ds02_rul/persistence.py está tres niveles por debajo.
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MANIFEST_CANDIDATES_DS02 = [
    os.path.join(REPO_ROOT, "models", MANIFEST_FILE),
    os.path.join(REPO_ROOT, "app", "cache", "cache_manifest.json"),
]


def sha256_of(path: str) -> str:
    """SHA-256 hexadecimal de un fichero, leído por bloques de 1 MiB."""
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expected_hashes(path: str, key: str) -> tuple[list[str], list[str]]:
    """Recoge los SHA-256 esperados para `key` de los manifiestos del repo y vecinos.

    Devuelve (hashes, manifest_paths_found). Aquí no se deserializa nada: los
    manifiestos son JSON plano y se leen solo con `json.load`.
    """
    candidates: list[str] = []
    sibling = os.path.join(os.path.dirname(os.path.abspath(path)), MANIFEST_FILE)
    candidates.append(sibling)
    candidates.extend(_MANIFEST_CANDIDATES_DS02)
    # cache_manifest.json también puede estar junto al artefacto (estructura de app/cache).
    sibling_cache = os.path.join(os.path.dirname(os.path.abspath(path)), "cache_manifest.json")
    candidates.append(sibling_cache)

    hashes: list[str] = []
    found: list[str] = []
    seen: set[str] = set()
    for manifest_path in candidates:
        if not os.path.exists(manifest_path) or manifest_path in seen:
            continue
        seen.add(manifest_path)
        try:
            with open(manifest_path, encoding="utf-8") as fh:
                manifest = json.load(fh)
        except (OSError, ValueError) as exc:
            raise RuntimeError(f"refusing to load {path!r}: cannot read manifest {manifest_path!r}: {exc}") from exc
        found.append(manifest_path)
        # ds02_manifest.json guarda `artifacts.<key>_sha256` y cache_manifest.json
        # guarda `artifact.<key>_sha256`. Se aceptan las dos estructuras.
        for container in (manifest.get("artifacts") or {}, manifest.get("artifact") or {}):
            value = container.get(key)
            if isinstance(value, str) and value:
                hashes.append(value.strip())
    return hashes, found


def verify_artifact_sha256(path: str, key: str) -> str:
    """Verifica `path` contra el manifiesto ANTES de deserializar.

    Lanza `RuntimeError` (sin deserializar) si no encuentra manifiesto o si el
    hash calculado no coincide con *todos* los esperados. Devuelve el digest
    verificado.
    """
    hashes, found = _expected_hashes(path, key)
    if not found:
        raise RuntimeError(
            f"refusing to load {path!r}: no manifest found to verify sha256 against "
            f"(looked for {MANIFEST_FILE} and cache_manifest.json in the repo and "
            f"next to the artifact). Refusing to deserialize unverified pickle."
        )
    if not hashes:
        raise RuntimeError(
            f"refusing to load {path!r}: manifest(s) {found} record no `{key}` sha256. "
            "Refusing to deserialize unverified pickle."
        )
    actual = sha256_of(path)
    mismatched = [h for h in hashes if h.lower() != actual.lower()]
    if mismatched:
        raise RuntimeError(
            f"refusing to deserialize {path!r}: sha256 mismatch "
            f"(actual={actual}, expected={hashes}). Artifact was not loaded. "
            f"Verified against manifests: {found}."
        )
    return actual


def resolve_within_repo(path: str, base: str | None = None) -> str:
    """Lista blanca: `path` debe resolver dentro del repo (o de `base`).

    Se usa para rutas de artefacto configurables desde fuera (por ejemplo
    `DS02_ARTIFACT`), de modo que una variable de entorno no pueda apuntar el
    cargador a un fichero arbitrario del sistema.
    """
    root = os.path.abspath(base or REPO_ROOT)
    candidate = os.path.abspath(path if os.path.isabs(path) else os.path.join(root, path))
    if os.path.commonpath([root]) != os.path.commonpath([root, candidate]):
        raise RuntimeError(
            f"artifact path {path!r} resolves outside the repository root {root!r}; refusing to load."
        )
    return candidate


def build_manifest(ensemble, metrics: dict, seed: int, dataset: str = "DS02", **extra) -> dict:
    """Compone el registro de procedencia de una ejecución terminada."""
    import keras
    import lightgbm
    import sklearn
    import tensorflow as tf

    model = ensemble._resolve_model()
    lgb_params = ensemble.lgb_standalone.get_params()
    return {
        "format_version": 1,
        "code_version": extra.pop("code_version", "uncommitted"),
        "dataset": dataset,
        "seed": int(seed),
        "python": extra.pop("python", None),
        "tensorflow": tf.__version__,
        "keras": keras.__version__,
        "sklearn": sklearn.__version__,
        "lightgbm": extra.pop("lightgbm", lightgbm.__version__),
        # El objetivo de la rama tabular es una decisión con su propio registro
        # (ADR-003, y ADR-007 para el experimento de la mediana descartado). Se
        # lee del estimador ajustado para poder auditar el bundle en vez de
        # confiar en él: la etiqueta del notebook es prosa, esto es el artefacto.
        "lgb_objective": {
            "objective": lgb_params.get("objective"),
            "alpha": lgb_params.get("alpha"),
        },
        "unit_partition": extra.pop(
            "unit_partition", {"fit": [2, 5, 10, 18, 20], "holdout": [16], "test": [11, 14, 15]}
        ),
        "model_shape": {
            "scaler_n_features": int(ensemble.scaler.n_features_in_),
            "n_op": int(ensemble.n_op),
            "lgb_n_features": int(ensemble.lgb_standalone.n_features_in_),
            "bilstm_input_shape": [d if d is not None else None for d in model.input_shape],
            "bilstm_params": int(model.count_params()),
            # El ancho del meta-aprendiz es la clave de la revisión de ablación
            # del ciclo: 2 columnas son [p_lstm, p_lgb] y 3 devuelven el reloj.
            "meta_features": int(ensemble.ridge_meta.n_features_in_),
        },
        # La banda de predicción calibrada viaja con el bundle. Las filas con
        # las que se ajustó el meta-aprendiz se registran aparte en
        # `meta_protocol`, que pasa el notebook.
        "conformal": getattr(ensemble, "conformal", None),
        "inference_contract": {
            "window_size": int(ensemble.window_size),
            "beta": float(ensemble.beta),
            "ema_span": int(ensemble.ema_span),
            "cycle_channel": bool(model.input_shape[-1] == EXPECTED_N_FEATURES + 1),
            "meta_features": int(ensemble.ridge_meta.n_features_in_),
        },
        "scaler_fingerprint_mean_first4": [round(float(v), 4) for v in ensemble.scaler.mean_[:4]],
        "metrics": metrics,
        **extra,
    }


def assert_ds02_artifact(ensemble) -> None:
    """Cancela el guardado si el bundle no tiene la forma DS02 que declara."""
    n_features = int(getattr(ensemble.scaler, "n_features_in_", -1))
    if n_features != EXPECTED_N_FEATURES:
        raise ValueError(
            f"refusing to save: scaler expects {n_features} channels, DS02 requires "
            f"{EXPECTED_N_FEATURES}. A wrong-paradigm artifact would have 16."
        )
    if int(ensemble.n_op) != EXPECTED_N_OP:
        raise ValueError(
            f"refusing to save: n_op={ensemble.n_op}, DS02 requires {EXPECTED_N_OP}"
        )


def save_ensemble(ensemble, out_dir: str = ".", manifest: dict | None = None) -> dict:
    """Escribe el bundle, el escalador y el modelo Keras nativo.

    Devuelve un diccionario con las rutas escritas y sus hashes.
    """
    os.makedirs(out_dir, exist_ok=True)
    assert_ds02_artifact(ensemble)

    model = ensemble._resolve_model()
    bilstm_path = os.path.join(out_dir, BILSTM_FILE)
    model.save(bilstm_path)

    scaler_path = os.path.join(out_dir, SCALER_FILE)
    joblib.dump(ensemble.scaler, scaler_path)

    # El grafo se referencia por ruta; nunca se serializa dentro del bundle.
    detached = _detached_copy(ensemble, bilstm_path)
    ensemble_path = os.path.join(out_dir, ENSEMBLE_FILE)
    joblib.dump(detached, ensemble_path)

    written = {
        "ensemble": ensemble_path,
        "scaler": scaler_path,
        "bilstm": bilstm_path,
        "sha256": {
            "ensemble": sha256_of(ensemble_path),
            "scaler": sha256_of(scaler_path),
            "bilstm": sha256_of(bilstm_path),
        },
    }

    if manifest is not None:
        manifest = dict(manifest)
        manifest["artifacts"] = {
            "ensemble_sha256": written["sha256"]["ensemble"],
            "bilstm_sha256": written["sha256"]["bilstm"],
            "bilstm_bytes": os.path.getsize(bilstm_path),
            "ensemble_bytes": os.path.getsize(ensemble_path),
        }
        manifest_path = os.path.join(out_dir, MANIFEST_FILE)
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2)
        written["manifest"] = manifest_path

    return written


def _detached_copy(ensemble, bilstm_path: str):
    """Clona el ensamble cambiando el modelo Keras por su ruta.

    Evita serializar un grafo Keras vivo (lo que ataba el artefacto antiguo a
    una versión concreta) y conserva todos los estimadores ajustados.
    """
    from .ensemble import HybridStackingEnsemble

    clone = HybridStackingEnsemble.__new__(HybridStackingEnsemble)
    clone.__dict__.update(ensemble.__dict__)
    clone.bilstm_model = None
    clone.bilstm_path = os.path.abspath(bilstm_path)
    return clone


def load_bilstm(path: str = BILSTM_FILE):
    """Carga el grafo Keras nativo registrando antes la capa de pooling propia.

    Keras resuelve una capa propia por nombre al deserializar, así que el módulo
    que la define ya debe estar importado. Importar `.pooling` aquí ejecuta su
    decorador `register_keras_serializable` y hace que el orden no importe.
    """
    import keras

    from . import pooling  # noqa: F401  (registers LastStepPooling)

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"BiLSTM artifact not found at {path!r}. Save it with "
            "ds02_rul.persistence.save_ensemble (writes bilstm_ds02.keras)."
        )
    # SHA-256 verificado ANTES de deserializar: se rechazan grafos manipulados.
    verify_artifact_sha256(path, "bilstm_sha256")
    return keras.models.load_model(path, compile=False)


def load_ensemble(path: str = ENSEMBLE_FILE):
    """Carga un bundle y vuelve a engancharle su grafo Keras nativo.

    Seguridad: el SHA-256 de `path` se verifica contra
    `models/ds02_manifest.json` y `app/cache/cache_manifest.json` (y un
    manifiesto vecino al artefacto) **antes** de `joblib.load`. Si no coincide
    se lanza `RuntimeError` y el pickle no se deserializa. No se usa `eval` ni
    `exec`. De esta comprobación dependen `app/ui_inference.get_ensemble` y
    `app/api.py`, que pasan por esta función.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"ensemble artifact not found at {path!r}")
    verify_artifact_sha256(path, "ensemble_sha256")
    ensemble = joblib.load(path)
    if getattr(ensemble, "bilstm_model", None) is None and getattr(ensemble, "bilstm_path", None):
        candidate = ensemble.bilstm_path
        if not os.path.exists(candidate):
            candidate = os.path.join(os.path.dirname(os.path.abspath(path)), BILSTM_FILE)
        ensemble.bilstm_model = load_bilstm(candidate)
        ensemble.bilstm_path = candidate
    return ensemble


def write_manifest(path: str, manifest: dict) -> None:
    """Guarda un manifiesto JSON con indentación estable."""
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)


def data_fingerprint(arrays: dict) -> str:
    """Hash estable de las formas ingeridas y las filas de frontera por unidad."""
    digest = hashlib.sha256()
    for key in sorted(arrays):
        value = np.asarray(arrays[key])
        digest.update(key.encode())
        digest.update(str(value.shape).encode())
        digest.update(value[:1].tobytes())
        digest.update(value[-1:].tobytes())
    return digest.hexdigest()
