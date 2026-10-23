"""Tests for incorporating N engines at once (`app/ui_batch.py`).

The batch is the one feature the plan says is missing: an operator brings N
engines, the app scores all of them and returns one triage row each. The claims
under test are the ones the plan calls verification:

* N blocks produce N rows;
* a block under 50 rows is rejected before the model is called;
* the engine cap is applied with a visible warning, not a silent failure;
* the batch never reports ground truth (the user brings the data, so there is
  none) — prediction and band only, and it says so.

Run:  python -m pytest tests/test_ui_batch.py -v
"""
from __future__ import annotations

import io
import os
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

import ui_data_loader as L  # noqa: E402
import ui_inference as INF  # noqa: E402
import ui_batch as B  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build_ui_cache.py`",
)

UMBRAL = {"apto": 30.0, "hangar": 25.0}


class _FakeUpload(io.BytesIO):
    """Exactly what `st.UploadedFile` is: a `BytesIO` with a `.name`."""

    def __init__(self, name: str, texto: str):
        super().__init__(texto.encode("utf-8"))
        self.name = name


def _bloque(unit: int, position: float, matricula: str) -> dict:
    tabla, _ = INF.example_window(unit, position)
    return {"tabla": tabla, "matricula": matricula, "fuente": "test"}


# --------------------------------------------------------------- splitting
@needs_cache
def test_bloques_de_csv_separan_por_unit_id():
    """One CSV, several engines: `unit_id` is what separates the blocks."""
    tabla, _ = INF.example_window()
    con_id = tabla.assign(unit_id=["MOTOR-A"] * 25 + ["MOTOR-B"] * 25)
    bloques = B.bloques_de_csv(con_id.to_csv(index=False))

    assert [b["matricula"] for b in bloques] == ["MOTOR-A", "MOTOR-B"]
    assert all(len(b["tabla"]) == 25 for b in bloques)
    assert "unit_id" not in bloques[0]["tabla"].columns
    assert list(bloques[0]["tabla"].columns) == INF.required_columns()


@needs_cache
def test_un_csv_sin_unit_id_se_rechaza_con_motivo():
    tabla, _ = INF.example_window()
    with pytest.raises(ValueError, match="unit_id"):
        B.bloques_de_csv(tabla.to_csv(index=False))


@needs_cache
def test_bloques_de_archivos_da_un_motor_por_archivo():
    tabla, _ = INF.example_window()
    csv = tabla.to_csv(index=False)
    bloques = B.bloques_de_archivos([
        _FakeUpload("motor-alpha.csv", csv),
        _FakeUpload("motor-beta.csv", csv),
    ])
    assert [b["matricula"] for b in bloques] == ["MOTOR-ALPHA", "MOTOR-BETA"]


# ----------------------------------------------------------------- preflight
@needs_cache
def test_un_bloque_corto_se_rechaza_antes_del_modelo():
    """A 20-row block cannot form a window: the validator says so, not the model."""
    tabla, _ = INF.example_window()
    aviso = B.validar_bloque({"tabla": tabla.head(20), "matricula": "CORTO",
                              "fuente": "test"})
    assert aviso["ok"] is False
    assert "al menos 50 filas" in aviso["error"]
    assert aviso["ventanas"] == 0


@needs_cache
def test_validar_bloque_reutiliza_el_validador_de_ui_inference():
    """One validator: the batch must not grow a second copy of the contract."""
    tabla, _ = INF.example_window()
    assert B.validar_bloque({"tabla": tabla, "matricula": "X", "fuente": "t"})["ok"] is True
    assert B.validar_bloque({"tabla": tabla, "matricula": "X", "fuente": "t"}) == INF.preflight(tabla)


# ----------------------------------------------------------------- scoring
@needs_cache
def test_n_bloques_producen_n_filas():
    """The feature: three engines in, three triage rows out."""
    bloques = [
        _bloque(15, 0.05, "BATCH-0"),
        _bloque(11, 0.36, "BATCH-1"),
        _bloque(14, 0.40, "BATCH-2"),
    ]
    resultado = B.puntuar_lote(bloques, UMBRAL, INF.get_ensemble())

    assert len(resultado) == 3
    assert list(resultado["matricula"]) == ["BATCH-0", "BATCH-1", "BATCH-2"]
    assert (resultado["lower"] <= resultado["pred"]).all()
    assert (resultado["pred"] <= resultado["upper"]).all()
    assert resultado["lower"].notna().all()
    assert resultado["estado"].isin(L.STATE_LABELS).all()


@needs_cache
def test_el_lote_no_muestra_ground_truth():
    """The user brings the data: there is no truth, so no RMSE/MAE is invented."""
    bloques = [_bloque(14, 0.40, "BATCH-0")]
    resultado = B.puntuar_lote(bloques, UMBRAL, INF.get_ensemble())

    assert list(resultado.columns) == B.COLUMNAS_TRIAJE
    for prohibida in ("rmse", "mae", "rul_real", "y_true", "error", "bias"):
        assert prohibida not in resultado.columns


@needs_cache
def test_resumen_lote_cuenta_por_estado():
    bloques = [_bloque(15, 0.05, "LOTE-A"), _bloque(14, 0.40, "LOTE-B")]
    resultado = B.puntuar_lote(bloques, UMBRAL, INF.get_ensemble())
    resumen = B.resumen_lote(resultado)

    assert resumen["total"] == 2
    assert sum(resumen["por_estado"].values()) == 2
    assert resumen["por_estado"][L.AOG] == 1  # el crítico entra en hangar
    assert resumen["por_estado"][L.AIRWORTHY] == 1


# -------------------------------------------------------------------- cap
def test_el_tope_se_aplica_con_aviso():
    assert B.MAX_MOTORES_LOTE == 25
    assert B.excede_limite(B.MAX_MOTORES_LOTE) is False
    assert B.excede_limite(B.MAX_MOTORES_LOTE + 1) is True
    assert B.excede_limite(250) is True


# --------------------------------------------------------------------- UI
@needs_cache
def test_la_sala_de_incorporacion_ofrece_el_lote():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=180)
    app.run()
    assert not app.exception, app.exception

    uploads = [u for u in app.get("file_uploader")
               if "motores" in (u.proto.label or "").lower()]
    assert len(uploads) == 1, "la sala de incorporación no admite CSV de lote"
    assert "25" in uploads[0].proto.label, uploads[0].proto.label
    texto = "\n".join(c.value for c in app.caption) + "\n".join(m.value for m in app.markdown)
    assert "ground truth" in texto.lower(), "el lote debe declarar que no hay verdad"
