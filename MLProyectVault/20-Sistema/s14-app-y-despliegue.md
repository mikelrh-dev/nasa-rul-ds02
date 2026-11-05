---
tipo: sistema
status: consolidado
tags:
  - app
  - despliegue
  - dss
---

# App y despliegue — del bundle al DSS

> [!abstract] En una frase
> El bundle no vive en un cuaderno: vive en una app con caché, API y contenedor que reproduce la inferencia.

## Contrato

| Entra | Sale |
|---|---|
| Ventanas crudas de un motor | RUL, banda y estado en pantalla |
| Bundle en `models/` | Inferencia idéntica en local, app y docker |

## Cómo está implementado

La superficie vive en `app/` con el bundle de `models/` y caché en `app/cache/`.

| Pieza | Qué hace | Dónde |
|---|---|---|
| `HybridStackingEnsemble` | `predict` y `predict_interval` en servicio | `src/ds02_rul/ensemble.py:101` |
| Carga perezosa | Recarga el `.keras` solo al primer uso | `src/ds02_rul/ensemble.py:82` |
| Ventanas por unidad | Orden por ciclo para inferencia real | `src/ds02_rul/inference.py:49` |
| Validación de ventana | Rechaza forma corta antes del modelo | `src/ds02_rul/inference.py:62` |
| Contenedor | Reproduce el entorno con pesos fijos | `Dockerfile` |

El flujo es el mismo que en train: crudo → scaler y ridges congelados → secuencia y tabular → bases → meta → EMA → banda → reglas. La diferencia es que aquí nada se ajusta: todo viene congelado de [[s12-persistencia-y-contrato]].

La caché evita recalcular ventanas y predicciones ya vistas. Si la caché y el bundle discrepan, manda el bundle: la caché se invalida, el manifiesto no.

Frontera producción (detalle en conceptos): validez dura vs aviso blando [[c23-validez-y-plausibilidad-ui]], ciclo gemelo→flota→hangar por sesión [[c24-gemelo-hangar-flota]], API con llave + rate-limit + SHA [[c25-seguridad-api-y-contrato]], límites no prometidos [[c26-deriva-y-limites]].

## La decisión que hay detrás

Se sirve el bundle exacto de disco en vez de reentrenar en el despliegue: el 4.338 defendido (bundle C) es el que sirve. Reentrenar en producción movería los decimales en ±0.1 sin mejorar nada ([[c14-ruido-y-reproducibilidad]]).

Se rechazó exponer solo el punto sin banda: la decisión opera sobre `L_inf` ([[s13-capa-de-reglas-y-decision]]). Una API sin intervalo invita a decidir sobre la media.

## Qué medimos

La app no tiene métrica propia: sirve las de [[e00-cifras-autoritativas]]. Su prueba es de identidad: misma ventana, misma predicción que `scripts/predict_ds02.py`.

El lead time por motor (9 / 23 / 17 en media) es lo que la pantalla traduce a plan de mantenimiento, no el RMSE suelto.

## El límite

> [!warning] Lo que el despliegue no promete
> La app no detecta cambio de distribución: si llega un régimen no visto, predice igual sin avisar. No hay monitor de deriva. Esa es la próxima frontera, no una prestación actual.
>
> **Pendientes declarados (rúbrica).** n8n (MIA-3, 35%: HANGAR → Postgres+Calendar+correo, INSPECCIÓN → Sheets, APTO → log) y MLflow (PIA-4, 20%: tracking de experimentos) van en el change siguiente, no en este. Si el tribunal los pide: están excluidos por alcance con diseño previsto, no olvidados. El negocio que sí cubre este change: [[c22-cuanto-vale-acertar]].

## Di esto en el tribunal

> [!quote]
> «La app carga el mismo bundle de disco con su manifiesto y sirve punto, banda y estado. Nada se reentrena en producción: misma ventana, misma predicción que el script de evaluación.»

## Flashcards

> [!question]- ¿Qué sirve la app?
> RUL, banda y estado por motor desde el bundle de disco.

> [!question]- ¿Qué se congela en producción?
> Todo: scaler, ridges, bases, meta, beta y banda. Nada se reajusta.

> [!question]- ¿Qué valida inference.py:62?
> Que la ventana tenga forma completa antes de predecir.

> [!question]- ¿Qué manda si caché y bundle discrepan?
> El bundle. La caché se invalida.

> [!question]- ¿Qué afirma esta nota en una frase?
> El bundle no vive en un cuaderno: vive en una app con caché, API y contenedor que reproduce la inferencia.

> [!question]- ¿Cómo la contarías en el tribunal?
> «La app carga el mismo bundle de disco con su manifiesto y sirve punto, banda y estado. Nada se reentrena en producción: misma ventana, misma predicción que el script de evaluación.»

## Conexiones

Antes: [[s13-capa-de-reglas-y-decision]] · Recorrido: [[n04-cadena-de-estado]] · Evidencia: [[e00-cifras-autoritativas]]
