# Pendiente: adopcion del bundle B (RESUELTO 2026-10-31 — adoptado)

Adopcion completada: 4 tests adaptados al bundle B, mia/casos.py actualizado (U14 ciclo 30 ahora HANGAR), cifras README/spec actualizadas. Suite verde.

Estado: ADOPTADO 2026-10-31. Bundle nuevo `ensemble 7acba335…`, `bilstm d0c5ed7f…`.
Baseline intacto en `git HEAD` (`ensemble 0acd795b…`) + backup `/tmp/ds02_backup_pre_refactor/`.
No commitear ni pushear hasta decidir.

## 1. Tests que hay que adaptar (4, todos frontera del bundle viejo)

| Test | Viejo | Nuevo observado | Acción |
|---|---|---|---|
| `tests/test_mia_rules.py::test_todos_los_casos_salen_BIEN` | U14 ciclo 30 = BIEN | `punto 35.159…` → deja de ser BIEN | Revisar `CASOS` y fijar el estado que el bundle nuevo defiende, con acta |
| `tests/test_simulacion.py::test_ciclos_hasta_fallo_coincide_con_la_cache` | `faltan[11] == 21` | `20` | Actualizar a `20` si la caché nueva lo confirma |
| `tests/test_ui_alta.py::test_el_modo_historia_se_deriva_de_la_cache` | `pasos[1] == (14, 8)` | `(14, 9)` | Actualizar a `(14, 9)` |
| `tests/test_ui_alta.py::test_el_paso_critico_cae_en_hangar_y_el_primero_no` | `estado(14, 8) == INSPECCION` | `APTO` | Actualizar a `APTO` o mover el ciclo de prueba |

Los 6 skips de `_p1_oof_cache.npz` son previos y no bloquean.

## 2. Papelada de cifras (obligatoria antes de defender con B)

- `README.md` (tabla + reproduce), `notebooks/ds02_ensemble/README.md`, `EVALUACION_EJECUCION.md`.
- `docs/informes/*` que citan `4.352/4.289/macro 4.9026` → nuevas: ref `RMSE 4.251, MAE 3.183, R2 0.9482, NASA 2305.1`; media `4.340±0.101`; macro `4.8433 (11:3.7874, 14:7.9974, 15:2.7451)`.
- `docs/02_DS02_ensemble_RUL_spec.md`, `openspec/*` que fijan hashes/cifras.
- `MLProyectVault/00-Guion-Defensa/00-cifras-autoritativas.md` + nodos con números (ya marcado como histórico).

## 3. Verificación final antes de commit

1. `git diff --stat -- models/ app/cache/` asumido y listado (será grande: `ensemble.joblib`, `bilstm_ds02.keras`, `scaler.joblib`, `ds02_manifest.json`, `app/cache/*`).
2. `.venv/Scripts/python -m pytest tests -q` → objetivo `217 passed, 0 failed` (6 skips previos aceptados solo si se regenera `_p1_oof_cache.npz` o se documentan).
3. `load_ensemble('models/ensemble.joblib')` en proceso limpio + `RELOAD OK` del NB03 (ya verde: `60.47 vs 58.00`).
4. `git status` revisado: solo entra `src/ds02_rul/viz.py`, 3 notebooks, `models/`, `app/cache/`, docs de cifras y este plan.

## 4. Rollback (opción A, una orden)

```bash
git checkout -- notebooks/ src/ models/ app/cache/
cp /tmp/ds02_backup_pre_refactor/models/* models/
cp /tmp/ds02_backup_pre_refactor/cache/* app/cache/
```

## 5. Decisión — ADOPTADO 2026-10-31 (acta cerrada)

- [x] Revisar notebooks reejecutados.
- [x] Elegir B (adaptar 4 tests + papelada). **ADOPTADO 2026-10-31**: bundle B en producción (ref 4.251; media 4.340 ± 0.101). Acta cerrada: sin rollback (opción A descartada). Bundle A (4.289 / sha `0acd795b…`) queda como histórico/pre-B, no vigente. No commitear ni pushear hasta orden explícita (según cabecera RESUELTO).
