"""Punto de entrada de la app en la ruta esperada (`app/entrypoints/streamlit_app.py`).

Uso::

    streamlit run app/entrypoints/streamlit_app.py

La app real vive en `app/entrypoints/dashboard_ds02.py` (producción: bundle C + reglas MIA);
este módulo solo la importa y la ejecuta, sin duplicar lógica. Funciona porque
el entrypoint añade la raiz del repo al `sys.path` y todo su código
de interfaz corre a nivel de módulo, como en cualquier script de Streamlit.

Un rerun re-ejecuta este entrypoint, NO los módulos que importa: sin más,
el segundo rerun (F5, o cualquier interacción) devuelve el objeto ya cacheado
en `sys.modules` y el código de interfaz no corre — página en blanco, sin
excepción. Por eso se saca `app.entrypoints.dashboard_ds02` de `sys.modules` antes de
importarlo: cada pasada lo ejecuta de nuevo, como si fuera el script directo.

Despliegue: el proyecto no lleva imagen de contenedor. En local:
`streamlit run app/entrypoints/streamlit_app.py --server.address 127.0.0.1 --server.port 8501`.
No publicar 0.0.0.0:8501 con HTTP plano; cualquier exposición externa debe pasar
por un proxy inverso que termine TLS.
"""

from __future__ import annotations

import importlib
import logging
import os
import sys
import tomllib
from pathlib import Path

# Bootstrap de paquete: este entrypoint vive en app/entrypoints/, asi que
# parents[2] es la raiz del repo. Es el UNICO sys.path.insert de app/ y el
# unico `__file__` admitido: sirve solo para poder importar `app`.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app import _paths  # noqa: E402

# El ROOT que usa la app sale de `_paths`, no de la aritmetica de `__file__`.
ROOT = _paths.ROOT

# Carga .streamlit/secrets.toml en os.environ si no vienen por entorno.
# Asi N8N_WEBHOOK_URL (y N8N_WEBHOOK_TOKEN si existe) quedan disponibles
# para src/n8n y app.entrypoints.dashboard_ds02 sin tocar los tests, que siguen usando
# os.environ directamente.
_secrets_path = str(_paths.SECRETS_PATH)
if os.path.exists(_secrets_path):
    try:
        with open(_secrets_path, "rb") as _f:
            _secrets = tomllib.load(_f)
        for _k in ("N8N_WEBHOOK_URL", "N8N_WEBHOOK_TOKEN"):
            if _k in _secrets and not os.environ.get(_k):
                os.environ[_k] = str(_secrets[_k])
    except (OSError, tomllib.TOMLDecodeError) as exc:
        # No se puede usar `st.warning` aqui: `set_page_config` vive en
        # app/entrypoints/dashboard_ds02.py:510 y debe ser el primer comando de Streamlit. El
        # aviso visible es otra tarea; esto deja rastro y un flag consultable.
        logging.getLogger("ds02.streamlit_app").warning(
            "no se pudo leer %s (%s): N8N_WEBHOOK_URL queda sin cargar",
            _secrets_path, exc,
        )
        os.environ.setdefault("DS02_SECRETS_ERROR", f"{type(exc).__name__}: {exc}")

# Forzar re-ejecución en cada rerun (ver docstring): un `import` a secas solo
# ejecuta el módulo la primera vez en el proceso del servidor.
sys.modules.pop("app.entrypoints.dashboard_ds02", None)

dashboard_ds02 = importlib.import_module("app.entrypoints.dashboard_ds02")  # noqa: E402,F401  (el import EJECUTA la app)
