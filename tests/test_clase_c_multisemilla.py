"""Contrato de la evidencia multisemilla del bundle C.

Lo que se fija aquí es la *agregación* (media ± desviación, coste frente al
campeón histórico) y la coherencia entre el manifiesto instalado y el CSV que
leen los cuadernos. No entrena nada: la suite tiene que correr sin GPU, sin
TensorFlow largo y sin dataset pesado.
"""

from __future__ import annotations

import json
import os

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "models", "ds02_manifest.json")
CSV = os.path.join(ROOT, "resultados", "comparativa_c_multisemilla.csv")


def _fila(seed: int, rmse: float, nasa: float) -> dict:
    return {"seed": seed, "RMSE": rmse, "MAE": 3.2, "R2": 0.947, "NASA_Score": nasa}


def test_agregar_semillas_media_y_desviacion():
    from src.clase.evaluar_c_multisemilla import agregar_semillas

    r = agregar_semillas([_fila(42, 4.338, 2336.2),
                          _fila(7, 4.338, 2350.9),
                          _fila(123, 4.266, 2330.3)])

    assert r["n_semillas"] == 3
    assert r["seeds"] == [42, 7, 123]
    assert r["rmse_media"] == pytest.approx(4.314, abs=1e-3)
    # ddof=1: la desviación que se publica es la muestral, no la poblacional.
    assert r["rmse_std"] == pytest.approx(0.0416, abs=1e-3)
    assert r["nasa_media"] == pytest.approx(2339.1, abs=0.1)


def test_agregar_semillas_exige_al_menos_una_fila():
    from src.clase.evaluar_c_multisemilla import agregar_semillas

    with pytest.raises(ValueError):
        agregar_semillas([])


def test_manifest_instalado_cumple_el_contrato_ds02():
    """El bundle desplegado es el C, pero declara la forma DS02."""
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)

    assert manifest["dataset"] == "DS02"
    assert "adaptada" in manifest["dataset_variant"]
    assert manifest["code_version"] == "clase-bundle-C"
    assert manifest["model_shape"]["bilstm_params"] == 154253
    assert manifest["unit_partition"]["test"] == [11, 14, 15]
    assert manifest["metrics"]["reference_row"]["RMSE"] > 0
    # La lectura macro viaja con el manifiesto: el reparto del error por motor
    # tiene que ser auditable desde el artefacto, no solo desde un documento.
    assert manifest["metrics"]["macro_rmse"] > manifest["metrics"]["reference_row"]["RMSE"]


def test_csv_multisemilla_coincide_con_el_manifest_si_existe():
    """Si el CSV está generado, su fila 42 tiene que ser la del manifiesto."""
    if not os.path.exists(CSV):
        pytest.skip("CSV multisemilla no generado: ejecuta python -m src.clase.evaluar_c_multisemilla")

    import pandas as pd

    with open(MANIFEST, encoding="utf-8") as fh:
        ref = json.load(fh)["metrics"]["reference_row"]
    tabla = pd.read_csv(CSV)
    fila = tabla.loc[tabla["seed"] == 42].iloc[0]
    assert fila["RMSE"] == pytest.approx(ref["RMSE"], abs=1e-9)
    assert fila["NASA_Score"] == pytest.approx(ref["NASA_Score"], abs=1e-6)
    assert len(tabla) == 3
