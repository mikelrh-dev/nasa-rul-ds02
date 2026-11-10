# MLflow PIA-4 a 10/10 (sin runs sobrantes)

## Objetivo

Cerrar PIA-4 (20 % de PIA) en 10/10 y dejar el store `mlruns/` curado y reproducible
desde un clon limpio: 17 runs históricos (9 fila + 4 ventana + 4 ablación), sin runs
`live__*` ni tombstones.

## Problema

- La ablación `cyc_norm` existe, pero solo como 24 runs `live__nb03_*` con `run_key`
  aleatorio (`hash()`), fuera del export y de las capturas. `grep cyc_norm` en
  `meta.yaml` da 0 porque la variante vive en `params/variant`.
- El store commiteado tiene 28 run dirs, todos `deleted`/ausentes: un clon limpio
  tiene 0 runs activas.
- El experimento `ds02-clase` mezcla 13 runs curados con 68 runs live y 26 tombstones.

## Fuente autoritativa

Sesión 2026-11-09 17:22 de `notebooks/03_feature_engineering_secuencial.ipynb`
(sus métricas coinciden con el output guardado del notebook). Sin re-ejecutar el
notebook ni tocar su código.

## Tareas

- [ ] T1. `resultados/ablacion_cycnorm.csv` desde los runs live de la sesión 17:22.
- [ ] T2. `scripts/backfill_mlflow.py`: 4 runs `ablacion__*`, `N_RUNS=17`, export con
      `metrics_json`, `--check` con desglose 9+4+4.
- [ ] T3. `tests/test_mlflow_backfill.py`: 17 runs, granos 9/4/4, `OK: 17 runs`.
- [ ] T4. Store: `--write`, purga de live y tombstones, `--check` verde.
- [ ] T5. README, README.en y guiones: conteos y tabla de ablación alineados.
- [ ] T6. Suite completa + commit por unidad de trabajo.

## Criterios de aceptación

- `python scripts/backfill_mlflow.py --check` → `OK: 17 runs (9 fila + 4 ventana + 4 ablación)`.
- `git status --porcelain mlruns` → 0 rutas sucias tras el commit.
- `grep -ril cyc_norm mlruns --include=params/*` ≥ 1.
- Suite verde (baseline 444 passed, 1 skipped).
