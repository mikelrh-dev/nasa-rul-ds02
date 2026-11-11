"""Facade del paquete `app.ui` (el split ya esta hecho).

Las pestanas viven en `_tab_flota`, `_tab_motor`, `_tab_auditoria` y `_tab_casos`;
la barra lateral en `_sidebar` y el sandbox de estres en `_sandbox_estres`. El
dashboard las importa con `from app.ui import ...`.

- `_sha256_cached` se re-exporta desde `app.lib.ui_data_loader` (unica definicion en `app/`).

Los imports de aqui nunca cargan TensorFlow: el dueno solo usa pandas, numpy y la
capa de reglas.
"""
from __future__ import annotations

from app.lib.ui_data_loader import _sha256_cached as _sha256_cached

__all__ = ["_sha256_cached"]
