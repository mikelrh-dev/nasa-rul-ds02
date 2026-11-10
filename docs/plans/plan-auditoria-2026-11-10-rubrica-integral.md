# Plan de auditoría integral 2026-11-10 — Rúbrica Reto 1 (SAA + PIA + MIA)

**Fecha:** 2026-11-10 · **Rama:** `fix/auditoria-2026-11-10` · **HEAD:** `025dcb20d301b9fd30193b9024693b3aee949f87`
**Modo:** SOLO LECTURA (no se arregla, no se commitea, no se reentrena, no se ejecutan notebooks, no se despliega)
**Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (9 págs.; 20 criterios y pesos en págs. 5-9)
**Framework:** `docs/framework_auditoria.md` v1.0 (bloques A-Q, fases F0-F6, puertas G0-G6, severidad C/A/M/B)
**Antecedentes:** `docs/plans/plan-auditoria-2026-11-06-reto1-v2.md` · `docs/informes/auditoria-2026-11-06-reto1-v2.md` · `docs/informes/auditoria-2026-11-07-ds02.md`
**Intérprete único:** `.venv/Scripts/python.exe` (Python 3.12.10) · **Shell:** bash (git-bash, Windows)

> **Regla de honestidad:** toda cifra de este plan lleva su comando o `path:línea`. Lo que no se pueda probar se declara **límite**, no se maquilla. Las notas de §4 son **estimación a verificar**, no una corrección oficial.

---

## 1. Pregunta de auditoría y criterio de éxito

**Pregunta.** ¿El repositorio, **tal como está hoy** (HEAD `025dcb2`, árbol sucio de 203 rutas), demuestra con evidencia reproducible en qué grado cumple los **20 criterios** de la rúbrica v5 (SAA 1-10, PIA 1-6, MIA 1-4), y cuál es el **techo real** de cada asignatura?

No se pregunta «¿funciona el modelo?» (ya medido: bundle C 4.338) ni «¿pasan los tests?» (ya verde: 435 passed). Se pregunta por **evidencia**: que exista, que se abra desde un clon limpio, que diga lo mismo que el artefacto y que cubra el 10, no el 7.

**Criterio de éxito.** 20 celdas (10 SAA + 6 PIA + 4 MIA) con nota 0/3/7/10, cada una con una prueba reproducible (`path:línea` o comando con salida literal); matriz ponderada por asignatura con techo declarado; hallazgos C/A/M/B con reproducción; `cobertura.csv` reconciliado; firma de no modificación (`git status` idéntico a F0).

---

## 2. Estado actual / F0 previo (verificado hoy)

### 2.1 Baseline

| Variable | Valor | Comando |
| --- | --- | --- |
| Rama / HEAD | `fix/auditoria-2026-11-10` / `025dcb2` | `git rev-parse --abbrev-ref HEAD && git rev-parse HEAD` |
| Último commit | `025dcb2` 2026-11-09 23:33:56 +0100 · `chore(repo): retira archive/ a backup externo y conserva solo el bundle B` | `git log -1 --format='%H %ad %s' --date=iso` |
| Árbol | **203 rutas** (36 A, 78 M, 1 D, 88 ??; 81 de los ?? son `mlruns/`) | `git status --porcelain \| wc -l` |
| Versionados | 1746 ficheros | `git ls-files \| wc -l` |
| Intérprete | `.venv/Scripts/python.exe` (3.12.10) | `pyproject.toml` `requires-python >=3.12` |

**F0 ya congelado por el contexto:** el árbol está sucio a propósito. El informe audita **este estado**, no un commit limpio inexistente. No se commitea nada durante la auditoría.

### 2.2 Hashes y sellos (G0)

| Artefacto | SHA-256 real | Contra manifiesto/caché |
| --- | --- | --- |
| `models/ensemble.joblib` | `d6c701429eed8623a9d900d922aca1922427d08ff8b4ec00604b8116c1a952dd` | `artifacts.ensemble_sha256` **coincide** |
| `models/bilstm_ds02.keras` | `bf9620a7de3bf9f8efa65c1993a96d8a95b903dc6fde72c772aa316f4c042219` | `artifacts.bilstm_sha256` **coincide** |
| `models/scaler.joblib` | `acccfab34dd15d248ba2ee507e345955bcc91cb62a8c4be6f6aa34c639541f8d` | `artifacts.scaler_sha256` **coincide** |
| `models/mejor_modelo.joblib` | `5aab4d2a050163c9d9db0d0d3f769c198fe2e47a1bf2959fb355ca6f4652615f` | `artifacts.clase_xgb_sha256` **coincide** |
| `models/mejor_modelo_clase_E2.joblib` | `3bebe67e8750f174737228bd5de9b13758b4889607b415840152b5b7a33aa376` | `artifacts.clase_e2_sha256` **coincide** |
| `models/ds02_manifest.json` | `6089457c772f8cb947ed58172703043a2c6b149f2bdde0ca71599a19ec83ea40` | sellado en `app/cache/cache_manifest.json → artifact.manifest_sha256` **coincide** |

```bash
sha256sum models/ensemble.joblib models/bilstm_ds02.keras models/scaler.joblib \
          models/mejor_modelo.joblib models/mejor_modelo_clase_E2.joblib models/ds02_manifest.json
.venv/Scripts/python.exe -c "import json,hashlib;d=json.load(open('app/cache/cache_manifest.json'));print(d['artifact']['manifest_sha256']);print(hashlib.sha256(open('models/ds02_manifest.json','rb').read()).hexdigest())"
```

**G0:** PASA. El bundle que sirve es el que el manifiesto firma. Manifiesto: `code_version clase-bundle-C`, `seed 42`, `python 3.12.10`, `metrics.reference_row` RMSE 4.338 / MAE 3.227 / R² 0.9461 / NASA 2336.2, `macro_rmse 5.0153`.

### 2.3 Suite y guards (G1)

| Comprobación | Resultado | Comando |
| --- | --- | --- |
| Suite completa | **435 passed, 1 skipped in 255.62 s, exit 0** (dato del usuario, 2026-11-10) | `python -m pytest tests -q -rs` |
| Skip único | `tests/test_mia_rules.py:181` por `_p1_oof_cache.npz missing` (esperado, M-01) | `--pytest -rs` |
| `compileall` | exit 0 (verificado en auditorías previas; re-verificar en F1) | `.venv/Scripts/python.exe -m compileall -q src app scripts tests` |
| Guards `needs_cache` | `app/cache/` presente → no saltan | `ls app/cache` |
| Guard `needs_oof` | apunta a `_p1_oof_cache.npz` (**inexistente**) → 1 skip | `ls _p1_oof_cache.npz` → No such file |
| Guard muerto | `tests/test_audit_fixes.py:43-45` define `needs_oof` pero **ningún test lo usa** | `grep -rn "@needs_oof" tests/` → solo `test_mia_rules.py:181` |

**Nota:** el framework §9 dice «G1 espera cero skips» porque los tests deberían correr contra el instrumento versionado `src/mia/instrumento_oof.npz` (ADR-012). Hoy el guard sigue apuntando al caché git-ignored. **M-01 sigue abierto.**

### 2.4 Inventario y versionado (G2/G6)

| Comprobación | Resultado | Comando |
| --- | --- | --- |
| `docs/assets` versionados | **10 PNG** | `git ls-files docs/assets \| wc -l` |
| `resultados` versionados | **36** (16 CSV + 20 PNG) | `git ls-files resultados \| wc -l` |
| `resultados` en disco | 37 (17 CSV + 20 PNG); `tiempos_nb01.csv` sin seguimiento | `ls resultados/*.csv \| wc -l` |
| `mlruns` versionados | **1010 ficheros** (28 `meta.yaml`); **109 `meta.yaml` en disco**; 81 dirs sin seguimiento | `git ls-files mlruns \| wc -l; find mlruns -name meta.yaml \| wc -l` |
| PNG totales versionados | 87 | `git ls-files \| grep -c '\.png$'` |
| Tests | 47 ficheros `tests/test_*.py` | `ls tests/test_*.py \| wc -l` |
| `app/dashboard_ds02.py` | 2197 líneas, 4 pestañas | `wc -l < app/dashboard_ds02.py`; `st.tabs` en `:1176` |

### 2.5 Reglas, n8n, MLflow (resumen)

- **Reglas:** `REGLAS_DECISION` 6 + `REGLAS_CORRECCION` 2 = **8**. Prioridades: R1_SEGURIDAD 10, R10_DATOS_INSUFICIENTES 9, R11_UMBRALES_INCOHERENTES 8, R9_HANGAR 3, R8_INSPECCION 2, R7_APTO 1; corrección R2b_ISOTONICO_CAUSAL 2, R6_BANDA 1. Fuente: `src/mia/reglas.py:246-270`.
- **n8n:** `n8n/flujo.json` — 14 nodos, `active: false`, webhook `POST ds02/decision` con `authentication: headerAuth`, switch de 3 salidas (APTO → Set log; INSPECCIÓN → Google Sheets; HANGAR → Postgres → Calendar → Gmail). **Modificado y sin commitear** (L-01).
- **MLflow:** `requirements.txt:19 mlflow==3.18.0`; `src/ds02_rul/mlflow_live.py` importa `mlflow`; 13 runs (9 fila + 4 ventana); `docs/evidencia/mlflow/comparativa.csv` (13 filas) + 3 PNG. `scripts/backfill_mlflow.py --check` → `OK: 13 runs (9 fila + 4 ventana), export y store coinciden, sin artefactos.`

### 2.6 Memoria del proyecto (Engram) — contraste

`mem_search` sobre el proyecto `nasa-rul-ds02` (las memorias viven en ese project, no en `mikel`):

| Consulta | Resultado |
| --- | --- |
| `bundle B 4.251` | **Sin memorias.** No hay ninguna entrada que cite 4.251. |
| `cuatro tests fallos` | **Sin memorias.** No hay ninguna entrada que hable de cuatro fallos. |
| `suite 406 passed` | #3006 «Suite 406 passed PIA-4 2026-11-09» → **obsoleto**: hoy 435 passed. |
| `bundle B` | #2994 «Bundle C campeón único ADR-011; B archivado», #2998 «Track clase E2 campeón fila, XGB mejor clásico». |

**Veredicto:** la memoria persistente **no contiene** las cifras `4.251` ni el relato de «cuatro tests fallos»; no hay nada que marcar como obsoleto en ese punto. Lo único caducado es el recuento de suite (#3006: 406 → 435) y el resumen de poda (#3001: 78 passed, 3 skipped). Se anota como **memoria parcialmente obsoleta**, no como contradicción.

---

## 3. Alcance

**Dentro**
- Los 20 criterios de la rúbrica v5 contra evidencia del árbol actual.
- Coherencia de cifras: manifiesto ↔ `e00` ↔ README ↔ README.en ↔ AGENT.md ↔ framework ↔ notebooks ↔ `resultados/` ↔ `mlruns/`.
- Reproducibilidad: suite, `compileall`, arranque de app/API, enlaces y figuras desde clone limpio.
- Contratos: manifiesto/caché, `src/n8n.py`, reglas, `app/api.py`, `app/cache/`.
- n8n: auditoría **estática** del JSON + payload + tests; ejecución solo si hay instancia.
- Cobertura: inventario con tiers A/B/C y `cobertura.csv`.

**Fuera**
- Reentrenar el bundle, recalibrar bandas, re-leer el test (uds 11/14/15), re-ejecutar notebooks.
- Corregir hallazgos: la auditoría **no arregla**; produce informe y propuesta.
- `git add/commit/push`, desplegar, credenciales reales, datos vivos de n8n.
- Docker: el proyecto no lleva contenedores (decisión 2026-11-07); el bloque C queda **n/a**.
- No ejecutar la suite completa (ya verde; solo spot-checks).

**Dependencias externas**
- **n8n:** sin instancia viva → MIA-3 se audita estático; techo declarado.
- **API `:8000` / dashboard `:8501`:** si no hay proceso, J y la parte viva de K son **NO VERIFICABLE**, no «PASA».
- **MLflow UI:** las capturas son PNG versionados; no se exige servidor.

---

## 4. Matriz de los 20 criterios (estimación a verificar)

> **Etiqueta:** toda nota de esta sección es **ESTIMACIÓN A VERIFICAR**. La nota definitiva la fija la evidencia de F2-F4, no esta tabla. Escala: 0 / 3 / 7 / 10.

### 4.1 SAA — Sistemas de Aprendizaje Automático

| # | Criterio (peso) | Evidencia esperada | Dónde buscarla |Qué demuestra el 10 | Est. | Evidencia que la sostiene |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | IA débil (5 %) | Párrafo + comparación con IA fuerte | `README.md:29` | Nombra la AGI y razona por qué no transfiere | **10** | `README.md:29`: «IA débil… Frente a una IA fuerte (AGI…) no transfiere nada fuera de DS02» |
| 2 | Tipo de aprendizaje (10 %) | Supervisado + regresión + diferencia con no supervisado | `README.md:29` | Razona el «por qué», no solo etiqueta | **10** | `README.md:29`: «Aprendizaje supervisado… de regresión… se diferencia del no supervisado en que hay etiqueta y métrica» |
| 3 | Dataset y campos (5 %) | Tabla con tipo, % nulos y campos descartados | `README.md:49-82` | Tabla con nulos por campo + qué quita y por qué | **10** | `README.md:49-69` tabla (campo/qué/tipo/nulos antes/después) + `:73-82` «Campos quitados… por qué». **Ojo:** v2 dio 7 porque la tabla no estaba en el raíz; hoy sí. |
| 4 | ≥5 gráficos comentados (5 %) | Barras, histograma, boxplot, dispersión, heatmap | `notebooks/01`, `docs/assets/` | 5 tipos, cada uno con «qué veo / conclusión» | **10** | NB01 + `docs/assets/` (barras, scatter, heatmap, hist, box). Verificar en F2 que los 5 tipos están comentados. |
| 5 | Nulos + variable nueva (5 %) | MAR justificado, imputación causal, `fase_vuelo` | `README.md:71`, `src/clase/dataset_clase.py` | Patrón físico + por qué la variable aporta | **10** | `README.md:71`: «Nulos MAR con patrón físico (dropout de T30 en crucero alto) → ffill causal + mediana»; `fase_vuelo` en `:68` |
| 6 | 5 modelos + extra (30 %) | Ridge/KNN/RF/XGB/SVM + algo no visto | `src/clase/train_clasicos.py`, `resultados/comparativa.csv` | Los 5 con GridSearchCV y el extra medido | **10** | `comparativa.csv` 5 filas clásicas; híbrido C como extra (4.338 vs LGBM 7.067) |
| 7 | MLP base + 3 experimentos (20 %) | Hipótesis escrita antes del resultado | `src/clase/train_mlp.py` (`EXPS`) | Cada experimento con su hipótesis y veredicto | **10** | `train_mlp.py` EXPS + `resultados/mlp_comparativa.csv` (base, E1, E2, E3) |
| 8 | Métricas y errores (10 %) | RMSE/MAE/R² + real-vs-pred + lectura de negocio | `README.md:106-160`, `resultados/` | Traduce el error a coste/hangar | **10** | `README.md:144` y `:149-157`; gráfico real-vs-pred en NB02/NB06 |
| 9 | Elección + SHAP (5 %) | Elección por negocio, desempate simple, SHAP en val | `src/clase/shap_clase.py`, `notebooks/07` | SHAP con aditividad y variables top | **10** (reserva A3) | SHAP E2 (aditividad) + SHAP-C en NB07 (fold-0). **Reserva:** `tabla_final.py:76-84` ordena por `rmse_test` en grano ventana. |
| 10 | Pregunta individual (5 %) | Guion con respuesta y `path:línea` | `docs/defensa/guiones-15min.md` | Respuesta defendible, no memorizada | **10** (no verificable desde repo) | `guiones-15min.md` §1 con `path:línea` (train_clasicos.py:145, etc.) |

### 4.2 PIA — Programación de Inteligencia Artificial

| # | Criterio (peso) | Evidencia esperada | Dónde buscarla | Qué demuestra el 10 | Est. | Evidencia que la sostiene |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | README + docstrings (10 %) | 6 apartados + apartados propios + funciones documentadas | `README.md`, `tests/test_docstrings*` | 0 públicas sin docstring y README con extras | **10** | README con 6 apartados + captura (`:16`) + extras (Arquitectura, MLflow, Estabilidad…); 268/268 docstrings (v2) |
| 2 | Carpetas y funciones (10 %) | Estructura del reto + `requirements.txt` | árbol, `requirements.txt` | Estructura reconocible y deps pinneadas | **10** | `data/`, `notebooks/`, `src/`, `app/`, `models/`, `n8n/`, `resultados/`; `requirements.txt` pineado |
| 3 | Pipeline sklearn (20 %) | `ColumnTransformer` compartido y guardado en el joblib | `src/clase/pipeline_clase.py`, `models/mejor_modelo.joblib` | Carga y predice un caso nuevo con el pipeline dentro | **10** | `pipeline_clase.py:27` (`StandardScaler` + `OneHotEncoder`); joblib cargado y predice (v2) |
| 4 | MLflow (20 %) | Runs con params/métricas/tiempo + capturas | `requirements.txt:19`, `mlruns/`, `docs/evidencia/mlflow/` | Compara en MLflow y lo enseña con capturas | **10** (reserva) | 13 runs (9 fila + 4 ventana); `comparativa.csv` 13 filas; 3 PNG. **Reserva:** la ablación `cyc_norm` no aparece como run; store con 81 dirs sin seguimiento. |
| 5 | App Streamlit (25 %) | Métricas test + caso nuevo + reglas + n8n + control de errores | `app/dashboard_ds02.py`, `app/ui_*.py` | Muestra la p del caso nuevo junto a la decisión | **10** | 4 pestañas (`:1176`); métricas test; `st.metric("RUL p35 (conservadora)", …)` (`:1975`) junto a `L_inf`/decisión (`:1977`); envío n8n (`:1951-1956`) |
| 6 | Pregunta individual de código (15 %) | Respuesta con archivo:línea | `docs/defensa/guiones-15min.md` §2 | Enseña el código y explica el porqué | **10** (no verificable desde repo) | `guiones-15min.md` §2 con `pipeline_clase.py:27` |

### 4.3 MIA — Modelos de Inteligencia Artificial

| # | Criterio (peso) | Evidencia esperada | Dónde buscarla | Qué demuestra el 10 | Est. | Evidencia que la sostiene |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Negocio con dato y objetivo (20 %) | Dato € + qué predice + para qué + quién + mejora | `README.md:21-25`, `costes_reales_aeronauticos.md` | Cuantifica qué supone para la empresa | **10** | `README.md:23`: AOG 10.000-15.000 USD/h, quién decide, qué evita; `costes_reales_aeronauticos.md` con fuentes IATA |
| 2 | ≥6 reglas (30 %) | Prioridad, decisión, porqué, regla de seguridad | `src/mia/reglas.py:246-270` | 6 de decisión + R1 y traza visible | **10** | 6 de decisión + 2 de corrección; R1 prioridad 10; `porque` por regla |
| 3 | n8n (35 %) | Webhook + rama por decisión + acción distinta a clase | `n8n/flujo.json`, `app/ui_n8n.py` | Recibe decisión y actúa distinto por rama | **7 (techo)** | 3 ramas con acción distinta (log / Sheets / Postgres+Calendar+Gmail), pero **las 4 acciones son las vistas en clase** → el 10 exige una distinta; `active:false` y credencial placeholder; no ejecutado |
| 4 | Pregunta individual (15 %) | Respuesta con `path:línea` | `docs/defensa/guiones-15min.md` §3 | Explica la decisión, no solo el modelo | **10** (no verificable desde repo) | `guiones-15min.md` §3 |

### 4.4 Cálculo de nota ponderada por asignatura

```
SAA = (10·5 + 10·10 + 10·5 + 10·5 + 10·5 + 10·30 + 10·20 + 10·10 + 10·5 + 10·5) / 100
    = 1000 / 100 = 10,0
PIA = (10·10 + 10·10 + 10·20 + 10·20 + 10·25 + 10·15) / 100
    = 1000 / 100 = 10,0
MIA = (10·20 + 10·30 +  7·35 + 10·15) / 100
    =  895 / 100 = 8,95 → 9,0
```

| Asignatura | Nota ponderada (est.) | Techo declarado | Qué lo limita |
| --- | --- | --- | --- |
| **SAA** | **10,0** | 10 | Reserva A3 (tabla final ordena por test) y la contradicción 4.368 (bloque G) si el tribunal la lee como «métrica engañosa». |
| **PIA** | **10,0** | 10 | Reserva PIA-4: la ablación `cyc_norm` no está como run; store con 81 dirs sin seguimiento. |
| **MIA** | **9,0** | **9,0** | MIA-3 techado en **7**: las acciones son las vistas en clase + flujo no ejecutado + credencial placeholder. |
| **Global** | la peor puerta manda | — | Árbol sucio (203 rutas) → ninguna cifra es reproducible desde un clon limpio; G3 falla en la 4.368. |

> **Advertencia:** SAA 10,0 y PIA 10,0 son **optimistas**. El framework manda «la nota se baja, no se negocia»: si en F2-F4 se encuentra que un criterio exige X y solo hay Y, la nota baja a la de Y. La 4.368 y el árbol sucio son los dos riesgos de que SAA/PIA no lleguen al 10.

---

## 5. Hipótesis a confirmar o refutar (escritas antes de mirar)

Cada hipótesis lleva su **comando de falsación**. Una hipótesis refutada se reporta como refutada.

| ID | Hipótesis | Comando de falsación |
| --- | --- | --- |
| **H1** | La cifra **4.368 ± 0.053 / NASA 2355.2 ± 24.6** publicada como «regenerable» **no es regenerable** desde el CSV vigente: `comparativa_c_multisemilla.csv` está obsoleto y su columna `origen` miente. | `.venv/Scripts/python.exe -c "import csv,statistics as st; a={r['seed']:r for r in csv.DictReader(open('resultados/comparativa_c_multisemilla.csv'))}; b={r['seed']:r for r in csv.DictReader(open('resultados/bundle_c_multiseed.csv'))}; print(st.mean([float(a[s]['RMSE']) for s in ['42','7','123']]), st.mean([float(b[s]['RMSE']) for s in ['7','123']]+[float(a['42']['RMSE'])]))"` → esperado 4.3677 vs 4.3243 |
| **H2** | El 4.368 **solo** reproduce la comparativa obsoleta (4.3677) y **no** el `bundle_c_multiseed.csv` vigente (4.3243). | El mismo comando; si ambas medias coinciden, H2 es falsa. |
| **H3** | `e00-cifras-autoritativas.md:47` está **desactualizado**: describe `bundle_c_multiseed.csv` como 7=4.429 / 123=4.336, pero hoy trae 7=4.211 / 123=4.424. | `cat resultados/bundle_c_multiseed.csv` vs `sed -n '47p' MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md` |
| **H4** | **MIA-3 está techado en 7**: las acciones del flujo (Sheets, Postgres, Calendar, Gmail) son las vistas en clase; el 10 exige una acción distinta. | `python -c "import json;d=json.load(open('n8n/flujo.json'));[print(n['type'],n['name']) for n in d['nodes']]"` y comparar con la lista de acciones de clase |
| **H5** | El flujo n8n **no puede ejecutarse**: `active:false` + credencial placeholder `REEMPLAZAR_CREDENCIAL`. | `python -c "import json;d=json.load(open('n8n/flujo.json'));print(d['active']);print([n.get('credentials') for n in d['nodes'] if n['type']=='n8n-nodes-base.webhook'])"` |
| **H6** | **M-01:** el guard `needs_oof` apunta a `_p1_oof_cache.npz` (inexistente) y no al instrumento versionado; `test_audit_fixes.py` define el guard pero no lo usa. | `grep -rn "@needs_oof" tests/` → solo `test_mia_rules.py:181`; `ls _p1_oof_cache.npz` → no existe |
| **H7** | **C-01:** `scripts/predict.py:22` apunta a `models/v3_bundle.joblib` (inexistente); el manifiesto ya no lo referencia. | `ls models/v3_bundle.joblib` → no existe; `grep -n v3_bundle models/ds02_manifest.json` → sin hits |
| **H8** | **I-01:** `openspec/project.md:104` publica cobertura 0.9012 y `:107` dice 0.9016; el instrumento mide 0.901643. | `grep -n "0.9012\|0.9016" openspec/project.md`; `.venv/Scripts/python.exe scripts/freeze_oof_instrument.py --check` → 0.901643 |
| **H9** | **A1-B:** el alias `mejor_modelo.joblib` es el XGB (8.2173), no el E2 (7.3404); `models/README.md` lo documenta y hay test que lo fija. | `sed -n '14,55p' models/README.md`; `grep -n "test_tres_campeones\|test_mejor_modelo_alias" tests/test_clase_rubrica.py` |
| **H10** | **L-01:** `n8n/flujo.json` está modificado y sin commitear. | `git status --porcelain n8n/flujo.json` → ` M` |
| **H11** | `docs/pendiente/deuda-riesgo-7-2026-11-10.md` está **parcialmente obsoleto**: cita «106 meta.yaml en disco» (hoy 109) y `tests/test_mlflow_ui.py` (inexistente). | `find mlruns -name meta.yaml \| wc -l`; `ls tests/test_mlflow_ui.py` → no existe |
| **H12** | La memoria Engram #3006 («406 passed») está **obsoleta**; hoy 435 passed. | `mem_get_observation(3006)` vs el dato de suite de hoy |
| **H13** | `docs/assets/` duplica 9 PNG de `resultados/`; 7 son byte-idénticos y **2 han divergido** (`real_vs_predicho_bundle_c.png`, `shap_importancia.png`). | `for b in $(git ls-files docs/assets); do cmp -s "$b" "resultados/$(basename $b)" && echo IDENTICO || echo DISTINTO; done` |
| **H14** | **H-01:** el manifiesto publica 4.338 / 3.227 y la caché 4.3382 / 3.2266 (dos precisiones). | `python -c "import json;print(json.load(open('models/ds02_manifest.json'))['metrics']['reference_row']);print(json.load(open('app/cache/cache_manifest.json'))['metrics'])"` |
| **H15** | El árbol está sucio (203 rutas) y **ninguna cifra es reproducible desde un clon limpio**. | `git status --porcelain \| wc -l` → 203 |

---

## 6. Fases F0-F6, comandos y orquestación

### 6.1 Orquestación por ondas (máximo 3 subagentes concurrentes, ventana deslizante)

```
Onda 0  F0 baseline                1 agente  (coordinador)
Onda 1  F1 mecánica + inventario   3 agentes (paralelo)
Onda 2  F2+F3 criterios            3 agentes (SAA | PIA | MIA)
Onda 3  F4 transversales           3 agentes (cifras G | artefactos H | tests/deuda M-Q)
Onda 4  F5 jueces                  2 jueces independientes (J1 | J2)
Onda 5  F6 síntesis                1 agente  (coordinador)
```

**Regla de ventana deslizante:** se lanza el siguiente subagente **solo cuando uno termina**; nunca más de 3 vivos. Cada subagente escribe sus hallazgos en un fichero temporal del scratch (`$TMPDIR`/`BH_AGENT_WORKSPACE`), **no en el repo**. Solo el coordinador escribe el informe final.

**Jueces (Onda 4):** 2 agentes independientes que **exploran el proyecto completo** y comparan hallazgos. J1 cubre SAA + PIA + G; J2 cubre MIA + L + transversal. Cada juez produce: (a) lista de hallazgos confirmados/refutados, (b) discrepancias con los agentes de Ondas 2-3, (c) nota final propuesta con techo. Si un juez discrepa de un agente, el coordinador arbitra con evidencia y lo documenta.

### 6.2 F0 — Baseline (Onda 0, 15 min)

```bash
cd /c/Users/mikel/Desktop/Pruebas/nasa
git rev-parse --abbrev-ref HEAD && git rev-parse HEAD
git status --porcelain | tee "$TMPDIR/f0_status.txt" | wc -l      # esperado 203
git log -1 --format='%H %ad %s' --date=iso
sha256sum models/*.joblib models/*.keras models/ds02_manifest.json
.venv/Scripts/python.exe -c "import json,hashlib;d=json.load(open('app/cache/cache_manifest.json'));print(d['artifact']['manifest_sha256']==hashlib.sha256(open('models/ds02_manifest.json','rb').read()).hexdigest())"
```

**Salida esperada:** HEAD `025dcb2…`; 203 rutas; sellos coinciden (`True`).

### 6.3 F1 — Mecánica e inventario (Onda 1, 3 agentes, 40 min)

**F1.a — Mecánica**
```bash
.venv/Scripts/python.exe -m compileall -q src app scripts tests; echo "exit=$?"     # esperado 0
.venv/Scripts/python.exe scripts/freeze_rules_evidence.py; echo "exit=$?"           # esperado 0
.venv/Scripts/python.exe scripts/freeze_oof_instrument.py --check; echo "exit=$?"   # esperado 0
.venv/Scripts/python.exe scripts/backfill_mlflow.py --check; echo "exit=$?"         # esperado 0
grep -rn "@needs_oof\|@needs_cache" tests/ | wc -l
ls _p1_oof_cache.npz 2>&1                                                       # esperado: no existe
```
> **No ejecutar la suite completa** (ya verde). Solo spot-checks de los gates.

**F1.b — Inventario y cobertura**
```bash
git ls-files | wc -l                                                              # 1746
git ls-files docs/assets | wc -l                                                 # 10
git ls-files resultados | wc -l                                                  # 36
git ls-files mlruns | wc -l                                                      # 1010
git status --porcelain | grep '^??' | wc -l                                      # 88
```
Construir `cobertura.csv` con una fila por archivo (`path,tier,veredicto,evidencia`), tiers excluyentes **C > B > A**. Universo = 1746 versionados + 88 sin seguimiento = **1834**.

**F1.c — Figuras y enlaces (G2)**
```bash
grep -on "docs/assets/[A-Za-z0-9_]*\.png\|resultados/[A-Za-z0-9_]*\.png\|docs/evidencia/[A-Za-z0-9_/]*\.png" README.md README.en.md src/clase/README.md | sort -u
for f in $(git ls-files docs/assets); do [ -f "$f" ] || echo "ROTO $f"; done
```

### 6.4 F2 — SAA 1-10 (Onda 2, agente SAA, 90 min)

```bash
sed -n '27,43p' README.md          # SAA-1, SAA-2
sed -n '45,82p' README.md          # SAA-3, SAA-5
.venv/Scripts/python.exe -c "import json;nb=json.load(open('notebooks/01_eda_y_contexto.ipynb'));[print(c['cell_type'],len(c.get('source',[])),len(c.get('outputs',[]))) for c in nb['cells']]"
.venv/Scripts/python.exe -c "import json;[print(f, len([c for c in json.load(open(f))['cells'] if c['cell_type']=='code'])) for f in __import__('glob').glob('notebooks/*.ipynb')]"
grep -n "GridSearchCV\|GroupKFold" src/clase/train_clasicos.py
grep -n "EXPS\|hipotesis\|hipótesis" src/clase/train_mlp.py | head
cat resultados/comparativa.csv
grep -n "shap\|aditividad\|check_aditividad" src/clase/shap_clase.py | head
ls notebooks/07_shap_c_bundle_c.ipynb docs/assets/shap_importancia.png
```

**Salida esperada:** 5 tipos de gráfico en NB01; 5 clásicos con GridSearchCV; 4 MLP con hipótesis; SHAP con aditividad.

### 6.5 F3 — PIA 1-6 (Onda 2, agente PIA, 90 min)

```bash
grep -n "^## " README.md
grep -rn '"""' src/clase/*.py | wc -l
grep -n "StandardScaler\|OneHotEncoder\|ColumnTransformer" src/clase/pipeline_clase.py
.venv/Scripts/python.exe -c "import joblib;m=joblib.load('models/mejor_modelo.joblib');print(type(m), hasattr(m,'named_steps'))"
grep -n "mlflow" requirements.txt pyproject.toml
cat docs/evidencia/mlflow/comparativa.csv | wc -l
ls docs/evidencia/mlflow/*.png
grep -n "st.tabs\|st.metric\|enviar_decision\|L_inf" app/dashboard_ds02.py | head -20
```

**Salida esperada:** 6 apartados + captura; pipeline con `StandardScaler`+`OneHotEncoder`; joblib con pipeline; 13 filas en `comparativa.csv`; 3 PNG; app con p + decisión + n8n.

### 6.6 F4 — MIA 1-4 (Onda 2, agente MIA, 90 min)

```bash
sed -n '21,25p' README.md
sed -n '246,270p' src/mia/reglas.py
.venv/Scripts/python.exe -c "import json;d=json.load(open('n8n/flujo.json'));print('active',d['active']);print('nodes',len(d['nodes']));[print(n['type'],n['name']) for n in d['nodes']]"
.venv/Scripts/python.exe -c "import json;d=json.load(open('n8n/flujo.json'));print(json.dumps(d['connections'],ensure_ascii=False,indent=1))"
grep -n "DECISIONES_QUE_NOTIFICAN" app/ui_n8n.py
```

**Salida esperada:** 8 reglas con prioridad; 3 ramas; `active:false`; acciones = Sheets/Postgres/Calendar/Gmail.

### 6.7 F4 transversal (Onda 3, 3 agentes, 90 min)

**F4.a — Cifras (G3):** cruzar manifiesto ↔ e00 ↔ README ↔ README.en ↔ AGENT.md ↔ framework ↔ CSV. Comando clave:
```bash
grep -rn "4\.368\|2355\.2\|4\.338\|2336\.2\|5\.0153" README.md README.en.md AGENT.md docs/framework_auditoria.md MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md
.venv/Scripts/python.exe -c "import csv,statistics as st;a={r['seed']:r for r in csv.DictReader(open('resultados/comparativa_c_multisemilla.csv'))};b={r['seed']:r for r in csv.DictReader(open('resultados/bundle_c_multiseed.csv'))};print('comparativa',st.mean([float(a[s]['RMSE']) for s in ['42','7','123']]),st.mean([float(a[s]['NASA_Score']) for s in ['42','7','123']]));print('bundle_c+42',st.mean([float(b[s]['RMSE']) for s in ['7','123']]+[float(a['42']['RMSE'])]),st.mean([float(b[s]['NASA_Score']) for s in ['7','123']]+[float(a['42']['NASA_Score'])]))"
```

**F4.b — Artefactos (H):** hashes, `load_ensemble`, `cache_manifest`, instrumento OOF.
```bash
sha256sum models/* app/cache/*.parquet
grep -n "verify_artifact_sha256\|load_ensemble\|resolve_within_repo" src/ds02_rul/persistence.py | head
```

**F4.c — Tests y deuda (M-Q):** guards, skips, TODO/FIXME, `docs/pendiente/`, `mlruns/` versioning.
```bash
grep -rn "TODO\|FIXME\|HACK" src app scripts tests --include=*.py | wc -l
cat docs/pendiente/deuda-riesgo-7-2026-11-10.md
git ls-files mlruns | wc -l
```

### 6.8 F5 — Jueces (Onda 4, 2 agentes, 60 min)

- **J1:** reproduce H1-H4, H8, H14; recorre SAA+PIA con `path:línea`; propone nota SAA/PIA.
- **J2:** reproduce H5-H7, H9-H13, H15; recorre MIA+transversal; propone nota MIA.
- Ambos escriben `juez1.csv` / `juez2.csv` en scratch y un veredicto de discrepancias.

### 6.9 F6 — Síntesis (Onda 5, 1 agente, 45 min)

- Pasa de hipótesis a confirmada/refutada con evidencia.
- Redacta el informe con la matriz de 20 celdas, nota ponderada y techo.
- Firma G5: `git status --porcelain` idéntico a F0 (salvo el informe y los CSV de salida).

---

## 7. Puertas G0-G6 y severidad

| Puerta | Condición | Si falla |
| --- | --- | --- |
| **G0** | Baseline congelado (commit + `git status` + hashes + sello caché) | No se auditan cifras |
| **G1** | `compileall` limpio; suite verde; el único skip es `test_mia_rules.py:181` y está nombrado | Hallazgo Crítico antes de seguir |
| **G2** | Toda figura, enlace y ruta citada existe y se abre | Hallazgo Alto por enlace roto |
| **G3** | Toda cifra publicada es rastreable a manifiesto/CSV/test | Hallazgo Crítico o Alto según cifra |
| **G4** | Cada criterio tiene evidencia para su nota | Se baja la nota, no se maquilla |
| **G5** | La auditoría no modificó nada (`git status` idéntico a F0 + informe/CSV) | El informe no se publica |
| **G6** | `cobertura.csv` reconcilia 1834 archivos y ninguno queda sin tier | Hallazgo Alto de cobertura |

**Severidad**

| Nivel | Criterio | Efecto |
| --- | --- | --- |
| **C — Crítico** | Invalida una cifra publicada, un criterio entero o la seguridad | Bloquea la conclusión de ese bloque |
| **A — Alto** | Resta credibilidad o rompe el nivel máximo de un criterio | Se reporta antes que el resto |
| **M — Medio** | Inconsistencia que un lector atento detectaría | Se corrige en la siguiente iteración |
| **B — Bajo** | Pulido, enlaces, redacción | Se agrupa en un anexo |

---

## 8. Entregables

1. **Informe:** `docs/informes/auditoria-2026-11-10-rubrica-integral.md` — veredicto por asignatura, matriz de 20 celdas con nota + evidencia, hallazgos C/A/M/B, límites, anexo de comandos y salidas literales, firma G5.
2. **CSVs** (en `resultados/auditoria-2026-11-10/`, no versionados o versionados según decisión):
   - `criterios.csv` — `#`,asignatura,criterio,peso,nota,evidencia,que_falta_para_10
   - `cobertura.csv` — `path,tier,veredicto,evidencia` (1834 filas, 0 sin tier)
   - `hallazgos.csv` — `id,bloque,severidad,hallazgo,reproduccion,evidencia,impacto,propuesta`
3. **Propuesta openspec** (si hay arreglos): nueva change con las correcciones priorizadas; **no se aplica** durante la auditoría.

---

## 9. Orden, duración estimada y riesgos

| Fase | Onda | Agentes | Duración |
| --- | --- | --- | --- |
| F0 | 0 | 1 | 15 min |
| F1 | 1 | 3 | 40 min |
| F2+F3 | 2 | 3 | 90 min |
| F4 | 3 | 3 | 90 min |
| F5 | 4 | 2 jueces | 60 min |
| F6 | 5 | 1 | 45 min |
| **Total** | | | **~4 h** (sin cómputo pesado) |

**Riesgos declarados**
1. **Árbol sucio (203 rutas):** el informe fija commit + lista; no se commitea nada.
2. **TensorFlow no determinismo:** no se reentrena ni se re-ejecuta nada que entrene.
3. **Test de una sola lectura:** no se re-mide; se cita la lectura existente.
4. **n8n sin instancia:** se distingue «estructura válida» de «flujo probado»; MIA-3 techo 7.
5. **API/dashboard:** si no hay proceso, J y la parte viva de K son NO VERIFICABLE.
6. **Memoria Engram obsoleta:** #3006 (406 passed) y #3001 (78 passed) están caducados; no se usan como fuente.
7. **Ventana deslizante:** si un subagente se cuelga, se relanza con `timeout` y se documenta.

---

## 10. Hallazgos preliminares ya detectados al planificar (con file:línea)

| ID | Bloque | Sev. | Hallazgo | Evidencia |
| --- | --- | --- | --- | --- |
| **G-01** | G | **C** | El 4.368 ± 0.053 / NASA 2355.2 ± 24.6 publicado como «regenerable» **no es regenerable** desde el CSV vigente; `comparativa_c_multisemilla.csv` está obsoleto y su columna `origen='bundle_c_multiseed.csv'` es **falsa** (ese fichero trae 7=4.211 / 123=4.424, no 4.429 / 4.336). | `resultados/comparativa_c_multisemilla.csv` (mtime 2026-11-06 15:25) vs `resultados/bundle_c_multiseed.csv` (mtime 2026-11-09 22:23); medias 4.3677 vs 4.3243 |
| **G-02** | G | **M** | `e00-cifras-autoritativas.md:47` está **desactualizado**: describe `bundle_c_multiseed.csv` como 7=4.429 / 123=4.336, pero hoy trae 4.211 / 4.424. El veto a 4.368 sigue vigente, pero la descripción del CSV ya no cuadra. | `sed -n '47p' MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md` vs `cat resultados/bundle_c_multiseed.csv` |
| **G-03** | G | **M** | `docs/framework_auditoria.md:560` publica 4.368 ± 0.053 como «cifra vigente», contradiciendo a `e00:166` que la veta. | `grep -n 4.368 docs/framework_auditoria.md` vs `e00:166` |
| **M-01** | M/G1 | **A** | El guard `needs_oof` apunta a `_p1_oof_cache.npz` (inexistente) y no al instrumento versionado `src/mia/instrumento_oof.npz`; `test_audit_fixes.py:43-45` define el guard pero **ningún test lo usa** (guard muerto). | `grep -rn "@needs_oof" tests/` → solo `test_mia_rules.py:181`; `ls _p1_oof_cache.npz` → no existe |
| **C-01** | C/D/H | **A** | `scripts/predict.py:22` apunta a `models/v3_bundle.joblib` (inexistente); el manifiesto ya no lo referencia. `_load()` lanza `RuntimeError` honesto. | `sed -n '22p' scripts/predict.py`; `ls models/v3_bundle.joblib` → no existe |
| **L-01** | L | **M** | `n8n/flujo.json` modificado y sin commitear; `active:false` y credencial placeholder `REEMPLAZAR_CREDENCIAL`. | `git status --porcelain n8n/flujo.json` → ` M`; `git diff n8n/flujo.json` |
| **I-01** | G/I | **M** | `openspec/project.md:104` publica cobertura 0.9012 y `:107` dice 0.9016; el instrumento mide 0.901643. | `grep -n "0.9012\|0.9016" openspec/project.md`; `freeze_oof_instrument.py --check` |
| **A1-B** | H/Q | **M** | El alias `models/mejor_modelo.joblib` es copia manual del XGB (8.2173), no del E2 (7.3404). Riesgo 7 declarado en `docs/pendiente/deuda-riesgo-7-2026-11-10.md`. | `models/README.md:22-32`; `tests/test_clase_rubrica.py:51,73` |
| **B5** | Q | **B** | `deuda-riesgo-7-2026-11-10.md` está parcialmente obsoleto: cita «106 meta.yaml en disco» (hoy 109) y `tests/test_mlflow_ui.py` (inexistente). | `find mlruns -name meta.yaml \| wc -l` → 109; `ls tests/test_mlflow_ui.py` → no existe |
| **H-01** | H | **B** | Las mismas métricas viven en dos precisiones: manifiesto 4.338 / 3.227 vs caché 4.3382 / 3.2266. | `models/ds02_manifest.json` `metrics.reference_row` vs `app/cache/cache_manifest.json` `metrics` |
| **N-01** | N | **B** | `docs/assets/` duplica 9 PNG de `resultados/`; 7 son byte-idénticos y **2 han divergido** (`real_vs_predicho_bundle_c.png`, `shap_importancia.png`). | `cmp` entre ambos árboles |
| **MIA-3** | L | **A** | MIA-3 está **techado en 7**: las 4 acciones del flujo (Sheets, Postgres, Calendar, Gmail) son las vistas en clase; el 10 exige una distinta. | `n8n/flujo.json` nodos; rúbrica pág. 9 |
| **PIA-4** | PIA | **M** | Reserva: la ablación `cyc_norm` no aparece como run en MLflow; el store tiene 81 dirs sin seguimiento y el export está modificado. | `cat docs/evidencia/mlflow/comparativa.csv`; `git status --porcelain docs/evidencia/mlflow/comparativa.csv` |
| **MEM-01** | — | **B** | La memoria Engram #3006 («406 passed») y #3001 («78 passed, 3 skipped») están **obsoletas**; hoy 435 passed / 1 skipped. No existe memoria sobre «bundle B 4.251» ni «cuatro tests fallos». | `mem_get_observation(3006)`; suite de hoy |

---

## 11. Checklist de ejecución

- [ ] **F0** · commit, `git status` (203), hashes y sello del caché (G0)
- [ ] **F1** · `compileall` + gates + conteo de skips (1 esperado) + guards (G1)
- [ ] **F1** · inventario: 1746 versionados + 88 ??; `cobertura.csv` con 1834 filas y 0 sin tier (G6)
- [ ] **F1** · figuras y enlaces abren (G2)
- [ ] **F2** · SAA 1-10 con evidencia por criterio
- [ ] **F3** · PIA 1-6 con evidencia por criterio
- [ ] **F4** · MIA 1-4 con evidencia por criterio
- [ ] **F4** · H1-H15 resueltas (confirmadas o refutadas)
- [ ] **F5** · 2 jueces independientes; discrepancias arbitradas
- [ ] **F6** · informe con veredicto, matriz de 20 celdas, nota ponderada y techo
- [ ] **G3** · toda cifra publicada rastreada (la 4.368 queda como hallazgo C)
- [ ] **G5** · `git status` idéntico a F0 + informe/CSV (la auditoría no tocó nada)
- [ ] **Entregables** · informe + `criterios.csv` + `cobertura.csv` + `hallazgos.csv` + propuesta openspec

---

## Conexiones

- Rúbrica: `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (20 criterios, págs. 5-9)
- Framework: `docs/framework_auditoria.md` (bloques A-Q, fases F0-F6, puertas G0-G6)
- Plan previo: `docs/plans/plan-auditoria-2026-11-06-reto1-v2.md`
- Informes previos: `docs/informes/auditoria-2026-11-06-reto1-v2.md` · `docs/informes/auditoria-2026-11-07-ds02.md`
- Cifras autoritativas: `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md`
- Deuda abierta: `docs/pendiente/deuda-riesgo-7-2026-11-10.md`
