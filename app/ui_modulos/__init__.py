"""Facade del paquete `ui_modulos` (el split ya esta hecho).

Las pestanas viven en `_tab_flota`, `_tab_motor`, `_tab_auditoria` y `_tab_casos`;
la barra lateral en `_sidebar` y el sandbox de estres en `_sandbox_estres`. El
dashboard las importa con `import ui_modulos as UM`.

- `_sha256_cached` se re-exporta desde `ui_data_loader` (unica definicion en `app/`).

Los imports de aqui nunca cargan TensorFlow: el dueno solo usa pandas, numpy y la
capa de reglas.
"""
from __future__ import annotations

try:
    from ui_data_loader import _sha256_cached as _sha256_cached
except ImportError:  # pragma: no cover - import-style fallback
    from app.ui_data_loader import _sha256_cached as _sha256_cached  # type: ignore[no-redef]

__all__ = ["_sha256_cached"]
