---
tipo: sistema
status: sin-estudiar
tags:
  - pipeline
  - sklearn
  - clase
  - pia
---

# Pipeline de clase — un ColumnTransformer para todo

> [!abstract] En una frase
> Un solo `ColumnTransformer` (19 numéricas + `fase_vuelo`) alimenta a los 5 clásicos y al MLP: el mismo preproceso, seis modelos comparables.

## Contrato

| Entra | Sale |
|---|---|
| Fila cruda (20 columnas + `unit`) | Predicción RUL + `predict_caso_nuevo` para la app |

## Cómo está implementado

| Pieza | Dónde | Qué hace |
|---|---|---|
| `NUM_COLS` (19) | `src/clase/pipeline_clase.py:22` | cycle, alt, Mach, TRA, T2 + 14 sensores → StandardScaler |
| `CAT_COLS` (1) | `src/clase/pipeline_clase.py:23` | `fase_vuelo` → OneHot(handle_unknown=ignore) |
| `FEATURE_COLS` | `src/clase/pipeline_clase.py:24` | 19 + 1; `unit` excluida (es grupo, no predictor) |
| `predict_caso_nuevo` | `src/clase/pipeline_clase.py:43` | predice un caso nuevo con el pipe guardado |
| Artefacto | `models/mejor_modelo_clase.joblib` | pipe completo (pre + reg), una sola pieza desplegable |

Un solo objeto serializado evita el skew train/serve: lo que se validó es byte a byte lo que predice.

## Conexiones

- Base: [[s15-dataset-de-clase]] · validación por motor: [[c16-groupkfold-por-motor]] · lo que cuelga encima: [[s17-clasicos-y-mlp]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Un único pipeline sklearn para seis modelos: el preproceso se ajusta una vez y se congela dentro del artefacto, así que la app no puede preprocesar distinto de como se entrenó».

## Flashcards

> [!question]- ¿Qué contiene el pipeline de clase y por qué un solo objeto?
> Un ColumnTransformer (19 numéricas escaladas + fase_vuelo en OneHot) más el regresor, guardado entero en `mejor_modelo_clase.joblib`: garantiza que la app preprocesa idéntico al entrenamiento (sin skew train/serve).
