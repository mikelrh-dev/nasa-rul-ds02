# Auditoría v2 del Reto 1 (SAA + PIA + MIA) — 2026-11-06

> **Actualización 2026-11-09 — PIA-4.** La ausencia de MLflow que puntúa esta
> auditoría queda cubierta por `openspec/changes/2026-11-09-mlflow-pia4/`:
> 17 runs en `mlruns/` (9 fila + 4 ventana + 4 ablación), export en
> `docs/evidencia/mlflow/comparativa.csv` y capturas. Las notas y puntuaciones
> de este informe son históricas (2026-11-06); no se reescriben.

> **Modo:** solo lectura. No se modificó código, artefacto, notebook, dato ni configuración.
> **Rama:** `clase-modelo-c` · **HEAD:** `a9d55a2` · **Árbol:** 49 modificados + 12 sin seguimiento
> **Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (escala 0 / 3 / 7 / 10)
> **Plan seguido:** `docs/plans/plan-auditoria-2026-11-06-reto1-v2.md`

---

## 1. Veredicto

**SAA 9,9 / 10 · PIA 7,7 / 10 · MIA 9,0 / 10.**

El modelado y la capa de decisión ya están a nivel de sobresaliente. Lo que resta no
es el sistema: es **evidencia versionada** (captura y figuras), **MLflow** (20 % de
PIA, ausente) y **una cifra multiseed que el README atribuye a un notebook que
imprime otra**. El bundle C no se tocó: sigue en 4.338 con huella verificada.

| Asignatura | Nota | Techo hoy | Qué la limita |
| --- | --- | --- | --- |
| **SAA** | **9,9** | 10 | Tabla de campos sin "campos quitados" y ausente del README raíz (SAA-3 = 7) |
| **PIA** | **7,7** | 8,0 | MLflow ausente (0/10 en el 20 %); README sin captura obligatoria (PIA-1 = 7; literal 3) |
| **MIA** | **9,0** | 10 | n8n válido pero no ejecutado y sin rama APTO desde la app (MIA-3 = 7) |

---

## 2. Línea base (F0)

| Comprobación | Resultado |
| --- | --- |
| `git rev-parse HEAD` | `a9d55a227929bdb1080f06af22c3c991630c719c` |
| Árbol | 49 `M` + 12 `??` (incluye los 7 notebooks, el manifiesto y este informe) |
| `models/ensemble.joblib` | `d6c70142…1a952dd` = manifiesto ✅ |
| `models/bilstm_ds02.keras` | `bf9620a7…4c042219` = manifiesto ✅ |
| Sello de caché | `artifact.manifest_sha256 = 1085dd67…` = SHA real del manifiesto ✅ |
| Manifiesto | `code_version clase-bundle-C`, `seed 42`, `python 3.12.10`, RMSE 4.338 / NASA 2336.2 |
| Bandas | `conformal` 17 450 (artefacto) · `conformal_decision` 14 915 (regla R6) — separadas y documentadas |

**Límite de la línea base:** el contenido auditado **no está en git** (49 archivos
modificados). El informe describe el árbol de trabajo en `a9d55a2`, no un commit.

---

## 3. Mecánica (F1)

| Comprobación | Resultado |
| --- | --- |
| `compileall src app scripts tests` | exit 0 |
| `pytest tests -q -rs -p no:cacheprovider` | **336 passed, 6 skipped, 194,70 s, exit 0** |
| Skips | 6/6 por `_p1_oof_cache.npz` ausente (los esperados; ninguno nuevo) |
| Notebooks | 7/7 con salida, **0 errores** |
| Docstrings públicas | **268 / 268 documentadas** (0 sin docstring) — cifra de 2026-11-06; hoy 344/345 (ver `docs/informes/auditoria-2026-11-10-rubrica-integral.md`) |
| App | `streamlit run app/streamlit_app.py` arranca; `/_stcore/health` → **200** |
| `docs/assets` | 9 PNG en disco, **0 versionados** (`git ls-files` vacío) |
| `resultados/` | 0 versionados (ignorado por diseño) |
| MLflow | **no está en `requirements.txt`** y **ningún módulo lo importa** |

---

## 4. Matriz de rúbrica (20 criterios)

### SAA — 9,85 → **9,9**

| # | Criterio | Nota | Evidencia | Qué falta para el 10 |
| --- | --- | --- | --- | --- |
| 1 | IA débil (5 %) | **10** | `README.md:23`; `notebooks/01` celda 3 | — |
| 2 | Tipo de aprendizaje (10 %) | **10** | `README.md:23`; NB01 celda 3 | — |
| 3 | Dataset y campos (5 %) | **7** | `src/clase/README.md` tabla con % nulos; NB01 celdas 6–7 | No dice qué campos quita y por qué; el README raíz no trae la tabla |
| 4 | 5 gráficos comentados (5 %) | **10** | NB01: 6 PNG; bar/hist/box/scatter/heatmap; celdas 10–16, 28 | — |
| 5 | Nulos + variable nueva (5 %) | **10** | `dataset_clase.py`; `auditoria_nulos.json`: 1 185 nulos (1,82 %), 9,48 % en elegibles, 0 rachas > 3; `fase_vuelo` | — |
| 6 | 5 modelos + extra (30 %) | **10** | `train_clasicos.py:128–145` (GridSearchCV + GroupKFold); `comparativa.csv` 5 filas; híbrido C como extra; SMOTE N/A justificado | — |
| 7 | MLP base + 3 exp (20 %) | **10** | `train_mlp.py` `EXPS` (hipótesis por experimento); NB02 celdas 16–17, 21 | — |
| 8 | Métricas y errores (10 %) | **10** | `comparativa.csv`; `mlp_comparativa.csv`; real-vs-pred en NB02; lectura de negocio en README | — |
| 9 | Elección + SHAP (5 %) | **10** | Elección por `rmse_val` y desempate simple; SHAP E2 (aditividad `2,1e-13`); SHAP-C en NB07 | Ver A3: el "campeón ventana" de la tabla se ordena por test |
| 10 | Pregunta individual (5 %) | **10** | `docs/defensa/guiones-15min.md`; `docs/chuleta-defensa.md` con `path:línea` | — |

### PIA — 7,70 → **7,7**

| # | Criterio | Nota | Evidencia | Qué falta para el 10 |
| --- | --- | --- | --- | --- |
| 1 | README + docstrings (10 %) | **7** | 268/268 docstrings; README con negocio, sistema, resultados y extras | **Sin captura de app** (apartado obligatorio) y sin tabla de campos en el raíz |
| 2 | Carpetas y funciones (10 %) | **10** | Estructura del reto completa; `requirements.txt` 31 líneas pinneadas | — |
| 3 | Pipeline sklearn (20 %) | **10** | `pipeline_clase.py`; `mejor_modelo.joblib` carga `pre+reg` y predice 1 caso (72,83) | — |
| 4 | MLflow (20 %) | **0** | No está en requirements ni se importa; `c27-mlflow.md` lo declara ausente | Todo el criterio |
| 5 | App Streamlit (25 %) | **10** | Arranca (200); 4 pestañas; métricas de test; caso nuevo + reglas; envío n8n; `ValueError` en datos vacíos/umbrales | — |
| 6 | Pregunta individual de código (15 %) | **10** | Guiones con archivo:línea | — |

### MIA — 8,95 → **9,0**

| # | Criterio | Nota | Evidencia | Qué falta para el 10 |
| --- | --- | --- | --- | --- |
| 1 | Negocio con dato (20 %) | **10** | `README.md:17–21`: 10–15 k USD/h, 240–360 k/día, quién decide, qué evita | — |
| 2 | ≥6 reglas (30 %) | **10** | `REGLAS_DECISION`: R1(10), R10(9), R11(8), R9(3), R8(2), R7(1) + 2 de corrección | — |
| 3 | n8n (35 %) | **7** | `flujo.json`: webhook + switch con 3 ramas + Sheets/Postgres/Calendar/Gmail; `active:false` | Ni ejecutado ni APTO enviado desde la app (A4) |
| 4 | Pregunta individual (15 %) | **10** | Guiones MIA | — |

---

## 5. Hallazgos

### Críticos

**C1 — El README atribuye a NB06 una media que NB06 no imprime.**
`README.md:98` y `:119` publican `4.368 ± 0.053` (NASA 2355,2 ± 24,6) y la fila 119
lo etiqueta como **«NB06»**. NB06, celda 45, imprime
`C (42,7,123): RMSE 4.322 +- 0.064 | NASA 2342.3 +- 43.4`, coherente con su nota de
la celda 42 (4.376 / 4.252). El 4.368 sale de otro CSV en disco
(`bundle_c_multiseed.csv`: 7 = 4.429, 123 = 4.336), no de lo impreso en el notebook.
`MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md:47,166` **veta explícitamente
el 4.368** hasta reconciliarlo. Además de C1, conviven 4.330 (NB05) y 4.322 (NB06).
La fila oficial 4.338 no está en discusión.
*Efecto:* una cifra publicada no es rastreable a la fuente que se le atribuye.
*Arreglo:* elegir una de las dos evidencias (CSV o NB06), regenerar la otra y citar
**una** media con su origen. No requiere reentrenar si se elige el CSV.

**C2 — PIA-4 (MLflow, 20 %) no tiene ninguna evidencia.**
`mlflow` no está en `requirements.txt`; `grep -rn "^import mlflow" src app tests` no
devuelve nada; `c27-mlflow.md` lo declara pendiente. La tabla comparativa es un CSV.
*Efecto:* techo de PIA en 8,0 aunque todo lo demás sea 10.

### Altos

**A1 — Las figuras del README no están versionadas.**
`docs/assets/` tiene 9 PNG en disco y **0 en git**. `README.md:12` y
`src/clase/README.md` citan 7 de ellos. En un clone limpio, las imágenes rompen.
*Arreglo:* `git add docs/assets` (no requiere tocar el contenido).

**A2 — Falta la captura de la app, apartado obligatorio del README.**
El reto marca «Captura de la app (*)» como sección 2. El README raíz abre con una
figura de RMSE y solo menciona la captura para decir que se regenera. Bajo lectura
literal, PIA-1 baja de 7 a 3.

**A3 — La tabla final elige el «campeón ventana» por RMSE de test.**
`src/clase/tabla_final.py:76–84` cae a `rmse_test` cuando el grano no tiene
validación, y NB06 celda 49 lo imprime. Es una selección sobre test, aunque el
bundle desplegado se adoptó por puerta (ADR-011). El código lo declara, pero
contradice «el test se toca una sola vez».
*Arreglo:* ordenar por la métrica de adopción del bundle (o no imprimir campeón en
ese grano).

**A4 — La rama APTO de n8n es inalcanzable desde la app.**
`app/ui_n8n.py:10` solo notifica `HANGAR` e `INSPECCION`; `dashboard_ds02.py:1898–1905`
deja APTO en log local. El flujo tiene 3 ramas, pero el webhook nunca recibe APTO.
*Efecto:* MIA-3 se queda en 7; el 10 exige que la decisión (las tres) llegue al flujo.

### Medios

- **M1 — Salidas sin sello de ejecución.** NB02 tiene 2 celdas con salida y
  `execution_count: null`; NB03, 1. No hay errores, pero la salida no es
  reproducible desde el JSON.
- **M2 — Árbol no reproducible.** 49 modificados + 12 sin seguimiento, incluido el
  manifiesto. Cualquier cifra auditada depende de un estado que git no conserva.
- **M3 — Comentario y guarda desactualizados en la banda.** `reglas.py` documenta
  el tramo `[75, ∞)` con 419 filas y `MIN_FILAS_TRAMO = 500`; el JSON trae 561 filas
  y `q_high = −17,45`. La guarda no se activa y el límite superior queda igual al
  punto. El comportamiento es conservador, pero el comentario miente.
- **M4 — n8n sin ejecutar y sin credenciales.** `active:false`,
  `templateCredsSetupCompleted:false`. Declarado; impide demostrarlo en vivo.

### Bajos

- **B1 —** NB06 celdas 12, 24 y 26 no tienen salida (intermedias).
- **B2 —** `resultados/` ignorado: correcto, pero deja las capturas fuera del repo.
- **B3 —** El README raíz no publica la tabla de campos que pide SAA-3.

---

## 6. Hipótesis: resultado

| ID | Estado | Evidencia |
| --- | --- | --- |
| H1 multiseed contradictorio | **Confirmada** | README 4.368 vs NB06 4.322 vs NB05 4.330 vs e00 que veta 4.368 |
| H2 PIA-4 = 0 | **Confirmada** | Sin dependencia, sin imports, sin runs |
| H3 n8n 7, no 10 | **Confirmada (matizada)** | Flujo válido y 3 ramas; APTO no se envía y no hay ejecución |
| H4 manifiesto/caché desalineados | **Refutada** | `manifest_sha256` del caché = SHA real |
| H5 notebooks no reflejan el código | **Parcial** | Sin errores; 3 salidas sin `execution_count` y 3 celdas vacías en NB06 |
| H6 `docs/assets` sin versionar | **Confirmada** | 9 en disco, 0 en `git ls-files` |
| H7 la app declara más de lo que muestra | **Refutada** | Arranca, 4 pestañas, SHAP y n8n cableados; falta solo la captura |
| H8 cifra no rastreable al manifiesto | **Confirmada** | C1 (la 4.338 sí es rastreable; la 4.368 no) |

---

## 7. Qué NO se tocó (puertas)

1. El bundle C no se reentrenó: SHA y métricas son los del manifiesto.
2. El test (uds 11/14/15) no se volvió a medir.
3. La banda conformal no se recalculó.
4. No se ejecutó n8n real ni se usaron credenciales.
5. No se abrió navegador: la app se verificó por arranque + health + código.
6. No se ejecutó un clone limpio; A1 se comprobó con `git ls-files`.

---

## 8. Límites

- n8n se auditó **estático** (JSON + payload + tests con `urlopen` mockeado).
- La UI se revisó por arranque y código, no click a click.
- Las notas son estimaciones con la rúbrica v5, no una corrección oficial.
- El informe se escribió sobre un árbol sucio; fija `a9d55a2` y la lista de cambios.

---

## 9. Orden de arreglo recomendado (no ejecutado)

1. **C1** — reconciliar multiseed y citar una sola media con origen (30 min).
2. **A1 + A2** — versionar `docs/assets` y añadir la captura de la app (20 min).
3. **A4** — enviar también APTO o demostrar la rama con un POST manual (20 min).
4. **C2** — MLflow: 5 runs con params/métricas/tiempo + captura (2–3 h).
5. **A3 + M1 + M3** — criterio de tabla, `execution_count`, comentario de la guarda (1 h).
