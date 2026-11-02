---
tipo: concepto
status: sin-estudiar
tags:
  - shrinkage
  - stacking
  - beta
  - out-of-fold
---

# Shrinkage beta — interpolar campeón y meta-aprendiz

> [!abstract] En una frase
> El híbrido no es el meta-aprendiz: es una interpolación entre el campeón BiLSTM y el meta-aprendiz, y el peso de esa interpolación se elige fuera de muestra.

## El problema que resuelve

Dos modelos base con sesgos inductivos distintos se combinan con un meta-aprendiz ([[c09-ensembles]]). El meta-aprendiz puede fallar: se ajusta sobre pocas filas y su error no queda acotado por el de los modelos que combina.

Un promedio convexo de pesos fijos tampoco alcanza. Solo mejora a su mejor componente cuando los errores de las dos ramas están correlacionados de forma negativa; con errores correlacionados de forma positiva, hereda el sesgo de la rama dominante y suma la varianza de la otra (`docs/decisions/ADR-001-reject-linear-blending-adopt-learned-stacking.md:28`).

La interpolación resuelve un problema distinto: acota el daño. Si el meta-aprendiz resulta peor que el campeón, el sistema puede volver al campeón sin reentrenar nada.

## Cómo funciona

Se define un único parámetro `beta` en el intervalo cerrado $[0, 1]$:

$$
p_{raw} = p_{lstm} + \beta \,(p_{meta} - p_{lstm})
        = \beta\, p_{meta} + (1 - \beta)\, p_{lstm}
$$

Los dos extremos son contratos, no aproximaciones:

| `beta` | Predicción resultante | Lectura |
|---|---|---|
| `0` | `p_lstm` | el campeón, exacto |
| `1` | `p_meta` | el meta-aprendiz puro |
| intermedio | mezcla | el meta corrige al campeón con peso acotado |

El grid es fijo: 21 valores equiespaciados entre 0 y 1, un paso de 0,05 (`src/ds02_rul/stacking.py:25`). Para cada valor se calcula un criterio que suma dos cocientes relativos al BiLSTM de ese mismo fold: RMSE dividido por el RMSE del campeón, más NASA dividido por el NASA del campeón (`src/ds02_rul/stacking.py:317`). Se elige el mínimo.

La selección no es única. Los motores de desarrollo se parten en tres folds agrupados, deterministas para una semilla (`src/ds02_rul/stacking.py:146`). El meta-aprendiz que puntúa un fold se ajusta solo con los otros folds, y una aserción aborta si una unidad aparece a la vez en ajuste y en puntuación (`src/ds02_rul/stacking.py:275`). Cada fold devuelve su propio `beta`; el valor final es la mediana de los tres (`src/ds02_rul/stacking.py:337`).

## Dónde aparece en este proyecto

- El valor enviado es `beta = 1.0`, con folds `[1.00, 1.00, 0.00]`, mediana `1.0` e IQR `0.5` ([[e00-cifras-autoritativas]]).
- La interpolación se aplica en inferencia en una sola línea: `src/ds02_rul/ensemble.py:157`.
- La selección completa, con el vector de folds y la tabla por fold, vive en [[s09-oof-y-beta]].
- El objeto que la consume y la expone en `predict` está en [[s10-stacking-hibrido]].
- `beta = 1.0` implica que la predicción final **es** la salida del meta-aprendiz; el campeón sobrevive como ingrediente (`README.md:111`).

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Pesos fijos, por ejemplo 0,6 LightGBM / 0,4 BiLSTM | Medido peor que el mejor componente en RMSE y en NASA; es el caso de correlación positiva de errores |
| Pesos por varianza inversa sobre validación | Mejor que los pesos fijos, todavía peor que el BiLSTM solo; los pesos dependen del ruido de validación, no de la estructura complementaria |
| `beta` elegido in-sample | El meta puntúa filas con las que fue ajustado: el criterio se desploma y empuja `beta` al máximo del grid (`src/ds02_rul/stacking.py:4`) |
| `beta` elegido sobre el test | Sería elegir sobre la lectura confirmatoria, que se lee una sola vez |

> [!warning] La trampa
> Tres folds que eligen `[1, 1, 0]` no son "beta = 1 con ruido". Significan que un tercio de la evidencia no encontró valor en el meta. La mediana tapa ese desacuerdo; el IQR de `0.5` lo publica. Un promedio habría dado un valor que ningún fold eligió.

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «`beta` no es un hiperparámetro decorativo: es el seguro del sistema. Con `beta = 0` la predicción es exactamente el campeón BiLSTM, así que el meta-aprendiz nunca puede empeorar el resultado sin que la selección lo autorice. Y esa selección se hace fuera de muestra, porque elegir `beta` sobre las filas que ajustaron el meta es medir la memoria del meta, no su utilidad.»

## Flashcards

> [!question]- Pregunta de repaso
> ¿Qué predicción devuelve el sistema con `beta = 0` y qué devuelve con `beta = 1`?
> Con `beta = 0` devuelve `p_lstm`, el campeón, de forma exacta. Con `beta = 1` devuelve `p_meta`, la salida del meta-aprendiz sin mezcla.

> [!question]- Pregunta de repaso
> ¿Por qué se toma la mediana de los folds y no el promedio?
> Porque un fold puede no encontrar valor en el meta y elegir `0`. La mediana reporta el valor que la mayoría de los folds sostiene; el promedio fabricaría un valor intermedio que ningún fold eligió. El IQR acompaña a la mediana para no esconder el desacuerdo.

> [!question]- Pregunta de repaso
> ¿Qué criterio decide `beta` y por qué tiene dos términos?
> La suma de RMSE relativo y NASA relativo al BiLSTM del fold. Un solo término elegiría un modelo que gana en error cuadrático y castiga mal las sobreestimaciones; el NASA score es exponencial y asimétrico, así que se pondera junto al RMSE.

> [!question]- Pregunta de repaso
> ¿Qué defecto concreto tiene elegir `beta` in-sample?
> El meta-aprendiz se ajusta y se puntúa sobre las mismas filas. Memoriza, el cociente RMSE contra el campeón cae muy por debajo de 1 y el criterio empuja `beta` al máximo del grid. Ese cociente anómalamente bajo es la firma del defecto, no una mejora.

## Conexiones

Antes: [[c10-oof-y-validacion-agrupada]] · Después: [[c12-conformal-prediction]]
