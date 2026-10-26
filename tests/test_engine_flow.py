"""Flujo de la pestaña de flota con un gemelo y el hangar.

Se inyecta un gemelo en `st.session_state` antes del primer render, así que el
test no carga TensorFlow: comprueba el cableado (tabla, formulario de apertura,
selector de destino y movimiento), no el modelo.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import os
import subprocess
import sys

import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, APP)

import hangar as HGR  # noqa: E402
import twin as T  # noqa: E402
import ui_alta as AL  # noqa: E402
import ui_data_loader as L  # noqa: E402
import ui_inference as INF  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build_ui_cache.py`",
)

UMBRALES = {"apto": 30.0, "hangar": 25.0}


def _gemelo(motor: str = "ESN-TEST") -> dict:
    resultado = {
        "windows": pd.DataFrame({
            "window": [0, 1],
            "cycle": [40.0, 41.0],
            "start_row": [10, 11],
            "pred": [15.0, 12.0],
            "lower": [10.0, 8.0],
            "upper": [22.0, 20.0],
        }),
        "contract": {"window": 50, "step": 1, "canales": ["alt"],
                     "artefacto_sha256": "b" * 64, "motor": motor},
    }
    return T.make_twin(motor, resultado, source="test", banda="artefacto",
                       correccion="ninguna", umbrales=UMBRALES,
                       fingerprint_value="f" * 64)


def _resultado_live() -> dict:
    """Lo que deja `score_table` en sesión, sin llamar al modelo."""
    return {
        "windows": pd.DataFrame({
            "window": [0, 1],
            "cycle": [40.0, 41.0],
            "start_row": [10, 11],
            "pred": [14.0, 11.0],
            "lower": [9.0, 7.0],
            "upper": [21.0, 19.0],
        }),
        "contract": {
            "window": 50, "step": 1, "canales": ["alt"],
            "unidad_simulada": -1.0, "artefacto": "models/ensemble.joblib",
            "artefacto_sha256": "c" * 64, "motor": "ESN-TEST",
            "fingerprint": "d" * 64, "filas": 51, "ventanas": 2,
        },
    }


def _boton(app, etiqueta: str):
    for boton in app.button:
        if (boton.label or "") == etiqueta:
            return boton
    raise AssertionError(f"no hay botón {etiqueta!r}: {[b.label for b in app.button]}")


@needs_cache
def test_el_gemelo_entra_en_la_flota_y_recorre_el_hangar():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=240)
    app.session_state["twins"] = {"ESN-TEST": _gemelo()}
    app.run()
    assert not app.exception, app.exception

    tablas = [d.value for d in app.dataframe if isinstance(d.value, pd.DataFrame)]
    flota = [t for t in tablas if "Motor" in t.columns and "Huella" in t.columns]
    assert flota, [list(t.columns)[:4] for t in tablas]
    assert "ESN-TEST" in set(flota[0]["Motor"])
    assert "HANGAR" in str(flota[0].iloc[0]["Estado"])

    # Abrir registro: la decisión de entrada queda congelada con sus umbrales.
    _boton(app, "Abrir registro").click().run()
    assert not app.exception, app.exception
    registros = app.session_state["hangar"]
    assert "ESN-TEST" in registros
    assert registros["ESN-TEST"]["estado"] == HGR.AOG
    assert registros["ESN-TEST"]["entrada"]["lower"] == 8.0
    assert registros["ESN-TEST"]["entrada"]["umbrales"] == {"apto": 30.0, "hangar": 25.0}

    # El único destino permitido desde AOG es taller.
    destinos = [s for s in app.selectbox if s.label == "Nuevo estado"]
    # `options` llega con la etiqueta formateada; el valor sigue siendo el estado.
    assert destinos and list(destinos[0].options) == [HGR.ETIQUETAS[HGR.TALLER]]

    _boton(app, "Registrar movimiento").click().run()
    assert not app.exception, app.exception
    assert app.session_state["hangar"]["ESN-TEST"]["estado"] == HGR.TALLER
    assert len(app.session_state["hangar"]["ESN-TEST"]["eventos"]) == 2

    tablas = [d.value for d in app.dataframe if isinstance(d.value, pd.DataFrame)]
    cola = [t for t in tablas if "L_inf de entrada" in t.columns]
    assert cola, [list(t.columns)[:4] for t in tablas]
    assert cola[0].iloc[0]["Estado"] == HGR.ETIQUETAS[HGR.TALLER]


@needs_cache
def test_el_muro_muestra_el_motor_registrado():
    """Registrar un motor lo pone en el muro: antes el muro solo leía la caché.

    El gemelo vive en `twins` y su serie dentro del gemelo, así que no está en
    `frame` y `fleet_snapshot` no lo veía. Este test ejercita el cableado
    (muro -> tarjeta -> sección de gemelos), no el módulo.
    """
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=240)
    app.session_state["twins"] = {"ESN-MURO": _gemelo("ESN-MURO")}
    app.run()
    assert not app.exception, app.exception

    tarjetas = [b for b in app.button if (b.proto.label or "").strip() == "Ver gemelo"]
    cache = sorted(int(u) for u in L.get_windows()["unit"].unique())
    assert len(tarjetas) == len(cache) + 1, [b.key for b in tarjetas]
    assert any("ESN-MURO" in (b.key or "") for b in tarjetas), [b.key for b in tarjetas]
    assert any("**ESN-MURO**" in (m.value or "") for m in app.markdown)
    # El badge de la tarjeta dice lo que el gemelo deriva con los umbrales en vigor.
    assert any("DERIVACIÓN A HANGAR" in (m.value or "") for m in app.markdown)

    # Pulsar la tarjeta lleva a la sección de gemelos, que es donde está su ficha.
    next(b for b in tarjetas if "ESN-MURO" in (b.key or "")).click().run()
    assert not app.exception, app.exception
    assert any("ESN-MURO" in (c.value or "") and "L_inf" in (c.value or "")
               for c in app.caption), [c.value for c in app.caption]


@needs_cache
def test_el_gemelo_registrado_tiene_detalle_abierto():
    """El gemelo registrado se puede abrir: antes no había panel para él.

    La serie del gemelo ya estaba guardada; lo que faltaba era un sitio donde
    verla. Este test fija el panel: curva, banda y las dos preguntas que un
    gemelo digital tiene que responder.
    """
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=240)
    app.session_state["twins"] = {"ESN-DETA": _gemelo("ESN-DETA")}
    app.run()
    assert not app.exception, app.exception

    texto = _texto(app)
    assert "Gemelo digital · detalle" in texto, texto
    assert "Ciclos hasta el umbral" in texto
    assert "La ventana que decide" in texto
    # La posición que cita el panel es dentro de la serie guardada, no un índice
    # de ventana del dataset: el número solo es honesto si la frase lo dice.
    assert "posición **1** de la serie guardada" in texto, texto
    # La banda se dibuja entera: el panel cita los dos extremos, no solo lower.
    alts = [c.proto.alt or "" for c in app.get("plotly_chart")]
    assert any("banda conformal al 90" in a for a in alts), alts
    # El gemelo de prueba cruza el umbral en el ciclo 40 y su último ciclo es 41:
    # el panel tiene que decir que ya está por debajo, no inventar un número.
    assert "ya está por debajo del umbral" in texto, texto


def _texto(app) -> str:
    partes = [m.value for m in app.markdown]
    partes += [c.value for c in app.caption]
    partes += [s.value for s in app.subheader]
    partes += [f"{m.label} {m.value}" for m in app.metric]
    return "\n".join(p for p in partes if p)


@needs_cache
def test_la_ventana_que_decide_es_la_de_menor_limite_inferior():
    """La ventana que decide se reporta, no la última fila de la serie.

    `vista_resultado` elige la ventana con el menor `lower` del último ciclo
    puntuado y luego escribe `len(frame) - 1`, que es la posición de la última
    fila guardada. Con un alta de la caché (`step=2`) el último ciclo tiene 44
    ventanas, así que los dos números discrepan: la U11 hasta el ciclo 22 guarda
    1219 filas y la ventana que decide está en la posición 1177, no en la 1218.
    El panel cita ese número como «la ventana que decide».
    """
    crudo = L.get_windows()
    recorte = AL.ventanas_de_alta(
        crudo.rename(columns={"start_index": "start_row"}), 11, 22, -11.0,
    )
    gemelo = T.make_twin(
        "U11-ALTA", {"windows": recorte.reset_index(drop=True),
                     "contract": {"window": 50, "step": 2, "canales": ["alt"],
                                  "motor": "U11-ALTA"}},
        source="cache", banda="artefacto", correccion="ninguna",
        umbrales=UMBRALES, fingerprint_value="f" * 64,
    )
    serie = pd.DataFrame(gemelo["serie"])
    ultimo = float(serie["cycle"].max())
    decidida = serie[serie["cycle"] == ultimo].sort_values("lower", kind="stable").iloc[0]

    # El alta reproduce el caso medido: el último ciclo no es una sola ventana.
    assert len(serie) == 1219
    assert int(ultimo) == 22
    assert int((serie["cycle"] == ultimo).sum()) == 44
    # `start_row // step` es la posición dentro de la serie guardada.
    assert int(decidida["start_row"]) // 2 == 1177

    reportada = int(T.vista_resultado(gemelo)["windows"].iloc[0]["window"])
    assert reportada == decidida.name == 1177
    assert reportada != len(serie) - 1, "la última fila no es la que decide"


@needs_cache
def test_la_orden_de_un_gemelo_sale_de_la_serie_guardada():
    """El papel de un gemelo se emite sin re-puntuar y sin inventar verdad.

    El gemelo de prueba tiene una ventana por ciclo (ciclos 40 y 41), así que la
    ventana que decide es la última fila: la posición 1 dentro de la serie
    guardada. Un alta de la caché, en cambio, solapa ventanas y la posición que
    reporta `vista_resultado` ya no es la de la última fila.
    """
    gemelo = _gemelo()
    orden = INF.live_work_order(
        T.vista_resultado(gemelo), {"source": gemelo["source"]},
        30.0, 25.0, banda=gemelo["banda"], correccion=gemelo["correccion"],
    )
    entrada = orden["unidades"][0]
    assert entrada["unidad"] == "ESN-TEST"
    # La orden cita la posición dentro de la serie guardada, no un índice de
    # dataset: con una ventana por ciclo es la última fila, la 1 de 2.
    assert entrada["ventana_evaluada"]["indice"] == 1
    assert entrada["ventana_evaluada"]["ciclo"] == 41.0
    assert entrada["limite_inferior"] == 8.0
    assert entrada["estado"] == L.AOG
    assert orden["artefacto_sha256"] == "b" * 64
    assert orden["sin_ground_truth"] is True
    assert "rul_real" not in entrada

    # El CSV no rompe por no haber verdad: la columna sale vacía.
    cabecera, fila = L.work_order_csv(orden).strip().splitlines()
    columnas = cabecera.split(",")
    assert fila.split(",")[columnas.index("rul_real")] == ""
    assert fila.split(",")[columnas.index("limite_inferior")] == "8.0"


@needs_cache
def test_el_panel_de_gemelos_documenta_y_elimina():
    """El panel construye la orden de cada gemelo y permite borrarlo."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=240)
    app.session_state["twins"] = {"ESN-TEST": _gemelo()}
    app.session_state["hangar"] = {
        "ESN-TEST": HGR.abrir("ESN-TEST", 41, 8.0, UMBRALES, "R9_HANGAR"),
    }
    app.run()
    # Construir la orden (dentro del expander) corre en cada render: si faltara
    # una clave del contrato, este `run` levantaría.
    assert not app.exception, app.exception

    _boton(app, "Eliminar gemelo").click().run()
    assert not app.exception, app.exception
    assert app.session_state["twins"] == {}
    # Libros distintos: borrar el gemelo no cierra el registro de hangar.
    assert app.session_state["hangar"]["ESN-TEST"]["estado"] == HGR.AOG


@needs_cache
def test_reemplazar_el_gemelo_desde_la_pestana_en_vivo():
    """Repuntuar el mismo motor pide confirmación y conserva la RUL real."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "dashboard_ds02.py"), default_timeout=240)
    app.session_state["twins"] = {"ESN-TEST": T.con_verdad(_gemelo(), 12.0, 41.0)}
    app.session_state["live_result"] = _resultado_live()
    app.session_state["live_meta"] = {"source": "test"}
    app.run()
    assert not app.exception, app.exception

    cajas = [c for c in app.checkbox if c.key == "twin_replace"]
    assert cajas, [c.key for c in app.checkbox]
    assert cajas[0].value is False  # sin la casilla no se sobrescribe
    cajas[0].set_value(True).run()
    assert not app.exception, app.exception

    _boton(app, "Reemplazar gemelo `ESN-TEST`").click().run()
    assert not app.exception, app.exception
    guardado = app.session_state["twins"]["ESN-TEST"]
    assert len(app.session_state["twins"]) == 1
    assert guardado["fingerprint"] == "d" * 64  # la serie nueva, no la vieja
    assert guardado["serie"][-1]["lower"] == 7.0
    assert guardado["truth"]["rul_real"] == 12.0


@needs_cache
def test_el_hangar_rechaza_un_movimiento_ilegal():
    """La UI no ofrece destinos imposibles; el módulo sigue siendo la defensa."""
    registro = HGR.abrir("ESN-TEST", 40, 8.0, UMBRALES, "R9_HANGAR")
    with pytest.raises(ValueError):
        HGR.avanzar(registro, HGR.EN_SERVICIO, 41)


# ------------------------------------------------------------ pre-vuelo
def test_el_pre_vuelo_no_carga_tensorflow():
    """La validación de una tabla inválida no debe arrastrar Keras."""
    codigo = (
        "import sys; sys.path.insert(0, 'app'); sys.path.insert(0, 'mia')\n"
        "import pandas as pd, ui_inference as INF\n"
        "tabla = pd.DataFrame({'cycle': [1, 2], 'alt': [1.0, 2.0]})\n"
        "print('ok', INF.preflight(tabla)['ok'])\n"
        "print('tensorflow', 'tensorflow' in sys.modules,\n"
        "      'keras', 'keras' in sys.modules)\n"
    )
    salida = subprocess.run([sys.executable, "-c", codigo], cwd=ROOT,
                            capture_output=True, text=True)
    assert salida.returncode == 0, salida.stderr
    assert "ok False" in salida.stdout
    assert "tensorflow False" in salida.stdout
    assert "keras False" in salida.stdout


@needs_cache
def test_el_pre_vuelo_cuenta_ventanas_y_detecta_el_orden():
    tabla, _ = INF.example_window()
    preflight = INF.preflight(tabla)
    assert preflight["ok"] is True
    assert preflight["filas"] == 50 and preflight["ventanas"] == 1
    assert len(preflight["fingerprint"]) == 64
    assert preflight["ciclos"] == [float(tabla["cycle"].min()),
                                  float(tabla["cycle"].max())]

    desordenada = tabla[list(tabla.columns[::-1])]
    malo = INF.preflight(desordenada)
    assert malo["ok"] is False
    assert "Orden de canales" in malo["error"]
