---
tipo: concepto
status: sin-estudiar
tags:
  - ensembles
  - stacking
  - blending
  - boosting
---

# Ensembles: bagging, boosting, stacking y blending

> [!abstract] En una frase
> Un ensemble combina modelos, y lo que decide si la combinación sirve no es cuántos modelos hay sino si sus errores son distintos.

## El problema que resuelve

El proyecto tiene dos ramas que leen la misma ventana de formas incompatibles: un árbol sobre un resumen plano de la ventana y una red recurrente sobre la trayectoria ordenada. La tentación inmediata es promediarlas con pesos. Ese promedio tiene una condición matemática que casi nunca se cumple, y cuando no se cumple empeora al mejor componente.

La pregunta correcta no es "¿cómo combino?", sino "¿los dos modelos se equivocan en los mismos lugares?".

## Cómo funciona

| Familia | Qué combina | Cómo lo hace | Qué reduce | Cuándo sirve |
|---|---|---|---|---|
| bagging | copias del mismo modelo | muestras bootstrap en paralelo, promedio | varianza | modelos inestables de alta varianza |
| boosting | árboles secuenciales | cada árbol corrige el residuo del anterior | sesgo | datos tabulares con interacciones |
| stacking | modelos distintos + meta-aprendiz | el meta se entrena sobre predicciones out-of-fold | sesgo y varianza | cuando los errores base son poco correlacionados |
| blending | igual, con holdout reservado | el meta se entrena sobre una porción apartada | lo mismo, con menos datos | cuando el OOF es caro o contaminado |

La diferencia entre stacking y blending es de dónde salen las filas del meta-aprendiz: el stacking estricto usa predicciones out-of-fold de todas las filas; el blending reserva un holdout y el meta solo ve esa porción. Este proyecto reserva la unidad 16 y ajusta el meta sobre ella, así que en sentido estricto es un blending con meta aprendido, aunque el código y los ADR lo llamen stacking. La distinción importa porque explica el costo: el meta ve 2 535 ventanas y nada más ([[e00-cifras-autoritativas]]).

**Por qué un promedio convexo falla.** Con $p = w\,p_a + (1-w)\,p_b$, la varianza del error combinado es

$$\sigma^2 = w^2\sigma_a^2 + (1-w)^2\sigma_b^2 + 2w(1-w)\rho\,\sigma_a\sigma_b$$

Si $\rho > 0$, el promedio hereda el sesgo de la rama dominante y le suma la varianza de la otra. Solo gana cuando $\rho$ es marcadamente negativa. En las dos primeras iteraciones del proyecto las ramas leían la misma señal contaminada, sus errores estaban correlacionados positivamente y todo promedio directo quedó por debajo del mejor componente.

**Cómo es el meta de este proyecto.** Dos meta-aprendices de capacidad deliberadamente baja sobre el diseño `Z = [p_lstm, p_lgb]`:

- `RidgeCV` con 20 valores de `alpha` en escala logarítmica (`src/ds02_rul/stacking.py:95`).
- `LGBMRegressor` superficial: profundidad 3, 7 hojas, 120 árboles, tasa 0.03 (`src/ds02_rul/stacking.py:115`).
- Reconciliación fija 50/50 entre ambos (`src/ds02_rul/stacking.py:184`), aplicada igual en inferencia (`src/ds02_rul/ensemble.py:153`).

El resultado es `p_meta`. Después entra el encogimiento: `p = p_lstm + beta·(p_meta − p_lstm)`, con `beta = 1.0` seleccionado ([[c11-shrinkage-beta]]). La BiLSTM es el campeón porque `beta = 0` la reproduce exactamente y acota el daño de un meta mal especificado.

## Dónde aparece en este proyecto

- `src/ds02_rul/stacking.py:84` — `fit_meta` ajusta ridge y árbol y guarda el soporte que vieron.
- `src/ds02_rul/stacking.py:128` — `predict_meta` aplica el meta respetando su especificación.
- `src/ds02_rul/ensemble.py:144` — en inferencia se mira `n_features_in_` del meta: si espera tres columnas, se agrega el ciclo normalizado.
- `src/ds02_rul/ensemble.py:157` — la mezcla con `beta` y, en la línea siguiente, el suavizado causal.
- El objeto completo, con `predict` y `predict_interval`, está en [[s10-stacking-hibrido]]; los ADR que lo deciden, en [[e01-adr-index]].

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Pesos fijos elegidos a mano | Medido peor que su mejor componente en RMSE y en NASA; la combinación convexa no tiene por qué mejorar |
| Pesos por varianza inversa | Adapta el peso al ruido de validación, no a la estructura complementaria; siguió por debajo de la BiLSTM |
| Champion-challenger (BiLSTM y el árbol como respaldo) | Renuncia a la ganancia medida del híbrido y deja la rama tabular sin aportar |
| Stacking puro, sin encogimiento | Le entrega el control total de la salida al meta, sin cota sobre su daño |
| Un solo meta-aprendiz (solo árbol) | Con 2 535 filas y 2 meta-atributos, la capacidad es justo lo que hay que limitar; el árbol ya sobreajusta |
| Random Forest, k-NN o AdaBoost como ramas | Ninguno expresa el cuantil asimétrico que premia la métrica NASA ni respeta el orden temporal (`docs/decisions/ADR-004-gradient-boosting-and-ridge-over-classical-models.md:21`) |

> [!warning] La trampa
> Dos afirmaciones fáciles de hacer y difíciles de sostener. Primera: "el stacking mejora porque combina dos modelos". Mejora solo si los errores son diversos, y en este proyecto la diversidad se infiere de la mejora del híbrido, no de un diagnóstico de correlación de residuos que nunca se corrió. Segunda: "beta = 1.0 está validado". En la versión original la grilla se puntuó sobre las mismas filas que ajustaron el meta; hoy se selecciona por folds agrupados, pero el `1.0` sigue siendo un valor que conviene explicar con esa historia, no citar como si fuera una validación limpia ([[c10-oof-y-validacion-agrupada]]).

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Un promedio ponderado solo le gana a su mejor componente si los errores están correlacionados negativamente; en las primeras dos iteraciones estaban correlacionados positivamente y el promedio empeoró todo».
> «Por eso no elijo pesos: entreno un meta-aprendiz, una ridge y un árbol superficial reconciliados 50/50, sobre predicciones de las dos ramas».
> «Y lo dejo atado con un encogimiento: con beta igual a cero el sistema es exactamente la BiLSTM, así que el meta nunca puede hacer más daño que el que yo permito».

## Flashcards

> [!question]- ¿Cuál es la diferencia operativa entre stacking y blending?
> De dónde salen las filas del meta-aprendiz. El stacking estricto usa predicciones out-of-fold de todas las filas; el blending reserva un holdout y el meta solo ve esa porción. Este proyecto reserva la unidad 16, así que es blending en sentido estricto.

> [!question]- ¿Cuándo un promedio convexo de dos modelos mejora al mejor de los dos?
> Solo cuando los errores están fuertemente correlacionados de forma negativa. Con correlación positiva el promedio hereda el sesgo de la rama dominante y suma la varianza de la otra.

> [!question]- ¿Qué dos meta-aprendices usa el proyecto y cómo se combinan?
> Una `RidgeCV` y un `LGBMRegressor` superficial, ambos sobre `[p_lstm, p_lgb]`, promediados 50/50 en una reconciliación fija.

> [!question]- ¿Qué aporta el bagging que el boosting no aporta?
> Reduce varianza promediando modelos entrenados en paralelo sobre muestras perturbadas. El boosting reduce sesgo encadenando modelos que corrigen el error del anterior.

## Conexiones

Antes: [[c04-metricas-y-baseline]] · Después: [[c10-oof-y-validacion-agrupada]]
