---
tipo: notebook
status: sin-estudiar
tags:
  - api
  - src
  - referencia
---

# API de src_ds02_rul — mapa regenerable

> [!abstract] En una frase
> Todo lo que los cuadernos importan vive en `src/ds02_rul/` y `src/clase/` con firma y línea conocidas.

## Contrato

| Entra | Sale |
|---|---|
| Ventanas crudas y prep congelado | RUL, banda y estado sin reentrenar |
| Cualquier semilla de `[42, 7, 123]` | Misma API, distinto ruido |

## Cómo está implementado

Inventario generado por AST desde `src/ds02_rul/` (firmas y líneas reales).

| Módulo | Función o clase clave | Línea |
|---|---|---|
| `data.py` | `load_ds02(path, stride=100)` | `src/ds02_rul/data.py:49` |
| `data.py` | `resolve_ds02(path)` | `src/ds02_rul/data.py:35` |
| `features.py` | `fit_preprocessing(W, Xs)` | `src/ds02_rul/features.py:25` |
| `features.py` | `build_windows(...)` | `src/ds02_rul/features.py:79` |
| `model.py` | `build_champion_bilstm(...)` | `src/ds02_rul/model.py:19` |
| `pooling.py` | `LastStepPooling` | `src/ds02_rul/pooling.py:16` |
| `pipeline.py` | `run_seed(...)` | `src/ds02_rul/pipeline.py:88` |
| `pipeline.py` | `oof_base_predictions(...)` | `src/ds02_rul/pipeline.py:157` |
| `pipeline.py` | `make_lgbm(seed)` | `src/ds02_rul/pipeline.py:46` |
| `stacking.py` | `select_beta_grouped(...)` | `src/ds02_rul/stacking.py:234` |
| `stacking.py` | `fit_meta_learners(...)` | `src/ds02_rul/stacking.py:192` |
| `ensemble.py` | `HybridStackingEnsemble` | `src/ds02_rul/ensemble.py:23` |
| `ensemble.py` | `predict / predict_interval` | `src/ds02_rul/ensemble.py:101` |
| `conformal.py` | `fit_conformal / apply_conformal` | `src/ds02_rul/conformal.py:28` |
| `metrics.py` | `calculate_nasa_score` | `src/ds02_rul/metrics.py:14` |
| `metrics.py` | `macro_rmse` | `src/ds02_rul/metrics.py:21` |
| `inference.py` | `windows_for_unit(...)` | `src/ds02_rul/inference.py:49` |
| `persistence.py` | `save_ensemble / load_ensemble` | `src/ds02_rul/persistence.py:108` |

Regla de lectura: `data` ingiere, `features` transforma, `model` y `pipeline` entrenan bases, `stacking` combina, `ensemble` sirve, `conformal` acota, `metrics` puntúa, `persistence` congela.

## Dónde se usa cada pieza (ver recorrido)

| Pieza | Ver recorrido |
|---|---|
| `data/features` + base clase | [[n01-recorrido-nb01]] NB01 EDA |
| `train_clasicos/train_mlp/shap_clase/tabla_final` | [[n02-recorrido-nb02]] NB02 fila |
| `stacking.py:161` reloj + ablación | [[n03-recorrido-nb03]] NB03 |
| `model/pipeline/stacking/ensemble/conformal` OOF+beta | [[n06-recorrido-nb04]] NB04 |
| `train_lgbm_adaptada` + multisemilla | [[n07-recorrido-nb05]] NB05 |
| `puente_c/run_seed/load_ensemble/tabla_final` bundle C | [[n08-recorrido-nb06]] NB06 |
| `shap_c.py:216` por ramas | [[n09-recorrido-nb07]] NB07 |
| Cadena artefactos NB01→NB06 | [[n04-cadena-de-estado]] |

## Inventario de `src/clase/` — el track tabular

| Módulo | Función o pieza clave | Línea |
|---|---|---|
| `dataset_clase.py` | `SENSOR_COLS` (14 sensores) | `src/clase/dataset_clase.py:31` |
| `pipeline_clase.py` | `NUM_COLS` / `CAT_COLS` / `FEATURE_COLS` | `src/clase/pipeline_clase.py:22` |
| `pipeline_clase.py` | `predict_caso_nuevo` | `src/clase/pipeline_clase.py:43` |
| `train_clasicos.py` | 5 clásicos + GroupKFold | `src/clase/train_clasicos.py` |
| `train_mlp.py` | MLP + GridSearch (E1/E2/E3) | `src/clase/train_mlp.py` |
| `train_ensemble_adaptado.py` | `construir_raw_adaptado` (EPOCHS 22) | `src/clase/train_ensemble_adaptado.py:67` |
| `train_lgbm_adaptada.py` | LGBM cuantil sobre base adaptada | `src/clase/train_lgbm_adaptada.py` |
| `evaluar_c_multisemilla.py` | protocolo [42, 7, 123] | `src/clase/evaluar_c_multisemilla.py` |
| `tabla_final.py` | `COLUMNAS` con `grano` | `src/clase/tabla_final.py:18` |
| `shap_clase.py` / `shap_clase_e2.py` | diccionario top SHAP | `src/clase/shap_clase.py` |
| `puente_c.py` / `ventanas_adaptadas.py` | puente + ventanas de 50 | `src/clase/puente_c.py` |

Regla de lectura del track clase: `dataset` ingiere, `pipeline_clase` transforma, `train_*` compiten con GroupKFold, `evaluar_c_multisemilla` repite, `tabla_final` ordena por grano, `shap` explica.

## La decisión que hay detrás

Separar `src/` de cuadernos permite que NB01–NB06 sean finos: importan, no definen. El código serio vive testeado en `src/` y los cuadernos solo orquestan.

Se rechazó definir modelos dentro del cuaderno: no se reutiliza, no se testea y no se sirve. Lo que se sirve es `src`, no celdas.

## Qué medimos

La API no puntúa: puntúa `metrics.py:46` con RMSE, MAE, R² y NASA. Sus números vigentes están en [[e00-cifras-autoritativas]].

Si una firma cambia, esta nota se regenera por AST: no se edita a mano. La fuente es el código, no la memoria.

## El límite

> [!warning] Lo que este mapa no es
> No es tutorial ni referencia completa: es índice con firma y línea. El comportamiento vive en el código y en su docstring. Si el código y esta nota discrepan, manda el código.

## Di esto en el tribunal

> [!quote]
> «Todo lo que uso está en src con firma conocida: data carga, features transforma, model y pipeline entrenan, stacking combina, ensemble sirve, conformal acota y persistence congela.»

## Flashcards

> [!question]- ¿Dónde se ajusta el preproceso?
> En `features.py:25`, solo con ajuste.

> [!question]- ¿Dónde se elige beta?
> En `stacking.py:234` con folds agrupados.

> [!question]- ¿Dónde se sirve la predicción?
> En `ensemble.py:101` con `predict` y `predict_interval`.

> [!question]- ¿Dónde se calibra la banda?
> En `conformal.py:28` con residuales fuera de fold.
