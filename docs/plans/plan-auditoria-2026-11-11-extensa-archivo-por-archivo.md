# Plan de auditoría extensa 2026-11-11 — rúbrica + buenas prácticas + errores potenciales

> **ESTADO: PROPUESTA. NO EJECUTADA.**
> Este documento es el plan que se ejecutará **solo si lo autorizas**. Hasta ahora
> solo se ha leído el repositorio y se ha generado el esqueleto de cobertura.
> **Modo previsto:** solo lectura. No arregla, no commitea, no reentrena, no
> reejecuta cuadernos, no escribe en `models/`, `data/` ni `mlruns/`.
>
> **Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (9 págs., 20 criterios,
> escala 0/3/7/10). Extraída y verificada el 2026-11-11 con `pdfplumber`.
> **Método:** `docs/framework_auditoria.md` v1.0 (bloques A–Q, fases F0–F6,
> puertas G0–G6, severidad C/A/M/B).
> **Cobertura preparada:** `docs/informes/auditoria-2026-11-11/cobertura.csv`
> (1.520 filas; generador reproducible en `gen_cobertura.py`).
> **Antecedentes que esta auditoría NO repite, sino que revalida:**
> `docs/informes/auditoria-2026-11-10-rubrica-integral.md` (SAA 9,7 · PIA 9,4 ·
> MIA 9,0) y `auditoria-2026-11-10-rubrica-post-cierre.md` (SAA 10,0 · PIA 9,4 ·
> MIA 10,0). El repo cambió después: 12 commits de refactor, 7 cuadernos
> regenerados y 28 runs live nuevos.

---

## 0. Las tres preguntas de la auditoría

1. **Rúbrica.** ¿Qué nota da la rúbrica v5, criterio a criterio, al estado actual
   (`refactor/estructura-ds02-clase-2026-11-10`, HEAD `72035c3`)? Cada nota con
   evidencia `path:línea`, comando o hash.
2. **Buenas prácticas.** ¿Qué prácticas de ingeniería, ML y MLOps incumple el
   repo (reproducibilidad, fuga, validación, seguridad, tests, documentación,
   trazabilidad, operación), con severidad y propuesta?
3. **Errores potenciales.** ¿Qué defectos latentes existen —contradicciones de
   cifras, rutas muertas, estados sucios, imports frágiles, errores silenciosos,
   artefactos sin verificar— y cómo se reproducen?

**Criterio de éxito:** las tres preguntas respondidas con evidencia, 1.520 filas
de cobertura con veredicto o `N/A` motivado, 20/20 criterios puntuados, y firma
de no modificación (G5).

---

## 1. Baseline F0 ya medido (se volverá a congelar al ejecutar)

| Dato | Valor medido hoy |
|---|---|
| Rama | `refactor/estructura-ds02-clase-2026-11-10` |
| HEAD | `72035c3` — `chore(repo): fija LF para el texto y renormaliza los ficheros CRLF` |
| Versionados | **1.200** archivos |
| Árbol antes de este plan | **42 rutas**: 14 `M` + 28 `??` |
| Rutas modificadas | 7 cuadernos + 7 `resultados/` (PNG/CSV) |
| Rutas sin seguimiento | 28 directorios de runs live en `mlruns/` |
| Este plan añade | 1 directorio de auditoría (`docs/informes/auditoria-2026-11-11/`) |
| Python | `.venv/Scripts/python.exe` 3.12.10 |
| Código Python | **144 archivos · 25.770 LOC** |
| Tests | **51 archivos** (446 passed, 1 skipped según el verify-report del refactor) |
| Cuadernos | **7**, todos con outputs (14/15/6/16/15/21/5 celdas de código) |
| `mlruns/` versionado | 668 archivos de texto; 19 `meta.yaml` (17 runs curados + 2 metadatos de experimento) |
| `mlruns/` en disco | 47 `meta.yaml` → **45 runs**: 17 curados + **28 live sin seguimiento** (`live__nb01…nb07`) |
| Documentación | 142 `docs/`, 148 `openspec/`, 278 archivos en `MLProyectVault/` (ignorado) |
| Datos locales | `data/processed/` 9 piezas + `data/raw/N-CMAPSS_DS02-006.h5` (ignorados) |

**Hashes de artefactos (medidos hoy):**

| Artefacto | SHA-256 | Contraste |
|---|---|---|
| `models/ensemble.joblib` | `d6c70142…c1a952dd` | = `artifacts.ensemble_sha256` ✅ |
| `models/bilstm_ds02.keras` | `bf9620a7…4c042219` | = `artifacts.bilstm_sha256` ✅ |
| `models/scaler.joblib` | `acccfab3…39541f8d` | = `artifacts.scaler_sha256` ✅ |
| `models/ds02_manifest.json` | `6089457c…ec83ea40` | sello de caché = `artifact.manifest_sha256` ✅ |
| `models/mejor_modelo.joblib` | `5aab4d2a…f4652615f` | = alias de `mejor_modelo_clase.joblib` (XGB) |

> El sello de caché **sí existe**, en `app/cache/cache_manifest.json →
> artifact.manifest_sha256`; no hay que confundirlo con una clave de primer nivel.

**G0:** se re-ejecutará al empezar. Si los hashes o el `git status` cambian entre
este plan y la ejecución, el informe fijará el nuevo estado y lo declarará.

---

## 2. Alcance y cobertura

### 2.1 Universo preparado

`cobertura.csv` tiene **1.520 filas**:

| Origen | Filas | Qué es |
|---|---:|---|
| `git` | 1.200 | todo lo versionado |
| `local-ignorado` | 291 | 278 `MLProyectVault/` + 13 `data/` (H5 + 9 parquet/JSON + 2 README + `.gitkeep`) |
| `untracked` | 29 | 28 runs live + el generador de cobertura |

| Tier | Filas | Regla |
|---|---:|---|
| **A** (leer entero) | 177 | `src/`, `app/`, `tests/`, `scripts/`, `notebooks/`, `n8n/`, configs raíz y CI |
| **B** (cotejar afirmación a afirmación) | 559 | `docs/`, `openspec/`, `docClase/`, vault, READMEs, CSV de resultados |
| **C** (verificar por huella/estructura) | 784 | `mlruns/`, imágenes, joblib/keras/npz, `archive/`, datos locales |

### 2.2 Reparto por grupo

| Grupo | Filas | Foco principal |
|---|---:|---|
| `mlruns` | 696 | 45 runs: nombres, `fuente`, params/métricas, grano, export, tombstones |
| `MLProyectVault` | 278 | 278 notas: cifras, enlaces, coherencia con ADRs e informes (opcional) |
| `openspec` | 148 | specs, changes, verify-reports: promesas vs realidad |
| `docs` | 81 | informes, planes, ADRs, defensa: vigencias y contradicciones |
| `tests` | 51 | contrato real, skips, orden, dependencias externas, tiempo |
| `resultados` | 39 | CSV/PNG citados por README y tests: cifras y duplicados |
| `docs/informes` | 26 | auditorías previas: hallazgos abiertos/cerrados |
| `docs/plans` | 24 | planes: alcance y deuda declarada |
| `models` | 20 | manifiesto, artefactos, alias, legacy, políticas |
| `src/ds02_rul` | 20 | pipeline, stacking, conformal, persistencia, SHAP |
| `app/lib` | 19 | datos, inferencia, reglas, PDF, n8n, contexto |
| `src/clase` | 14 | dataset, pipeline, 5 modelos, MLP, SHAP, tabla |
| `data-local` | 13 | H5, parquet, auditoría de nulos |
| `docs/decisions` | 12 | 12 ADRs: decisión, alternativa, consecuencia |
| `notebooks` | 9 | 7 cuadernos + README + `.gitkeep` |
| `raiz` | 9 | README, AGENT, pyproject, requirements, lock, gitignore |
| `scripts/legacy` | 9 | código FD001: ¿fuera de servicio o roto? |
| `app/ui` | 8 | 4 pestañas, sidebar, paneles, sandbox |
| `scripts/auditoria` | 8 | gates, instrumento OOF, ablaciones |
| `src/mia` | 7 | reglas, motor, casos, calibración, instrumento |
| `app/raiz` | 6 | `_paths`, `__init__`, README |
| `scripts/operativo` | 5 | backfill, estabilidad, predict, gate |
| `app/entrypoints` | 3 | entrypoint de rúbrica + orquestador |
| `app/services` | 2 | API FastAPI |
| `docClase` | 2 | rúbrica PDF + ejemplo de README |
| `scripts/build` | 2 | generador NB07 y caché UI |
| Resto | 9 | `src/raiz` (2), `.github`, `.streamlit`, `.vscode`, `.codegraph`, `n8n`, `nasa`, `scripts/raiz` |
| **Total** | **1.520** | Suma verificada contra `cobertura.csv` (A 177 · B 559 · C 784) |

### 2.3 Reglas de cobertura

- **Tier A:** se lee **entero**, no por muestreo. 177 archivos, 25.770 LOC de
  código + cuadernos + configs.
- **Tier B:** se coteja **cada afirmación verificable** contra su fuente
  (manifiesto, CSV, test, código). No se lee como literatura.
- **Tier C:** se verifica **huella y estructura**, no contenido línea a línea.
  - `mlruns` se audita **por run** (45), no por los 696 ficheros YAML: se
    comprueban `meta.yaml`, `params`, `metrics`, `tags`, `run_id`, `fuente`,
    `status`, y la correspondencia con `docs/evidencia/mlflow/comparativa.csv`.
    Excepción declarada al “una fila por fichero” del framework.
  - Imágenes: hash, dimensiones, fecha y duplicados contra `resultados/` y
    `docs/assets/`.
  - `joblib`/`keras`: hash contra manifiesto, byte size, escritor declarado.
- **Ningún archivo queda sin tier.** `cobertura.csv` lo garantiza; G6 lo verifica.

### 2.4 Fuera de alcance

| Fuera | Motivo |
|---|---|
| Reentrenar o recalibrar | Mueve cifras y destruye la comparación (G5) |
| Reejecutar cuadernos | Cambia outputs y runs; solo se leen |
| Leer el test otra vez | Violaría “test una sola vez” de SAA |
| Escribir en `models/`, `data/`, `mlruns/`, `n8n/` | Solo lectura |
| Desplegar, `git push`, credenciales reales | No autorizado |
| Docker | n/a por decisión 2026-11-07 |
| Preguntas individuales | No auditables desde el repo; techo declarado |

### 2.5 Dependencias externas y techos

| Dependencia | Estado | Efecto si falta |
|---|---|---|
| H5 DS02 (2,3 GB) | Presente en local, **no en git** | Un clon limpio no ejecuta NB01; se declara |
| `data/processed/` | Presente, **sin generador en el repo** | T02 sigue abierto; no se puede reproducir desde cero |
| Instancia n8n | No se usará salvo autorización | MIA-3 se puntúa con estructura + tests + historial documentado |
| MLflow UI | No hace falta: el store es texto | Se verifica con `backfill_mlflow.py --check` y lectura del store |
| Red | No se usa | Sin descargas ni instalaciones salvo autorización |

---

## 3. Método, fases y puertas

### 3.1 Fases

| Fase | Contenido | Salida | Tiempo |
|---|---|---|---|
| **F0** | Congelar commit, árbol, hashes, sello de caché, intérprete, recuentos | tabla de trazabilidad | 20 min |
| **F1** | Mecánica: `compileall`, suite completa `-q -rs`, 4 gates, imports, arranque API/UI headless | G1–G2 | 60 min |
| **F2** | Rúbrica SAA 1–10: README, NB01, 5 clásicos, MLP, SHAP, tabla final | matriz SAA | 75 min |
| **F3** | Rúbrica PIA 1–6: estructura, pipeline, MLflow, app, README, docstrings | matriz PIA | 75 min |
| **F4** | Rúbrica MIA 1–4: negocio, reglas, n8n, guion | matriz MIA | 60 min |
| **F5** | Código y arquitectura: 144 `.py`, capas, errores, seguridad, estado | hallazgos D/J/Q | 120 min |
| **F6** | Cuadernos, documentos, cifras y artefactos: 7 NB, 142 docs, 45 runs | matriz G/H/N | 120 min |
| **F7** | Síntesis + 2 jueces independientes + informe + CSV | informe final | 75 min |

**Total estimado:** 9–11 h de trabajo efectivo, en 2 sesiones. La suite sola son
~4–5 min; la lectura de 25.770 LOC y 45 runs es el grueso.

### 3.2 Oleadas de trabajo (para no perder foco)

| Oleada | Fase | Qué produce |
|---|---|---|
| W0 | F0 | `00_baseline.md` |
| W1 | F1 | `01_mecanica.md` + salida literal de suite y gates |
| W2 | F2 | `02_saa.md` + filas de rúbrica SAA |
| W3 | F3 | `03_pia.md` + filas de rúbrica PIA |
| W4 | F4 | `04_mia.md` + filas de rúbrica MIA |
| W5 | F5 | `05_codigo.md` + hallazgos de `src/` y `scripts/` |
| W6 | F5 | `06_app_tests.md` + hallazgos de `app/` y `tests/` |
| W7 | F6 | `07_datos_cifras.md` + conciliación manifiesto ↔ docs ↔ CSV |
| W8 | F6 | `08_mlflow_n8n.md` + runs, export y flujo |
| W9 | F7 | informe único + `cobertura.csv` relleno + `hallazgos.csv` + `rubrica.csv` |

### 3.3 Reglas de evidencia

1. Cada afirmación lleva `path:línea`, comando con salida y exit, o hash.
2. “Lo he mirado” no es evidencia.
3. Una hipótesis refutada se reporta como refutada.
4. Lo no verificable se declara `NO VERIFICABLE` con motivo; no se maquilla.
5. La nota se baja, no se negocia.
6. Se separa “funciona” de “lo demuestra”.
7. Un solo intérprete: `.venv/Scripts/python.exe`.

### 3.4 Severidad y veredictos

| Nivel | Criterio | Efecto |
|---|---|---|
| **C — Crítico** | Invalida una cifra publicada, un criterio o la seguridad | Bloquea el bloque |
| **A — Alto** | Resta credibilidad o rompe el 10 de un criterio | Se reporta primero |
| **M — Medio** | Inconsistencia detectable por un lector atento | Siguiente iteración |
| **B — Bajo** | Pulido, enlaces, redacción | Anexo |

Veredicto por bloque: **PASA / PASA CON RESERVAS / FALLA / NO VERIFICABLE**.
El global es la peor puerta, no el promedio.

### 3.5 Puertas

| Puerta | Condición | Si falla |
|---|---|---|
| **G0** | Commit + árbol + hashes + sello congelados | No se auditan cifras |
| **G1** | `compileall` y suite ejecutan; skips nombrados | Hallazgo Crítico |
| **G2** | Toda figura, enlace y ruta citada existe | Hallazgo Alto |
| **G3** | Toda cifra publicada es rastreable | Crítico o Alto según cifra |
| **G4** | Cada criterio tiene evidencia para su nota | Se baja la nota |
| **G5** | `git status` final = inicial + entregables de auditoría | No se publica |
| **G6** | 1.520/1.520 filas con tier y veredicto o `N/A` | Hallazgo Alto de cobertura |

### 3.6 Solo lectura, con una excepción controlada

- La auditoría **no modifica** código, artefactos, datos, cuadernos ni store.
- Los únicos archivos nuevos son los de `docs/informes/auditoria-2026-11-11/`.
- Si se autoriza arrancar API/UI, se hace en puertos loopback y se cierran.
- Si se autoriza instalar analizadores, se instalan **en `.venv`**, no en
  `requirements.txt` ni `pyproject.toml`, y se declara.

---

## 4. Matriz de la rúbrica v5 (20 criterios)

Escala 0/3/7/10. Se puntúa con la evidencia, no con la intención. Los textos del
ancla 10 están resumidos; la cita literal vive en el PDF.

### 4.1 SAA — 10 criterios

| # | Peso | Ancla 10 (resumen) | Dónde se prueba | Cómo se falsifica |
|---|---:|---|---|---|
| 1 | 5 % | IA débil + comparación razonada con IA fuerte | `README.md` “Qué hemos construido” | Si solo dice “IA débil” sin comparar |
| 2 | 10 % | Tipo de aprendizaje + diferencia con no supervisado | `README.md`, NB02 | Si no distingue supervisado/no supervisado |
| 3 | 5 % | Tabla de campos + nulos por campo + campos que quita y por qué | README, NB01, `dataset_clase.py` | Si la tabla no dice nulos o no justifica exclusiones |
| 4 | 5 % | ≥5 gráficos comentados: barras, histograma, boxplot, dispersión, heatmap | NB01 (26 celdas MD) | Si falta un tipo o no hay comentario debajo |
| 5 | 5 % | Patrón de nulos + variable nueva útil y explicada | `auditoria_nulos.json`, `fase_vuelo` | Si imputa sin decir MCAR/MAR/MNAR |
| 6 | 30 % | 5 modelos + algo no visto en clase, con mejora demostrada | `train_clasicos.py`, `comparativa.csv`, bundle C | Si falta un modelo o el extra no se compara |
| 7 | 20 % | MLP base + 3 experimentos, con hipótesis por experimento | `train_mlp.py`, `mlp_comparativa.csv` | Si hay 3 experimentos sin porqué |
| 8 | 10 % | MAE/RMSE/R² + real vs predicho + significado para la empresa | README, `_tab_auditoria.py`, figuras | Si publica cifras no trazables o no traduce el error |
| 9 | 5 % | Elige por validación + tabla con tiempo + SHAP con validación | `tabla_final.py`, `shap_clase_e2.py` | Si elige por test o el SHAP usa test |
| 10 | 5 % | Pregunta individual + lo enseña en código/resultados | `docs/defensa/guiones-15min.md` | No verificable desde el repo |

### 4.2 PIA — 6 criterios

| # | Peso | Ancla 10 (resumen) | Dónde se prueba | Cómo se falsifica |
|---|---:|---|---|---|
| 1 | 10 % | README con 6 apartados + funciones documentadas + apartados propios | README, AST de docstrings | Si falta un apartado o una función pública |
| 2 | 10 % | Estructura de carpetas + funciones + `requirements.txt` correcto | Árbol real vs rúbrica, pins | Si la estructura literal no existe o los pins divergen |
| 3 | 20 % | Pipeline sklearn + modelo guardado incluye pipeline + predice caso nuevo | `pipeline_clase.py`, joblib, NB02 | Si el joblib es solo el regresor |
| 4 | 20 % | Todos los modelos en MLflow + comparación + capturas | Store, export, 3 PNG | Si falta una run o el store no viaja |
| 5 | 25 % | App evalúa test + predice caso nuevo + muestra `p` con la decisión | `app/entrypoints/*`, `app/ui/*` | Si no muestra la `p` o no evalúa test |
| 6 | 15 % | Pregunta individual + código/resultados | `guiones-15min.md` §2 | No verificable desde el repo |

### 4.3 MIA — 4 criterios

| # | Peso | Ancla 10 (resumen) | Dónde se prueba | Cómo se falsifica |
|---|---:|---|---|---|
| 1 | 20 % | Problema de negocio con dato + objetivo + mejora para la empresa | README, coste del error | Si el dato no tiene fuente o no hay mejora |
| 2 | 30 % | ≥6 reglas con prioridad, porqué y regla de seguridad | `src/mia/reglas.py`, motor | Si hay <6 o falta seguridad/prioridad |
| 3 | 35 % | Webhook + una rama por decisión + acción distinta a las de clase | `n8n/flujo.json`, tests, historial | Si las 3 ramas hacen lo mismo o no hay acción novedosa |
| 4 | 15 % | Pregunta individual + código/resultados | `guiones-15min.md` §3 | No verificable desde el repo |

### 4.4 Puntuación

```text
SAA = Σ(nota_i × peso_i) / 100,  i = 1..10
PIA = Σ(nota_i × peso_i) / 100,  i = 1..6
MIA = Σ(nota_i × peso_i) / 100,  i = 1..4
Techo global = min(SAA, PIA, MIA)
```

Se reportarán **dos lecturas**: literal (solo lo que el repo demuestra) y
defensa (incluyendo lo que el guion permite explicar). La diferencia entre ambas
es un hallazgo, no una nota.

---

## 5. Protocolo archivo por archivo

### 5.1 Módulo Python (177 tier A incluyen 144 `.py`)

Por cada archivo:

1. **Contrato:** docstring de módulo y de API pública; firma vs uso real.
2. **Fronteras:** imports permitidos por capa (`datos → features → modelo →
   decisión → superficie`); ciclos; imports invertidos.
3. **Efectos al importar:** ¿lee disco, entrena, arranca UI o escribe al importar?
4. **Errores:** `except` desnudo, `except Exception` que traga, `pass`, retorno
   silencioso, `NotImplementedError` en ruta viva.
5. **Validación de entrada:** tipos, rangos, `NaN`/`Inf`, unidad vacía, `None`.
6. **Estado global:** cachés de módulo, singletons, mutabilidad compartida.
7. **Unidades:** RUL en ciclos, umbrales 30/25, banda 90 %, tiempo en s.
8. **Seguridad:** rutas absolutas, `eval`/`exec`, deserialización, secretos,
   `0.0.0.0`, comparación de tokens.
9. **Determinismo:** semillas, orden, `PYTHONHASHSEED`, ramas no deterministas.
10. **Duplicación:** misma métrica/umbral/banda en dos sitios; cuál manda.
11. **Código muerto:** exports sin consumidor, compatibilidad sin dueño.
12. **Rutas:** relativas vs absolutas; Windows vs Linux; `__file__` vs cwd.

### 5.2 Test (51 archivos)

1. ¿Prueba el **contrato** o la implementación?
2. ¿Fallaría si cambia el artefacto, la cifra o el umbral?
3. Skips: nombre, motivo, condición; un skip nuevo es hallazgo.
4. Dependencias externas: red, caché, git, n8n; ¿se saltan en silencio?
5. Orden: ¿pasa aislado y en suite? (el refactor ya encontró un fallo de orden).
6. Fixtures: idempotencia, limpieza, `finally`, estado persistido.
7. Determinismo: semillas, TF, orden de dict, hash.
8. Tiempo: suite < 5 min; sin reentrenar.
9. Cobertura real de los caminos de borde: nulos, umbrales invertidos, payload
   inválido, unidad vacía, decisión desconocida.
10. Asserts que se debilitaron para pasar: se buscan explícitamente.

### 5.3 Cuaderno (7 `.ipynb`)

Se inspecciona como JSON de celdas, nunca como binario:

1. `execution_count` monótono y sin huecos; orden real de ejecución.
2. Outputs presentes y coherentes con el código; sin salidas obsoletas.
3. Cifras del output vs README/manifiesto/CSV.
4. Fuga: split por motor, `ffill` causal, escalado ajustado sin test, ventanas
   centradas, `cycle` como predictor.
5. “Test una sola vez”: ¿se relee el test para seleccionar?
6. Rutas absolutas, imports que dependen del cwd, `sys.path`.
7. Semillas y reproducibilidad; celdas que reentrenan o escriben en `models/`.
8. Comentarios MD: qué veo/qué concluyo debajo de cada figura.
9. Tiempos y logs: `None`/vacíos declarados, no maquillados.
10. Coherencia con el relato de defensa (`docs/defensa/mapa-nb01-nb07.md`).

### 5.4 Documento (559 tier B)

1. Cada cifra, fecha, ruta y enlace se coteja con su fuente.
2. Un solo campeón vigente; lo histórico rotulado como histórico.
3. Enlaces internos y figuras abren (G2).
4. Diagramas coherentes con módulos y flujo reales.
5. READMEs de subcarpeta con su contrato.
6. ADRs con decisión, alternativas rechazadas y consecuencia.
7. Sin promesas de futuro escritas como presente.
8. Fecha y versión; lo caducado se marca, no se borra.
9. Duplicación de fuentes: se identifica cuál manda.
10. Idioma y tono consistentes.

### 5.5 Artefacto y configuración

1. SHA-256 vs manifiesto **antes** de deserializar.
2. Escritor declarado (`script:función:línea`) y comando de regeneración.
3. Loader único; nadie carga por su cuenta saltándose la verificación.
4. Caché con sello del manifiesto fuente y hash de los parquet.
5. Legacy separado y rotulado; nunca citado como vigente.
6. `requirements.txt` ↔ `pyproject.toml`: mismos pins, sin duplicidad divergente.
7. `requires-python` vs CI vs `.venv` vs manifiesto (`3.12.10`).
8. CI: ramas cubiertas, gates, prohibición de reentrenar.
9. Secretos: `.env` fuera de git, defaults seguros, sin eco en logs.
10. `.gitignore`: datos, resultados, runs, respaldos y artefactos temporales.

### 5.6 Run de MLflow (45)

1. `meta.yaml`: `run_id`, `experiment_id`, `status`, `start_time`, nombre.
2. `params`: modelo, semilla, ventana, features, grano.
3. `metrics`: RMSE/MAE/R²/NASA/tiempo; `NaN`/`Inf` descartados.
4. `tags`: `fuente=historico|live_notebook`, `run_key`, `grano`, `job`.
5. Coherencia con `docs/evidencia/mlflow/comparativa.csv` (17 filas curadas).
6. Grano: no mezclar fila y ventana en la misma comparación.
7. Duplicados, tombstones, `.trash`, runs vacíos.
8. Runs live: ¿untracked? ¿se deben commitear, ignorar o restaurar?
9. Capturas: corresponden al run y a la cifra citada.
10. “Todos los modelos” de PIA-4: 5 clásicos + MLP base/E1/E2/E3 + ventana.

---

## 6. Checklist de buenas prácticas (bloques A–Q)

| Bloque | Comprobaciones específicas de este repo |
|---|---|
| **A. Inventario** | 1.200 versionados + 291 locales; 1.520 filas; duplicados (`mejor_modelo*`), huérfanos, `.bak`, `.hermes-respaldo`, `archive/` |
| **B. Entorno** | pins 22↔22 con `tomllib`; Python 3.12.10; `pip install -e .`; imports por `sys.path`; arranque API/UI; semillas; rutas Windows/Linux |
| **C. Build** | n/a contenedores; CI cubre `main`/`clase-*`, **no** `refactor/*`; gates fuera del CI |
| **D. Código** | `compileall`; capas `app.lib/ui/services`; 79 `sys.path.insert`; 20 `except Exception`; 2 `eval/exec`; 35 `joblib.load`; estado global; docstrings |
| **E. Datos** | split por motor; `RUL` no como feature; `ffill` causal; escalado sin test; nulos MAR; 1.185 nulos T30; duplicados; rangos; test leído una vez |
| **F. Modelo** | baseline; 5 clásicos + MLP; OOF agrupado; stacking sin in-sample; ablación `cyc_norm`; multiseed; banda 90 %; macro-RMSE U14 8,58; límites |
| **G. Cifras** | manifiesto → CSV → test → README/EN/AGENT/e00/framework/NB; 4.338/3.227/0.9461/2336.2; 4.324±0.107; 4.368 obsoleto; 0.9016 |
| **H. Artefactos** | 4 SHA; manifiesto; `load_ensemble`; sello `artifact.manifest_sha256`; `instrumento_oof.npz` sin hash; alias manual; legacy |
| **I. Reglas** | 8 reglas, R1 prioridad 10; una pasada; `L_inf`; casos `NaN`/`None`/umbral invertido; traza; umbral único 30/25 |
| **J. API** | `/health`, `/predict`, `/units`, `/n8n-decision`; token `compare_digest`; rate limit; CORS; docs abiertos; errores sin stack; 0.0.0.0 |
| **K. UI** | 4 pestañas; estados vacío/error/carga; cifras = artefacto; `p` junto a decisión; persistencia atómica; caché; accesibilidad |
| **L. n8n** | JSON importable; `active:false`; credencial `REEMPLAZAR`; 3 ramas; acción propia HANGAR; idempotencia; ejecuciones reales vs documentadas |
| **M. Tests** | 446 passed/1 skipped; skip `needs_oof`; orden; fixtures; dependencias; tiempo; cobertura honesta |
| **N. Documentación** | 6 apartados README; un campeón; enlaces; diagramas; ADRs; fechas; duplicados `docs/assets` |
| **O. Negocio** | AOG 10–15k USD/h con credibilidad Media; umbrales → consecuencia; ROI; falso negativo; deriva |
| **P. Ética** | IA débil; licencia del dataset; revisión humana; sesgo por unidad; límites visibles; reproducibilidad |
| **Q. Operación** | arranque en frío; dependencias; puntos únicos; deuda con coste; onboarding; rollback; quién despliega |

---

## 7. Hipótesis de error (se escriben antes de comprobar)

> Ninguna es un hallazgo todavía. Cada una declara cómo se falsifica. Si se
> refuta, se reporta como refutada.

| ID | Sospecha | Semilla de evidencia | Falsación | Sev. si se confirma |
|---|---|---|---|---|
| **H-01** | El store tiene 28 runs live sin seguimiento y el README sigue diciendo “17 runs y ninguna `live__*`” | `mlruns/` 47 `meta.yaml` vs 19 trackeados; 28 `??` | `grep -c live__ mlruns/.../tags/mlflow.runName` vs README | A (PIA-4/G) |
| **H-02** | Los 7 cuadernos regenerados (11-11, 18:08–22:44) tienen outputs que no coinciden con el CSV/manifiesto citado | 7 `M`; mtimes; `resultados/*.csv` `M` | Comparar cifras de outputs con `models/ds02_manifest.json` | A (G) |
| **H-03** | La rúbrica pide `src/reglas.py`, `src/utils.py`, `app/streamlit_app.py`, `notebooks/01_eda.ipynb`; el commit `813869e` retiró las fachadas y el refactor movió el entrypoint | `ls` → NO en las 4 rutas; `git log` | Leer la estructura “básica” del PDF y decidir si es literal o orientativa | A/M (PIA-2, MIA-2) |
| **H-04** | El CI no cubre la rama de refactor ni los gates; el verde es local | `.github/workflows/ci.yml` → `main`, `clase-*` | `git branch --show-current` vs `on.push.branches` | M/A (Q) |
| **H-05** | Un clon limpio no puede ejecutar NB01: `data/processed/` no está y no tiene generador | `data/README.md`: “copia manual” | `git ls-files data` → 0; `dataset_clase.py` no escribe parquet | A (B/E) |
| **H-06** | El skip `needs_oof` sigue apuntando a `_p1_oof_cache.npz`; el verify-report dice 446 pero el recuento real puede ser 445/446 con 1 skip | `tests/test_mia_rules.py:181`; `@needs_oof` | Ejecutar suite `-q -rs` y contar | M (M) |
| **H-07** | Quedan 79 `sys.path.insert` y el refactor solo dejó los entrypoints; puede haber shadowing `reglas` | `git grep sys.path.insert` → 79 | Contar por directorio y probar `test_rules_gate` en orden | M (D) |
| **H-08** | 20 `except Exception` pueden tragar fallos de datos/modelo y devolver una decisión con estado incompleto | `git grep` | Inspeccionar cada uno y su rama de error | M/A (D/I) |
| **H-09** | 35 `joblib.load` pueden saltarse la verificación de hash de `load_ensemble` | `git grep joblib.load` | Ver si cada uno verifica SHA o es test/CLI | M (H) |
| **H-10** | Los umbrales 30/25 se declaran “dueño único” pero reaparecen duplicados en UI y helpers | `_constantes.py` vs `_sidebar.py`, `_sandbox_estres.py`, `ui_alta.py`, `dashboard_helpers.py` | `grep -rn "30\\.0\\|25\\.0" app/` y comparar | M (I) |
| **H-11** | La API puede exponer `0.0.0.0`, docs abiertos o rate limit solo en memoria | 3 ocurrencias de `0.0.0.0`; `app/services/api.py` | Leer `api.py`, `test_security_api.py`, `test_api_limites.py` | A (J) |
| **H-12** | Hay 2 `eval`/`exec` en código vivo | `git grep eval/exec` | Ver archivo, contexto y entrada | A (D/J) |
| **H-13** | `docs/assets/` duplica PNG de `resultados/`, con 2 divergentes | Auditoría previa B-02 | `sha256sum` de ambos conjuntos | B (N) |
| **H-14** | Caché 4.3382/3.2266 vs manifiesto 4.338/3.227 vs README: tres precisiones sin rótulo de alcance | `cache_manifest.json`; manifiesto | Comparar y decidir si es redondeo o contradicción | B (G) |
| **H-15** | “Test una sola vez” puede romperse si la app reevalúa test al abrir o si NB06 vuelve a leerlo | README; `ui_data_loader.py`; NB06 | Rastrear cada lectura del test | A (SAA-8/E) |
| **H-16** | Los runs live mezclan grano fila (NB02) y ventana (NB03) en el mismo experimento | 28 live: `live__nb02_*` y `live__nb03_*` | Leer tags `grano` de cada run | M (G/PIA-4) |
| **H-17** | `mejor_modelo.joblib` es el XGB (8,2173), no el E2 (7,3404); la rúbrica PIA-3 puede leerlo como “el mejor” | `models/README.md`; hashes iguales al XGB | Cargar el joblib y comparar `rmse_val` | M (PIA-3) |
| **H-18** | Los nombres de cuadernos no siguen la estructura básica del PDF (`01_eda`, `02_modelos_A`, `03_modelos_B`) | `notebooks/` 01–07 con nombres largos | Leer el PDF: ¿estructura obligatoria u orientativa? | M/B (PIA-2) |
| **H-19** | El README promete 4 pestañas y SHAP del híbrido, pero SHAP explica solo el LGBM; la app puede haber cambiado tras el refactor | `README.md`; `app/README.md`; verify-report | Abrir la app headless y recorrer las 4 pestañas | M (K/N) |
| **H-20** | El “0 funciones públicas sin docstring” puede haber cambiado con 25 módulos nuevos | AST previo; refactor | AST sobre `src/` y `app/` | B (PIA-1) |
| **H-21** | El refactor eliminó `src/reglas.py` y `src/utils.py`, pero la rúbrica MIA-2 cita `src/reglas.py`; el guion de defensa puede seguir citándolo | `git show 813869e`; `guiones-15min.md` | `grep -rn "src/reglas.py" docs/ scripts/ tests/` | A (MIA-2/N) |
| **H-22** | `scripts/legacy/predict.py` sigue apuntando a `models/v3_bundle.joblib` inexistente | Auditoría previa M-03 | Ejecutar con `--help` o leer la ruta | M (Q) |
| **H-23** | El instrumento OOF sigue sin hash en el manifiesto y `freeze_oof_instrument.py` carga joblib sin verificar | Auditoría previa M-02/B-04 | `grep instrumento_oof`; leer el script | M (H) |
| **H-24** | `n8n/flujo.json` sigue con `REEMPLAZAR_CREDENCIAL` y `active:false`; el flujo vivo no coincide | Auditoría previa B-05 | Leer JSON; comparar con instancia solo si se autoriza | M/A (L) |

---

## 8. Entregables

| Archivo | Contenido |
|---|---|
| `docs/informes/auditoria-2026-11-11-extensa.md` | Informe único: baseline, alcance, método, resultados por bloque, 20 criterios, hallazgos, límites, firma G5 |
| `docs/informes/auditoria-2026-11-11/cobertura.csv` | 1.520 filas: `path,tier,grupo,tipo,loc,origen,estado,evidencia` con veredicto |
| `docs/informes/auditoria-2026-11-11/rubrica.csv` | 20 filas: criterio, peso, nota, evidencia, qué falta para 10 |
| `docs/informes/auditoria-2026-11-11/hallazgos.csv` | ID, bloque, severidad, síntesis, reproducción, evidencia, impacto, propuesta |
| `docs/informes/auditoria-2026-11-11/anexo_comandos.md` | Comandos y salidas literales (suite, gates, hashes, recuentos) |
| `docs/informes/auditoria-2026-11-11/00_baseline.md` … `08_*.md` | Notas de trabajo por oleada (opcionales, para trazabilidad) |

**No se entrega:** parches, cambios de código, runs nuevos, artefactos
regenerados ni commits. Las propuestas quedan escritas, no aplicadas.

---

## 9. Criterios de aceptación (Definition of Done)

- [ ] 1.520/1.520 filas con `estado` distinto de `pendiente` o `N/A` motivado.
- [ ] 20/20 criterios con nota, evidencia y “qué falta para el 10”.
- [ ] Toda cifra de README/EN/AGENT/e00/framework/docs/NB reconciliada o marcada.
- [ ] Todo hallazgo con reproducción, severidad, impacto y propuesta.
- [ ] Dos jueces independientes sobre las notas; discrepancias resueltas por escrito.
- [ ] `compileall` y suite ejecutados con exit y skips nombrados.
- [ ] 4 gates ejecutados con su salida.
- [ ] G5: `git status` final = inicial + entregables de auditoría.
- [ ] Límites declarados (n8n, datos, preguntas individuales, herramientas).
- [ ] Sin reentrenar, sin reejecutar cuadernos, sin tocar `models/`.

---

## 10. Riesgos y límites de esta auditoría

| Riesgo | Mitigación |
|---|---|
| Árbol sucio (42 rutas) invalida “clon limpio” | Se congela el estado y se declara; no se finge un commit limpio |
| 7 cuadernos `M` + 7 resultados `M` | Se audita el working tree y se compara con HEAD |
| 28 runs live untracked | Se auditan como runs; se decide si son evidencia o ruido |
| `data/processed` sin generador | Se verifica en local; se declara T02 |
| Sin `ruff/mypy/bandit/vulture` | AST + `compileall` + `pytest`; instalar solo con autorización |
| TF/Keras no determinista | Se documenta; no se exige bit-reproducibilidad |
| Suite ~4–5 min | Se ejecuta una vez; no se repite por cada hallazgo |
| n8n sin instancia autorizada | MIA-3 con estructura + tests + historial; techo declarado |
| Preguntas individuales | No puntuables desde el repo; techo y límite |
| MLProyectVault 278 notas | Bloque B opcional; si no se autoriza, se marca `N/A` |
| Tiempo | 9–11 h; se entrega por oleadas, no en una sola respuesta |

---

## 11. Autorización que necesito

Marca o responde a estas decisiones. Sin ellas no ejecuto la auditoría.

| # | Decisión | Opciones | Recomendación |
|---|---|---|---|
| 1 | **¿Ejecutar la auditoría?** | Sí / No / Solo una parte | Sí, completa |
| 2 | **Alcance** | (a) 1.520 filas, incluye vault y datos locales; (b) 1.200 versionados; (c) solo código+rúbrica | (a) |
| 3 | **Modo** | (a) solo lectura estricta; (b) permitir arreglos después, en otra rama | (a) |
| 4 | **Suite y superficies** | (a) suite + gates + API/UI headless; (b) solo suite+gates; (c) nada | (a) |
| 5 | **Analizadores** | (a) instalar `ruff`, `mypy`, `bandit`, `vulture` en `.venv`; (b) solo AST/`compileall` | (a) si no te importa tocar el venv |
| 6 | **n8n** | (a) solo estático; (b) inspección de solo lectura de la instancia | (a) |
| 7 | **Salida** | (a) informe + CSV, sin commit; (b) además commit de evidencia | (a) |
| 8 | **Vault** | (a) incluir 278 notas; (b) excluir y marcar `N/A` | (a) si quieres cubrir la defensa |

---

## Anexo A — Comandos que se ejecutarán (solo lectura)

```bash
# F0
git rev-parse HEAD && git status --porcelain | wc -l
sha256sum models/ensemble.joblib models/bilstm_ds02.keras models/scaler.joblib models/ds02_manifest.json
python -c "import json,hashlib,pathlib; ..."   # sello artifact.manifest_sha256

# F1
.venv/Scripts/python.exe -m compileall -q src app scripts tests; echo "exit=$?"
.venv/Scripts/python.exe -m pytest tests -q -rs -p no:cacheprovider; echo "exit=$?"
.venv/Scripts/python.exe scripts/auditoria/freeze_rules_evidence.py; echo "exit=$?"
.venv/Scripts/python.exe scripts/auditoria/freeze_oof_instrument.py --check; echo "exit=$?"
.venv/Scripts/python.exe scripts/operativo/backfill_mlflow.py --check; echo "exit=$?"
.venv/Scripts/python.exe scripts/operativo/verify_gate.py; echo "exit=$?"

# F1 — superficies (si se autoriza)
.venv/Scripts/python.exe -m uvicorn app.services.api:app --host 127.0.0.1 --port 8000 &
curl -fsS http://127.0.0.1:8000/health
.venv/Scripts/python.exe -m streamlit run app/entrypoints/dashboard_ds02.py \
  --server.address 127.0.0.1 --server.port 8501 --server.headless true &

# F5 — estático
.venv/Scripts/python.exe - <<'PY'   # AST: docstrings, imports, capas, except, eval
...
PY

# F6 — cifras
grep -RIn "4\.338\|4\.324\|4\.368\|2336\.2\|0\.9016\|0\.9012" \
  README.md README.en.md AGENT.md docs/ MLProyectVault/50-Evidencia/ models/ds02_manifest.json
```

---

## Anexo B — Recuentos que sostienen el plan

```text
git ls-files | wc -l                               1200
git status --porcelain | wc -l                       42  (+1 dir de auditoría)
git ls-files '*.py' | wc -l                         144
git ls-files '*.py' | xargs cat | wc -l           25770
git ls-files 'tests/*' | wc -l                       51
git ls-files '*.ipynb' | wc -l                        7
find mlruns -name meta.yaml | wc -l                  47
git ls-files 'mlruns/**/meta.yaml' | wc -l           19
runs en disco                                        45  (17 curados + 28 live)
cobertura.csv                                      1520  (A 177 · B 559 · C 784)
```

---

## Anexo C — Cómo se rellena `cobertura.csv`

| Columna | Valores | Regla |
|---|---|---|
| `path` | ruta relativa | Una fila por archivo; runs live por directorio |
| `tier` | A/B/C | A lectura entera; B cotejo; C huella |
| `grupo` | directorio lógico | Ver §2.2 |
| `tipo` | python/test/notebook/doc/artefacto/… | Deriva de la extensión |
| `loc` | entero o vacío | Líneas de texto; vacío en binarios |
| `origen` | git / untracked / local-ignorado | Procedencia |
| `estado` | pendiente / leido / cotejado / hash_ok / N/A / FALLA | Veredicto por archivo |
| `evidencia` | `path:línea`, comando, hash | Obligatorio si `estado ≠ pendiente` |

---

*Plan v1 · 2026-11-11 · rama `refactor/estructura-ds02-clase-2026-11-10` · HEAD `72035c3` · pendiente de autorización.*
