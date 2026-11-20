"""Tests de la superficie de decisión DS02.

Se comprueban cuatro afirmaciones y cada una corresponde a un bloqueo
detectado en la auditoría del diseño original de la UI:

1. los umbrales de triaje se comportan (el verde es alcanzable, AOG es conservador);
2. la caché contiene lo que predice el bundle congelado (recuentos, invariante de banda);
3. la orden de trabajo solo incluye unidades fundamentadas y lleva procedencia;
4. ningún artefacto FD001 se filtra a una superficie DS02.

Ejecutar:  python -m pytest tests -q
"""
from __future__ import annotations

import copy
import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, ROOT)

from app.lib import ui_data_loader as L  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build/build_ui_cache.py`",
)


# ------------------------------------------------------------------- policy
@pytest.mark.parametrize(
    "lower, expected",
    [
        (35.7, L.AIRWORTHY),
        (30.0, L.AIRWORTHY),
        (25.0, L.AIRWORTHY),
        (24.9, L.PREVENTIVE),
        (20.0, L.PREVENTIVE),
        (19.9, L.AOG),
        (-3.0, L.AOG),
    ],
)
def test_triage_states_follow_the_lower_bound(lower, expected):
    assert L.classify(lower) == expected


def test_airworthy_state_is_reachable_on_this_band():
    """La regla `L_inf >= 50` del diseño original nunca podía ponerse en verde."""
    assert L.classify(36.0) == L.AIRWORTHY
    assert L.classify(50.0) == L.AIRWORTHY


def test_thresholds_must_be_ordered():
    with pytest.raises(ValueError, match="aog < airworthy"):
        L.classify(30.0, airworthy=25.0, aog=30.0)
    with pytest.raises(ValueError, match="umbral inválido"):
        L.thresholds_from(airworthy=20.0, aog=25.0)


# -------------------------------------------------------------------- cache
@needs_cache
def test_cache_counts_match_the_evaluation_contract():
    windows = L.get_windows()
    counts = windows.groupby("unit").size().to_dict()
    assert len(windows) == 6196
    assert counts == {11: 3293, 14: 760, 15: 2143}


@needs_cache
def test_band_contains_its_point_estimate_and_is_non_negative():
    windows = L.get_windows()
    assert (windows["lower"] <= windows["pred"]).all()
    assert (windows["pred"] <= windows["upper"]).all()
    assert (windows["lower"] >= 0.0).all()
    assert np.isfinite(windows[["y_true", "pred", "lower", "upper"]].to_numpy()).all()


@needs_cache
def test_first_scored_cycle_is_airworthy_for_every_unit():
    windows = L.get_windows()
    for unit in (11, 14, 15):
        cycle = int(windows.loc[windows["unit"] == unit, "cycle"].min())
        snapshot = L.fleet_snapshot(windows, cycle)
        row = snapshot[snapshot["unit"] == unit].iloc[0]
        assert row["state"] == L.AIRWORTHY, (unit, cycle, row["lower"])


@needs_cache
def test_units_are_clamped_not_extrapolated():
    windows = L.get_windows()
    snapshot = L.fleet_snapshot(windows, 76)
    row = snapshot[snapshot["unit"] == 11].iloc[0]
    assert int(row["scored_cycle"]) == 59
    assert bool(row["clamped"]) is True
    row14 = snapshot[snapshot["unit"] == 14].iloc[0]
    assert int(row14["scored_cycle"]) == 76
    assert bool(row14["clamped"]) is False


@needs_cache
def test_engine_without_flight_is_not_given_a_state():
    windows = L.get_windows()
    snapshot = L.fleet_snapshot(windows, 1)
    row = snapshot[snapshot["unit"] == 14].iloc[0]
    assert row["state"] == L.NO_DATA
    assert row["state"] not in (L.AIRWORTHY, L.AOG)


@needs_cache
def test_metrics_are_recomputed_from_the_cache():
    windows = L.get_windows()
    live = L.global_metrics(windows)
    y = windows["y_true"].to_numpy()
    p = windows["pred"].to_numpy()
    assert live["rmse"] == pytest.approx(float(np.sqrt(np.mean((p - y) ** 2))), abs=1e-9)
    assert live["mae"] == pytest.approx(float(np.mean(np.abs(p - y))), abs=1e-9)
    per_unit = L.per_unit_metrics(windows)
    assert live["macro_rmse"] == pytest.approx(float(per_unit["rmse"].mean()), abs=1e-9)
    # La caché puntúa el bundle desplegado: debe reproducir el registro del manifiesto.
    recorded = L.get_manifest()["macro_rmse"]["per_unit_rmse"]
    for unit in (11, 14, 15):
        assert live["macro_rmse"] > 0
        assert per_unit.loc[per_unit["unit"] == unit, "rmse"].iloc[0] == pytest.approx(
            recorded[str(float(unit))], abs=5e-3
        )


@needs_cache
def test_mae_by_band_covers_every_row_once():
    windows = L.get_windows()
    bands = L.mae_by_band(windows)
    assert bands["windows"].sum() == len(windows)
    # Una banda sin filas puede no tener MAE; una banda con filas, no.
    populated = bands[bands["windows"] > 0]
    assert not populated.empty
    assert populated["mae"].notna().all()
    assert (populated["mae"] >= 0).all()


@needs_cache
def test_channels_use_the_dataset_names():
    rows = L.get_rows()
    for name in ("T24", "T30", "T48", "T50", "P15", "P2", "P21", "P24",
                 "Ps30", "P40", "P50", "Nf", "Nc", "Wf", "alt", "Mach", "TRA", "T2"):
        assert name in rows.columns, name
    assert not any(col.startswith("s") and col[1:].isdigit() for col in rows.columns)


# --------------------------------------------------------------- work order
@needs_cache
def test_work_order_lists_only_grounded_units():
    windows = L.get_windows()
    provenance = L.get_provenance()
    snapshot = L.fleet_snapshot(windows, 40)
    order = L.work_order(snapshot, provenance)
    blocked = set(snapshot.loc[snapshot["state"] == L.AOG, "unit"].astype(int))
    assert blocked, "the fixture cycle should ground at least one unit"
    assert {entry["unidad"] for entry in order["unidades"]} == blocked
    for entry in order["unidades"]:
        assert entry["motivo"]
        assert entry["limite_inferior"] < 25.0


@needs_cache
def test_work_order_carries_provenance():
    windows = L.get_windows()
    provenance = L.get_provenance()
    order = L.work_order(L.fleet_snapshot(windows, 40), provenance, airworthy=32.0, aog=26.0)
    assert order["artefacto_sha256"] == provenance["artifact"]["ensemble_sha256"]
    assert order["umbrales"] == {
        "apto_si_limite_inferior_ge": 32.0,
        "hangar_si_limite_inferior_lt": 26.0,
    }
    assert json.dumps(order)  # serialisable


@needs_cache
def test_empty_work_order_is_still_a_valid_document():
    windows = L.get_windows()
    provenance = L.get_provenance()
    order = L.work_order(L.fleet_snapshot(windows, 1), provenance)
    assert order["unidades"] == []
    csv_text = L.work_order_csv(order)
    assert csv_text.strip().splitlines() == [
        "unidad,estado,regla,ciclo_simulado,ciclo_evaluado,rul_estimada,"
        "limite_inferior,limite_superior,rul_real,motivo,accion"
    ]


# --------------------------------------------------------- dataset isolation
def _ui_sources() -> list[str]:
    sources = []
    for name in (os.path.join("entrypoints", "dashboard_ds02.py"),
                 os.path.join("lib", "ui_data_loader.py")):
        with open(os.path.join(APP, name), encoding="utf-8") as fh:
            sources.append(fh.read())
    return sources


def test_no_fd001_artifact_is_referenced():
    joined = "\n".join(_ui_sources())
    assert "alarm_policy" not in joined
    assert "test_eval_ultima_ventana" not in joined


def test_ui_does_not_reimplement_the_model():
    joined = "\n".join(_ui_sources())
    for forbidden in ("tensorflow", "import keras", "joblib.load", "train_", "fit("):
        assert forbidden not in joined, forbidden


@needs_cache
def test_reading_the_ui_leaves_the_frozen_artifacts_untouched():
    """`models/` es de solo lectura: hashes antes y después de un pase completo de datos de la UI."""
    import hashlib

    watched = [
        os.path.join(ROOT, "models", name)
        for name in ("ensemble.joblib", "bilstm_ds02.keras", "scaler.joblib",
                     "ds02_manifest.json")
    ]

    def digest(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        return h.hexdigest()

    before = {path: digest(path) for path in watched}
    windows = L.get_windows()
    snapshot = L.fleet_snapshot(windows, 40)
    L.work_order(snapshot, L.get_provenance())
    L.get_manifest()
    after = {path: digest(path) for path in watched}
    assert before == after
    assert os.path.exists(L.MANIFEST_PATH) and L.MANIFEST_PATH.endswith("ds02_manifest.json")


# ------------------------------------------------- cache / artifact seal
def _sha256(path) -> str:
    import hashlib

    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


@needs_cache
def test_artifact_hash_check_is_quiet_when_the_seal_matches(monkeypatch):
    """La caché registrada contra el artefacto que hay en disco: coinciden."""
    monkeypatch.setattr(L, "ARTIFACT_PATH", os.path.join(ROOT, "models", "ensemble.joblib"))
    registrado = L.get_provenance()["artifact"]["ensemble_sha256"]
    assert _sha256(L.ARTIFACT_PATH) == registrado, (
        "la caché registrada no corresponde al artefacto de este repo"
    )

    informe = L.artifact_hash_check(L.get_provenance())
    assert informe["checked"] is True, informe
    assert informe["ok"] is True, informe
    assert informe["esperado"] == registrado, informe
    assert informe["leido"] == registrado, informe
    assert len(informe["leido"]) == 64, informe


def test_artifact_hash_check_names_the_mismatch(monkeypatch, tmp_path):
    """Un artefacto reentrenado sin reconstruir la caché se detecta y se nombra."""
    sello = tmp_path / "ensemble.joblib"
    sello.write_bytes(b"pesos reentrenados, no los de la cach\xe9")
    monkeypatch.setattr(L, "ARTIFACT_PATH", str(sello))

    registrado = L.get_provenance()["artifact"]["ensemble_sha256"]
    informe = L.artifact_hash_check(L.get_provenance())
    assert informe["checked"] is True, informe
    assert informe["ok"] is False, informe
    assert informe["esperado"] == registrado, informe
    assert informe["leido"] == _sha256(str(sello)), informe
    assert informe["leido"] != informe["esperado"], informe


def test_artifact_hash_check_degrades_to_not_checked(monkeypatch, tmp_path):
    """Sin artefacto no se comprueba nada: avisa, no tira el render."""
    ausente = tmp_path / "no_existe.joblib"
    monkeypatch.setattr(L, "ARTIFACT_PATH", str(ausente))

    informe = L.artifact_hash_check(L.get_provenance())
    assert informe["checked"] is False, informe
    assert informe["ok"] is False, informe
    assert informe["esperado"] == L.get_provenance()["artifact"]["ensemble_sha256"], informe
    assert informe["leido"] is None, informe

    # Manifest truncado (sin la clave) y procedencia inexistente: tampoco crashea.
    for roto in ({"source": {}}, {}, None):
        informe = L.artifact_hash_check(roto)
        assert informe["checked"] is False, (roto, informe)
        assert informe["ok"] is False, (roto, informe)


def test_artifact_hash_check_no_importa_tensorflow():
    """El sello se compara en el módulo ligero: importar Keras aqui seria un error."""
    import subprocess

    code = (
        "import sys; from app.lib import ui_data_loader; "
        "print('tensorflow' in sys.modules, 'keras' in sys.modules)"
    )
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip() == "False False"


# ------------------------------------------------------------------- render
@needs_cache
def test_app_renders_headless_without_exception():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"), default_timeout=120)
    app.run()
    assert not app.exception, app.exception
    assert "DS02" in app.title[0].value
    # Cuatro pestanas de tarea, no cinco de capas del modelo.
    assert len(app.tabs) == 4
    labels = [tab.label for tab in app.tabs]
    assert any("Flota" in label for label in labels)
    assert any("Motor" in label for label in labels)
    assert any("Casos nuevos" in label for label in labels)
    assert any("Auditoría" in label for label in labels)


@needs_cache
def test_every_chart_and_grid_has_an_accessible_name():
    """`alt=` es el nombre accesible: ningún gráfico ni tabla puede salir sin él."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"), default_timeout=120)
    app.run()
    assert not app.exception, app.exception
    charts = app.get("plotly_chart")
    grids = app.get("dataframe")
    assert len(charts) >= 6, f"lost a chart: {len(charts)}"
    assert len(grids) >= 7, f"lost a grid: {len(grids)}"
    for element in list(charts) + list(grids):
        assert element.proto.alt and element.proto.alt.strip(), element.proto


def test_theme_config_is_dark_and_parseable():
    """El acabado visual vive en config.toml, no en CSS inyectado."""
    import tomllib

    path = os.path.join(ROOT, ".streamlit", "config.toml")
    with open(path, "rb") as fh:
        config = tomllib.load(fh)
    theme = config["theme"]
    assert theme["base"] == "dark"
    assert theme["backgroundColor"].startswith("#")
    assert theme["textColor"].startswith("#")
    assert len(theme["chartSequentialColors"]) == 10
    assert len(theme["chartDivergingColors"]) == 10
    assert "font" in theme and "headingFont" in theme
    assert config["theme"]["sidebar"]["backgroundColor"] != theme["backgroundColor"]


def test_no_css_is_injected_into_the_app():
    joined = "\n".join(_ui_sources())
    assert "unsafe_allow_html" not in joined
    assert "<style" not in joined


@needs_cache
def test_the_cycle_slider_drives_the_grounded_kpi():
    """El simulador es interactivo: mover el reloj cambia el estado de la flota."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"), default_timeout=120)
    app.run()
    # Por etiqueta, no por índice: el reloj se movió a la barra lateral y el
    # índice 0 pasó a ser el slider del sandbox.
    _ciclo = next(s for s in app.slider if (s.label or "").startswith("Ciclo de vuelo"))
    _ciclo.set_value(40).run()
    assert not app.exception, app.exception

    expected = int((L.fleet_snapshot(L.get_windows(), 40)["state"] == L.AOG).sum())
    assert expected > 0, "cycle 40 should ground at least one unit"
    kpi = next(m for m in app.metric if "hangar" in m.label.lower())
    assert kpi.value.startswith(f"{expected} /")

    downloads = [
        widget for widget in app.get("download_button")
        if "orden" in widget.proto.label.lower()
    ]
    assert len(downloads) == 2, "a grounded fleet must offer the work order (JSON + PDF)"
    for widget in downloads:
        assert widget.proto.disabled is False


# ------------------------------------------- regresiones H1 / H3 / H6c
DASHBOARD_PATH = os.path.join(APP, "entrypoints", "dashboard_ds02.py")


def _app(ds02=DASHBOARD_PATH):
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(ds02, default_timeout=180)


@needs_cache
def test_auditar_hashes_no_rompe_sin_bilstm_sha256(monkeypatch):
    """H1: pulsar «Auditar hashes del artefacto» no puede tirar la pestaña.

    El manifiesto de procedencia no registra `bilstm_sha256` y el manifiesto del
    artefacto tampoco: el render debe avisar, no lanzar `TypeError`.
    """
    provenance = copy.deepcopy(L.get_provenance())
    (provenance.get("artifact") or {}).pop("bilstm_sha256", None)
    manifest = copy.deepcopy(L.get_manifest())
    (manifest.get("artifacts") or {}).pop("bilstm_sha256", None)
    monkeypatch.setattr(L, "get_provenance", lambda: provenance)
    monkeypatch.setattr(L, "get_manifest", lambda: manifest)

    app = _app()
    app.run()
    assert not app.exception, app.exception
    boton = next(b for b in app.button if b.key == "btn_audit_hashes")
    boton.click().run()
    assert not app.exception, app.exception
    # La pestaña sigue mostrando reglas e informe: no se trunca.
    subheaders = [s.value for s in app.subheader]
    assert "Vista de las 6 reglas de decisión" in subheaders
    assert "Informe de auditoría" in subheaders


@needs_cache
def test_auditar_hashes_toma_el_hash_del_manifiesto(monkeypatch):
    """TRIANGULATE H1: si procedencia no trae la clave, el manifiesto la aporta."""
    provenance = copy.deepcopy(L.get_provenance())
    (provenance.get("artifact") or {}).pop("bilstm_sha256", None)
    monkeypatch.setattr(L, "get_provenance", lambda: provenance)

    app = _app()
    app.run()
    assert not app.exception, app.exception
    boton = next(b for b in app.button if b.key == "btn_audit_hashes")
    boton.click().run()
    assert not app.exception, app.exception
    assert any("hash coincide con el manifest" in (s.value or "")
               for s in app.success), [s.value for s in app.success]


@needs_cache
def test_umbral_invertido_mantiene_la_app_operable():
    """H3: Hangar >= Apto muestra un error y restaura el preset, sin `st.stop()`."""
    app = _app()
    app.session_state["th_apto_Normal"] = 25.0
    app.session_state["th_aog_Normal"] = 30.0
    app.run()
    assert not app.exception, app.exception
    # La app sigue completa: barra lateral y cuatro pestañas para corregir.
    assert len(app.tabs) == 4
    assert len(app.sidebar) > 0
    assert any("umbral de hangar" in (e.value or "").lower() for e in app.error)
    # El preset queda restaurado en sesión y los spinbuttons nacen válidos.
    assert float(app.session_state.get("th_apto_Normal") or 0.0) == 25.0
    assert float(app.session_state.get("th_aog_Normal") or 0.0) == 20.0
    vals = {n.key: float(n.value) for n in app.number_input
            if (n.key or "").startswith("th_")}
    assert vals.get("th_apto_Normal") == 25.0
    assert vals.get("th_aog_Normal") == 20.0


@needs_cache
def test_umbral_valido_no_muestra_el_error_de_rango():
    """TRIANGULATE H3: un par ordenado (30/25) no dispara el error ni el stop."""
    app = _app()
    app.session_state["th_apto_Normal"] = 30.0
    app.session_state["th_aog_Normal"] = 25.0
    app.run()
    assert not app.exception, app.exception
    assert not any("umbral de hangar" in (e.value or "").lower() for e in app.error)
    assert len(app.tabs) == 4
    vals = {n.key: float(n.value) for n in app.number_input
            if (n.key or "").startswith("th_")}
    assert vals.get("th_apto_Normal") == 30.0
    assert vals.get("th_aog_Normal") == 25.0


def test_probar_n8n_huella_unica_por_pulsacion(monkeypatch):
    """H6c: el test del panel manda una huella distinta en cada pulsación."""
    from unittest import mock

    import src.n8n as N8N

    from app.lib import dashboard_helpers as DH

    enviados = []

    def _fake_enviar(decision, payload, *args, **kwargs):
        enviados.append(payload)
        return {"ok": True, "status": 200, "decision": decision}

    monkeypatch.setattr(N8N, "enviar_decision", _fake_enviar)
    with mock.patch.dict(os.environ, {}, clear=False):
        DH.probar_n8n()
        DH.probar_n8n()

    assert len(enviados) == 2
    huellas = [str(p["fingerprint"]) for p in enviados]
    assert all(huellas)
    assert len(set(huellas)) == 2, f"la huella debe ser única por pulsación: {huellas}"
    assert "test-panel" not in huellas
    for payload in enviados:
        assert payload["idempotency_key"] == payload["fingerprint"]
