---
tipo: concepto
status: sin-estudiar
tags:
  - validacion
  - out-of-fold
  - folds-agrupados
  - fuga-de-informacion
---

# OOF y validación agrupada: predecir sin haber visto la fila

> [!abstract] En una frase
> Una predicción out-of-fold es la que produce un modelo que no vio esa fila, y agrupar por motor es la única forma de que esa frase sea cierta cuando las filas son ciclos de una misma máquina.

## El problema que resuelve

Un meta-aprendiz aprende a partir de las predicciones de los modelos base. Si esas predicciones se generaron con los mismos datos con los que se ajustó el meta, el meta no aprende a corregir: aprende a copiar. La firma del defecto es una mejora imposible en validación y un rendimiento normal en test.

Con datos de degradación hay un segundo problema, más sutil. Las filas no son independientes. Todos los ciclos de un motor comparten nivel de RUL, régimen de vuelo y estado físico: dos ventanas del mismo motor a ciclos vecinos son casi la misma ventana.

## Cómo funciona

**Out-of-fold.** Se parte el conjunto en $K$ grupos, se entrenan $K$ modelos —cada uno dejando un grupo afuera— y cada fila recibe la predicción del modelo que no la vio. El resultado es una columna completa de predicciones honestas, una por fila, sin gastar datos en un holdout separado.

**Validación agrupada.** La partición se hace sobre unidades únicas, no sobre filas. `grouped_folds` baraja las unidades y las reparte en tercios (`src/ds02_rul/stacking.py:146`). Con `K = 3` el ajuste ve cuatro motores y la puntuación ve los dos restantes.

| Partición | Qué pasa | Síntoma |
|---|---|---|
| aleatoria por fila | ventanas del mismo motor caen en ajuste y en puntuación | validación optimista, test mediocre |
| agrupada por motor | el meta nunca ve un motor que también puntúa | el número de validación se sostiene en test |
| por tramo temporal | el último tramo cubre un rango angosto de RUL | el modelo no aprende el rango completo y test explota |

**Qué se rompe si se mezclan filas del mismo motor.** Dos mecanismos distintos, y conviene separarlos:

1. El modelo aprende el nivel del motor, no la relación entre desgaste y RUL. Cada motor tiene un techo de vida distinto; si una hermana de la misma unidad está en ajuste, el nivel se filtra.
2. El régimen y el desgaste de una unidad son suaves en el ciclo: la fila vecina es casi un duplicado. El error de validación deja de estimar el error sobre motores nuevos.

Por eso el código no confía en la convención: `src/ds02_rul/stacking.py:275` verifica la intersección de unidades entre ajuste y puntuación y levanta `AssertionError` si aparece una sola repetida.

**Los tres folds reales.** Con las seis unidades de dev y semilla 42, el barajado produce `[2, 10]`, `[5, 18]` y `[20, 16]`. Cada fold ajusta el meta sobre los otros cuatro motores y puntúa sobre los dos que quedaron afuera. El `beta` elegido por fold fue `[1.00, 1.00, 0.00]`, con mediana `1.0` e IQR `0.5` ([[e00-cifras-autoritativas]]).

Ese `0.00` no es ruido: en un fold el meta no mejora a la BiLSTM y la selección honesta es apagarlo. El spread es la información, no el promedio.

## Dónde aparece en este proyecto

- `src/ds02_rul/pipeline.py:157` — `oof_base_predictions` genera las predicciones fuera de fold de los modelos base, reajustando por fold.
- `src/ds02_rul/stacking.py:234` — `select_beta_grouped`: ajusta el meta por fold y devuelve el `beta` con su dispersión.
- `src/ds02_rul/stacking.py:344` — las predicciones OOF se guardan para calibrar la banda, porque cada fila fue puntuada por un meta que no la vio.
- El holdout reservado tiene 2 535 ventanas: es todo lo que el meta ve en el protocolo vigente ([[e00-cifras-autoritativas]]).
- El resultado aplicado está en [[s09-oof-y-beta]]; el reparto de unidades, en [[s01-protocolo-honesto]].

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Split aleatorio por fila | Deja ventanas del mismo motor en ajuste y en puntuación; la validación mide memoria |
| K-fold sobre los seis motores de dev | Cara en CPU y, medida, el meta agrupado no transfiere el nivel de vida |
| Holdout por tramo temporal | El último tramo cubre un rango angosto de RUL y el error de test se dispara |
| Usar las unidades de test para ajustar el meta | Es fuga de test; se leen una sola vez, para reportar |

**El experimento del OOF agrupado.** Se probó agrupar el OOF de los cinco motores de ajuste —14 915 ventanas— para ajustar el meta con más filas. La lógica parecía impecable: más datos, meta mejor entrenado, y un `beta` seleccionable de forma honesta porque las predicciones usadas para puntuar serían fuera de muestra.

Se midió y se rechazó. El meta agrupado infló el nivel de predicción sobre la unidad 16, porque los motores de dev viven más ciclos que los de test y el meta aprendió un prior de vida larga que no transfiere. El RMSE de test creció de forma monótona con `beta`: la selección honesta colapsaba a cero y el ensamble desaparecía. La conclusión quedó escrita en el código (`src/ds02_rul/stacking.py:161`) y en el ADR-005.

La lección es incómoda: **más filas no equivalen a mejor mapeo cuando las filas vienen de otro nivel**. Un OOF honesto que alimenta un meta inútil es peor que un holdout chico que alimenta un meta que sí transfiere.

> [!warning] La trampa
> Dos frases que suenan bien y son falsas. "Usé validación cruzada, así que no hay fuga": depende de la unidad de partición, y una K-fold por fila fuga siempre en datos de degradación. "El OOF es más honesto, así que es mejor": honesto describe la estimación, no la utilidad del meta; el experimento de arriba tenía un OOF impecable y produjo un ensamble peor. Y el detalle que hay que decir sin que lo pregunten: la unidad 16 se usa para el early stopping de la BiLSTM y para ajustar el meta; el `beta` por folds corrige la selección, no esa superposición.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Out-of-fold significa que la fila se puntúa con un modelo que no la vio, y agrupar por motor es lo único que hace verdadera esa frase cuando las filas son ciclos de la misma máquina».
> «Los folds no son por fila porque dos ventanas del mismo motor a ciclos vecinos son casi la misma ventana: sin agrupar, la validación mide memoria, no generalización».
> «Probamos agrupar el OOF de los cinco motores de ajuste para tener más filas y lo rechazamos con medición: el meta aprendía un prior de vida que no transfería y el ensamble se apagaba solo».

## Flashcards

> [!question]- ¿Qué es una predicción out-of-fold?
> La que produce un modelo que no fue entrenado con esa fila: se parte en grupos, se entrena un modelo por grupo dejando uno afuera y cada fila recibe la predicción del modelo que la excluyó.

> [!question]- ¿Por qué los folds van por motor y no por fila?
> Porque las filas de un mismo motor no son independientes: comparten nivel de RUL, régimen y estado. Un split por fila deja ventanas casi idénticas en ajuste y en puntuación, y la validación mide memorización.

> [!question]- ¿Qué tres grupos de unidades producen los folds con semilla 42?
> `[2, 10]`, `[5, 18]` y `[20, 16]`; cada uno se puntúa con un meta ajustado sobre los otros cuatro motores.

> [!question]- ¿Por qué se rechazó ajustar el meta sobre el OOF de los cinco motores de ajuste?
> Porque el meta aprendió un nivel de vida de los motores de dev que no transfiere a los de test: infló las predicciones sobre la unidad 16 y el RMSE de test creció con `beta`, así que la selección honesta lo apagaba.

## Conexiones

Antes: [[c09-ensembles]] · Después: [[c11-shrinkage-beta]]
