# scripts/ — vigente vs legacy

## Vigente (se usa)

- `build_ui_cache.py` — genera `app/cache/` (ventanas demo + provenance).
- `freeze_rules_evidence.py` — evidencia congelada de reglas (gate de tests).
- `predict_ds02.py` — inferencia CLI sobre el bundle.
- `build_02_notebook.py`, `build_05_notebook.py` — generan notebooks congelados de referencia.

## Legacy (no tocar, solo historia)

- `finalize_v2.py`, `finalize_v3.py`, `inspect_v2_v3.py`, `execute_baseline_cells.py`, `extract_legacy_artifact.py` — era FD001/v2-v3.
- `ablate_meta_cycle.py`, `p0_density_control.py`, `p1_*.py` — experimentos de un solo uso ya registrados.
- `ajustar_notebook.py`, `add_v3_notebook.py`, `dump_cells.py`, `inspect_cells.py`, `build_and_run_notebook.py` — utilidades de edición de notebooks.
- `*.npy`, `nb_exec_v4*.log` — restos de ejecuciones (ignorados por git).
