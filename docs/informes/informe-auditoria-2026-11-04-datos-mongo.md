# Auditoría read-only NASA DS02 — Datos + Mongo (2026-11-04, histórica: B autoritativo entonces, hoy C 4.338 ver e00)

**Repo:** `C:/Users/mikel/Desktop/Pruebas/nasa` — rama `clase-experimental`, HEAD `098a1bf`
**Alcance:** Datos RAW + procesados + caches + MongoDB + tests/gate + docs/reproducibilidad. HDFS y Kafka aparcados por instrucción.
**Método:** 5 subagentes read-only en ventana deslizante máx 3, probes en scratch Hermes, verificación con ejecución real. Ningún archivo del repo modificado durante la auditoría.

**Escalas usadas:**

- **Improve 0-10:** cuánto mejora la decisión y reduce la chance de contradicción en vivo.
- **Riesgo 0-10:** probabilidad × coste de romper algo o fallar ante audiencia.

---

## Resumen ejecutivo

| Frente | Veredicto ejecutado | Impacto | Riesgo |
|---|---|---|---|
| RAW HDF5 | 0 nulos/inf, ciclo monótono, hash H5 47971a68 OK, partición por unidad OK | 8/10 | 2/10 |
| Procesados+cache | MAR 12499/1185 exacto, 6196/12538 exacto, 4/4 SHA exactos, sin fuga | 8/10 | 2/10 |
| MongoDB | 0% implementado, readiness 2/10, solo diseño | 9/10 | 8/10 si se mete sin diseño |
| Tests + gate | 256 passed, 5 failed (poda 7d0da94), 6 skipped — bundle B 4/4 verde, gate honesto FAILED | 8/10 | 2/10 |
| Docs + git | B autoritativo OK en AGENT/README/vault e00, 16 contradicciones (6 P1) | 9/10 | 8/10 si se defiende sin corregir |

Reproducibilidad externa: **3/10 end-to-end** (pipeline completo con H5), **8/10 demo con cache**.

---

## 1. RAW — `data/raw/N-CMAPSS_DS02-006.h5` (2.3 GB)

### Inventario verificado (h5py readonly)

- `A_dev (5263447,4)`, `W_dev (5263447,4)`, `X_s_dev (5263447,14)`, `Y_dev (5263447,1)`
- `A_test (1253743,4)`, `W_test (1253743,4)`, `X_s_test (1253743,14)`, `Y_test (1253743,1)`
- `W_var = alt, Mach, TRA, T2`. `X_s_var = T24,T30,T48,T50,P15,P2,P21,P24,Ps30,P40,P50,Nf,Nc,Wf`
- Extra ignorado por diseño: `X_v_dev/test`, `T_dev/test`, `A_var`
- Unidades dev `[2,5,10,16,18,20]` ciclos 75/89/82/63/71/66, Y 0-88
- Unidades test `[11,14,15]` ciclos 59/76/67, Y 0-75
- Nulos/inf = 0 real en A,W,Xs,Y dev y test. Cycle no decreciente True. Overlap dev-test = vacío.
- Stride 100: dev 52635 filas, test 12538 filas. Por unidad U11 6635, U14 1568, U15 4335 — coincide con `cache_manifest.json`.

### Código `src/ds02_rul/data.py`

- `resolve_ds02` 39-50: `raise FileNotFoundError` descriptivo, sin fallback FD001 silencioso. Correcto.
- `load_ds02` 53,65: `[::100]` alineado A/W/Xs/Y. Sin clamp 125. Correcto.
- Asserts 70-96: alineación, ndim, op/sensor names vs W/Xs, `np.isfinite` global, cycle no decreciente por unidad. Pasan en ejecución.
- `FD001_CANDIDATE_PATHS` 28-33 muerta, cero usos. `load_fd001_reference` 117-135 separado explícito.
- `archive/CCMaps/` solo `100_primeros_datos.txt` (21K), sin H5. Fallback inactivo.

### Manifiestos

- SHA-256 H5 real `47971a68b239ecb756833218a95d68ded6eb7e63ee84e86671c8b188de1ca765` = `cache_manifest.json:32` ✅
- SHA-256 `ds02_manifest.json` `71607f0b...883c7a18` = `cache_manifest.json:38` ✅
- `ds02_manifest.json`: seed 42, fit `[2,5,10,18,20]` holdout `[16]` test `[11,14,15]`, stride 100 window 50, RMSE ref 4.251 MAE 3.183 R2 0.9482 NASA 2305.1 macro 4.8433.
- Hueco P2: `ds02_manifest.json` no registra `h5_sha256`, solo `ensemble_sha256` `7acba335...d64b1b` y `bilstm` `d0c5ed7f`. Pin H5 vive solo en `cache_manifest.json`.

### Hallazgos

- **P1-1 Densidad U14 extrema** — `features.py:79-163` + `cache_manifest.json:56-63`. U14 20.63 filas/ciclo vs U11 112.46 (densidad 0.175). RMSE U14 7.997 vs U11 3.787 vs U15 2.745, bias -5.096. Ventana 50 filas strided = 2.4 ciclos en U14 vs 0.44 en U11. Conclusión por unidad U14 frágil.
- **P1-2 Horizonte mal etiquetado** — window 50 filas strided se presenta como ciclos. Real: 0.445 ciclos en U11, 0.773 en U15. `features.py:139` divide `ciclo/100` sin span. No es error numérico, es error de interpretación.
- **P2-1 STRIDE=100 descarta 99%** — `data.py:65`. Sin análisis de sensibilidad stride en el repo.
- **P2-2 X_v/T ignorados sin documentar** — `data/raw/README.md` no los menciona. Riesgo de malentendido de cobertura.
- **P2-3 H5 no versionado** — `.gitignore:21,97`, sin URL de descarga en README. Clon limpio no reproduce.
- **P2-4 Conformal n=17450** — `cache_manifest` bandas suman 17450, holdout unit 16 sola (2535 rows). Generalización descansa en 9 motores totales en el H5.
- **P3** — `scaler_n_features 18` ok, `lgb_n_features 93` ok, `FD001_CANDIDATE_PATHS` muerta.

### Veredicto RAW

Suficiente para scoring global RUL con stride 100 y split por unidad, 0 nulos, leakage evitado en `fit_preprocessing` solo fit units `features.py:25-52`. No suficiente para afirmar horizonte de vuelo ni confianza U14.

---

## 2. Procesados + caches

### Inventario (2026-11-02 14:16)

- `train.parquet 52635×23`, `test.parquet 12538×23`, `X_train 52635×21`, `X_test 12538×21`, `y_train 52635×1`, `y_test 12538×1`, `*_con_nulos` mismos shapes.
- `ds02_rows.parquet 12538×20`, `ds02_windows.parquet 6196×7`, mtime 2026-10-26 22:17.
- `cache_manifest.json` `generated_at 2026-10-26T21:17:27`, mtime 2026-11-04 08:14 modificado sin commitear (+5/-2).

### Conteos verificados (pandas)

- `X_train.equals(train cols)` True, `X_test.equals` True.
- Diff train vs train_con_nulos 1056 celdas solo T30, test 129 celdas solo T30.
- Unidades train 2,5,10,16,18,20 test 11,14,15 solape vacío. Nulos finales 0. RUL train 0-88 test 0-75.
- `fase_vuelo` train Descenso 23318 Crucero 15813 Ascenso 13504; test Descenso 5681 Ascenso 5091 Crucero 1766.

### `auditoria_nulos.json` MAR T30 alt>27000 & Mach>0.68 seed 7

- Elegibles 12499 exacto, nulos 1185 exacto (1056+129), tasa elegibles 0.0948 exacto, global 0.01818 exacto.
- Rachas por unidad `{2:3,5:3,10:3,11:3,14:0,15:1,16:2,18:3,20:2}` exacto. Reproducible al entero.

### Features

- Tabular por fila X = 21 cols = unit+cycle+4 op+14 sensores+fase_vuelo. Sin unit 20, numéricas pipeline 19, +OneHot fase 3 = 22 total. No 93.
- Ventana X_tab = 93 = 1 cycle + 4 mean op + 4 last op + 14 mean + 14 last + 14 std + 14 last10 mean + 14 diff + 14 pres5 = 93. Sin fase_vuelo, contrato 93 intacto `ventanas_adaptadas.py`. Manifest `lgb_n_features 93`, `scaler_n_features 18`, `bilstm_input_shape [None,50,19]`.

### Código `dataset_clase.py` + `pipeline_clase.py`

- `ffill` causal `groupby(unit)` ordenado `[unit,cycle]` + `fillna(medianas)`. Correcto.
- Medianas solo train, en `ventanas_adaptadas.py` solo `FIT_UNITS [2,5,10,18,20]`. Correcto.
- Split por unidad TRAIN `[2,5,10,18,20,16]` vs TEST `[11,14,15]` solape vacío. Nunca por fila.
- `GroupKFold(3)` con `groups=unit`. Folds verificados sin overlap `{5,16},{10,20},{2,18}`.
- `fase_vuelo` solo alt/Mach + diff alt causal. Sin fuga de etiqueta.
- `unit` no predictor, solo grupo. Scaler dentro de Pipeline fit por CV.

### Hashes (hashlib.sha256)

- `models/ensemble.joblib` `7acba335...d64b1b` MATCH ✅
- `app/cache/ds02_windows.parquet` `0c18927b...0b60` MATCH ✅
- `app/cache/ds02_rows.parquet` `bfeecbd2...f4579a` MATCH ✅
- `data/raw/N-CMAPSS_DS02-006.h5` `47971a68...ca765` MATCH ✅
- 4/4 exactos. 6196 windows y 12538 rows = manifest.

### Hallazgos

- **P3** `imputar_ffill` si `medianas=None` calcula sobre propio df `dataset_clase.py:169-170`. Docstring dice SOLO válido para train. No hay llamada indebida en ruta principal.
- **P2** `cycle` como predictor: RUL = total - cycle, atajo fuerte (SHAP cycle dominante). No fuga, sí shortcut a vigilar.
- **P2** manifest sin commit VCS (+5/-2 aditivo correcto).
- **P1** ninguno.

### Veredicto procesados

Reproducible en conteos, MAR, split por unidad, GroupKFold, imputación causal y hashes.

---

## 3. MongoDB gap (0% implementado)

### Triple búsqueda de ausencia

- `grep pymongo|mongosh|mongodb` en `src,app,scripts,tests,pyproject,requirements,docker-compose,Dockerfile`: 0 menciones.
- `requirements.txt` sin pymongo, `pyproject.toml` solo `plotly>=6.0`. Sin `MONGO_URL`.
- `docker-compose.yml`: 2 servicios solo `api` 8000 y `dashboard` 8501, volumen `./archive:/app/archive:ro`. Sin mongo, sin healthcheck DB.

### Persistencia actual

- **`app/registros_flota.json`**: JSON plano `twins/hangar/altas`. Escritura whole-file `app/twin.py:252-268`, `app/hangar.py:165-181`, `app/flota.py:137-147`. Sin lock, sin escritura atómica, last-writer-wins. Gitignored, hoy ausente solo `.hermes-respaldo` 49 bytes. Dockerfile `COPY app/` sin volumen compose. **Pérdida total en redeploy.**
- **`app/cache/`**: 2 parquet versionados + `cache_manifest.json` con `h5_sha256, windows_sha256, rows_sha256`. Regenerables con `scripts/build_ui_cache.py`, hash verificado en `src/ds02_rul/persistence.py`. Solo lectura `st.cache_data ttl=3600 u i_data_loader.py:115-148`.
- **`models/`**: `ensemble.joblib` 460K, `scaler.joblib` 1.1K, `bilstm_ds02.keras` 1.9M con `ds02_manifest.json`. Contrato inmutable: SHA verificado antes de cualquier `joblib.load`/`keras load`. Sin coincidencia `RuntimeError` y el pickle nunca se deserializa.
- **`src/mia/calibracion_banda.json`**: 1.7K split-conformal asimétrico 14915 OOF unidades 2,5,10,18,20 coverage 0.90. No migrable sin romper trazabilidad OOF.

### Diseño mínimo viable recomendado (solo operativo)

| Colección | Clave natural | Campos | Índices |
|---|---|---|---|
| `telemetry_raw` | `unit,cycle,row_idx` | 14 sensores + 4 op + ts + fingerprint | unique `unit+cycle+row_idx`, sin TTL |
| `predictions` | `unit,cycle,fingerprint` | pred, lower, upper, hash, `model_version=ensemble_sha256` | unique `unit+cycle+fingerprint`, sin TTL |
| `twins` | `engine_id` | serie ciclo a ciclo, estado, fingerprint `twin.fingerprint` | unique `engine_id` |
| `work_orders` | `id` | unit, engine_id, estado COLA/REVISION/HANGAR, lower, umbrales, nota, historial `$push` | `estado+creado_en`, `engine_id+creado_en` |
| `audit_log` | append-only | ts, actor, accion, coleccion, id, before, after | `ts`, TTL 180 días |

- Validación `$jsonSchema` tipos estrictos + fingerprint SHA-256 canónico de claves ordenadas + `ensemble_sha256`. Reutilizar `twin.fingerprint` y `persistence.data_fingerprint`, no inventar otra.
- **Sin romper artifact contract:** Contrato fichero + manifest + hash antes de deserializar. Mongo solo tras predict verificado o sobre estados operativos.

### Riesgos

- Sobreingeniería para demo: 1 proceso Streamlit, 12538 filas cache, pocos gemelos. pymongo + 3er servicio compose + credenciales + backups cuesta más que lo que devuelve.
- Ganancia real: concurrencia multi-replica y auditoría. Hoy dos replicas escribiendo `registros_flota.json` se pisan sin aviso.
- Regresión: `tests/conftest.py` apunta a `app/registros_flota.json` y `test_mejoras_streamlit.py` lo lee. Cambiar a Mongo sin adaptar tests = suite roja.

### n8n no afecta

- `n8n/flujo.json` 194 bytes placeholder `{"pendiente": "MIA3 — flujo n8n real. Placeholder... No usar..."}`.
- `src/n8n.py` 677 bytes stub `enviar_decision raises NotImplementedError` siempre, nunca POST. Flujo pendiente HANGAR → Postgres+Calendar+correo, INSPECCIÓN → Sheets, APTO → solo log. Cero referencia Mongo. ADR-010 rechaza polling n8n.

### Scores

- Readiness Mongo **2/10** (diseño sin código).
- Impacto auditoría **9/10**, riesgo meter Mongo sin diseño **8/10**.

### Opciones

1. **Mínima recomendada hoy:** volumen nombrado Docker para `app/registros_flota.json`. Cero dependencias, cero riesgo.
2. **Mongo mínimo viable:** 5 colecciones anteriores, artefactos siempre en fichero, índice único `unit+cycle`, fingerprint canónico, TTL 180 solo `audit_log`. Solo si habrá más de una réplica o auditoría formal.
3. **No hacer Mongo en demo:** JSON + volumen cubre el caso.

---

## 4. Tests + verification gate

### Inventario

- 28 módulos `test_*` + `conftest.py`, 267 tests collected en 5.11s. `verify_gate.py --list` 267 coincide.
- `conftest.py`: fixture autouse aparta `app/registros_flota.json` a `.hermes-respaldo` y restaura siempre. Evita borrar la flota del usuario.
- `pyproject.toml`: `testpaths=["tests"]`, excluye scripts FD001 históricos.

### Ejecución

`.venv/Scripts/python -m pytest tests -q: 256 passed, 5 failed, 6 skipped en 119-130s. Exit 1. GATE FAILED.`

### Fallos conocidos bundle B resueltos

- `test_mia_rules::test_todos_los_casos_salen_BIEN` ✅ PASA
- `test_simulacion::test_ciclos_hasta_fallo_coincide_con_la_cache` ✅ PASA
- `test_ui_alta::test_el_modo_historia_se_deriva_de_la_cache` ✅ PASA
- `test_ui_alta::test_el_paso_critico_cae_en_hangar_y_el_primero_no` ✅ PASA
- Conjunto 25 passed, 2 skipped en 8.84s. Adopción bundle B cerrada.

### Fallos nuevos (preexistentes en HEAD, no unión bundle B)

5 fallos, todos en `tests/test_dss_interaction.py`:

- `test_el_onboarding_es_uno_solo`
- `test_el_modo_historia_carga_el_paso_3_en_la_app`
- `test_el_paso_4_afloja_los_umbrales`
- `test_el_registro_de_sesion_es_visible_y_exportable`
- `test_la_vista_turno_oculta_el_material_de_tribunal`

Causa: commit `7d0da94` (2026-11-03, poda selectiva) eliminó de `app/dashboard_ds02.py` subheader "Modo historia" y botones `historia_*`, pero tests sin modificar siguen exigiéndolos. En HEAD `historia_*` 0 ocurrencias. Falla con árbol limpio, no regresión bundle B. `app/ui_alta.py` conserva `estado_historia()`, solo falta superficie UI.

### Skips

6, todos `_p1_oof_cache.npz` ausente: `test_audit_fixes` 1, `test_mia_rules` 2, `test_rules_gate` 3. Preexistentes y documentados.

### `verify_gate.py` honesto

Lee completo (58 líneas): lanza `[sys.executable, -m, pytest, target, -q, --no-header]` vía subprocess, propaga `returncode`, imprime `GATE PASSED` solo si 0 y `GATE FAILED (exit N)` si no. Sin timeout, sin retry, sin `--ignore`. Exit 1 hoy.

### xfail / métricas / data

- xfail: 0 marcadores en `tests/*.py`. No hay xfail stale.
- Métricas: ningún test pinnea RMSE 4.251/4.289/4.352 ni NASA 2305. Sí pinnea SHA256 recomputado en runtime contra provenance (`test_dss_ui test_artifact_hash_check_*`), inmutabilidad `calibracion_banda.json`, `test_ui_rules` vs manifest `abs=5e-3`, y consistencia vivo recomputada.
- Data/Mongo: no existe Mongo en ningún `.py`. Data layer `src/ds02_rul/data.py` solo cubierto por `test_artifact_contract::test_ds02_loader_refuses_silent_fd001_fallback` con path inexistente. `load_ds02` con H5 real nunca ejercido en tests.

### Veredicto gate

**GATE FAILED (exit 1): 256 passed, 5 failed preexistentes (poda), 6 skipped.** Bundle B verde. Qué lo pone verde: actualizar `test_dss_interaction.py` al estado podado o restaurar UI, y opcionalmente regenerar `_p1_oof_cache.npz`. **No se modificó nada en el repo.**

---

## 5. Docs reproducibilidad + git hygiene

### Estado git real

Rama `clase-experimental`: **63 modified, 2 deleted, 15 untracked, total 80 líneas** (corrige enunciado 63+9).

- Deleted sin commit: `02_DS02_ensemble_RUL.ipynb`, `notebook_nasa_fd001.ipynb`.
- Untracked 15 incluyendo `src/clase/models/` (6 joblib+keras+manifest), `models/mejor_modelo.joblib`, `app/streamlit_app.py`, `src/utils.py`, `tests/test_clase_rubrica.py`, `tests/test_clase_shap_e2.py`, `app/registros_flota.json.hermes-respaldo`.
- Diff stat: 65 ficheros, 1391 inserciones, 7827 borrados. Casi todo el borrado son los dos ipynb.
- `.gitignore` verificado: H5 ignorado por patrón `*.h5`, `archive/`, `data/`, `resultados/`, `.venv/`. Diff gitignore solo añade 6 líneas secretos env pem key, no cambia H5 ni parquet.
- Excepción no documentada: `app/cache/` con `ds02_rows.parquet` y `ds02_windows.parquet` versionados pese a ignorar parquet en `data/`. Acierto para demo sin H5 pero no explicado en README estructura.

### Código real autoritativo B

- `models/ds02_manifest.json`: RMSE 4.251 MAE 3.183 R2 0.9482 NASA 2305.1, macro 4.8433 (11: 3.787, 14: 7.997, 15: 2.745), hashes `7acba335…` / `d0c5ed7f…` verificados por sha256sum en disco.
- `app/cache/cache_manifest.json`: rmse 4.2515 mae 3.1826 macro 4.8433 coincide.
- Diff `cache_manifest.json` benigno: +3 hashes h5/windows/rows.
- `AGENT.md` 5-6, `README.md` 91,93, `README.en.md` 61-62, vault e00 citan B correcto.
- Bundle A `4.289 0acd795b` solo histórico etiquetado en informes y vault lista negra. Correcto como historia, incorrecto como vigente.

### Tabla de contradicciones doc vs código

| # | Archivo:línea | Doc dice | Realidad | Sev |
|---|---|---|---|---|
| 01 | `README.md:84-85` vs `README.en.md:52-53` | Revisión 2026-10-21 ES 4.289±0.018, EN 4.344±0.075 misma revisión | Una copia histórica errónea | **P1** |
| 02 | `openspec/project.md:222` tabla iteración 4 | Híbrido 5.522 NASA 3435.1 sin banner B | Tras fix §6.12: 4.251 ref y 4.340 media | **P1** |
| 03 | `openspec/project.md:168-176` inventario | `ensemble.joblib` y `scaler.joblib` copiados en raíz | Canónico `models/ensemble.joblib` + `bilstm_ds02.keras`. Duplicados raíz ignorados | P2 |
| 04 | `openspec/project.md:178-181` known limitation | Pickle con `__main__` unloadable | Carga en 3.12 sin shim según `README.en.md:200-207` y spec `388-393` closed | P2 |
| 05 | `openspec/project.md:116-117` How to run | `nbconvert 02_DS02_ensemble_RUL.ipynb` | ipynb deleted `D` en working tree, no ejecutable en rama actual | **P1** |
| 06 | `project.md:46,63` + spec `120,138,146` rutas `mia/` y fallback FD001 | Fallback como vigente | Real `src/mia/` y `data.py:44-52` raise sin fallback | **P1** |
| 07 | `docs/02_DS02_ensemble_RUL_spec.md:632` | Shipped 4.301±0.068 | Real B 4.251 media 4.340. Banner `643` mitiga §6.13 pero 632 queda | P2 |
| 08 | spec `218,489` población fit | Linea 218 "all six dev units" antes del split | Manifest y código: fit `[2,5,10,18,20]` n=44982 sin 16 | P2 |
| 09 | `README.en.md:6-8,187,363` `track_clase` y `mia` sin `src/` | Carpeta inexistente | Real `src/clase/` `src/mia/`, `README.md` ya corregido en working tree | P2 |
| 10 | `docs/pendiente/pendiente-adopcion-bundle-B.md:6` | Baseline HEAD ensemble `0acd795b` | `git show HEAD:models/ds02_manifest.json` ya `7acba335` B. Doc no actualizado tras adopción | P2 |
| 11 | Ruta canónica H5 spec `8,138,742` `archive/CCMaps/` y compose `archive` | vs `data.py:21 data/raw` y `cache_manifest` `data/raw` disco `data/raw` 2.3G | `archive/CCMaps/` solo txt 21K. Clon limpio con compose no encuentra H5 donde lo busca | **P1** |
| 12 | `Dockerfile` HEAD `COPY mia/mia` | vs working Dockerfile sin esa copia | `app/ui_rules.py` `from src.mia`. HEAD stale copiaría carpeta inexistente. Working corrige sin commit, fix no viaja en clon | **P1** higiene |
| 13 | `models/` legacy FD001 `rf 88M`, `lstm*.h5`, `v3_bundle`, `v2_metrics` | Tracked `git ls-files`, sin cita en README estructura | `AGENT.md:7` avisa no citar `v2_metrics` pero legacy ocupa repo sin cita | P2 |
| 14 | Vault `90-Archivo/00-Guion/00-cifras:28-29` | Disco 4.289 `051e0af4` `0acd795b` | Hoy disco 4.251 `7acba335` `d0c5ed7f`. Superseded por e00 y 000-Guion B. Riesgo cita por error | P2 |
| 15 | README baseline 4.301 `README.md:65 README.en:33 spec:31,521,632` | vs Manifest media B 4.340 | Etiquetado histórico en READMEs pero en spec se etiqueta shipped | P3 |
| 16 | `README.md:216-217` `data/processed` ignorado | No advierte que `app/cache` parquet versionado es lo que hace demo sin H5 | Es la excepción que permite clon limpio demo | P3 |

### Vault vs repo

- `50-Evidencia/e00-cifras-autoritativas.md:35-54,98-99` coincide exacto con B: RMSE MAE R2 NASA, macro por motor, hashes `7acba335` `d0c5ed7f`. ✅
- Lista negra e00 `122-125` prohíbe 4.289 4.9026 051e0af4 0acd795b. Coincide con bundle A obsoleto. ✅
- `90-Archivo/00` stale superseded por e00 y `000-Guion-Refactor-Novato` con B. No contradicción activa si se respeta carpeta, sí riesgo cita P2.

### Reproducibilidad externa

- H5 2.3G en disco `data/raw/` ignorado, `archive/CCMaps/` vacío salvo txt. Grep de URL descarga en README, README.en, spec, data.py y build_ui_cache: cero URLs de datos. Solo DOI en `openspec/project.md:248-250`.
- `.venv/` ignorado correcto, `requirements.txt` pineado Python 3.12.10 TensorFlow 2.21 LightGBM 4.7.0 sklearn 1.9.1, recreable pero no versionado por diseño. Bien.
- `app/api.py:109-110` carga ensemble en startup, `173` lazy `load_ds02` para predict. `build_ui_cache.py` necesita H5. Tests de contrato según spec pueden cargar bundle sin H5, retrain necesita H5.
- BiLSTM no bit-determinista documentado en `AGENT.md:11` y spec `594,732`. Re-ejecución mueve RMSE ±0.1.
- Dockerfile `COPY src app scripts` + 4 ficheros models incluye `app/cache` vía `COPY app`. Dashboard desde cache funciona sin H5 en clon. API predict no funciona sin H5 montado y compose monta `archive` equivocado.
- No hay `pip freeze` además de requirements, `pyproject` `requires-python >=3.10` sin pin superior.

### Veredicto

- **3/10 end-to-end**. Dashboard desde cache versionado solo sería **8/10**. Retrain, `build_ui_cache`, API predict y notebooks de clase son 0 sin H5 manual. Sin URL ni compose correcto, el 3 refleja demo reproducible pero pipeline completo no por tercero. Si el tribunal solo exige demo con cache, subir a 8. Si exige reentreno, quedar en 3.

### Impacto / riesgo

- Impacto **9/10** si se corrigen 01,02,05,06,11,12 antes de defensa, porque elimina también cita cruzada ES contra EN.
- Riesgo **8/10** si se defiende sin corregir, porque 4.289 contra 4.344, 5.522 en openspec y ruta `track_clase` se detectan en 30 segundos.

---

## Plan de acción requerido

### Bloque 1 — Defensa inmediata (tribunal no detecta en 30 segundos)

| Tarea | Acción | Improve | Riesgo |
|---|---|---|---|
| 01 README ES/EN desync 4.289 vs 4.344 | Sincronizar una sola fuente, corregir la otra el mismo día | 9 | 1 |
| 02 openspec/project 5.522 sin banner B | Reescribir tabla iteración con B 4.251 / 4.340 | 9 | 1 |
| 03 Horizonte 50 ciclos mal etiquetado | Texto defensa + README + spec: 50 filas strided = 0.44 ciclos U11, no 50 ciclos | 9 | 1 |
| 04 U14 no concluyente por unidad | Frase explícita, tabla ya existe, no ocultar | 8 | 1 |
| 05 Elegir vía 5 fallos `test_dss_interaction` poda `7d0da94` | Decisión usuario primero: restaurar UI o actualizar tests | 9 | 4 (2 si se decide antes) |

### Bloque 2 — Higiene git y docs que bloquean clon

| Tarea | Acción | Improve | Riesgo |
|---|---|---|---|
| 06 How to run nbconvert deleted ipynb | Apuntar a `notebooks/ds02_ensemble/` o retirar instrucción | 7 | 2 |
| 07 Retirar fallback FD001 y `__main__` como vigentes | Reescribir `project.md` con B vigente (`src/mia/`, raise sin fallback) | 7 | 1 |
| 08 Ruta H5 compose `archive` vs `data/raw` | Componer a `data/raw` o montar ambos, verificar sha `47971a68` | 9 | 3 |
| 09 Dockerfile HEAD `COPY mia/mia` stale | Commitear fix working tree, probar build | 8 | 3 |
| 10 Commitear higiene: `cache_manifest` +5 hashes, `src/clase/models` untracked, deleted 2 ipynb, `hermes-respaldo`, `src/utils.py`, `streamlit_app.py` | Decidir borrados ipynb primero, no todo en un commit | 6 | 3 |
| 11 Documentar excepción `app/cache` versionado vs `data/` ignorado | README estructura explica demo sin H5 | 4 | 1 |

### Bloque 3 — Reproducibilidad externa

| Tarea | Acción | Improve | Riesgo |
|---|---|---|---|
| 12 Publicar fuente H5 URL oficial + sha en manifest/docs | URL N-CMAPSS oficial, checksum `47971a68…ca765`, colocación `data/raw` | 7 | 2 |
| 13 Documentar `X_v/T` ignorados + stride 100 descarta 99% | Nota en README y spec, transparencia | 6 | 1 |
| 14 Test capa datos H5 real opcional | Test slow readonly: shapes dev/test, finito, partición por unidad. No en gate rápido | 6 | 3 |
| 15 Skips 6 por `_p1_oof_cache.npz` | Regenerar o documentar como aceptado | 4 | 2 |

### Bloque 4 — Técnico opcional (no antes de defensa)

| Tarea | Acción | Improve | Riesgo |
|---|---|---|---|
| 16 Mongo volumen nombrado `registros_flota.json` | Volumen compose para `app/`, cero dependencias | 6 | 2 |
| 17 Mongo diseño documental 5 colecciones sin código | ADR papel: `telemetry_raw`, `predictions`, `twins`, `work_orders`, `audit_log` | 5 | 1 |
| 18 Mongo implementación real | NO recomendado para demo actual. Solo si multi-réplica / auditoría formal | 4 (7 si multi-réplica) | 8 |
| 19 Sensibilidad stride 50 vs 100 + ablación sin `cycle` | Experimento separado post-defensa, nunca tocar artefacto B congelado | 5 | 6 |
| 20 Recalibrar conformal más allá de holdout unit 16 | No tocar antes de defensa. Recalibrar rompe banda + reglas + ADR 2-3 días | 3 | 7 |

### Orden recomendado

1. Empezar por decisión de **tarea 05** y **tarea 10**, sin eso las demás pueden pisarse.
2. **01-04** son cierre rápido de contradicciones en vivo, improve 8-9 riesgo 1.
3. **06-11** higiene improve 4-9 riesgo 1-3, clon deja de ser lotería.
4. **12-15** reproducibilidad improve 4-7 riesgo 1-3.
5. **Mongo:** volumen sí (16), diseño papel sí (17), código no ahora (18).

---

## Opciones numeradas (docs)

1. Commitear higiene bundle B y decidir borrados de los dos ipynb, mover `src/clase/models/` a versionado o a ignorado explícito, y eliminar o commitear `registros_flota.hermes-respaldo`.
2. Sincronizar README ES contra EN y spec el mismo día, corregir tabla revisión 4.289 contra 4.344 en una sola fuente.
3. Reescribir `openspec/project.md` con cifras B vigentes, retirar fallback FD001 y `__main__` como vigentes y actualizar How to run a notebooks ds02_ensemble reales.
4. Publicar fuente H5 con URL oficial + sha256 en manifest, corregir compose a `data/raw/` o montar ambos, y dejar Dockerfile HEAD alineado con `src/mia/` o eliminar `COPY mia/` en commit.
5. Dejar Vault e00 como única autoritativa y renombrar `90-Archivo/00` con prefijo `ARCHIVO_` para evitar cita errónea.
6. Documentar excepción `app/cache` parquet versionado frente a `data/` parquet ignorado en README estructura.

---

## Evidencia y trazabilidad

- Probes scratch: `C:/Users/mikel/AppData/Local/hermes/cache/scratch/probe_ds02.py`, `probe2.py`, `audita/probe.py`, `probe2.py` (subagentes).
- Hashes reproducidos: H5 `47971a68...ca765` (2.45 GB), ensemble `7acba335...d64b1b` (470446 bytes), windows `0c18927b...0b60` (202001 bytes), rows `bfeecbd2...f4579a` (1958368 bytes).
- Suite: `.venv/Scripts/python -m pytest tests --collect-only -q` 267 tests en 5.11s; `tests -q` 256 passed 5 failed 6 skipped en 119-130s.
- Transcripts subagentes: `C:\Users\mikel\AppData\Local\hermes\cache\delegation\live\deleg_83c27800\task-*.log` y `deleg_33c15f96\task-*.log`.

**Nada modificado en el repo durante la auditoría. Este informe es la primera escritura pedida por el usuario.**

---
*Documento generado 2026-11-04. Rama `clase-experimental`. Autoridad numérica: `models/ds02_manifest.json` bundle B (RMSE 4.251, MAE 3.183, R2 0.9482, NASA 2305.1, macro 4.8433, hashes `7acba335` / `d0c5ed7f`).*
