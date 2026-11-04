"""Facade for the upcoming `ui_modulos` split (PR1 foundation).

Re-exports the helpers that are already unified, so future tab modules
(`sandbox_estres`, `tab_flota`, `tab_motor`, `tab_auditoria`) and the
dashboard orchestrator resolve the same objects without importing
`dashboard_ds02` (which would be circular).

- `_sha256_cached` is owned by `ui_data_loader` (one definition in `app/`).
- `PREFIJO_ALTA` is owned by `ui_alta` (one assignment in `app/`).

Imports here never load TensorFlow: both owners only use pandas,
numpy and the rules layer.
"""
from __future__ import annotations

import os
import sys

# Support both import styles: `import ui_modulos` (app dir on sys.path,
# how dashboard and tests load it) and `import app.ui_modulos` (repo
# root on sys.path, namespace package).
try:
    from ui_data_loader import _sha256_cached as _sha256_cached
except ImportError:  # pragma: no cover - import-style fallback
    from app.ui_data_loader import _sha256_cached as _sha256_cached  # type: ignore[no-redef]

try:
    from ui_alta import PREFIJO_ALTA as PREFIJO_ALTA
except ImportError:  # pragma: no cover - import-style fallback
    from app.ui_alta import PREFIJO_ALTA as PREFIJO_ALTA  # type: ignore[no-redef]

__all__ = ["_sha256_cached", "PREFIJO_ALTA"]
