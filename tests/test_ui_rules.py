"""Tests del puente `app/ui_rules.py` entre la caché y la capa de reglas.

Tres cosas han de sostenerse:

1. la corrección no inventa ni pierde ventanas y deja la lectura cruda a la vista;
2. el punto corregido es el extremo del ajuste isotónico causal por unidad y la
   banda sigue conteniéndolo;
3. el tablero sigue renderizando con la corrección activada, arranca con el
   interruptor apagado y no describe la corrección como monotonicidad estricta;
4. la pasada de decisión la firma src.mia.motor (R1/R7/R8/R9), no una
   reclasificación paralela, y el SHA-256 completo se muestra en la UI.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import os
import re
import sys
import unicodedata

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)
sys.path.insert(0, ROOT)

import ui_data_loader as L  # noqa: E402
import ui_rules as UR  # noqa: E402
from src.mia import reglas as R  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build_ui_cache.py`",
)


@needs_cache
def test_la_correccion_conserva_filas_y_deja_la_lectura_cruda():
    crudo = L.get_windows()
    corregido = UR.corregir_ventanas(crudo)
    assert len(corregido) == len(crudo)
    for columna in ("pred_enviada", "lower_enviada", "upper_enviada", "corregida"):
        assert columna in corregido.columns
    assert bool(corregido["corregida"].all())


@needs_cache
def test_el_punto_corregido_es_el_ajuste_isotonico_causal():
    """El punto corregido es el extremo del ajuste isotonico del prefijo."""
    crudo = L.get_windows()
    corregido = UR.corregir_ventanas(crudo)
    for unit in crudo["unit"].unique():
        sub = crudo[crudo["unit"] == unit]
        orden = np.lexsort((sub["start_index"].to_numpy(),
                            sub["cycle"].to_numpy()))
        serie = sub["pred"].to_numpy()[orden]
        esperado = R.pava_causal_no_creciente(serie)
        posiciones = sub.index.to_numpy()[orden]
        np.testing.assert_allclose(corregido.loc[posiciones, "pred"].to_numpy(),
                                   esperado)


@needs_cache
def test_la_lectura_cruda_sigue_siendo_la_envolvente_monotono():
    """La monotonía estricta de la corrección es la de la lectura cruda."""
    corregido = UR.corregir_ventanas(L.get_windows())
    for unit in corregido["unit"].unique():
        frame = corregido[corregido["unit"] == unit]
        orden = np.lexsort((frame["start_index"].to_numpy(), frame["cycle"].to_numpy()))
        serie = frame["pred"].to_numpy()[orden]
        envolvente = np.minimum.accumulate(serie)
        cruda = frame["pred_enviada"].to_numpy()[orden]
        np.testing.assert_allclose(envolvente, np.minimum.accumulate(cruda))


@needs_cache
def test_la_banda_corregida_contiene_al_punto():
    corregido = UR.corregir_ventanas(L.get_windows())
    assert (corregido["lower"] <= corregido["pred"]).all()
    assert (corregido["pred"] <= corregido["upper"]).all()
    assert (corregido["lower"] >= 0.0).all()


@needs_cache
def test_el_resumen_informa_lo_movido():
    crudo = L.get_windows()
    corregido = UR.corregir_ventanas(crudo)
    resumen = UR.resumen_correccion(crudo, corregido)
    assert resumen["ventanas"] == len(crudo)
    assert resumen["ventanas_corregidas"] >= 0
    assert resumen["ventanas_corregidas"] <= len(crudo)
    assert 0.0 <= resumen["porcentaje"] <= 100.0


@needs_cache
def test_el_tablero_rendea_con_la_correccion_activada():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=180)
    app.run()
    assert not app.exception, app.exception
    assert app.toggle, "el interruptor de corrección tiene que existir"
    app.toggle[0].set_value(True).run()
    assert not app.exception, app.exception
    # Cuatro pestanas de tarea (Flota, Motor, Casos nuevos, Auditoría).
    assert len(app.tabs) == 4


# ------------------------------------------- garantías de superficie (3.1)
BANNED = (
    "monotonia estricta",
    "estrictamente monoton",
    "serie monotona",
    "serie no creciente",
    "regla de monotonia",
    "R2b_MONOTONIA",
    "R2b_MONOTONICO",
)
NEGADORES = ("no", "nunca", "ni")


def _plano(texto: str) -> str:
    """Minúsculas, sin tildes y con los espacios colapsados."""
    sin_tildes = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(c for c in sin_tildes if not unicodedata.combining(c))
    return " ".join(sin_tildes.casefold().split())


def _infracciones(texto: str) -> list[str]:
    """Formulaciones prohibidas, salvo que la misma frase las niegue."""
    hallazgos = []
    for frase in re.split(r"(?<=[.;:!?])\s+|\n+", texto):
        plano = _plano(frase)
        if not plano:
            continue
        palabras = set(re.findall(r"[a-z0-9_]+", plano))
        for prohibida in BANNED:
            if _plano(prohibida) in plano and not palabras & set(NEGADORES):
                hallazgos.append(f"{prohibida!r} en: {frase.strip()}")
    return hallazgos


def test_la_copia_no_dice_monotonia_estricta():
    """Los textos de la app y las seis frases vivas no sobreafirman."""
    for nombre in ("dashboard_ds02.py", "ui_rules.py"):
        with open(os.path.join(APP, nombre), encoding="utf-8") as fh:
            assert not _infracciones(fh.read()), nombre

    for nombre, _condicion, _efecto, _prioridad, porque in (
            R.REGLAS_CORRECCION + R.REGLAS_DECISION):
        assert not _infracciones(nombre), nombre
        assert not _infracciones(porque), porque

    # La frase que sí debe aparecer es la correcta.
    assert "isotonico" in _plano(R.REGLAS_CORRECCION[0][4])


def _conformal():
    """Carga `ds02_rul.conformal` sin ejecutar el `__init__` (importa Keras)."""
    import types

    if "ds02_rul" not in sys.modules:
        paquete = types.ModuleType("ds02_rul")
        paquete.__path__ = [os.path.join(ROOT, "src", "ds02_rul")]
        sys.modules["ds02_rul"] = paquete
    from ds02_rul import conformal

    return conformal


@needs_cache
def test_la_cobertura_en_test_es_total():
    """Sobre las 6 196 ventanas corregidas, la verdad cae dentro de la banda."""
    corregido = UR.corregir_ventanas(L.get_windows())
    assert len(corregido) == 6196
    cobertura = _conformal().empirical_coverage(
        corregido["y_true"].to_numpy(),
        corregido["lower"].to_numpy(),
        corregido["upper"].to_numpy(),
    )
    assert cobertura == 1.0


@needs_cache
def test_el_interruptor_arranca_apagado():
    """Una sesión nueva muestra la lectura cruda, sin tocar el interruptor."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=180)
    app.run()
    assert not app.exception, app.exception
    assert app.toggle, "el interruptor de corrección tiene que existir"
    assert app.toggle[0].value is False
    # Cuatro pestanas de tarea (Flota, Motor, Casos nuevos, Auditoría).
    assert len(app.tabs) == 4


# ------------------------------------------------- pasada A en la interfaz
def test_la_pasada_a_viene_del_motor_de_reglas():
    """R7/R8/R9 y la prioridad de R1 se resuelven en src.mia.motor."""
    frame = pd.DataFrame({
        "unit": [11, 11, 14],
        "cycle": [1, 2, 1],
        "pred": [40.0, 20.0, 31.0],
        "lower": [35.0, 18.0, 25.5],
        "upper": [45.0, 30.0, 40.0],
    })
    umbrales = {"apto": 30.0, "hangar": 25.0}
    decidido = UR.decidir_ventanas(frame, umbrales)
    assert decidido["decision"].tolist() == [L.AIRWORTHY, L.AOG, L.PREVENTIVE]
    assert decidido["regla_decision"].tolist() == [
        "R7_APTO", "R9_HANGAR", "R8_INSPECCION"
    ]
    assert "R9_HANGAR" in decidido.loc[1, "motivo_decision"]

    con_alerta = UR.decidir_ventanas(
        frame, umbrales, alertas=[["canal fuera de rango"], [], []],
    )
    assert con_alerta.loc[0, "decision"] == R.SIN_DECISION
    assert "R1_SEGURIDAD" in con_alerta.loc[0, "regla_decision"]


def test_el_estado_de_flota_sale_de_la_pasada_a():
    """El snapshot toma estado y regla del motor cuando el frame los trae."""
    frame = pd.DataFrame({
        "unit": [11, 11, 14],
        "cycle": [1, 2, 1],
        "pred": [40.0, 20.0, 31.0],
        "lower": [35.0, 18.0, 25.5],
        "upper": [45.0, 30.0, 40.0],
        "y_true": [41.0, 22.0, 30.0],
        "start_index": [0, 0, 0],
    })
    decidido = UR.decidir_ventanas(frame, {"apto": 30.0, "hangar": 25.0})
    snapshot = L.fleet_snapshot(decidido, 2)
    u11 = snapshot[snapshot["unit"] == 11].iloc[0]
    u14 = snapshot[snapshot["unit"] == 14].iloc[0]
    assert (u11["state"], u11["rule"]) == (L.AOG, "R9_HANGAR")
    assert (u14["state"], u14["rule"]) == (L.PREVENTIVE, "R8_INSPECCION")


@needs_cache
def test_la_ui_muestra_el_sha_completo():
    """El SHA-256 se muestra entero y etiquetado, no un prefijo suelto."""
    from streamlit.testing.v1 import AppTest

    sha = L.get_provenance()["artifact"]["ensemble_sha256"]
    assert len(sha) == 64
    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=180)
    app.run()
    assert not app.exception, app.exception
    codigos = [(element.value or "") for element in app.get("code")]
    assert any(sha in texto for texto in codigos), codigos
    # `st.badge` se expone como markdown con la sintaxis `:color-badge[...]`.
    markdowns = [(element.value or "") for element in app.markdown]
    assert any("SHA-256" in texto and sha[:8] in texto for texto in markdowns), markdowns


@needs_cache
def test_el_tablero_sigue_entregando_las_mismas_metricas_crudas():
    """Con el interruptor apagado, el contrato congelado se reproduce igual."""
    crudo = L.get_windows()
    live = L.global_metrics(crudo)
    recorded = L.get_manifest()["macro_rmse"]["per_unit_rmse"]
    for unit in (11, 14, 15):
        assert live["macro_rmse"] > 0
        assert L.per_unit_metrics(crudo).loc[
            L.per_unit_metrics(crudo)["unit"] == unit, "rmse"
        ].iloc[0] == pytest.approx(recorded[str(float(unit))], abs=5e-3)
