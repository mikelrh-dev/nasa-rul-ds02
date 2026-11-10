# Proposal: Novel n8n action — HTTP call to the project's own API

**Change:** `2026-11-10-n8n-accion-propia`
**Capability:** `ds02-n8n-decision` (ADDED: own-API action)
**Branch:** `fix/auditoria-2026-11-10`
**Date:** 2026-11-10

## Intent

MIA-3 (35 % of MIA) is capped at **7** because the four n8n actions
(Sheets, Postgres, Calendar, Gmail) are the ones seen in class; criterion 10
requires an action **not** seen in class. The audit
(`docs/informes/auditoria-2026-11-10-rubrica-integral.md`, H4) confirms it:
J2 checked the class workflows in the live instance and the flow is a
sub-set of them. The instance at `localhost:5678` is alive and the flow
`DS02 Decision MIA-3` is active.

## Scope

### In Scope
- `POST /n8n-decision` in `app/api.py`: token auth via
  `hmac.compare_digest` against `N8N_WEBHOOK_TOKEN`, `decision` in
  {APTO, INSPECCION, HANGAR}, idempotent append by `fingerprint` into
  `app/registros_n8n.json`, 503 when the env token is unset.
- One `n8n-nodes-base.httpRequest` node on the HANGAR branch, after Gmail,
  POSTing to `http://localhost:8000/n8n-decision` with the token in
  `X-DS02-Token`; every other node and connection intact.
- `tests/test_n8n_propia.py` (happy 200, bad token 401, bad decision 400,
  duplicate fingerprint 200 `recorded:false`, unset token 503).
- One doc line in `docs/defensa/guiones-15min.md` and `src/clase/README.md`.

### Out of Scope
- Archive, commits, pushes, retraining, any file under `models/`.
- Changing the APTO/INSPECCION branches, the webhook, the Switch or the
  existing four actions.
- Making the app call the new endpoint (the app keeps its single
  `enviar_decision(` call site).

## Capabilities

- **New Capabilities:** None.
- **Modified Capabilities:** `ds02-n8n-decision` — ADDED requirement
  `Own-API n8n action` (the endpoint, the flow node, their contract).
  Deployed spec: [`openspec/specs/ds02-n8n-decision/spec.md`](../../specs/ds02-n8n-decision/spec.md).

## Approach

Add a token-guarded write endpoint next to `/predict` that records the
decision in a JSON log, and let n8n call it as the fifth action of the
HANGAR chain. Idempotency by `fingerprint` makes a retry harmless, which
is the property the audit asked for.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/api.py` | Modified | New `POST /n8n-decision` route + models |
| `n8n/flujo.json` | Modified | New HTTP Request node + connection |
| `app/registros_n8n.json` | New | Decision log (git-ignored, per-machine) |
| `tests/test_n8n_propia.py` | New | 5 tests for the endpoint contract |
| `docs/defensa/guiones-15min.md`, `src/clase/README.md` | Modified | One line naming the novel action |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Rate limiter (10/min) rejects the n8n write | Low | `/n8n-decision` is a dependency, so it is not throttled; documented |
| Appending duplicates | Low | `fingerprint` check before write |
| Tests write into the real log | Low | `tmp_path` + `monkeypatch` path |
| Breaking existing n8n/API tests | Low | Existing routes untouched; run the four named files |

## Rollback Plan

- Delete `POST /n8n-decision` and its models from `app/api.py`.
- Remove the `HANGAR API propia` node and its connection from `n8n/flujo.json`.
- Delete `tests/test_n8n_propia.py` and revert the two doc lines.
- `app/registros_n8n.json` is disposable; no migration, no model artifact.

## Dependencies

- `N8N_WEBHOOK_TOKEN` in the environment of the API process; the token
  travels in `X-DS02-Token`, never in the repo.
- The API must be reachable at `http://localhost:8000` from the n8n host.

## Success Criteria

- [ ] `POST /n8n-decision` returns 200 with `recorded: true`, 401 on a bad
      token, 400 on a bad decision, 200 `recorded: false` on a duplicate
      fingerprint and 503 when `N8N_WEBHOOK_TOKEN` is unset.
- [ ] `n8n/flujo.json` parses and the HANGAR chain ends in a
      `n8n-nodes-base.httpRequest` node pointing at `/n8n-decision`.
- [ ] `tests/test_n8n_propia.py` plus the four existing n8n/API test files
      pass with exit 0.
- [ ] The five protected artifact hashes do not move.

Detailed evidence: [`verify-report.md`](verify-report.md).
