# Auditoría ejecutada — Rúbrica Reto 1 v5 (2026-11-10)

> **Modo:** solo lectura. No se modificó código, artefacto, notebook, dato ni configuración.
> **Plan:** `docs/plans/plan-auditoria-2026-11-10-rubrica-exhaustiva.md`
> **Rúbrica:** `docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf` (9 págs., 20 criterios)
> **HEAD:** `10761e7b960f2404adb8cfea93b82072ec4cb213` · rama `fix/auditoria-2026-11-10`
> **Árbol al cerrar:** 19 `M` + 3 `??` (18 `M` preexistentes + `docs/pendiente/plan-cierre-rubrica.md`, modificado durante la sesión y ajeno; plan, respaldo vacío y este informe); 1.171 ficheros versionados
> **Informe previo:** `docs/informes/auditoria-2026-11-10-rubrica-post-cierre.md` (SAA 10,0 · PIA 9,4 · MIA 10,0)

---

## 1. Veredicto

**SAA 10,0 / 10 · PIA 10,0 / 10 · MIA 10,0 / 10. Techo: 10,0.**

Los 20 criterios alcanzan su ancla de 10. No hay ningún criterio roto por un fallo funcional.
Lo que separa este 10 de una entrega segura no es la rúbrica, sino **tres riesgos de entrega**
(§5: C1, C2, A1) y una docena de defectos de robustez/documentación.

Con **lectura estricta de proceso** (tracking MLflow en vivo, ejecución n8n real y coste del
error cuantificado) el suelo realista es **SAA 9,7 · PIA 9,4 · MIA 8,95**, techo 9,4. Las tareas
T06, T09 y T12 del backlog son exactamente las que cierran esa brecha.

---

## 2. F0/G0 — baseline

| Comprobación | Valor |
| --- | --- |
| HEAD | `10761e7b…` · 2026-11-10 15:43 · `test(mlflow): alinea la aserción de backfill con los 17 runs` |
| Árbol | **20 rutas** en F0: 18 `M` + 2 `??` (plan y respaldo vacío del fixture) |
| Versionados | **1.171** |
| `models/ensemble.joblib` | `d6c70142…1a952dd` |
| `models/bilstm_ds02.keras` | `bf9620a7…c042219` |
| `models/scaler.joblib` | `acccfab3…9541f8d` |
| `models/ds02_manifest.json` | `6089457c…3ea40` |
| Sello caché ↔ manifiesto | **`seal_ok True`** |

**G0: PASA.** El binario que sirve la app es el que firma el manifiesto.

**Nota F6:** durante la sesión apareció un `M` adicional en
`docs/pendiente/plan-cierre-rubrica.md`, ajeno a esta auditoría. El baseline F0 sigue siendo
18 `M` + 2 `??`; el recuento de cierre es 19 `M` + 3 `??`.

---

## 3. F1 — mecánica, gates y suite

| Comprobación | Resultado |
| --- | --- |
| `python -m compileall -q src app scripts tests` | **exit 0** |
| `python scripts/freeze_rules_evidence.py` | **exit 0** · cobertura OOF 0,901643 · 14.915 filas puras · R2b máx +1,4756 |
| `python scripts/freeze_oof_instrument.py --check` | **exit 0** · instrumento 14.915 filas · banda reproduce `calibracion_banda.json` |
| `python scripts/backfill_mlflow.py --check` | **exit 0** · 17 runs (9 fila + 4 ventana + 4 ablación), export = store, 0 artefactos |
| `python -m pytest tests -q -rs -p no:cacheprovider` | **exit 1 · 445 errores, 1 skip en 38,75 s** |

La suite **no corre en este árbol** por un residuo local, no por una regresión del código: el
fixture `_flota_limpia` intenta mover `app/registros_sesiones` a un respaldo que ya contiene una
carpeta vacía `registros_sesiones`, y `shutil.move` falla en el setup de **todos** los tests.
En un clon limpio no existe `app/registros_sesiones`, el fixture no dispara y la suite pasa (la
auditoría previa midió 444 passed con `c14d91b`). El defecto real es que el fixture **no es
idempotente ni exception-safe**: si el `shutil.move` falla, el `yield` no se alcanza y el teardown
no restaura nada, aunque el registro ya se haya copiado y borrado.

**Efecto colateral contenido:** en este árbol el setup falló antes del `yield`, así que el teardown
no corrió. El respaldo `app/registros_flota.json.hermes-respaldo` quedó con 49 B y el registro
legacy `app/registros_flota.json` está ausente. **No se perdió flota:** el fichero legacy es un
estado vacío por diseño (`docs/plans/coste-arreglos-app.md:22`) y las 2 sesiones de
`app/registros_sesiones/` siguen intactas y vacías. El incidente es el hallazgo C1.

---

## 4. Matriz de 20 criterios

Escala 0/3/7/10. La columna «Ancla 10» dice qué parte del nivel superior está cubierta.

### 4.1 SAA — 10 criterios (100 %)

| # | Criterio (peso) | Nota | Evidencia y ancla 10 |
| --- | --- | ---: | --- |
| 1 | IA débil (5 %) | **10** | `README.md:29`: «solo predice RUL de DS02… no sabría fijar precios»; se compara con una AGI y se razona por qué no transfiere. |
| 2 | Tipo de aprendizaje (10 %) | **10** | `README.md:29`: supervisado + regresión + diferencia explícita con no supervisado (etiqueta y métrica contra verdad). |
| 3 | Dataset y campos (5 %) | **10** | `README.md:49-84`: 20 campos con significado, tipo y nulos antes/después; 3 campos quitados con por qué, grueso y `path:línea`. |
| 4 | Gráficos comentados (5 %) | **10** | NB01 celdas MD 10-32: barras, histograma, boxplot, dispersión, heatmap y residual; cada figura con «Cómo leer» y «Qué concluyo». |
| 5 | Nulos + variable nueva (5 %) | **10** | `src/clase/dataset_clase.py:11-18`: MAR en T30 (alt>27k, Mach>0,68), ffill causal + mediana solo train, `fase_vuelo` desde régimen; `data/processed/auditoria_nulos.json`. |
| 6 | Cinco modelos + extra (30 %) | **10** | `src/clase/train_clasicos.py:38-70` (Ridge, KNN, RF, XGB, SVR + grids), `:128-150` (GridSearchCV + GroupKFold por motor); extra híbrido **4,338** frente a LGBM 7,067 / BiLSTM 5,654. |
| 7 | MLP base + 3 experimentos (20 %) | **10** | `src/clase/train_mlp.py:38-44`: base/E1/E2/E3, **cada uno con su hipótesis**; `resultados/mlp_comparativa.csv` con params, tiempos y métricas. |
| 8 | Métricas y errores (10 %) | **10** | Train/val/test + `real_vs_pred` (`resultados/clasicos_real_vs_pred.png`, `mlp_real_vs_pred.png`); `app/ui_modulos/_tab_auditoria.py:169-180` explica el sesgo negativo como «el error caro» y mide MAE en zona crítica. |
| 9 | Mejor modelo + SHAP (5 %) | **10** | `resultados/tabla_final_clase.csv` (métricas + tiempo + grano); elección por `rmse_val` con desempate al simple (`train_clasicos.py:150`, `train_mlp.py:132`); SHAP **de validación** del E2 (`shap_clase_e2.py:123-124,178`) y SHAP del bundle en `app/ui_shap.py`. |
| 10 | Pregunta individual (5 %) | **10** | `docs/defensa/guiones-15min.md` §1: 4 preguntas con respuesta, `path:línea` y «qué NO decir». |

### 4.2 PIA — 6 criterios (100 %)

| # | Criterio (peso) | Nota | Evidencia y ancla 10 |
| --- | --- | ---: | --- |
| 1 | Documenta código y README (10 %) | **10** | `README.md` con los 6 obligatorios + 6 propios; **0 funciones públicas sin docstring** (AST sobre `src/` y `app/`); 38/39 módulos con docstring. |
| 2 | Carpetas y funciones (10 %) | **10** | `src/utils.py`, `src/reglas.py`, `src/n8n.py`, `app/streamlit_app.py`, `notebooks/01-07`, `models/`, `n8n/`, `resultados/`; `requirements.txt` con 22 pins = 22 de `pyproject.toml`. |
| 3 | Pipeline sklearn (20 %) | **10** | `pipeline_clase.py:27` (`ColumnTransformer` + `StandardScaler` + `OneHotEncoder`) y `:43` (`predict_caso_nuevo`); el joblib contiene `pre`+`reg` y predice: **66,29** (XGB) y **6,58** (E2). |
| 4 | MLflow (20 %) | **10** | 17 runs (9 fila + 4 ventana + 4 ablación), **todos** con params y métricas; export de 17 filas; capturas `compare_fila.png`, `compare_ventana.png`, `run_prod.png`; `--check` en 0. |
| 5 | App Streamlit (25 %) | **10** | 4 pestañas; RMSE/MAE/sesgo por unidad y curva **RUL real vs predicha** (`_tab_motor.py:463-490`); caso nuevo con decisión de reglas y **RUL p35 + L_inf + decisión en el mismo bloque** (`dashboard_ds02.py:1975-1997`); envío n8n. |
| 6 | Pregunta individual (15 %) | **10** | `guiones-15min.md` §2: pipeline, fuga, grano y test único, con anclas y errores que no debe decir. |

### 4.3 MIA — 4 criterios (100 %)

| # | Criterio (peso) | Nota | Evidencia y ancla 10 |
| --- | --- | ---: | --- |
| 1 | Negocio y objetivo (20 %) | **10** | `README.md:23-25`: AOG 10.000-15.000 USD/h, «jefe de taller», objetivo APTO/INSPECCIÓN/HANGAR y «evitar una parada al año paga el sistema»; `costes_reales_aeronauticos.md` §1. |
| 2 | Reglas (30 %) | **10** | `src/mia/reglas.py:246-262`: **8 reglas** (2 corrección + **6 decisión**), prioridad numérica, `porque` y **R1 seguridad con prioridad 10**; motor en dos pasadas (`motor.py`). |
| 3 | n8n (35 %) | **10** | 15 nodos, webhook con Header Auth, switch con **3 salidas**, cadena HANGAR → Postgres → Calendar → Gmail → **API propia**; `src/n8n.py` reintenta 5xx y no lanza; `/n8n-decision` con token e idempotencia; tests de contrato. |
| 4 | Pregunta individual (15 %) | **10** | `guiones-15min.md` §3: por qué reglas, 25/30, R2b, y lo que no debe confundir (`L_inf` ≠ probabilidad). |

### 4.4 Ponderación

```text
SAA = (10·5 + 10·10 + 10·5 + 10·5 + 10·5 + 10·30 + 10·20 + 10·10 + 10·5 + 10·5) / 100 = 10,00
PIA = (10·10 + 10·10 + 10·20 + 10·20 + 10·25 + 10·15) / 100                          = 10,00
MIA = (10·20 + 10·30 + 10·35 + 10·15) / 100                                          = 10,00
Techo = min(SAA, PIA, MIA)                                                           = 10,00
```

---

## 5. Hallazgos

Severidad: **C** crítico (bloquea entrega/verificación) · **A** alto (riesgo real de nota o de
pérdida de datos) · **M** medio (robustez/documentación) · **B** bajo (higiene).

### C1 — La suite no corre en este árbol y el fixture puede borrar la flota (C)

- **Síntoma:** `445 errores, 1 skip`; todos en el setup de `_flota_limpia`.
- **Causa:** `tests/conftest.py:38-41` copia y **borra** `app/registros_flota.json`, y después
  `shutil.move` de `app/registros_sesiones` a `app/registros_sesiones.hermes-respaldo`, que ya
  contiene una carpeta vacía `registros_sesiones` (residuo del 2026-11-07).
  `shutil.Error: Destination path ... already exists`.
- **Agravante:** si el setup falla después del `os.remove`, el registro real queda solo en el
  respaldo; el teardown no corre. En esta auditoría el `yield` no se alcanzó y el registro legacy
  quedó ausente, pero no había flota que perder: el fichero es un estado vacío por diseño y las
  sesiones siguieron intactas.
- **Alcance:** es un defecto del fixture, no del producto. En clon limpio no hay sesiones que
  mover y la suite pasa. Pero la verificación local queda bloqueada y el riesgo de pérdida es real.

### C2 — Un clon limpio no reproduce el dataset (C)

- `git ls-files data` = **0**; `data/processed` = **30 MB** (9 ficheros), `data/raw` = **2,3 GB**.
- `.gitignore:117` ignora `data/`; `data/raw/README.md` documenta la ruta canónica y las claves,
  pero **no una URL de descarga ni un checksum**.
- Consecuencia: PIA-3 se verificó en local, no desde el repositorio; `train_clasicos.py` y
  `train_mlp.py` fallan en un clon sin el HDF5. `resultados/` sí está versionado (39 ficheros).

### A1 — La corrección 13→17 runs está sin commitear (A)

- **18 `M`**, entre ellos `src/clase/README.md`, `openspec/config.yaml`, informes y presentación.
- HEAD sigue diciendo 13 en varios sitios; el árbol ya dice 17. Si se entrega HEAD, PIA-1/G
  pierden coherencia y la defensa puede citar dos cifras distintas.

### A2 — Contradicción documental (A)

- `src/clase/README.md:82`: «No se descarta ningún campo del dataset», mientras la tabla de
  `:73` lista `unit`, `RUL`, `split_origen` y `fase_vuelo` como quitados. Una de las dos frases sobra.

### A3 — CLI legacy roto (A)

- `scripts/predict.py:22` apunta a `models/v3_bundle.joblib`, que **no existe** (solo pesos en
  `models/legacy/`, sin bundle). El script muere antes de predecir. El manifiesto lo declara archivado.

### M1 — `models/mejor_modelo.joblib` sin escritor (M)

- Es una copia byte-idéntica del XGB de clase (SHA `5aab4d2a…`, verificado en la planificación);
  ningún script lo escribe. Si se reentrena el pipeline, el artefacto queda obsoleto en silencio.

### M2 — Skip permanente y guard muerto (M)

- `tests/test_mia_rules.py:181` se salta siempre por `_p1_oof_cache.npz` ausente; el instrumento
  versionado es `src/mia/instrumento_oof.npz`.
- `tests/test_audit_fixes.py:43-45` define el mismo guard y no lo usa. El «1 skipped» es real,
  pero el test nunca corre.

### M3 — n8n sin rama de descarte (M)

- El switch solo tiene APTO/INSPECCION/HANGAR; `SIN_DECISION` o un valor raro **no cae en ninguna
  rama** y se pierde en silencio.
- El JSON está `active:false` y con 2 × `REEMPLAZAR_CREDENCIAL`: no hay ejecución de punta a
  punta atribuible a la app.

### M4 — El cargador de secretos se traga el error (M)

- `app/streamlit_app.py:38-45` captura `OSError` y `TOMLDecodeError` con `pass`: un
  `secrets.toml` mal formado deja la app sin webhook y **sin aviso**. El cambio está sin commitear.

### M5 — El test de fila se lee dos veces (M)

- `README.md:187` dice «una sola vez y solo para el elegido», pero se publican test de **XGB
  (11,034)** y de **MLP-E2 (7,7211)**: una lectura por familia. Ninguna se usó para seleccionar,
  pero la frase es imprecisa.

### M6 — MLflow está backfilled, no trackeado en vivo (M)

- `backfill_mlflow.py` es «el único que escribe los 17 runs»; los runs se reconstruyen de los CSV.
  Cumple el ancla (todos con params/métricas + capturas), pero si preguntan «¿lo registrabas
  mientras entrenabas?», la respuesta honesta es no.

### B1 — SHAP: TreeExplainer vs PermutationExplainer (B)

- `README.md:29` dice «SHAP (TreeExplainer)» para la app; el campeón de clase E2 usa
  **PermutationExplainer** (`shap_clase_e2.py:124`). Más abajo se aclara, pero la primera mención confunde.

### B2 — El entrypoint es un wrapper (B)

- `app/streamlit_app.py` importa y ejecuta `dashboard_ds02.py`; cumple la rúbrica, pero conviene
  saberlo para no buscar la lógica en el fichero equivocado.

### Falso positivo descartado

Los **19 `meta.yaml`** no son 19 runs: son **17 runs + 2 metadatos de experimento**
(`mlruns/0` y `mlruns/456179934766753270`). El store coincide con el export.

---

## 6. Backlog de remate (qué hacer, riesgo y beneficio)

**Escala de beneficio (0-10):** 10 = desbloquea la verificación o evita pérdida de datos;
9 = hace el entregable reproducible/coherente desde clon o HEAD; 7-8 = cierra una brecha de
lectura estricta o un riesgo de defensa; 5-6 = calidad/deuda técnica; 3-4 = documentación;
0-2 = cosmético.

**Riesgo de implementación:** Bajo = solo tests/docs, sin tocar artefactos; Medio = toca
contratos, datos o requiere una decisión; Alto = depende de servicios/credenciales o de reentrenar.

### Prioridad 1 — desbloquear y asegurar la entrega

| ID | Tarea (qué hacer) | Qué arregla | Riesgo | Beneficio | Esfuerzo | Verificación |
| --- | --- | --- | --- | ---: | --- | --- |
| **T01** | Hacer `_flota_limpia` idempotente y exception-safe: limpiar respaldos obsoletos, usar `try/finally`, no borrar el registro hasta tener el respaldo verificado. | **C1**: 445 errores → suite ejecutable; elimina el riesgo de perder la flota. | **Bajo** (solo `tests/conftest.py`) | **10** | S (1-2 h) | `pytest tests -q -rs` → 0 errores; matar el proceso a mitad y comprobar que el registro sigue. |
| **T02** | Versionar `data/processed` (30 MB) + checksum, y documentar en `data/raw/README.md` la fuente y SHA del HDF5; opcional `scripts/build_dataset.py`. | **C2**: un clon puede ejecutar PIA-3 y los notebooks sin depender de un HDF5 invisible. | **Medio** (tamaño de repo y decisión de qué versionar) | **9** | M (media jornada) | Clon limpio → `pytest tests/test_clase_pipeline.py` y `python -m src.clase.train_mlp --help` sin `data/` manual. |
| **T03** | Revisar los 18 `M` y commitear la corrección 13→17 en un commit propio (`docs: alinea 17 runs`), dejando el informe aparte; no arrastrar cambios ajenos. | **A1**: HEAD y árbol dejan de contradecirse. | **Bajo** (revisar `git diff` antes) | **9** | S | `git status` limpio salvo el informe; `grep -rn "13 runs"` → 0. |
| **T06** | Añadir rama de descarte al switch n8n para decisiones desconocidas y un test que la cubra. La evidencia de las 29 ejecuciones ya está en `guiones-15min.md`; si se quiere artefacto, exportar historial, no re-ejecutar. | **M3**: protege llamadas externas; **la app nunca envía `SIN_DECISION`** (`ui_n8n.debe_notificar` lo filtra). | **Bajo/Medio** (JSON de integración) | **6** | S | JSON con 4ª salida y conexión; test del switch; `debe_notificar('SIN_DECISION') is False` intacto. |
| **T12** | Añadir una tabla de coste del error: RMSE 4,338 ciclos → coste esperado de FN/FP con AOG 10-15k USD/h e inspección, con fuentes y supuestos. | Brecha de **SAA-8/MIA-1** en lectura estricta (hoy la mejora es cualitativa). | **Medio** (credibilidad analítica) | **8** | M | Tabla en README/defensa con fórmula, rangos y `costes_reales_aeronauticos.md` citado. |

### Prioridad 2 — robustez y coherencia

| ID | Tarea (qué hacer) | Qué arregla | Riesgo | Beneficio | Esfuerzo | Verificación |
| --- | --- | --- | --- | ---: | --- | --- |
| **T04** | Corregir `src/clase/README.md:82`: «no se descarta ningún campo **físico**; se excluyen del predictor `unit`, `RUL` y `split_origen`, y `fase_vuelo` del bundle». | **A2**: elimina la contradicción con la tabla de `:73`. | **Bajo** | **7** | XS | Leer `:73-84` y comprobar que tabla y frase dicen lo mismo. |
| **T05** | Copiar **byte a byte** (`shutil.copy2`) `models/mejor_modelo_clase.joblib` → `models/mejor_modelo.joblib` desde un script/flag que **no reentrene**, y actualizar `models/README.md`. **No** tocar `models/ds02_manifest.json`: ya contiene `clase_xgb_sha256`. | **M1**: procedencia del alias sin re-serializar ni invalidar el sello del bundle. | **Bajo** (copia) / **Medio** si se reentrena | **6** | S | `sha256` idéntico al canónico; `test_mejor_modelo_alias_paridad`; `seal_ok` sigue `True`. |
| **T09** | Documentar la procedencia real: 17 runs `fuente=historico` + instrumentación live en `src/ds02_rul/mlflow_live.py` y NB01-07, con **0 runs live** hasta re-ejecutar un notebook. **No** añadir logging a los scripts de entrenamiento. | **M6**: corrige la premisa; evita reentrenar o duplicar runs. | **Bajo** (solo doc) | **6** | XS | README dice «17 históricos + live instrumentado, 0 live»; `grep -rl live_notebook mlruns` = 0; `models/` intacto. |
| **T13** | Ampliar CI: `compileall`, `freeze_rules`, `freeze_oof --check`, `backfill --check` y `pytest`; incluir `fix/*` o PR. | Verificación continua; hoy CI solo corre pytest en `main`/`clase-*`. | **Bajo** | **7** | S | Workflow con 5 pasos en verde; PR de la rama dispara. |
| **T07** | Sustituir el `pass` de `streamlit_app.py:38-45` por `logging.warning` + flag de entorno; el banner visible va aparte en `dashboard_ds02.py`, después de `set_page_config` (línea 510). | **M4**: un secreto mal formado deja de fallar en silencio, sin romper el orden de Streamlit. | **Bajo** (log) / **Medio** (banner en dashboard) | **5** | XS | TOML corrupto → warning; `set_page_config` sigue siendo el primer comando; sin `st.warning` en el entrypoint. |
| **T08** | Ajustar la frase de `README.md:187` a «una lectura de test por familia (XGB y E2), ninguna usada para seleccionar» o retirar el test de XGB de la tabla. | **M5**: exactitud metodológica. | **Bajo** | **6** | XS | Texto y `comparativa.csv` coinciden. |
| **T11** | Re-apuntar `needs_oof` a `src/mia/instrumento_oof.npz` (adaptar claves) y borrar el guard muerto de `test_audit_fixes.py`. | **M2**: 0 skips; el test vuelve a correr. | **Bajo/Medio** (adaptar test) | **6** | S | `pytest -q -rs` → 0 skips y 445+ passed. |

### Prioridad 3 — deuda e higiene

| ID | Tarea (qué hacer) | Qué arregla | Riesgo | Beneficio | Esfuerzo | Verificación |
| --- | --- | --- | --- | ---: | --- | --- |
| **T10** | Retirar `scripts/predict.py` o lanzar un error explícito: «CLI FD001 fuera de servicio; usa `predict_ds02.py`». | **A3**: deja de apuntar a un bundle inexistente. | **Bajo** | **5** | XS | `python scripts/predict.py` → mensaje accionable, sin traza críptica. |
| **T14** | Unificar la mención de SHAP (Tree vs Permutation), aclarar que `streamlit_app.py` es wrapper y añadir `*.hermes-respaldo` a `.gitignore`. | **B1/B2** + residuos de tests. | **Bajo** | **3** | XS | `README.md:29` coherente; `git check-ignore app/registros_flota.json.hermes-respaldo`. |

### 6.1 Radio de impacto (revisión pre-aprobación)

> **Para decidir qué autorizar:** `docs/informes/auditoria-2026-11-10-alcance-y-autorizacion.md`.

**Definición:** *modelo* = artefacto bajo `models/`; *código crítico* = entrypoint de la app,
flujo n8n, núcleo de inferencia (`src/ds02_rul/`), reglas (`src/mia/`) o dashboard
(`app/dashboard_ds02.py`).

| Tarea | ¿Notebooks? | ¿Modelo? | ¿Código crítico? | Toca de verdad | Aprobación |
| --- | --- | --- | --- | --- | --- |
| T01 | No | No | No | `tests/conftest.py` | Aprobar. |
| T02 | No (puede ejecutar, no editar) | No | No | `data/`, `.gitignore`, `data/raw/README.md` | Aprobar opción A (versionar `processed`); no crear `build_dataset.py` aún. |
| T03 | No | No | No, pero índice | commit selectivo | Aprobar con `git add` por ruta; nunca `-A`. |
| T04 | No | No | No | `src/clase/README.md` | Aprobar. |
| T05 | No | **Sí: alias no servido** | Sí si se elige writer (`src/clase/train_clasicos.py`) | `models/mejor_modelo.joblib`, `models/README.md` | Aprobar solo copia byte a byte; no manifest, no reentrenar. |
| T06 | No | No | **Sí: `n8n/flujo.json`** | workflow JSON | Aprobar con validación; no cubre el camino de la app. |
| T07 | No | No | **Sí: `app/streamlit_app.py`** | entrypoint | Aprobar solo logging; banner = tarea aparte en dashboard. |
| T08 | No | No | No | `README.md` | Aprobar. |
| T09 | No | No | No (doc-only) | README + guion | Aprobar doc-only; no tocar scripts de entrenamiento. |
| T10 | No | No | No | `scripts/predict.py` | Aprobar. |
| T11 | No | No | No | tests | Aprobar. |
| T12 | No | No | No | docs | Aprobar. |
| T13 | No | No | No | `.github/workflows/ci.yml` | Aprobar tras T01/T02. |
| T14 | No | No | No | `README.md`, `.gitignore` | Aprobar. |

**Veredicto de alcance:** ninguna tarea edita notebooks. Solo **T05** toca un modelo, y es el
**alias de clase** (`mejor_modelo.joblib`), no el bundle servido (`ensemble.joblib`,
`bilstm_ds02.keras`, `scaler.joblib`, `ds02_manifest.json`). Código crítico: **T06** (flujo n8n),
**T07** (entrypoint) y, solo si se elige la variante de código, **T05/T09** (scripts de
entrenamiento). Ninguna toca `src/ds02_rul/`, `src/mia/`, `app/dashboard_ds02.py`,
`app/ui_modulos/` ni `app/api.py`.

**Por qué se ajustaron cuatro tareas:**

- **T05:** `models/ds02_manifest.json:199` ya contiene `clase_xgb_sha256`
  (`5aab4d2a…`), el mismo SHA del alias. Volver a serializar con `joblib.dump` puede cambiar los
  bytes y obligaría a reescribir el manifiesto, invalidando `seal_ok` y `app/cache/cache_manifest.json`.
  La copia con `shutil.copy2` conserva bytes, SHA y paridad de predicciones
  (`test_mejor_modelo_alias_paridad`).
- **T06:** `app/ui_n8n.py:52` (`debe_notificar`) excluye `SIN_DECISION`; la app nunca lo envía.
  El fallback protege llamadas externas o malformadas, no el camino de la app. Además, la
  evidencia de **29 ejecuciones** (25 success / 4 error, 2026-11-07) ya está documentada en
  `docs/defensa/guiones-15min.md:6` y `src/clase/README.md:19`.
- **T07:** `dashboard_ds02.py:510` llama a `st.set_page_config` y debe ser el primer comando de
  Streamlit; `streamlit_app.py` ni siquiera importa `st`. Un `st.warning` en el entrypoint rompería
  el arranque. El log y el flag son seguros; el banner exige tocar el dashboard en una tarea aparte.
- **T09:** el tracking live **ya existe**: `src/ds02_rul/mlflow_live.py`, cabecera y celda live en
  NB01-07, y `test_notebooks_instrument_mlflow_live` lo exige. Lo que no hay es **ningún run live**
  (`grep -rl live_notebook mlruns` = 0); los 17 canónicos son `fuente=historico`. Añadir logging a
  los scripts de entrenamiento crearía runs mal etiquetados y podría reescribir `models/`.

### Orden recomendado

1. **Hoy (2-3 h):** T01 → T03 → T04. Suite ejecutable, HEAD coherente y contradicción fuera.
2. **Antes de defender (media jornada):** T02, T06, T12. Clon reproducible, n8n sin descarte
   silencioso y coste del error cuantificado.
3. **Cuando se toque esa zona:** T05, T07, T08, T09, T11, T13.
4. **Higiene:** T10, T14.

### Lo que NO hay que hacer

- No reentrenar ni recalibrar para «subir» una nota: los 4,338 y la banda ya están congelados y
  verificados.
- No volver a leer el test para elegir modelo: rompería SAA-8/9 y la defensa.
- No activar el flujo n8n en el repositorio con credenciales reales: la evidencia va aparte.
- No tocar `models/ensemble.joblib`, `bilstm_ds02.keras` ni `scaler.joblib` sin actualizar
  manifiesto y sello de caché a la vez.

---

## 7. Límites de esta auditoría

1. **No se levantó** Streamlit ni uvicorn: PIA-5 y la API se puntúan por código, tests y contratos.
2. **No hay ejecución n8n** atribuible: MIA-3 se puntúa por estructura, conexiones, endpoint y tests.
3. **La suite no corre** en este árbol (C1); los gates que sí pasan son `compileall`, reglas, OOF y MLflow.
4. **SAA-10, PIA-6 y MIA-4** dependen de la persona en la defensa; aquí se puntúa el guion.
5. El **HDF5 crudo** no está en git; el análisis del dato se hizo sobre `data/processed` local.
6. Las notas son la aplicación de la rúbrica v5, no una corrección oficial.

---

## 8. Anexo — salidas literales

```text
$ git rev-parse HEAD
10761e7b960f2404adb8cfea93b82072ec4cb213
$ git status --porcelain --untracked-files=all | wc -l
22   # F6: 19 M + 3 ?? (incluye plan-cierre-rubrica.md, ajeno)
$ git ls-files | wc -l
1171
$ python -m compileall -q src app scripts tests ; echo $?
0
$ python scripts/freeze_rules_evidence.py ; echo $?
rules=0
$ python scripts/freeze_oof_instrument.py --check ; echo $?
oof=0
$ python scripts/backfill_mlflow.py --check ; echo $?
OK: 17 runs (9 fila + 4 ventana + 4 ablacion), export y store coinciden, sin artefactos.
mlflow=0
$ python -m pytest tests -q -rs -p no:cacheprovider ; echo $?
SKIPPED [1] tests\test_mia_rules.py:181: _p1_oof_cache.npz missing
1 skipped, 445 errors in 38.75s
pytest=1
```

```text
$ python -c "import json,hashlib; ..."
seal_ok True 6089457c772f8cb947ed58172703043a2c6b149f2bdde0ca71599a19ec83ea40
$ sha256sum models/ensemble.joblib
d6c701429eed8623a9d900d922aca1922427d08ff8b4ec00604b8116c1a952dd
```

```text
$ find app/registros_sesiones.hermes-respaldo -maxdepth 1 -type d
app/registros_sesiones.hermes-respaldo
app/registros_sesiones.hermes-respaldo/registros_sesiones   # vacía, causa del fallo
$ ls -la app/registros_flota.json
ls: cannot access 'app/registros_flota.json': No such file or directory   # legacy ausente (la app lo crea vacío)
$ ls -la app/registros_flota.json.hermes-respaldo
-rw-r--r-- 1 mikel 197609 49 ... app/registros_flota.json.hermes-respaldo   # {"twins":{},"hangar":{},"altas":{}}
```

---

## 9. Firma G5

- **F0:** 20 rutas (18 `M` + 2 `??`: plan y respaldo vacío), con la corrección 13→17 en curso.
- **F6:** 22 rutas (19 `M` + 3 `??`). Además del informe, apareció un `M` externo en
  `docs/pendiente/plan-cierre-rubrica.md` durante la sesión; no lo tocó esta auditoría. Nada de
  código, artefactos, notebooks ni datos fue modificado por la auditoría.
- **Efecto colateral contenido:** `app/registros_flota.json` sigue ausente (estado legacy vacío);
  `app/registros_sesiones/` conserva sus 2 ficheros vacíos y el respaldo del fixture es de 49 B.
  No se perdió ningún dato de flota.
