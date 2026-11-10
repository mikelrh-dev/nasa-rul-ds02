# Auditoría integral 2026-11-10 — Rúbrica Reto 1 (SAA + PIA + MIA)

> **Modo:** solo lectura. No se modificó código, artefacto, notebook, dato ni configuración.
> **Plan ejecutado:** `docs/plans/plan-auditoria-2026-11-10-rubrica-integral.md`
> **Framework:** `docs/framework_auditoria.md` v1.0 (bloques A–Q, fases F0–F6, puertas G0–G6)
> **Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (escala 0 / 3 / 7 / 10)
> **Orquestación:** ondas de ≤3 subagentes con ventana deslizante + 2 jueces independientes (F5)

---

## 1. Veredicto

**SAA 9,7 / 10 · PIA 9,4 / 10 · MIA 9,0 / 10.** Techo global: **MIA 9,0** (MIA-3 techado en 7).

| Asignatura | Nota | Techo | Qué la limita |
| --- | --- | --- | --- |
| **SAA** | **9,7** | 10 | SAA-8 capado a 7: `README.md:144`/`:218` publican 4.368 como «regenerable» y no lo es (G-01, C). |
| **PIA** | **9,4** | 10 | PIA-4 capado a 7: ablación `cyc_norm` no es run (P-02) + reproducibilidad del store (P-01/N-02). |
| **MIA** | **9,0** | **9,0** | MIA-3 = 7: las acciones del flujo son las vistas en clase (0 novedosas) + flujo no ejecutable tal cual. |

La estimación del plan era SAA 10,0 / PIA 10,0 / MIA 9,0. Los jueces independientes bajaron SAA y PIA al aplicar la regla del framework («la nota se baja, no se negocia»).

---

## 2. Baseline (F0) — congelado al empezar

| Comprobación | Valor |
| --- | --- |
| Rama / HEAD | `fix/auditoria-2026-11-10` · `025dcb20d301b9fd30193b9024693b3aee949f87` |
| Último commit | `025dcb2` 2026-11-09 23:33:56 +0100 |
| Árbol | **204 rutas** (36 A, 78 M, 1 D, 89 `??`); el plan era 203: el `+1` es el propio plan (untracked) |
| `models/ensemble.joblib` | `d6c70142…1a952dd` = manifiesto ✅ |
| `models/bilstm_ds02.keras` | `bf9620a7…cfe8434` = manifiesto ✅ |
| `models/scaler.joblib` | `acccfab3…9541f8d` = manifiesto ✅ |
| `models/ds02_manifest.json` | `6089457c…83ea40`; sello de caché `manifest_sha256` = SHA real ✅ |
| Intérprete | `.venv/Scripts/python.exe` — Python 3.12.10 |
| Suite | **435 passed, 1 skipped** (255,62 s, exit 0); único skip `tests/test_mia_rules.py:181` |

**Límite:** el contenido auditado **no está en git** (78 modificados, 36 adds). El informe describe el árbol de trabajo en `025dcb2`, no un commit.

---

## 3. Alcance

**Dentro:** 20 criterios de rúbrica; bloques A–Q del framework; cifras manifiesto ↔ e00 ↔ README ↔ CSV; artefactos y hashes; suite y gates; n8n (estático + instancia viva); MLflow (store + export + capturas).

**Fuera:** reentrenar, recalibrar bandas, re-leer el test, desplegar, `git push`, credenciales reales, Docker (bloque C: n/a por decisión 2026-11-07).

**Dependencias externas:** n8n sí tiene instancia viva (`localhost:5678`, `~/.n8n/database.sqlite`); MLflow tiene server vivo en `127.0.0.1:5001` levantado durante la auditoría (file store `./mlruns`).

---

## 4. Método y orchestración

| Onda | Fase | Agentes | Entregable |
| --- | --- | --- | --- |
| 0 | F0 baseline | coordinador | §2 |
| 1 | F1 mecánica + inventario + G2 | 3 | `$TMPDIR/f1a_mecanica.txt`, `f1b_resumen.txt`+`cobertura.csv`, `f1c_enlaces.txt` |
| 2 | F2 SAA + F3 PIA + F4 MIA | 3 | `f2_saa.md`, `f2_pia.md`, `f2_mia.md` |
| 3 | F4 transversal (G, H, M–Q) | 3 | `f4a_cifras.md`, `f4b_artefactos.md`, `f4c_tests_deuda.md` |
| 4 | F5 jueces | 2 | `juez1.csv`/`juez1_veredicto.md`, `juez2.csv`/`juez2_veredicto.md` |
| 5 | F6 síntesis | coordinador | este informe + CSV |

Los subagentes escribieron solo en `$TMPDIR` (scratch de Hermes). El coordinador escribió el informe y los CSV de salida.

---

## 5. Hipótesis (H1–H15): resueltas

| ID | Hipótesis | Veredicto |
| --- | --- | --- |
| H1 | 4.368 no es regenerable desde el CSV vigente | **Confirmada** (4.3677 obsoleto vs 4.3243 vigente) |
| H2 | 4.368 solo reproduce la comparativa obsoleta | **Confirmada** |
| H3 | `e00:47` desactualizado | **Confirmada** (era correcto al escribirse; el rerun del 11-09 lo dejó viejo) |
| H4 | MIA-3 techado en 7 | **Confirmada** por J2 (instancia n8n: 7 tipos de nodo subconjunto de los flujos de clase) |
| H5 | Flujo no ejecutable | **Matizada**: el JSON versionado no es ejecutable tal cual, pero la instancia ejecutó 29 veces |
| H6 | Guard `needs_oof` al fichero inexistente | **Confirmada** (A) |
| H7 | `predict.py` → `v3_bundle.joblib` inexistente | **Refutada en su cláusula literal** (el manifiesto sí lo referencia en `historical_reference:180-181`); **confirmada en sustancia** |
| H8 | `project.md:104` (0.9012) vs `:107` (0.9016) | **Confirmada** |
| H9 | Alias `mejor_modelo.joblib` = XGB | **Confirmada** |
| H10 | `n8n/flujo.json` sin commitear | **Confirmada** (` M`) |
| H11 | `deuda-riesgo-7` obsoleto | **Confirmada** (106→109; `test_mlflow_ui.py` inexistente) |
| H12 | Memoria Engram #3006 obsoleta | **Confirmada** (406 → 435/436) |
| H13 | `docs/assets/` duplica PNG | **Confirmada** (9 compartidos: 7 idénticos, 2 divergentes) |
| H14 | Dos precisiones de métricas | **Confirmada** (B, sin contradicción numérica) |
| H15 | Árbol sucio | **Confirmada** (204, no 203) |

---

## 6. Matriz de 20 criterios (nota definitiva)

Escala 0 / 3 / 7 / 10. Nota del juez independiente, no del plan.

### SAA — 9,7

| # | Criterio (peso) | Nota | Evidencia | Qué falta para el 10 |
| --- | --- | --- | --- | --- |
| 1 | IA débil (5 %) | 10 | `README.md:29` (compara con AGI y razona) | — |
| 2 | Tipo de aprendizaje (10 %) | 10 | `README.md:29` (supervisado + regresión + no supervisado) | — |
| 3 | Dataset y campos (5 %) | 10 | `README.md:49-69` (nulos por campo) + `:73-82` (campos quitados y por qué) | La frase `README.md:82` «No se descarta ningún campo» contradice la tabla (B) |
| 4 | ≥5 gráficos (5 %) | 10 | NB01 Fig. 1–5: barras, histograma, boxplot, dispersión, heatmap, cada uno comentado | — |
| 5 | Nulos + variable nueva (5 %) | 10 | `README.md:71` (MAR T30 + ffill causal); `fase_vuelo` | — |
| 6 | 5 modelos + extra (30 %) | 10 | `comparativa.csv` 5 clásicos con GridSearchCV/GroupKFold; híbrido C como extra | El extra es grano **ventana** y los clásicos grano **fila** (B) |
| 7 | MLP base + 3 exp (20 %) | 10 | `train_mlp.py:38` EXPS con hipótesis; `mlp_comparativa.csv` | — |
| 8 | Métricas y errores (10 %) | **7** | Tablas train/val/test + real-vs-pred + lectura de negocio | **Publica 4.368 como «regenerable» y no lo es** (G-01, C) |
| 9 | Elección + SHAP (5 %) | 10 | Elección por validación; SHAP en fold-0 con aditividad | `tabla_final.py:85-86` ordena ventana por `rmse_test` (B); `shap_xgb_top.joblib` reescrito por un test |
| 10 | Pregunta individual (5 %) | 10 | `docs/defensa/guiones-15min.md` §1 con `path:línea` | No verificable desde el repo |

### PIA — 9,4

| # | Criterio (peso) | Nota | Evidencia | Qué falta para el 10 |
| --- | --- | --- | --- | --- |
| 1 | README + docstrings (10 %) | 10 | 6 apartados + captura + extras; 344/345 públicas con docstring | 1 función sin docstring (`mlflow_live.py:44`) |
| 2 | Carpetas y funciones (10 %) | 10 | Estructura del reto completa; `requirements.txt` pineado | — |
| 3 | Pipeline sklearn (20 %) | 10 | `pipeline_clase.py:27` ColumnTransformer; joblib con `pre`+`reg` y predice caso nuevo | — |
| 4 | MLflow (20 %) | **7** | 13 runs con params/métricas; `comparativa.csv`; 3 PNG | Ablación `cyc_norm` no es run (P-02); store no reproducible desde clon limpio (P-01/N-02) |
| 5 | App Streamlit (25 %) | 10 | 4 pestañas; métricas de test; `RUL p35` junto a `L_inf` y estado; envío n8n | — |
| 6 | Pregunta individual (15 %) | 10 | `guiones-15min.md` §2 | No verificable desde el repo |

### MIA — 9,0

| # | Criterio (peso) | Nota | Evidencia | Qué falta para el 10 |
| --- | --- | --- | --- | --- |
| 1 | Negocio con dato (20 %) | 10 | `README.md:23,25` (AOG 10–15k USD/h, quién, qué evita) | — |
| 2 | ≥6 reglas (30 %) | 10 | `src/mia/reglas.py:254-271`: 6 de decisión + 2 corrección, prioridad + porqué + R1 | — |
| 3 | Flujo n8n (35 %) | **7 (techo)** | Webhook + Switch 3 ramas con acciones distintas | Las 4 acciones son las vistas en clase (0 novedosas); JSON versionado no ejecutable tal cual |
| 4 | Pregunta individual (15 %) | 10 | `guiones-15min.md` §3 | No verificable desde el repo |

### Nota ponderada

```
SAA = (10·5 + 10·10 + 10·5 + 10·5 + 10·5 + 10·30 + 10·20 +  7·10 + 10·5 + 10·5) / 100
    =  970 / 100 = 9,70
PIA = (10·10 + 10·10 + 10·20 +  7·20 + 10·25 + 10·15) / 100
    =  940 / 100 = 9,40
MIA = (10·20 + 10·30 +  7·35 + 10·15) / 100
    =  895 / 100 = 8,95 → 9,0
```

---

## 7. Hallazgos

### Críticos

| ID | Bloque | Hallazgo | Evidencia | Propuesta |
| --- | --- | --- | --- | --- |
| **G-01** | G | La media **4.368 ± 0.053 / NASA 2355.2 ± 24.6** publicada como «regenerable» **no lo es**. `comparativa_c_multisemilla.csv` (mtime 11-06) está obsoleto y su columna `origen` miente: dice `bundle_c_multiseed.csv`, que hoy trae 7=4.211 / 123=4.424, no 4.429 / 4.336. | `README.md:144,218`; `AGENT.md:6`; `framework_auditoria.md:560`; medias 4.3677 vs 4.3243 | Citar la media vigente (4.3243 ± 0.107) o regenerar la comparativa; alinear e00 y README |

### Altos

| ID | Bloque | Hallazgo | Evidencia | Propuesta |
| --- | --- | --- | --- | --- |
| **N-02** | G/H | `resultados/` **no está en HEAD** (0 ficheros; está stageado). Un clon limpio no tiene los CSV y `backfill_mlflow.py --check` falla con `FileNotFoundError`. | `git ls-tree -r HEAD \| grep -c ^resultados/` → 0; 36 en el índice | Commitear `resultados/` o declarar que el clon limpio no reproduce la evidencia |
| **P-01** | H/Q | El store MLflow de los 13 runs vigentes **no está versionado** (los 81 runs activos son untracked; el índice tiene 13 borrados + 13 duplicados). En HEAD el CSV sí coincide con el store, pero el working tree tiene el CSV modificado con otros IDs. | `git ls-files mlruns \| grep -c <id>` → 0/13; `docs/evidencia/mlflow/comparativa.csv` está ` M` | Commit de evidencia o desversionado con copia congelada (B5 como está redactado no aplica) |
| **M-01** | M/G1 | El guard `needs_oof` apunta a `_p1_oof_cache.npz` (gitignored, inexistente) → 1 skip. El guard de `test_audit_fixes.py:43-45` está **muerto**. El instrumento versionado no sirve al test (claves distintas). | `grep -rn "@needs_oof" tests/` → solo `test_mia_rules.py:181`; `ls _p1_oof_cache.npz` → no existe | Re-apuntar el guard al instrumento `src/mia/instrumento_oof.npz` o declarar el skip como esperado |
| **C-01** | C/D/H | `scripts/predict.py:22` apunta a `models/v3_bundle.joblib` (inexistente); el guard lanza `RuntimeError`. El manifiesto sigue referenciándolo (`historical_reference:180-181`) y `scripts/v3_finalize.py:82` **sigue escribiéndolo**. | `ls models/v3_bundle.joblib` → no existe; `sed -n '82p' scripts/v3_finalize.py` | Declarar el CLI FD001 fuera de servicio y retirar el escritor |
| **MIA-3** | L | **Techado en 7**: las 4 acciones (Sheets, Postgres, Calendar, Gmail) son las vistas en clase; 0 acciones novedosas. | `n8n/flujo.json` nodos; `workflow_history` de la instancia (`m3cI2u3OH5yXK4gs`, `39fg1Y8tF7rBcStR`) | Añadir una acción no vista en clase para llegar al 10 |
| **H-MIA-2** | L | El `flujo.json` versionado **no es el vivo**: repo `active:false` + `headerAuth` con `REEMPLAZAR_CREDENCIAL`, 14 nodos; instancia `active:1`, webhook sin auth, 10 nodos, `versionId de0ce3a5`. La mejora de seguridad del repo **no está desplegada**. | `git status --porcelain n8n/flujo.json` → ` M`; diff 11+/4- | Commitear el flujo y alinear `active`/auth con el entorno |

### Medios

| ID | Bloque | Hallazgo | Evidencia |
| --- | --- | --- | --- |
| **G-02** | G | `e00-cifras-autoritativas.md:47` y `:166` describen `bundle_c_multiseed.csv` con 7=4.429 / 123=4.336; hoy trae 4.211 / 4.424. | `sed -n '47p' e00…` vs `cat resultados/bundle_c_multiseed.csv` |
| **G-03** | G | `docs/framework_auditoria.md:560` publica 4.368 como «cifra vigente», contradiciendo `e00:166`. | `grep -n 4.368 docs/framework_auditoria.md` |
| **G-04** | G | `notebooksMD/05:374` y `/06:559` declaran 4.368 «autoritativa» e invierten la jerarquía de fuentes. | Ambas líneas vs `e00:166` |
| **I-01** | G/I | `openspec/project.md:104` publica 0.9012 y `:107` 0.9016; el instrumento mide 0.901643. | `grep -n "0.9012\|0.9016" openspec/project.md`; `freeze_oof_instrument.py --check` |
| **P-02** | PIA | La ablación `cyc_norm` es un experimento **no registrado como run** → PIA-4 techo 7. | `README.md:284-292`; `scripts/ablate_meta_cycle.py` |
| **H-02** | H | El instrumento OOF está versionado pero **sin hash en el manifiesto** (SHA real `04d972ed…`, 0 hits en `ds02_manifest.json`). | `git ls-files src/mia/instrumento_oof.npz`; `grep -c 04d972ed models/ds02_manifest.json` |
| **H-03** | H | `freeze_oof_instrument.py:80` carga `notebooks/artifacts_c/nb2_selection.joblib` (gitignored, sin manifiesto) **sin verificación**. | `sed -n '80p' scripts/freeze_oof_instrument.py`; `.gitignore:67` |
| **L-01** | L | `n8n/flujo.json` modificado y sin commitear. | `git status --porcelain n8n/flujo.json` → ` M` |
| **A1-B** | H/Q | El alias `mejor_modelo.joblib` es copia manual del XGB (8.2173), no del E2 (7.3404). Riesgo 7 declarado. | `models/README.md:22-32`; `tests/test_clase_rubrica.py:51,73` |
| **H-MIA-4** | L | 4 ejecuciones con error (ids 147, 148, 158, 159) sin documentar: 147 HANGAR (Calendar credential revoked), 148/158/159 INSPECCIÓN (Sheets 404). | `~/.n8n/database.sqlite` `execution_entity` |
| **MIA-EJEC** | L | El repo afirma «inactivo / no ejecuta nada / no se afirma ejecución real», pero la instancia ejecutó **29 veces el 2026-11-07 (25 success / 4 error)** con efectos reales (Postgres id=9, Calendar `ugjgger592ml79oengrs20oges`, Gmail `1a1b7e725375a554`). **Matiz:** 14 POST son `curl` manuales y 15 `Python-urllib` scriptados; **ninguna es atribuible a la app Streamlit**. | `src/clase/README.md:19,41`; `guiones-15min.md:6,125`; `presentacion-ds02.html:744,750-751` vs `~/.n8n/database.sqlite` |

### Bajos

| ID | Bloque | Hallazgo |
| --- | --- | --- |
| **G-05** | G | `freeze_rules_evidence.py:97` fija `EXPECTED["coverage"]=0.9012`; solo alcanza con `--cache` y queda fuera del gate por defecto. |
| **H-01** | H | Manifiesto 4.338/3.227 vs caché 4.3382/3.2266 (dos precisiones, sin contradicción numérica). |
| **H-06** | H | La caché no verifica los hash de los parquet fuente (`cache_available()` sí verifica `manifest_sha256`, `windows_sha256`, `rows_sha256`). |
| **N-01** | N | `docs/assets/` duplica 9 PNG de `resultados/`: 7 byte-idénticos y 2 divergentes (`real_vs_predicho_bundle_c.png`, `shap_importancia.png`). |
| **P-03** | PIA | 1 función pública sin docstring (`src/ds02_rul/mlflow_live.py:44`). |
| **P-04** | PIA | El «268/268 docstrings» de la v2 **no es reproducible** (hoy 345 públicas, 1 sin docstring; 268 no corresponde a ningún scope). |
| **P-05** | PIA | El real-vs-pred de la app es línea temporal, no dispersión. |
| **SAA-3** | SAA | `README.md:82` dice «No se descarta ningún campo» junto a la tabla de campos quitados. |
| **SAA-6** | SAA | El extra (híbrido C) es grano ventana y los 5 clásicos grano fila; `README.md:153-155` los compara directamente. |
| **SAA-9** | SAA | `tabla_final.py:85-86` ordena el grano ventana por `rmse_test`; `shap_xgb_top.joblib` lo reescribe un test con `n_filas=30` (cycle 36,667 vs 34,497 del CSV). |
| **B5** | Q | `deuda-riesgo-7` cita 106 `meta.yaml` (hoy 109) y `tests/test_mlflow_ui.py` (inexistente); el doc es untracked. |
| **MEM-01** | — | Memoria Engram #3006 («406 passed») obsoleta; hoy 435/436. |
| **H-07** | H | Los tests cargan joblib directo a propósito (aserciones de paridad, no serving). |
| **H15** | — | Árbol sucio (204 rutas); ninguna cifra es reproducible desde un clon limpio. |

---

## 8. Límites de esta auditoría

1. **Árbol sucio:** 204 rutas; el informe fija `025dcb2` y la lista, no un commit limpio.
2. **No se reentrenó nada** ni se recalibró la banda; no se releyó el test.
3. **Suite:** se ejecutó completa una vez (435 passed, 1 skip); el resto fueron spot-checks de gates.
4. **n8n:** se auditó la estructura del JSON, los tests con `urlopen` mockeado y la instancia viva (`~/.n8n/database.sqlite`); no se ejecutó un POST nuevo desde la app.
5. **MLflow:** se verificó store, export y capturas; no se reejecutaron notebooks.
6. **H4 (MIA-3):** J1 lo dio por no verificable en su totalidad (el material de clase del repo solo muestra Sheets); J2 lo confirmó con los flujos de clase presentes en la propia instancia n8n. Se toma la evidencia de J2.
7. **Las notas son estimaciones** con la rúbrica v5, no una corrección oficial. Las preguntas individuales (SAA-10, PIA-6, MIA-4) no son puntuables desde el repo.

---

## 9. Firma G5 (no modificación)

- F0: **204 rutas** (`git status --porcelain`).
- F6: **204 rutas** + los entregables de esta auditoría (`docs/informes/auditoria-2026-11-10-rubrica-integral.md` y `resultados/auditoria-2026-11-10/*.csv`, estos últimos ignorados por `.gitignore`).
- Ningún fichero del repo se arregló, renombró ni revirtió. Los hallazgos quedan **documentados, no aplicados**.

---

## 10. Anexo — comandos y salidas literales

```bash
git rev-parse HEAD                      # 025dcb20d301b9fd30193b9024693b3aee949f87
git status --porcelain | wc -l          # 204
sha256sum models/*.joblib models/*.keras models/ds02_manifest.json
#   d6c70142… *models/ensemble.joblib
#   bf9620a7… *models/bilstm_ds02.keras
#   acccfab3… *models/scaler.joblib
#   6089457c… *models/ds02_manifest.json
python -c "…manifest_sha256 == sha256(manifest)"   # True
python -m pytest tests -q -rs            # 435 passed, 1 skipped in 255.62s
python -m compileall -q src app scripts tests       # exit 0
python scripts/freeze_rules_evidence.py             # exit 0
python scripts/freeze_oof_instrument.py --check     # exit 0 (14915 filas)
python scripts/backfill_mlflow.py --check           # exit 0 (13 runs)
# medias multisemilla
#   comparativa (obsoleta) 4.367666666666667  |  bundle_c+42 (vigente) 4.324333333333334
git ls-files | wc -l                    # 1746
git status --porcelain | grep '^??' | wc -l   # 89
find mlruns -name meta.yaml | wc -l     # 109
```

---

## 11. Propuesta openspec (priorizada, no aplicada)

1. **G-01 (C):** change de cifras — regenerar `comparativa_c_multisemilla.csv` con `evaluar_c_multisemilla --desde-csv` y alinear `README.md`, `README.en.md`, `AGENT.md`, `framework_auditoria.md`, `notebooksMD/05` y `/06`, `e00` y `ADR-011` a **una** media vigente con su origen.
2. **N-02 (A/C):** commitear `resultados/` (los CSV/PNG citados) o declarar el límite de clon limpio.
3. **P-01 (A):** decidir el store MLflow (commit de evidencia o desversionado con copia congelada) y alinear el CSV del working tree con el store.
4. **M-01 (A):** re-apuntar el guard `needs_oof` al instrumento versionado o declarar el skip como esperado.
5. **C-01 (A):** declarar el CLI FD001 fuera de servicio y retirar el escritor `v3_finalize.py:82`.
6. **MIA-3 (A):** añadir una acción no vista en clase (p. ej. notificación a un endpoint propio) para desbloquear el 10.
7. **H-MIA-2 (A):** commitear `n8n/flujo.json` y alinear `active`/auth con el entorno; documentar las 4 ejecuciones con error.
8. **Medios:** G-02/G-03/G-04, I-01, P-02, H-02, H-03, A1-B.

---

## Conexiones

- Plan: `docs/plans/plan-auditoria-2026-11-10-rubrica-integral.md`
- Framework: `docs/framework_auditoria.md`
- Rúbrica: `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf`
- Cifras autoritativas: `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md`
- Auditorías previas: `docs/informes/auditoria-2026-11-06-reto1-v2.md` · `docs/informes/auditoria-2026-11-07-ds02.md`
- CSV de criterios/cobertura/hallazgos: `resultados/auditoria-2026-11-10/`
