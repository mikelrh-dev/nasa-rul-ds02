"""Entry-point de la app con el nombre que pide la rúbrica (`app/streamlit_app.py`).

Uso::

    streamlit run app/streamlit_app.py

La app real vive en `app/dashboard_ds02.py` (producción: bundle B + reglas MIA);
este módulo solo la importa y la ejecuta, sin duplicar lógica. Funciona porque
`dashboard_ds02.py` añade su propio directorio al `sys.path` y todo su código
de interfaz corre a nivel de módulo, como en cualquier script de Streamlit.
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dashboard_ds02  # noqa: E402,F401  (el import EJECUTA la app)
