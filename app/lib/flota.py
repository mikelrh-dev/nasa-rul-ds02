"""Registro de motores: una clave y una etiqueta por motor en todas las vistas.

Antes cada vista usaba una clave distinta para el mismo motor: el muro la
etiqueta visible, los gemelos el `engine_id`, el hangar `U<unit>` para caché y
altas pero el `engine_id` para gemelos, y las órdenes `motor` o `"externa"`. Un
alta creada en la barra lateral quedaba con clave `U-1000` y desaparecía al
recargar.

Este módulo es la única fuente de nombres. Todas las vistas resuelven un motor
por aquí, así que el muro, el almacén de gemelos, el hangar y las órdenes
coinciden.

Se llama `flota`, no `motor`, porque `src/mia/motor.py` es el motor de reglas y
`app/lib/rules.py` lo importa como `from src.mia import motor as M`. Los dos
paquetes están en `sys.path` cuando corre la app, así que ese nombre taparía el
motor de reglas y el dashboard importaría el registro donde espera
`motor.motor`.

No es un módulo puro: importa `ui_data_loader` para `UNIT_LABELS` y para leer la
caché en `registrar_alta`, y ese cargador importa Streamlit. No tiene efectos
secundarios (no escribe), así que se puede probar con el runtime de Streamlit.
"""
from __future__ import annotations

from app.lib import hangar as HGR
from app.lib import twin as T
from app.lib import alta as A
from app.lib.alta import PREFIJO_ALTA
from app.lib import ui_data_loader as L

ALTAS_KEY = "altas"
# PREFIJO_ALTA lo define alta (una sola definición); se reexporta aquí
# para que sigan funcionando los imports existentes `flota.PREFIJO_ALTA`.


def normalizar_matricula(texto) -> str:
    """Matrícula normalizada; vacía o corta es un error, no un valor por defecto.

    Reutiliza `twin.normalizar_id` en vez de definir otro normalizador: dos
    normalizadores son dos sitios donde arreglar el mismo fallo.
    """
    return T.normalizar_id(texto)


def etiqueta(clave, registro: dict | None = None) -> str:
    """Etiqueta legible de una clave del registro.

    Las claves de caché delegan en `L.UNIT_LABELS` y no se reescriben aquí. Las
demás claves (la matrícula de un alta o el id de un gemelo) son su propia
etiqueta, porque las escribió el operador y son las que reconoce.
    """
    clave = str(clave)
    if clave.startswith("U") and clave[1:].isdigit():
        unidad = int(clave[1:])
        return L.UNIT_LABELS.get(unidad, f"Unidad {unidad}")
    return clave


def clave_de(unidad_float, registro: dict | None = None) -> str:
    """Convierte una unidad float en su clave de registro.

    Si el float no está en el registro, cae a `f"U{int(u)}"`, así que la caché
    sigue funcionando sin entradas explícitas: la unidad 14 pasa a `U14`, que es
    lo que ya usaba el hangar. El id negativo de un alta vuelve a su matrícula,
    que es justo el objetivo del registro.
    """
    unidad = float(unidad_float)
    if registro:
        for clave, alta in (registro.get(ALTAS_KEY) or {}).items():
            if float(alta.get("unit_id", 0)) == unidad:
                return str(clave)
    return f"U{int(unidad)}"


def unidad_de(clave, registro: dict | None = None) -> float:
    """Registry key -> float unit. Inverse of `clave_de`."""
    clave = str(clave)
    if registro:
        alta = (registro.get(ALTAS_KEY) or {}).get(clave)
        if alta:
            return float(alta["unit_id"])
    if clave.startswith("U") and clave[1:].isdigit():
        return float(clave[1:])
    return float("nan")


def _proximo_indice(registro: dict) -> int:
    """Contador que solo crece, para no reutilizar nunca un id borrado.

    `len(altas)` era la fuente antigua y colisionaba: al quitar la primera de dos
    altas, la siguiente reutilizaba el id de la segunda. El contador es un entero
    no negativo guardado por alta, así que quitar una no lo hace retroceder.
    """
    altas = registro.get(ALTAS_KEY) or {}
    if not altas:
        return 0
    return max(int(alta["indice"]) for alta in altas.values()) + 1


def registrar_alta(registro: dict, matricula: str, unidad_cache: int,
                   ciclo: int) -> dict:
    """Añade un alta con id nuevo y crea su gemelo.

    El gemelo se construye con ventanas que la caché ya puntuó (`ventanas_de_alta`
    más `twin.make_twin`), así que el motor aparece en "Gemelos registrados" con
    su serie guardada. No se llama al modelo: el alta toma historial que ya
    existe.

    Lanza `ValueError` si la unidad no tiene ventanas hasta `ciclo` (indicando el
    primer ciclo puntuado) o si la matrícula ya está registrada.
    """
    clave = normalizar_matricula(matricula)
    altas = dict(registro.get(ALTAS_KEY) or {})
    if clave in altas:
        raise ValueError(f"ya hay una aeronave de alta con la matricula {clave}")
    ventanas = A.ventanas_de_alta(
        L.get_windows(), int(unidad_cache), int(ciclo), 0.0)
    indice = _proximo_indice(registro)
    altas[clave] = {
        "unit_id": float(PREFIJO_ALTA - indice),
        "indice": indice,
        "unidad_cache": int(unidad_cache),
        "ciclo": int(ciclo),
        "ventanas": int(len(ventanas)),
    }
    nuevo = dict(registro)
    nuevo[ALTAS_KEY] = altas
    return nuevo


def quitar_alta(registro: dict, matricula: str) -> dict:
    """Quita un alta, su gemelo y su registro de hangar. Su id no se reutiliza."""
    clave = normalizar_matricula(matricula)
    altas = {k: v for k, v in (registro.get(ALTAS_KEY) or {}).items() if k != clave}
    nuevo = dict(registro)
    nuevo[ALTAS_KEY] = altas
    if "twins" in registro:
        nuevo["twins"] = {k: v for k, v in (registro.get("twins") or {}).items() if k != clave}
    if "hangar" in registro:
        nuevo["hangar"] = {k: v for k, v in (registro.get("hangar") or {}).items() if k != clave}
    return nuevo



def cargar(ruta: str) -> dict:
    """Lee el registro; si falta o está corrupto, delega el respaldo en hangar."""
    return HGR.load_json_dict(ruta)
