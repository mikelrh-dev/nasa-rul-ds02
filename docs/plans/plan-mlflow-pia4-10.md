# Plan MLflow · PIA-4 al 10 sin reentrenar

Fecha: 2026-11-07 · Revisión 2 (sustituye a la v1 del mismo día)
**Estado: PLAN CERRADO — NO EJECUTADO.** Decisión: planificar ahora, ejecutar después.
Verificación de "no ejecutado" al pie (§14). Nada de este documento se ha aplicado al árbol.

- **Objetivo:** llevar PIA-4 (MLflow, 20 % de PIA) de 0 a 10 y, con el mismo trabajo,
  cerrar PIA-1 y SAA-3. Sin reentrenar, sin mover cifras, sin tocar el manifiesto.
- **Resultado esperado:** PIA 7,70 → **10,00** · SAA 9,90 → **10,00**.
- **Coste estimado:** 3–4 h. **Riesgo:** 3/10 (de evidencia, no de instalación).

---

## 1. La rúbrica, literal

PIA criterio 4 «Registra los experimentos en MLflow», peso **20 %** de la asignatura:

| Nivel | Texto de la rúbrica |
|---|---|
| 0 | No usa MLflow |
| 3 | Solo algunos modelos |
| 7 | Todos los modelos y experimentos, con hiperparámetros y métricas |
| 10 | **Además compara los modelos en MLflow y lo enseña con capturas** |

Pesos PIA: README/documentación 10 % · carpetas y funciones 10 % · pipeline sklearn 20 % ·
**MLflow 20 %** · app Streamlit 25 % · pregunta individual 15 %. Suman 100, se calcula directo.

Además, la parte de SAA exige en el README una «**tabla comparativa sacada de MLflow** …
con una captura de MLflow» y el apartado 6 del README «tabla con los modelos y sus
métricas **sacada de MLflow**». Es decir: la tabla no puede ser un CSV transcrito a mano.

### Aritmética que decide el alcance

| Escenario | PIA-1 README | PIA-4 MLflow | PIA |
|---|---|---|---|
| Hoy | 7 | 0 | **7,70** |
| Solo MLflow | 7 | 10 | **9,70** |
| MLflow + README | 10 | 10 | **10,00** |

**Implementar MLflow sin tocar el README deja la asignatura en 9,7, no en 10.** El
«techo 8,0» de `auditoria-2026-11-06-reto1-v2.md:22` es el techo *suponiendo* README a 10;
hoy el techo efectivo es 7,7. Por eso PIA-1 entra en este plan.

---

## 2. Qué cambia respecto a la v1

La v1 acertaba la lectura de la rúbrica (7 vs 10) y la decisión de no reentrenar.
Se corrigen cinco cosas:

| # | v1 | v2 (este plan) |
|---|---|---|
| 1 | 15 runs (enumeraba 16) | **10 runs**, todos con params probados |
| 2 | Store «como está» | **store versionado** + artefactos ignorados + export a `docs/` |
| 3 | Solo PIA-4 | **PIA-4 + PIA-1 + SAA-3** en el mismo change |
| 4 | Prosa con ROI | tareas con acceptance, invariantes y rollback (forma SDD) |
| 5 | No menciona superficies que dicen «MLflow fuera» | **7 superficies** a actualizar en el mismo change |

---

## 3. Inventario de evidencia disponible

Todo sale de ficheros ya medidos. `resultados/` está ignorado por diseño
(`.gitignore:108`), así que **se lee, no se versiona**; el export va a `docs/`.

| Fuente | Filas | Hiperparámetros | Métricas | Tiempo | ¿Sirve? |
|---|---|---|---|---|---|
| `resultados/comparativa.csv` | 5 | ✅ `mejores_params` | train+val (+test solo xgb) | ✅ `tiempo_s` | **Sí, 5 runs** |
| `resultados/mlp_comparativa.csv` | 4 | ✅ `params` | train+val | ✅ `tiempo_s` | **Sí, 4 runs** |
| `models/ds02_manifest.json` | 1 | ⚠️ seed + SHA (no hiperparams) | ✅ oficial 4 filas | — | **Sí, run de producción** |
| `resultados/comparativa_bundle_c.csv` | 4 | ❌ solo model+grano | ✅ | ❌ | No como run |
| `resultados/bundle_c_multiseed.csv` | 2 | ❌ solo `seed` | ✅ | ❌ | No como run |
| `resultados/bundle_c_por_motor.csv` | 3 | ❌ | ✅ RMSE | ❌ | No como run |
| `resultados/comparativa_ventanas.csv` | 1 | ❌ | ✅ | ✅ | No como run |
| `resultados/tabla_final_clase.csv` | 13 | ❌ | ✅ | ✅ | No como run |

**Regla dura: un run sin hiperparámetros no se loguea.** El nivel 7 exige «con
hiperparámetros y métricas»; un run sin params es evidencia de cartón y resta si el
tribunal lo abre.

---

## 4. Los 10 runs

Experimento único `ds02-clase`. Tag `grano` separa las dos ligas: **no son comparables
entre sí** (fila vs ventana) y mezclarlas en una tabla sería una afirmación falsa.

### Liga `grano=fila` · 9 runs de comparación

| # | Run | `familia` | Params (verificados) | `tiempo_s` | RMSE val |
|---|---|---|---|---|---|
| 1 | `regresion` | clasico | `reg__alpha=10.0` | 3,5 | 8,2762 |
| 2 | `knn` | clasico | `reg__n_neighbors=31` | 9,1 | 9,4092 |
| 3 | `rf` | clasico | `reg__max_depth=8` | 79,6 | 9,0704 |
| 4 | `svm` | clasico | `reg__C=10.0`, `reg__epsilon=1.0` | 2,7 | 8,2927 |
| 5 | `xgb` | clasico | `reg__max_depth=4` | 7,2 | 8,2173 |
| 6 | `mlp_base` | mlp | `hidden=(128,64)`, `alpha=0.001` | 27,5 | 7,3580 |
| 7 | `mlp_E1_capacidad` | mlp | `hidden=(256,128,64)`, `alpha=0.001` | 70,7 | 7,4808 |
| 8 | `mlp_E2_reg_lr` | mlp | `hidden=(128,64)`, `alpha=0.01` | 33,3 | 7,3404 |
| 9 | `mlp_E3_batch` | mlp | `hidden=(128,64)`, `alpha=0.001`, `batch_size=1024` | 38,6 | 7,3554 |

Métricas por run: `rmse/mae/r2` en `train` y `val`; `rmse/mae/r2` en `test` cuando el CSV
lo trae (solo `xgb`). `tiempo_s` se loguea **como métrica** (la rúbrica pide el tiempo de
entrenamiento en la tabla).

### Liga `grano=ventana` · 1 run de producción

| # | Run | `rol` | Params | Métricas |
|---|---|---|---|---|
| 10 | `prod_bundle_c` | produccion | `seed=42`, `beta=1.00`, `ema=5`, `objetivo=rul`, 4 SHA (`ensemble_sha256`, `bilstm_sha256`, `clase_xgb_sha256`, `clase_e2_sha256`) | RMSE 4,338 · MAE 3,227 · R² 0,9461 · NASA 2336,2 |

- `v3_bundle_sha256` **no** se loguea como param: apunta a un fichero archivado
  (hallazgo C-01). Se registra como tag `v3_bundle=archivado`.
- Tag `origen=manifiesto`. Este run es el «modelo elegido y por qué» que pide la rúbrica.

### Fuera del alcance (y por qué)

- **Semillas 7 y 123, componentes del bundle C, 13 filas de `tabla_final_clase`**: no
  aportan criterio y la mayoría no tiene params. Se quedan como CSV.
- **LGBM**: sus hiperparámetros no están literales en `src/clase/*.py`; habría que
  rastrearlos. Condicional en T7: si se prueban desde el manifiesto/README, entra como
  run 11 con tag `origen=historico`; si no, se declara su ausencia y no se inventa.

---

## 5. Política de evidencia (lo que decide si el 10 es real o de cartón)

1. **El store se versiona.** `mlruns/` con `meta.yaml`, `params/`, `metrics/` y `tags/`
   de los 10 runs son ficheros de texto (~100 KB). Sin ellos, los `run_id` que cite el
   README no existen en un clon: sería el hallazgo A-01 con otro nombre.
2. **Artefactos y papelera, ignorados.** `.gitignore` añade `mlruns/**/artifacts/` y
   `mlruns/.trash/`. No se usa `log_model` (skops escribiría binarios): solo params,
   métricas y tags.
3. **Export versionado, no en `resultados/`.** `resultados/` está ignorado; la tabla
   exportada va a **`docs/evidencia/mlflow/comparativa.csv`**, generada desde la API, no
   escrita a mano. Ese CSV es el que se pega en el README.
4. **Capturas versionadas** en `docs/evidencia/mlflow/`:
   - `compare.png` — vista de **comparación multi-run** con la columna de tiempo visible
     (es lo que pide el nivel 10: «compara los modelos en MLflow»).
   - `run_prod.png` — detalle del run de producción con params y SHA.
   `docs/assets/` ya está versionado (9/9 PNG), así que la captura no rompe en un clon.
5. **Captura de la app, nueva.** El README actual dice que la anterior «mostraba cifras
   que ya no existen»; hay que recapturar desde `app/dashboard_ds02.py`.

---

## 6. Tareas

| # | Tarea | Ficheros | Acceptance | Riesgo |
|---|---|---|---|---|
| T1 | Pin de dependencia | `requirements.txt`, `pyproject.toml` | `mlflow==3.18.0`; `pip install` no mueve numpy 2.5.4 / pandas 3.0.6 / sklearn / TF (dry-run ya verificado); `pip check` exit 0 | 1 |
| T2 | Política de store | `.gitignore` | añade `mlruns/**/artifacts/` y `mlruns/.trash/`; `git status` no lista binarios | 0 |
| T3 | Backfill | `scripts/backfill_mlflow.py` (nuevo), `--write/--check` (0/2) | 10 runs; params con `ast.literal_eval` y aplanado de `reg__*`; rechaza `None`/`NaN`; idempotente; `--check` compara params+métricas, no `run_id` | 3 |
| T4 | Run de producción | mismo script | 4 SHA + seed + beta + EMA5; `v3_bundle=archivado` como tag; métricas = `reference_row` | 1 |
| T5 | Export + capturas | `docs/evidencia/mlflow/` (nuevo) | `comparativa.csv` con una fila por run y `run_id`; 2 PNG; tabla ordenada por `grano` | 2 |
| T6 | README (PIA-1 + SAA-3) | `README.md`, `README.en.md` | captura de app arriba; tabla de campos con % nulos + campos quitados y por qué; tabla MLflow + captura + elección | 3 |
| T7 | LGBM condicional | `scripts/backfill_mlflow.py` | si params probados → run 11; si no → nota explícita, sin run | 2 |
| T8 | Test sin servidor | `tests/test_mlflow_backfill.py` (nuevo) | lee el store de disco; 10 runs con params+métricas+tiempo; CSV exportado == store; **sin skips** (la dependencia está declarada) | 3 |
| T9 | Superficies y docs | 7 ficheros (§13) + `c27`, `s14`, `openspec/config.yaml` | ninguna dice «MLflow fuera»; el guion de defensa puede demostrarlo | 2 |

**Nota de implementación (T3):** `mejores_params` es un dict en texto con comillas
simples → `ast.literal_eval`, aplanar `reg__x` → `x`, y `hidden_layer_sizes` → string
`128-64`. La columna `hipotesis` del MLP va como **descripción del run**, no como param.

---

## 7. Verificación al ejecutar (no ejecutada)

```bash
.venv/Scripts/python.exe -m pip install -r requirements.txt     # sin downgrades
.venv/Scripts/python.exe -m pip check                           # 0
.venv/Scripts/python.exe scripts/backfill_mlflow.py --write     # 0
.venv/Scripts/python.exe scripts/backfill_mlflow.py --check     # 0
.venv/Scripts/python.exe -m pytest tests/test_mlflow_backfill.py -q -rs   # 0, 0 skips
.venv/Scripts/python.exe -m pytest tests -q -rs                 # 0, 0 skips
.venv/Scripts/python.exe scripts/freeze_rules_evidence.py       # 0
.venv/Scripts/python.exe scripts/freeze_oof_instrument.py --check  # 0
git status --short                                              # sin binarios
```

---

## 8. Invariantes byte-compatibles

Ninguna tarea de este plan toca estos artefactos. Si alguno cambia, el plan está mal
ejecutado y se revierte.

| Artefacto | Valor que debe seguir igual |
|---|---|
| `models/ds02_manifest.json` | `1085dd67…` (lo sella `tests/test_cache_drift.py`) |
| `models/ensemble.joblib` | `d6c70142…` |
| `models/bilstm_ds02.keras` | `bf9620a7…` |
| `src/mia/calibracion_banda.json` | bins `[5125, 6094, 3135, 561]`, `q_low` sin cambios |
| `app/cache/` | intacta (su sello apunta al manifiesto) |
| Cobertura de banda | 0,901643 |

---

## 9. Rollback

| Superficie | Reversión |
|---|---|
| Dependencia | quitar la línea de `requirements.txt` y `pyproject.toml` |
| Código | borrar `scripts/backfill_mlflow.py` y `tests/test_mlflow_backfill.py` |
| Store | borrar `mlruns/` (no versionado hasta el commit) |
| Export y capturas | borrar `docs/evidencia/mlflow/` |
| README | revertir las 3 secciones (captura, campos, tabla MLflow) |
| `.gitignore` | quitar 2 líneas |

Riesgo de rollback ≈ 0: no hay migración de datos ni artefacto de modelo implicado.

---

## 10. Riesgos

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| Runs sin params → criterio en 7, no 10 | media | alto | 10 runs con params probados; T7 condicional |
| `run_id` huérfanos en un clon | alta si no se versiona | alto | store versionado + test que lo lee de disco |
| 33 paquetes nuevos (docker, gitpython, sqlalchemy) | cierta | bajo | pin exacto, `pip check`, sin `log_model` |
| La tabla mezcla granos y afirma de más | media | alto | tag `grano` y dos bloques separados |
| El guion de defensa sigue diciendo «fuera» | cierta si se olvida T9 | alto | T9 en el mismo change |
| Captura caduca al mover la app | media | bajo | recapturar al cerrar; pie con fecha |

---

## 11. Alternativas rechazadas

- **Reentrenar para generar runs en vivo**: TF no determinista mueve el 4,338 y rompe
  `test_cache_drift`. Rechazada.
- **Backfill de 16 runs** (v1): la mitad sin hiperparámetros; infla sin acreditar.
- **`mlflow server` o backend sqlite**: innecesario para 10 runs; añade proceso y estado.
- **`log_model`**: skops escribe binarios y duplicaría el bundle.
- **Export a `resultados/`**: está ignorado; no sobrevive a un clon.
- **Inventar params de LGBM/híbrido**: prohibido; T7 es condicional.

---

## 12. Fuera de alcance

n8n (MIA-3), respuesta individual, reentrenamiento, cambios en notebooks, en el
manifiesto, en la banda o en el bundle. Nada de eso se toca aquí.

---

## 13. Superficies que hoy dicen «MLflow fuera» (actualizar en T9)

1. `docs/chuleta-defensa.md:51` — «no los vendas como hechos».
2. `docs/defensa/guiones-15min.md:4` y `:124` — «pendiente, declarado en README».
3. `docs/presentacion/presentacion-ds02.html:19, 562, 659, 683` — «MLflow fuera» (×4).
4. `MLProyectVault/10-Conceptos/c27-mlflow.md` — estado «pendiente».
5. `MLProyectVault/20-Sistema/s14-app-y-despliegue.md` — pendiente declarado (y residuo
   de Docker que hay que limpiar aparte: sigue citando `Dockerfile`).
6. `openspec/config.yaml` — nota de alcance.
7. `README.md` / `README.en.md` — resultados.

Si alguna se queda atrás, la defensa se contradice con el repo.

---

## 14. Estado: no ejecutado (verificado)

Comprobado al cerrar este documento:

| Comprobación | Resultado |
|---|---|
| `python -c "import mlflow"` | `ModuleNotFoundError` |
| `ls mlruns/` | no existe |
| `grep -c mlflow requirements.txt pyproject.toml` | `0` y `0` |
| `docs/evidencia/` | no existe |
| Artefactos de modelo | sin cambios |

**Al ejecutar**, este plan se promueve a `openspec/changes/<fecha>-mlflow-pia4/` con
proposal, tasks con acceptance, delta de spec y rollback. Aquí queda la decisión, el
alcance y la evidencia que lo sostiene.

## Prerrequisitos ajenos a este plan

- **A-01**: `src/mia/instrumento_oof.npz` sin trackear (afecta al change de la banda, no
  a este, pero deja el repo sin instrumento en un clon).
- **C-01**: `scripts/predict.py:24` apunta a `models/v3_bundle.joblib`, ya archivado.
  Por eso `v3_bundle_sha256` va como tag `archivado`, no como param.
- **`docs/pendiente/plan-cierre-rubrica.md`** está obsoleto (rama `clase-experimental`,
  PIA 6,7, «sin MLflow») y contradice a este plan: marcarlo como superado.
