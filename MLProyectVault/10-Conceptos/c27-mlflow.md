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
> MLflow registra qué hiperparámetros se probaron, con qué métricas train/val/test y cuánto tiempo tardaron, para comparar experimentos sin perder el rastro.

## La idea

MLflow es la herramienta estándar de tracking de experimentos: cada corrida (`run`) guarda parámetros, métricas y artefactos en un mismo sitio, así la comparativa deja de vivir en un CSV suelto y se puede consultar, filtrar y reproducir.

Tres piezas:

1. **Parámetros**: los hiperparámetros probados (p. ej. `n_neighbors`, `alpha`, `max_depth`). Quedan fijados en la corrida.
2. **Métricas**: RMSE/MAE/R² en train y en validación (y test cuando existe). Son el criterio para elegir.
3. **Tiempo**: segundos de entrenamiento por modelo. Permite descartar lo que no compensa, aunque mida bien.

## MLflow del proyecto (13 runs)

El 2026-11-09 se registraron **13 corridas** en el experimento `ds02-clase`, dentro de `mlruns/` (file store de texto, sin servidor ni SQLite). No se reentrenó nada: `scripts/backfill_mlflow.py --write` lee los CSV, el log del bundle y el manifiesto, y es idempotente por el tag `run_key`.

| Grano | Runs | Qué contiene |
|---|---:|---|
| fila | 9 | 5 clásicos + 4 MLP; `rmse_val` y test solo del elegido |
| ventana | 4 | LGBM, BiLSTM, BiLSTM+EMA5 y bundle C; test 6.196 ventanas |

La tabla de 5 clásicos sigue siendo la foto rápida (`resultados/comparativa.csv`); el CSV exportado por la API (`docs/evidencia/mlflow/comparativa.csv`) añade `run_id`, `grano`, `rol`, `seleccion`, `params_summary` y las métricas de los 13.

| Modelo | Hiperparámetros | Tiempo (s) | RMSE train/val | MAE train/val | R² train/val |
|---|---|---|---|---|---|
| knn | `{'reg__n_neighbors': 31}` | 9.1 | 6.984 / 9.4092 | 5.3739 / 8.1856 | 0.9025 / 0.8181 |
| regresion | `{'reg__alpha': 10.0}` | 3.5 | 8.2004 / 8.2762 | 6.9054 / 7.6611 | 0.8656 / 0.8502 |
| rf | `{'reg__max_depth': 8}` | 79.6 | 7.1572 / 9.0704 | 5.7492 / 8.1534 | 0.8977 / 0.8270 |
| svm | `{'reg__C': 10.0, 'reg__epsilon': 1.0}` | 2.7 | 7.5251 / 8.2927 | 5.8227 / 7.5299 | 0.8869 / 0.8565 |
| xgb | `{'reg__max_depth': 4}` | 7.2 | 7.1887 / 8.2173 | 5.9025 / 7.4688 | 0.8968 / 0.8543 |

Solo `xgb` y `mlp__E2_reg_lr` traen `rmse_test` en el grano fila (11.034 y 7.7211): el test se leyó una vez y solo para el elegido. El resto deja test vacío porque la selección se hace con train/val.

Las capturas viven en `docs/evidencia/mlflow/`: `compare_fila.png` (9 runs de fila), `compare_ventana.png` (4 de ventana) y `run_prod.png` (bundle C con los cuatro SHA). El store no guarda binarios; los modelos siguen en `models/` y se identifican por SHA-256.

## Dónde aparece en este proyecto

- `mlruns/` — store MLflow de texto con los 13 runs (PIA-4).
- `scripts/backfill_mlflow.py` — backfill idempotente `--write` / `--check` / `--export`.
- `docs/evidencia/mlflow/comparativa.csv` — exportación por API del store.
- `docs/evidencia/mlflow/compare_fila.png`, `compare_ventana.png`, `run_prod.png` — evidencia visual.
- [[s14-app-y-despliegue]] — la app sirve el bundle C; no depende de MLflow en runtime.
- `s17-clasicos-y-mlp` y `s18-lgbm-adaptada` — familias registradas en el experimento.

> [!warning] La trampa
> «El CSV ya es MLflow»: no. El CSV es una foto; MLflow guarda el historial de corridas con parámetros, métricas y tags consultables. Aquí el CSV es la **exportación** del store, no su sustituto.

## Estado actual

Implementado el 2026-11-09 (change `2026-11-09-mlflow-pia4`): MLflow 3.18.0, file store de texto en `mlruns/`, 13 runs (9 fila + 4 ventana), `MLFLOW_ALLOW_FILE_STORE=true` porque 3.18 bloquea el backend de ficheros por defecto. No hay artefactos ni `log_model`/`autolog`; los binarios siguen en `models/` y los cuatro SHA del manifiesto identifican el bundle. `tests/test_mlflow_backfill.py` lee el store desde disco, sin servidor, y `--check` exige 13 runs, 9/4 por grano, `run_key` único y CSV==store.

## Di esto en el tribunal

> [!quote]
> «MLflow registra 13 corridas en `mlruns/`: 9 de grano fila (5 clásicos + 4 MLP) y 4 de grano ventana (LGBM, BiLSTM, EMA5 y el bundle C). Cada una guarda parámetros, métricas y tiempo; el CSV de `docs/evidencia/mlflow/` es la exportación, y las dos capturas separan los granos para no comparar peras con racimos. El store es texto y los binarios siguen en `models/` con su SHA».

## Flashcards

> [!question]- ¿Qué es MLflow?
> Tracking de experimentos: cada corrida guarda hiperparámetros, métricas train/val/test y tiempo para comparar y reproducir.

> [!question]- ¿Cuántos runs y de qué granos hay?
> 13 en `ds02-clase`: 9 de fila (5 clásicos + 4 MLP) y 4 de ventana (LGBM, BiLSTM, EMA5, bundle C).

> [!question]- ¿Dónde están las capturas?
> En `docs/evidencia/mlflow/`: `compare_fila.png`, `compare_ventana.png` y `run_prod.png`.

> [!question]- ¿Cuál es el estado de MLflow en el proyecto?
> Implementado (2026-11-09) con 13 runs y store de texto en `mlruns/`; `--check` y el test lo verifican. No guarda binarios.

> [!question]- ¿Qué afirma esta nota en una frase?
> MLflow es el registro de experimentos con hiperparámetros y métricas; el proyecto tiene 13 runs y el CSV es su exportación, no un sustituto.
