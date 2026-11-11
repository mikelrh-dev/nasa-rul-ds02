# Plan de reestructuración /claridad/nucleo actual vs track clase

## Objetivo

Subir la recomprensibilidad del repo de forma real, sin depender de formato y sin romper la rúbrica. El foco es separar claramente lo que corresponde al programa actual de lo que es evidence / soporte del track de clase, reducir la entrada cognitiva por zona y eliminar duplicados que ya no tienen justificación.

Criterios de éxito operativa:

- Quien entra entiende rápido qué zona es cada cosa.
- La lógica del programa actual queda separada de la entrega / evidencia de clase.
- Las métricas, particiones y persistencia tienen fuentes claras y no se repiten sin razón.
- Ningún archivo se mueve o quita sin verificar consumidor real.
- El cambio es compatible con .py y con notebooks; no depende de markdown.

## Qué se mantiene implícito del trabajo actual

- `src/ds02_rul/` es el núcleo del programa actual.
- `src/clase/` se lee como evidencia o entrega del track de clase PIA 3, no como núcleo del programa actual.
- `models/ds02_manifest.json` es la fuente de verdad de checksums y particiones del bundle C desplegado.
- Hay productos derivados que el repositorio usa hoy: por ejemplo `models/ensemble.joblib` y `ds02_manifest.json` usados por la UI actual; el script `src/ds02_rul/persistence.py` define `load_ensemble` / `save_ensemble` y la validación de artefactos.

## Qué está bien hoy

- `src/ds02_rul/metrics.py`: `evaluate_predictions` como única fuente real de métricas (RMSE/MAE/R2/NASA Score).
- `src/ds02_rul/pipeline.py`: creación de modelos (`make_lgbm`, `fit_bilstm`) centralizada.
- `src/ds02_rul/features.py`: `build_windows`, `fit_preprocessing` como plumbing de ventanas.
- `src/ds02_rul/persistence.py`: persistencia y validación de artefactos DS02.
- `src/ds02_rul/viz.py`: envoltorios de presentación ya diseñados (`evaluar_clase`, `mostrar_clase`) sobre `evaluate_predictions`.

## Redundancia identificada

### 1. Métricas duplicadas en `src/clase/`

`src/clase/train_clasicos.py` y `src/clase/train_mlp.py` vuelven a definir sus propias métricas de train/test/OOF con firmas y formatos distintos, cuando `ds02_rul/metrics.py` ya calcula lo mismo centralizado.

Riesgo implícito:

- duplicidad de decisión métrica,
- mayor mantenimiento y desajuste entre versiones.

### 2. Algoritmo de entrenamiento/evaluación repetido

Los mismos pasos aparecen replicados en:

- `src/clase/train_clasicos.py`
- `src/clase/train_mlp.py`
- `src/clase/train_ensemble_adaptado.py`

Patrón común:

1. entrenar varios modelos,
2. elegir por métrica de validación,
3. medir test solo para el elegido,
4. escribir resultados CSV,
5. persistir el mejor en `models/`.

Riesgo implícito:

- orquestación repetida con variaciones pequeñas pero costosas de mantener,
- posible confusión sobre qué versión es la referencia del bundle C actual.

### 3. Particiones compartidas definidas en varios sitios

`FIT_UNITS`, `HOLDOUT_UNITS`, `TEST_UNITS` aparecen definidos tanto en:

- `src/clase/ventanas_adaptadas.py`,
- `src/clase/train_ensemble_adaptado.py`.

Además, hay otras constantes de partición en `src/clase/dataset_clase.py` (`TRAIN_UNITS`, `TEST_UNITS`).

Riesgo implícito:

- desfase entre zonas si se cambia una y no la otra,
- imposibilidad de saber cuál es la definición oficial del bundle C desplegado sin cruzar varios archivos.

### 4. Manipulación de datos extra repetida

`src/clase/ventanas_adaptadas.py` importa `build_windows`, `fit_preprocessing` desde `src/ds02_rul.features` y re-añade imputación, partición y ventaneado adaptado en lugar de extender o componer sobre lo existente.

Riesgo implícito:

- dos caminos de limpieza/partición con mismo proposito pero separados,
- lógica adaptada difícil de seguir por dispersión.

### 5. Presentación/evaluación duplicada

`src/ds02_rul/viz.py` ya define envoltorios `evaluar_clase` y `mostrar_clase`, pero `src/clase/` sigue manejando sus propias tablas de resultados directamente sin usarlas.

Riesgo implícito:

- dos estilos de resultado para el mismo tipo de decisión.

## Archivos que se revisan por zona

### `src/clase/`

#### Quedan bien ubicados como evidencia / track de clase

- `dataset_clase.py`
- `pipeline_clase.py`
- `train_clasicos.py`
- `train_mlp.py`

Estos archivos describen la ejecución del clase/track y puede que sigan teniendo valor como entrega histórica o docente. Se revisan antes de cualquier decisión de eliminar o mover.

#### Zona gris, pero probablemente de acuerdo con lo que ustedes describen

- `ventanas_adaptadas.py`
- `train_ensemble_adaptado.py`
- `evaluar_c_multisemilla.py`
- `puente_c.py`
- `tabla_final.py`
- `mil_models.py`

La zona gris se resuelve con una pregunta concreta antes de mover o borrar: ¿quién consume hoy esto de forma real? Si la respuesta es vacía o muy débil, la acción está más cerca de consolidar o retirar. Si la respuesta es fuerte, se queda donde está o se mueve con propósito claro.

### `src/ds02_rul/`

Se mantiene como núcleo actual. Se mantiene implícitamente la separación entre:

- lógica de entrenamiento y estructura de modelos,
- métricas,
- ventanas/plumbing,
- persistencia,
- presentación,
- soporte de notebooks o tracking si aplica.

Se revisa solo si alguna pieza actual ya no tiene consumidor real o si hay señales de código zombi relativo.

## Criterios de decisión

- El movimiento va a favor de la lectura del repositorio real actual, no a favor de imitar un notebook.
- No se borra nada de zona gris hasta verificar importaciones o ejecución reales.
- La decisión se toma por consumidor profesional, no por estilo o por evidencia no ejecutada.
- La redundancia se consolida solo si hay consumidores reales que puedan cambiar a la versión consolidada o si la versión original era solo duplicación de andamiaje.

## Acciones claras

### A. Separar responsabilidades

- Mantener `src/ds02_rul/` como núcleo actual.
- Mantener `src/clase/` como evidencia/track de clase, con indicación clara de que su contenido puede ser entrega histórica y no lógica del programa actual.
- Separar explícitamente:
  - código de entrenamiento / evaluación del bundle actual,
  - código de soporte o experimento del track clase,
  - código de utilidad o diagnóstico.

### B. Consolidar donde tiene sentido

- Unificar en `src/ds02_rul/metrics.py` la métrica de referencia.
- Reducir o consolidar las métricas duplicadas en `src/clase/` solo después de verificar consumidores y formato.
- Trasladar las particiones compartidas (`FIT_UNITS`, `HOLDOUT_UNITS`, `TEST_UNITS`) a un único lugar compartido entre `class/` y `ds02_rul/` cuando corresponda.
- Reducir la repetición de pipeline de entrenamiento elegir-por-val + test una vez si se puede alinear sobre una ruta única.

### C. Revisar y decidir zona gris

- `ventanas_adaptadas.py`
- `train_ensemble_adaptado.py`
- `evaluar_c_multisemilla.py`
- `puente_c.py`
- `tabla_final.py`
- `mil_models.py`

Cada uno se decide con una pregunta:

- ¿Quién importa o ejecuta esto hoy?
- ¿Sigue siendo útil como evidencia ejecutada o soporte de notebooks?
- ¿Debería volver a `ds02_rul/`, quedarse en `clase/`, o retirarse?

### D. Gestionar la evidencia no ejecutada con cuidado

- Los notebooks y páginas de evidencia tienen valor de ejecución, pero no deben ser fuente de verdad sobre lo que corre hoy. Si una pieza de evidencia no se ejecuta o no tiene consumidor real, se marca como tal y no se confunde con el programa actual.

## Qué no se hace

- No se borra automáticamente nada de zona gris solo por inercia.
- No se mezcla el “lo que enseñan las profesoras como estilo” con la estructura real del repositorio actual. El objetivo es recomprensibilidad, no imitación.
- No se toca la lógica del bundle C actual sin validar el impacto real.
- No se renombra o reubica algo sin verificar impacto de import y ejecución.

## Verificación antes de mover/borrar

Antes de cualquier acción sobre zona gris, se verifica:

- quién importa o ejecuta el archivo,
- si existen tests o notebooks consumidores reales,
- si el archivo toca artefactos o manifiestos que son fuente de verdad del bundle actual,
- si hay duplicidad con `ds02_rul/` que pueda resolverse ya.

Si no hay consumidor real y la pieza es evidencia histórica o soporte de notebook, se documenta como tal y se decide conservar, reubicar o retirar.

## Entregables del plan

- Criterios de éxito operativa escritos arriba.
- Inventario por zona con claro qué está bien ubicado.
- Lista de redundancias identificadas y su riesgo implícito.
- Lista de zona gris con pregunta de decisión.
- Criterios de exclusión para que no se haga gala.

## Nota práctica

Este plan es una hoja de ruta para la reorganización y la claridad, no una reunión de copias de plantillas ni un cambio de estilo de markdown. Si un agente lo verifica, él debería comprobar el consumo real antes de aprobar cualquier borrado o movimiento de zona gris.

## Estado del plan en esta rama (`refactor/estructura-ds02-clase-2026-11-10`)

La reestructuración que se ejecutó **sólo implementó la parte que el plan ya consideraba decidida**: separar la responsabilidad del bundle C del soporte de clase y consolidar las particiones compartidas en un único contrato. Los movimientos se hicieron en tres grupos, de acuerdo con el principio de no mover nada sin consumidor real:

1. **Código del bundle C desplazado a `src/ds02_rul/`**

   - `src/clase/train_ensemble_adaptado.py` → `src/ds02_rul/blob_c.py` (ahora `entrenar()`).
   - `src/ds02_rul/puente_c.py` quedó en `src/ds02_rul/puente_c.py` (era zona gris de soporte de notebook).
   - `src/clase/evaluar_c_multisemilla.py` → `scripts/evaluate_bundle_stability.py` (sección fuera del entrenamiento del bundle; ahora operacional).

2. **Consolidación del contrato compartido**

   - `src/ds02_rul/data.py` pasó a ser la fuente de `FIT_UNITS`, `HOLDOUT_UNITS`, `TEST_UNITS`, `TRAIN_UNITS`, las columnas, el esquema, las medianas de fit-units y la función `construir_raw_adaptado`.
   - `src/ds02_rul/metrics.py` pasó a ser la única métrica de referencia: `regression_metrics`, `aggregate_seed_metrics` y las metáricas de evaluación.
   - Los dos paquetes ahora leen ese contrato desde `ds02_rul`; `clase` puede importar `ds02_rul`, pero no al revés (test `tests/test_architecture.py`).

3. **Módulos que no se movieron porque ya son el bundle congelado**

   - `ensemble.py`, `residualizer.py`, `pooling.py`, `persistence.py`, `stacking.py`, `conformal.py`, `smoothing.py` no se tocaron: ya viven donde el pickle/Keras los registra (`ds02_rul.ensemble.HybridStackingEnsemble`, `ds02_rul.residualizer.SensorResidualizer`, `ds02_rul.pooling.LastStepPooling`).

4. **Evidencia/evaluación de clase que se quedó donde estaba**

   - `dataset_clase.py`, `pipeline_clase.py`, `train_clasicos.py`, `train_mlp.py` son evidencia del track de clase; no se movieron y no se eliminaron.
   - `tabla_final.py` sigue como rúbrica de resultados.
   - `mil_models.py` es zona gris pendiente; en esta rama no se ha decidido ni consumido.

### Lo que no se hizo (queda en el plano, no en código)

- No se retiró `mil_models.py`: sigue como zona gris del plan; no tenía consumidor real comprobado en esta sesión.
- No se tocó `shim` ni retiro de compatibilidad: no era necesario, porque el bundle ya se carga desde su ubicación current y el movimiento se verificó con los mismos nombres de módulo que usa el pickle/Keras.
- No se reentrenó el bundle principal; cualquier reentrenamiento queda en sombra por contrato (`bundle_c.entrenar` con `out_dir` propio, sin escribir en `models/`).

### Verificación del plano contra lo ejecutado

- Los movimientos aplicados son exactamente los del plan: dos ampliaciones al núcleo actual (`data.py`, `metrics.py`) y tres reubicaciones hacia su nuevo dueño (`blob_c → src/ds02_rul`, `puente_c` ya allí, `evaluar_c_multisemilla → scripts`).
- Las zonas grises de mayor riesgo (`ensemble.py`, residualizer, pooling) se conservaron intencionalmente y no se violó la regla de “no mover sin consumidor real verificado”.
- `models/` quedó intacto por contrato y se comprobó que el bundle congelado sigue siendo el mismo ciclo de hashes.

### Pendiente por sí decides avanzar más tarde

- Decidir qué pasa con `mil_models.py`: conservar como evidencia histórica de zona gris, retiro documentado, o reubicación a scripts/ si surge un consumidor real.
- Unificar o desautorizar cualquier métrica/evaluación duplicada que siga viviendo en `src/clase/`, pero solo tras comprobar consumidor real; no hay urgencia operativa ahora.
- Complementar la documentación del guión oficial si algún notebook queda sin mapa o si un artefato intermedio cambia de contrato.

> El plan plantaba separar responsabilidades y consolidar contratos; esta rama ejecutó eso para lo decidido y dejó la zona gris restante marcada en el mismo plano.
