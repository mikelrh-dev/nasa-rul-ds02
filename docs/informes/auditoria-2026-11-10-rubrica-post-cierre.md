# Auditoría 2026-11-10 (post-cierre) — Rúbrica Reto 1 v5

> **Modo:** solo lectura. No se modificó código, artefacto, notebook, dato ni configuración.
> **Plan:** `docs/plans/plan-auditoria-2026-11-10-rubrica-post-cierre.md`
> **Framework:** `docs/framework_auditoria.md` v1.0 (A–Q, F0–F6, G0–G6)
> **Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf`, extraída con `pdfplumber` (9 págs.)
> **Comparación:** `docs/informes/auditoria-2026-11-10-rubrica-integral.md` (árbol sucio, `025dcb2`)
> **Estado de pendientes:** [`../pendiente/pendientes-2026-11-10-post-auditoria.md`](../pendiente/pendientes-2026-11-10-post-auditoria.md)

---

## 1. Veredicto

**SAA 10,0 / 10 · PIA 9,4 / 10 · MIA 10,0 / 10.** Techo global: **PIA 9,4**.

| Asignatura | Nota | Techo | Qué la limita |
| --- | --- | --- | --- |
| **SAA** | **10,0** | 10 | Nada de la rúbrica. Reservas menores: PNG duplicados y el desempate del grano ventana. |
| **PIA** | **9,4** | 10 | PIA-4 = 7: la ablación `cyc_norm` no es una run de MLflow y el store no viaja en git. |
| **MIA** | **10,0** | 10 | Nada. MIA-3 pasa a 10 por la acción no vista en clase (API propia en HANGAR), con reservas. |

Sube respecto de la auditoría anterior (SAA 9,7 · PIA 9,4 · MIA 9,0): el 4.368 quedó rotulado
como obsoleto en todas las fuentes (SAA-8 → 10) y el flujo n8n ganó una acción novedosa
(MIA-3: 7 → 10). PIA no se mueve porque su límite no era documental sino de registro.

## 2. Baseline (F0/G0)

| Comprobación | Valor |
| --- | --- |
| HEAD | `c14d91b` · 2026-11-10 12:26 · `docs: cifras 4.368 y 0.9012 etiquetadas y specs alineadas` |
| Árbol | **94 rutas**: 13 `M` + 81 `??`, **todas** bajo `mlruns/` |
| Versionados | 1761 |
| `ensemble.joblib` | `d6c70142…1a952dd` = `artifacts.ensemble_sha256` ✅ |
| `bilstm_ds02.keras` | `bf9620a7…cfe8434` = manifiesto ✅ |
| `scaler.joblib` | `acccfab3…9541f8d` = manifiesto ✅ |
| `ds02_manifest.json` | `6089457c…83ea40`; sello de `app/cache` = SHA real → `seal_ok True` |
| Manifiesto | `clase-bundle-C`, seed 42, py 3.12.10, RMSE 4.338 / MAE 3.227 / R² 0.9461 / NASA 2336.2, `macro_rmse 5.0153` |

**G0: PASA.** El binario que sirve es el que el manifiesto firma.

## 3. F1 — mecánica y suite (G1)

| Comprobación | Resultado |
| --- | --- |
| `compileall src app scripts tests` | exit **0** |
| `freeze_rules_evidence.py` | exit **0** |
| `freeze_oof_instrument.py --check` | exit **0** · cobertura 0.901643 · 14 915 filas puras · banda reproduce `calibracion_banda.json` |
| `backfill_mlflow.py --check` | exit **0** · «13 runs (9 fila + 4 ventana), export y store coinciden, sin artefactos» |
| Suite completa | **444 passed, 1 skipped in 246,64 s, exit 0** (`-q -rs -p no:cacheprovider`) |
| Skip | 1, el mismo de siempre (`tests/test_mia_rules.py:181`, `@needs_oof`) |

## 4. Matriz de 20 criterios

Escala 0/3/7/10. Evidencia = `path:línea` o comando.

### SAA — 10,0

| # | Criterio (peso) | Nota | Evidencia | Reserva |
| --- | --- | --- | --- | --- |
| 1 | IA débil (5 %) | 10 | `README.md:29`: compara con AGI y razona por qué no transfiere | — |
| 2 | Tipo de aprendizaje (10 %) | 10 | `README.md:29`: supervisado + regresión + diferencia con no supervisado | — |
| 3 | Dataset y campos (5 %) | 10 | `README.md:49-69` (nulos por campo) + `:73-84` (campos quitados, por qué y evidencia) | — |
| 4 | ≥5 gráficos comentados (5 %) | 10 | NB01: 26 celdas MD; bar 6, hist 3, box 2, scatter 2, heatmap 2 | — |
| 5 | Nulos + variable nueva (5 %) | 10 | `README.md:71` (MAR T30, ffill causal) + `fase_vuelo` justificada | — |
| 6 | 5 modelos + extra (30 %) | 10 | `resultados/comparativa.csv` 5 filas con `GridSearchCV` + `GroupKFold` (`train_clasicos.py:30,38`); híbrido C como extra (4.338 vs LGBM 7.067) | Granos distintos (fila/ventana), declarado |
| 7 | MLP base + 3 experimentos (20 %) | 10 | `train_mlp.py:38 EXPS` con hipótesis por experimento; `mlp_comparativa.csv` 4 filas | — |
| 8 | Métricas y errores (10 %) | 10 | `README.md:144` publica 4.338 oficial + 4.324 ± 0.107 de variabilidad y **rotula** 4.368/NB05/NB06 como obsoletos o históricos | — |
| 9 | Elección + SHAP (5 %) | 10 | `src/clase/tabla_final.py:81-92`: ordena por `rmse_val` y documenta la reserva del grano ventana; SHAP con aditividad en NB07 | El grano ventana sin `rmse_val` cae en `rmse_test` (declarado en el código) |
| 10 | Pregunta individual (5 %) | 10 | `docs/defensa/guiones-15min.md` §1 con `path:línea` | No verificable desde el repo |

### PIA — 9,4

| # | Criterio (peso) | Nota | Evidencia | Qué falta para el 10 |
| --- | --- | --- | --- | --- |
| 1 | README + docstrings (10 %) | 10 | 6 apartados + captura + extras; **0 funciones públicas sin docstring** en `src/` y `app/` (AST) | — |
| 2 | Carpetas y funciones (10 %) | 10 | `data/ notebooks/ src/ app/ models/ n8n/ resultados/`; `requirements.txt` pineado; `requires-python >=3.12` | — |
| 3 | Pipeline sklearn (20 %) | 10 | `pipeline_clase.py:27` `ColumnTransformer`; joblib con `pre`+`reg` y predice caso nuevo | — |
| 4 | MLflow (20 %) | **7** | 13 runs (9 fila + 4 ventana) con params/métricas; `comparativa.csv` 13 filas; 3 PNG; `--check` OK | La ablación `cyc_norm` (tabla en `README.md:286-292`) **no es una run**: `grep -ril cyc_norm mlruns --include=meta.yaml` → 0; el store no está versionado |
| 5 | App Streamlit (25 %) | 10 | 4 pestañas (`app/dashboard_ds02.py:1176`), métricas de test, `RUL p35` junto a `L_inf` y decisión, envío n8n | — |
| 6 | Pregunta individual (15 %) | 10 | `guiones-15min.md` §2 | No verificable desde el repo |

### MIA — 10,0

| # | Criterio (peso) | Nota | Evidencia | Reserva |
| --- | --- | --- | --- | --- |
| 1 | Negocio con dato (20 %) | 10 | `README.md:23-25`: AOG 10 000–15 000 USD/h, quién decide, qué evita | — |
| 2 | ≥6 reglas (30 %) | 10 | `src/mia/reglas.py:246-270`: 6 de decisión + 2 de corrección, prioridad y `porque`; R1 seguridad prioridad 10 | — |
| 3 | Flujo n8n (35 %) | **10** | Webhook `ds02/decision` + Switch de 3 ramas; HANGAR encadena Postgres → Calendar → Gmail → **`HANGAR API propia`** (`POST localhost:8000/n8n-decision`), acción **no vista en clase**; `tests/test_n8n_propia.py:139` la fija | Flujo `active:false`, credencial `REEMPLAZAR_CREDENCIAL`, no ejecutado de punta a punta contra la instancia |
| 4 | Pregunta individual (15 %) | 10 | `guiones-15min.md` §3 | No verificable desde el repo |

### Nota ponderada

```
SAA = (10·5 + 10·10 + 10·5 + 10·5 + 10·5 + 10·30 + 10·20 + 10·10 + 10·5 + 10·5) / 100 = 10,00
PIA = (10·10 + 10·10 + 10·20 +  7·20 + 10·25 + 10·15) / 100                          =  9,40
MIA = (10·20 + 10·30 + 10·35 + 10·15) / 100                                          = 10,00
```

## 5. Hallazgos abiertos

### Altos

| ID | Bloque | Hallazgo | Reproducción | Propuesta |
| --- | --- | --- | --- | --- |
| **A-01** | H/PIA | El store MLflow de los 13 runs **no está versionado**: 13 `meta.yaml` modificados + 81 runs untracked. Un clon limpio no reproduce `backfill_mlflow.py --check` (depende de `./mlruns` local). | `git status --porcelain \| wc -l` → 94; `git ls-files mlruns \| wc -l` → 1010 pero sin los 81 nuevos | Versionar/ignorar explícitamente el store, o generar los 13 runs desde `comparativa.csv` como hace el backfill |
| **A-02** | M/G1 | `@needs_oof` sigue apuntando a `_p1_oof_cache.npz` (inexistente) en vez del instrumento versionado `src/mia/instrumento_oof.npz`; el guard de `tests/test_audit_fixes.py` está muerto. | `grep -rn @needs_oof tests/` → solo `test_mia_rules.py:181`; `ls _p1_oof_cache.npz` → no existe | Re-apuntar el fixture al instrumento (ADR-012) y borrar el guard muerto |

### Medios

| ID | Bloque | Hallazgo | Reproducción |
| --- | --- | --- | --- |
| **M-01** | PIA-4 | La ablación `cyc_norm` está en `README.md:286-292` y en `resultados/ablacion_cycnorm_rmse.png`, pero **no como run**: 0 coincidencias en `mlruns`. Es lo único que separa PIA-4 del 10. | `grep -ril "cyc_norm\|abla" mlruns --include=meta.yaml` → 0 |
| **M-02** | H | `src/mia/instrumento_oof.npz` (`04d972ed…`) está versionado **sin hash en el manifiesto**. | `grep -c instrumento_oof models/ds02_manifest.json` → 0 |
| **M-03** | C/H | `scripts/predict.py:22` resuelve `models/v3_bundle.joblib`, que no existe; el manifiesto lo declara archivado (`historical_reference:180-181`) y `v3_finalize.py` ya no lo escribe. El CLI FD001 muere con `RuntimeError`. | `sed -n '22p' scripts/predict.py`; `ls models/v3_bundle.joblib` |
| **M-04** | Q/A | `app/registros_flota.json.hermes-respaldo` (49 B) está **versionado** desde `fbec2d2`: fichero de respaldo de Hermes dentro de `app/`. | `git ls-files \| grep hermes-respaldo` |
| **M-05** | N/Q | `docs/pendiente/deuda-riesgo-7-2026-11-10.md` está obsoleto: dice «28 `meta.yaml` versionados (106 en disco)» cuando hay 1010/109, y cita `tests/test_mlflow_ui.py`, que no existe. | `find mlruns -name meta.yaml \| wc -l` → 109; `ls tests/test_mlflow_ui.py` → no existe |

### Bajos

| ID | Bloque | Hallazgo |
| --- | --- | --- |
| **B-01** | G | Cobertura en dos valores sin rótulo de alcance: `e00:145` y `README.en:365` dicen 0.9012; el instrumento mide 0.901643 (`project.md` ya dice 0.9016). |
| **B-02** | N | `docs/assets/` duplica 9 PNG de `resultados/`: 7 idénticos y **2 divergentes** (`real_vs_predicho_bundle_c.png`, `shap_importancia.png`). |
| **B-03** | H | Manifiesto 4.338/3.227 vs caché 4.3382/3.2266 (dos precisiones, sin contradicción). |
| **B-04** | H | `freeze_oof_instrument.py:46,80` carga `notebooks/artifacts_c/nb2_selection.joblib` (gitignored) sin verificar hash. |
| **B-05** | L | `n8n/flujo.json` lleva 2 × `REEMPLAZAR_CREDENCIAL` y `active:false`: no es importable y ejecutable tal cual. |
| **B-06** | G | `docs/evidencia/mlflow/comparativa.csv` exporta 13 filas, pero `mlruns` en disco tiene 109 `meta.yaml` (27 runs antiguos + 81 sin seguimiento): el export no cubre el store entero. |

## 6. Cerrado desde la auditoría anterior

| Antes | Estado actual |
| --- | --- |
| **G-01** 4.368 como «regenerable» (C) | **Cerrado**: 4.368 rotulado obsoleto en `README.md:144`, `README.en.md:80`, `AGENT.md:6`, `e00:47,166`, `framework:560`, `notebooksMD/05:374`, `06:559` |
| **N-02** `resultados/` fuera de HEAD (A) | **Cerrado**: 38 ficheros versionados |
| **L-01** `n8n/flujo.json` sin commitear | **Cerrado**: commit `9ca9df6` |
| **C-01** escritor `v3_bundle` activo | **Cerrado**: `scripts/v3_finalize.py` ya no lo escribe; el manifiesto conserva solo el hash histórico |
| **P-03** 1 función sin docstring | **Cerrado**: 0 públicas sin docstring (AST sobre `src/` y `app/`) |
| **SAA-3** «No se descarta ningún campo» | **Cerrado**: `README.md:73-84` ahora dice qué se quita y por qué |
| **I-01** `project.md` 0.9012 vs 0.9016 | **Parcial**: `project.md` corregido a 0.9016; quedan `e00:145` y `README.en:365` (B-01) |
| **MIA-3** = 7 | **Cerrado**: acción novedosa en HANGAR → 10 |

## 7. Límites de esta auditoría

1. **Cobertura por muestreo**, no fila a fila: no se generó `cobertura.csv` con 1761 veredictos.
2. **No se reentrenó** ni se recalibró la banda; no se releyó el test.
3. **n8n:** se auditó el JSON, las conexiones y los tests; la instancia responde 200 pero no se
   inspeccionó su base de datos ni se lanzaron ejecuciones nuevas. «Flujo válido» ≠ «flujo ejecutado».
4. **G2** se comprobó por existencia de ficheros y referencias, no abriendo cada imagen.
5. **Preguntas individuales** (SAA-10, PIA-6, MIA-4) no son puntuables desde el repositorio.
6. Las notas son estimaciones con la rúbrica v5, no una corrección oficial.

## 8. Firma G5

- F0: **94 rutas** (`git status --porcelain`), todas bajo `mlruns/`.
- F6: las mismas 94 rutas + este informe y su plan (2 ficheros nuevos). Nada más se tocó:
  ni código, ni artefactos, ni notebooks, ni datos.

## 9. Anexo — salidas literales

```text
$ git rev-parse HEAD
c14d91b5fbb1bd92736e452cf1784990911dee42
$ git status --porcelain | wc -l
94
$ python -m compileall -q src app scripts tests ; echo $?
0
$ python scripts/freeze_oof_instrument.py --check
OOF coverage (corrected point)  -  0.901643  reported
pure OOF rows                  14915  14915.000000  ok
$ python scripts/backfill_mlflow.py --check
OK: 13 runs (9 fila + 4 ventana), export y store coinciden, sin artefactos.
$ python -m pytest tests -q -rs -p no:cacheprovider
SKIPPED [1] tests/test_mia_rules.py:181: _p1_oof_cache.npz missing
444 passed, 1 skipped in 246.64s (0:04:06)
EXIT=0
```

```text
$ grep -rn "4\.368" README.md README.en.md AGENT.md
README.md:144: ... la antigua 4.368 ... queda obsoleta y no debe citarse
README.en.md:80: ... the old 4.368 ... is obsolete and must not be cited
AGENT.md:6: ... the old 4.368 ... is obsolete
$ grep -ril "cyc_norm\|abla" mlruns --include=meta.yaml | wc -l
0
$ grep -rn "@needs_oof" tests/ | grep -v pyc
tests/test_mia_rules.py:181:@needs_oof
```
