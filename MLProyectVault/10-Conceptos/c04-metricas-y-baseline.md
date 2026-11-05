---
tipo: concepto
status: sin-estudiar
tags:
  - metricas
  - nasa-score
  - baseline
---

# Métricas, macro-RMSE y el baseline honesto

> [!abstract] En una frase
> Cuatro métricas miden cuatro cosas distintas y una de ellas, el NASA score, es una suma asimétrica que cobra más caro sobreestimar que subestimar.

## El problema que resuelve

Un solo número no alcanza para describir un modelo de RUL, porque cada métrica miente distinto.

El RMSE castiga el error grande y es sensible a un solo motor mal predicho. El MAE dice cuántos ciclos se equivoca uno en promedio y no distingue dirección. El R² compara contra predecir la media. El NASA score pondera sobreestimar más que subestimar, porque en mantenimiento creer que un motor dura más de lo que dura es el error caro.

Y ninguno de los cuatro dice si el resultado es bueno. Para eso hace falta un piso: algo trivial contra lo que comparar.

## Cómo funciona

| Métrica | Fórmula | Qué pregunta responde |
|---|---|---|
| RMSE | $\sqrt{\frac{1}{n}\sum (y-\hat{y})^2}$ | Cuánto se equivoca, castigando los errores grandes |
| MAE | $\frac{1}{n}\sum \lvert y-\hat{y}\rvert$ | Cuántos ciclos se equivoca en promedio |
| R² | $1 - \frac{\sum (y-\hat{y})^2}{\sum (y-\bar{y})^2}$ | Cuánta varianza del objetivo explica |
| NASA score | $\sum \begin{cases} e^{-d/13}-1 & d<0 \\ e^{d/10}-1 & d\ge 0 \end{cases}$ | Cuánto cuesta el error, con la asimetría de la planta |

con $d = \hat{y} - y$. La implementación es literal:

```python
d = np.asarray(y_pred).ravel() - np.asarray(y_true).ravel()
score = np.where(d < 0.0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)
return float(np.sum(score))
```

`src/ds02_rul/metrics.py:16`

Tres propiedades que hay que decir juntas:

- **Es asimétrica.** Un ciclo de sobreestimación cuesta con pendiente 1/10; uno de subestimación, con 1/13. La relación es de aproximadamente 1,3 a 1 por ciclo.
- **Es exponencial.** El costo de un error grande crece sin techo, mientras que acertar vale exactamente cero. Un motor mal sobreestimado puede dominar el total de la flota.
- **Es una suma, no una media.** Su magnitud escala con la cantidad de ventanas evaluadas (`src/ds02_rul/metrics.py:3`). Por eso solo es comparable entre modelos medidos sobre las mismas filas.

El macro-RMSE responde a otra pregunta: qué sufre un motor elegido al azar. Es el promedio de los RMSE por motor, cada uno pesando lo mismo, sin importar cuántas ventanas aporte (`src/ds02_rul/metrics.py:21`). El RMSE ponderado, en cambio, deja que el motor con más ventanas domine.

En el bundle vigente (C) la diferencia no es cosmética: el ponderado da ≈4.34 y el macro 5.0153, con 3.6328 / 8.5761 / 2.8371 por motor ([[e00-cifras-autoritativas]]). El motor 14 es el peor y el que menos ventanas aporta —760 de 6 196—, así que el promedio de flota lo disimula.

El baseline cierra el círculo. Es una constante: la media del objetivo en las filas de ajuste.

```python
const = np.full_like(y, float(np.mean(train_y)))
```

`scripts/ablate_meta_cycle.py:132`

Su RMSE es 20.022. Existe por dos razones: demuestra que el pipeline no está roto, y convierte «4,25 ciclos» en una frase con significado. No compite porque no es un modelo: no lee features, no se puede mejorar y no entra en la tabla de comparación.

## Dónde aparece en este proyecto

- Score asimétrico y su suma: `src/ds02_rul/metrics.py:14`.
- Macro-RMSE por motor: `src/ds02_rul/metrics.py:21`.
- Fila única de RMSE / MAE / R² / NASA: `src/ds02_rul/metrics.py:46`.
- Baseline constante: `scripts/ablate_meta_cycle.py:132`.
- Cifras vigentes y su lectura: [[d05-como-decir-las-cifras]] y [[e00-cifras-autoritativas]].

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Reportar solo RMSE | No distingue sobreestimar de subestimar, y en esta planta esas dos direcciones no cuestan lo mismo. |
| Reportar el NASA como media | Ya es una suma; dividirla cambiaría su significado y la haría parecer comparable entre conjuntos de distinto tamaño. |
| MAPE o error porcentual | La RUL tiende a cero al final de la vida del motor: el denominador explota justo donde la decisión importa. |
| Accuracy o F1 | Son métricas de clasificación; el objetivo es continuo. |
| Solo el RMSE ponderado por ventana | Esconde al motor 14: la flota se ve mejor de lo que sufre una unidad elegida al azar. |

> [!warning] La trampa
> El NASA score no se compara con el de un paper ni con el de otra revisión. Es una suma sobre 6 196 ventanas concretas: cambia si cambia el conjunto, aunque el modelo sea idéntico.

## Di esto en el tribunal

> [!quote]
> «Informo cuatro métricas porque cada una responde a una pregunta distinta. El NASA score es una suma de exponenciales asimétricas: sobreestimar cuesta con pendiente 1/10 y subestimar con 1/13, así que la misma equivocación no se cobra igual en las dos direcciones. Y además del RMSE ponderado informo el macro-RMSE, que es el que dice la verdad incómoda: 5,02 frente a 4,34, porque el motor con peor error es también el que menos ventanas aporta.»

## Flashcards

> [!question]- ¿Por qué el NASA score no se promedia?
> Porque la fórmula es una suma (`src/ds02_rul/metrics.py:18`). Su valor escala con la cantidad de filas evaluadas; promediarla cambiaría la unidad de comparación.

> [!question]- ¿Qué mide el macro-RMSE que el ponderado no mide?
> El error de un motor típico. Cada motor pesa 1/n, así que el peor motor no queda diluido por tener pocas ventanas.

> [!question]- ¿Para qué existe un baseline que predice la media?
> Para fijar el piso. Con 20.022 de RMSE, un resultado de 4,25 demuestra que el pipeline aprendió algo; sin piso, el número no tiene escala.

> [!question]- ¿El baseline compite con los modelos?
> No. No lee features, no se entrena y no se puede mejorar. Aparece solo en el diagnóstico como referencia.

## Conexiones

Antes: [[c03-fuga-de-informacion]] · Después: [[c05-regresion-cuantilica]] · Cifras: [[e00-cifras-autoritativas]]
