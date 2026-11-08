---
tipo: concepto
status: sin-estudiar
tags:
  - reproducibilidad
  - ruido
  - semillas
  - limites
---

# Ruido de ejecución y reproducibilidad

> [!abstract] En una frase
> El sistema no es bit a bit determinista, y el proyecto convierte ese ruido en una regla de lectura: ninguna diferencia menor a ±0,1 RMSE se presenta como mejora.

## El problema que resuelve

El mismo cuaderno, ejecutado dos veces con el mismo código y la misma semilla, no devuelve el mismo RMSE del híbrido. La causa no es un cambio de modelo: las operaciones que TensorFlow ejecuta en CPU pasan por kernels de oneDNN que reordenan sumas en coma flotante, de modo que la rama BiLSTM se mueve unas centésimas incluso con la semilla fija (`docs/02_DS02_ensemble_RUL_spec.md:731`).

LightGBM, que no pasa por TensorFlow, sí reproduce (`notebooks/ds02_ensemble/EVALUACION_EJECUCION.md:92`). Por eso el ruido se concentra en todo lo que contiene al BiLSTM, incluido el híbrido y la banda que se calibra sobre sus residuos (`AGENT.md:11`).

Si «reproducible» significara «bit a bit idéntico», el proyecto no sería reproducible. La salida es definir la reproducibilidad de forma estadística: qué se repite, con qué dispersión y a partir de qué tamaño una diferencia es atribuible al modelo y no al ruido.

## Cómo funciona

Hay tres poblaciones distintas y conviene no mezclarlas:

| Nivel | Qué se repite | Qué se reporta |
|---|---|---|
| Reejecución | mismo código, misma semilla, misma máquina | el híbrido se mueve ±0,05 RMSE (`README.md:55`) |
| Semillas | protocolo completo con semillas 42, 7 y 123 | media ± desviación: `4.322 ± 0.064` impresa en NB06, **NO reconciliada** con el CSV (4.368 pendiente per [[e00-cifras-autoritativas]]); oficial 4.338 semilla 42 |
| Fila en disco | una corrida concreta, la que reproduce el artefacto | `4.338` |

La resolución de trabajo es ±0,1 RMSE. No es una convención arbitraria: la desviación entre semillas del híbrido es 0,101 y la dispersión entre reejecuciones es de ±0,05. Cualquier afirmación más fina que eso no es verificable con este pipeline (`README.md:57`).

Por eso cada cifra se cita con su dispersión y no sola. Una media sin desviación invita a comparar el tercer decimal de dos corridas y llamarlo progreso.

La misma lógica ordena las comparaciones. La ventaja del híbrido sobre el campeón es de casi dos ciclos de RMSE, muy por encima del ruido, así que la decisión estructural se sostiene. La estabilidad del LightGBM, con desviación 0,034 entre semillas, también. Una diferencia de 0,05 entre dos variantes no se sostiene.

## Dónde aparece en este proyecto

- La tabla vigente publica media ± desviación sobre tres semillas, y la fila de referencia en disco por separado (`README.md:52`).
- El README pide leer las desviaciones antes que las medias (`README.md:30`).
- La limitación está declarada: `beta` se elige solo con la semilla 42 (`README.md:347`).
- La explicación del no-determinismo y de sus efectos sobre los folds está en `notebooks/ds02_ensemble/EVALUACION_EJECUCION.md:92`.
- La consecuencia práctica para citar cifras vive en [[d05-como-decir-las-cifras]]; la tabla única, en [[e00-cifras-autoritativas]].

## Qué alternativa se rechazó

| Alternativa | Por qué no |
|---|---|
| Fijar todas las semillas y exigir igualdad bit a bit | La semilla no controla el orden interno de los kernels de CPU; el requisito es imposible de cumplir en esta máquina |
| Citar una sola corrida como resultado del sistema | Un solo sorteo oculta la dispersión y hace que la próxima reejecución parezca una regresión |
| Relajar la tolerancia de comparación hasta que todo pase | Una tolerancia global ancha tapa deriva real; la tolerancia se elige por ruta, no por conveniencia |
| Elegir `beta` en las tres semillas y reportar la mejor | Sería elegir sobre el resultado que se reporta; la limitación se declara en lugar de explotarse |

> [!warning] La trampa
> El ±0,1 corta en las dos direcciones. Prohíbe presentar como mejora una diferencia de centésimas, y también prohíbe presentar como regresión una reejecución que se mueva dentro de ese margen.
>
> | Situación | Veredicto |
> |---|---|
> | Una celda imprime un RMSE distinto del manifiesto | No es error: la celda es una salida de ejecución, el manifiesto es la fila en disco |
> | La fila de referencia dice `4.338` y la media dice `4.322` | No es error: una corrida frente a la media de tres semillas |
> | Un fold elige `beta = 0` y el enviado es `1.0` | No es error: el enviado es la mediana de tres folds |
> | Se cita la cifra de una revisión anterior como vigente | Error: no pertenece al bundle en disco |
> | Se presenta una diferencia de 0,05 como mejora | Error: está por debajo de la resolución |
> | Se omite el vector de folds | Error: esconde que la selección está poco determinada |

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «El pipeline no es determinista bit a bit: TensorFlow en CPU reordena operaciones en coma flotante y el RMSE se mueve unas centésimas entre corridas idénticas. Por eso no reporto un número solo, reporto media y desviación sobre tres semillas, y por eso la resolución de cualquier afirmación es ±0,1 RMSE. Eso no debilita la conclusión: la ventaja del híbrido es de unos dos ciclos, muy por encima del ruido, y la limitación de que `beta` se elige solo en la semilla 42 está escrita, no escondida.»

## Flashcards

> [!question]- Pregunta de repaso
> ¿Por qué dos ejecuciones idénticas no dan el mismo RMSE?
> Porque la rama BiLSTM corre sobre TensorFlow en CPU, y sus kernels de oneDNN reordenan operaciones en coma flotante. La semilla fija el muestreo y la inicialización, no el orden de esas sumas. LightGBM, que no pasa por TensorFlow, sí reproduce.

> [!question]- Pregunta de repaso
> ¿Por qué la resolución de las afirmaciones es ±0,1 RMSE y no menos?
> Porque la desviación entre semillas del híbrido es 0,101 y la dispersión entre reejecuciones es de aproximadamente la mitad. Por debajo de ese margen no se puede distinguir un cambio de modelo del ruido de ejecución.

> [!question]- Pregunta de repaso
> ¿Por qué se reporta media ± desviación en lugar de una corrida?
> Porque una corrida es un sorteo de una distribución. La desviación publica cuánto puede moverse el resultado sin que nada haya cambiado, y permite comparar dos modelos contra el margen en vez de contra el azar.

> [!question]- Pregunta de repaso
> ¿Qué limitación implica elegir `beta` solo con la semilla 42?
> Que el valor enviado es una selección hecha sobre una corrida. La dispersión de métricas se reporta sobre tres semillas, pero la de `beta` no. El vector de folds, con IQR 0,5, muestra que la selección está poco determinada en la parte alta del rango.

> [!question]- Pregunta de repaso
> ¿Qué diferencia hay entre «no determinista» y «no reproducible»?
> No determinista significa que dos corridas idénticas no coinciden bit a bit. No reproducible significaría que la conclusión no se repite. Acá el tercer decimal cambia, pero la comparación entre modelos se repite en todas las semillas.

## Conexiones

Antes: [[c13-ema-causal]] · Después: [[e00-cifras-autoritativas]]
