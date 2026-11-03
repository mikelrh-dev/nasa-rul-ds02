# archive/ — lo que el proyecto ya no usa (orden, no borrado)

Zona git-ignorada y de solo lectura: nada de aquí lo importa, ejecuta o cita
como vivo ningún test, notebook 01–06, `src/`, `mia/` ni `app/`.
Se conserva por trazabilidad histórica; **no re-ejecutar nada de aquí**.

## Mapa (de dónde vino cada cosa)

| Carpeta | Contenido | Motivo |
|---|---|---|
| `02_DS02_ensemble_RUL.ipynb`, `notebook_nasa_fd001.ipynb` | Notebooks congelados de referencia (raíz) | Sustituidos por `notebooks/01–06` + `notebooks/ds02_ensemble/01–03` |
| `notebooks-legado/` | `notebooks/backup/` (01_eda, 02_modelos_A/B, 04_lgbm, 05_ensemble) + `motorReglasEjemplo/practica_reglas.ipynb` | Originales previos a la secuencia 01–06; ejercicio de ejemplo |
| `app-legado/` | `app/dashboard.py` | Tablero legacy roto (falla al renderizar); lo sustituye `app/dashboard_ds02.py` vía `app/streamlit_app.py` |
| `scripts-fd001/` | ~50 ficheros: builders FD001 (`finalize_*`, `rebuild_v2`, `v2_*`, `update_v2_cells`, `add_v3_notebook`), sondas `probe_*`, `test_*` de un uso, logs y `.npy` | Experimentos ya registrados; lo vivo sigue en `scripts/` (ver abajo) |
| `scratch/` | Logs de ejecución y scripts `fix_*` puntuales | Tránsito de depuración |
| `CCMaps/` | Muestra de 100 datos | Ya estaba aquí |

## Lo que se queda FUERA (vivo, no mover)

- `notebooks/ds02_ensemble/artifacts/` — NB03–06 los cargan (`ART/nb1_dev.npz`…).
- `models/legacy/` — punto de restauración citado en openspec.
- `scripts/` vivos: `predict.py` + `v3_core.py` (pinneados por spec, FD001),
  `predict_ds02.py`, `build_ui_cache.py`, `freeze_rules_evidence.py`,
  `p1_oof_cache.py`, `ablate_meta_cycle.py`, `p0_density_control.py`,
  `p1_meta_support.py`, `verify_gate.py`, `verify_blend.py`,
  `repackage_artifact.py`, `build_02_notebook.py`, `evaluate_model_quality.py`.
