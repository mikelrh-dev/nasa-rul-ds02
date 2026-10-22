# Proposal: engine passport, twin registry and hangar lifecycle

## Why

The DSS scores an engine and forgets it. Every unit the user brings enters as
`unidad = -1`, is validated only after the model loads, disappears when the tab
closes, and never reaches the fleet table. The hangar is a snapshot of one
simulated cycle with no entry, queue, workshop or return to service. For a live
demonstration — where someone hands over an unknown engine and asks what happens
to it — the surface can show a number but cannot manage an engine.

This change turns the stored prediction into a **twin**: one record per engine
with its identity, the series it produced, the band that produced it, and its
maintenance history.

## What changes

| # | Capability | Change |
| --- | --- | --- |
| 1 | Passport | Engine id, source and a fingerprint of the scored table, visible in the contract and in every document |
| 2 | Pre-flight | Validation, window count, envelope warnings and fingerprint computed **before** the model loads |
| 3 | Registry | Twins live in session state and appear next to the three cached units |
| 4 | Twin as record | The series is stored once; state and hangar are derived on read, so moving a threshold never rewrites history |
| 5 | Hangar | `EN_SERVICIO → INSPECCION_PROGRAMADA → AOG_DERIVADO → EN_TALLER → PRUEBA_EN_BANCO → EN_SERVICIO`, with the entry decision frozen |
| 6 | Truth loop | When the real RUL is known it is stored against the twin and accumulates coverage and error |

Alongside them, two carried-over fixes: the fleet KPI reads the same frame as the
per-unit cards, and work orders carry the window identity (`start_index`).

## Non-goals

- No retraining, no change under `models/` or `app/cache/`.
- No server-side persistence. Twins live in the session and can be exported as
  JSON; a database is a separate decision.
- The hangar is operational bookkeeping, not a scheduling optimiser.

## Byte-compatible artifacts

`models/*`, `app/cache/*`, `mia/calibracion_banda.json` and `_p1_oof_cache.npz`
are untouched. The four recorded metric rows stay as measured. The gate keeps
its four exit codes.

## Rollback

The new logic lives in two modules (`app/twin.py`, `app/hangar.py`) and is wired
into the dashboard behind explicit widgets. Reverting the dashboard wiring
restores today's surface; the cached-unit path never depends on the new modules.
