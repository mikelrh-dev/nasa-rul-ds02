---
tipo: concepto
status: sin-estudiar
tags:
  - cuantil
  - pinball
  - lightgbm
---

# Regresión cuantílica y por qué alpha = 0,35

> [!abstract] En una frase
> Entrenar con pérdida pinball en el cuantil 0,35 desplaza la predicción por debajo de la media para convertir sobreestimaciones caras en subestimaciones baratas.

## El problema que resuelve

Una regresión entrenada con error cuadrático estima la **media condicional**: es insesgada en promedio, así que aproximadamente la mitad de sus errores quedan por arriba de la verdad. Bajo el score NASA, esa mitad paga la rama exponencial más empinada.

El problema no es que el modelo sea malo: es que está optimizando la cosa equivocada. Minimizar error cuadrático no es minimizar el costo de mantenimiento. La pérdida tiene que tener la misma asimetría que la métrica.

## Cómo funciona

La pérdida pinball para el cuantil $\alpha$ se define como

$$
\rho_\alpha(y, \hat{y}) = \max\big(\alpha\,(y - \hat{y}),\ (\alpha - 1)\,(y - \hat{y})\big)
$$

y su mínimo, sobre la distribución condicional de $y$, se alcanza en el cuantil $\alpha$. Tres casos:

- $\alpha = 0{,}5$: es la mediana. Penaliza igual en las dos direcciones.
- $\alpha < 0{,}5$: el mínimo queda por debajo de la mediana y por lo tanto por debajo de la media en una distribución aproximadamente simétrica.
- $\alpha = 0{,}35$: cada ciclo que el modelo sobreestima cuesta 0,65; cada ciclo que subestima cuesta 0,35. La sobreestimación pesa casi el doble.

Con esa pérdida, la rama tabular no predice «cuánto dura» sino «un valor que se queda corto siete veces de cada veinte». Ese sesgo hacia abajo es deliberado: convierte una parte de los errores caros en errores baratos, y el costo en RMSE queda acotado porque el desplazamiento es pequeño y aproximadamente constante.

La asimetría de la pérdida va en el mismo sentido que la de la métrica. Sobreestimar cuesta con pendiente 1/10 en el score NASA; subestimar, con 1/13. La pérdida no copia esa proporción exacta, pero apunta al mismo lado ([[c04-metricas-y-baseline]]).

En el código, el objetivo es una constante de configuración:

```python
LGB_PARAMS = dict(
    objective="quantile",
    alpha=0.35,
```

`src/ds02_rul/pipeline.py:30`

## Dónde aparece en este proyecto

- Objetivo y `alpha` de la rama tabular: `src/ds02_rul/pipeline.py:30`.
- El comentario que resume el rechazo del 0,50, con las cifras de dev y de test: `src/ds02_rul/pipeline.py:23`.
- Solo una de las dos ramas lleva la asimetría; la recurrente usa Huber, simétrica ([[s06-bilstm-triple-pooling]]).
- Esa rama es la que aporta la señal asimétrica al ensamble: [[s05-lightgbm-cuantilico]].
- Decisión completa y su respaldo: [[e01-adr-index]].

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Regresión L2 / media (iteraciones 1 a 3) | Insesgada: produce sobreestimaciones frecuentes, y el costo de la planta no es simétrico. |
| Mediana, `alpha = 0,50` | Ganó en dev por márgenes claros y perdió en el test confirmatorio: con el BiLSTM fijo, el híbrido pasó de ≈4,24 a ≈4,59 y la rama de ≈7,1 a ≈9,1 (ADR-007). |
| `alpha = 0,60` | Ya era el peor en dev, y el mecanismo que hundió la mediana lo habría amplificado. Rechazado sin lectura de test. |
| MSE asimétrico a medida | Reimplementar el crecimiento por hoja de LightGBM; más lento y no portable entre versiones. |
| Corrección afín posterior sobre un modelo L2 | Un desplazamiento global mueve el grueso de la distribución y deja intactas las colas grandes, que son las que la exponencial castiga. |
| Entrenar también el BiLSTM con cuantiles | Considerado y postergado: reentrenar el campeón cuesta mucho más que ajustar la rama barata. |

> [!warning] La trampa
> El cuantil no da un intervalo. Devuelve un punto desplazado, no una cota. La banda de predicción la produce el conformal, y son dos mecanismos distintos ([[c12-conformal-prediction]]). Tampoco es una probabilidad de falla: 0,35 es un cuantil del objetivo, no un riesgo.

## Di esto en el tribunal

> [!quote]
> «La rama tabular no estima la media: estima el percentil 35 de la distribución condicional, con pérdida pinball. Eso la sesga hacia abajo a propósito, porque el score NASA cobra más caro sobreestimar que subestimar, y así una parte de los errores caros se convierte en errores baratos. Probamos la mediana y ganó en dev, pero perdió en el test confirmatorio: con el BiLSTM fijo, el híbrido pasó de 4,24 a 4,59. Por eso el valor vigente sigue siendo 0,35.»

## Flashcards

> [!question]- ¿Qué se minimiza con pérdida pinball en alpha = 0,35?
> El cuantil 0,35 de la distribución condicional del objetivo, no su media. Por eso la predicción queda por debajo.

> [!question]- ¿Por qué 0,35 y no 0,50?
> Porque en el test confirmatorio, con el BiLSTM fijo, el 0,50 costó ≈0,35 de RMSE al híbrido y ≈2 a la rama. El 0,35 es mejor sobre el objetivo de despliegue (ADR-007).

> [!question]- ¿Qué pasó cuando se probó la mediana?
> Ganó en todos los cortes de dev: rama de ≈9,1 a ≈8,2 y híbrido de ≈13,2 a ≈12,1. Perdió en el test. La razón es que los motores de dev viven más y están subestimados en RUL alta, y los de test son más cortos.

> [!question]- ¿El cuantil 0,35 produce la banda de predicción?
> No. Produce un punto. La banda sale de calibrar cuantiles de residuales fuera de fold, en `src/ds02_rul/conformal.py:28`.

## Conexiones

Antes: [[c04-metricas-y-baseline]] · Después: [[c06-bilstm-y-secuencias]] · Rama tabular: [[s05-lightgbm-cuantilico]]
