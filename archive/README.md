# archive/ — lo que el proyecto ya no usa

Solo queda el punto de restauración del bundle B (histórico, **NO vigente**) y su
evidencia mínima. Nada de aquí lo importa ni lo ejecuta `src/`, `mia/`, `app/` ni
los tests vivos.

| Ruta | Qué es |
|---|---|
| `models_b/` | los 4 artefactos de B (`ensemble.joblib`, `bilstm_ds02.keras`, `scaler.joblib`, `ds02_manifest.json`) con sus hashes; lo cita `models/ds02_manifest.json → historical_reference` y el rollback de ADR-011 |
| `cache_b/cache_manifest.json` | manifiesto de caché de B, necesario para el rollback de ADR-011 |
| `tests/test_clase_b_robusto.py` | evaluador de B archivado (no lo colecta pytest: `testpaths = ["tests"]`) |

El resto de `archive/` (374 ficheros, 214 MB: notebooks legados, FD001 legacy,
sondas `probe_*`, `RequisitosClase/Ejemplos/`, `CCMaps/`) se retiró el
**2026-11-09** a un backup externo, fuera del repo y fuera de git:

`~/Documents/backup-archive-nasa/archive-2026-11-09.zip` + `MANIFEST.txt`
(sha256 y tamaño por fichero; rutas relativas a la raíz del repo).
