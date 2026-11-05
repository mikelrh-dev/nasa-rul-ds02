---
tipo: sistema
status: sin-estudiar
tags:
  - dss
  - app
  - tabs
  - modo-historia
---

# DSS por pestañas — flota, motor, auditoría y estrés

> [!abstract] En una frase
> Cuatro fragments con dueño: cada pestaña delega en su módulo, el dashboard conserva los globales y el modo historia guía al operario en cuatro pasos.

## Contrato

| Entra | Sale |
|---|---|
| Ventana de test + registro de taller | Estado por motor, decisión y traza auditable en pantalla |
| Caso nuevo (CSV o formulario) | Gemelo registrado + veredicto con explicación |

## Cómo está implementado

| Pieza | Dónde | Qué hace |
|---|---|---|
| Flota + modo historia | `app/ui_modulos/_tab_flota.py:140` | snapshot, tarjetas de gemelos, 4 botones `historia_1..4` con pasos y umbrales |
| Motor | `app/ui_modulos/_tab_motor.py:64` | curva, SHAP, deriva y badge de estado del motor elegido |
| Casos nuevos | `app/ui_batch.py:192` + `app/ui_inference.py:455` + `app/ui_rules.py:152` | `puntuar_lote` + `score_table` + decisión en vivo: CSV/formulario a gemelo y veredicto |
| Auditoría | `app/ui_modulos/_tab_auditoria.py:48` | per-unit, provenance, informe PDF con firma |
| Estrés (sandbox, no pestaña) | `app/ui_modulos/_sandbox_estres.py:42` | sandbox de puntuación con caché propia, dentro del dashboard |
| Alta de motor | `app/ui_alta.py:92` | `estado_historia`: los 4 pasos con datos vivos |
| Gemelo | `app/twin.py:60` | `make_twin` + `registrar`: del resultado al registro |
| Flota (registro) | `app/flota.py:99` | `registrar_alta` de matrículas |
| Hangar (estados) | `app/hangar.py:57` | `permitidas`: transiciones legales de estado |
| Caso vivo | `app/ui_inference.py:455` | `score_table`: puntúa la tabla del operario |
| Reglas en vivo | `app/ui_rules.py:152` | `decision_en_vivo`: RUL → estado con umbrales |
| Datos en vivo | `app/ui_data_loader.py:327` | `fleet_snapshot`: foto de flota a un ciclo |
| Lote CSV | `app/ui_batch.py:192` | `puntuar_lote` + `registrar_gemelos` |
| API | `app/api.py:208` | `predict` con API key y rate limit |

Los wrappers del dashboard delegan con los globales (`frame_cache` ttl 3600, caché SHAP, firma PDF) y los fragments reciben todo por argumentos: el fallback de importación solo cubre llamadas sueltas, nunca el run normal.

## El modo historia

Cuatro pasos con datos vivos (no un tour de botones): cada `historia_N` fija escenario, umbrales y log, con toast de confirmación. Lo exigen 20 tests de interacción (`tests/test_dss_interaction.py`): si el modo historia se rompe, el gate lo dice antes que el taller.

## Conexiones

- Despliegue: [[s14-app-y-despliegue]] · reglas: [[s13-capa-de-reglas-y-decision]] · SHAP: [[s22-shap-y-app-de-clase]] · persistencia: [[s12-persistencia-y-contrato]]
- Demo: [[d06-demo-y-plan-b]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «El DSS son cuatro pestañas (`dashboard_ds02.py:1107` flota/motor/casos/auditoría) más sandbox de estrés: la flota guía con el modo historia, el motor explica con SHAP, casos puntúa lo nuevo, la auditoría firma el PDF y el estrés prueba sin romper nada».

## Flashcards

> [!question]- ¿Qué cubre cada pestaña del DSS?
> Flota (`_tab_flota.py:140`): snapshot + modo historia. Motor (`_tab_motor.py:64`): curva, SHAP y estado. Casos (`ui_batch.py:192`/`ui_inference.py:455`): lote y vivo a gemelo. Auditoría (`_tab_auditoria.py:48`): traza y PDF. Estrés (`_sandbox_estres.py:42`): sandbox con caché, no pestaña.

> [!question]- ¿Qué es el modo historia y quién lo protege?
> Cuatro pasos guiados con datos vivos (`ui_alta.py:92`, botones `historia_1..4` en flota); lo protegen 20 tests de interacción que fallan antes que el taller.
