"""Tests del gate de evidencias `scripts/auditoria/freeze_rules_evidence.py` (RULES-06).

Seis comprobaciones, en dos bloques:

1. superficie del CLI — cache ausente o incompleta (código 3, nunca «skip»),
   ausencia de TensorFlow en la importación y exclusividad de `--check`/`--write`;
2. reproducción — el gate verifica la banda publicada contra el instrumento
   congelado (`mia/instrumento_oof.npz`, versionado), detecta la deriva con
   código 4 y no toca el JSON congelado cuando todo cuadra.

La evidencia de la banda viaja con el repositorio, así que no hay nada que
saltar: si el instrumento falta, el **CLI** sale con 3 y el **test** falla.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import subprocess
import sys

import numpy as np
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts", "auditoria")
sys.path.insert(0, SCRIPTS)

import freeze_rules_evidence as G  # noqa: E402

CALIBRACION = os.path.join(ROOT, "src", "mia", "calibracion_banda.json")
INSTRUMENT = os.path.join(ROOT, "src", "mia", "instrumento_oof.npz")


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
    assert "python scripts/auditoria/p1_oof_cache.py" in texto
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
def test_el_gate_reproduce_la_banda_comprometida():
    """La banda publicada se verifica contra el instrumento, no contra un refit."""
    salida = io.StringIO()
    assert G.run(instrument=True, stream=salida) == 0
    texto = salida.getvalue()
    assert "pure OOF rows" in texto
    assert "frozen instrument" in texto
    # La tabla OOF y la cobertura se informan: no son contrato de este camino,
    # porque describen un refit que ningún artefacto del repositorio reproduce.
    assert "reported" in texto
    assert "OOF coverage (corrected point)" in texto


def test_el_gate_detecta_drift(tmp_path):
    """Un recuento movido una sola fila sale con código 4, no con verde."""
    malo = {"pure_rows": 14914}
    salida = io.StringIO()
    assert G.run(malo, instrument=True, stream=salida) == 4
    texto = salida.getvalue()
    assert "pure_rows" in texto
    assert "14914" in texto and "14915" in texto
    assert "pure OOF rows" in texto


def test_la_escritura_es_idempotente(tmp_path):
    """`--write` sobre un árbol que cuadra no toca el JSON congelado."""
    antes = _sha256(CALIBRACION)
    salida = io.StringIO()
    assert G.run(G.INSTRUMENT_EXPECTED, write=True, instrument=True,
                 stream=salida) == 0
    assert "no change" in salida.getvalue()
    assert _sha256(CALIBRACION) == antes


# ------------------------------------------- instrumento congelado (versionado)
def test_el_instrumento_congelado_reproduce_la_banda():
    """La banda publicada sale de un npz versionado, no de un joblib ignorado."""
    assert os.path.exists(INSTRUMENT), "falta src/mia/instrumento_oof.npz"
    with np.load(INSTRUMENT) as data:
        units = np.asarray(data["units"], dtype=float)
        cycles = np.asarray(data["cycles"], dtype=float)
        y_true = np.asarray(data["y"], dtype=float)
        pred = np.asarray(data["pred_ema"], dtype=float)

    assert len(y_true) == 14915
    assert sorted({int(u) for u in np.unique(units)}) == [2, 5, 10, 18, 20]

    positions = G._ordered_positions(units, cycles)
    corrected = G._per_unit(positions, pred, G.REGLAS.pava_causal_no_creciente)
    fit = G.CONFORMAL.fit_conformal(
        y_true, corrected, target=0.90,
        edges=G.CONFORMAL.DEFAULT_EDGES, min_rows=100,
    )

    with open(CALIBRACION, encoding="utf-8") as fh:
        committed = json.load(fh)

    assert fit["n_calibration"] == committed["n_calibration"] == 14915
    assert [b["n"] for b in fit["bins"]] == [b["n"] for b in committed["bins"]]
    for have, want in zip(committed["bins"], fit["bins"]):
        assert (have["q_low"], have["q_high"]) == (want["q_low"], want["q_high"])
    assert fit["global_quantiles"] == committed["global_quantiles"]


def test_el_gate_verifica_la_banda_sin_la_cache_oof():
    """`--instrument` cierra en 0 sin `_p1_oof_cache.npz`: la banda queda verificada."""
    salida = io.StringIO()
    assert G.run(instrument=True, stream=salida) == 0
    texto = salida.getvalue()
    assert "pure OOF rows" in texto
    assert "frozen instrument" in texto


def test_el_instrumento_congelado_esta_versionado():
    """Si el npz se ignora, la evidencia no viaja con el repositorio."""
    if subprocess.run(["git", "--version"], capture_output=True).returncode != 0:
        pytest.skip("git not available")
    ignorado = subprocess.run(["git", "check-ignore", "-q", INSTRUMENT],
                              cwd=ROOT, capture_output=True)
    assert ignorado.returncode == 1, "instrumento_oof.npz está en .gitignore"
