# Proposal: Session-Scoped Fleet Registries (Streamlit)

## Intent

`app/registros_flota.json` serves every Streamlit user (`app/dashboard_ds02.py:49-79`) with no session isolation, lock, or atomic write. Concurrent users overwrite one fleet. Isolate registries per `session_id` without breaking twins, hangar, or altas.

## Scope

### In Scope
- Per-`session_id` registries (`twins`, `hangar`, `altas`); path helper.
- Atomic write (temp file + rename) plus lock/`st.session_state` guard.
- Backward-compatible migration of global JSON `{twins, hangar, altas}`; backup, copy-not-move.
- Schema validation on load/save (`app/twin.py`, `app/hangar.py`, `app/flota.py`).
- Preserve twins/hangar/altas; byte-compatible `models/`, `app/cache/`, `src/ds02_rul/`.

### Out of Scope
- Full authentication or identity.
- External database/central store.
- Dashboard split or UI refactor.

## Capabilities

> Contract with sdd-spec. Capability `rul-prediction-ds02` ([deployed spec](../../specs/rul-prediction-ds02/spec.md)) is unaffected: no model/metric change.

### New Capabilities
- `fleet-registries-session`: session-isolated registries, atomic validated persistence, backward-compatible migration.

### Modified Capabilities
- `ds02-dss-ui`: dashboard persistence from one global file to per-session files.

## Approach

Path from `session_id`; `st.session_state` stays the per-session source. Save to `{path}.tmp`, then rename. First run copies legacy global JSON if the session file is absent; missing/corrupt JSON becomes an empty registry. Budget: 400 lines, 1 work unit.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/dashboard_ds02.py:49-79` | Modified | Session path, atomic save, migration |
| `app/hangar.py:165-181` | Modified | Atomic save, schema check |
| `app/twin.py:252-268` | Modified | Atomic save, schema check |
| `app/flota.py:137-147` | Modified | Schema check, missing-file behavior |
| `app/registros_flota.json` | Modified | Per-session files; legacy stays readable |
| `tests/` | New | Isolation, atomicity, migration |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Fleet loss on bad migration | High | Pre-migration backup; copy-not-move; count check |
| Race on concurrent save | Medium | Atomic rename + lock; interleaved-session test |
| Corrupt/missing JSON | Medium | `try/except`, empty fallback, schema validation |
| Orphan session files | Low | Documented cleanup policy; no auto-delete now |

## Rollback Plan

1) Stop app; 2) revert path to global `registros_flota.json`; 3) restore pre-migration backup (or `.hermes-respaldo`); 4) revert single commit. Legacy format stays readable, so no data transform is needed.

## Dependencies

- Streamlit `session_id`/`st.session_state` in pinned version.
- `python -m pytest tests -q` stays green.

## Success Criteria

- [ ] Two simultaneous sessions never overwrite each other.
- [ ] Reload preserves own fleet; other sessions unaffected.
- [ ] Existing global JSON migrates with zero record loss.
- [ ] Interrupted save leaves no truncated JSON.
- [ ] `python -m pytest tests -q` passes; `models/`/`app/cache/` untouched.
