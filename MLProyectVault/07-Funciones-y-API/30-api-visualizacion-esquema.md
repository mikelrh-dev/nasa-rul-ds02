---
title: Esquema — API Visualización
course: DS02-RUL
block: B7 — Funciones y API
node: N30
type: esquema
status: en-curso
tags:
  - esquema
  - api
  - viz
---

# Esquema — API Visualización

> Teoría completa: [[30-api-visualizacion]]

## La idea en una frase

> viz.py = pincel del tribunal: 22 funciones (tablas, barras, scatter, residuos, tramos, curvas, beta por fold). 7 sin nodo previo.

## Tablas vs gráficos

| Tablas | Gráficos |
|---|---|
| nombre_corto, tabla_modelos, comparar_con_base, tabla_por_motor, evaluar_clase, mostrar_clase | barras_metricas, dispersion_por_semilla, barras_ablacion, real_vs_predicho, residuos, error_por_tramo, curva_entrenamiento, beta_por_fold |

## Sí / No

- ✅ residuos ≠ error_por_tramo (distribución vs por tramo).
- ❌ barras_ablacion no mejora el modelo, mide el efecto.

## Flashcards #flashcards

- ¿Error por tramo? :: error_por_tramo.
- ¿Comparar modelos? :: tabla_modelos.
- ¿Dispersión por semilla? :: dispersion_por_semilla.

## Estado

- [ ] En curso
