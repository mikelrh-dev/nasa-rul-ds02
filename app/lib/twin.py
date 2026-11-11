"""Gemelos digitales: lo que el modelo produjo, guardado una vez.

Un `twin` es un diccionario serializable con la identidad del motor, la huella de
la tabla que se puntuó, la fuente de banda, los umbrales en vigor y la serie de
ventanas. El estado **no** se guarda: se deriva al leer con la pasada A del motor
(`mia.motor`), de modo que mover un umbral no reescribe la serie ni obliga a
volver a puntuar.

La decisión que abre un registro de hangar sí se congela, pero eso vive en
`app/hangar.py`: aquí solo se guarda lo que el modelo dijo y con qué banda.

Sin Streamlit: el registro se guarda en `st.session_state` desde el tablero, pero
este módulo no lo importa, para poder probarlo sin levantar la app.
"""
from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from app.lib import hangar as HGR
from app.lib import rules as UR
from app.lib.hangar import _ahora  # dueno unico del reloj UTC

REGISTRY_KEY = "twins"
MIN_ID = 3


def fingerprint(table: pd.DataFrame) -> str:
    """Huella de los valores que se puntúan, no del fichero.

    Se ordenan las columnas tal como llegan, se fuerzan a numérico y se redondean
    a 9 decimales: el mismo dato escrito con otro espaciado o con `1` en vez de
    `1.0` da la misma huella.
    """
    frame = pd.DataFrame(table).copy()
    frame.columns = [str(c).strip() for c in frame.columns]
    # Todo a float: un entero y el mismo valor como decimal han de dar la misma
    # huella, y `to_csv` los escribiría distinto.
    frame = frame.apply(pd.to_numeric, errors="coerce").astype(float)
    payload = frame.to_csv(index=False, float_format="%.9f").encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalizar_id(engine_id: str | None) -> str:
    """Id recortado y en mayúsculas; vacío es un error, no un valor por defecto."""
    texto = str(engine_id or "").strip().upper()
    if len(texto) < MIN_ID:
        raise ValueError(
            f"el id del motor necesita al menos {MIN_ID} caracteres, llegó {texto!r}"
        )
    return texto


def make_twin(engine_id: str, result: dict, *, source: str,
              banda: str, correccion: str, umbrales: dict,
              fingerprint_value: str | None = None,
              created_at: str | None = None) -> dict:
    """Construye el gemelo a partir del resultado de `score_table`."""
    ventanas = result["windows"]
    serie = [
        {
            "cycle": float(row["cycle"]),
            "pred": float(row["pred"]),
            "lower": float(row["lower"]),
            "upper": float(row["upper"]),
            "start_row": int(row.get("start_row", -1)),
        }
        for _, row in ventanas.iterrows()
    ]
    return {
        "id": normalizar_id(engine_id),
        "source": str(source),
        "fingerprint": str(fingerprint_value or ""),
        "created_at": created_at or _ahora(),
        "banda": banda,
        "correccion": correccion,
        "umbrales": {"apto": float(umbrales["apto"]),
                     "hangar": float(umbrales["hangar"])},
        "contrato": dict(result.get("contract", {})),
        "serie": serie,
        "truth": None,
    }


def registrar(registro: dict, twin: dict, reemplazar: bool = False) -> dict:
    """Añade el gemelo a una copia del registro; rechaza ids repetidos.

    Con `reemplazar=True` la serie, la huella y el contrato se sustituyen. La
    **RUL real reportada se conserva**: es un hecho del motor, no de la ventana
    que se acaba de puntuar, y perderla al re-puntuar sería destruir el único
    dato de validación que hay.
    """
    engine_id = normalizar_id(twin.get("id"))
    anterior = registro.get(engine_id)
    if anterior is not None and not reemplazar:
        raise ValueError(
            f"ya hay un gemelo registrado con el id {engine_id}; marca «reemplazar» "
            "o elimina el anterior"
        )
    nuevo = {**twin, "id": engine_id}
    if anterior is not None and anterior.get("truth"):
        nuevo["truth"] = anterior["truth"]
    actualizado = dict(registro)
    actualizado[engine_id] = nuevo
    return actualizado


def eliminar(registro: dict, engine_id: str) -> dict:
    """Devuelve el registro sin el gemelo indicado; no muta la entrada."""
    engine_id = normalizar_id(engine_id)
    return {k: v for k, v in registro.items() if k != engine_id}


def vista_resultado(twin: dict) -> dict:
    """Resultado compatible con `live_work_order` a partir de la serie guardada.

    Devuelve una sola fila: la **peor ventana del último ciclo**, que es la que
    decide. Con la última fila de la serie, la orden y la tabla podrían discrepar
    cuando el último ciclo tiene varias ventanas.

    El `window` devuelto es la **posición de esa ventana dentro de la serie
    guardada** (`peor.name`), no un índice de ventana del dataset: la serie del
    gemelo es la lista de ventanas que se puntuaron y el índice solo la ordena.
    Es el mismo valor para un alta de la caché, una evaluación en vivo y un
    gemelo registrado, porque `twin["serie"]` es siempre una lista plana.
    """
    frame = pd.DataFrame(twin["serie"])
    if frame.empty:
        raise ValueError("el gemelo no tiene serie que documentar")
    ultimo = float(frame["cycle"].max())
    del_ciclo = frame[frame["cycle"] == ultimo].sort_values("lower", kind="stable")
    peor = del_ciclo.iloc[0]
    return {
        "windows": pd.DataFrame([{
            "window": int(peor.name),
            "cycle": float(peor["cycle"]),
            "start_row": int(peor.get("start_row", -1)),
            "pred": float(peor["pred"]),
            "lower": float(peor["lower"]),
            "upper": float(peor["upper"]),
        }]),
        "contract": dict(twin.get("contrato", {})),
    }


def serie(twin: dict) -> pd.DataFrame:
    """Serie guardada, con las columnas que espera la pasada A."""
    frame = pd.DataFrame(twin["serie"])
    if frame.empty:
        return frame
    frame["unit"] = 0
    frame["start_index"] = frame["start_row"]
    frame["y_true"] = np.nan
    return frame[["unit", "cycle", "pred", "lower", "upper", "start_index", "y_true"]]


def ciclo_a_ciclo(twin: dict, umbrales: dict) -> pd.DataFrame:
    """Lectura por ciclo: media para el gráfico, peor ventana para decidir.

    La decisión se recalcula aquí, no se guarda: es lo que permite mover el
    umbral y ver el efecto sin volver a puntuar.
    """
    frame = serie(twin)
    if frame.empty:
        return pd.DataFrame(columns=["cycle", "pred", "lower_media", "lower_min",
                                     "upper", "decision", "regla"])
    decidido = UR.decidir_ventanas(frame, umbrales)
    peor = decidido.loc[decidido.groupby("cycle")["lower"].idxmin()]
    medias = frame.groupby("cycle", as_index=False).agg(
        pred=("pred", "mean"),
        lower_media=("lower", "mean"),
        upper=("upper", "mean"),
    )
    salida = medias.merge(
        peor[["cycle", "lower", "decision", "regla_decision"]].rename(
            columns={"lower": "lower_min", "regla_decision": "regla"}),
        on="cycle", how="left",
    )
    return salida.sort_values("cycle").reset_index(drop=True)


def estado_actual(twin: dict, umbrales: dict) -> dict:
    """Último ciclo con su decisión, que es lo que la flota muestra."""
    curva = ciclo_a_ciclo(twin, umbrales)
    if curva.empty:
        return {"cycle": None, "lower_min": float("nan"), "decision": None, "regla": ""}
    ultima = curva.iloc[-1]
    return {
        "cycle": float(ultima["cycle"]),
        "lower_min": float(ultima["lower_min"]),
        "decision": str(ultima["decision"]),
        "regla": str(ultima["regla"] or ""),
    }


def con_verdad(twin: dict, rul_real: float, ciclo: float | None = None) -> dict:
    """Copia del gemelo con la RUL real reportada por el taller."""
    valor = float(rul_real)
    if not np.isfinite(valor) or valor < 0.0:
        raise ValueError(f"RUL real inválida: {rul_real!r}")
    ciclo = float(ciclo) if ciclo is not None else float(twin["serie"][-1]["cycle"])
    return {**twin, "truth": {"rul_real": valor, "cycle": ciclo, "at": _ahora()}}


def metricas_verdad(twin: dict) -> dict | None:
    """Error y cobertura de la banda en el ciclo donde se conoció la verdad.

    Se usa la ventana más pesimista de ese ciclo (la de menor `lower`): si esa
    banda cubre la verdad, la decisión que la acompañó era defendible.
    """
    truth = twin.get("truth")
    if not truth or not twin.get("serie"):
        return None
    frame = pd.DataFrame(twin["serie"])
    distancia = (frame["cycle"] - float(truth["cycle"])).abs()
    ciclo = frame.loc[distancia.idxmin(), "cycle"]
    del_ciclo = frame[frame["cycle"] == ciclo]
    fila = del_ciclo.loc[del_ciclo["lower"].idxmin()]
    real = float(truth["rul_real"])
    return {
        "cycle": float(ciclo),
        "rul_real": real,
        "pred": float(fila["pred"]),
        "lower": float(fila["lower"]),
        "upper": float(fila["upper"]),
        "error": float(fila["pred"]) - real,
        "cubierta": bool(fila["lower"] <= real <= fila["upper"]),
    }


def resumen_gemelos(registro: dict) -> dict:
    """Cuántos gemelos hay y cuántos tienen verdad conocida."""
    con_verdad = [t for t in registro.values() if t.get("truth")]
    metricas = [metricas_verdad(t) for t in con_verdad]
    metricas = [m for m in metricas if m]
    return {
        "total": len(registro),
        "con_verdad": len(metricas),
        "cubiertos": sum(1 for m in metricas if m["cubierta"]),
        "mae": float(np.mean([abs(m["error"]) for m in metricas])) if metricas else float("nan"),
    }


def guardar_disco(registro: dict, ruta: str) -> None:
    """Persiste el registro de gemelos en JSON (atómico, delegado a hangar)."""
    HGR.atomic_save_json(ruta, registro)


def cargar_disco(ruta: str) -> dict:
    """Lee el registro; si no existe o está corrupto, devuelve uno vacío."""
    return HGR.load_json_dict(ruta)
