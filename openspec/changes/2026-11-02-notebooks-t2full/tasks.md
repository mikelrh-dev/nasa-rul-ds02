# Tareas T2-full (una por notebook, orden 02 -> 03 -> 04 -> 05 -> 01-repaso)

Estado: **completado**. Todos los notebooks 01-05 ejecutan sus procesos en vivo
(entreno + metricas en memoria), con storytelling celda a celda para defensa.

## T1 — 02: GridSearch oficial en vivo  [x]
- [x] Celda que importa `ESPEC`, `CV` de `track_clase.train_clasicos` y ejecuta el
  loop completo (5 modelos, GroupKFold 3, SVR en 5k seed 42) en memoria.
- [x] Imprime tabla comparativa + `assert` contra `comparativa.csv` (tol 0.01).
- [x] Retira celda ancla SVR (la reemplaza el entreno) y fast-demo 2k (la reemplaza
  el oficial). Conserva procedencia MD + nota SVR-5k.
- [x] Anade MD estilo viejo: glosario fila, baseline-primero, regla de empate.
- Verificado: `nbconvert --execute 02` verde; RMSE tabla == CSV.

## T2 — 03: MLP base+E1/E2/E3 en vivo + SHAP vivo  [x]
- [x] Celda que importa `EXPS`, `BASE_KW` de `track_clase.train_mlp` y entrena los
  4 en memoria; tabla + `assert` vs `mlp_comparativa.csv` (tol 0.05).
- [x] Retira celda ancla E1 (la reemplaza el loop). Conserva ancla permutacion y CV.
- [x] Celda SHAP viva: XGB mejores params + TreeExplainer + top + PNG (sin CSV).
- [x] MD estilo viejo: hipotesis ya visibles; anade que-vemos con numeros.
- Verificado: `nbconvert --execute 03` verde; E1 == 7.7019.

## T3 — 04: LGBM entrenado en vivo  [x]
- [x] Celda que entrena `make_lgbm(42)` sobre ventanas fit-units en memoria;
  metricas + `assert` vs `comparativa_ventanas.csv` (tol 0.01/0.5).
- [x] Retira ancla con joblib guardado (la reemplaza el entreno). Conserva
  shapes, CV diagnostica, procedencia.
- Verificado: `nbconvert --execute 04` verde; RMSE == 7.067.

## T4 — 05: C completo en memoria + diagnostico estilo viejo  [x]
- [x] Celda BiLSTM-42 + curva de perdida + que-vemos (reutiliza `run_seed` seed 42,
  epochs 22; sin `save_ensemble`).
- [x] Celdas OOF/beta + meta/EMA + conformal con TIPs (sin persistir).
- [x] Celdas diagnostico: residuos, MAE por tramo, por motor (estilo 03-viejo §11).
- [x] Nota de procedencia con divergencia esperada (~4.3x vivo vs 4.251/4.338).
  Conserva ancla manifest, multiseed vivo, tabla viva, D11.
- Verificado: cadena ejecutada 1.802 s (entreno + inferencia, cero escrituras a
  `models/`). Runs: SEC_A 694 chars + curva de perdida; SEC_B beta OOF; SEC_C
  comparativa viva (LGBM/BiLSTM/BiLSTM+EMA/Hibrido) + scatter; SEC_D banda
  conformal 90 % (cobertura test 1.000, ancho mediano 29.89); SEC_E residuales
  (media +0.426, |res|>10 en 259 ventanas) y MAE por tramo (RUL<25: 1.233,
  25-60: 4.112, >60: 7.999).
- Notebook: 37 celdas, 3 imagenes embebidas (`loss_curve_c`,
  `real_vs_predicho_bundle_c`), ids de ejecucion 1-5.

## T5 — 01 repaso + cierre  [x]
- [x] 01 repasado (solo markdown): glosario de terminos, "como leer" en las 4
  cabeceras de figura, TIP de fuga y bloque de procedencia de datos.
- [x] `pytest -q`: 232 passed, 6 skipped, 3 failed. Los 3 fallos
  (`test_clase_bundle_c.py`) son contaminacion **preexistente** del suite
  completo: `test_audit_fixes.py:237` y `test_ui_rules.py:166` inyectan un
  `ds02_rul` falso en `sys.modules`, y el import posterior responde
  "unknown location". Ejecutado en aislamiento: `3 passed in 12.87s`.
- [x] `git status`: sin cambios en `models/`, `src/`, `app/cache/` (solo
  notebooks 01-05 + `docs/plans/` + este change).

## Decision de alcance (registrada)
- B no se reentrena en 05: se carga y se evalua. El protocolo que construye C es
  el mismo que construyo B, y una replica limpia daria ~4.3x por
  no-determinismo de TF, generando dos cifras de "B" en defensa.
- C se reentrena integro en 05 paso a paso, sin persistir artefactos.
