---
tipo: notebook
status: sin-estudiar
tags:
  - nb03
  - multisemilla
  - persistencia
---

# NB03 — Evidencia multisemilla y persistencia

> [!abstract] En una frase
> Este cuaderno convierte una ejecución en evidencia: tres semillas, diagnóstico por motor y bundle en disco.

## Antes de empezar

Requiere `[LOAD NB2 OK] BETA = 1.0` y `p_ens (6196,)`. Es el cuaderno más largo: 24 celdas de código verificadas que van de la tabla multisemilla al `RELOAD OK`.

Sus salidas clave: híbrido ≈4.28 ± 0.05 en esa ejecución, por motor 3.867 / 8.018 / 2.662 y `[RELOAD OK] 60.40 vs 58.00`.

## Recorrido celda a celda

| Celda | Qué entra | Qué hace | Qué sale | Por qué está ahí |
|---|---|---|---|---|
| 3 | Estado NB02 | Recarga beta y predicciones | `[LOAD NB2 OK]` | Verifica el puente |
| 5 | Semillas `[42,7,123]` | Repite pipeline completo | LGBM ≈7.10, BiLSTM ≈6.35, híbrido ≈4.28 | Mide el ruido real |
| 8 | Tres corridas | Tabla redondeada | Híbrido 4.278 ± 0.051 con NASA 2315.1 | La que se cita |
| 11 | Test por motor | Desagrega el global | 11: 3.867, 14: 8.018, 15: 2.662 | Desenmascara al 14 |
| 13 | Folds NB03 | Reconfirma beta | `[1.0, 1.0, 0.0]` según partición | Honestidad repetida |
| 15 | `models/` | Persiste bundle y manifiesto | Escribe `ensemble.joblib` y `.keras` | Lo defendido queda en disco |
| 16 | Bundle recargado | Prueba de identidad | `[RELOAD OK] 60.40 vs 58.00`, `True` | Servir es recargar |

Todas las cifras de celdas son salida de esa ejecución. El bundle vigente es ≈4.34 ± 0.10 con fila 4.251 y macro 4.8433 ([[e00-cifras-autoritativas]]).

## Las 5 celdas que importan

1. Celda 5: las tres semillas que fijan la dispersión.
2. Celda 8: la tabla multisemilla redondeada.
3. Celda 11: el por motor que explica el macro.
4. Celda 15: el guardado con hashes y bytes.
5. Celda 16: el `RELOAD OK` que prueba el despliegue.

## Salidas que hay que saber leer

`seed 42: LGBM 7.113 | BiLSTM 5.651 | Hybrid 4.251` muestra el orden en cada semilla: el híbrido gana siempre aunque el BiLSTM oscile.

`motor 14 760 ventanas 8.018` explica el macro: el peor motor aporta menos filas y el ponderado lo esconde ([[c04-metricas-y-baseline]]).

## Qué NO hace este cuaderno

No decide nada operativo: no aplica umbrales ni declara estados. Eso es [[s13-capa-de-reglas-y-decision]]. NB03 termina con el bundle servible, no con un veredicto.

## Si falla algo

Si las cifras se mueven en ±0.1 respecto al manifiesto, es TensorFlow en CPU, no un bug: el README del ensemble lo documenta ([[c14-ruido-y-reproducibilidad]]). Si el reload falla, revisa `LastStepPooling` y la guarda de forma ([[s12-persistencia-y-contrato]]).

> [!quote] Di esto en el tribunal
> «En el tercer cuaderno repito con tres semillas, desagrego por motor y persisto. El híbrido da 4.28 en esa ejecución y el reload clava 60.4 frente a 58 real. Lo que defiendo es lo de disco.»

## Flashcards

> [!question]- ¿Qué deja la celda 3?
> `[LOAD NB2 OK]` con beta 1.0 y predicciones intactas.

> [!question]- ¿Qué da cada semilla en esa ejecución?
> Híbrido 4.251, 4.318 y similar: siempre gana al campeón.

> [!question]- ¿Qué revela el por motor?
> El 14 da 8.02 con 760 filas: poco peso y mucho error.

> [!question]- ¿Qué prueba el RELOAD?
> Que recargado predice igual: 60.40 vs 58.00 con `True`.

> [!question]- ¿Qué afirma esta nota en una frase?
> Este cuaderno convierte una ejecución en evidencia: tres semillas, diagnóstico por motor y bundle en disco.

> [!question]- ¿Cómo la contarías en el tribunal?
> «En el tercer cuaderno repito con tres semillas, desagrego por motor y persisto. El híbrido da 4.28 en esa ejecución y el reload clava 60.4 frente a 58 real. Lo que defiendo es lo de disco.»

> [!question]- ¿Qué archivo respalda esta nota?
`models/`

> [!question]- ¿Qué archivo respalda esta nota?
`notebooks/ds02_ensemble/EVALUACION_EJECUCION.md`

