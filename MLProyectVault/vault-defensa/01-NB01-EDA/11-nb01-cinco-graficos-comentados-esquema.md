---
title: Esquema — Cinco gráficos comentados
course: Reto 1 · SAA+PIA+MIA
block: 01 — NB01 EDA
node: B1.2
type: esquema
status: en-curso
tags:
  - esquema
  - graficos
---

# Esquema — Cinco gráficos comentados

> Nota de repaso rápido. Teoría completa: [[11-nb01-cinco-graficos-comentados]]

## La idea en una frase
> Cada gráfico termina en una decisión de modelado; si no, es decoración.

## Los cinco tipos
| Tipo | Qué concluyo | Decisión |
|---|---|---|
| Barras | el crucero domina | fase entra como categórica |
| Histograma | RUL con cola | RMSE y macro |
| Boxplot | T48 se separa por fase | sin fase aprendería pilotaje |
| Dispersión | hay regímenes | residualizar sensores |
| Heatmap | sensores correlados, RUL débil | hace falta ventana |

## Sí / No
- ✅ «cinco tipos» con su conclusión debajo.
- ❌ «hice muchos gráficos».
- ❌ vender correlación como causalidad.

## Flashcards #flashcards
- ¿Qué cinco tipos exige la rúbrica? :: barras, histograma, boxplot, dispersión y heatmap.
- ¿Qué decisión sale del heatmap? :: que una fila no basta: hace falta ventana.

## Estado
- [ ] En curso
