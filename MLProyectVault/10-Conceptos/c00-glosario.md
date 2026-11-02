---
tipo: concepto
status: sin-estudiar
tags:
  - glosario
  - vocabulario
  - indice
---

# Glosario del proyecto

> [!abstract] En una frase
> Cuarenta términos, una línea cada uno y la nota que los explica, para traducir el vocabulario del proyecto sin abrir cinco notas.

## Cómo usar este glosario

1. Leelo una vez de arriba abajo antes de estudiar los ejes; vas a reconocer el mapa.
2. La tercera columna no es decorativa: es la nota dueña. Si un término aparece en el tribunal y no lo podés explicar, esa es la nota que falta.
3. Este glosario no explica mecanismos. Define y deriva; el mecanismo vive en la nota enlazada.

## Los 40 términos

| Término | Qué es en una línea | Nota dueña |
|---|---|---|
| RUL | Ciclos de vuelo que le quedan al motor antes del fallo. | [[c01-que-es-rul]] |
| Ventana | Bloque de 50 filas consecutivas de un mismo motor que el modelo lee como contexto. | [[c02-ventanas-y-horizonte]] |
| Stride | Decimación aplicada al cargar el HDF5: se conserva una fila de cada 100. | [[s02-datos-ds02-y-reparto]] |
| Step | Distancia en filas entre el inicio de una ventana y el inicio de la siguiente. | [[c02-ventanas-y-horizonte]] |
| Horizonte | Tiempo real que cubre una ventana; con stride 100 son 0,44 ciclos, no 50. | [[c02-ventanas-y-horizonte]] |
| cyc_norm | Ciclo acumulado del motor dividido por 100; entra como canal 19 y como feature tabular. | [[s08-ablacion-cyc-norm]] |
| OOF | Predicción de una fila hecha por un modelo que no vio esa fila ni su motor. | [[c10-oof-y-validacion-agrupada]] |
| Fold agrupado | Partición de validación que separa motores enteros, nunca filas sueltas. | [[c10-oof-y-validacion-agrupada]] |
| beta | Contracción entre el campeón y el meta: `p = p_lstm + beta · (p_meta − p_lstm)`. | [[c11-shrinkage-beta]] |
| Meta-learner | Regresor de baja capacidad que combina las dos predicciones base. | [[c09-ensembles]] |
| Stacking | Combinar modelos con un aprendizaje de segundo nivel sobre sus predicciones. | [[c09-ensembles]] |
| Blending | Promedio convexo con pesos fijos o por varianza; acá se midió y se descartó. | [[c09-ensembles]] |
| Bagging | Promedio de copias del mismo algoritmo entrenadas en muestras bootstrap. | [[c09-ensembles]] |
| Boosting | Suma secuencial de árboles donde cada uno corrige el error del anterior. | [[c09-ensembles]] |
| LightGBM | Gradient boosting con crecimiento por hoja; es la rama tabular del ensamble. | [[s05-lightgbm-cuantilico]] |
| Cuantil | Valor por debajo del cual cae una fracción alpha de la distribución condicional. | [[c05-regresion-cuantilica]] |
| Pinball loss | Pérdida asimétrica cuyo mínimo está en el cuantil alpha, no en la media. | [[c05-regresion-cuantilica]] |
| alpha | Cuantil con el que se entrena LightGBM; el vigente es 0,35. | [[c05-regresion-cuantilica]] |
| Residualización | Restar a cada sensor la parte que explica el régimen operativo. | [[c08-residualizacion]] |
| Régimen operativo | Los 4 canales W: altitud, Mach, TRA y T2. | [[c08-residualizacion]] |
| W | Matriz de canales operativos; describe cómo se vuela, no cuánto se desgastó. | [[s02-datos-ds02-y-reparto]] |
| Xs | Matriz de los 14 sensores físicos; describe el estado del motor. | [[s02-datos-ds02-y-reparto]] |
| Scaler | Estandarizador de 18 canales ajustado solo con los motores de ajuste. | [[s03-preproceso-sin-fuga]] |
| Ridge | Regresión lineal penalizada en L2; quita el régimen y también oficia de meta. | [[c08-residualizacion]] |
| Pooling | Reducir la secuencia de 50 pasos a un vector fijo antes de la capa densa. | [[c07-pooling-temporal]] |
| BiLSTM | Red recurrente bidireccional de dos capas; es el campeón y lee la secuencia. | [[s06-bilstm-triple-pooling]] |
| EMA | Media móvil exponencial que suaviza la serie de predicciones de un motor. | [[c13-ema-causal]] |
| Conformal | Método que convierte un punto en banda con cuantiles de residuales no vistos. | [[c12-conformal-prediction]] |
| Cobertura | Fracción de filas cuya verdad cae dentro de la banda; se mide, no se asume. | [[s11-banda-conformal]] |
| q_low / q_high | Cuantiles por tramo que se suman a la predicción para fijar los dos bordes. | [[s11-banda-conformal]] |
| L_inf | Borde inferior de la banda; es la cifra sobre la que se decide el estado. | [[s13-capa-de-reglas-y-decision]] |
| Macro-RMSE | Promedio de los RMSE por motor, cada motor pesando lo mismo. | [[c04-metricas-y-baseline]] |
| RMSE | Raíz del error cuadrático medio, expresada en ciclos. | [[c04-metricas-y-baseline]] |
| MAE | Error absoluto medio, en ciclos; no castiga más los errores grandes. | [[c04-metricas-y-baseline]] |
| R² | Fracción de la varianza del objetivo que el modelo explica. | [[c04-metricas-y-baseline]] |
| NASA score | Suma de exponenciales asimétricas: sobreestimar cuesta más que subestimar. | [[c04-metricas-y-baseline]] |
| Baseline | Modelo trivial que predice la media de ajuste; marca el piso y no compite. | [[c04-metricas-y-baseline]] |
| Leakage | Información disponible al entrenar que no lo estará al predecir. | [[c03-fuga-de-informacion]] |
| Holdout | Unidad 16, reservada para el meta y para beta; nunca entrena las bases. | [[s01-protocolo-honesto]] |
| Manifest | JSON de procedencia: formas, partición, semilla, métricas y hashes. | [[s12-persistencia-y-contrato]] |

## Flashcards

> [!question]- ¿Stride y step son lo mismo?
> No. El stride decima la serie al cargarla (`src/ds02_rul/data.py:61`) y define cuántos registros entran. El step avanza la ventana dentro de un motor ya cargado (`src/ds02_rul/features.py:130`) y define cuántas ventanas salen.

> [!question]- ¿Qué diferencia hay entre OOF y holdout?
> El holdout es una unidad entera reservada; el OOF es una predicción por fila producida por un modelo que no vio ni esa fila ni su motor. El holdout es un conjunto; el OOF es una propiedad de cada predicción.

> [!question]- ¿Qué significa beta = 1,0?
> Que la predicción final es exactamente la salida del meta-learner. Con beta = 0 sería el BiLSTM puro; los valores intermedios interpolan (`src/ds02_rul/ensemble.py:157`).

> [!question]- ¿El NASA score es una media?
> No, es una suma (`src/ds02_rul/metrics.py:18`). Su magnitud crece con la cantidad de ventanas evaluadas, así que solo se compara entre modelos medidos sobre las mismas filas.

## Conexiones

Antes: nada · Después: [[c01-que-es-rul]] · Cifras: [[e00-cifras-autoritativas]]
