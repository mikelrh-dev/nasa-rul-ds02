# Tasks: Novel n8n action — HTTP call to the project's own API

**Change:** `2026-11-10-n8n-accion-propia`
**Branch:** `fix/auditoria-2026-11-10`
**Capability:** `ds02-n8n-decision`

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~180 (endpoint ~70, flow node ~40, test ~110, docs 2) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single change |
| Delivery strategy | auto-chain |
| Chain strategy | pending |

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Endpoint + flow node + test + docs | PR 1 | `python -m pytest tests/test_n8n_propia.py tests/test_n8n_decision.py tests/test_n8n_apto_post.py tests/test_security_api.py -q -p no:cacheprovider` | `python -c "import json;json.load(open('n8n/flujo.json'))"` | `app/api.py`, `n8n/flujo.json`, `tests/test_n8n_propia.py`, two doc lines |

## Phase 1 — Foundation

- [ ] 1.1 Snapshot the five protected artifact hashes and the `app/api.py` / `n8n/flujo.json` hashes before editing.
- [x] 1.2 Add `app/registros_n8n.json` to `.gitignore` (per-machine state, next to `app/registros_flota.json`).

## Phase 2 — Core Implementation (strict TDD: RED first)

- [x] 2.1 Write `tests/test_n8n_propia.py` RED: happy path 200 `recorded:true`, invalid token 401, invalid decision 400, duplicate fingerprint 200 `recorded:false`, unset token 503, and the flow node/connection contract.
- [x] 2.2 Confirm RED: the new test file fails (no route, no node).
- [x] 2.3 Implement `POST /n8n-decision` in `app/api.py` (token via `hmac.compare_digest`, decision validation, fingerprint idempotency, atomic append, 503 when the env token is unset).
- [x] 2.4 Confirm GREEN: `tests/test_n8n_propia.py` passes.
- [x] 2.5 Add the `HANGAR API propia` `n8n-nodes-base.httpRequest` node to `n8n/flujo.json` after Gmail, POSTing to `http://localhost:8000/n8n-decision` with `X-DS02-Token`, keeping every other node and connection.
- [x] 2.6 Validate `n8n/flujo.json` with `json.load` and re-run the flow test.

## Phase 3 — Integration / Docs

- [x] 3.1 Add one line to `docs/defensa/guiones-15min.md` naming the novel action (own-API call) as the action not seen in class.
- [x] 3.2 Add one line to `src/clase/README.md` naming the same action.

## Phase 4 — Verification

- [x] 4.1 Run the focused suite: `python -m pytest tests/test_n8n_propia.py tests/test_n8n_decision.py tests/test_n8n_apto_post.py tests/test_security_api.py -q -p no:cacheprovider` and record exit code.
- [x] 4.2 Re-check the five protected hashes and confirm no file under `models/` moved.
- [x] 4.3 Write `verify-report.md` with the exact commands, exit codes and results.
