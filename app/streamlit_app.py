"""Entry-point de la app con el nombre que pide la rúbrica (`app/streamlit_app.py`).

Uso::

    streamlit run app/streamlit_app.py

La app real vive en `app/dashboard_ds02.py` (producción: bundle C + reglas MIA);
este módulo solo la importa y la ejecuta, sin duplicar lógica. Funciona porque
`dashboard_ds02.py` añade su propio directorio al `sys.path` y todo su código
de interfaz corre a nivel de módulo, como en cualquier script de Streamlit.

Un rerun re-ejecuta este entrypoint, NO los módulos que importa: sin más,
el segundo rerun (F5, o cualquier interacción) devuelve el objeto ya cacheado
en `sys.modules` y el código de interfaz no corre — página en blanco, sin
excepción. Por eso se saca `dashboard_ds02` de `sys.modules` antes de
importarlo: cada pasada lo ejecuta de nuevo, como si fuera el script directo.

Despliegue: el proyecto no lleva imagen de contenedor. En local:
`streamlit run app/streamlit_app.py --server.address 127.0.0.1 --server.port 8501`.
No publicar 0.0.0.0:8501 con HTTP plano; cualquier exposición externa debe pasar
por un proxy inverso que termine TLS.
"""

from __future__ import annotations

import logging
import os
import sys
import tomllib

import _paths

sys.path.insert(0, str(_paths.APP_DIR))

# Carga .streamlit/secrets.toml en os.environ si no vienen por entorno.
# Asi N8N_WEBHOOK_URL (y N8N_WEBHOOK_TOKEN si existe) quedan disponibles
# para src/n8n y app/dashboard_ds02 sin tocar los tests, que siguen usando
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
        # dashboard_ds02.py:510 y debe ser el primer comando de Streamlit. El
        # aviso visible es otra tarea; esto deja rastro y un flag consultable.
        logging.getLogger("ds02.streamlit_app").warning(
            "no se pudo leer %s (%s): N8N_WEBHOOK_URL queda sin cargar",
            _secrets_path, exc,
        )
        os.environ.setdefault("DS02_SECRETS_ERROR", f"{type(exc).__name__}: {exc}")

# Forzar re-ejecución en cada rerun (ver docstring): un `import` a secas solo
# ejecuta el módulo la primera vez en el proceso del servidor.
sys.modules.pop("dashboard_ds02", None)

import dashboard_ds02  # noqa: E402,F401  (el import EJECUTA la app)
