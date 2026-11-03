# Plan: reestructurar notebooks de track_clase/ para explicar el modelo completo

## Estado: ✅ COMPLETADO (2026-11-03)

Reestructuración ejecutada con **6 notebooks** (01-06) en lugar de los 5 propuestos originalmente. Discrepancia documentada en `docs/NOTEBOOKS.md`.

- Notebooks creados: `01_eda_y_contexto`, `02_modelos_clasicos_y_mlp`, `03_feature_engineering_secuencial`, `04_arquitectura_bilstm_oof`, `05_meta_ensemble_y_conformal`, `06_evaluacion_produccion_comparativa`.
- Todos ejecutados con `nbconvert --execute --inplace`: 0 errores.
- Originales movidos a `notebooks/backup/`.
- `ds02_ensemble/` y `models/` no tocados.
- Verificación: `docs/NOTEBOOKS.md`.

---

## Instrucción para el agente que ejecute este plan

**ANTES de implementar, explora el repo y saca tus propias conclusiones.** Lee los notebooks de `notebooks/ds02_ensemble/` (01-03) y los de `notebooks/` (01-05). Analiza qué explica cada uno, qué falta, y si la reestructuración propuesta tiene sentido. Si tus conclusiones coinciden con las de este documento, implementa. Si no, documenta tus discrepancias y propón una alternativa.

**NO marques la carpeta `notebooks/ds02_ensemble/` como legacy.** Se mantiene intacta, sin modificaciones ni etiquetas.

## Problema

Los notebooks de `notebooks/ds02_ensemble/` (01-03) documentan el proceso completo del modelo (Ridge, BiLSTM, LightGBM, meta-learner, beta, EMA, conformal, multisemilla, diagnósticos). Los notebooks de `notebooks/` (01-05) de track_clase/ NO lo hacen: solo 05 cubre los 8 temas del pipeline, los demás son EDA, clásicos, MLP y LGBM tabular.

El objetivo es que la secuencia de notebooks (01→05) cuente la historia completa del modelo, como los ds02_ensemble/ (01→03) lo hacían, pero integrando la parte de clase (nulos, fase_vuelo, clásicos, MLP, LGBM adaptada, ensemble adaptado, SHAP, robustez).

## Por qué lo hacemos

1. **Un solo conjunto de notebooks para la defensa:** el tribunal no debería tener que abrir dos carpetas. Una secuencia 01→05 que explique todo.
2. **No duplicar código:** tomar contenido de ds02_ensemble/ y adaptarlo a track_clase/, no copiar/pegar sin más.
3. **Mantener la parte de clase:** nulos, fase_vuelo, clásicos, MLP, LGBM adaptada, ensemble adaptado, SHAP, robustez. Esto es lo que diferencia el track de clase del legacy.
4. **No tocar ds02_ensemble/:** se mantiene intacto como referencia.

## Propuesta de reestructuración

### Secuencia unificada

| Notebook | Contenido (historia incremental) | Fuente (ds02_ensemble/) | Lo que ya tiene (track_clase/) |
|---|---|---|---|
| **01_eda** | Datos + EDA + nulos + fase_vuelo + **residualización Ridge** + ventanas + feature blocks | 01 (datos + preprocesado) | EDA completo, nulos, fase_vuelo, 5 figuras |
| **02_modelos_A** | **LightGBM + BiLSTM + baseline** + 5 clásicos + GridSearchCV | 01 (LGBM + BiLSTM) | 5 clásicos + GridSearchCV + tabla comparativa |
| **03_modelos_B** | **Ablación cyc_norm + meta-learner + beta + EMA** + MLP + SHAP | 02 (ablación + meta + beta + EMA) | MLP base+3 exp + importancia + SHAP |
| **04_lgbm_adaptada** | **Conformal + multisemilla + diagnósticos** + LGBM con nulos + glosario | 03 (conformal + multisemilla + diagnósticos) | LGBM con nulos + glosario + cuantil |
| **05_ensemble_adaptado** | Ensemble con nulos + robustez 3 vías + veredicto D11 + **ecuaciones** | Ya está (9/10) | Los 8 temas + veredicto + robustez |

### Mejoras transversales (todos los notebooks)

1. **Kernelspec:** añadir metadata de kernel para que "Run All" funcione sin preguntar.
2. **Rutas relativas:** verificar que `../` funciona desde `notebooks/`.
3. **Limpiar warnings de TF** en 05 (filtrar `tf.get_logger().setLevel('ERROR')`).
4. **Mover celda markdown** que está antes del título en 05.
5. **Añadir ecuaciones** de residualización, meta-learner, beta, EMA, conformal, cyc_norm (Markdown).

### Ecuaciones que faltan (añadir en los notebooks correspondientes)

| Ecuación | Notebook | Fuente |
|---|---|---|
| Residualización: `sensor − Ridge(poly(W, deg=2))` con Ridge alpha=1.0 | 01_eda | src/ds02_rul/residualizer.py |
| LightGBM cuantil 0.35 (mediana rechazada) | 02_modelos_A | src/ds02_rul/pipeline.py (LGB_PARAMS) |
| BiLSTM triple pooling (último/media/máximo) | 02_modelos_A | src/ds02_rul/model.py |
| Ablación cyc_norm (4 variantes) | 03_modelos_B | ds02_ensemble/02 |
| Meta-learner: `Z = [p_lstm, p_lgb]`, RidgeCV + LGBM, blend 50/50 | 03_modelos_B | src/ds02_rul/stacking.py |
| Beta: grid 0-1 (21 puntos), mediana de 3 folds, criterio RMSE+NASA | 03_modelos_B | ds02_ensemble/02 |
| EMA causal: `alpha = 2/(span+1)`, span=5, solo pasado | 03_modelos_B | src/ds02_rul/smoothing.py |
| Conformal: split 90% asimétrico, bins por tramo RUL, clip de lower al punto | 04_lgbm_adaptada | ds02_ensemble/02 |
| Multisemilla: media ± desvío, regla de empate | 04_lgbm_adaptada | ds02_ensemble/03 |
| Diagnósticos: real vs predicho, residuos, por tramo, por motor | 04_lgbm_adaptada | ds02_ensemble/03 |

## Cobertura verificada (legacy → propuesta)

### Legacy 01 (datos + bases) → cubierto en 01_eda + 02_modelos_A

| Legacy 01 | Cubierto? |
|---|---|
| Carga HDF5, reparto por motor | ✅ 01_eda |
| Residualización Ridge (14 ridges, base polinómica) | ✅ 01_eda (añadir sección) |
| Ventanas (dev 17.450×50×19, test 6.196×50×19) | ✅ 01_eda |
| EDA (correlación, histograma RUL) | ✅ 01_eda |
| LightGBM cuantílico 0.35 + baseline + importancia | ✅ 02_modelos_A (añadir sección) |
| BiLSTM triple pooling (154.253 params) entrenado | ✅ 02_modelos_A (añadir sección) |
| Puente de estado (guarda artifacts/) | ✅ (simplificado, integrado en mismo notebook) |

### Legacy 02 (decisión + ablación + conformal) → cubierto en 03_modelos_B + 04_lgbm_adaptada

| Legacy 02 | Cubierto? |
|---|---|
| Ablación cyc_norm (4 variantes) | ✅ 03_modelos_B (añadir sección) |
| OOF agrupado por motor (3 folds) para beta | ✅ 03_modelos_B (añadir sección) |
| Protocolo legado como diagnóstico (0.725x) | ✅ 03_modelos_B (añadir como nota) |
| Meta-aprendices (Ridge/LightGBM) sobre holdout 16 | ✅ 03_modelos_B (añadir sección) |
| Ensamble híbrido + EMA5 | ✅ 03_modelos_B (añadir sección) |
| Tabla titular, extras EMA3/5/10, macro-RMSE | ✅ 03_modelos_B (añadir sección) |
| Conformal split 90% asimétrico por tramo | ✅ 04_lgbm_adaptada (añadir sección) |
| 3 variantes de banda + cobertura por motor | ✅ 04_lgbm_adaptada (añadir sección) |

### Legacy 03 (evidencia + multisemilla) → cubierto en 04_lgbm_adaptada + 05_ensemble_adaptado

| Legacy 03 | Cubierto? |
|---|---|
| Semillas 42/7/123, media ± desvío | ✅ 05_ensemble_adaptado (ya tiene multiseed) |
| 4 vistas amigables (trayectoria, embudo, cobertura, estabilidad) | ✅ 04_lgbm_adaptada (añadir diagnósticos) |
| Comparativa de modelos, mejora relativa, regla de empate | ✅ 04_lgbm_adaptada (añadir sección) |
| Diagnóstico: real vs predicho, residuos, error por tramo, por motor, curvas | ✅ 04_lgbm_adaptada (añadir gráficas) |
| Vista de depuración por motor | ✅ 04_lgbm_adaptada (añadir sección) |
| Persistencia + manifiesto + recarga verificada | ✅ 05_ensemble_adaptado (ya tiene puerta D11) |

## Gaps que existen en ambos (legacy y propuesta)

Estos gaps los identificó el subagente de ds02_ensemble. Existen tanto en los legacy como en la propuesta. Se pueden añadir como Markdown en 5-10 min cada uno:

| Gap | Dónde añadir | Esfuerzo |
|---|---|---|
| Ecuación de residualización (sensor − Ridge(poly(W))) | 01_eda (Markdown) | 5 min |
| Hiperparámetros del meta-learner (LGBM meta, blend 50/50) | 05_ensemble_adaptado (Markdown) | 5 min |
| Grid de beta (0-1, 21 puntos) y criterio RMSE+NASA | 05_ensemble_adaptado (Markdown) | 5 min |
| Fórmula EMA causal (alpha=2/(span+1)) | 05_ensemble_adaptado (Markdown) | 5 min |
| min_rows fallback + clip de lower en conformal | 04_lgbm_adaptada (Markdown) | 5 min |
| Alternativa use_baseline_delta en cyc_norm | 03_modelos_B (Markdown) | 5 min |
| Detalles de entrenamiento BiLSTM (Huber δ=10, Adam lr=1e-3, etc.) | 02_modelos_A (Markdown) | 5 min |
| LGB_PARAMS (de pipeline.py) | 02_modelos_A (Markdown) | 5 min |

## Esfuerzo total: ~4-5 horas | Riesgo global: 3/10

## Restricciones

- NO marcar `notebooks/ds02_ensemble/` como legacy. Se mantiene intacto.
- NO modificar `src/`, `app/`, `mia/`, `models/`, `requirements.txt`.
- Solo modificar archivos dentro de `notebooks/` (01-05).
- Verificar con `nbconvert --execute` tras cada cambio.

## Archivos de referencia

- Legacy notebooks: `notebooks/ds02_ensemble/01_datos_y_bases.ipynb`, `02_decision_ablacion_oof_ensamble.ipynb`, `03_evidencia_multisemilla_diagnostico.ipynb`
- Track notebooks: `notebooks/01_eda.ipynb` ... `notebooks/05_ensemble_adaptado.ipynb`
- Código fuente: `src/ds02_rul/data.py`, `features.py`, `residualizer.py`, `pipeline.py`, `model.py`, `stacking.py`, `smoothing.py`, `metrics.py`
- Funciones de inferencia: `app/ui_inference.py` (example_window, window_ending_at, demo_presets)
- Datos: `data/processed/` (parquet, ignorado en git, regenerable)
- Resultados: `resultados/` (CSV, PNG, ignorado en git, regenerable)

## Verificación post-implementación

Tras cada notebook modificado, ejecutar:
```bash
.venv/Scripts/python -m nbconvert --execute notebooks/0X_*.ipynb --to notebook --inplace
.venv/Scripts/python -m pytest tests -q
```

## Notas para el agente

- El agente que lea este documento debe primero explorar el repo y sacar sus propias conclusiones.
- Si las conclusiones del agente coinciden con las de este documento, implementar.
- Si no coinciden, documentar las discrepancias y proponer una alternativa.
- El agente puede usar subagentes para explorar notebooks, código y resultados.
- El agente debe verificar con `nbconvert --execute` que cada notebook modificado se ejecuta sin errores.
