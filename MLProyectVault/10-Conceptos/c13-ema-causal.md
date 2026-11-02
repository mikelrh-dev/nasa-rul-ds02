---
tipo: concepto
status: sin-estudiar
tags:
  - ema
  - causalidad
  - suavizado
  - series-temporales
---

# Media móvil exponencial causal por motor

> [!abstract] En una frase
> El suavizado del proyecto es una media móvil exponencial que solo usa el presente y el pasado de cada motor, y por eso puede ejecutarse en un motor que todavía no falló.

## El problema que resuelve

La RUL es monótona no creciente dentro de un motor: a más ciclos, menos vida. Un predictor por ventana no lo es. Su salida salta con el ruido local del sensor, y cada salto hacia arriba es una oportunidad de sobreestimar.

Ese error no es simétrico. La métrica de NASA castiga la sobreestimación con una exponencial más empinada que la subestimación, así que una serie ruidosa paga de más aunque su error medio sea correcto (`docs/decisions/ADR-006-causal-ema-smoothing-of-final-prediction.md:13`).

Un filtro centrado resolvería el ruido, pero consumiría muestras futuras. El artefacto tiene que funcionar sobre un motor vivo, de modo que el filtro debe ser causal (`docs/decisions/ADR-006-causal-ema-smoothing-of-final-prediction.md:15`).

## Cómo funciona

La recursión es una media ponderada entre la observación nueva y el estado anterior:

$$
s_t = \alpha\, x_t + (1 - \alpha)\, s_{t-1},
\qquad \alpha = \frac{2}{\text{span} + 1}
$$

Con `span = 5`, el peso de la observación nueva es $\alpha = 1/3$ (`src/ds02_rul/smoothing.py:23`). El parámetro `adjust=False` es lo que hace la recursión causal: cada valor suavizado depende solo de la predicción actual y de las anteriores de ese motor, nunca de las siguientes (`src/ds02_rul/smoothing.py:5`).

El agrupamiento por motor no es un detalle de presentación. El código recorre las unidades una por una, ordena las filas de esa unidad por ciclo y aplica la EMA sobre esa subserie; después escribe los valores en las posiciones originales, de modo que la salida conserva el orden de entrada (`src/ds02_rul/smoothing.py:33`).

Sin esa separación, todas las ventanas forman una sola serie. La predicción de un motor se mezcla con la del siguiente y el resultado sigue pareciendo razonable, que es lo peligroso: `predict` lo advierte y colapsa todo en una pseudo-unidad cuando `units` falta (`src/ds02_rul/ensemble.py:122`).

El suavizado se aplica **después** de la mezcla y **antes** del recorte en cero: corrige la salida del ensamble completo, no el problema de aprendizaje de ninguno de los dos modelos base (`docs/decisions/ADR-006-causal-ema-smoothing-of-final-prediction.md:32`).

El precio es un retardo de aproximadamente `span` ciclos: al comienzo de la vida del motor el suavizado arrastra el nivel inicial y produce un sesgo optimista pequeño, aceptable para RUL y no para una métrica que exija alineación exacta de ciclo (`docs/decisions/ADR-006-causal-ema-smoothing-of-final-prediction.md:72`).

## Dónde aparece en este proyecto

- Función única del módulo, `causal_ema_by_unit`, con `span` por defecto 5 (`src/ds02_rul/smoothing.py:14`).
- En inferencia se llama una vez, sobre la predicción ya mezclada con `beta` (`src/ds02_rul/ensemble.py:158`).
- La ruta de entrenamiento calcula, para cada modelo, la fila de métricas sin suavizar y la suavizada, de modo que la comparación queda registrada en la misma tabla (`src/ds02_rul/pipeline.py:78`).
- El valor enviado es `ema_span = 5` ([[e00-cifras-autoritativas]]); el detalle de la etapa está en [[s07-ema-por-motor]].
- Efecto medido: la rama BiLSTM mejora en RMSE y en NASA cuando se le aplica la EMA (`docs/decisions/ADR-006-causal-ema-smoothing-of-final-prediction.md:40`).

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| No suavizar | Medido: la rama BiLSTM queda peor en RMSE y en NASA; el ruido de discontinuidad se paga |
| Media móvil centrada | Consume muestras futuras; no es desplegable en un motor en vuelo |
| Savitzky-Golay | Conserva picos y suaviza mejor, pero también es centrado: mismo problema de causalidad |
| Filtro de mediana | Quita picos aislados, pero no es un estimador de nivel y deja la estructura de escalón que la exponencial castiga |
| Regresión isotónica por motor | Impone monotonía exacta, pero ajusta la serie completa, incluido el futuro, y no se actualiza de forma incremental |
| Suavizar las entradas o los objetivos | Cambia el problema de aprendizaje y borra los transitorios que la rama de max-pooling existe para capturar |

> [!warning] La trampa
> Causal no significa monótono. La EMA solo mira hacia atrás, pero su salida puede subir si las predicciones recientes suben. La monotonía estricta es otra regla, con otro nombre y otro costo, y vive en la capa de decisión ([[s13-capa-de-reglas-y-decision]]). Confundirlas hace que se defienda una propiedad que el código no tiene.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «El suavizado es causal: cada valor depende del ciclo actual y de los anteriores de ese motor, nunca de los siguientes, así que el mismo código corre en un motor que todavía está volando. Se aplica por motor porque dos motores distintos no comparten nivel de vida: mezclarlos produce números plausibles y falsos. Y el precio está declarado: la EMA introduce un retardo de aproximadamente `span` ciclos al comienzo de la vida.»

## Flashcards

> [!question]- Pregunta de repaso
> ¿Qué hace exactamente `adjust=False` en la recursión?
> Convierte la media en una recursión causal: el valor suavizado en `t` es una mezcla del valor actual y del suavizado en `t-1`. Sin ese ajuste, la media se recalcularía como un promedio ponderado de toda la serie, que no es lo mismo ni tiene el mismo arranque.

> [!question]- Pregunta de repaso
> ¿Por qué el suavizado se aplica por motor y no sobre el lote completo?
> Porque la EMA depende del orden y del nivel de la serie. Si se aplica sobre todas las ventanas juntas, las predicciones de un motor contaminan las del siguiente y el resultado parece válido sin serlo. Además, el orden por ciclo solo tiene sentido dentro de una unidad.

> [!question]- Pregunta de repaso
> ¿Qué ruido quita la EMA y qué introduce?
> Quita el ruido de alta frecuencia: el salto entre ventanas consecutivas por ruido local del sensor. Introduce un retardo de aproximadamente `span` ciclos y una dependencia del orden de presentación: la misma ventana puntuada en otro orden da otro valor.

> [!question]- Pregunta de repaso
> ¿Dónde se aplica la EMA dentro de la cadena y por qué ahí?
> Después de la mezcla con `beta` y antes del recorte en cero. Así corrige la salida del ensamble completo y puede agregarse o quitarse sin reentrenar los modelos base.

> [!question]- Pregunta de repaso
> ¿Por qué la salida de la EMA puede subir si la RUL debería bajar?
> Porque la EMA es un estimador de nivel con memoria, no una restricción de monotonía. Si las predicciones recientes suben, el promedio también sube. La regla monótona es una decisión separada y tiene su propio costo medido.

## Conexiones

Antes: [[c12-conformal-prediction]] · Después: [[c14-ruido-y-reproducibilidad]]
