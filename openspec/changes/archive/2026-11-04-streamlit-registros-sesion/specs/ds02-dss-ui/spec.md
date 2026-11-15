# Delta for ds02-dss-ui

Dashboard persistence moves from the single global
`app/registros_flota.json` shared by all users to per-session registries.
The deployed spec holds no registry-persistence requirement to modify, so
the change is recorded as ADDED below.
(Previously: one global fleet file, unisolated, ungoverned by any
requirement.)

## ADDED Requirements

### Requirement: Session-scoped twin, hangar and altas persistence

The dashboard MUST load and save `twins`, `hangar` and `altas` through the
per-session registry of `fleet-registries-session`, keyed by the validated
`session_id`. Existing twins/hangar/altas behavior MUST be preserved:
adding a twin registers it once, hangar membership and altas edits survive
a reload within the same session, and another session never observes them.

#### Scenario: Hangar flow survives reload in own session

- GIVEN a session where an engine was added to the hangar
- WHEN the dashboard reloads
- THEN the hangar still lists exactly that engine
- AND `twins` and `altas` are unchanged for that session

#### Scenario: Twins and altas editing are preserved

- GIVEN an existing twin and an `altas` record in a session
- WHEN the operator edits the altas record and saves
- THEN the session file holds the edited record after reload
- AND no duplicate twin is registered

#### Scenario: Work-order and metrics surfaces are untouched

- GIVEN the cache under `app/cache/` and frozen `models/` artifacts
- WHEN the session-scoped persistence is exercised
- THEN work-order export, charts and live metrics render as before
- AND `models/`, `app/cache/` and `src/ds02_rul/` stay byte-compatible
