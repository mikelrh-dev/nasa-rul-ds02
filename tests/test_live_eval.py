"""Tests for evaluating a unit the user brings to the UI.

The claims under test: the validator rejects anything the frozen bundle cannot
score, the example window is a real contract-valid window, scoring is banded and
reproducible through the CSV path, the model loads only on demand, and the
evaluation leaves `models/` and `app/cache/` untouched.

Run:  python -m pytest tests -q
"""
from __future__ import annotations

import io
import json
import os
import subprocess
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP = os.path.join(ROOT, "app")
sys.path.insert(0, ROOT)

from app.lib import ui_data_loader as L  # noqa: E402
from app.lib import ui_inference as INF  # noqa: E402
from app.lib import ui_rules as UR  # noqa: E402

needs_cache = pytest.mark.skipif(
    not L.cache_available(),
    reason="app/cache missing — run `python scripts/build/build_ui_cache.py`",
)


# ------------------------------------------------------------------ imports
def test_importing_the_module_does_not_load_tensorflow():
    code = (
        "import sys; from app.lib import ui_inference; "
        "print('tensorflow' in sys.modules, 'keras' in sys.modules)"
    )
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr[-2000:]
    assert proc.stdout.strip() == "False False"


# --------------------------------------------------------------- validation
@needs_cache
def test_example_window_is_contract_valid():
    table, meta = INF.example_window()
    assert list(table.columns) == INF.required_columns()
    assert len(table) == INF.window_size()
    assert meta["unit"] == 14
    assert meta["start_cycle"] <= meta["end_cycle"]
    cleaned = INF.validate_table(table)
    assert cleaned.shape == table.shape
    assert cleaned.dtypes.eq(float).all()


@needs_cache
def test_short_table_is_rejected_with_counts():
    table, _ = INF.example_window()
    with pytest.raises(ValueError, match=r"al menos 50 muestras remuestreadas.*llegaron 20"):
        INF.validate_table(table.head(20))


@needs_cache
def test_a_table_over_the_row_cap_is_rejected_before_the_model():
    """Un histórico completo son cientos de miles de ventanas: se corta antes."""
    table, _ = INF.example_window()
    larga = pd.concat([table] * (INF.MAX_FILAS // len(table) + 2), ignore_index=True)
    larga["cycle"] = np.arange(len(larga), dtype=float)  # ciclos crecientes
    assert len(larga) > INF.MAX_FILAS

    aviso = INF.preflight(larga)
    assert aviso["ok"] is False
    assert aviso["ventanas"] == 0
    assert L.fmt_miles(INF.MAX_FILAS) in aviso["error"]
    assert L.fmt_miles(len(larga)) in aviso["error"]

    # El mismo tope protege la ruta de puntuación, antes de importar Keras.
    with pytest.raises(ValueError, match="máximo"):
        INF.score_table(larga)


@needs_cache
def test_wrong_channel_order_is_rejected_and_named():
    table, _ = INF.example_window()
    order = INF.channel_order()
    shuffled = table[["cycle", order[1], order[0]] + order[2:]]
    with pytest.raises(ValueError, match="Orden de canales incorrecto"):
        INF.validate_table(shuffled)


@needs_cache
def test_missing_column_is_rejected():
    table, _ = INF.example_window()
    with pytest.raises(ValueError, match="Faltan columnas obligatorias: Wf"):
        INF.validate_table(table.drop(columns=["Wf"]))


@needs_cache
def test_unknown_column_is_rejected():
    table, _ = INF.example_window()
    with pytest.raises(ValueError, match="Columnas no reconocidas: engine_id"):
        INF.validate_table(table.assign(engine_id=7))


@needs_cache
def test_non_numeric_cell_is_rejected_with_position():
    table, _ = INF.example_window()
    broken = table.astype(object)
    broken.loc[3, "T24"] = "n/a"
    with pytest.raises(ValueError, match=r"`T24`, fila 4"):
        INF.validate_table(broken)


@needs_cache
def test_non_finite_values_are_rejected_with_column_and_row():
    """`inf` is not a number the bundle can score, even though `isna()` says it is.

    `to_numeric(errors="coerce")` turns "n/a" into NaN and rejects it, but `inf`
    survives as a perfectly valid float. From there it reaches the scaler, the
    residualizer and the network, and the causal EMA is a recurrence over the
    unit's windows: one `inf` contaminates every window after it, while the UI
    paints it as an ordinary finite number.
    """
    positiva, _ = INF.example_window()
    con_inf = positiva.copy()
    con_inf.loc[3, "T48"] = np.inf
    with pytest.raises(ValueError, match=r"`T48`, fila 4") as exc:
        INF.validate_table(con_inf)
    # El mismo formato de mensaje que un NaN, con la pista que lo distingue.
    assert "infinito" in str(exc.value), str(exc.value)

    negativa, _ = INF.example_window()
    con_menos_inf = negativa.copy()
    con_menos_inf.loc[7, "Ps30"] = -np.inf
    with pytest.raises(ValueError, match=r"`Ps30`, fila 8") as exc:
        INF.validate_table(con_menos_inf)
    assert "infinito" in str(exc.value), str(exc.value)

    # El contraste que hace al test util: NaN ya se rechazaba y no trae la pista
    # de infinito, porque el operador no tiene que corregir la misma celda dos veces.
    con_nan, _ = INF.example_window()
    con_nan.loc[0, "T24"] = np.nan
    with pytest.raises(ValueError, match=r"`T24`, fila 1") as exc:
        INF.validate_table(con_nan)
    assert "infinito" not in str(exc.value), str(exc.value)


@needs_cache
def test_decreasing_cycles_are_rejected():
    table, _ = INF.example_window()
    broken = table.copy()
    broken.loc[10, "cycle"] = broken.loc[2, "cycle"] - 1
    with pytest.raises(ValueError, match="disminuye"):
        INF.validate_table(broken)


@needs_cache
def test_repeated_cycles_are_allowed():
    """Several sampled rows per flight cycle are the normal DS02 layout."""
    table, _ = INF.example_window()
    assert INF.validate_table(table) is not None
    assert table["cycle"].duplicated().any()


# ----------------------------------------------------------------- scoring
@needs_cache
def test_live_score_is_banded_and_finite():
    table, _ = INF.example_window()
    result = INF.score_table(table)
    windows = result["windows"]
    assert len(windows) == 1
    assert np.isfinite(windows[["pred", "lower", "upper"]].to_numpy()).all()
    assert (windows["lower"] <= windows["pred"]).all()
    assert (windows["pred"] <= windows["upper"]).all()
    assert (windows["lower"] >= 0).all()
    assert 0.0 <= float(windows["pred"].iloc[0]) <= 90.0


@needs_cache
def test_the_triage_rule_is_the_same_one():
    table, _ = INF.example_window()
    last = INF.score_table(table)["windows"].iloc[-1]
    expected = L.classify(float(last["lower"]), 30.0, 25.0)
    assert expected in (L.AIRWORTHY, L.PREVENTIVE, L.AOG)
    assert L.classify(24.9, 30.0, 25.0) == L.AOG


@needs_cache
def test_csv_round_trip_scores_identically():
    table, _ = INF.example_window()
    direct = INF.score_table(table)["windows"]
    csv_bytes = table.to_csv(index=False)
    again = INF.score_table(pd.read_csv(io.StringIO(csv_bytes)))["windows"]
    pd.testing.assert_frame_equal(direct, again)


@needs_cache
def test_longer_history_produces_a_trajectory():
    rows = L.get_rows()
    frame = rows[rows["unit"] == 14].reset_index(drop=True).iloc[802:862]
    table = frame[["cycle"] + INF.channel_order()].reset_index(drop=True)
    result = INF.score_table(table)
    assert result["contract"]["ventanas"] == 11
    assert len(result["windows"]) > 1
    assert result["windows"]["cycle"].is_monotonic_increasing


@needs_cache
def test_model_is_loaded_once_and_reused():
    INF.score_table(INF.example_window()[0])
    first = INF.get_ensemble()
    second = INF.get_ensemble()
    assert first is second


# -------------------------------------------------------------- work order
@needs_cache
def test_live_work_order_claims_no_ground_truth():
    table, meta = INF.example_window()
    result = INF.score_table(table)
    order = INF.live_work_order(result, meta, 30.0, 25.0)
    assert order["modo"] == "evaluación en vivo"
    assert order["sin_ground_truth"] is True
    assert order["procedencia_datos"]["unit"] == 14
    entry = order["unidades"][0]
    assert "rul_real" not in entry
    assert entry["unidad"] == "externa"
    assert entry["estado"] in (L.AIRWORTHY, L.PREVENTIVE, L.AOG)
    assert order["artefacto_sha256"] == L.get_provenance()["artifact"]["ensemble_sha256"]
    assert json.dumps(order)


# ------------------------------------------------------------ app surface
@needs_cache
def test_the_app_does_not_load_the_model_until_asked():
    """Rendering the page must stay TensorFlow-free — checked in a fresh process."""
    code = (
        "import sys, os\n"
        "from streamlit.testing.v1 import AppTest\n"
        "app = AppTest.from_file('app/entrypoints/dashboard_ds02.py', default_timeout=120)\n"
        "app.run()\n"
        "assert not app.exception, app.exception\n"
        "print(len(app.tabs), 'tensorflow' in sys.modules, 'keras' in sys.modules)\n"
    )
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT,
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr[-3000:]
    assert proc.stdout.strip().splitlines()[-1] == "4 False False"


@needs_cache
def test_pressing_evaluate_renders_a_live_result():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"), default_timeout=180)
    app.run()
    button = next(b for b in app.button if b.label == "Evaluar unidad")
    button.click().run()
    assert not app.exception, app.exception
    labels = [m.label for m in app.metric]
    assert any("RUL p35" in l for l in labels), labels
    live_metric = next(m for m in app.metric if m.label == "RUL p35 (conservadora)")
    assert float(live_metric.value) >= 0.0


# --------------------------------------------------------------- explanation
@needs_cache
def test_every_channel_is_named_and_described():
    """No column may reach the grid as a bare acronym."""
    labels = INF.channel_labels()
    assert list(labels) == INF.channel_order()
    assert len(labels) == 18
    for channel, label in labels.items():
        assert label.startswith(channel + " · "), channel
        assert len(label.split(" · ", 1)[1]) > 3, channel


@needs_cache
def test_the_envelope_is_measured_and_ordered():
    envelope = INF.observed_envelope()
    assert list(envelope["canal"]) == INF.channel_order()
    assert len(envelope) == 18
    assert (envelope["mínimo"] < envelope["máximo"]).all()
    assert (envelope["aviso_desde"] < envelope["mínimo"]).all()
    assert (envelope["aviso_hasta"] > envelope["máximo"]).all()
    assert envelope["qué mide"].str.len().gt(3).all()


@needs_cache
def test_the_cached_example_raises_no_plausibility_note():
    table, _ = INF.example_window()
    assert INF.plausibility_warnings(table) == []


@needs_cache
def test_a_value_outside_the_training_range_is_flagged_but_still_scored():
    table, _ = INF.example_window()
    absurd = table.copy()
    absurd.loc[0, "Mach"] = 49.0
    notes = INF.plausibility_warnings(absurd)
    assert len(notes) == 1
    assert "`Mach` 1/50" in notes[0]
    assert "dominio de entrenamiento" in notes[0]
    assert INF.validate_table(absurd) is not None


@needs_cache
def test_in_domain_values_are_never_flagged_by_a_percentile_cut():
    """A real engine crossing the pooled p1 is in domain, not out of it."""
    table, _ = INF.example_window()
    envelope = INF.observed_envelope().set_index("canal")
    inside = all(
        table[c].between(envelope.loc[c, "aviso_desde"], envelope.loc[c, "aviso_hasta"]).all()
        for c in INF.channel_order()
    )
    assert inside
    assert INF.plausibility_warnings(table) == []


@needs_cache
def test_a_single_cycle_window_is_flagged():
    table, _ = INF.example_window()
    flat = table.copy()
    flat["cycle"] = 40
    notes = INF.plausibility_warnings(flat)
    assert any("mismo ciclo" in note for note in notes)


@needs_cache
def test_the_template_has_the_contract_shape_and_no_invented_data():
    template = INF.template_csv()
    frame = pd.read_csv(io.StringIO(template))
    assert list(frame.columns) == INF.required_columns()
    assert len(frame) == INF.window_size()
    assert frame.isna().all().all()
    with pytest.raises(ValueError, match="Valor no numérico"):
        INF.validate_table(frame)


@needs_cache
def test_the_tab_explains_the_columns_and_offers_a_template():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"), default_timeout=180)
    app.run()
    assert not app.exception, app.exception
    labels = [expander.label for expander in app.expander]
    assert any("Qué es cada columna" in label for label in labels), labels
    downloads = [button.label for button in app.download_button]
    assert any("plantilla CSV" in label for label in downloads), downloads
    # Una sola plantilla: un segundo boton con la cabecera escrita a mano era un
    # segundo sitio donde arreglar el mismo contrato.
    assert len([d for d in downloads if "plantilla CSV" in d]) == 1, downloads


@needs_cache
def test_la_plantilla_rellenada_pasa_el_validador_y_no_trae_columna_de_unidad():
    """La plantilla que se descarga es la que el validador acepta.

    Antes el alta con unidad y ciclo libres y la plantilla no tenian ningun
    test: la suite estaba verde sin exercise el codigo nuevo.
    """
    template = INF.template_csv()
    frame = pd.read_csv(io.StringIO(template))
    # Sin columna de unidad: el contrato la rechaza, no la adivina.
    assert "unit" not in frame.columns
    # Rellenada con valores validos, pasa el validador entero.
    rellena = frame.copy()
    for columna in rellena.columns:
        rellena[columna] = 1.0
    rellena["cycle"] = range(1, len(rellena) + 1)
    validada = INF.validate_table(rellena)
    assert len(validada) == INF.window_size()
    assert list(validada.columns) == INF.required_columns()


@needs_cache
def test_the_paste_grid_carries_the_glossary_and_a_row_counter():
    """The editable grid must not ask for 19 acronyms with no explanation."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"), default_timeout=180)
    app.run()
    # Se elige por etiqueta, no por índice: la sala de incorporación añadió un
    # `segmented_control` delante y el índice dejó de ser estable.
    entrada = next(
        c for c in app.segmented_control
        if (c.proto.label or "").startswith("Entrada de datos")
    )
    entrada.set_value("Editar tabla (pegar)").run()
    assert not app.exception, app.exception

    grid = next(el for el in app.dataframe if len(json.loads(el.proto.columns or "{}")) == 20)
    config = json.loads(grid.proto.columns)
    documented = [
        entry.get("help") for key, entry in config.items()
        if not key.startswith("_") and key != "cycle"
    ]
    assert len(documented) == 18
    assert all(text and "·" in text for text in documented)
    assert "altitud" in config["alt"]["help"]
    assert "Ciclo de vuelo" in config["cycle"]["help"]

    captions = [c.value for c in app.caption]
    assert any("50 muestras" in text and "ventana(s)" in text for text in captions), captions[-4:]


@needs_cache
def test_the_sidebar_explains_the_vocabulary_of_the_screen():
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"), default_timeout=180)
    app.run()
    assert not app.exception, app.exception
    labels = [expander.label for expander in app.expander]
    assert any("Cómo leer esta pantalla" in label for label in labels), labels
    text = "\n".join(m.value for m in app.markdown) + "\n".join(c.value for c in app.caption)
    for term in ("RUL", "L_inf", "objetivo nominal 90 %", "cobertura medida",
                 "HANGAR/AOG", "Ciclo de vuelo", "Ventana"):
        assert term in text, term


# ------------------------------------------------------------------ sandbox
def _sandbox_app():
    """Renders the live tab once and returns the handle to the sandbox widgets."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"), default_timeout=300)
    app.run()
    assert not app.exception, app.exception
    return app


def _slider_sandbox(app, key: str = "sbx_deriva"):
    return next(s for s in app.slider if s.key == key)


def _cruce_hangar(app) -> str:
    return next(m for m in app.metric if m.label == "Cruce a hangar").value


@needs_cache
def test_el_sandbox_reproduce_la_caché_con_deriva_cero():
    """A 0 % el cruce a hangar es el primer ciclo HANGAR de la caché, no una constante."""
    app = _sandbox_app()
    _slider_sandbox(app).set_value(0).run()
    assert not app.exception, app.exception

    curva = L.unit_curve(L.get_windows(), 14)
    bajo = curva[curva["lower_min"] < 25.0]
    esperado = int(bajo["cycle"].min())
    assert _cruce_hangar(app) == f"ciclo {esperado}", _cruce_hangar(app)


@needs_cache
def test_el_sandbox_degrada_la_banda_cuando_la_entrada_es_sintetica():
    """Con deriva != 0 la leyenda deja de llamarse conformal y el aviso lo explica."""
    app = _sandbox_app()
    _slider_sandbox(app).set_value(10).run()
    assert not app.exception, app.exception

    graficos = [c for c in app.get("plotly_chart") if "unidad 14" in (c.proto.alt or "")]
    assert graficos, "el sandbox no dibuja su curva"
    assert graficos[0].proto.alt.strip(), "G3: el gráfico del sandbox no tiene alt"
    spec = json.loads(graficos[0].proto.spec)
    leyenda = [t.get("name") for t in (spec.get("figure") or spec)["data"]]
    assert "Banda proyectada (fuera de garantía conformal 90 %)" in leyenda, leyenda
    assert any("Deriva sintética" in (w.value or "") for w in app.warning)


@needs_cache
def test_la_deriva_sintetica_adelanta_la_decision():
    """La intervención mueve la decisión: el cruce se adelanta o se queda, nunca se retrasa."""
    app = _sandbox_app()
    slider = _slider_sandbox(app)

    def cruce_con(valor: int) -> int:
        slider.set_value(valor).run()
        assert not app.exception, app.exception
        valor_visto = _cruce_hangar(app)
        assert valor_visto.startswith("ciclo "), valor_visto
        return int(valor_visto.split()[1])

    sin = cruce_con(0)
    con = cruce_con(10)
    assert con <= sin, (sin, con)


@needs_cache
def test_el_sandbox_decide_con_el_motor_oficial():
    """El estado mostrado es una etiqueta del motor `mia/reglas.py`, no un texto inventado."""
    app = _sandbox_app()
    _slider_sandbox(app).set_value(0).run()
    assert not app.exception, app.exception
    textos = " ".join(m.value for m in app.markdown)
    assert any(etiqueta in textos for etiqueta in L.STATE_LABELS.values()), textos[:200]


@needs_cache
def test_el_sandbox_muestra_el_tramo_y_no_toda_la_vida_del_motor():
    """A 0 % la métrica y el conteo de ventanas son del tramo, no de la unidad entera.

    Sin el filtro por `_c_fin`, `unit_curve` devuelve los 76 ciclos de U14 y la
    métrica enseñaba el RUL del último ciclo (0,9) en vez del del tramo (38,3).
    """
    app = _sandbox_app()
    _slider_sandbox(app).set_value(0).run()
    assert not app.exception, app.exception

    windows = L.get_windows()
    curva = L.unit_curve(windows, 14)
    bajo = curva[curva["lower_min"] < 25.0]
    c_fin = int(bajo["cycle"].min())
    esperado = float(curva[curva["cycle"] == c_fin]["pred"].iloc[0])

    metrica = next(m for m in app.metric if m.label == "RUL p35 al final del tramo")
    assert metrica.value == f"{esperado:.1f} ciclos", (metrica.value, esperado)

    ventanas_tramo = int(((windows["unit"] == 14)
                          & (windows["cycle"] >= 3)
                          & (windows["cycle"] <= c_fin)).sum())
    texto = " ".join(c.value for c in app.caption)
    assert f"{ventanas_tramo} ventanas" in texto, texto[:200]
    assert f"{int(curva['windows'].sum())} ventanas" not in texto or ventanas_tramo == int(curva['windows'].sum())


@needs_cache
def test_una_cautela_de_plausibilidad_no_bloquea_la_decision():
    """Una cautela no es un dato imposible: R1 solo debe saltar con invalidez real.

    El preset «Medio U11 desgaste» cae entero dentro de un ciclo de vuelo y el
    aviso lo dice («la tendencia es casi plana»). Ese aviso es una cautela: la
    UI afirma «se puede puntuar, pero...». Pasarlo como alerta de decision mete
    la cautela en `alertas_datos`, activa R1_SEGURIDAD y devuelve SIN_DECISION,
    que es lo contrario de lo que el propio aviso dice.

    La decision se toma de la invalidez real de la banda (`alertas_de_ventana`),
    no de las cautelas de plausibilidad.
    """
    tab, _meta = INF.example_window(11, 0.40)  # C: 0.40 -> L_inf 28.1 INSPECCION
    pf = INF.preflight(tab)
    assert any("mismo ciclo" in aviso for aviso in pf["avisos"]), pf["avisos"]

    resultado = INF.score_table(tab)
    last = resultado["windows"].iloc[-1]
    umbrales = {"apto": 30.0, "hangar": 25.0}

    # Con las cautelas metidas como alertas: R1 dispara y no se decide nada.
    traza_con_cautelas = UR.traza_decision(float(last["lower"]), umbrales, pf["avisos"])
    assert traza_con_cautelas["decision"] == "SIN_DECISION", traza_con_cautelas

    # Con la invalidez real de la banda (que aqui es ninguna): se decide.
    alertas_reales = UR.alertas_de_ventana(resultado["windows"])[-1]
    traza_real = UR.traza_decision(float(last["lower"]), umbrales, alertas_reales)
    assert traza_real["decision"] != "SIN_DECISION", traza_real
    assert traza_real["usadas"] == ["R8_INSPECCION"], traza_real


@needs_cache
def test_la_ruta_viva_decide_con_la_banda_y_no_con_las_cautelas():
    """Regresión: el cableado de la ruta viva, no solo el motor.

    `dashboard_ds02.py` metía `preflight()["avisos"]` en `alertas_datos`, así que
    el preset «Medio U11 desgaste» —una ventana entera dentro de un ciclo de
    vuelo— activaba R1_SEGURIDAD y la pantalla pintaba SIN_DECISION en vez del
    INSPECCION que promete su propio nombre.

    Aquí se comprueba `decision_en_vivo`, que es donde ahora vive esa elección:
    el test anterior probaría el motor y seguiría en verde aunque el cableado
    volviera a cruzarse.
    """
    tab, _meta = INF.example_window(11, 0.40)  # C: 0.40 -> L_inf 28.1 INSPECCION
    pf = INF.preflight(tab)
    assert pf["ok"], pf["error"]
    assert pf["avisos"], "el preset trae la cautela de ciclo único"
    assert any("mismo ciclo" in aviso for aviso in pf["avisos"]), pf["avisos"]

    resultado = INF.score_table(tab, engine_id="ESN-MEDIO-01")
    umbrales = {"apto": 30.0, "hangar": 25.0}

    decision = UR.decision_en_vivo(resultado, umbrales)
    assert decision["alertas"] == [], decision["alertas"]
    assert decision["traza"]["decision"] == L.PREVENTIVE, decision["traza"]
    assert decision["traza"]["usadas"] == ["R8_INSPECCION"], decision["traza"]

    # El contraste que explica por qué no hay que hacer lo otro: la misma ventana
    # con las cautelas metidas a mano pierde el estado.
    traza_cruzada = UR.traza_decision(
        float(decision["ventana"]["lower"]), umbrales, pf["avisos"]
    )
    assert traza_cruzada["decision"] == L.SIN_DECISION, traza_cruzada
    assert traza_cruzada["usadas"] == ["R1_SEGURIDAD"], traza_cruzada


@needs_cache
def test_el_preset_demo_pinta_el_estado_que_promete():
    """Regresión de cableado: el preset pinta su estado, no SIN_DECISION.

    El preset «Medio U11 desgaste» cae entera dentro de un ciclo de vuelo, así que
    trae la cautela de plausibilidad. Antes esa cautela viajaba en `alertas_datos`,
    R1_SEGURIDAD disparaba y la pantalla decía «SIN DECISIÓN» cuando el nombre del
    propio botón promete «INSPECCIÓN».

    Los dos tests anteriores ejercitan `decision_en_vivo` y el motor: seguirían en
    verde aunque el cableado de `dashboard_ds02.py` volviera a cruzarse. Este
    renderiza el tablero, pulsa el preset y lee el badge que ve el usuario.

    Tambien fija el largo del tramo: con `DEMO_ROWS` el preset abarca varios
    ciclos, asi que la cautela de ciclo unico no sale y la grafica tiene curva.
    Si volviera a salir, el tramo se habria quedado corto.
    """
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"),
                            default_timeout=300)
    app.run()
    assert not app.exception, app.exception

    boton = next(b for b in app.button if b.key and "Medio U11" in b.key)
    boton.click()
    app.run()
    assert not app.exception, app.exception

    badges = [(m.value or "") for m in app.markdown]
    decision = next((b for b in badges if "umbrales en vigor" in b), "")
    assert "INSPECCIÓN" in decision, decision
    assert "R8_INSPECCION" in decision, decision
    assert "SIN DECISIÓN" not in decision, decision

    # El tramo largo se nota en que la cautela de ciclo unico ya no sale.
    avisos = [(w.value or "") for w in app.warning]
    assert not any("mismo ciclo" in aviso for aviso in avisos), avisos


@needs_cache
def test_alargar_un_tramo_no_mueve_su_final():
    """`rows` ensancha hacia atras; el final (y la decision) no se mueven.

    Es la invariante que hace seguro alargar los presets: el tramo largo y el
    corto acaban en las mismas 50 muestras, asi que la pasada A decide igual y
    solo cambia la trayectoria de delante.
    """
    largo, meta_largo = INF.example_window(11, 0.36, rows=INF.DEMO_ROWS)
    corto, meta_corto = INF.example_window(11, 0.36)
    assert len(largo) == INF.DEMO_ROWS
    assert len(corto) == INF.window_size()
    assert largo.iloc[-INF.window_size():].reset_index(drop=True).equals(corto)
    assert meta_largo["end_cycle"] == meta_corto["end_cycle"]
    assert meta_largo["start_cycle"] < meta_corto["start_cycle"]

    # Lo mismo por ciclo final, que es como elige el preset critico.
    largo_c, meta_lc = INF.window_ending_at(14, 29, rows=INF.DEMO_ROWS)
    corto_c, meta_cc = INF.window_ending_at(14, 29)
    assert largo_c.iloc[-INF.window_size():].reset_index(drop=True).equals(corto_c)
    assert meta_lc["end_cycle"] == meta_cc["end_cycle"] == 29


@needs_cache
def test_cada_preset_cae_en_el_estado_que_dice_su_nombre():
    """Los nombres de los presets prometen un estado; el tramo tiene que darlo.

    Los tramos son datos (`ui_inference.demo_presets`) y sus nombres enseñan un
    estado de mantenimiento. Alargarlos es lo que da la curva y le quita el
    arranque en frio al EMA, pero no puede mover el estado: el tramo termina
    donde terminaba la ventana. Si un tramo deja de dar su estado, el boton
    prometeria algo que no muestra.
    """
    import unicodedata

    from app.lib import ui_alta as A

    def sin_acentos(texto: str) -> str:
        """El estado vive en ASCII (`INSPECCION`) y el nombre no (`INSPECCIÓN`)."""
        return "".join(c for c in unicodedata.normalize("NFD", texto)
                       if unicodedata.category(c) != "Mn")

    umbrales = {"apto": 30.0, "hangar": 25.0}
    # El preset critico usa el ciclo del estado demo (29): es el primer ciclo
    # cuyo tramo en vivo (ultima ventana) cae en HANGAR con C (L_inf 21.4).
    # El paso 3 del modo historia (25) es la primera derivacion por peor
    # ventana de la flota: otra agregacion, no el tramo en vivo.
    demo = A.estado_demo()
    presets = INF.demo_presets(int(demo["unidad"]), int(demo["ciclo"]))
    assert len(presets) >= 3, presets

    for largo in (INF.window_size(), INF.DEMO_ROWS):
        for nombre, (u, p, ciclo, _did) in presets.items():
            if ciclo is None:
                tab, _meta = INF.example_window(u, p, rows=largo)
            else:
                tab, _meta = INF.window_ending_at(u, ciclo, rows=largo)
            esperado = sin_acentos(nombre.rsplit("(", 1)[-1].rstrip(")"))
            traza = UR.decision_en_vivo(
                INF.score_table(tab, engine_id="ESN-TEST"), umbrales)["traza"]
            assert traza["decision"] == esperado, (
                f"{nombre} con {largo} filas dio {traza['decision']}, "
                f"no {esperado}")


# ------------------------------------------------------- la rejilla editable
@needs_cache
def test_recortar_la_rejilla_no_rompe_la_app():
    """El botón de recortar reduce la tabla y la página sobrevive.

    Escribía en la clave de un `st.data_editor`. Streamlit declara esa clave de
    solo lectura (`StreamlitValueAssignmentNotAllowedError`), así que no se puede
    escribir desde un handler ni con el patrón diferido: la tabla se guarda en
    `_editor_value` y es la que la rejilla dibuja.
    """
    from streamlit.testing.v1 import AppTest

    base, _meta = INF.example_window(14, 0.55)
    grande = base.copy()
    while len(grande) <= INF.UMBRAL_RECORTE_EDITOR:
        grande = pd.concat([grande, base], ignore_index=True)

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"),
                            default_timeout=300)
    app.session_state["_editor_value"] = grande
    app.run()
    assert not app.exception, app.exception

    modo = next(s for s in app.segmented_control if s.key == "live_mode")
    modo.set_value("Editar tabla (pegar)").run()
    assert not app.exception, app.exception

    boton = next((b for b in app.button if b.key == "recortar_editor"), None)
    assert boton is not None, "el botón de recortar no aparece con una tabla grande"
    boton.click().run()
    assert not app.exception, app.exception

    assert len(app.session_state["_editor_value"]) == INF.UMBRAL_RECORTE_EDITOR, (
        f"quedaron {len(app.session_state['_editor_value'])} filas"
    )


@needs_cache
def test_el_preset_demo_funciona_tambien_en_modo_editar():
    """Los presets de demo sirven en «Editar tabla», no solo en el ejemplo.

    Escribían en la clave del `data_editor`. En el modo por defecto la página no
    se caía porque la rejilla no se llega a instanciar; en cuanto el usuario
    cambiaba a «Editar tabla (pegar)» y pulsaba un preset, la clave ya existía y
    la página se rompía.
    """
    from streamlit.testing.v1 import AppTest

    base, _meta = INF.example_window(14, 0.55)
    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"),
                            default_timeout=300)
    app.session_state["_editor_value"] = pd.concat([base] * 3, ignore_index=True)
    app.run()
    assert not app.exception, app.exception

    modo = next(s for s in app.segmented_control if s.key == "live_mode")
    modo.set_value("Editar tabla (pegar)").run()
    assert not app.exception, app.exception

    boton = next(b for b in app.button if b.key == "live_demo_Sano U15 inicio (APTO)")
    boton.click().run()
    assert not app.exception, app.exception

    assert len(app.session_state["_editor_value"]) == INF.DEMO_ROWS
    assert app.session_state["live_engine_id"] == "ESN-SANO-01"


# ------------------------------------------------------- explorar por ciclo
@needs_cache
def test_explorar_por_ciclo_genera_tabla_valida():
    """El bloque genera una tabla válida sin puntuar."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"),
                            default_timeout=180)
    app.run()
    assert not app.exception, app.exception

    sel = next(s for s in app.selectbox if s.key == "explorar_unit")
    sel.select(14).run()
    assert not app.exception, app.exception

    sl = next(s for s in app.slider if s.key == "explorar_pos")
    sl.set_value(0.5).run()
    assert not app.exception, app.exception

    tabla = app.session_state.get("explorar_table")
    assert tabla is not None
    assert len(tabla) >= INF.window_size()
    assert list(tabla.columns) == INF.required_columns()
    # No se ha puntuado todavía.
    assert app.session_state.get("live_result") is None


@needs_cache
def test_explorar_por_ciclo_evaluar_funciona():
    """Pulsar 'Evaluar este tramo' produce un resultado."""
    from streamlit.testing.v1 import AppTest

    app = AppTest.from_file(os.path.join(APP, "entrypoints", "dashboard_ds02.py"),
                            default_timeout=300)
    app.run()
    assert not app.exception, app.exception

    boton = next(b for b in app.button if b.key == "explorar_evaluar")
    boton.click().run()
    assert not app.exception, app.exception

    resultado = app.session_state.get("live_result")
    assert resultado is not None
    assert resultado.get("windows") is not None
    assert len(resultado["windows"]) > 0
