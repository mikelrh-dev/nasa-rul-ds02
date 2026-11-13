# Delta for ds02-n8n-decision

## ADDED Requirements

### Requirement: Umbrales del correo HANGAR desde el payload

El nodo Gmail de HANGAR MUST usar los umbrales del payload
(`umbrales.apto`/`umbrales.hangar`) y MUST tener 25/20 como valores por defecto,
no 30/25.

#### Scenario: Umbrales 25/20

- GIVEN un payload con `umbrales` 25/20
- WHEN se envía el correo de HANGAR
- THEN el texto muestra apto ≥ 25 / hangar < 20

### Requirement: Evento de Calendar con zona horaria

El nodo Calendar de HANGAR MUST declarar `timeZone` (Europe/Madrid) y un `summary`
no vacío.

#### Scenario: Zona y título

- GIVEN el nodo Calendar de HANGAR
- WHEN se inspecciona
- THEN `timeZone` es Europe/Madrid AND `summary` no es vacío

### Requirement: idempotency_key en el insert de Postgres

El nodo Postgres de HANGAR MUST mapear `idempotency_key` desde el payload.

#### Scenario: Mapeo de la clave

- GIVEN un payload con `idempotency_key`
- WHEN se inserta
- THEN la fila guarda ese `idempotency_key`

### Requirement: Fallback que distingue SIN_DECISION

El fallback del Switch MUST distinguir `SIN_DECISION` (sin acción, solo registro)
de una decisión no reconocida (aviso de payload).

#### Scenario: SIN_DECISION

- GIVEN `decision=SIN_DECISION`
- WHEN cae al fallback
- THEN el registro lo trata como SIN_DECISION, no como no reconocida

## MODIFIED Requirements

### Requirement: Flujo n8n importable con Switch de 3 ramas

`n8n/flujo.json` SHALL contener un workflow n8n válido (JSON parseable, formato de
exportación) con: nodo Webhook POST con path `ds02/decision`; nodo Switch con 3
ramas sobre `decision` (APTO / INSPECCION / HANGAR) y un fallback que recoge
`SIN_DECISION` y cualquier valor no reconocido sin ejecutar acciones críticas;
rama HANGAR con Postgres insert + Google Calendar + Gmail; rama INSPECCION con
Google Sheets append; rama APTO con Set (log). El JSON MUST NOT contener valores
de credenciales (solo referencias). Las credenciales viven en la instancia local
de n8n; el repo solo guarda el flujo.

(Previously: Switch con 3 ramas APTO/INSPECCION/HANGAR, sin fallback.)

#### Scenario: Flujo válido y con las 3 ramas

- GIVEN `n8n/flujo.json`
- WHEN se parsea como JSON y se inspeccionan los nodos
- THEN es válido, contiene un Webhook `ds02/decision` y un Switch con las 3
  salidas APTO/INSPECCION/HANGAR conectadas a sus acciones

#### Scenario: El fallback recoge valores raros

- GIVEN una `decision` fuera de APTO/INSPECCION/HANGAR
- WHEN llega al Switch
- THEN cae al fallback, que solo registra y avisa, sin acciones críticas

## REMOVED Requirements

None.

## RENAMED Requirements

None.
