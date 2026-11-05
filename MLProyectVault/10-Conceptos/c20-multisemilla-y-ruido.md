---
tipo: concepto
status: sin-estudiar
tags:
  - multisemilla
  - reproducibilidad
  - metricas
---

# Multisemilla y lectura con ruido

> [!abstract] En una frase
> Una sola corrida es una anécdota: tres semillas dan media y dispersión, y la dispersión es la regla con la que se leen todas las diferencias.

## La idea

TensorFlow en CPU no es determinista bit a bit: la misma configuración con distinta semilla mueve el RMSE ±0.1. Reportar una sola corrida esconde esa banda. El protocolo **multisemilla** entrena con `[42, 7, 123]` y reporta `media ± std`: la media es el resultado, la std es la cota de ruido por debajo de la cual ninguna diferencia significa nada.

## Cómo se lee una tabla con este criterio

- Híbrido-C: media 4.322 ± 0.064 (NB06, ventana test) y 4.330 ± 0.053 (NB05, OOF). Las dos medias caen dentro de la banda de la otra: no hay contradicción, hay ruido.
- Fila oficial 4.338 (semilla 42, en disco): cae dentro de 4.322 ± 0.064. El artefacto desplegado es una muestra típica, no un cherry-pick.
- Regla práctica: diferencias menores que ~0.1 en RMSE con una sola semilla por lado **no se anuncian como mejora**.

## Dónde aparece en este proyecto

- `src/clase/evaluar_c_multisemilla.py` — el script del protocolo [42, 7, 123].
- `resultados/bundle_c_multiseed.csv` y `resultados/comparativa_bundle_c.csv` — la evidencia en disco.
- `models/ds02_manifest.json → metrics.reference_row` — la fila oficial 4.338.
- El mecanismo del ruido: [[c14-ruido-y-reproducibilidad]]; las cifras: [[e00-cifras-autoritativas]].

> [!warning] La trampa
> «Mejoré de 4.34 a 4.30»: con una semilla por lado y ruido ±0.1, eso es indistinguible de cero. Sin std no hay mejora, hay titular. La lista negra de [[e00-cifras-autoritativas]] existe exactamente por este pecado.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Reportamos media de tres semillas porque TensorFlow en CPU mueve el RMSE una décima entre corridas; sin la dispersión, cualquier comparación es teatro».
> «La fila 4.338 del artefacto cae dentro de la media 4.322 más-menos 0.064: el desplegado es típico, no elegido».

## Flashcards

> [!question]- ¿Qué aporta el protocolo multisemilla frente a una sola corrida?
> Media y dispersión sobre [42, 7, 123]: la media es el resultado y la std (±0.064 en NB06) es la cota de ruido por debajo de la cual ninguna diferencia cuenta como mejora.

> [!question]- ¿Contradicen 4.322 (NB06) y 4.330 (NB05) a la fila 4.338?
> No: ambas medias caen dentro de la banda de ruido mutua y la fila oficial cae dentro de 4.322±0.064. Miden poblaciones distintas (ventanas test vs OOF vs una semilla en disco).
