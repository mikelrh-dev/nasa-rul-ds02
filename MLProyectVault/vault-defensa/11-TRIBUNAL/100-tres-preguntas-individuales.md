---
title: Las tres preguntas individuales
course: Reto 1 · SAA+PIA+MIA
block: 11 — Tribunal
node: F1
indicador: SAA-10, PIA-6, MIA-4
descriptor: 10
spine: true
status: en-curso
tags:
  - tribunal
  - individual
---

# Las tres preguntas individuales

> [!abstract] En una frase
> Después de los 15 minutos, **cada uno responde solo**: una pregunta de SAA, una de PIA y una de
> MIA. El 10 no es «responder bien»: es responder bien, enseñarlo en el código y explicar por qué.

## La fórmula de respuesta (vale para las tres)

1. **Respuesta en una frase.** Sin rodeos.
2. **Dónde está.** `archivo:línea` o «en este run».
3. **Por qué así.** La decisión, con su alternativa.
4. **Qué límite tiene.** Una frase honesta.

Si no se enseña el código o el resultado, el máximo es 7. Por eso hay que **llevar las pestañas
abiertas** antes de empezar ([[03-checklist-dia-D]]).

## SAA — las tres más probables

| Pregunta | Respuesta núcleo | Dónde lo enseño |
|---|---|---|
| «¿Cómo elegiste el modelo y usaste el test?» | Validación, desempate al más simple, test una vez | `train_clasicos.py:145` · `train_mlp.py:107` |
| «¿Cómo evitaste la fuga?» | Split por motor, escalado solo en train, OOF para el meta | `pipeline_clase.py:27` · `stocking`/`stacking.py` |
| «¿Qué explica SHAP y con qué control?» | Aportes con aditividad a 1e-5 sobre validación | `shap_clase.py` (`check_aditividad`) |

## PIA — las tres más probables

| Pregunta | Respuesta núcleo | Dónde lo enseño |
|---|---|---|
| «Enséñame el pipeline y por qué está dentro del artefacto» | `ColumnTransformer` + estimador en un `Pipeline`; el joblib lo incluye | `pipeline_clase.py:27` · `models/*.joblib` |
| «¿Dónde registras los experimentos?» | 17 runs con params y métricas + export CSV | `mlruns/` · `docs/evidencia/mlflow/` |
| «¿Qué hace la app con un caso nuevo?» | Predice, muestra `L_inf` y la decisión con su regla | `app/dashboard_ds02.py` · `_tab_motor.py` |

## MIA — las tres más probables

| Pregunta | Respuesta núcleo | Dónde lo enseño |
|---|---|---|
| «¿Qué regla manda y por qué?» | La de seguridad (prioridad 10): dato inválido, no se decide | `src/mia/reglas.py` · `motor.py` |
| «¿Qué hace n8n que no se vio en clase?» | `POST /n8n-decision` a nuestra API, con token e idempotencia | `app/api.py:262` · `n8n/flujo.json` |
| «¿Qué mejora para la empresa?» | Aviso 9–23 ciclos antes con 3,2 de error típico | `README.md:21` · manifiesto |

## Errores que bajan la nota

| Error | Efecto |
|---|---|
| Responder en general, sin «en mi proyecto…» | El 3 de la rúbrica |
| Decir «lo hizo mi compañero» | Cero: la pregunta es individual |
| No saber abrir el archivo | Techo de 7 |
| Inventar una cifra | Pierdes credibilidad en las tres |

## Di esto en el tribunal

> «Lo tengo medido y lo enseño: validación para elegir, test una vez, pipeline dentro del artefacto
> y la decisión la gobierna la regla de seguridad.»

## Flashcards #flashcards

- ¿Qué cuatro partes tiene una respuesta individual? :: frase, dónde está, por qué así y qué límite tiene.
- ¿Qué pasa si no enseñas el código? :: el máximo es 7 aunque la respuesta sea correcta.
