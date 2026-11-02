---
tipo: sistema
status: sin-estudiar
tags:
  - preproceso
  - fuga
  - scaler
---

# Preproceso sin fuga — scaler y ridges

> [!abstract] En una frase
> Todo lo que resta y centra se ajusta solo con los cinco motores de ajuste.

## Contrato

| Entra | Sale |
|---|---|
| W y Xs crudos de los motores de ajuste | Scalers y 14 ridges ajustados, listos para transformar |
| Filas de holdout y test | Las mismas transformaciones aplicadas, sin reajustar |

## Cómo está implementado

El ajuste vive en `src/ds02_rul/features.py:25` con la exigencia literal de «ONE split only».

| Objeto | Qué ajusta | Dónde |
|---|---|---|
| Scaler de 18 canales | Medias y varianzas de W + Xs | `src/ds02_rul/features.py:25` |
| 14 ridges de grado 2 | Sensor en función del régimen | `src/ds02_rul/features.py:25` |
| Reajuste por fold | Scalers y ridges propios por fold | `src/ds02_rul/pipeline.py:157` |
| Guarda anti-fuga | Excepción si un fold comparte unidad | `src/ds02_rul/stacking.py:275` |

Antes se ajustaba con las seis unidades de desarrollo: 52 635 filas. Ahora solo con ajuste: 44 982 filas. El holdout queda limpio de punta a punta, no solo para los pesos ([[c03-fuga-de-informacion]]).

Cada fold reagrupa motores enteros (`src/ds02_rul/stacking.py:146`) y reajusta sus transformaciones. Sin ese reajuste, la transformación seguiría viendo las filas puntuadas aunque los pesos no las vieran.

## La decisión que hay detrás

ADR-002 elige Ridge de grado 2 para quitar el régimen: suficiente para capturar la no linealidad del vuelo sin memorizar el motor. Un polinomio mayor o un modelo flexible aquí sería fuga disfrazada de capacidad.

Se rechazó ajustar con dev completo «porque da mejor validación»: eso es exactamente la firma de la fuga. La validación mejora y el test empeora.

## Qué medimos

No hay métrica propia de esta etapa, pero su efecto es medible: con fuga en el preproceso la validación sube de forma artificial. El número sano del pipeline es ≈4.34 ± 0.10 con fila de disco 4.251 ([[e00-cifras-autoritativas]]).

El scaler deja 18 canales listos y la residualización deja 14 sensores limpios para ventanas y features ([[s04-ventanas-y-features]]).

## El límite

> [!warning] Lo que esta etapa no arregla
> Un preproceso limpio no compensa un fold mal armado. Si el fold parte por filas, la fuga vuelve por la puerta de atrás aunque el scaler sea honesto. Ambas defensas tienen que estar activas.

## Di esto en el tribunal

> [!quote]
> «El escalador y los 14 ridges se ajustan solo con 44 982 filas de los cinco motores de ajuste. El holdout no entra ni en una media. Y cada fold reagrupa motores y reajusta todo, con una guarda que aborta si una unidad aparece en los dos lados.»

## Flashcards

> [!question]- ¿Con cuántas filas se ajusta el preproceso?
> Con 44 982, solo motores de ajuste. Antes eran 52 635 con holdout incluido.

> [!question]- ¿Qué exige el docstring de features.py:25?
> «ONE split only»: un solo split para ajustar, nunca dev completo.

> [!question]- ¿Qué hace stacking.py:275?
> Levanta una excepción si un fold comparte una unidad entre ajuste y puntuación.

> [!question]- ¿Por qué se reajusta por fold?
> Porque si la transformación viera las filas puntuadas, la validación dejaría de ser out-of-sample.

> [!question]- ¿Qué afirma esta nota en una frase?
> Todo lo que resta y centra se ajusta solo con los cinco motores de ajuste.

> [!question]- ¿Cómo la contarías en el tribunal?
> «El escalador y los 14 ridges se ajustan solo con 44 982 filas de los cinco motores de ajuste. El holdout no entra ni en una media. Y cada fold reagrupa motores y reajusta todo, con una guarda que aborta si una unidad aparece en los dos lados.»

> [!question]- ¿Qué archivo respalda esta nota?
`src/ds02_rul/features.py:25`

## Conexiones

Antes: [[s02-datos-ds02-y-reparto]] · Después: [[s04-ventanas-y-features]] · Mecanismo: [[c03-fuga-de-informacion]]
