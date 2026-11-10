---
title: Mapa indicador → evidencia
course: Reto 1 · SAA+PIA+MIA
block: 12 — Rúbrica
node: G1
indicador: —
descriptor: —
spine: true
status: en-curso
tags:
  - rubrica
  - mapa
---

# Mapa indicador → evidencia

> [!abstract] En una frase
> Diecinueve filas: qué pide la rúbrica, dónde está la nota, qué evidencia la sostiene y qué
> descriptor alcanzamos hoy. Si una fila no tiene evidencia, no se defiende.

## SAA — 75 % de la nota está en modelos

| # | Indicador | Peso | Nota | Evidencia | Hoy |
|---|---|---|---|---|---|
| 1 | IA débil | 5 % | [[02-apertura-30s]] | `README.md:29` compara con AGI | 10 |
| 2 | Tipo de aprendizaje | 10 % | [[02-apertura-30s]] | supervisado/regresión vs no supervisado | 10 |
| 3 | Dataset y campos | 5 % | [[10-nb01-dataset-y-tabla-de-campos]] | tabla + nulos por campo + campos quitados | 10 |
| 4 | Gráficos comentados | 5 % | [[11-nb01-cinco-graficos-comentados]] | 6 PNG + `QUÉ VEO`/`CONCLUSIÓN` en NB01 | 10 |
| 5 | Nulos y variable nueva | 5 % | [[12-nb01-nulos-mar-y-variable-nueva]] | MAR T30 + `fase_vuelo`/`cyc_norm` | 10 |
| 6 | Cinco modelos | 30 % | [[20-nb02-cinco-modelos-y-tiempos]] · [[30-nb03-ablacion-cyc-norm]] | `comparativa.csv` + ablación | 10 |
| 7 | MLP + 3 experimentos | 20 % | [[21-nb02-mlp-base-y-tres-experimentos]] | `mlp_comparativa.csv` con `hipotesis` | 10 |
| 8 | Métricas | 10 % | [[22-nb02-metricas-y-error-de-negocio]] | MAE/RMSE/R² + real vs predicho | 10 |
| 9 | Mejor modelo + SHAP | 5 % | [[23-nb02-eleccion-y-desempate]] · [[70-nb07-shap-aditividad]] | SHAP validación + aditividad | 10 |
| 10 | Pregunta individual | 5 % | [[100-tres-preguntas-individuales]] | código abierto en vivo | 10* |

## PIA — pipeline y app son el 65 %

| # | Indicador | Peso | Nota | Evidencia | Hoy |
|---|---|---|---|---|---|
| 1 | README + docstrings | 10 % | [[80-pia-readme-y-funciones]] | 6 apartados + 0 sin docstring | 10 |
| 2 | Estructura | 10 % | [[81-pia-estructura-de-carpetas]] | tabla de equivalencias | 10 |
| 3 | Pipeline sklearn | 20 % | [[82-pia-pipeline-sklearn]] | `pipeline_clase.py:27` + joblib con pipeline | 10 |
| 4 | MLflow | 20 % | [[83-pia-mlflow]] | 17 runs, export y capturas | **7** |
| 5 | Streamlit | 25 % | [[84-pia-streamlit-test-y-caso-nuevo]] | test + caso nuevo + decisión | 10 |
| 6 | Pregunta individual | 15 % | [[100-tres-preguntas-individuales]] | código abierto en vivo | 10* |

## MIA — n8n pesa el 35 %

| # | Indicador | Peso | Nota | Evidencia | Hoy |
|---|---|---|---|---|---|
| 1 | Negocio con dato | 20 % | [[90-mia-negocio-con-dato-y-objetivo]] | 3,2 ciclos vs 9–23 de margen | 10 |
| 2 | Seis reglas | 30 % | [[91-mia-seis-reglas]] | `src/mia/reglas.py` + `motor.py` | 10 |
| 3 | n8n con acción propia | 35 % | [[92-mia-n8n-rama-propia]] | `POST /n8n-decision` | 10 |
| 4 | Pregunta individual | 15 % | [[100-tres-preguntas-individuales]] | código abierto en vivo | 10* |

\* Las individuales solo valen 10 si se responde **y** se enseña.

## Resumen

| Asignatura | Nota estimada | Techo | Qué la limita |
|---|---|---|---|
| SAA | 10,0 | 10 | nada |
| PIA | 9,4 | 10 | PIA-4 = 7 |
| MIA | 10,0 | 10 | nada |

## Cómo se usa esta tabla

Antes de ensayar: se lee una fila y se dice la respuesta en voz alta. Si la respuesta no sale, se
abre la nota enlazada. Al terminar, se marca la fila con `date:` en la nota.

## Flashcards #flashcards

- ¿Qué indicador está por debajo de 10? :: PIA-4, MLflow, en 7.
- ¿Qué tres indicadores pesan más? :: MIA-3 (35 %), SAA-6 (30 %) y MIA-2 (30 %).
