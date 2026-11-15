# Tasks: Session-Scoped Fleet Registries (Streamlit)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 220-320 |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Session-scoped atomic registries + migration, `python -m pytest tests -q` green | PR 1 | `python -m pytest tests/test_fleet_registries_session.py -q` | Run `streamlit run app/dashboard_ds02.py` with 2 sessions, reload each, verify own fleet | Revert path to global `app/registros_flota.json`, restore pre-migration backup |

## Phase 1: Foundation (Validation + Paths)

- [x] 1.1 Add `validate_session_id()` in `app/dashboard_ds02.py:49-79`; reject `^[A-Za-z0-9_-]{1,64}$` violations, no file on error.
- [x] 1.2 Add `session_registry_path(session_id)` in `app/dashboard_ds02.py`; derive path only from validated id.
- [x] 1.3 Add `validate_registry_schema()` returning mapping with list `twins`/`hangar`/`altas`, used on load/save.

## Phase 2: Core Implementation (Atomic + Migration + Wiring)

- [x] 2.1 Add `atomic_save_json()` (tmp write, fsync, rename) + module lock in `app/hangar.py:165-181`; no side effects on failed validation.
- [x] 2.2 Add same atomic save + schema check to `app/twin.py:252-268` and `app/flota.py:137-147`; missing/corrupt JSON falls back visibly.
- [x] 2.3 Add `migrate_legacy_registry()` in `app/dashboard_ds02.py`: backup legacy JSON, copy (never move), count-check per collection, abort to backup on mismatch.
- [x] 2.4 Wire dashboard load/save in `app/dashboard_ds02.py:49-79` through session path, schema, atomic save; keep `models/`, `app/cache/`, `src/ds02_rul/` byte-compatible.

## Phase 3: Tests

- [x] 3.1 Tests in `tests/test_fleet_registries_session.py`: session isolation (`s1`/`s2` interleaved saves), invalid `session_id` creates no file.
- [x] 3.2 Tests same file: interrupted save keeps last valid JSON, success save leaves no `{path}.tmp`, corrupt/missing JSON falls back per spec.
- [x] 3.3 Tests same file: migration zero-loss (5/2/3, legacy unchanged), count-mismatch aborts, empty start without legacy.
- [x] 3.4 Tests same file: concurrency serialization per session; full `python -m pytest tests -q` green.

## Phase 4: Cleanup

- [x] 4.1 Document session-file cleanup policy (orphan files kept, no auto-delete).
- [x] 4.2 Confirm `git diff --stat` <= 400 lines; one work-unit commit, rollback restores global path.
