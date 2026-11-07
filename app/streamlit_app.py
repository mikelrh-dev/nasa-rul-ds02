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

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Forzar re-ejecución en cada rerun (ver docstring): un `import` a secas solo
# ejecuta el módulo la primera vez en el proceso del servidor.
sys.modules.pop("dashboard_ds02", None)

import dashboard_ds02  # noqa: E402,F401  (el import EJECUTA la app)
