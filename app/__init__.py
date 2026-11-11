"""Paquete `app/`: superficie de decisión DS02.

Cuatro subpaquetes:

* `app.entrypoints` — puntos de entrada (`dashboard_ds02.py`, `streamlit_app.py`).
* `app.ui` — fragmentos de Streamlit (barra lateral y pestañas).
* `app.lib` — estado puro, datos, inferencia, reglas y helpers.
* `app.services` — API FastAPI.

`app/_paths.py` es el único dueño de las rutas del repositorio; no se mueve.
Los imports entre módulos son de paquete (`from app.lib import ...`), nunca
desnudos: la raíz del repo la añade el entrypoint al `sys.path`.
"""
