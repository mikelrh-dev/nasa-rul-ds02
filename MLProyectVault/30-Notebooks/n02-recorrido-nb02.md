---
tipo: notebook
status: sin-estudiar
tags:
  - nb02
  - clasicos
  - mlp
  - shap
---

# NB02 — 5 clásicos + MLP

> [!abstract] En una frase
> Seis modelos pelean en grano fila con el mismo pipeline y GroupKFold por motor; gana el MLP E2 por validación y SHAP cuenta qué miró el árbol.

## Antes de empezar

39 celdas. Requiere la base de [[s15-dataset-de-clase]] y el pipeline de [[s16-pipeline-de-clase]]. Cubre rúbrica SAA 6/8 (comparativa) y SAA 7/9 (MLP + importancia). GridSearch con GroupKFold: tarda minutos en CPU.

## Recorrido celda a celda

| Bloque | Qué entra | Qué hace | Qué sale |
|---|---|---|---|
| 5 clásicos + GridSearch | pipeline + base | Ridge (baseline), KNN, RF, SVM, XGB, CV por motor | tabla con baseline primero + regla de empate |
| Real vs predicho (clásico) | test 11/14/15, 1 lectura | scatter del mejor clásico | XGB val 8.22, dónde falla |
| Análisis por motor | test desagregado | el global puede esconder un motor | el 14, como siempre |
| MLP base + E1/E2/E3 | mismo pipe | capacidad vs regularización vs batch | E2 (val 7.34) < base (7.36) < E3 |
| Real vs predicho (MLP) | test, 1 lectura | scatter del E2 | test 7.72, MAE 5.81, R² 0.83 |
| Importancia mejor clásico | modelo ajustado | qué variables pesan | ranking tabular |
| SHAP XGB | TreeExplainer exacto, 200 filas val | doble lectura global+local | `shap_xgb_top.joblib` |
| Cierre | comparativa | MLP E2 campeón de fila por validación | test leído una sola vez |

Set real de clásicos según `resultados/comparativa.csv`: **knn, regresion (Ridge), rf, svm, xgb** (5 filas; el LightGBM cuantil 0.35 es la rama tabular del híbrido, no una fila de ese CSV). No decir "5 clásicos" incluyendo LightGBM como si estuviera en ese CSV.

Las cifras oficiales: E2 train 5.71 / val 7.34 / test 7.72 ([[e00-cifras-autoritativas]]).

### Experimentos MLP (celda 15, `notebooks/02_modelos_clasicos_y_mlp.ipynb`)

| Nombre | Qué cambia | Resultado en val |
|---|---|---|
| base | (128,64), alpha 1e-3 | 7.36, referencia |
| E1_capacidad | más capas (256,128,64) | 7.48, overfit, se descarta |
| E2_reg_lr | más regularización alpha 1e-2 | 7.34, gana, test 7.72 |
| E3_batch | batch_size 1024 | 7.36, igual que la base |

Regla para no liarte: E1 = capacidad, E2 = regularización, E3 = batch.

### Conclusion (celda 38, texto exacto del notebook)

> **Conclusion:**
> He visto los 5 modelos clasicos con GridSearch, el MLP (E1-E3) y el SHAP del XGB.
> He medido todos con la misma validacion y la misma semilla.
> La decision sale de la tabla comparativa de este notebook, no de un solo modelo suelto.
> No he re-ejecutado nada: esto es solo texto Markdown.
> Siguiente paso: 03_feature_engineering_secuencial.ipynb

## Código que ejecuta cada bloque (.py:línea)

| Bloque | .py que manda |
|---|---|
| 5 clásicos + GridSearch GroupKFold | `src/clase/train_clasicos.py:145` ordena por `rmse_val` |
| MLP base/E1/E2/E3 | `src/clase/train_mlp.py:107` ordena por `rmse_val` |
| SHAP XGB exacto + aditividad 1e-5 | `src/clase/shap_clase.py` `check_aditividad`, fondo 200 train / 200 val fold-0 |
| Permutación XGB | `src/clase/train_mlp.py` 200 filas val fold-0, T30 6ª |
| Tabla final por grano | `src/clase/tabla_final.py:18` `COLUMNAS` con `grano`, nunca ranking mixto |

## Las 5 celdas que importan

1. Tabla con baseline primero: sin suelo no hay carrera.
2. Regla de empate: escrita, no opinada.
3. Por motor: el global esconde al 14.
4. E2 por validación: la elección es previa al test.
5. SHAP: la explicabilidad del que no ganó también cuenta.

## Qué NO hace este cuaderno

No toca ventanas ni secuencias (eso es NB04), no ablaciona `cyc_norm` (eso es NB03), no multisemilla (eso es NB05). NB02 corona al campeón de fila.

## Conexiones

- Grano fila: [[c15-grano-fila-vs-ventana]] · GroupKFold: [[c16-groupkfold-por-motor]] · sistema: [[s17-clasicos-y-mlp]] · SHAP: [[c21-shap-e-ia-debil]] · tabla: [[s19-tabla-final-y-grano]]
- Sigue en [[n03-recorrido-nb03]] (features secuenciales).

> [!quote] Di esto en el tribunal
> «En el segundo cuaderno compiten seis con las mismas reglas: mismo pipeline, validación por motor, baseline primero. Gana el MLP E2 por validación con 7.34 y el test se lee una vez: 7.72».

## Flashcards

> [!question]- ¿Quién gana NB02 y cómo se decidió?
> El MLP E2 ((128,64), alpha 0.01): gana en validación (7.34) con GroupKFold por motor; su test 7.72 se lee una sola vez, posterior a la elección.

> [!question]- ¿Qué pinta SHAP en un cuaderno que corona un MLP?
> Explica al mejor clásico (XGB): la explicabilidad no es premio del ganador, es requisito del sistema; el diccionario top queda en `shap_xgb_top.joblib`.
