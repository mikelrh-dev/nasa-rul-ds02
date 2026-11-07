---
tipo: concepto
status: consolidado
tags:
  - mlflow
  - tracking
  - experimentos
---

# MLflow — tracking de experimentos

> [!abstract] En una frase
> MLflow registra qué hiperparámetros se probaron, con qué métricas train/val y cuánto tiempo tardaron, para comparar experimentos sin perder el rastro.

## La idea

MLflow es la herramienta estándar de tracking de experimentos: cada corrida (`run`) guarda parámetros, métricas y artefactos en un mismo sitio, así la comparativa deja de vivir en un CSV suelto y se puede consultar, filtrar y reproducir.

Tres piezas:

1. **Parámetros**: los hiperparámetros probados (p. ej. `n_neighbors`, `alpha`, `max_depth`). Quedan fijados en la corrida.
2. **Métricas**: RMSE/MAE/R² en train y en validación (y test cuando existe). Son el criterio para elegir.
3. **Tiempo**: segundos de entrenamiento por modelo. Permite descartar lo que no compensa, aunque mida bien.

## Comparativa del proyecto (sustituto actual)

Tabla de `resultados/comparativa.csv` (hiperparámetros y métricas train/val/tiempo):

| Modelo | Hiperparámetros | Tiempo (s) | RMSE train/val | MAE train/val | R² train/val |
|---|---|---|---|---|---|
| knn | `{'reg__n_neighbors': 31}` | 9.1 | 6.984 / 9.4092 | 5.3739 / 8.1856 | 0.9025 / 0.8181 |
| regresion | `{'reg__alpha': 10.0}` | 3.5 | 8.2004 / 8.2762 | 6.9054 / 7.6611 | 0.8656 / 0.8502 |
| rf | `{'reg__max_depth': 8}` | 79.6 | 7.1572 / 9.0704 | 5.7492 / 8.1534 | 0.8977 / 0.8270 |
| svm | `{'reg__C': 10.0, 'reg__epsilon': 1.0}` | 2.7 | 7.5251 / 8.2927 | 5.8227 / 7.5299 | 0.8869 / 0.8565 |
| xgb | `{'reg__max_depth': 4}` | 7.2 | 7.1887 / 8.2173 | 5.9025 / 7.4688 | 0.8968 / 0.8543 |

Columnas del CSV original: `modelo,mejores_params,tiempo_s,rmse_train,mae_train,r2_train,rmse_val,mae_val,r2_val,rmse_test,mae_test,r2_test`. Solo `xgb` trae fila de test (11.034 / 9.9098 / 0.6616); el resto deja test vacío porque la selección se hace con train/val.

Las capturas y figuras de esta comparativa viven en `resultados/` junto al CSV (`mlp_comparativa.csv`, `tabla_final_clase.csv`, `comparativa_bundle_c.csv`, `comparativa_c_multisemilla.csv`, `comparativa_ventanas.csv` y los PNG asociados). Hoy son el artefacto consultable: si hay que defender un número, se abre el CSV y el PNG de esa carpeta.

## Dónde aparece en este proyecto

- `resultados/comparativa.csv` — la comparativa vigente sin MLflow.
- `s14-app-y-despliegue` pendiente declarado: MLflow (PIA-4, 20%: tracking de experimentos).
- `s17-clasicos-y-mlp` y `s18-lgbm-adaptada` — familias que hoy se comparan con CSV.

> [!warning] La trampa
> «El CSV ya es MLflow»: no. El CSV guarda la foto de una comparativa; MLflow guarda el historial ordenado de corridas con parámetros, métricas y artefactos recuperables. El CSV engaña si no se sabe qué se probó antes.

## Estado actual

La spec lo exige como PIA-4 (tracking de experimentos, 20 % de rúbrica), pero **el proyecto aún no lo tiene**: no hay `mlflow` en `requirements` ni runs registrados en el repo. Hoy se sustituye con `resultados/comparativa.csv` y los PNG en `resultados/`.

Está declarado como pendiente en [[s14-app-y-despliegue]]: «MLflow (PIA-4) va en el change siguiente, no en este. Si el tribunal lo pide: está excluido por alcance con diseño previsto, no olvidado». No se inventa un backend ni una URL: cuando se implemente, esta nota se actualiza con el destino de los runs.

## Di esto en el tribunal

> [!quote]
> «MLflow es el registro de experimentos: hiperparámetros, métricas train/val y tiempo por corrida. La rúbrica lo pide como PIA-4; hoy lo sustituye `resultados/comparativa.csv` con sus capturas en `resultados/`, y está declarado como pendiente con diseño previsto».

## Flashcards

> [!question]- ¿Qué es MLflow?
> Tracking de experimentos: cada corrida guarda hiperparámetros, métricas train/val y tiempo para comparar y reproducir.

> [!question]- ¿Qué columnas tiene la comparativa actual?
> `modelo,mejores_params,tiempo_s,rmse_train,mae_train,r2_train,rmse_val,mae_val,r2_val,rmse_test,mae_test,r2_test` en `resultados/comparativa.csv`.

> [!question]- ¿Dónde están las capturas?
> En `resultados/` junto a los CSV (`mlp_comparativa.csv`, `tabla_final_clase.csv`, `comparativa_bundle_c.csv` y sus PNG).

> [!question]- ¿Cuál es el estado de MLflow en el proyecto?
> Exigido por la spec (PIA-4) pero aún no implementado; hoy se sustituye con `resultados/comparativa.csv`. Pendiente declarado en `s14`.

> [!question]- ¿Qué afirma esta nota en una frase?
> MLflow es el registro de experimentos con hiperparámetros y métricas; hoy el CSV es su sustituto y PIA-4 sigue pendiente.
