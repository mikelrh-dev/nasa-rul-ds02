# Deuda diferida: hallazgos de riesgo 7 (auditoría 2026-11-10)

Rama: `fix/auditoria-2026-11-10` (base `mlflow-pia4`, HEAD `025dcb2`).
Estado: **no ejecutados**. Se aplicaron el resto de hallazgos (C1, M1–M7, A1-A, A2–A4,
B1–B4, B6). Estos dos quedan para revisión del 2026-11-11 por su radio de impacto.

Invariante que ninguno de los dos puede romper: `models/ensemble.joblib`,
`models/bilstm_ds02.keras` y `models/scaler.joblib` (bundle C, desplegado) siguen
siendo los servidos, con métricas 4.338 / 3.227 / 0.9461 / 2336.2 sobre 6.196
ventanas y 12.538 filas.

---

## A1-B — Repuntar el alias `models/mejor_modelo.joblib` al mejor de fila (E2)

**Qué cambiaría.** `genai/assets/train_clasicos.py` escribe hoy `mejor_modelo.joblib`
como copia del mejor **clásico** (XGB, `rmse_val` 8.2173). A1-B propone que el alias
pase a ser copia de `models/mejor_modelo_clase_E2.joblib` (MLP, `rmse_val` 7.3404),
que es el mejor de fila por validación.

**Por qué riesgo 7.**

- `PIA-3` y `notebooks/02_*` cargan `models/mejor_modelo.joblib` y asumen un
  `Pipeline` con `XGBRegressor`; con E2 el estimador final es `MLPRegressor` y
  cualquier `get_feature_importance()`/atributo de XGB falla en tiempo de ejecución.
- Cambia el artefacto que la rúbrica SAA-9 identifica como "mejor modelo", sin
  cambiar las métricas del desplegado: el riesgo es de **defensa**, no de serving.
- Obliga a regenerar `models/README.md`, la tabla de campeones y el hash de
  cualquier checksum que lo cubra (`scripts/make_clase_checksums.py`).
- El bundle C no se toca, pero un lector puede concluir que "el mejor modelo"
  del repo es el que se sirve; hoy eso ya se aclara con la tabla de tres campeones.

**Qué se hizo en su lugar (A1-A).** Se documentaron los tres campeones y su
criterio en `models/README.md` y en `README.md`, y se fijó por test en
`tests/test_clase_rubrica.py::test_tres_campeones_no_se_confunden`:

| Grano | Artefacto | Criterio |
|---|---|---|
| mejor clásico (fila) | `mejor_modelo_clase.joblib` + alias `mejor_modelo.joblib` | menor `rmse_val` de los 5 clásicos (XGB, 8.2173) |
| mejor de fila (todos) | `mejor_modelo_clase_E2.joblib` | menor `rmse_val` global en fila (MLP E2, 7.3404) |
| desplegado (ventana) | `ensemble.joblib` | campeón congelado C (4.338) |

**Plan si se aprueba.**

1. `train_clasicos.py`: escribir `mejor_modelo.joblib` desde el ganador de fila,
   con un flag explícito (`--alias-mejor-fila`) para no cambiar el default.
2. Buscar consumidores de XGB sobre el alias: `grep -rn "mejor_modelo.joblib"`.
   Adaptar `PIA-3`/`NB02` para leer `mejor_modelo_clase.joblib` (nombre exacto del
   clásico) en vez del alias.
3. Regenerar checksums (`scripts/make_clase_checksums.py`), actualizar
   `models/README.md` y la tabla de campeones del `README.md`.
4. Criterio de aceptación: `pytest tests/test_clase_rubrica.py tests/test_joblib_guard.py -q`
   en verde y `models/ds02_manifest.json` sin cambios de métricas.

**Rollback.** `git checkout -- models/mejor_modelo.joblib` y revertir el flag.

---

## B5 — Desversionar `mlruns/`

**Qué cambiaría.** Hoy el store tiene 17 runs versionados en `mlruns/` (9 fila +
4 ventana + 4 ablación; sin `live__*` ni tombstones). B5 proponía `git rm -r --cached mlruns`
+ añadir `mlruns/` a `.gitignore`, dejando la evidencia MLflow fuera del repo. **No se
ejecutó:** el 2026-11-10 se eligió la opción contraria, versionar el store de texto.

**Por qué riesgo 7.**

- `tests/test_mlflow_backfill.py` espera runs
  versionados; `scripts/backfill_mlflow.py --check` reporta hoy 17 runs (9 fila + 4 ventana +
  4 ablación) por `fuente=historico`. Desversionar los dejaría en 0 y esos tests fallarían.
- La evidencia de tracking es parte del entregable de la defensa (comparativa de
  experimentos en `docs/evidencia/mlflow/comparativa.csv`); sacarla del repo
  obliga a definir dónde vive (artefacto comprimido, release, Drive) antes de
  borrarla.
- Un `git rm --cached` mal ejecutado con `-r` sobre el patrón equivocado puede
  arrastrar `models/` o `app/cache/`; el riesgo es de pérdida de artefactos, no
  solo de tests.

**Plan si se aprueba.**

1. Congelar la evidencia: `tar -czf evidencia-mlflow-2026-11-10.tar.gz mlruns/` y
   publicarla como artefacto (release o almacenamiento acordado). Verificar que el
   archivo abre y contiene los 109 `meta.yaml`.
2. `git rm -r --cached mlruns` (nunca sin `--cached`), añadir `mlruns/` a
   `.gitignore` y comprobar con `git status` que solo salen bajas de `mlruns/`.
3. Reescribir `tests/test_mlflow_backfill.py` y `test_mlflow_ui.py` para sembrar un
   `mlruns/` temporal (`tmp_path`) en vez de depender del árbol versionado, y
   ajustar `--check` a la expectativa 0.
4. Criterio de aceptación: suite completa en verde con `mlruns/` ausente del índice,
   y `git ls-files mlruns | wc -l` = 0.

**Rollback.** `git checkout HEAD -- mlruns` restaura el índice y el árbol desde el
commit; la copia comprimida cubre el caso de que ya se haya limpiado el working tree.
