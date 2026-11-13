"""Único dueño de las rutas del repositorio para `app/`.

Cada módulo solía derivar sus rutas de `__file__` (`dirname(abspath(__file__))`),
de modo que mover un módulo movía la caché y los registros con él. Este módulo
se ancla a una constante de raíz — `Path(__file__).resolve().parents[1]`, ya
que vive en `app/` — y el resto de `app/` importa de aquí.

Regla: **ningún otro módulo de `app/` vuelve a escribir esa aritmética.** El
siguiente movimiento de paquetes (Fase 4) mueve los módulos y estas rutas
siguen apuntando al mismo sitio.

Los valores son los de antes del movimiento, sin redondeos: `ROOT` es la raíz
del repositorio, `APP_DIR` el directorio `app/`, `CACHE_DIR` la caché versionada
(`ds02_windows.parquet`, `ds02_rows.parquet`, `cache_manifest.json`), y los
registros (`registros_flota.json`, `registros_sesiones/`)
viven junto a `app/`.
"""
from __future__ import annotations

from pathlib import Path

# Raíz del repositorio: `_paths.py` vive en `app/`, así que parents[1] es la raíz.
ROOT: Path = Path(__file__).resolve().parents[1]
APP_DIR: Path = ROOT / "app"

# Caché de solo lectura construida por `scripts/build/build_ui_cache.py`.
CACHE_DIR: Path = APP_DIR / "cache"
WINDOWS_PATH: Path = CACHE_DIR / "ds02_windows.parquet"
ROWS_PATH: Path = CACHE_DIR / "ds02_rows.parquet"
PROVENANCE_PATH: Path = CACHE_DIR / "cache_manifest.json"

# Contrato congelado del artefacto (solo lectura).
MANIFEST_PATH: Path = ROOT / "models" / "ds02_manifest.json"
ARTIFACT_PATH: Path = ROOT / "models" / "ensemble.joblib"

# Árbol de código fuente (paquetes `src.ds02_rul`, `src.mia`, ...).
SRC_DIR: Path = ROOT / "src"

# Registros de flota: el legacy `registros_flota.json` y las sesiones.
REGISTROS_PATH: Path = APP_DIR / "registros_flota.json"
SESIONES_DIR: Path = APP_DIR / "registros_sesiones"

# Secretos de Streamlit (no versionados; `streamlit_app.py` los carga a os.environ).
SECRETS_PATH: Path = ROOT / ".streamlit" / "secrets.toml"
