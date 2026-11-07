---
tipo: sistema
status: sin-estudiar
tags:
  - n8n
  - mia-3
  - webhook
  - decision
---

# n8n y decisión MIA-3 — del veredicto a la acción

> [!abstract] En una frase
> La pestaña Casos decide con `decision_en_vivo` y, si la decisión es HANGAR o INSPECCIÓN, manda un POST al webhook `ds02/decision` de n8n para que el flujo reparta la acción.

## Contrato

| Entra | Sale |
|---|---|
| Traza de `decision_en_vivo` (ventana + alertas + decisión) | POST JSON a `ds02/decision` una vez por fingerprint, o nada si es APTO / SIN_DECISION |
| Resultado del POST (2xx o error logueado) | Dedupe en sesión + log local; nunca excepción a la UI |

## Cómo está implementado

| Pieza | Dónde | Qué hace |
|---|---|---|
| Payload desde la traza | `app/ui_n8n.py:15` `payload_desde_traza` | Construye el payload EXACTO sin re-clasificar ni incluir `X_raw` |
| Dedupe por fingerprint | `app/ui_n8n.py:52` `debe_notificar` | HANGAR/INSPECCION notifican; APTO solo log; SIN_DECISION nada |
| POST con timeout | `src/n8n.py:22` `enviar_decision` | `urllib` stdlib, timeout 5 s, `{ok,status,decision}` sin lanzar a la UI |
| Punto de llamada | `app/dashboard_ds02.py:1877` | Tras `decision_en_vivo` en la pestaña Casos; fingerprint de `live["contract"]` |
| Flujo n8n | `n8n/flujo.json` webhook `ds02/decision` | Switch por decisión → APTO=log, INSPECCION=Sheets, HANGAR=Postgres+Calendar+Gmail |

El payload se compone desde la traza tal cual: `decision`, `unidad`, `ciclo`, `rul_punto`, `limite_inferior`, `limite_superior`, `umbrales`, `usadas`, `porque`, `motivo`, `alertas_datos`, `artefacto_sha256` y `fingerprint` (que además viaja como `idempotency_key`). `decision`, `usadas` y `porque` se leen de `traza`; `motivo` es `" · ".join(porque)`; `ciclo`/`rul_punto`/`limite_inferior`/`limite_superior` salen de la ventana; la unidad sale del contrato (`unidad_simulada`) porque la ventana en vivo no trae columna `unit`.

`src/n8n.py` hace POST con `urllib.request`, timeout 5 s y cabecera `Content-Type: application/json`. La URL sale del parámetro o del env `N8N_WEBHOOK_URL`; sin URL no se envía. Valida `decision` en APTO/INSPECCION/HANGAR/SIN_DECISION y devuelve `{ok,status,decision}`. Cualquier error de red, timeout o HTTP se loguea y se devuelve como `ok=False`: nunca se lanza excepción a la UI.

`app/ui_n8n.py` es módulo puro, sin Streamlit. `debe_notificar(decision, fingerprint, enviadas)` filtra por decisión y por fingerprint ya en sesión (`st.session_state["n8n_enviadas"]`): HANGAR e INSPECCION notifican; APTO solo deja log local sin POST (`_log` en dashboard); SIN_DECISION nunca notifica. El dedupe dura lo que dure la sesión de Streamlit.

## El flujo n8n por ramas

- Webhook: `ds02/decision` (POST, `responseMode: onReceived`).
- Switch por `decision` con tres ramas:
  - **APTO** → Set log (`APTO unidad … ciclo …: sin acción`): solo constancia, sin acción externa.
  - **INSPECCION** → Google Sheets append (documento `DS02 Decisiones`, hoja `Decisiones`): fila con decision, unidad, ciclo, rul_punto, limite_inferior, motivo y fingerprint para revisión.
  - **HANGAR** → cadena en 3 pasos: Postgres insert en `ds02_decisiones` → Google Calendar evento → Gmail a operaciones.

El flujo está **inactivo** esperando credenciales (`"active": false` en `n8n/flujo.json`): faltan revisar Google Sheets, Postgres, Google Calendar y Gmail en la instancia local. El repo no guarda secretos. ID n8n `hLlkHl3X33roWPEQ`: es el flujo `DS02 Decision MIA-3` (`versionId ds02-mia3-v1`).

## Qué NO hace

No re-clasifica: prohibido `classify` en el payload, reutiliza la traza de `decision_en_vivo`. No incluye `X_raw` (numpy, no JSON). No crea endpoint `/decide` en la API: `/predict` no aplica reglas y la única vía de decisión es la pestaña Casos. No hay watcher autónomo en segundo plano: el punto de llamada es la evaluación en vivo que dispara el operario.

## Conexiones

- Decisión: [[s13-capa-de-reglas-y-decision]] · app: [[s14-app-y-despliegue]] · pestañas: [[s23-dss-por-pestanas]]
- Pendiente hermano: [[c27-mlflow]] (PIA-4) · negocio: [[c22-cuanto-vale-acertar]]

## Di esto en el tribunal

> [!quote] Di esto en el tribunal
> «La pestaña Casos decide con `decision_en_vivo` y, si es HANGAR o INSPECCIÓN, manda una vez por fingerprint un POST a n8n `ds02/decision` con la traza completa; el Switch reparte: APTO solo log, INSPECCIÓN a Sheets, HANGAR a Postgres, Calendar y Gmail».

## Flashcards

> [!question]- ¿Qué endpoint de n8n recibe la decisión?
> Webhook `ds02/decision` (POST) en `n8n/flujo.json`, con Switch por decisión.

> [!question]- ¿Qué lleva el payload?
> decision, unidad, ciclo, rul_punto, limite_inferior, limite_superior, umbrales, usadas, porque, motivo, alertas_datos, artefacto_sha256 y fingerprint.

> [!question]- ¿Cómo se envía el POST y qué pasa si falla?
> `src/n8n.py` con `urllib` stdlib, timeout 5 s, devuelve `{ok,status,decision}`; el error se loguea y se devuelve `ok=False`, nunca se lanza a la UI.

> [!question]- ¿Quién decide si se notifica?
> `app/ui_n8n.py` `debe_notificar` por fingerprint en sesión: HANGAR/INSPECCION notifican, APTO solo log local sin POST, SIN_DECISION nada.

> [!question]- ¿Qué hace cada rama del Switch?
> APTO=log, INSPECCION=Sheets, HANGAR=Postgres+Calendar+Gmail.

> [!question]- ¿En qué estado está el flujo?
> Inactivo (`active: false`, ID n8n `hLlkHl3X33roWPEQ`) esperando credenciales de Sheets, Postgres, Calendar y Gmail.
