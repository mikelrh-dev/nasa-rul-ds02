"""Fachada del paquete `app.ui` (la división ya está hecha).

Las pestañas viven en `_tab_flota`, `_tab_motor`, `_tab_auditoria` y `_tab_casos`;
la barra lateral en `_sidebar` y el sandbox de estrés en `_sandbox_estres`. El
dashboard las importa con `from app.ui import ...`.

- `_sha256_cached` se reexporta desde `app.lib.ui_data_loader` (única definición en `app/`).

Los imports de aquí nunca cargan TensorFlow: el dueño re-exporta
`_sha256_cached` desde `app.lib.ui_data_loader`, que importa pandas, numpy y
Streamlit (para cachear la lectura), no TensorFlow.
"""
from __future__ import annotations

from app.lib.ui_data_loader import _sha256_cached as _sha256_cached

__all__ = ["_sha256_cached"]
