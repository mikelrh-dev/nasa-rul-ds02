"""Evaluate a unit the user brings to the UI.

Three input paths (example window, editable grid, CSV) converge here: one
validator, one scoring call, one contract. The frozen bundle is loaded lazily —
importing this module does not import TensorFlow — and held by
`st.cache_resource`, so the first score pays the load and later ones do not.

Nothing is written: the model is read from `models/`, the example comes from
`app/cache/`, and a live evaluation leaves both untouched.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd
import streamlit as st

APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(APP_DIR)
SRC = os.path.join(ROOT, "src")
ARTIFACT = os.path.join(ROOT, "models", "ensemble.joblib")

import twin as T  # noqa: E402
import ui_data_loader as L  # noqa: E402
import ui_rules as UR  # noqa: E402

LIVE_UNIT = -1.0  # a DS02 unit can never take this value, so EMA never mixes

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
        f"La tabla tiene {filas:,} filas y el máximo es {MAX_FILAS:,} "
        f"(~{MAX_FILAS - window_size() + 1:,} ventanas). Recorta el histórico o "
        "usa un muestreo declarado: por encima de ese tamaño la puntuación deja de "
        "ser interactiva."
    )


def channel_order() -> list[str]:
    """The dataset's own channel order: operational conditions, then sensors.

    Read from the cache provenance (which copied it from the HDF5), never typed
    by hand — a silent reordering here would feed the model the wrong columns.
    """
    source = L.get_provenance()["source"]
    return list(source["op_names"]) + list(source["sensor_names"])


def window_size() -> int:
    return int(L.get_provenance()["source"]["window"])


def required_columns() -> list[str]:
    return ["cycle"] + channel_order()


def example_window(unit: int = 14, position: float = 0.55) -> tuple[pd.DataFrame, dict]:
    """A real cached window, lifted from `app/cache/ds02_rows.parquet`.

    The cache already stores the downsampled grid (`[::100]`), so these 50 rows
    are exactly the representation the model consumes. `position` picks where in
    the engine's life the window ends: 0.55 lands mid-life, which demonstrates a
    non-trivial state rather than the trivial end.
    """
    rows = L.get_rows()
    frame = rows[rows["unit"] == int(unit)].reset_index(drop=True)
    span = window_size()
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


def channel_labels() -> dict[str, str]:
    """What each column physically is, in the dataset's own vocabulary.

    The names are N-CMAPSS engine stations (`T24` is the LPC outlet, not a
    temperature index), so a reader cannot guess them from the header. They are
    declared once in the data loader and reused here, never retyped.
    """
    return {channel: L.CHANNEL_LABELS.get(channel, channel) for channel in channel_order()}


@st.cache_data(show_spinner=False)
def observed_envelope() -> pd.DataFrame:
    """The range the frozen bundle was actually trained on, per channel.

    Measured from the cached DS02 rows rather than quoted from memory. The
    alerting bounds are the observed extremes with a 5 % margin on each side: a
    percentile cut flags genuine in-domain telemetry (a real engine crosses p1 all
    the time), while a unit slip — psia sent as Pa, degrees R sent as K — lands
    orders of magnitude outside.
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
    """Non-blocking notes when the data is scoreable but outside the training domain.

    A cell can be numeric, in the right column and in the right order and still be
    meaningless (a Mach of 49, a pressure in the wrong unit). The bundle will
    happily return a number for it, so the honest move is to say so, not to hide
    the result and not to reject data the model can technically consume.
    """
    frame = pd.DataFrame(table).copy()
    frame.columns = [str(c).strip() for c in frame.columns]
    envelope = observed_envelope().set_index("canal")
    warnings: list[str] = []

    outside: list[str] = []
    for channel in channel_order():
        if channel not in frame.columns:
            continue
        values = pd.to_numeric(frame[channel], errors="coerce").to_numpy(dtype=float)
        low = float(envelope.loc[channel, "aviso_desde"])
        high = float(envelope.loc[channel, "aviso_hasta"])
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
    """A blank, correctly shaped CSV so nobody has to guess the 19 columns.

    Header in the dataset's order plus empty rows: filling it in Excel and
    uploading it is the low-friction path, and empty cells are rejected by the
    validator rather than silently scored as zero.
    """
    span = window_size() if rows is None else int(rows)
    columns = required_columns()
    return pd.DataFrame({column: [""] * span for column in columns}).to_csv(index=False)


def validate_table(table: pd.DataFrame) -> pd.DataFrame:
    """Reject anything the frozen bundle cannot score, naming the problem.

    The contract is not bureaucratic: the model consumes 50 rows × 18 channels in
    one fixed order, and silently reordering or short-circuiting it produces a
    confident wrong number instead of an error.
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
            f"Se necesitan al menos {span} filas para formar una ventana y llegaron "
            f"{len(frame)}."
        )

    for column in required:
        coerced = pd.to_numeric(frame[column], errors="coerce")
        bad = coerced.isna()
        if bad.any():
            first = int(np.flatnonzero(bad.to_numpy())[0])
            bruto = frame[column].iloc[first]
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
    """Load the frozen bundle on demand — never at page render."""
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
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
    span = window_size()
    if len(frame) > MAX_FILAS:
        return {"ok": False, "error": _mensaje_limite(len(frame)),
                "filas": int(len(frame)), "ventanas": 0, "avisos": [],
                "fingerprint": "", "ciclos": []}
    ventanas = int(max(0, len(frame) - span + 1))
    ciclos = frame["cycle"].to_numpy(dtype=float)
    return {
        "ok": ventanas > 0,
        "error": None if ventanas > 0 else (
            f"La tabla tiene {len(frame)} filas y hacen falta {span} para una ventana."),
        "filas": int(len(frame)),
        "ventanas": ventanas,
        "avisos": plausibility_warnings(table),
        "fingerprint": T.fingerprint(frame),
        "ciclos": [float(ciclos.min()), float(ciclos.max())],
    }


def score_table(table: pd.DataFrame, unit_id: float = LIVE_UNIT,
                engine_id: str | None = None, ensemble=None) -> dict:
    """Score every complete window in the table with the frozen bundle.

    Returns the per-window frame plus the contract actually used. The band comes
    from the artifact's own split-conformal calibration; the unit identifier is
    `-1` so the causal EMA never mixes user data with a cached engine. When an
    engine id is given it travels in the contract, so the work order and the twin
    can name the engine instead of saying "externa".

    `ensemble` lets a caller that already holds the artifact (the batch route)
    reuse it instead of going through `get_ensemble()` again.
    """
    frame = validate_table(table)
    if len(frame) > MAX_FILAS:
        raise ValueError(_mensaje_limite(len(frame)))
    if SRC not in sys.path:
        sys.path.insert(0, SRC)
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
    """Work order for a user-scored unit, with its provenance.

    Deliberately separate from the cached-fleet order: this unit has no ground
    truth, so the document says where the data came from and omits `rul_real`.

    The state comes from `mia.motor`, the same pass the on-screen badge uses, and
    the document keeps the rule and the motive. Classifying here independently
    would let the paper and the screen answer with different policies.
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
