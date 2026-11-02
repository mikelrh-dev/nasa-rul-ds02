---
tipo: sistema
status: sin-estudiar
tags:
  - oof
  - beta
  - validacion
---

# OOF y beta — selección honesta del shrinkage

> [!abstract] En una frase
> Beta se elige con folds que separan motores enteros, y el meta nunca se puntúa donde se ajustó.

## Contrato

| Entra | Sale |
|---|---|
| 5 motores de ajuste y 3 folds agrupados | Predicciones OOF por ventana |
| Grid `beta` en [0, 1] | `beta = 1.0` con mediana 1.0 e IQR 0.5 |

## Cómo está implementado

El OOF vive en `src/ds02_rul/pipeline.py:157` y la selección en `src/ds02_rul/stacking.py:234`.

| Pieza | Qué hace | Dónde |
|---|---|---|
| Folds agrupados | Separan motores enteros, nunca filas | `src/ds02_rul/stacking.py:146` |
| Reajuste por fold | Scalers y ridges propios por fold | `src/ds02_rul/pipeline.py:157` |
| Guarda | Aborta si una unidad aparece en ambos lados | `src/ds02_rul/stacking.py:275` |
| Meta en holdout | RidgeCV + LGBM somero en unidad 16 | `src/ds02_rul/stacking.py:192` |
| Shrinkage | `p = p_lstm + beta · (p_meta − p_lstm)` | `src/ds02_rul/ensemble.py:49` |

Los folds dan `[1.00, 1.00, 0.00]`: dos piden meta completo y uno pide campeón puro. La mediana es 1.0 con IQR 0.5 (`models/ds02_manifest.json`). No es unanimidad: es mayoría con un disidente.

El criterio combina RMSE y NASA relativos al BiLSTM sobre el grid `linspace(0, 1, 21)`. El meta se ajusta en la 16 y `beta` se puntúa fuera: separar ambas preguntas evita que el meta se lea su propia respuesta ([[c10-oof-y-validacion-agrupada]]).

## La decisión que hay detrás

ADR-007 fija este protocolo tras el fallo del cuaderno original, que ajustaba y puntuaba en la 16 y obtenía validación absurda con `beta` en el extremo. La defensa 3 de [[c03-fuga-de-informacion]] nace de ese error.

Se rechazó elegir `beta` contra el test: sería ajustar el despliegue. ADR-007 lo prohíbe explícitamente.

## Qué medimos

`beta` vigente 1.0, folds `[1.00, 1.00, 0.00]`, mediana 1.0, IQR 0.5 ([[e00-cifras-autoritativas]]). El híbrido con este `beta` da ≈4.34 ± 0.10 con fila 4.251.

Que `beta` sea 1.0 no significa que el campeón sobre: significa que, en esta partición, el meta aporta más que el ancla en dos de tres folds.

## El límite

> [!warning] Lo que beta 1.0 no promete
> Un fold pide 0.00: hay un motor donde el meta no ayuda. Si el test se pareciera a ese fold, beta 1.0 sufriría. El shrinkage acota el daño pero no lo elimina. Por eso se cita el IQR, no solo la mediana.

## Di esto en el tribunal

> [!quote]
> «Beta se elige con folds por motor, fuera de donde se ajusta el meta. Da 1.0 con mediana 1.0, pero un fold pide 0. Hay disenso y lo enseño: el meta ayuda en dos de tres particiones.»

## Flashcards

> [!question]- ¿Dónde se ajusta el meta y dónde se elige beta?
> El meta en la unidad 16; beta con OOF agrupado sobre ajuste.

> [!question]- ¿Qué valores dan los folds?
> `[1.00, 1.00, 0.00]`, mediana 1.0 e IQR 0.5.

> [!question]- ¿Qué fórmula aplica beta?
> `p = p_lstm + beta · (p_meta − p_lstm)`; beta 0 es el campeón puro.

> [!question]- ¿Qué guarda evita la fuga en folds?
> `stacking.py:275` aborta si una unidad aparece en ambos lados.

> [!question]- ¿Qué afirma esta nota en una frase?
> Beta se elige con folds que separan motores enteros, y el meta nunca se puntúa donde se ajustó.

> [!question]- ¿Cómo la contarías en el tribunal?
> «Beta se elige con folds por motor, fuera de donde se ajusta el meta. Da 1.0 con mediana 1.0, pero un fold pide 0. Hay disenso y lo enseño: el meta ayuda en dos de tres particiones.»

## Conexiones

Antes: [[s08-ablacion-cyc-norm]] · Después: [[s10-stacking-hibrido]] · Mecanismo: [[c11-shrinkage-beta]]
