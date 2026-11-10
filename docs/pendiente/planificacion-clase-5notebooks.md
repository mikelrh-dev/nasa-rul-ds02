# Planificación completa — Track de clase DS02 (5 notebooks) — para verificación por agente

> Re-generado a partir de la sesión "Analizar cumplimiento rubrica y reto". No modifica archivos del repo. Solo documento.

## Prompt para agente (copiar y pegar)

```
Eres un agente de verificación. Tu tarea es verificar que la planificación ACTUALIZADA de 5 notebooks en clase/ cumple la rúbrica del Reto 1 (SAA + PIA + MIA) y que no hay redundancias, violaciones de restricciones ni problemas de trazabilidad.

CONTEXTO DEL PROYECTO:
- Repo: C:\Users\mikel\Desktop\Pruebas\nasa
- Rama: clase-experimental (ya creada, sincronizada con origin)
- Proyecto principal: N-CMAPSS DS02 RUL (BiLSTM + LightGBM + stacking + EMA)
- Modelo de producción: bundle B (RMSE 4.251, sin nulos) — congelado en models/ensemble.joblib
- Modelo experimental: bundle C (RMSE 4.338, con nulos) — reentrenado en clase/05_ensemble_adaptado.ipynb
- Mejor modelo del track de clase: MLP E1 (RMSE 7.70, MAE 5.57, R² 0.84)
- Restricción: SOLO modificar archivos dentro de clase/ (excepto models/ y tests/ cuando se guarde un modelo o test).
- Rúbrica en: docClase/Reto1_SAA_PIA_MIA_2026-27_v5.pdf (texto en C:\Users\mikel\AppData\Local\hermes\cache\scratch\reto.txt).

ESTRUCTURA FINAL (5 notebooks en clase/):
1. 01_eda.ipynb — EDA + nulos + fase_vuelo.
2. 02_modelos_A.ipynb — 5 clásicos + GridSearchCV.
3. 03_modelos_B.ipynb — MLP + importancia.
4. 04_lgbm_adaptada.ipynb — LightGBM con nulos (prototipo).
5. 05_ensemble_adaptado.ipynb — Ensemble con nulos (bundle C) + comparativa vs MLP E1.

CAMBIOS RESPECTO A LA PLANIFICACIÓN ANTERIOR:
1. **RA1 y RA2 de SAA se incluyen explícitamente en celdas Markdown del notebook 01:**
   - Celda Markdown: "Este sistema es una IA débil porque solo predice RUL de DS02 con telemetría aprendida. No sabría fijar precios ni atender llamadas. Ventaja: barata, rápida, auditable. Aprendizaje supervisado (cada fila lleva su RUL real) de regresión (valor continuo, no clase). Se diferencia del no supervisado en que hay etiqueta y métrica contra verdad (RMSE/MAE/R²)."
2. **Narrativa alternativa para evitar mencionar "bundle B" en los notebooks:**
   - En notebook 05: "Se evalúa si el Ensamble (4.33) supera el umbral preestablecido de calidad industrial (RMSE < 4.25). Al no superarlo, el modelo MLP (7.70) o el SVM clásico se postulan como los mejores modelos del entorno académico."
3. **Documentación en README de clase (clase/README.md):**
   - "La app Streamlit (app/dashboard_ds02.py) y las reglas (mia/reglas.py) se evalúan sobre el modelo de producción. El track de clase demuestra que el pipeline también funciona con nulos (bundle C, 4.338)."
   - "MLflow y n8n se añaden en el change siguiente. La tabla comparativa es resultados/comparativa.csv (pandas)."
4. **MLflow se excluye deliberadamente** (decisión del usuario: "excepto parte n8n y mlflow"). Se documenta como pendiente en el README de clase.
5. **n8n se excluye deliberadamente** (decisión del usuario). Se documenta como pendiente en el README de clase.

DETALLE DE CADA NOTEBOOK:

### 01_eda.ipynb
- Carga HDF5 (src/ds02_rul/data.py, stride=100).
- **Celda Markdown RA1:** "Este sistema es una IA débil porque solo predice RUL de DS02 con telemetría aprendida. No sabría fijar precios ni atender llamadas. Ventaja: barata, rápida, auditable."
- **Celda Markdown RA2:** "Aprendizaje supervisado (cada fila lleva su RUL real) de regresión (valor continuo, no clase). Se diferencia del no supervisado en que hay etiqueta y métrica contra verdad (RMSE/MAE/R²)."
- Inyección de nulos (MAR en T30, crucero alto). Auditoría: % nulos por sensor.
- Imputación: ffill causal por unidad, orden temporal, mediana de train para primer NaN.
- Crear fase_vuelo (Ascenso/Crucero/Descenso) a partir de alt/Mach (umbrales 18k/26k+0.65).
- 5 gráficos obligatorios: barras (fase), histograma (RUL), boxplot (T48 por fase), dispersión (alt vs Mach), heatmap (correlación).
- Tabla de campos: nombre, qué significa, tipo, nulos antes/después.
- Conclusiones EDA.

### 02_modelos_A.ipynb
- Cargar parquet existentes (train_con_nulos, test_con_nulos) + fase_vuelo.
- Residualización (Ridge sobre W polinomial) — fit solo fit units [2,5,10,18,20].
- Features tabulares (93).
- Pipeline sklearn: StandardScaler + OneHotEncoder(fase_vuelo) + modelo. Un pipeline por modelo.
- Split: fit units [2,5,10,18,20], holdout unit 16, test [11,14,15].
- 5 modelos: Regresión (Ridge), KNN, RF, XGBoost, SVM. Con GridSearchCV.
- Métricas: RMSE, MAE, R², NASA score. Tabla comparativa.
- Análisis por motor: tabla RMSE/MAE/sesgo.
- Gráfica: comparativa de los 5 modelos.

### 03_modelos_B.ipynb
- Cargar parquet + fase_vuelo + residualización + features.
- MLP base + 3 experimentos (capacidad, regularización, batch size/learning rate).
- Comparativa: base vs E1 vs E2 vs E3. Tabla + gráfica.
- Métricas: RMSE, MAE, R², NASA score. Análisis por motor.
- Importancia de variables (permutación o SHAP). Variables que pesan más: T50, cycle, T48.
- Gráfica real vs predicho (mejor MLP).
- Conclusión: MLP E1 (RMSE 7.70). Justificación: RMSE manda.

### 04_lgbm_adaptada.ipynb
- Cargar parquet MAR-imputado + residualización + features (SIN fase_vuelo: contrato 93 intacto).
- LightGBM cuantil 0.35 (LGB_PARAMS) + GridSearchCV.
- Métricas: RMSE, MAE, R², NASA score.
- Análisis por motor: tabla + gráfica.
- Gráfica real vs predicho.
- Comparativa: LightGBM (con nulos) vs MLP E1 (7.70).
- Importancia de features.
- Conclusión: si RMSE razonable (~7.0), pasar a BiLSTM (nb05).

### 05_ensemble_adaptado.ipynb
- Cargar parquet MAR-imputado + residualización + features + ventanas (50 ciclos, SIN fase_vuelo: contrato 93 intacto).
- BiLSTM (triple pooling, early stopping, cyc_norm canal 19).
- LightGBM cuantil 0.35 (93 features).
- Stacking (RidgeCV + LightGBM meta, sin cyc_norm).
- Beta shrinkage (beta=1.0) + EMA causal (span=5).
- Métricas: RMSE, MAE, R², NASA score. Análisis por motor.
- Gráfica real vs predicho (ensemble).
- **Narrativa explícita (mencionar bundle B congelado como referencia):** "Se evalúa si el Ensamble (4.33) supera el umbral preestablecido de calidad industrial (RMSE < 4.25). Al no superarlo, el modelo MLP (7.70) o el SVM clásico se postulan como los mejores modelos del entorno académico."
- Guardar models/mejor_modelo_clase_ensemble.joblib (bundle C).
- **Conclusión (texto exacto que debe imprimirse):** "evaluar puerta D11. Como el RMSE (4.33) no es ≤ 4.25, imprimir: 'El ensamble no supera el umbral de calidad industrial. Se mantiene la arquitectura base de producción y el ensamble adaptado queda como experimento documentado.'"

VERIFICACIÓN SOLICITADA:
1. ¿Los 5 notebooks cumplen la rúbrica SAA (criterios 1-10)? Reportar puntuación estimada por criterio.
2. ¿Los 5 notebooks cumplen la rúbrica PIA (criterios 1-6)? Reportar puntuación estimada por criterio.
3. ¿Los 5 notebooks cumplen la rúbrica MIA (criterios 1-4)? Reportar puntuación estimada por criterio.
4. ¿Hay redundancias entre notebooks? (ej. código duplicado, gráficas repetidas, datos re-inyectados).
5. ¿Se viola la restricción "SOLO modifica archivos dentro de clase/"? (verificar que no se tocan src/, app/, mia/, README.md raíz, requirements.txt).
6. ¿Se preserva la trazabilidad del bundle B? (verificar que models/ensemble.joblib, 02_DS02_ensemble_RUL.ipynb, notebooks/ds02_ensemble/ no se modifican).
7. ¿Se menciona "bundle B" en los notebooks? (no debería, según la planificación).
8. ¿Se incluye cyc_norm en los notebooks? (sí en BiLSTM, no en meta-learner). ¿Se explica por qué?
9. ¿Se incluyen gráficas explicativas y comparativas en cada notebook?
10. ¿Se incluye análisis por motor en los notebooks 02, 03, 04, 05?
11. ¿Se incluyen RA1 y RA2 de SAA en celdas Markdown del notebook 01?
12. ¿Se documenta en el README de clase que la app y las reglas existen en el proyecto principal?
13. ¿Se documenta MLflow y n8n como pendientes en el README de clase?

FORMATO DE SALIDA:
- Tabla resumen por criterio (SAA, PIA, MIA) con puntuación estimada.
- Lista de redundancias detectadas (si las hay).
- Lista de violaciones de restricciones (si las hay).
- Lista de problemas de trazabilidad (si los hay).
- Recomendaciones de mejora (si las hay).
- Veredicto final: ¿la planificación es sólida o necesita cambios?

NO MODIFICAR ARCHIVOS. Solo verificar y reportar.
```
```

## Resumen
- Documento completo re-generado a partir de la sesión anterior.
- Listo para copiar/pegar a un agente verificador.
- Sin cambios en el repo.