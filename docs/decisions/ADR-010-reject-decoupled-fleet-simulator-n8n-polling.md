# ADR-010: Reject decoupled fleet simulator via n8n polling (proposal #11)

## Status

Rejected — not implemented. Recorded as a hypothesis evaluated against the
repository's real architecture.

## Date

2026-10-31

## Context

Proposal #11, "Simulador de Flota Desacoplado (n8n Polling)", proposes that
Streamlit becomes a pure rendering surface: an external VPS running n8n sends
telemetry one cycle per second through an API, and the dashboard only paints
what it receives. The proposal is read-only with respect to the model.

The repository already contains the thing this proposal wants to replace: a
pure, in-process fleet simulator (`app/lib/simulacion.py`) that advances a shared
fleet clock over the scored cache (`app/cache/ds02_windows.parquet`). It never
calls the model; advancing the fleet is a read. The dashboard (`app/entrypoints/dashboard_ds02.py`)
holds the clock and the held-engine set in `st.session_state`, per browser
session.

## Architecture fit

Streamlit is a request/response UI server. Each browser tab owns its own
`session_state`; there is no server-side state shared between sessions and no
inbound channel for an external process to push telemetry into a running
dashboard. The only HTTP surface in the repo is the FastAPI artifact API
(`app/services/api.py`: `/health`, `/units`, `/predict`), which scores windows from the
cached dataset — it does not ingest telemetry and it is not consumed by the
dashboard.

For the proposal to work, Streamlit would have to (a) accept pushes from n8n,
(b) store them somewhere shared, and (c) poll or stream them back to every
client. That is a backend + store + transport, none of which exists in this
repository.

## Scores (proposal's own rating)

- Feasibility: 3
- Improvement: 9
- Risk: 10

The high improvement score is the appeal of a "live" fleet; the low
feasibility and maximal risk scores reflect that the gain requires building an
entire ingestion and transport layer around a framework that does not provide
one, for a demo that already advances the fleet from a cache.

## Verification — no pub/sub infrastructure exists

Checked on 2026-10-31 against the repository tree (excluding `.venv` and `.git`):

1. `docker-compose.yml` defines exactly two services: `api` (FastAPI, port 8000)
   and `dashboard` (Streamlit, port 8501). No broker, cache, or message-queue
   service.
2. `requirements.txt` contains no redis, kafka, paho-mqtt, websockets, aiohttp,
   celery, rq, amqp, nats, pulsar, or zmq dependency. The only HTTP libraries
   are those pulled by FastAPI/Streamlit themselves.
3. No Python module imports any pub/sub, broker, websocket, or streaming
   library. The only `async def` in `app/` is FastAPI's lifespan handler.
4. `app/entrypoints/dashboard_ds02.py` makes no outbound HTTP calls and exposes no
   WebSocket or server-sent-events endpoint. The fleet clock advances through
   `st.session_state` writes, not through external messages.
5. `app/services/api.py` has no telemetry-ingestion route, no `/telemetry`, no
   `/ingest`, and no subscription endpoint.

Conclusion: there is no pub/sub infrastructure in this repository, so adopting
the proposal would mean building it from scratch.

## Decision

Reject. Keep the fleet simulator in-process and cache-backed
(`app/lib/simulacion.py` + `st.session_state` clock), as it is today. Do not add
an external VPS/n8n telemetry path, a polling loop, or a shared store for a
read-only demo surface.

## Alternatives considered

- **Build the ingestion layer anyway (FastAPI + store + polling).** Rejected:
  adds runtime dependencies and a network hop to a demo that already advances
  the fleet deterministically from a cache; the gain is cosmetic and the risk
  (live network in front of a jury, state desync between wall and twin) is
  maximal.
- **Replace Streamlit with a framework that supports push.** Rejected: out of
  scope; the UI is pinned to Streamlit by the deployed spec and tests, and the
  change would touch every screen.
- **Keep the proposal as a future "live mode" behind a flag.** Rejected for now:
  no consumer of live telemetry exists, and the cache already encodes the full
  recorded life.

## Consequences

- No new runtime dependencies, no new services in `docker-compose.yml`, no
  writes outside `models/` or the cache contract.
- The fleet clock remains per-session and deterministic; the wall and the twin
  cannot disagree about an engine because both read the same cache.
- If a genuine live-telemetry requirement appears later, it must arrive with
  its own backend, store, and transport design and its own ADR; it cannot be
  bolted onto Streamlit through n8n polling.