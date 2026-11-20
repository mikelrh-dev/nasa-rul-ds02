"""Evalúa una unidad que el usuario trae a la interfaz.

Tres rutas de entrada (ventana de ejemplo, rejilla editable y CSV) convergen
aquí: un validador, una llamada de puntuado y un contrato. El bundle congelado se
carga de forma diferida (importar este módulo no importa TensorFlow) y se guarda
en `st.cache_resource`, así que el primer puntuado paga la carga y los siguientes
no.

No se escribe nada: el modelo se lee de `models/`, el ejemplo viene de
`app/cache/` y una evaluación en vivo deja ambos intactos.
"""
from __future__ import annotations

import os

import numpy as np
import pandas as pd
import streamlit as st

from app import _paths

ROOT = str(_paths.ROOT)
ARTIFACT = str(_paths.ARTIFACT_PATH)

from app.lib import twin as T  # noqa: E402
from app.lib import ui_data_loader as L  # noqa: E402
from app.lib import rules as UR  # noqa: E402

LIVE_UNIT = -1.0  # una unidad DS02 nunca toma este valor, así que la EMA no mezcla

# La banda de la ruta en vivo es siempre la del artefacto: no pasa por R6.
BANDA_ARTEFACTO = "artefacto (models/ds02_manifest.json)"
CORRECCION_NINGUNA = "ninguna (banda del artefacto sobre la ventana aportada)"

# Tope de tabla. Cada fila extra es una ventana más (step=1): 5 000 filas son
# ~4 951 ventanas y unos 18 MB solo para el tensor de entrada. Por encima, la
# puntuación deja de ser interactiva y puede agotar la memoria del portátil.
MAX_FILAS = 5000

# A partir de aquí la rejilla editable se vuelve lenta: se ofrece recortar.
# El recorte es siempre explícito (botón) y visible (aviso con cifras).
UMBRAL_RECORTE_EDITOR = 1500


def limitar_filas(table: pd.DataFrame, max_filas: int = UMBRAL_RECORTE_EDITOR) -> tuple[pd.DataFrame, bool]:
    """Devuelve la tabla recortada a `max_filas` y si hubo recorte.

    No adivina: quien recorta es el botón de la UI, que lo anuncia con cifras.
    Aquí solo se ejecuta el corte para poder probarlo sin levantar la app.
    """
    frame = pd.DataFrame(table)
    if len(frame) <= max_filas:
        return frame, False
    return frame.iloc[:max_filas].copy().reset_index(drop=True), True


def _mensaje_limite(filas: int) -> str:
    return (
        f"La tabla tiene {L.fmt_miles(filas)} filas y el máximo es {L.fmt_miles(MAX_FILAS)} "
        f"(~{L.fmt_miles(MAX_FILAS - window_size() + 1)} ventanas). Recorta el histórico o "
        "usa un muestreo declarado: por encima de ese tamaño la puntuación deja de "
        "ser interactiva."
    )


def channel_order() -> list[str]:
    """Orden de canales del dataset: condiciones operativas y después sensores.

    Se lee de la procedencia de la caché (que lo copió del HDF5), nunca se escribe
a mano: un reordenamiento silencioso aquí daría al modelo las columnas
equivocadas.
    """
    source = L.get_provenance()["source"]
    return list(source["op_names"]) + list(source["sensor_names"])


def window_size() -> int:
    """Ventana temporal (lecturas) que espera el bundle congelado.

    Se lee de la provenance de la caché, nunca se escribe a mano: si el
    artefacto cambiase de ventana, la UI la hereda sin editar código.
    """
    return int(L.get_provenance()["source"]["window"])


def required_columns() -> list[str]:
    """Columnas del caso nuevo: cycle + los 18 canales DS02.

    El orden lo da `channel_order()` (heredado de la caché/HDF5): un cambio
    de orden aquí alimentaría al bundle con columnas cruzadas.
    """
    return ["cycle"] + channel_order()


def example_window(unit: int = 14, position: float = 0.55,
                   rows: int | None = None) -> tuple[pd.DataFrame, dict]:
    """Una ventana real cacheada, tomada de `app/cache/ds02_rows.parquet`.

    La caché ya guarda la rejilla submuestreada (`[::100]`), así que estas 50
    filas son exactamente la representación que consume el modelo. `position`
elige dónde termina la ventana en la vida del motor: 0.55 cae a media vida, lo
que muestra un estado no trivial en vez del final obvio.

    `rows` amplía el corte hacia atrás sin mover el final, así que quien llama
recibe una trayectoria en vez de una sola ventana: la EMA causal tiene historial
que suavizar y el gráfico tiene curva. Nunca baja de `window_size()`: el modelo
consume una ventana de longitud fija y un corte más corto no lo es. El final del
corte no se mueve, así que ampliarlo no cambia la decisión.
    """
    rows_frame = L.get_rows()
    frame = rows_frame[rows_frame["unit"] == int(unit)].reset_index(drop=True)
    span = window_size() if rows is None else max(window_size(), int(rows))
    if len(frame) < span:
        raise ValueError(f"unit {unit} has {len(frame)} cached rows, needs {span}")
    end = int(round(len(frame) * float(np.clip(position, 0.0, 1.0))))
    end = max(span, min(end, len(frame)))
    start = end - span
    chunk = frame.iloc[start:end].copy()
    table = chunk[["cycle"] + channel_order()].reset_index(drop=True)
    meta = {
        "source": "app/cache/ds02_rows.parquet",
        "unit": int(unit),
        "row_slice": [int(start), int(end)],
        "start_cycle": int(chunk["cycle"].iloc[0]),
        "end_cycle": int(chunk["cycle"].iloc[-1]),
    }
    return table, meta


def cycles_of_unit(unit: int) -> list[int]:
    """Ciclos disponibles de una unidad, leídos de la caché de filas."""
    rows_frame = L.get_rows()
    frame = rows_frame[rows_frame["unit"] == int(unit)]
    return sorted(int(c) for c in frame["cycle"].unique())


def window_between_cycles(unit: int, start_cycle: int,
                          end_cycle: int) -> tuple[pd.DataFrame, dict]:
    """Tramo manual: todas las filas de la caché entre dos ciclos, ambos incluidos.

    Es el equivalente manual de `example_window`/`window_ending_at`: no elige
    una posición ni un ciclo final, sino el rango exacto que pide el usuario.
    El mínimo de 50 filas lo valida `preflight`, no esta función, para que la
    tabla se pueda ver aunque el tramo todavía no sea puntuable.
    """
    inicio, fin = int(start_cycle), int(end_cycle)
    if inicio > fin:
        raise ValueError(f"el ciclo inicial ({inicio}) no puede ser mayor que el final ({fin})")
    rows_frame = L.get_rows()
    frame = rows_frame[rows_frame["unit"] == int(unit)].reset_index(drop=True)
    mask = frame["cycle"].between(inicio, fin).to_numpy()
    posiciones = np.flatnonzero(mask)
    if posiciones.size == 0:
        raise ValueError(f"la unidad {unit} no tiene filas entre los ciclos {inicio} y {fin}")
    chunk = frame.iloc[int(posiciones[0]):int(posiciones[-1]) + 1].copy()
    table = chunk[["cycle"] + channel_order()].reset_index(drop=True)
    meta = {
        "source": "app/cache/ds02_rows.parquet",
        "unit": int(unit),
        "row_slice": [int(posiciones[0]), int(posiciones[-1]) + 1],
        "start_cycle": int(chunk["cycle"].iloc[0]),
        "end_cycle": int(chunk["cycle"].iloc[-1]),
    }
    return table, meta


def window_ending_at(unit: int, cycle: int,
                     rows: int | None = None) -> tuple[pd.DataFrame, dict]:
    """La ventana que termina en la última fila cacheada de `cycle`.

    `example_window` elige por fracción de filas; esta elige por el ciclo de vuelo
    en el que termina, que es la unidad de razonamiento del modo historia y del
    panel de flota. La forma es la misma: `window_size()` muestras submuestreadas
    en el orden de canales del dataset.

    `rows` amplía el corte hacia atrás sin mover el final, igual que
    `example_window`. El ciclo final no cambia, así que la decisión tampoco; solo
    crece la trayectoria anterior.
    """
    rows_frame = L.get_rows()
    frame = rows_frame[rows_frame["unit"] == int(unit)].reset_index(drop=True)
    span = window_size() if rows is None else max(window_size(), int(rows))
    mask = (frame["cycle"] == int(cycle)).to_numpy()
    if not mask.any():
        disponibles = sorted(int(c) for c in frame["cycle"].unique())
        raise ValueError(
            f"la unidad {unit} no tiene filas en el ciclo {cycle}; "
            f"los suyos van de {disponibles[0]} a {disponibles[-1]}"
        )
    end = int(np.flatnonzero(mask)[-1]) + 1
    end = max(span, end)
    start = end - span
    chunk = frame.iloc[start:end].copy()
    table = chunk[["cycle"] + channel_order()].reset_index(drop=True)
    meta = {
        "source": "app/cache/ds02_rows.parquet",
        "unit": int(unit),
        "row_slice": [int(start), int(end)],
        "start_cycle": int(chunk["cycle"].iloc[0]),
        "end_cycle": int(chunk["cycle"].iloc[-1]),
    }
    return table, meta


# Cuantas muestras abarca un tramo de demo. Con una sola ventana (50) el EMA
# arranca en frio y la grafica tiene un punto; con 300 hay curva y el EMA ya
#olvido. El estado no cambia: el tramo termina donde terminaba la ventana.
DEMO_ROWS = 300


def demo_presets(u_hangar: int, c_hangar: int,
                 rows: int = DEMO_ROWS) -> dict[str, tuple]:
    """Tramos de demo: nombre -> (unidad, posicion, ciclo_final, matricula).

    `posicion` es None cuando el tramo se elige por ciclo final. Cada nombre
    lleva el estado que debe demostrar y `tests/test_live_eval.py` lo fija: si
    alargar un tramo le cambia el estado, el test lo dice en vez de dejar que el
    boton prometa un estado que no da.

    `rows` va como parametro para que ese test pueda comprobar el nombre a
    cualquier largo, no solo al que hay hoy.
    """
    return {
        "Sano U15 inicio (APTO)": (15, 0.05, None, "ESN-SANO-01"),
        "Medio U11 desgaste (INSPECCIÓN)": (11, None, 24, "ESN-MEDIO-01"),  # C: ciclo 24 -> L_inf 22.9 INSPECCION
        f"Crítico U{u_hangar} · ciclo {c_hangar} (HANGAR)": (
            u_hangar, None, c_hangar, "ESN-CRIT-01"),
        "Clásico U14 (HANGAR)": (14, 0.55, None, "ESN-DEMO-01"),
    }


def channel_labels() -> dict[str, str]:
    """Qué es físicamente cada columna, con el vocabulario del dataset.

    Los nombres son estaciones del motor N-CMAPSS (`T24` es la salida del
compresor de baja, no un índice de temperatura), así que el lector no puede
adivinarlos por la cabecera. Se declaran una vez en el cargador de datos y se
reutilizan aquí, nunca se reescriben.
    """
    return {channel: L.CHANNEL_LABELS.get(channel, channel) for channel in channel_order()}


@st.cache_data(show_spinner=False)
def observed_envelope() -> pd.DataFrame:
    """Rango real de entrenamiento del bundle congelado, por canal.

    Se mide sobre las filas DS02 cacheadas, no se copia de memoria. Los límites de
    aviso son los extremos observados con un margen del 5 % por lado: un corte por
    percentil marcaría telemetría legítima del dominio (un motor real cruza p1
    continuamente), mientras que un fallo de unidades (psia enviado como Pa, grados
    R como K) cae órdenes de magnitud fuera.
    """
    rows = L.get_rows()
    records = []
    for channel in channel_order():
        values = rows[channel].to_numpy(dtype=float)
        low, high = float(values.min()), float(values.max())
        margin = 0.05 * (high - low)
        label = L.CHANNEL_LABELS.get(channel, channel)
        records.append({
            "canal": channel,
            "qué mide": label.split(" · ", 1)[-1],
            "mínimo": low,
            "máximo": high,
            "aviso_desde": low - margin,
            "aviso_hasta": high + margin,
        })
    return pd.DataFrame(records)


def plausibility_warnings(table: pd.DataFrame) -> list[str]:
    """Avisos no bloqueantes si el dato se puede puntuar pero sale del dominio.

    Una celda puede ser numérica, estar en la columna correcta y en el orden
correcto y aun así no significar nada (un Mach de 49, una presión en unidades
equivocadas). El bundle devolverá un número sin quejarse, así que lo honesto es
decirlo: ni ocultar el resultado ni rechazar datos que el modelo puede consumir
técnicamente.
    """
    frame = pd.DataFrame(table).copy()
    frame.columns = [str(c).strip() for c in frame.columns]
    envelope = observed_envelope().set_index("canal")
    warnings: list[str] = []

    outside: list[str] = []
    for channel in channel_order():
        if channel not in frame.columns:
            continue
        numeric: pd.Series = pd.to_numeric(frame[channel], errors="coerce")  # type: ignore[assignment]
        values = numeric.to_numpy(dtype=float)
        low = float(envelope.loc[channel, "aviso_desde"])
        high = float(envelope.loc[channel, "aviso_hasta"])
        # isna explícito: pd.to_numeric(..., errors="coerce") convierte huecos
        # en NaN y la comparación con el envelope los ignora en silencio
        # (NaN < low == False). Se cuentan y se avisan como NaN, no como
        # fuera de rango, para no confundir "sin dato" con "dato imposible".
        nan_count = int(numeric.isna().sum())
        if nan_count:
            outside.append(f"`{channel}` {nan_count}/{len(values)} NaN")
        count = int(np.sum((values < low) | (values > high)))
        if count:
            outside.append(f"`{channel}` {count}/{len(values)} (DS02: {low:.4g}–{high:.4g})")
    if outside:
        shown = "; ".join(outside[:6]) + ("; …" if len(outside) > 6 else "")
        warnings.append(
            "Hay valores fuera del rango que el modelo vio al entrenar "
            "(extremos observados en DS02 con un 5 % de margen): "
            f"{shown}. Se puede puntuar, pero el resultado cae fuera del dominio "
            "de entrenamiento; revisa las unidades."
        )

    if "cycle" in frame.columns:
        cycles = pd.to_numeric(frame["cycle"], errors="coerce").dropna()
        if cycles.nunique() < 2:
            warnings.append(
                "Todas las filas pertenecen al mismo ciclo de vuelo: la ventana "
                "cubre un único ciclo, así que la tendencia que ve el modelo es "
                "casi plana."
            )
    return warnings


def template_csv(rows: int | None = None) -> str:
    """Un CSV vacío con la forma correcta para no adivinar las 19 columnas.

    Cabecera en el orden del dataset y filas vacías: rellenarlo en Excel y subirlo
es la vía más cómoda, y el validador rechaza las celdas vacías en vez de
puntuarlas como cero sin avisar.
    """
    span = window_size() if rows is None else int(rows)
    columns = required_columns()
    return pd.DataFrame({column: [""] * span for column in columns}).to_csv(index=False)


def validate_table(table: pd.DataFrame) -> pd.DataFrame:
    """Rechaza lo que el bundle congelado no puede puntuar, diciendo qué falla.

    El contrato no es burocracia: el modelo consume 50 filas × 18 canales en un
    orden fijo, y reordenarlos o recortarlos en silencio produce un número
    equivocado con seguridad en vez de un error.
    """
    if table is None:
        raise ValueError("No hay tabla que evaluar.")
    frame = pd.DataFrame(table).copy()
    frame.columns = [str(c).strip() for c in frame.columns]

    required = required_columns()
    present = [c for c in frame.columns if c in required]
    missing = [c for c in required if c not in frame.columns]
    if missing:
        raise ValueError(
            "Faltan columnas obligatorias: " + ", ".join(missing) +
            ". Se esperaba `cycle` y los 18 canales del dataset."
        )
    extra = [c for c in frame.columns if c not in required and c != "unit"]
    if extra:
        raise ValueError(
            "Columnas no reconocidas: " + ", ".join(extra) +
            ". Solo se aceptan `cycle`, los 18 canales y, opcionalmente, `unit`."
        )

    channel_cols = [c for c in present if c != "cycle"]
    expected_channels = channel_order()
    if channel_cols != expected_channels:
        raise ValueError(
            "Orden de canales incorrecto. Se esperaba: " + ", ".join(expected_channels)
        )

    span = window_size()
    if len(frame) < span:
        raise ValueError(
            f"Se necesitan al menos {span} muestras remuestreadas (~0,4 ciclos de vuelo) "
            f"para formar una ventana y llegaron {len(frame)}."
        )

    for column in required:
        crudo = frame[column]
        coerced = pd.to_numeric(crudo, errors="coerce")
        # `inf` es un float perfectamente valido y `isna()` lo da por bueno: pasaba
        # al scaler, al residualizador y a la red, y el EMA causal es una
        # recurrencia sobre las ventanas de la unidad, asi que un solo `inf`
        # contaminaba todas las siguientes mientras la UI lo pintaba como un
        # numero finito. Se rechaza en el mismo bucle y con el mismo formato de
        # mensaje que un NaN: el operador necesita la columna y la fila, y un
        # segundo formato de error para el mismo tipo de celda rota solo confundiria.
        malo = coerced.isna() | coerced.map(lambda v: bool(np.isinf(v))).fillna(False)
        if bool(malo.to_numpy(dtype=bool).any()):
            first = int(np.flatnonzero(malo.to_numpy())[0])
            bruto = crudo.iloc[first]
            pista = ""
            texto = str(bruto).strip()
            if "," in texto:
                import re as _re

                if _re.fullmatch(r"-?\d+,\d+", texto):
                    pista = (" Parece coma decimal europea (p. ej. `3,2`): el contrato "
                             "pide punto decimal (`3.2`). En Excel: selecciona la columna, "
                             "reemplaza `,` por `.` y vuelve a pegar.")
                else:
                    pista = (" Si son decimales con coma europea, pásalos a punto decimal "
                             "(`3.2` en vez de `3,2`).")
            elif np.isinf(float(coerced.iloc[first])):
                pista = (" Un infinito no es un valor que el paquete congelado pueda "
                         "puntuar: llega al EMA causal y corrompe todas las ventanas "
                         "posteriores; corrige la celda.")
            raise ValueError(
                f"Valor no numérico en la columna `{column}`, fila {first + 1} "
                f"({bruto!r}).{pista}"
            )
        frame[column] = coerced.astype(float)

    cycles = frame["cycle"].to_numpy()
    if np.any(np.diff(cycles) < 0):
        first = int(np.flatnonzero(np.diff(cycles) < 0)[0])
        raise ValueError(
            f"La columna `cycle` disminuye en la fila {first + 2}: las filas deben "
            "venir en orden temporal (varios registros por ciclo están permitidos)."
        )

    return frame[required].reset_index(drop=True)


def reordenar_columnas(table: pd.DataFrame) -> pd.DataFrame:
    """Devuelve la tabla en el orden del contrato cuando trae las 19 columnas.

    `validate_table` sigue siendo estricta (el contrato no adivina), pero la UI
    ofrece este botón antes de puntuar: si el conjunto coincide y solo cambia el
    orden, se reordena sin tocar ningún valor. Si faltan o sobran columnas,
    propaga el mismo error de `validate_table` con el mismo mensaje.
    """
    frame = pd.DataFrame(table).copy()
    frame.columns = [str(c).strip() for c in frame.columns]
    required = required_columns()
    if set(frame.columns) != set(required):
        return validate_table(table)
    return validate_table(frame[required])


@st.cache_resource(show_spinner="Cargando el artefacto congelado (una sola vez)…")
def get_ensemble():
    """Carga el bundle congelado a demanda, nunca al pintar la página.

    Seguridad: `load_ensemble` verifica el SHA-256 del artefacto contra
    `models/ds02_manifest.json` y `app/cache/cache_manifest.json`, y lanza
    `RuntimeError` sin deserializar si no coincide. No se usa `eval`.
    """
    from ds02_rul.persistence import load_ensemble

    return load_ensemble(ARTIFACT)


def preflight(table: pd.DataFrame) -> dict:
    """Valida la tabla y cuenta ventanas **sin** cargar el modelo.

    Existe para no pagar la carga de TensorFlow antes de saber si la tabla sirve.
    Devuelve `ok`, el motivo cuando no lo es, cuántas ventanas saldrían, los
    avisos de plausibilidad y la huella de los valores que se puntuarían.
    """
    try:
        frame = validate_table(table)
    except ValueError as exc:
        return {"ok": False, "error": str(exc), "filas": 0, "ventanas": 0,
                "avisos": [], "fingerprint": "", "ciclos": []}
    except (FileNotFoundError, OSError) as exc:
        # Caché/manifiesto ausente: validate_table()->required_columns()->
        # get_provenance() abre ficheros; no debe tumbar la UI.
        return {"ok": False, "error": f"Fichero de caché/manifiesto no disponible: {exc}",
                "filas": 0, "ventanas": 0, "avisos": [], "fingerprint": "", "ciclos": []}
    span = window_size()
    if len(frame) > MAX_FILAS:
        return {"ok": False, "error": _mensaje_limite(len(frame)),
                "filas": int(len(frame)), "ventanas": 0, "avisos": [],
                "fingerprint": "", "ciclos": []}
    ventanas = int(max(0, len(frame) - span + 1))
    ciclos = frame["cycle"].to_numpy(dtype=float)
    # P1.5 · fingerprint sin caché (documentado, no aplicado): `T.fingerprint`
    # ya es la huella (SHA-256 sobre CSV, ~6 ms/500 filas medidas); cachearlo
    # por "hash de tabla" exigiría un pre-hash del mismo coste y `twin.py`
    # no puede importar Streamlit (diseño testeable sin runtime). Con P1.4
    # los sliders repetidos ya no llegan aquí: no hay 2ª llamada que ahorrar.
    return {
        "ok": ventanas > 0,
        "error": None if ventanas > 0 else (
            f"La tabla tiene {len(frame)} muestras y hacen falta {span} para una ventana."),
        "filas": int(len(frame)),
        "ventanas": ventanas,
        "avisos": plausibility_warnings(table),
        "fingerprint": T.fingerprint(frame),
        "ciclos": [float(ciclos.min()), float(ciclos.max())],
    }


def score_table(table: pd.DataFrame, unit_id: float = LIVE_UNIT,
                engine_id: str | None = None, ensemble=None,
                timeout_s: float | None = 120.0) -> dict:
    """Puntúa con el bundle congelado todas las ventanas completas de la tabla.

    Devuelve el frame por ventana y el contrato realmente usado. La banda sale de
    la calibración split-conformal del propio artefacto; el identificador de
unidad es `-1` para que la EMA causal nunca mezcle datos del usuario con un
motor cacheado. Si se pasa un id de motor, viaja en el contrato, así que la
orden y el gemelo pueden nombrarlo en vez de decir "externa".

    `ensemble` permite que quien ya tiene el artefacto (la ruta de lote) lo
reutilice sin pasar otra vez por `get_ensemble()`.

    `timeout_s` limita el tiempo de puntuado (carga del bundle y predicción). Si
se supera, lanza `TimeoutError` con el contexto del tope de filas: 5 000 filas
ya son ~4 951 ventanas, así que el presupuesto evita que el portátil se quede
en una pausa no interactiva.
    """
    import time

    frame = validate_table(table)
    if len(frame) > MAX_FILAS:
        raise ValueError(_mensaje_limite(len(frame)))
    _t0 = time.monotonic()
    from ds02_rul.inference import raw_windows

    order = channel_order()
    n_op = len(L.get_provenance()["source"]["op_names"])
    W = frame[order[:n_op]].to_numpy(dtype=np.float32)
    Xs = frame[order[n_op:]].to_numpy(dtype=np.float32)
    cycles = frame["cycle"].to_numpy(dtype=np.float64)
    units = np.full(len(frame), float(unit_id), dtype=np.float64)

    X, cyc_end, uni, meta = raw_windows(
        W, Xs, units, cycles, window=window_size(), step=1
    )
    if ensemble is None:
        ensemble = get_ensemble()
    point, lower, upper = ensemble.predict_interval(X, cyc_end, uni)
    if timeout_s is not None and time.monotonic() - _t0 > float(timeout_s):
        raise TimeoutError(
            f"La puntuación de {L.fmt_miles(len(frame))} filas superó el presupuesto de "
            f"{float(timeout_s):.0f} s (~{L.fmt_miles(max(0, len(frame) - window_size() + 1))} "
            f"ventanas). Recorta el histórico o usa un muestreo declarado."
        )

    result = pd.DataFrame(
        {
            "window": np.arange(len(point)),
            "cycle": cyc_end,
            "start_row": meta["start_index"].to_numpy(),
            "pred": point,
            "lower": lower,
            "upper": upper,
        }
    )
    return {
        "windows": result,
        "contract": {
            "window": window_size(),
            "step": 1,
            "unidad_simulada": unit_id,
            "canales": order,
            "artefacto": os.path.relpath(ARTIFACT, ROOT).replace("\\", "/"),
            "artefacto_sha256": L.get_provenance()["artifact"]["ensemble_sha256"],
            "motor": T.normalizar_id(engine_id) if engine_id else None,
            "fingerprint": T.fingerprint(frame),
            "filas": int(len(frame)),
            "ventanas": int(len(result)),
        },
    }


def live_work_order(result: dict, example_meta: dict | None,
                    airworthy: float, aog: float,
                    alertas: list[str] | None = None,
                    banda: str = BANDA_ARTEFACTO,
                    correccion: str = CORRECCION_NINGUNA,
                    ) -> dict:
    """Orden de trabajo de una unidad puntuada por el usuario, con su procedencia.

    Está separada a propósito de la orden de la flota cacheada: esta unidad no
tiene verdad, así que el documento dice de dónde salieron los datos y omite
`rul_real`.

    El estado sale de `mia.motor`, la misma pasada que usa la insignia en
pantalla, y el documento conserva la regla y el motivo. Clasificar aquí por
separado haría que el papel y la pantalla respondieran con políticas distintas.
    """
    last = result["windows"].iloc[-1]
    traza = UR.traza_decision(
        float(last["lower"]), {"apto": airworthy, "hangar": aog}, alertas,
    )
    state = traza["decision"] if traza["decision"] in L.STATE_LABELS \
        else L.classify(float(last["lower"]), airworthy, aog)
    entry = {
        "unidad": result["contract"].get("motor") or "externa",
        "estado": state,
        "regla_decision": " + ".join(traza["usadas"]),
        "ventana_evaluada": {
            "filas": int(result["contract"]["window"]),
            "step": int(result["contract"]["step"]),
            "ciclo": float(last["cycle"]),
            "start_row": int(last.get("start_row", -1)),
            "indice": int(last.get("window", -1)),
        },
        "ciclo_evaluado": float(last["cycle"]),
        "rul_estimada": round(float(last["pred"]), 2),
        "limite_inferior": round(float(last["lower"]), 2),
        "limite_superior": round(float(last["upper"]), 2),
        "motivo": " · ".join(traza["porque"]) or L.STATE_LABELS[state],
        "accion": L.ACTIONS[state],
    }
    return {
        "documento": "Orden de mantenimiento — unidad evaluada en la UI",
        "generado_en": pd.Timestamp.now().isoformat(timespec="seconds"),
        "dataset": "DS02 (datos aportados por el usuario)",
        "modo": "evaluación en vivo",
        "procedencia_datos": example_meta or {"source": "entrada manual o CSV"},
        "artefacto_sha256": result["contract"]["artefacto_sha256"],
        "motor": result["contract"].get("motor"),
        "fingerprint": result["contract"].get("fingerprint"),
        "ventana": {
            "size": result["contract"]["window"],
            "step": result["contract"]["step"],
            "canales": result["contract"]["canales"],
        },
        "umbrales": {"apto_si_limite_inferior_ge": airworthy,
                     "hangar_si_limite_inferior_lt": aog},
        "banda": banda,
        "correccion": correccion,
        "sin_ground_truth": True,
        "unidades": [entry],
    }
