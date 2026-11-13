"""Interaction tests: the two star buttons must not break the app.

The logic behind C1 (alta) was correct and covered by
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
sys.path.insert(0, ROOT)

from app.lib import ui_data_loader as L  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build/build_ui_cache.py`",
)

DASHBOARD = os.path.join(APP, "entrypoints", "dashboard_ds02.py")


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


def _matricula_auto(app) -> str:
    """La matrícula es una etiqueta auto-generada (MTTT<unidad>), no un input libre.

    El campo sigue en el formulario para que el operador vea con qué nombre va a
    aparecer el motor, pero es de solo lectura: se deriva de la unidad elegida.
    """
    for field in app.text_input:
        if (field.proto.label or "").lower().startswith("matrícula"):
            return field.value
    pytest.fail("el formulario de alta no tiene campo de matrícula")


def _slider_ciclo(app):
    """El reloj de flota, por su etiqueta.

    No por índice: el reloj vive ahora en la barra lateral y el índice 0 pasó a
    ser el slider del sandbox, que se renderiza antes en el árbol de AppTest.
    """
    return next(s for s in app.slider if (s.label or "").startswith("Ciclo de vuelo"))


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

    matricula = _matricula_auto(app)

    assert _click(app, "Incorporar unidad"), "el botón de alta no está en la página"
    assert not app.exception, app.exception

    opciones = _opciones_selector(app)
    assert any(matricula in opcion for opcion in opciones), opciones


@needs_cache
def test_el_alta_crea_el_gemelo_y_el_motor_sobrevive_un_recargo():
    """El alta con unidad y ciclo libres crea su gemelo y persiste.

    Antes el alta vivia solo en `session_state` y desaparecia al recargar: el
    motor se perdia y el usuario creia haber hecho algo mal. Y no creaba gemelo,
    asi que no aparecia en «Gemelos registrados».
    """
    app = _app()
    app.run()
    assert not app.exception

    matricula = _matricula_auto(app)

    assert _click(app, "Incorporar unidad"), "el botón de alta no está en la página"
    assert not app.exception, app.exception

    gemelos = app.session_state["twins"]
    assert matricula in gemelos, gemelos
    assert gemelos[matricula]["serie"], "el gemelo del alta no tiene serie guardada"

    # El gemelo vive en el registro persistido, no solo en la sesion.
    assert matricula in app.session_state["altas"], app.session_state["altas"]


@needs_cache
def test_un_ciclo_sin_ventanas_se_rechaza_sin_romper_la_app():
    """Pedir un ciclo que la unidad no tiene muestra error, no un fallo.

    El slider usa el minimo global (1, de U11), asi que para U14 —que empieza
    en el ciclo 3— se puede pedir el 1 y caer en el rechazo.
    """
    app = _app()
    app.run()
    assert not app.exception

    # El selector de unidad base guarda el int como valor (el format_func solo
    # cambia como se muestra), asi que se elige por int.
    for control in app.selectbox:
        if (control.proto.label or "").startswith("Unidad base"):
            control.set_value(14).run()
            break
    else:
        pytest.fail("no está el selector de unidad base del alta")

    # Ciclo 1: la U14 empieza en el 3, asi que no tiene ventanas.
    for campo in app.number_input:
        if (campo.proto.label or "").startswith("Ciclo hasta"):
            campo.set_value(1).run()
            break
    else:
        pytest.fail("no está el campo de ciclo del alta")

    # La matrícula se deriva de la unidad elegida: con U14 es MTTT14.
    matricula = _matricula_auto(app)
    assert matricula == "MTTT14", matricula

    assert _click(app, "Incorporar unidad")
    # No puede romper la aplicacion: el rechazo se muestra y la app sigue viva.
    assert not app.exception, app.exception
    # Y la unidad no entró en la flota.
    assert matricula not in app.session_state.get("altas", {})


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
    assert "Vista consolidada" in texto, texto
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
    _slider_ciclo(app).set_value(29).run()
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
    _slider_ciclo(app).set_value(29).run()
    assert not app.exception, app.exception

    snap = L.fleet_snapshot(L.get_windows(), 29, 30.0, 25.0)
    fila = snap[snap["unit"] == 14].iloc[0]
    assert fila["state"] == L.AOG
    assert float(fila["pred"]) >= 25.0, (
        "la predicción puntual está por encima del umbral y aun así se deriva")

    assert "límite inferior" in _texto(app).lower()


# ------------------------------------------------------------------ fase 5
@needs_cache
def test_el_registro_de_sesion_es_visible_y_exportable():
    app = _app()
    app.run()
    assert not app.exception, app.exception
    # El registro vive plegado en un expander (es un log, no algo de demo):
    # lo que el test fija es que se pueda encontrar y exportar.
    etiquetas = [e.label or "" for e in app.expander]
    assert any("Registro de sesión" in e for e in etiquetas), etiquetas

    # Una acción discreta llena el registro; sin ella no hay nada que exportar.
    assert _click(app, "Incorporar unidad")
    assert not app.exception, app.exception

    descargas = [b.proto.label or "" for b in app.download_button]
    assert any("registro" in d.lower() for d in descargas), descargas


@needs_cache
def test_avanzar_la_flota_mueve_el_reloj_sin_romper_la_app():
    """El botón mueve el reloj y la página sobrevive.

    Escribía `st.session_state["cycle"]` desde su propio handler, y el widget ya
    se había instanciado en esa pasada: Streamlit levantaba
    `StreamlitWidgetAlreadyInstantiatedError` y la página se caía. El handler era
    correcto; lo que faltaba era dejar la escritura para antes de que el widget
    nazca.
    """
    app = _app()
    app.run()
    assert not app.exception, app.exception
    ciclo_antes = app.session_state["cycle"]

    for boton in app.button:
        if boton.key == "avanzar_flota":
            boton.click().run()
            break
    else:
        pytest.fail("no está el botón de avanzar la flota")

    assert not app.exception, app.exception
    assert app.session_state["cycle"] == ciclo_antes + 10, (
        f"{ciclo_antes} -> {app.session_state['cycle']}"
    )


# ------------------------------------------------------------------ auditoría
@needs_cache
def test_el_informe_de_auditoria_es_un_pdf_descargable():
    """El informe de auditoría existe como descarga y es un PDF de verdad.

    Congela las dos tablas de auditoría (precisión por tramo y alarma vs.
    verdad) con la huella del artefacto. El test valida el binario, no solo el
    botón: un PDF truncado sería una promesa incumplida ante el tribunal.

    P1 (mejoras-streamlit): el PDF se genera al pulsar «Generar informe», no en
    cada render; el test pulsa ese botón antes de buscar la descarga.
    """
    app = _app()
    app.run()
    assert not app.exception, app.exception

    for boton in app.button:
        if boton.key == "btn_gen_pdf":
            boton.click().run()
            break
    else:
        pytest.fail("no está el botón Generar informe (PDF)")
    assert not app.exception, app.exception

    etiquetas = [b.proto.label or "" for b in app.download_button]
    assert any("auditor" in e.lower() and "pdf" in e.lower() for e in etiquetas), etiquetas

    # La función real vive en `app/lib/informe_auditoria.py`; se valida su salida.
    from app.lib.informe_auditoria import _informe_auditoria_pdf

    windows = L.get_windows()
    curves = {int(u): L.unit_curve(windows, int(u)) for u in windows["unit"].unique()}
    data = _informe_auditoria_pdf(
        windows, curves, sorted(curves), 30.0, 25.0,
        L.get_provenance(), L.critical_zone_mae(windows, 25.0),
    )
    assert data[:5] == b"%PDF-", data[:20]
    assert data.rstrip().endswith(b"%%EOF"), "PDF sin marca de fin"


# ------------------------------------------------------------------ vista
@needs_cache
def test_la_vista_turno_oculta_el_material_de_tribunal():
    """La vista de turno deja solo lo que un operario usa en su guardia.

    Esconde el registro de sesión (log) y la traza de reglas (auditoría).
    Lo operativo —muro, reloj, orden de trabajo, hangar— sigue en su sitio.
    """
    app = _app()
    app.run()
    assert not app.exception, app.exception

    vista = next(c for c in app.segmented_control if c.label == "Vista")
    assert vista.value == "Tribunal", vista.value

    def _secciones(a):
        return [s.value for s in a.tabs[0].subheader]

    tribunal = _secciones(app)
    assert "Motor de reglas · traza del caso" in tribunal
    assert any("Registro de sesión" in (e.label or "") for e in app.tabs[0].expander)

    vista.set_value("Turno").run()
    assert not app.exception, app.exception

    turno = _secciones(app)
    assert "Motor de reglas · traza del caso" not in turno, turno
    assert not any("Registro de sesión" in (e.label or "")
                   for e in app.tabs[0].expander)

    for seccion in ("Muro del hangar", "Avanzar la flota", "Orden de trabajo",
                    "Hangar · ciclo de vida"):
        assert seccion in turno, (seccion, turno)
