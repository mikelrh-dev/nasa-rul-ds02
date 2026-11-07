# Tasks: bloques BL-01…BL-09 de la auditoría

**Change:** `2026-11-05-bloques-auditoria`
**Estado:** aplicado y verificado

Cada tarea cierra con su acceptance. Comandos desde la raíz del repo.

## Review workload guard

```
Decision needed before apply: No (usuario autorizó los 9 bloques, sin MLflow/n8n)
Chained PRs recommended: No (un change, cambios por bloque)
400-line budget risk: Medium (BL-01 y BL-02 son los mayores; van en commits distintos)
```

---

### [x] BL-01 · Narrativa única: C es el campeón

README raíz, `src/clase/README.md`, `docs/chuleta-defensa.md` y
`docs/defensa/guiones-15min.md` dicen lo mismo: E2 es el campeón del track de clase
(7,72) y C es el modelo desplegado (4,338, macro-RMSE 5,0153). Se añade la pregunta
«¿Y el modelo que se despliega?» al guion y macro-RMSE al README español.

Acceptance: `grep -rn "XGBoost (elegido)" src/clase/README.md` vacío; los cuatro
documentos nombran C como producción.

### [x] BL-02 · Banda conformal única

`models/ds02_manifest.json` gana `conformal_decision` (14 915 filas, unidades 2/5/10/18/20, unidad 16 excluida y por qué), donde se declara que es la banda opcional R6 y solo rige con `aplicar_reglas`. El bloque `conformal` sigue declarando la banda interna del artefacto (17 450) sin falsearla. `_tab_auditoria` muestra las dos, etiquetadas.

Acceptance: `test_la_banda_de_decision_es_la_del_json_de_calibracion` verde;
`python -c "from src.mia.reglas import cargar_calibracion"` sigue en 14 915.

### [x] BL-03 · Evidencia multisemilla completa

`resultados/comparativa_c_multisemilla.csv` con 3 filas (42 del manifiesto, 7 y 123
medidas en `bundle_c_multiseed.csv`). `evaluar_c_multisemilla --desde-csv`
reconstruye la tabla sin entrenar; sin el flag sigue entrenando como antes.

Cifra publicada: **4,368 ± 0,053** RMSE · **2355,2 ± 24,6** NASA (antes 4,322 ± 0,064).

Acceptance: `pytest tests/test_clase_c_multisemilla.py -q` ya no salta: 4 tests verdes.

### [x] BL-04 · Seis reglas de decisión

`src/mia/reglas.py` añade `R10_DATOS_INSUFICIENTES` (prioridad 9) y
`R11_UMBRALES_INCOHERENTES` (8). Solo actúan donde antes el motor caía en
`SIN_DECISION` por defecto; no tocan ninguna decisión de R1/R9/R8/R7.

Acceptance: `len(REGLAS_DECISION) == 6`; tests de ficha incompleta y umbrales
invertidos verdes; `test_la_seguridad_gana_a_los_umbrales` sigue verde.

### [x] BL-05 · Evidencia visual versionada (parcial)

Nueve figuras reales copiadas a `docs/assets/` y enlazadas desde README raíz y
`src/clase/README.md` (sus antiguas rutas `resultados/` o `../resultados/` no se versionan
y algunas estaban rotas). La captura obsoleta del dashboard se sustituye por figuras
medidas y por una nota que explica cómo regenerar la captura.

Pendiente declarado: **captura en vivo** — aquí no hay `playwright` instalado para
capturarla de forma automática.

Acceptance: `docs/assets/` contiene las figuras enlazadas; `grep -RIn "resultados/app_clase.png" README.md src/clase/README.md` vacío.

### [x] BL-06 · SHAP del bundle C en primera línea

`src/clase/README.md` documenta `src/ds02_rul/shap_c.py` + NB07 (3 ramas,
aditividad ~1e-6). `app/ui_shap.py` deja de decir «model B»: sirve el bundle C.

Acceptance: docstring correcto; ningún documento de defensa presenta el SHAP de XGB
como el del modelo desplegado sin aclararlo.

### [x] BL-07 · Contrato de artefacto

`models/ds02_manifest.json`: `python: "3.12.10"` y `historical_reference` con el
bundle B archivado (4,251; multiseed 4,340 ± 0,101, semillas [42, 7, 123], 6 196 ventanas,
procedencia `archive/models_b/ds02_manifest.json`) más la nota de comparabilidad del NASA.

Acceptance: `test_el_manifiesto_declara_la_referencia_historica` verde.

### [x] BL-08 · Coherencia de la suite

`tests/test_clase_rubrica.py` gana `test_el_campeon_desplegado_es_el_bundle_c`: ata
`code_version`, seed, RMSE 4,338 y lo contrasta con el test de E2. Docstring del SVR
corregido (5k uniforme, no estratificada). La tabla final imprime el criterio usado
por grano.

Acceptance: `pytest tests/test_clase_rubrica.py -q` verde en el venv.

### [x] BL-09 · Docstrings y gate (parcial)

Docstrings añadidas hasta llegar a **0 públicas sin docstring en 264** (`app`,
`src/clase`, `src/mia` y `src/ds02_rul`). El gate se deja **fail-closed** documentado:
sin `_p1_oof_cache.npz` sale con 3, que es su contrato (RULES-06), no un fallo
silencioso.

Pendiente declarado: el caché OOF no se puede generar aquí (falta el HDF5 de DS02
y es un cálculo largo); las 6 pruebas que lo necesitan quedan saltadas por diseño.

Acceptance: `python scripts/freeze_rules_evidence.py` sigue saliendo con 3 y el
mensaje nombra el instrumento que falta y la política.

---

## Verificación

```
.venv/Scripts/python.exe -m compileall -q src app scripts tests
.venv/Scripts/python.exe -m pytest tests -q -rs -p no:cacheprovider
```

Deltas de especificación: `specs/ds02-rules-engine/spec.md` (R10/R11 y R6 opcional) y
`specs/rul-prediction-ds02/spec.md` (dos bandas e historia B).

Resultado final: **315 passed, 6 skipped en 136,17 s (exit 0)**. Los 6 skips son
los 6 tests que exigen `_p1_oof_cache.npz`, ausente por diseño hasta generar el
instrumento OOF.
