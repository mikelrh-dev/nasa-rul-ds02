---
tipo: notebook
status: sin-estudiar
tags:
  - nb05
  - conformal
  - multisemilla
  - lgbm-adaptada
---

# NB05 — Conformal, multisemilla y LGBM adaptada

> [!abstract] En una frase
> La banda se calibra honesta, el número se repite en tres semillas y la LGBM sola prueba la base imputada: el puente al bundle C.

## Antes de empezar

42 celdas. Requiere beta y ensamble de NB04. Tres bloques independientes: evidencia multisemilla, diagnósticos por motor y prototipo LGBM sobre base adaptada.

## Recorrido celda a celda

| Bloque | Qué entra | Qué hace | Qué sale |
|---|---|---|---|
| Línea base | prosa + manifiesto | fija la cifra autoritativa y la regla del empate | media vs fila, sin contradicciones |
| Fases B1 / B4 (celdas 9-10) | `p_ens`, `lo/hi` de test | B1: trayectoria por motor con banda (real vs predicha por ciclo); B4: cobertura real vs 90% nominal por motor | B1: la verde sigue a la negra dentro de la sombra; B4: 100% en 11/14/15 con anchos 27.6 / 26.8 / 26.5 |
| Tabla línea base (celda 11) | manifiesto C | fila oficial 4.338 (seed 42) frente a 3 semillas | RMSE 4.338, MAE 3.227, R2 0.9461, NASA 2336.2; macro 5.0153 (11: 3.633 · 14: 8.576 · 15: 2.837). Nota de autoridad: 4.347±0.012 sustituido por NB05 4.330±0.053 y NB06 4.322±0.064 **(impresas, NO reconciliadas con el CSV en disco — 4.368 pendiente per [[e00-cifras-autoritativas]]; oficial 4.338 semilla 42)** |
| Mejora sobre bases | tabla | cada modelo contra su baseline | deltas negativos en RMSE |
| Regla del empate | resta 1.º−2.º | diferencia menor que el ruido = empate | criterio escrito, no opinado |
| Diagnóstico | residuales por motor | dónde falla (el 14, siempre el 14) | vistas + macro-RMSE |
| Beta y ensamble | referencia a NB04 | no se repite: se enlaza | evita duplicar entrenos |
| LGBM adaptada | base MAR+ffill | LightGBM cuantil sobre 93 columnas residualizadas | **7.067**: la base imputada no degrada |
| Real vs predicho adaptada | test 11/14/15 | scatter + análisis por motor | puente honesto al bundle C |

## Las 5 celdas que importan

1. Línea base: TensorFlow en CPU no es bit a bit determinista; la prosa fija qué cifra manda.
2. Regla del empate: si la diferencia no supera el ruido, es empate aunque haya un número menor.
3. Diagnóstico por motor: el RMSE global esconde al 14; el macro lo revela.
4. LGBM adaptada 7.067: el número que autoriza a construir el híbrido-C encima.
5. Glosario ventana/grano/GroupKFold: el vocabulario mínimo del tribunal.

## Qué NO hace este cuaderno

No reentrena la BiLSTM (viene de NB04), no congela el artefacto final (eso es NB06). NB05 evidencia y prototipa.

## Conexiones

- Multiseed: [[c20-multisemilla-y-ruido]] · LGBM adaptada: [[s18-lgbm-adaptada]] · conformal: [[c12-conformal-prediction]] y [[s11-banda-conformal]] · cifras: [[e00-cifras-autoritativas]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «En el 05 repetimos en tres semillas para saber cuánto es ruido, diagnosticamos por motor para saber dónde duele, y probamos la base imputada sola antes de construir el híbrido encima».

## Flashcards

> [!question]- ¿Qué tres cosas evidencia NB05?
> La estabilidad (multisemilla [42,7,123]), el diagnóstico por motor (el 14 concentra el error) y el puente honesto (LGBM 7.067 sobre base adaptada sin degradación).

> [!question]- ¿Qué es la regla del empate?
> Si la diferencia de RMSE entre 1.º y 2.º no supera la banda de ruido (~0.1), se declara empate: el número menor sin significancia es titular, no mejora.
