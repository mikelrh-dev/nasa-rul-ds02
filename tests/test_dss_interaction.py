"""Interaction tests: the two star buttons must not break the app.

The logic behind C1 (alta) and C2 (demo) was correct and covered by
`tests/test_ui_alta.py`. What was missing is a test that *presses* the button.
Both broke with `StreamlitWidgetAlreadyInstantiatedError` because the handler
wrote to a session-state key owned by an already-instantiated widget. The 152
green tests never saw it: `AppTest` renders the page but clicks nothing.

Run:  python -m pytest tests/test_dss_interaction.py -v
"""
from __future__ import annotations

import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

import ui_data_loader as L  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build_ui_cache.py`",
)

DASHBOARD = os.path.join(APP, "dashboard_ds02.py")
MATRICULA = "EC-PROBE-1"


def _app():
    from streamlit.testing.v1 import AppTest

    return AppTest.from_file(DASHBOARD, default_timeout=180)


def _click(app, label: str) -> bool:
    for button in app.button:
        if label.lower() in (button.proto.label or "").lower():
            button.click().run()
            return True
    return False


def _opciones_selector(app) -> list[str]:
    return [opcion.content for opcion in _selector_unidad(app).proto.options]


def _selector_unidad(app):
    """The sidebar's unit picker (the first `segmented_control` is the data mode)."""
    for control in app.segmented_control:
        if (control.proto.label or "").startswith("Unidad de test"):
            return control
    pytest.fail("no está el selector de unidad en la barra lateral")


@needs_cache
def test_incorporar_unidad_no_rompe_la_app():
    """C1: alta individual. Pressing it must not raise, and the unit must appear."""
    app = _app()
    app.run()
    assert not app.exception

    for field in app.text_input:
        if (field.proto.label or "").lower().startswith("matrícula"):
            field.set_value(MATRICULA)
            break
    else:
        pytest.fail("el formulario de alta no tiene campo de matrícula")

    assert _click(app, "Incorporar unidad"), "el botón de alta no está en la página"
    assert not app.exception, app.exception

    opciones = _opciones_selector(app)
    assert any(MATRICULA in opcion for opcion in opciones), opciones


@needs_cache
def test_cargar_escenario_demo_no_rompe_la_app():
    """C2: demo. Pressing it must load 30/25, cycle 29 and unit 14."""
    app = _app()
    app.run()
    assert not app.exception

    assert _click(app, "Cargar escenario de demo"), "el botón de demo no está"
    assert not app.exception, app.exception

    assert _selector_unidad(app).value == 14, _selector_unidad(app).value
    assert app.slider[0].value == 29, app.slider[0].value


# ------------------------------------------------------------------ fase 1
def _tarjetas_del_muro(app) -> list:
    return [b for b in app.button if (b.proto.label or "").strip() == "Ver gemelo"]


@needs_cache
def test_el_muro_tiene_una_tarjeta_por_motor():
    """El muro es una tarjeta por unidad, y cada una se puede pulsar."""
    app = _app()
    app.run()
    assert not app.exception, app.exception

    tarjetas = _tarjetas_del_muro(app)
    unidades = sorted(int(u) for u in L.get_windows()["unit"].unique())
    assert len(tarjetas) == len(unidades), [b.key for b in tarjetas]
    assert {b.key for b in tarjetas} == {f"muro_gemelo_{u}" for u in unidades}


@needs_cache
def test_pulsar_una_tarjeta_cambia_la_unidad_seleccionada():
    """El botón de la tarjeta selecciona el motor en la barra lateral."""
    app = _app()
    app.run()
    assert _selector_unidad(app).value == 11

    for boton in _tarjetas_del_muro(app):
        if boton.key == "muro_gemelo_14":
            boton.click().run()
            break
    else:
        pytest.fail("no está la tarjeta del motor 14")

    assert not app.exception, app.exception
    assert _selector_unidad(app).value == 14


@needs_cache
def test_el_onboarding_carga_el_archetype_critico():
    """El onboarding es el estado inicial del tablero: 1 clic y el escenario está cargado."""
    app = _app()
    app.run()
    assert not app.exception, app.exception

    for boton in app.button:
        if boton.key == "arquetipo_Fin de vida / crítico":
            boton.click().run()
            break
    else:
        pytest.fail("no está el archetype crítico del onboarding")

    assert not app.exception, app.exception
    assert _selector_unidad(app).value == 14
    assert app.slider[0].value == 29


# ------------------------------------------------------------------ fase 3
def _texto(app) -> str:
    partes = [m.value for m in app.markdown]
    partes += [c.value for c in app.caption]
    partes += [s.value for s in app.subheader]
    partes += [f"{m.label} {m.value}" for m in app.metric]
    return "\n".join(partes)


@needs_cache
def test_el_gemelo_consolida_la_decision_y_su_regla():
    """El gemelo responde «¿por qué está así?» sin cambiar de pestaña."""
    app = _app()
    app.run()
    assert not app.exception, app.exception

    texto = _texto(app)
    assert "El gemelo" in texto
    assert "Regla que decide" in texto
    # La traza de la pasada A debe aparecer con sus reglas, no solo el estado.
    assert "mia.motor" in texto


@needs_cache
def test_el_gauge_del_gemelo_tiene_nombre_accesible():
    app = _app()
    app.run()
    assert not app.exception, app.exception

    alts = [c.proto.alt or "" for c in app.get("plotly_chart")]
    assert any("Gauge de RUL" in a for a in alts), alts


@needs_cache
def test_el_gemelo_incluye_ciclo_de_vida_y_orden_de_trabajo():
    app = _app()
    app.run()
    assert not app.exception, app.exception

    texto = _texto(app)
    assert "Ciclo de vida del hangar" in texto
    assert "Radiografía de sensores" in texto


# ------------------------------------------------------------------ fase 4
def _cuenta_hangar(app) -> int:
    kpi = next(m for m in app.metric if "hangar" in m.label.lower())
    return int(kpi.value.split("/")[0].strip())


def _number_input(app, fragmento: str):
    return next(n for n in app.number_input if fragmento in (n.proto.label or ""))


@needs_cache
def test_el_taller_es_una_sala_con_explicacion():
    """Sala 3: los controles de política viven aquí, con lo que hacen y lo que no."""
    app = _app()
    app.run()
    assert not app.exception, app.exception

    texto = _texto(app)
    assert "El taller" in texto
    assert "qué pasa si cambio la política" in texto.lower()


@needs_cache
def test_mover_un_umbral_cambia_la_cola():
    """El efecto del taller es visible: aflojar el umbral de hangar deriva menos."""
    app = _app()
    app.run()
    app.slider[0].set_value(29).run()
    assert not app.exception, app.exception
    antes = _cuenta_hangar(app)
    assert antes > 0

    _number_input(app, "Hangar si L_inf").set_value(5.0).run()
    assert not app.exception, app.exception
    assert _cuenta_hangar(app) < antes


@needs_cache
def test_la_decision_no_cambia_de_agregacion():
    """Mover los umbrales no cambia la agregación: la decisión sigue usando L_inf."""
    app = _app()
    app.run()
    app.slider[0].set_value(29).run()
    assert not app.exception, app.exception

    snap = L.fleet_snapshot(L.get_windows(), 29, 30.0, 25.0)
    fila = snap[snap["unit"] == 14].iloc[0]
    assert fila["state"] == L.AOG
    assert float(fila["pred"]) >= 25.0, (
        "la predicción puntual está por encima del umbral y aun así se deriva")

    assert "límite inferior" in _texto(app).lower()
