---
title: Banco de preguntas
course: Reto 1 · SAA+PIA+MIA
block: 11 — Tribunal
node: F2
indicador: —
descriptor: —
spine: false
status: en-curso
tags:
  - tribunal
  - preguntas
---

# Banco de preguntas

> [!abstract] En una frase
> Treinta y seis respuestas de una línea: si sabes decirlas sin pensar, el resto es conversación.

## NB01 — datos

| Pregunta | Respuesta |
|---|---|
| ¿Qué predices exactamente? | RUL: ciclos que le quedan al motor |
| ¿Cuántas unidades? | 9: 5 ajuste, 1 holdout, 3 test |
| ¿Por qué hay nulos si el dataset no trae? | Inyectados: MAR en T30, auditado, seed 7 |
| ¿Los nulos son al azar? | No: dependen de altitud y Mach (MAR) |
| ¿Qué variable nueva creaste? | `fase_vuelo`, `cyc_norm` y residualización |
| ¿Por qué residualizas? | Para que el sensor mida degradación, no pilotaje |

## NB02 — modelos

| Pregunta | Respuesta |
|---|---|
| ¿Cuántos modelos clásicos? | Cinco, mismo pipeline y mismo split |
| ¿Cuál gana y con cuánto? | XGBoost, 8,217 en validación |
| ¿Y el MLP? | Base + 3 experimentos; gana E2 con 7,340 |
| ¿Por qué E2? | Regularización: el problema era varianza |
| ¿Por qué no SMOTE? | Es regresión, no clasificación |
| ¿Cuántas veces viste el test? | Una, con el elegido |

## NB03–NB05

| Pregunta | Respuesta |
|---|---|
| ¿Qué pasa sin `cyc_norm`? | BiLSTM 5,796 → 6,563; LGBM 7,067 → 6,297 |
| ¿Qué es OOF? | Predicciones fuera de fold: 14 915 ventanas puras |
| ¿Por qué la 16 no es test? | Es holdout del meta, no se usa para medir |
| ¿Qué beta usas? | 1,0 de mediana, folds 1,00/1,00/0,00, IQR 0,5 |
| ¿Por qué el meta y no un promedio? | El promedio arrastra la rama que falla |
| ¿Qué cubre la banda? | 100 % en test, 26,41 de ancho: cota conservadora |

## NB06–NB07

| Pregunta | Respuesta |
|---|---|
| ¿De dónde sale el 4,34? | Cascada: 7,07 → 5,65 → 5,62 → 4,34 |
| ¿Y el 5,02? | Macro: cada motor pesa 1/3 |
| ¿Por qué el 14 falla más? | Menos ventanas (760) y degradación abrupta |
| ¿SHAP en test o validación? | Validación, con aditividad a 1e-5 |
| ¿Qué variables pesan? | `cycle` y `T50`, coinciden con permutación |
| ¿El 4,34 es media? | No: semilla 42 en disco; media 4,324 ± 0,107 |

## PIA

| Pregunta | Respuesta |
|---|---|
| ¿Dónde está el preprocesado? | En el `Pipeline`, ajustado solo en train |
| ¿El joblib preprocesa? | Sí: incluye el pipeline completo |
| ¿Cuántos runs en MLflow? | 13, con params y métricas; falta la ablación |
| ¿Dónde está `src/reglas.py`? | `src/mia/reglas.py`; el motor en `motor.py` |
| ¿La app reentrena? | No: carga el artefacto congelado |

## MIA

| Pregunta | Respuesta |
|---|---|
| ¿Cuántas reglas hay? | Seis, con prioridad y porqué |
| ¿Cuál manda? | `R1_SEGURIDAD`, prioridad 10 |
| ¿Por qué 25 y 30? | Salen de la calibración de la banda |
| ¿Qué hace n8n de distinto? | Llama a nuestra API y registra la decisión |
| ¿Está en producción? | No: instancia local con ejecuciones reales |

## Cómo se ensaya

Se tapa la columna de respuestas y se contestan en voz alta, 10 segundos cada una. Las que no
salgan se marcan y se vuelven al día siguiente. Objetivo: 30 de 36 sin mirar.

## Flashcards #flashcards

- ¿Cuál es la respuesta si preguntan «cuántas veces viste el test»? :: una, solo con el modelo elegido.
- ¿Qué diferencia hay entre 4,34 y 5,02? :: 4,34 es el global y 5,02 el macro: cada motor pesa 1/3.
