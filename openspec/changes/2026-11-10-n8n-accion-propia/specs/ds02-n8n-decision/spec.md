# Delta for ds02-n8n-decision

**Change:** `2026-11-10-n8n-accion-propia`
**Capability:** `ds02-n8n-decision` (ADDED requirement)
**Deployed spec:** [`openspec/specs/ds02-n8n-decision/spec.md`](../../../specs/ds02-n8n-decision/spec.md)

---

## ADDED Requirements

### Requirement: Own-API n8n action on the HANGAR branch

The system SHALL expose a novel action, distinct from the class actions
(Google Sheets, Postgres, Google Calendar, Gmail): a `POST /n8n-decision`
endpoint in `app/api.py` that records a decision in a local log and is
idempotent by `fingerprint`.

The endpoint SHALL accept a JSON payload with exactly the keys `decision`,
`fingerprint`, `artefacto_sha256`, `unidad` and `token`. The endpoint
SHALL authenticate the caller by comparing `token` with the `N8N_WEBHOOK_TOKEN`
environment variable using `hmac.compare_digest`. A missing or invalid token
SHALL be rejected with `401`. A `decision` outside {APTO, INSPECCION, HANGAR}
SHALL be rejected with `400` and a message. When `N8N_WEBHOOK_TOKEN` is not
defined, the endpoint SHALL respond `503` with a clear message and SHALL NOT
prevent the application from starting.

On a valid request the system SHALL append a record
`{"decision", "fingerprint", "artefacto_sha256", "unidad", "ts"}` to
`app/registros_n8n.json`. If the `fingerprint` already exists in the log, the
system SHALL NOT append a duplicate and SHALL return `{"ok": true,
"recorded": false}`. Otherwise it SHALL return `{"ok": true, "recorded": true}`.

The n8n flow `DS02 Decision MIA-3` SHALL add a `n8n-nodes-base.httpRequest`
node on the HANGAR branch, after Gmail, that POSTs to
`http://localhost:8000/n8n-decision` with the payload and the token in the
`X-DS02-Token` header. Every existing node and connection SHALL remain intact.

#### Scenario: A valid HANGAR decision is recorded once

- GIVEN `N8N_WEBHOOK_TOKEN` is set and the log is empty
- WHEN a client POSTs a valid `HANGAR` payload with a new `fingerprint`
- THEN the response status is `200`
- AND the body is `{"ok": true, "recorded": true}`
- AND the log contains exactly one record with that `fingerprint`, the given
  `decision`, `artefacto_sha256`, `unidad` and a `ts` timestamp

#### Scenario: A repeated fingerprint is idempotent

- GIVEN the log already contains a record with fingerprint `fp1`
- WHEN a client POSTs a valid payload with the same `fingerprint`
- THEN the response status is `200`
- AND the body is `{"ok": true, "recorded": false}`
- AND the log still contains exactly one record with that `fingerprint`

#### Scenario: A bad token is rejected

- GIVEN `N8N_WEBHOOK_TOKEN` is set to a secret
- WHEN a client POSTs a valid payload with a different token
- THEN the response status is `401`
- AND the log is unchanged

#### Scenario: An invalid decision is rejected

- GIVEN `N8N_WEBHOOK_TOKEN` is set and a valid token is sent
- WHEN the client POSTs `decision` equal to `PARAR`
- THEN the response status is `400`
- AND the body carries an explanatory message
- AND the log is unchanged

#### Scenario: The endpoint is unavailable without a configured token

- GIVEN `N8N_WEBHOOK_TOKEN` is not defined
- WHEN a client POSTs any payload
- THEN the response status is `503`
- AND the body explains that the token is not configured

#### Scenario: The flow stays importable and gains the new action

- GIVEN `n8n/flujo.json`
- WHEN it is parsed as JSON
- THEN the HANGAR branch ends in a `n8n-nodes-base.httpRequest` node named
  `HANGAR API propia`
- AND that node POSTs to `http://localhost:8000/n8n-decision`
- AND the nodes and connections that existed before the change are unchanged

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
