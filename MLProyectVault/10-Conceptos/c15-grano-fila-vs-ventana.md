---
tipo: concepto
status: sin-estudiar
tags:
  - grano
  - rubrica
  - saa
---

# Grano — fila vs ventana

> [!abstract] En una frase
> El grano es la unidad que el modelo puntúa: una fila suelta o una ventana de 50 lecturas; mezclar granos en un ranking es comparar peras con manzanas.

## La idea

Una **fila** es una lectura instantánea del motor (un ciclo, 20 columnas). Una **ventana** es una secuencia de 50 lecturas consecutivas del mismo motor: contiene la forma de la degradación, no solo su foto. Un modelo de fila aprende «con estos valores, quedan N ciclos»; un modelo de ventana aprende «con esta trayectoria, quedan N ciclos».

El grano lo decide todo lo demás: qué features existen (una fila no tiene pendiente ni curvatura), qué validación vale (las filas vecinas del mismo motor se parecen) y contra qué baseline se compite.

## Por qué dos granos conviven aquí

El track de clase empieza en grano fila: 5 clásicos + MLP sobre filas imputadas, porque es el grano donde se enseña regresión tabular y donde la rúbrica SAA pide el pipeline sklearn. El híbrido desplegado vive en grano ventana: BiLSTM + LightGBM sobre ventanas de 50, porque la trayectoria degrada mejor que la foto (RMSE 7.72 del MLP E2 frente a 4.338 del híbrido, [[e00-cifras-autoritativas]]).

## La regla de oro (SAA-9)

**Prohibido el ranking mixto.** La tabla final (`src/clase/tabla_final.py:18`, `COLUMNAS` con campo `grano`) pone filas `grano=fila` y `grano=ventana` en la misma tabla para el README pero **nunca las ordena juntas**: cada grano elige su campeón. El campeón fila es el MLP E2; el campeón ventana es el híbrido-C. Decir «el híbrido gana al MLP» sin mencionar el grano es la frase que el tribunal espera cazar.

## Dónde aparece en este proyecto

- `src/clase/tabla_final.py:18` — `COLUMNAS` incluye `grano`; la tabla final lo lleva por fila.
- `src/clase/pipeline_clase.py:22-24` — el pipeline de clase opera en grano fila (19 numéricas + 1 categórica por lectura).
- `src/ds02_rul/features.py:79` — `build_windows` construye el grano ventana `(50, 19)`.
- `src/clase/README.md` — campeones separados por grano; `README.md` filas 102/112, una tabla por grano.
- El pipeline que la consume: [[s16-pipeline-de-clase]]; la tabla final: [[s19-tabla-final-y-grano]].

> [!warning] La trampa
> «Mi modelo tiene menos RMSE, luego es mejor»: sin igualar el grano, la frase no significa nada. Una ventana contiene 50 veces más información que una fila; el RMSE más bajo puede venir del grano, no del modelo.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Grano fila: una lectura, un número. Grano ventana: cincuenta lecturas, una trayectoria. Cada grano tiene su campeón y su tabla; ordenarlos juntos es hacer trampa con el denominador».
> «El MLP E2 es el mejor de su grano, no el mejor a secas: 7.72 contra 4.338, y la diferencia la pone la ventana, no el apellido del algoritmo».

## Flashcards

> [!question]- ¿Qué es el grano de un modelo?
> La unidad que puntúa: una fila (una lectura del motor) o una ventana (50 lecturas consecutivas con su trayectoria de degradación).

> [!question]- ¿Por qué no se pueden ordenar juntos los modelos de fila y de ventana?
> Porque la ventana contiene 50 veces más información que la fila: el RMSE más bajo puede venir del grano y no del modelo. Cada grano elige su campeón por separado (regla SAA-9, campo `grano` en `tabla_final.py:18`).
