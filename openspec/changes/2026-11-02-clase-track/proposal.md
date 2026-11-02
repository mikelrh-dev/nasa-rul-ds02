# Proposal: Track de clase DS02 (SAA+PIA+MIA sin MLflow/n8n)

**Change:** `2026-11-02-clase-track`
**Status:** Proposed
**Capability:** `clase-track` (new) — no modifica `rul-prediction-ds02`, `ds02-dss-ui`, `ds02-live-evaluation`, `ds02-rules-engine`
**Rama:** `clase-experimental` (trabajo aquí; `master` y `backup-2026-11-02` intactos; copia en disco externo solo backup, no se edita allí)
**Fecha:** 2026-11-02

---

## Why

El pipeline DS02 congelado (híbrido BiLSTM + LightGBM + stacking, RMSE 4.251, `models/` + `app/cache/`) está por encima del nivel técnico del reto, pero **suspende el formato de clase**: DS02 real trae 0% nulos y 0 categóricas (requisito bloqueante), no existen los 5 modelos clásicos + GridSearchCV, ni MLP con 3 experimentos, ni EDA con 5 gráficos matplotlib, ni pipeline sklearn compartido, ni README de 6 apartados. La rúbrica SAA 6+7 (50% del peso SAA) está hoy en 0.

Se crea un **track de clase separado en `clase/`** que reutiliza `X_tab` (93 features) sin reentrenar el híbrido. El híbrido queda citado como "extra no visto en clase" (criterio SAA 6, 10 pts) y como modelo en producción (README §6). MLflow (PIA 4) y n8n (MIA 3, PIA 5-parcial) quedan **explícitamente fuera** de este change y se harán después.

## Scope

**In scope (4 fases, sin MLflow/n8n)**

0. Congelar y ramificar: verificar `clase-experimental` limpio, crear esqueleto `clase/`, `data/`, `notebooks/01|02|03`, `resultados/`, `n8n/flujo.json` (placeholder), `src/reglas.py` (re-export) + `src/n8n.py` (stub).
1. Dataset clase + EDA: inyección MAR ~2% SOLO en T30 cuando alt>27_000 y Mach>0.68 (crucero alto DS02; el 30k/0.8 teórico no existe: Mach máx 0.74), imputación ffill causal por unidad + mediana de train, categórica `fase_vuelo` desde `alt`/`Mach`, split por `unit` (no aleatorio), `notebooks/01_eda.ipynb` con tabla campos + 5 gráficos matplotlib comentados. Se guarda `train_con_nulos.parquet` (con MAR) + `train/test.parquet` imputados; test de robustez AC 20-170 (degradación <5% RMSE, R1 si >3 ciclos seguidos) en Fase 2.
2. Pipeline + modelos: `ColumnTransformer(StandardScaler + OneHot(fase_vuelo))` compartido, 5 clásicos (Ridge, KNN, RF, XGB, SVR) + GridSearchCV con `GroupKFold(groups=unit)`, MLP base + 3 experimentos con hipótesis, tabla comparativa pandas + tiempos, SHAP/permutación sobre mejor clásico, gráfico real-vs-predicho + significado empresa.
3. README + app clase: README 6 apartados estilo `README_ejemplo_CV.md` (frase+resultado, captura app arriba, esquema Mermaid modelo→reglas→(n8n pendiente)→acción, tabla campos, tabla comparativa, €/empresa), app clase que reutiliza `validate_table`/`mia/motor` (métricas test + caso nuevo + decisión, controla vacíos/erróneos).

**Out of scope**

- `models/`, `src/ds02_rul/`, `mia/` (lógica), `app/cache/`, `02_DS02_ensemble_RUL.ipynb`, `archive/` — solo lectura. Sin reentrenar, sin refit, sin recalibrar banda, sin tocar reglas.
- MLflow: sin `mlruns/`, sin loguear, sin capturas. La tabla comparativa es `resultados/comparativa.csv` (pandas).
- n8n: sin webhook real ni acciones. `n8n/flujo.json` placeholder + `src/n8n.py` stub que NO se llama desde la app en este change.
- SMOTE: no aplica (regresión sin clases; se declara explícitamente).
- `master`, `backup-*`, disco externo: no se tocan.

## Capability

Nueva capacidad `clase-track` (evidencia de clase). No añade ni modifica las 4 capacidades desplegadas. El híbrido se cita, no se versiona de nuevo.

## What changes (resumen por fase)

### Fase 0 — Esqueleto (1 commit)
- `clase/` (+ `dataset_clase.py`, `pipeline_clase.py`, `train_clasicos.py`, `train_mlp.py` en Fase 2), `data/raw|processed/` (+ `README` con fingerprint, HDF5 fuera de git), `notebooks/01_eda.ipynb|02_modelos_A.ipynb|03_modelos_B.ipynb`, `resultados/`, `models/mejor_modelo_clase.joblib` (al final Fase 2), `n8n/flujo.json` placeholder, `src/reglas.py` re-export de `mia/reglas.py`, `src/n8n.py` stub documentado como pendiente.

### Fase 1 — Dataset + EDA
- Inyección MCAR auditada (sensores declarados, tasa, seed, mask guardada), ffill causal + mediana train, `fase_vuelo` con umbrales publicados, split por unidad, 5-6 figuras `resultados/eda_*.png` con "qué veo / conclusión".

### Fase 2 — Pipeline + modelos
- Un `Pipeline(pre, reg)` por modelo, grids mínimos declarados, `GroupKFold(3, groups=unit)`, tiempos registrados, `comparativa.csv`, MLP base + E1 capacidad / E2 reg-lr / E3 batch-early con hipótesis, SHAP (o permutación si SHAP no corre en 200 filas), real-vs-predicho.

### Fase 3 — README + app
- README reescrito (6 apartados, captura arriba, Mermaid, tablas, €, limitaciones, cómo ejecutar clase), app clase fina que importa validadores y motor existentes. Sin `POST` a n8n.

## Artifacts that stay byte-compatible

- `models/*`, `app/cache/*`, `src/ds02_rul/*`, `mia/*`, `02_DS02_ensemble_RUL.ipynb`, `archive/*` — `git status --porcelain` sobre ellos retorna vacío al cerrar cada fase.
- `tests/` existentes siguen verdes; los nuevos tests de clase solo leen `data/processed/` y `resultados/`.

## Rollback plan

Un commit por fase sobre `clase-experimental`. Revertir Fase 2 borra `clase/*.py` + notebooks 02/03 sin tocar Fase 1. Revertir Fase 0 borra el esqueleto vacío. Ningún rollback toca `models/` ni `app/cache/` porque nunca se escriben.

## Risks

1. Profesor no acepta nulos simulados (mayor). Mitigación: MAR con patrón físico (altitud) + auditoría (tasa global/en elegibles, 100% en crucero alto, rachas, >3 seguidos para R1) + plan B (imposibles reales como "nulo funcional") + pregunta en tutoría con EDA delante.
2. `fase_vuelo` vista como fuga (deriva de inputs que el modelo ya ve). Mitigación: solo de `alt`/`Mach`, umbrales publicados, ablación con/sin.
3. ffill con fuga si se calcula mal. Mitigación: `groupby(unit)` tras ordenar por ciclo, medianas solo de train, test explícito.
4. SVM/Grid eternos. Mitigación: grids mínimos, `n_jobs=-1`, submuestra estratificada por unidad declarada.
5. Confusión "¿cuál es el modelo elegido?". Mitigación: frase canónica README §6 (híbrido en producción, clásicos comparativa de clase).
6. SHAP caro. Mitigación: muestra 200 filas + fallback a permutación, ambos valen para SAA 9-técnico.

## Open questions

1. ¿Tasa 3% fija o barrido 2-4%? Propuesta: 3% fija (reproducible), barrido como experimento opcional.
2. ¿`fase_vuelo` entra al pipeline de todos los modelos? Propuesta: sí, vía `OneHot(handle_unknown=ignore)`, con ablación.
3. ¿App clase nueva o pestaña en `dashboard_ds02.py`? Propuesta: `clase/app_clase.py` fina que reutiliza validadores, sin duplicar DSS.

## Ampliación NB04/NB05 — bundle C (2026-11-02, autorizada A+B, C pendiente)

Con tiempo disponible, se reentrena el pipeline honesto sobre la base adaptada (MAR T30 + ffill; medianas recalculadas SOLO con fit-units `[2,5,10,18,20]`, holdout 16 y test `[11,14,15]` intactos). `fase_vuelo` queda FUERA del contrato de 93 (sigue en el track de clase). Dos tablas separadas: SAA (grano fila: 5 + MLP) y producción (grano ventana: B vs C, mismas 6.196 ventanas). Bundle C versionado en `clase/models/` (nunca en `models/`).

NB04 (LGBM adaptada, prototipo barato) → valida el plumbing honesto. NB05 (ensemble completo, seed 42 primero; 7/123 solo si queda cerca) → bundle C + banda propia. Puerta de adopción pre-registrada: `RMSE_C ≤ 4.25 − spread` Y `NASA_C ≤ NASA_B`; si no se cumple, C queda como experimento y B sigue. El re-freeze (caché + banda + reglas + ADR, 2–3 días) requiere otra autorización explícita.
