---
tipo: concepto
status: sin-estudiar
tags:
  - validacion
  - groupkfold
  - rubrica
  - saa
---

# GroupKFold por motor

> [!abstract] En una frase
> La validación se parte por motor, nunca por fila: todas las filas de un motor van juntas al mismo fold.

## La idea

En datos de degradación, las filas no son independientes: dos ciclos vecinos del mismo motor son casi la misma observación. Un KFold clásico que reparte filas al azar pone ventanas casi idénticas a ambos lados de la frontera ajuste/validación, y la validación mide memoria en vez de generalización. GroupKFold con `groups=unit` obliga a que cada motor entero caiga en un solo fold: el modelo se puntúa siempre sobre un motor que no vio.

## Por qué el grupo es el motor

El motor es la unidad que se despliega: en producción el modelo puntúa motores nuevos, no filas nuevas de motores conocidos. Partir por motor reproduce en validación la pregunta real («¿qué tal con un motor que no vi?»). Es el mismo principio que el OOF agrupado del track de ventanas ([[c10-oof-y-validacion-agrupada]]), aplicado al track tabular de clase.

## Dónde aparece en este proyecto

- `src/clase/train_clasicos.py` y `src/clase/train_mlp.py` — GridSearchCV con GroupKFold por `unit` (CV score media±std que pide la rúbrica SAA P6).
- `src/clase/README.md` — la tabla de clase reporta el CV por motor.
- El espejo en el track de ventanas: `src/ds02_rul/pipeline.py:157` (`oof_base_predictions` por motor) y [[s09-oof-y-beta]].
- `unit` no es predictor en ningún modelo: `src/clase/pipeline_clase.py` la excluye de `FEATURE_COLS` y solo la usa como grupo.

> [!warning] La trampa
> «Usé validación cruzada, así que no hay fuga»: depende de la unidad de partición. Un KFold por fila en datos de degradación fuga siempre, y con RMSE peligrosamente optimista. La pregunta del tribunal no es «¿hiciste CV?» sino «¿por qué partiste?».

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «Partimos por motor porque el motor es lo que se despliega: validar sobre filas de un motor ya visto es examinarse con las respuestas delante».
> «La `unit` no entra al modelo como feature; entra como grupo de partición. Es lo único que impide que la validación mida memoria».

## Flashcards

> [!question]- ¿Qué es GroupKFold por motor y por qué se usa aquí?
> Un KFold donde cada motor entero va a un solo fold (`groups=unit`): el modelo siempre se valida sobre motores no vistos, reproduciendo la pregunta real de producción.

> [!question]- ¿Qué mide un KFold por fila en datos de degradación?
> Memoria, no generalización: filas vecinas del mismo motor son casi idénticas y quedan a ambos lados de la frontera, inflando el score de validación.
