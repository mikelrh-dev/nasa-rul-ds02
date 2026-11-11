"""Incorporación en lote: puntúa N motores a la vez y devuelve un triaje.

El operador trae N motores (los que sean), la app los puntúa todos de una vez y
devuelve una fila por motor: predicción, banda y estado decidido por el límite
inferior. No reentrena, no toca la caché y no inventa ground truth: los datos los
aporta el usuario, así que no hay error que reportar.

Sin Streamlit: el módulo no llama a ningún `st.*`, para poder probarlo sin
levantar la app (misma convención que `twin.py`, `hangar.py` y `ui_alta.py`). El
único camino al modelo y al validador es `ui_inference`: no hay un segundo
validador ni una segunda llamada al artefacto.
"""
from __future__ import annotations

import io
import os

import pandas as pd

from app.lib import ui_data_loader as L
from app.lib import ui_inference as INF
from app.lib import ui_rules as UR
from app.lib import twin as T

# Tope duro por memoria del portátil: cada motor son ~50 muestras remuestreadas
# (~0,4 ciclos de vuelo) y una llamada al modelo. 25 es interactivo; 250 no lo es.
# Se aplica con un aviso visible.
MAX_MOTORES_LOTE = 25

# P1 hardening de subidas: antes de `read_csv` se valida el tamaño (bytes) y
# luego se acota la lectura con `nrows=MAX_FILAS+1`. `MAX_FILAS` es el mismo
# tope de `ui_inference` (un solo validador, un solo tope).
MAX_FILAS = getattr(INF, "MAX_FILAS", 5000)
MAX_BYTES_CSV = 5 * 1024 * 1024  # 5 MiB: holgado para 5.000 filas x 19 cols.

# Las columnas del triaje. Son lo que se muestra y lo que se exporta: ni una
# más. `rmse` y `mae` no están porque el usuario trae los datos y no hay verdad.
COLUMNAS_TRIAJE = ["matricula", "ciclo", "pred", "lower", "upper", "estado", "regla"]


def excede_limite(n: int) -> bool:
    """True si `n` supera el tope de motores por lote."""
    return int(n) > MAX_MOTORES_LOTE


def _check_bytes(n_bytes: int, origen: str) -> None:
    """Rechaza el CSV si su tamaño en bytes supera `MAX_BYTES_CSV`."""
    if int(n_bytes) > MAX_BYTES_CSV:
        raise ValueError(
            f"El CSV «{origen}» pesa {L.fmt_miles(int(n_bytes))} bytes y el máximo es "
            f"{L.fmt_miles(MAX_BYTES_CSV)} bytes. Recorta el histórico o usa un muestreo "
            "declarado antes de subirlo."
        )


def _check_filas(n_filas: int, origen: str) -> None:
    """Rechaza la tabla si supera `MAX_FILAS` (detectado con nrows=MAX_FILAS+1)."""
    if int(n_filas) > MAX_FILAS:
        raise ValueError(
            f"El CSV «{origen}» tiene más de {L.fmt_miles(MAX_FILAS)} filas. Recorta el "
            "histórico o usa un muestreo declarado: por encima de ese tamaño "
            "la puntuación deja de ser interactiva."
        )


def _size_bytes(archivo) -> int | None:
    """Best-effort byte size of an uploaded file-like object without reading it."""
    size = getattr(archivo, "size", None)
    if isinstance(size, (int, float)):
        return int(size)
    try:
        buffer = archivo.getbuffer()  # Streamlit UploadedFile
        return int(buffer.nbytes)
    except Exception:  # noqa: BLE001 - best effort, falls through to nrows check
        pass
    try:
        value = archivo.getvalue()
        return int(len(value))
    except Exception:  # noqa: BLE001
        pass
    try:
        stream = getattr(archivo, "file", None) or archivo
        pos = stream.tell()
        stream.seek(0, 2)
        size_int = int(stream.tell())
        stream.seek(pos)
        return size_int
    except Exception:  # noqa: BLE001
        pass
    return None


def bloques_de_csv(texto: str) -> list[dict]:
    """CSV con columna `unit_id` que separa bloques: cada bloque es un motor.

    La columna `unit_id` no viaja a la puntuación (no forma parte del contrato);
    solo dice qué filas son de cada motor.

    P1: valida el tamaño en bytes antes de parsear y acota la lectura con
    `nrows=MAX_FILAS+1`; además limita los motores por lote a
    `MAX_MOTORES_LOTE` antes de devolver ningún bloque.
    """
    _check_bytes(len(str(texto).encode("utf-8")), "CSV por bloques")
    crudo = pd.read_csv(io.StringIO(texto), nrows=MAX_FILAS + 1)
    _check_filas(len(crudo), "CSV por bloques")
    if "unit_id" not in crudo.columns:
        raise ValueError(
            "El CSV por bloques necesita una columna `unit_id` que diga qué filas "
            "pertenecen a cada motor."
        )
    bloques = []
    for unit_id, grupo in crudo.groupby("unit_id", sort=False):
        bloques.append({
            "tabla": grupo.drop(columns=["unit_id"]).reset_index(drop=True),
            "matricula": str(unit_id).strip().upper(),
            "fuente": "CSV por bloques",
        })
    if len(bloques) > MAX_MOTORES_LOTE:
        raise ValueError(
            f"El CSV por bloques trae {len(bloques)} motores y el máximo por "
            f"lote es {MAX_MOTORES_LOTE}. Divide el lote en varios envíos."
        )
    return bloques


def bloques_de_archivos(archivos) -> list[dict]:
    """Varios CSV subidos a la vez: cada archivo es un motor.

    P1: rechaza el lote antes de parsear todo si hay más de
    `MAX_MOTORES_LOTE` archivos; por archivo valida el tamaño en bytes
    antes de `read_csv` y acota la lectura con `nrows=MAX_FILAS+1`.
    """
    archivos = list(archivos or [])
    if len(archivos) > MAX_MOTORES_LOTE:
        raise ValueError(
            f"El lote trae {len(archivos)} archivos y el máximo por lote es "
            f"{MAX_MOTORES_LOTE}. Divide el lote en varios envíos."
        )
    bloques = []
    for archivo in archivos:
        nombre = getattr(archivo, "name", None) or "csv"
        n_bytes = _size_bytes(archivo)
        if n_bytes is not None:
            _check_bytes(n_bytes, str(nombre))
        tabla = pd.read_csv(archivo, nrows=MAX_FILAS + 1)
        _check_filas(len(tabla), str(nombre))
        matricula = os.path.splitext(os.path.basename(str(nombre)))[0]
        bloques.append({
            "tabla": tabla,
            "matricula": matricula.strip().upper(),
            "fuente": str(nombre),
        })
    return bloques


def validar_bloque(bloque: dict) -> dict:
    """Preflight de un bloque. Reutiliza `ui_inference.preflight`: un solo validador."""
    return INF.preflight(bloque["tabla"])


def validar_lote(bloques: list[dict]) -> dict:
    """Preflight de todo el lote antes de llamar al modelo, con el primero que falla."""
    resumen = {"ok": True, "bloques": len(bloques), "errores": {}}
    for bloque in bloques:
        aviso = validar_bloque(bloque)
        if not aviso["ok"]:
            resumen["ok"] = False
            resumen["errores"][str(bloque["matricula"])] = aviso["error"]
    return resumen


def puntuar_bloque(bloque: dict, motor) -> pd.DataFrame:
    """Puntúa un bloque y devuelve una fila: matrícula, ciclo final, pred, lower, upper.

    `motor` es el ensemble ya cargado (`ui_inference.get_ensemble()`): el lote lo
    pasa para no recargar el artefacto una vez por motor. El camino al modelo es
    `ui_inference.score_table`, el mismo de la evaluación individual.
    """
    resultado = INF.score_table(
        bloque["tabla"], engine_id=bloque["matricula"], ensemble=motor,
    )
    ultima = resultado["windows"].iloc[-1]
    return pd.DataFrame([{
        "matricula": str(bloque["matricula"]),
        "ciclo": float(ultima["cycle"]),
        "pred": float(ultima["pred"]),
        "lower": float(ultima["lower"]),
        "upper": float(ultima["upper"]),
    }])


def puntuar_lote(bloques: list[dict], umbrales: dict, motor, progreso=None) -> pd.DataFrame:
    """N motores -> N filas con su estado decidido por el límite inferior.

    El estado se pregunta al motor `mia/` (la pasada A de siempre), no se
    reclasifica aquí: una UI y un documento no pueden responder con políticas
    distintas. `progreso(i, n, matrícula)` se llama antes de cada motor, para que
    la barra diga el conteo real y no un spinner.
    """
    filas = []
    for i, bloque in enumerate(bloques, start=1):
        if progreso is not None:
            progreso(i, len(bloques), str(bloque["matricula"]))
        fila = puntuar_bloque(bloque, motor).iloc[0].to_dict()
        traza = UR.traza_decision(float(fila["lower"]), umbrales)
        fila["estado"] = traza["decision"] if traza["decision"] in L.STATE_LABELS \
            else L.classify(float(fila["lower"]), umbrales["apto"], umbrales["hangar"])
        fila["regla"] = " + ".join(traza["usadas"])
        filas.append(fila)
    return pd.DataFrame(filas, columns=COLUMNAS_TRIAJE)


def registrar_gemelos(bloques: list[dict], motor, umbrales: dict,
                      gemelos: dict, progreso=None) -> dict:
    """Puntúa el lote y deja los N gemelos en una copia del registro.

    Es una acción explícita del usuario (no el camino normal del lote), así que
    re-puntuar aquí es aceptable: el artefacto está cacheado y son N llamadas.
    """
    nuevo = dict(gemelos)
    for i, bloque in enumerate(bloques, start=1):
        if progreso is not None:
            progreso(i, len(bloques), str(bloque["matricula"]))
        resultado = INF.score_table(
            bloque["tabla"], engine_id=bloque["matricula"], ensemble=motor,
        )
        gemelo = T.make_twin(
            bloque["matricula"], resultado,
            source=str(bloque["fuente"]),
            banda=INF.BANDA_ARTEFACTO,
            correccion=INF.CORRECCION_NINGUNA,
            umbrales=umbrales,
            fingerprint_value=resultado["contract"].get("fingerprint", ""),
        )
        nuevo = T.registrar(nuevo, gemelo)
    return nuevo


def resumen_lote(resultado: pd.DataFrame) -> dict:
    """Cuántos motores hay por estado, para los KPIs del lote."""
    cuentas = resultado["estado"].value_counts().to_dict() if not resultado.empty else {}
    return {
        "total": int(len(resultado)),
        "por_estado": {estado: int(cuentas.get(estado, 0)) for estado in L.STATE_LABELS},
    }
