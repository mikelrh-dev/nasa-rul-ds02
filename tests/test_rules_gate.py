"""Tests del gate de evidencias `scripts/freeze_rules_evidence.py` (RULES-06).

Seis comprobaciones, en dos bloques:

1. superficie del CLI — cache ausente o incompleta (código 3, nunca «skip»),
   ausencia de TensorFlow en la importación y exclusividad de `--check`/`--write`;
2. reproducción — el gate rehace las cifras comprometidas, detecta la deriva con
   código 4 y no toca el JSON congelado cuando todo cuadra.

El instrumento ausente salta el **test** (marcador `@needs_oof`, copiado de
`test_mia_rules.py`) y falla el **CLI** con código 3: dos políticas, un artefacto.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import copy
import hashlib
import io
import os
import subprocess
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

import freeze_rules_evidence as G  # noqa: E402

needs_oof = pytest.mark.skipif(
    not os.path.exists(os.path.join(ROOT, "_p1_oof_cache.npz")),
    reason="_p1_oof_cache.npz missing",
)

CALIBRACION = os.path.join(ROOT, "mia", "calibracion_banda.json")


def _sha256(path: str) -> str:
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


# ------------------------------------------------- superficie del CLI (2.1)
def test_el_gate_falla_sin_cache_y_no_escribe(tmp_path):
    """La ausencia del instrumento falla con 3 y jamás se anuncia como salto."""
    antes = _sha256(CALIBRACION)

    ausente = tmp_path / "absent.npz"
    salida = io.StringIO()
    assert G.run(cache=str(ausente), stream=salida) == 3
    texto = salida.getvalue()
    assert str(ausente) in texto
    assert "python scripts/p1_oof_cache.py" in texto
    assert "RULES-06" in texto
    assert "skip" not in texto.lower()
    assert _sha256(CALIBRACION) == antes

    # Una cache a la que le falta una clave también es una entrada inválida.
    base = dict(units=np.array([2.0, 2.0]), cycles=np.array([1.0, 2.0]),
                y=np.array([10.0, 9.0]), p_lstm=np.array([9.0, 8.0]),
                p_lgb=np.array([11.0, 10.0]))
    incompleta = tmp_path / "incomplete.npz"
    np.savez(incompleta, **{k: v for k, v in base.items() if k != "y"})
    salida = io.StringIO()
    assert G.run(cache=str(incompleta), stream=salida) == 3
    assert "missing key y" in salida.getvalue()

    # Y una cache con valores no finitos, nombrando la clave culpable.
    rota = dict(base, y=np.array([10.0, np.nan]))
    no_finita = tmp_path / "nonfinite.npz"
    np.savez(no_finita, **rota)
    salida = io.StringIO()
    assert G.run(cache=str(no_finita), stream=salida) == 3
    assert "non-finite values in y" in salida.getvalue()

    assert _sha256(CALIBRACION) == antes


def test_el_gate_no_carga_tensorflow():
    """Importar el gate no arrastra Keras: el caché OOF basta."""
    codigo = (
        f"import sys; sys.path.insert(0, r'{SCRIPTS}');"
        "import freeze_rules_evidence;"
        "print('tensorflow', 'tensorflow' in sys.modules);"
        "print('keras', 'keras' in sys.modules)"
    )
    salida = subprocess.run([sys.executable, "-c", codigo],
                            capture_output=True, text=True)
    assert salida.returncode == 0, salida.stderr
    assert "tensorflow False" in salida.stdout
    assert "keras False" in salida.stdout


def test_el_defecto_es_check_y_los_flags_son_excluyentes(tmp_path):
    """Sin bandera se verifica; `--check` con `--write` es un error de uso."""
    ausente = str(tmp_path / "absent.npz")
    assert G.main(["--cache", ausente]) == 3
    with pytest.raises(SystemExit) as exc:
        G.main(["--check", "--write"])
    assert exc.value.code == 2


# -------------------------------------------------------- reproducción (2.2)
@needs_oof
def test_el_gate_reproduce_las_cifras_comprometidas():
    """La tabla de §13 sale del caché: no es una cita, es un cálculo."""
    salida = io.StringIO()
    assert G.run(G.EXPECTED, stream=salida) == 0
    texto = salida.getvalue()
    for fila in ("Baseline (raw EMA5)", "V1 running-min", "V2 prefix PAVA",
                 "V3 min(prefix PAVA)"):
        assert fila in texto
    assert "(recorded)" in texto
    # La identidad de la envolvente y la máscara pura también se comprueban.
    assert "pure OOF rows" in texto


@needs_oof
def test_el_gate_detecta_drift(tmp_path):
    """Una figura movida una orden por encima de su HULP sale con código 4."""
    malo = copy.deepcopy(G.EXPECTED)
    malo["rmse_r2b"] += 5e-3
    salida = io.StringIO()
    assert G.run(malo, stream=salida) == 4
    texto = salida.getvalue()
    assert "9.623" in texto
    assert "expected" in texto and "observed" in texto
    assert "R2b OOF RMSE" in texto


@needs_oof
def test_la_escritura_es_idempotente(tmp_path):
    """`--write` sobre un árbol que cuadra no toca el JSON congelado."""
    antes = _sha256(CALIBRACION)
    salida = io.StringIO()
    assert G.run(G.EXPECTED, write=True, stream=salida) == 0
    assert "no change" in salida.getvalue()
    assert _sha256(CALIBRACION) == antes
