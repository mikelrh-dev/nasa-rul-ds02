---
tipo: concepto
status: sin-estudiar
tags:
  - shap
  - explicabilidad
  - ia-debil
  - rubrica
  - saa
---

# SHAP e IA débil

> [!abstract] En una frase
> SHAP reparte el mérito de cada predicción entre features; la IA débil recuerda que el sistema solo sabe hacer eso, y por eso es auditable.

## La idea en dos mitades

**SHAP** (*SHapley Additive exPlanations*): cada predicción se descompone en contribuciones aditivas por feature, con fundamento en valores de Shapley de teoría de juegos. El gráfico global ordena features por impacto medio; el local explica un motor concreto («este HANGAR es por T48 alta y fase de crucero»). No mejora el RMSE: lo hace defendible.

**IA débil**: el sistema solo predice RUL de DS02 con lo aprendido de su telemetría. No razona en general, no transfiere a otros dominios, no fija precios ni atiende llamadas (frente a la IA fuerte/AGI, inexistente aquí). Y esa estrechez es la virtud: barata, rápida y auditable. Es el P1 del plan de rúbrica SAA.

## El tipo de aprendizaje (SAA 2)

Supervisado de regresión: cada fila trae su RUL real y el modelo aprende a predecirla (RMSE/MAE/R² contra verdad). Se diferencia del no supervisado en que hay etiqueta y métrica contra verdad: sin RUL no habría ni error que medir ni modelo que elegir. Y es regresión, no clasificación: el objetivo es continuo, así que SMOTE no aplica (no hay clases que balancear) y los umbrales APTO/INSPECCIÓN/HANGAR van después, en reglas.

## Dónde aparece en este proyecto

- `src/clase/shap_clase.py` — genera el diccionario top (`models/shap_xgb_top.joblib`).
- `src/clase/shap_clase_e2.py` — variante del análisis para el MLP E2.
- `app/` — panel SHAP de la app de producción (cada decisión HANGAR lleva su explicación).
- `src/clase/README.md` — sección «Tipo de IA»: débil, supervisada, de regresión.
- El coste de equivocarse sin explicación: [[s13-capa-de-reglas-y-decision]].

> [!warning] La trampa
> «El modelo es explicable porque es un árbol»: no. Un LightGBM de cientos de árboles nadie lo lee a mano; la explicabilidad la pone SHAP encima, no el apellido del algoritmo. Y al revés: SHAP sobre un modelo con fuga explica la fuga con gran elocuencia.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «SHAP no baja el RMSE ni un punto: lo que baja es el coste de equivocarse, porque cada HANGAR llega con su porqué firmado por feature».
> «Es una IA débil a propósito: solo sabe de RUL de DS02, y por eso un taller puede auditarla sin un doctorado».

## Flashcards

> [!question]- ¿Qué explica SHAP y qué no?
> Descompone cada predicción en contribuciones por feature (global: qué manda; local: por qué este motor). No mejora la métrica ni detecta fuga: explica lo que el modelo hace, sea bueno o malo.

> [!question]- ¿En qué se diferencia tu aprendizaje del no supervisado?
> En que cada fila trae su etiqueta (RUL real): hay verdad contra la que medir (RMSE/MAE/R²) y con la que elegir modelo. Sin etiqueta no hay error, ni validación, ni elección posible.

> [!question]- ¿Por qué no usas SMOTE?
> Porque es regresión: el objetivo es continuo y no hay clases desbalanceadas que compensar. El desbalance aquí se llama de otra forma (el motor 14) y se trata con macro-RMSE, no con filas sintéticas.

> [!question]- ¿Qué es una IA débil y por qué se reivindica aquí?
> Un sistema que solo resuelve su tarea entrenada (RUL de DS02), sin razonamiento general. Se reivindica porque la estrechez la hace barata, rápida y auditable: justo lo que un taller necesita.
