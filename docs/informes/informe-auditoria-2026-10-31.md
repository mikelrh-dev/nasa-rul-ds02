# Auditoría exhaustiva file-by-file — reto DS02 RUL (2026-10-31)

## 0. Veredicto

**Código y artefacto: 10/10. Proyecto documentado: 9/10. No es un 10/10 estricto.**

Revisado un archivo Python tras otro (105 ficheros `*.py`: 13 en `app/`, 15 en
`src/ds02_rul/`, 5 en `mia/`, 16 en `tests/`, ~56 en `scripts/`), más los 5
notebooks, los 14 informes, las 10 ADR, `openspec/`, `models/` y la raíz.
Todo compila (`compileall` limpio), la suite da **213 passed + 6 skipped** y los
sellos SHA-256 coinciden entre fichero, manifiesto y caché. Las 8 incidencias
son de documentación, orden y restos legados; ninguna altera el modelo.

Este informe es el único fichero nuevo: no se tocó nada del proyecto.

## 1. `app/` — 13/13 revisados (8829 líneas en total, 3595 solo el tablero)

| Fichero | Líneas | Estado | Notas |
|---|---|---|---|
| `api.py` | 123 | OK | `lifespan` carga el bundle; `GET /health` expone paradigma/ventana/beta/ema/n_op/tabuladas; `POST /predict` ventana o trayectoria; 404/422/503 correctos. Sin auth (demo local, aceptable). |
| `dashboard.py` | 131 | OK con reserva | Tablero simple legado: carga HDF5 2.3 GB + ensemble **en el render**. Funciona pero lo sustituye `dashboard_ds02`. Sin cartel de "legado": alguien puede arrancarlo creyendo que es el DSS. |
| `dashboard_ds02.py` | 3595 | OK con reserva | El DSS real: solo `app/cache/` + manifiesto, modelo perezoso (`get_ensemble` solo con deriva ≠ 0), escrituras diferidas (corrige el `StreamlitWidgetAlreadyInstantiatedError` de C1/C2), toasts, sandbox con leyenda degradada honesta, botón de auditoría de hashes, sello ensemble vs disco, PDF. Reserva: es un monolito; futuro: extraer sandbox e informe PDF. |
| `flota.py` | 147 | OK | Registro único de nombres; contador monótono (no reutiliza ids); `U<int>` por defecto. Testeado. |
| `hangar.py` | 181 | OK | FSM pura, decisión de entrada congelada, `revision()` contrasta política vieja vs hoy, `reiniciar` como replay honesto. |
| `pdf_partes.py` | 54 | OK | Espejo PDF del JSON/CSV, plegado latin-1, sin recálculo. Import local de fpdf2 (correcto). |
| `simulacion.py` | 103 | OK | Reloj de flota como lectura; documenta el desajuste step-2-caché vs step-1-vivo medido (U14 c76: 0.6692 vs 0.8654). |
| `twin.py` | 268 | OK | Huella a 9 decimales insensible a formato; id normalizado (mín. 3); `registrar` conserva `truth`; estado siempre re-derivado (los umbrales no reescriben la serie); orden usa la peor ventana del último ciclo. |
| `ui_alta.py` | 147 | OK | Perfiles medidos contra la caché; `ventanas_de_alta` no re-puntúa; `estado_demo` (30/25, U14, ciclo 29); `estado_historia` derivado, no constante. |
| `ui_batch.py` | 166 | OK | Tope 25 con aviso; columnas de triaje sin `rmse/mae` (sin verdad no hay error); preflight único; lote por `score_table` + pasada A de `mia`. |
| `ui_data_loader.py` | 515 | OK | Solo caché, nunca TF; `artifact_hash_check` por bloques; `classify` sobre `L_inf`; `unit_curve` guarda media y `lower_min`; `fleet_snapshot` con clamp (no extrapola); métricas recomputadas; `mae_by_band` por RUL **real** (distinto de los bines conformales por RUL predicha: documentado); `work_order` declara banda + corrección + regla; `parte_disponibilidad` audita el "nada que derivar". |
| `ui_inference.py` | 542 | OK | Ensemble perezoso; `LIVE_UNIT=-1` (el EMA no mezcla); topes 5000/1500 explícitos; orden de canales desde provenance; `example_window`/`window_ending_at` reales; `observed_envelope` ±5 %; avisos no bloqueantes; `validate_table` estricta (orden, 50 filas, numérico, temporal, coma decimal europea, `inf` que corrompería el EMA); `preflight` sin modelo; `score_table` step=1 + contrato con SHA; `live_work_order` vía `mia`. |
| `ui_rules.py` | 188 | OK | R2b causal por `(ciclo, start_index)` + R6 vectorial; conserva `*_enviada`; decisión solo por `mia.motor`; `decision_en_vivo` excluye avisos de plausibilidad de `alertas_datos` (correcto: si no, R1 devolvería `SIN_DECISION` contradiciendo el aviso). |

## 2. `src/ds02_rul/` — 15/15 revisados

| Fichero | Líneas | Estado | Notas |
|---|---|---|---|
| `data.py` | 99 | OK | `resolve_ds02` enumera rutas y **lanza** si falta (sin fallback FD001 silencioso); `load_fd001_reference` separada con clamp 125 solo-FD001. |
| `features.py` | 169 | OK | `fit_preprocessing` solo-fit-units; `BASE_CYCLES=3`; ventanas 50×19 + tabular 93; baselines causales. |
| `model.py` | 51 | OK | Campeón 2×BiLSTM(64) + triple pooling, 154 253 params (verificado en contrato). |
| `pooling.py` | 26 | OK | `LastStepPooling` serializable; adiós `Lambda`/marshal. |
| `smoothing.py` | 37 | OK | EMA causal `adjust=False` por motor. |
| `residualizer.py` | 38 | OK | 14 ridges régimen→sensor. |
| `metrics.py` | 53 | OK con minucia | NASA como **suma**, macro-RMSE, `evaluate_predictions`. Minucia: el docstring cita 4.26/4.88 frente a 4.2515/4.8433 vigentes. |
| `ensemble.py` | 224 | OK | Keras perezoso; aviso `units=None`; valida ventana; respeta `meta_features` 2 (sin ciclo) o 3; 50/50 ridge+LGBM; `beta`; EMA; `clip≥0`; `predict_interval` separada. Rama 92/93 coherente con `features`. |
| `stacking.py` | 410 | OK | `MetaSpec` validada; `support_gate`; `beta` agrupado OOF; diseño OOF-pooling medido y **rechazado** con cifras (39.9 vs 31.5, 4.04→10.17). |
| `conformal.py` | 119 | OK | Asimétrica por bines de RUL predicha; `min_rows`→global; `debias` solo diagnóstico; invariantes `lower≤pred≤upper`; `empirical_coverage`. |
| `inference.py` | 72 | OK | Ventanas crudas alineadas a fin de ventana; mensaje de error con unidades disponibles. |
| `pipeline.py` | 291 | OK | `alpha=0.35` con rechazo documentado de la mediana (ADR-007); early-stopping; `run_seed` con prep solo-fit; OOF con re-ajuste por fold. |
| `persistence.py` | 215 | OK | `.keras` nativo; copia destacada con `bilstm_path` absoluto + fallback al directorio del bundle; guardia 18 canales / `n_op=4`; manifiesto con objetivo tabular y `meta_features`. |
| `viz.py` | 325 | OK | Solo presentación estilo-clase; no entrena. |
| `__init__.py` | 41 | OK | API pública + versión 4.1.0. |

## 3. `mia/` — 5/5 revisados

`motor.py` (56): dos pasadas, prioridad, una aplicación por pasada, `MAX_VUELTAS=32`. OK.
`reglas.py` (206): PAVA causal + guarda `MIN_FILAS_TRAMO=500` (el tramo `[75,inf)` con
419 filas y `q_high` negativo ya no hunde el límite); bandas con clip; R1/R7/R8/R9.
Calibración 14 915 filas OOF puras (sin unidad 16) frente a `n_calibration=17450`
del manifiesto (6 motores dev): ambas correctas, usos distintos, documentado.
`modelo.py` (65): carga perezosa; `COLUMNAS` coincide con `hstack([W, Xs])`.
`casos.py` (158): 9 casos desde la caché + seguridad sintética; U14-ciclo-30 ya en
HANGAR del bundle B (cambio sin commitear, coherente con la suite verde).
`__init__.py` (14): mapa de pasadas. OK.

## 4. `tests/` — 16/16 revisados (213 passed, 6 skipped)

Contrato del artefacto (carga en proceso limpio `4 50 1.0 5`, sin `Lambda`,
forma DS02, `alpha=0.35`, `LastStepPooling==slice`, cabeza 384, reload idéntico,
aviso `units=None`, validación de ventana, sin fallback FD001; 1 skip legado si
faltan pesos). Reglas (forma de tuplas, todos los casos BIEN, causalidad,
calibración 14 915). Gate RULES-06 (CLI 0/2/3/4/5, sin TF al importar,
idempotencia). DSS-UI (umbrales incl. regresión del verde inalcanzable, caché ==
bundle, orden con provenance, sin fuga FD001). Interacción (AppTest pulsa C1/C2:
cubre el `StreamlitWidgetAlreadyInstantiatedError`). Flujo motor (gemelo+hangar
sin TF). Flota (claves, contador sin reutilización). Hangar (transiciones, cola
por urgencia, entrada congelada). Twin (huella insensible a formato, serie,
verdad). Simulación (U14 cruza en 29; `faltan {11:20, 14:28}` del bundle B).
Alta (perfiles en banda, demo medida). Lote (N→N, <50 rechazado pre-modelo, tope
25, sin verdad). Puente rules (filas conservadas, isotónico, firma `mia`, SHA en
pantalla). Evaluación en vivo (sin TF al importar, ejemplo válido,
reproducible, carga bajo demanda, sin escrituras). Auditoría 2026-10-21 (5
familias). UX ronda 3 (persistencia, coma decimal, recorte, a11y). `conftest.py`
aparta y restaura `app/registros_flota.json`: la suite no destruye la flota del
usuario. Los 6 skips son `needs_cache`/`needs_oof` preexistentes (`_p1_oof_cache.npz`
ausente por `.gitignore`): el gate CLI los trata como fallo 3, los tests como
skip. Doble política intencionada y documentada.

## 5. `scripts/` — revisados por familias

Núcleo DS02 (leídos enteros o en cabecera + uso): `build_ui_cache` (bundle
solo-lectura → 6196 ventanas + 12 538 filas + provenance), `freeze_rules_evidence`
(542 líneas, códigos, sin TF por paquete de nombres explícito), `predict_ds02`
(CLI unidad/todo/listar), `build_02_notebook` (1211 líneas, nbformat puro: el
`.ipynb` es salida), `extract/repackage_legacy_artifact` (migración 3.10),
`ablate_meta_cycle`, `p0_density_control`, `p1_meta_support`, `p1_oof_cache`,
`evaluate_model_quality`. Sondas `probe_*` (~30): todas por `load_ensemble`
contra el bundle congelado; son evidencia, no deuda. Legado FD001 (`predict.py`,
`v3_*`, `rebuild_v2`, `recalcular_test`, `test_fixed_pipeline`,
`test_lstm_clean`, `test_xgb_rolling`, `update_v2_cells`, `v2_add_cells`,
`v2_conclusion`, `verify_blend`, `verify_gate`, `finalize_v2/v3`, `add_v3_notebook`,
`ajustar/inspect/dump/execute_*`): fuera de `pytest` gracias a `testpaths=["tests"]`
medida correcta. `verify_gate.py`/`verify_blend.py` son sondas, no gates.

## 6. Notebooks — 5/5 (todos ejecutados)

Raíz `02_DS02_ensemble_RUL.ipynb` 35/35, `01` 12/12, `02` 18/18, `03` 25/25
(`[LOAD NB1 OK]`, `[LOAD NB2 OK]`, `[RELOAD OK]`, `recargado == en memoria: True`).
Rerun ≠ publicado (híbrido 4.278±0.051 vs 4.352±0.055; BiLSTM 6.347±0.748 vs
6.233±0.485; LightGBM idéntico 7.098±0.034): no-determinismo TF/oneDNN ya
declarado; la decisión no cambia (Δ≈2 RMSE ≫ ±). `notebook_nasa_fd001.ipynb`
32/32: legado FD001 sin cartel de archivo — riesgo de confusión. `artifacts/`
ignorado por git (correcto: tránsito 01→02→03). `motorReglasEjemplo/practica_reglas.ipynb`
es material de clase, ajeno al DSS. `RequisitosClase/Ejemplos/` excluido por
`.gitignore`. `02_exec.log`/`03_exec.log`/`retrain_nb*.log` solo muestran
avisos nbformat/zmq/oneDNN, sin errores.

## 7. `docs/`, `openspec/`, `models/`, raíz

`docs/02_DS02_ensemble_RUL_spec.md` (793 líneas): tabla ya con fila bundle B y
macro 4.8433 — al día en cifras. 10 ADR (001–010) con la cadena causal completa;
ADR-008 demuestra el verde inalcanzable del plan original. 14 informes (uno por
pregunta) + `README` de índice. `docs/pendiente/pendiente-adopcion-bundle-B.md`:
adopción verificada pero **"No commitear"**, backup en `/tmp` (volátil). 11
planes en `docs/plans/` = backlog, no deuda. `costes_reales_aeronauticos.md` y
`literatura_costes_rul.md` son contexto, no contrato. `openspec/project.md` dice
que el fallback FD001 es "dead code": el código hoy **lanza** en vez de
degradar — párrafo desactualizado. Spec `rul-prediction-ds02` (573 líneas):
contrato desplegado.
`models/`: bundle B íntegro (ensemble 470 KB `7acba335…`, keras 1.9 MB
`d0c5ed7f…`, manifiesto `71607f0b…`, sellos cruzados OK); `ablation_meta_cycle.json`
coherente con README; `legacy/` (8 ficheros) respalda 2 tests de contrato;
`alarm_policy.json`, `psi_reference.json`, `v2_metrics.json`,
`test_eval_ultima_ventana.csv`, baselines `*_FD001_*.joblib`, `lstm_FD001_*.h5`,
`v3_bundle/joblib`, `v3_quantile_FD001.csv`, `v3_results.json`,
`informe_batch.csv` = época FD001/v3: conservar, no mezclar (de ahí sale el
"LightGBM 13.42" de `AGENT.md`). Duplicados `ensemble.joblib`/`scaler.joblib`
en raíz: bit-idénticos pero ignorados por git (`.gitignore` dice que lo canónico
vive en `models/`); en disco confunden.
Raíz: `README.md` mezcla tres generaciones (v4.1.0 4.301±0.068, revisión
4.344±0.075, bundle B 4.251) y cita macro 4.939/4.903 frente a 4.8433 vigente;
la línea de ablación aún llama "shipped" al 4.301. `AGENT.md` describe otro
experimento (FD001 13.42/26.16, Python 3.10). `Dockerfile`/`compose`: `config`
válido, imagen nunca construida (limitación declarada). `requirements.txt` +
`pyproject` coherentes (`testpaths`, Python ≥3.10, venv 3.12.10 real).
`git status`: 7 modificados + `MLProyectVault/07-Funciones-y-API/` untracked.

## 8. Incidencias (8, ninguna del modelo)

1. README con tres generaciones de cifras (incl. "shipped 4.301" y macro viejo).
2. `AGENT.md` obsoleto (FD001, Python 3.10).
3. 7 ficheros sin commitear + directorio untracked; backup solo en `/tmp`.
4. Duplicados raíz idénticos a `models/` sin señal de cuál manda.
5. `notebook_nasa_fd001.ipynb` y `app/dashboard.py` sin cartel de legado.
6. `openspec/project.md` ("fallback dead code") y docstring de `metrics.py`
   (4.26/4.88) con números viejos.
7. 14915 vs 17450 sin cartel local (correctos, usos distintos).
8. `dashboard_ds02.py` monolítico (3595 líneas) y Docker sin construir.

## 9. Qué se verificó y qué no

Compilación total, suite completa, sellos, caché vs manifiesto, carga del bundle,
conteo de celdas, `docker compose config`, `git status/diff`, duplicados,
parquets, calibración. No: arranque interactivo en navegador, construcción Docker
ni re-ejecución de notebooks (coste CPU y reescribiría `models/`).

## 10. Recomendación

Una tabla vigente en el README, archivar/actualizar `AGENT.md` y `project.md`,
commitear (o decidir espera) con backup persistente, señalizar duplicados y
legados, y construir Docker una vez. Con eso, el 9/10 actual es 10/10 sin tocar
modelo, app ni tests.
