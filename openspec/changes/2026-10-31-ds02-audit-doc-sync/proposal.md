# Change: sincronización documental tras la auditoría 2026-10-31 (bundle B)

**Capability:** `rul-prediction-ds02` (documentación y contrato legible; el artefacto
no se toca) y `ds02-dss-ui` (una línea de docstring).
**Type:** docs-only + docstring-only. Ningún cambio de comportamiento, ninguna
métrica alterada, ningún artefacto reescrito.

## Why

La auditoría file-by-file (`docs/informes/informe-auditoria-2026-10-31.md`)
dio código 10/10 y proyecto 9/10. Las 8 incidencias son papeles
desincronizados del bundle B (adoptado 2026-10-26, `ensemble 7acba335…`):
el README mezcla tres generaciones de cifras, `AGENT.md` describe el experimento
FD001, `openspec/project.md` conserva el párrafo del fallback ya eliminado por
el change `2026-10-20-ds02-honest-deployable`, y hay restos sin señalizar
(duplicados en raíz, notebooks legados, 14915 vs 17450).

## What changes

1. `README.md`: tablas etiquetadas por revisión con una sola fila vigente
   (bundle B: RMSE 4.251 / MAE 3.183 / R² 0.9482 / NASA 2305.1; macro 4.8433);
   línea de ablación "shipped 4.301" → bundle B; notas de legados
   (`notebook_nasa_fd001.ipynb`, `app/dashboard.py`), duplicados en raíz
   (canónico: `models/`) y 14915 vs 17450.
2. `AGENT.md`: Python 3.12.10, cifras DS02 bundle B, misma estructura.
3. `openspec/project.md`: el loader **lanza** si falta el HDF5 (fallback
   eliminado, no "dead code"); `openspec/config.yaml`: persistencia canónica
   en `models/` (copias de raíz ignoradas por git).
4. `src/ds02_rul/metrics.py`: docstring 4.26/4.88 → 4.2515/4.8433 (comentario).
5. `app/dashboard.py`: cartel de legado en el docstring (comentario).
6. Commit local (sin push) de los 7 ficheros + `MLProyectVault/07-…` (116 KB)
   + este change + informe. Modelos, caché, notebooks y `archive/` intactos.

## Out of scope (declarado, no olvidado)

- Partir `dashboard_ds02.py` (3595 líneas): funciona y está testeado; partirlo
  es riesgo sin beneficio medible. Backlog en `docs/pendiente/`.
- `docker build`: el daemon no está disponible en este entorno
  (`docker info` falla); `docker compose config` ya valida. Pendiente de una
  máquina con daemon.

## Byte-compatibility

`models/*`, `app/cache/*`, `*.ipynb`, `archive/*`: sin cambios (verificado por
`git status` en la fase verify). `predict()` y la suite: idénticos.

## Rollback

`git revert` del commit local: solo toca `.md`, dos docstrings y añade el change.
Sin migraciones ni artefactos.
