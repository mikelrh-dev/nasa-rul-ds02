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

---

## 15. Orden de ejecución decidido (2026-11-09)

**Decisión: MLflow primero, notebooks después.** El usuario reejecutará los 7
cuadernos para comprobar que todo funciona; eso no cambia el orden.

### Por qué antes y no después

1. **Los 10 runs no dependen de los notebooks.** `comparativa.csv` y
   `mlp_comparativa.csv` los escriben `src/clase/train_*.py`, no los cuadernos
   (NB02 entrena en vivo pero no exporta); el manifiesto no lo toca ningún
   notebook. Reejecutar después no invalida ningún run.
2. **El 20 % se cierra antes de gastar 2–3 h de cómputo.** Si el tiempo aprieta,
   lo urgente ya está bancado.
3. **El entorno se valida antes de los notebooks.** Se instalan 40 paquetes,
   se corre la suite (345) y después se ejecuta. Si algo falla al ejecutar, el
   sospechoso es el cuaderno, no la dependencia.
4. **El único retoque posterior es una línea**, no una segunda pasada de README:
   la media multiseed si NB06 reescribe `bundle_c_multiseed.csv`.

**No hacer** MLflow después para "loguear en vivo" desde los notebooks: añade
código a los cuadernos de evidencia, cambia `tiempo_s` frente al CSV y duplica
los modos de fallo. El backfill declarado es más defendible.

### Lo que sí hay que re-tocar después de ejecutar

| Superficie | Cuándo |
|---|---|
| `README.md` línea de 4.322 ± 0,064 | solo si NB06 cambia el CSV multiseed |
| `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md` | si cambia la media |
| `MLProyectVault/30-Notebooks/n0x` que cite cifras del rerun | si cambian |
| Capturas de app/MLflow | no: no dependen del rerun |

---

## 16. Protocolo seguro de re-ejecución (decidido por el usuario)

`notebooks/artifacts_c/` (2,7 MB) y `resultados/` (1,3 MB) están **git-ignored**:
un `git checkout` no los restaura. Antes de ejecutar:

```bash
git switch -c mlflow-pia4
cp -r notebooks/artifacts_c notebooks/artifacts_c.bak-2026-11-09
cp -r resultados          resultados.bak-2026-11-09
cp src/mia/instrumento_oof.npz src/mia/instrumento_oof.npz.bak-2026-11-09
sha256sum models/ensemble.joblib models/bilstm_ds02.keras \
          models/ds02_manifest.json src/mia/calibracion_banda.json \
          src/mia/instrumento_oof.npz > .pytest_cache/hashes-pre-notebooks.txt
.venv/Scripts/python.exe -m pytest tests -q -rs        # baseline: 345 passed
```

### Orden y puntos de control

| Paso | Notebook | Tras ejecutar comprobar |
|---|---|---|
| 1 | `01_eda_y_contexto` | 0 outputs de error; 6 PNG |
| 2 | `02_modelos_clasicos_y_mlp` | 0 errores; se rellenan los 2 `execution_count` nulos |
| 3 | `03_feature_engineering_secuencial` | 0 errores; 1 `execution_count` nulo relleno |
| 4 | `04_arquitectura_bilstm_oof` | 0 errores; `nb2_*` reescritos; `freeze_oof_instrument.py --check` y `freeze_rules_evidence.py` |
| 5 | `05_meta_ensemble_y_conformal` | 0 errores; lee los `nb2_*` del 04 |
| 6 | `06_evaluacion_produccion_comparativa` | 0 errores; **diff de `resultados/bundle_c_multiseed.csv`** |
| 7 | `07_shap_c_bundle_c` | 0 errores; figuras SHAP |

Comando por cuaderno (kernel `ds02-venv`, 2 h de margen):

```bash
.venv/Scripts/python.exe -m nbconvert --to notebook --execute --inplace \
  --ExecutePreprocessor.kernel_name=ds02-venv \
  --ExecutePreprocessor.timeout=7200 notebooks/0X_*.ipynb
```

**Parar en el primer error.** No continuar "para ver si el resto va".

### Qué se considera rotura y cómo se revierte

| Síntoma | Lectura | Reversión |
|---|---|---|
| Hash de `models/*` o manifiesto cambia | un notebook escribió donde no debía | restaurar desde git; el rerun no es la evidencia |
| `freeze_rules_evidence.py` exit != 0 | la banda ya no cuadra con el instrumento | restaurar `instrumento_oof.npz` y `calibracion_banda.json` del backup |
| `bundle_c_multiseed.csv` cambia | TF no determinista (esperado) | decidir: actualizar README/e00 **o** restaurar CSV y declarar el rerun. Nunca dejar las dos cifras |
| Un notebook falla por datos | falta parquet/HDF5 o ruta | no tocar el árbol; arreglar la causa antes de repetir |

Al final: `pytest tests -q -rs`, `freeze_rules_evidence.py`,
`freeze_oof_instrument.py --check` y `sha256sum -c` contra el snapshot previo.
Si los tres pasan y los hashes de `models/` no se movieron, el rerun es un
smoke test válido y no una segunda fuente de cifras.

---

## 17. Enmiendas al alcance v2 (obligatorias al ejecutar)

1. **Params del run de producción.** No dejar el run del bundle con solo seed/beta/EMA:
   loguear los que están literales (ventana 50, 93 features, cuantil 0.35, épocas si
   están escritas) y **declarar** los no registrados. Un run sin hiperparámetros lee
   como nivel 7, no 10.
2. **Dos capturas de comparación**, una por `grano` (`fila` / `ventana`), no una que
   mezcle 7,36 con 4,338.
3. **README:** columnas `rmse_val` y `rmse_test` explícitas; la tabla de clase actual
   es de test y la de MLflow es de validación. No renumerar tablas existentes.
4. **`requirements.txt`:** actualizar la cabecera (deja de ser solo «runtime que produjo
   los modelos») y `uv lock`, porque `uv.lock` está trackeado.

Coste revisado: **5–7 h** (no 3–4). Riesgo: **4/10** (consistencia documental, no
instalación; el dry-run de `mlflow==3.18.0` no mueve numpy/pandas/sklearn/TF).

---

## 18. Inventario cerrado de MLflow (sustituye §4: 17 runs)

> **Cierre 2026-11-10.** Este inventario recoge los 13 runs originales (9 fila + 4 ventana);
> el cierre de PIA-4 añadió 4 runs de ablación de `cyc_norm`, así que el store final tiene
> **17 runs** (9 fila + 4 ventana + 4 ablación).

**Experimento:** `ds02-clase`, con descripción y tags de entorno/datos a nivel de
experimento. **Nada de binarios, registry ni servidor.**

### Liga `grano=fila` · 9 runs (`origen=csv`)

| Run | `familia` | Params (literales del código/CSV) |
|---|---|---|
| `clasico__regresion` | clasico | `reg__alpha=10.0` |
| `clasico__knn` | clasico | `reg__n_neighbors=31` |
| `clasico__rf` | clasico | `reg__max_depth=8`, `n_estimators=200` |
| `clasico__svm` | clasico | `reg__C=10.0`, `reg__epsilon=1.0`, `subsample=5000`, `seed_subsample=42` |
| `clasico__xgb` | clasico | `reg__max_depth=4`, `n_estimators=300`, `learning_rate=0.05`, `subsample=0.8`, `colsample_bytree=0.8` |
| `mlp__base` | mlp | `hidden_layer_sizes=(128, 64)`, `alpha=0.001`, `batch_size=auto`, `activation=relu`, `learning_rate_init=0.001`, `max_iter=300`, `early_stopping=True` |
| `mlp__E1_capacidad` | mlp | `hidden_layer_sizes=(256, 128, 64)`, `alpha=0.001`, resto igual |
| `mlp__E2_reg_lr` | mlp | `hidden_layer_sizes=(128, 64)`, `alpha=0.01`, resto igual |
| `mlp__E3_batch` | mlp | `hidden_layer_sizes=(128, 64)`, `alpha=0.001`, `batch_size=1024`, resto igual |

| Run | RMSE/MAE/R² train | RMSE/MAE/R² val | Test | `tiempo_s` | Tag de selección |
|---|---|---|---|---|---|
| regresion | 8.2004 / 6.9054 / 0.8656 | 8.2762 / 7.6611 / 0.8502 | — | 3.5 | — |
| knn | 6.984 / 5.3739 / 0.9025 | 9.4092 / 8.1856 / 0.8181 | — | 9.1 | — |
| rf | 7.1572 / 5.7492 / 0.8977 | 9.0704 / 8.1534 / 0.827 | — | 79.6 | — |
| svm | 7.5251 / 5.8227 / 0.8869 | 8.2927 / 7.5299 / 0.8565 | — | 2.7 | — |
| xgb | 7.1887 / 5.9025 / 0.8968 | 8.2173 / 7.4688 / 0.8543 | 11.034 / 9.9098 / 0.6616 | 7.2 | `seleccion=mejor_clasico` · `test_lectura=unica` |
| MLP base | 5.7128 / 4.0254 / 0.9348 | 7.358 / 5.6405 / 0.8918 | — | 27.5 | — |
| MLP E1 | 5.2291 / 3.5858 / 0.9454 | 7.4808 / 5.7735 / 0.8882 | — | 70.7 | — |
| MLP E2 | 5.7249 / 4.0399 / 0.9345 | 7.3404 / 5.6481 / 0.8924 | 7.7211 / 5.8132 / 0.8343 | 33.3 | `seleccion=mejor_mlp,campeon_fila` · `test_lectura=unica` |
| MLP E3 | 5.7856 / 4.121 / 0.9331 | 7.3554 / 5.7035 / 0.8919 | — | 38.6 | — |

**Nota de selección:** son tres «elegidos» distintos y no se mezclan: XGB es el mejor
**clásico** (`mejor_modelo_clase.joblib`), E2 es el mejor **MLP** y campeón del grano
fila (7.3404 val), y el bundle C es el **desplegado** (4.338, grano ventana).

### Liga `grano=ventana` · 4 runs (`origen=comparativa_bundle_c + bundle_c_train.log`)

| Run | Params | Test (RMSE/MAE/R²/NASA) | `tiempo_s` | `rol` |
|---|---|---|---|---|
| `bundle__lgbm_c` | `objective=quantile`, `alpha=0.35`, `n_estimators=300`, `learning_rate=0.02`, `num_leaves=15`, `max_depth=4`, `min_child_samples=50`, `reg_alpha=1.0`, `reg_lambda=5.0`, `colsample_bytree=0.8`, `subsample=0.8`, `seed=42` | 7.067 / 5.545 / 0.857 / 5731.3 | 0.3 | `componente` · `alias=lgbm_adaptada` |
| `bundle__bilstm_c` | 2×BiLSTM(64), dropout 0.2, dense 32, input 50×19, Adam lr 0.001, Huber δ=10, `epochs=22`, `batch_size=128`, `early_stopping_patience=5`, `seed=42`, `n_params=154253` | 5.654 / 4.295 / 0.9084 / 3674.0 | 113.2 | `componente` |
| `bundle__bilstm_ema5` | `ema_span=5`, `base=bilstm_c` | 5.618 / 4.268 / 0.9096 / 3649.4 | — (no cronometrado) | `variante` |
| `prod__bundle_c` | `seed=42`, `beta=1.0`, `ema_span=5`, `window=50`, `lgb_features=93`, `scaler_features=18`, `n_op=4`, `bilstm_input=50x19`, `meta_features=2`, `epochs=22`, `epochs_oof=15`, `step_train=3`, `step_test=2`, `conformal_target=0.90`, `n_calibration=17450`, 4 SHA | 4.338 / 3.227 / 0.9461 / 2336.2 · `macro_rmse=5.0153` | `tiempo_total_s=447` · `t_lgb_s=0.3` · `t_bilstm_s=113.2` | `produccion` · `origen=manifiesto` · `seleccion=produccion` · `v3_bundle=archivado` |

Los 4 SHA del run de producción: `ensemble_sha256`, `bilstm_sha256`,
`clase_xgb_sha256`, `clase_e2_sha256`. `v3_bundle_sha256` va como **tag**
(`archivado`), no como param: apunta a un fichero que ya no está en `models/`.

### Tags comunes (todas las runs)

`cv_scheme=GroupKFold`, `cv_folds=3`, `cv_group=unit`, `scoring=rmse`,
`refit=rmse`, `seed=42`, `pipeline=StandardScaler(19)+OneHot(fase_vuelo)`,
`n_features=22`, `dataset=DS02`, `dataset_variant=DS02-adaptada (MAR T30 + ffill,
medianas fit-units)`, `n_train=52635`, `n_test=12538`, `git_commit`, `git_dirty`.

A nivel de **experimento**: `python=3.12.10`, `sklearn=1.9.1`, `xgboost=3.4.1`,
`lightgbm=4.7.0`, `tensorflow=2.21.0`, `keras=3.15.1`, `data_sha256` (parquet de
train y test), `job=reto-1-saa-pia-mia`.

### Lo que NO se loguea (y por qué)

- **Semillas 7/123**: no tienen hiperparámetros; se quedan en el CSV multiseed.
- **Binarios (`log_model`, skops, registry)**: duplican `models/` y meten artefactos
  en el store; el rubric pide tracking, no serving.
- **Artefactos de datos o figuras**: 8 MB de parquet y PNG ya viven en `docs/assets`;
  se loguea su hash, no una copia.
- **Curvas por época**: no se guardaron; inventarlas sería peor que no tenerlas.

---

## 19. Buenas prácticas: qué añadimos y qué rechazamos

| Práctica | ¿Entra? | Motivo |
|---|---|---|
| Nombre de run + tags (`grano`, `familia`, `origen`, `rol`) | **Sí** | Es lo que hace usable la vista de comparación y evita mezclar ligas |
| `mlflow.note.content` con la hipótesis / motivo de selección | **Sí** | La rúbrica pide «y por qué»; el MLP ya trae `hipotesis` en el CSV |
| Protocolo de validación (`GroupKFold(3)`, grupo `unit`, scoring, refit) | **Sí** | Sin él, «val 7.34» no es interpretable; está en `train_clasicos.py` |
| Linaje de datos (SHA de parquet, filas, unidades fit/holdout/test) | **Sí** | Reproducibilidad real; el manifiesto ya lo declara |
| Entorno + commit git | **Sí** | Buenas prácticas de MLflow; coste cero |
| Runs de los componentes del bundle | **Sí** | Sin ellos, el modelo desplegado es una caja opaca; con ellos, «todos los modelos» es literal |
| Export generado por API con `run_id` | **Sí** | La tabla del README debe ser «sacada de MLflow», no transcrita |
| Backfill idempotente (`--check`) | **Sí** | Se puede reejecutar sin duplicar runs |
| Store de texto versionado, artefactos ignorados | **Sí** | Un clon debe poder leer los `run_id`; los binarios no |
| `mlflow.sklearn.log_model` / Model Registry | **No** | Binarios + backend/DB; duplica el bundle y no suma rúbrica |
| `mlflow.autolog()` | **No** | Exigiría reentrenar y movería cifras |
| Firma de modelo / input example | **No (deuda)** | Requiere cargar el modelo y escribir artefacto; no lo pide la rúbrica |
| `mlflow.data` con copia del dataset | **No** | 8 MB; el hash da la trazabilidad sin duplicar |
| Nested runs para el bundle | **No** | Complica export y comparación; `rol` + `base` tags bastan |
| Servidor MLflow / backend SQLite | **No** | 17 runs en file store; un proceso más no aporta |
| Figuras por run | **No** | Duplican `docs/assets` y engordan el store |

---

## 20. Plan de inclusión (fases, ficheros, acceptance)

| Fase | Trabajo | Ficheros | Acceptance | Tiempo |
|---|---|---|---|---|
| **0. Preflight** | Rama, backups de `resultados/` y `artifacts_c`, snapshot de hashes, baseline de suite | — | 345 passed; `models/*` y manifiesto sin tocar | 15 min |
| **1. Dependencia** | `mlflow==3.18.0`, cabecera de requirements, `uv lock`, instalar, `pip check` | `requirements.txt`, `pyproject.toml`, `uv.lock` | 0 downgrades de numpy/pandas/sklearn/TF; 345 passed | 30 min |
| **2. Store** | Política de store y experimento | `.gitignore`, `scripts/backfill_mlflow.py` | `git status` sin binarios; `mlruns/` de texto | 10 min |
| **3. Backfill** | 9 runs fila + 3 componentes + 1 producción + 4 ablación; `--write/--check` | `scripts/backfill_mlflow.py` | 17 runs con params/métricas (y tiempo cuando se midió); `--check` exit 0 | 2–3 h |
| **4. Export + capturas** | CSV desde la API + 2 capturas de comparación + run de producción | `docs/evidencia/mlflow/` | CSV == store; `run_id` presentes; capturas con tiempo | 45 min |
| **5. README** | Captura de app, tabla MLflow etiquetada, elección y captura | `README.md`, `README.en.md` | PIA-1 y PIA-4; tabla separada de la de test | 45–60 min |
| **6. Superficies** | Quitar «MLflow fuera» de 7 sitios; rúbrica v4→v5 | `docs/chuleta`, `guiones`, `presentacion`, `c27`, `s14`, `openspec/config` | Ninguna superficie activa dice «fuera» | 30–45 min |
| **7. Test + gate** | Test que lee el store de disco; suite; freeze de reglas e instrumento | `tests/test_mlflow_backfill.py` | 0 skips; gate exit 0; sin binarios | 45 min |
| **8. Parada** | No tocar notebooks hasta autorización aparte | — | §16 se ejecuta después | — |

**Comandos de cierre (todos deben salir 0):**

```bash
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe scripts/backfill_mlflow.py --write
.venv/Scripts/python.exe scripts/backfill_mlflow.py --check
.venv/Scripts/python.exe -m pytest tests/test_mlflow_backfill.py -q -rs
.venv/Scripts/python.exe -m pytest tests -q -rs
.venv/Scripts/python.exe scripts/freeze_rules_evidence.py
.venv/Scripts/python.exe scripts/freeze_oof_instrument.py --check
git status --short
```

**Rollback:** quitar la línea de `requirements.txt`/`pyproject.toml`; borrar
`scripts/backfill_mlflow.py`, `tests/test_mlflow_backfill.py`, `mlruns/` y
`docs/evidencia/mlflow/`; revertir README y las 7 superficies. No hay migración de
datos ni artefacto de modelo implicado.
