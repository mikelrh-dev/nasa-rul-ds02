# Proposal: app/ readability restructure (package layout + dead-code cleanup)

**Change:** `2026-11-11-app-reestructuracion-legibilidad`
**Status:** Proposed
**Capabilities:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md) (Modified); no new capability. `ds02-rules-engine` is touched by Phase 0 but gets no delta.

## Intent

`app/` has 25 modules and 8 401 LOC with flat imports, nine in-module
`sys.path.insert` calls, duplicated tokens and thresholds, and dead re-exports.
The change makes the tree readable without changing behavior: delete dead code,
unify duplicated helpers, close the `AppCtx` cycle, and move modules into a
package (`entrypoints/`, `ui/`, `lib/`, `services/`). Phase 0 fixes the
order-dependent `test_rules_gate.py` failure.

## Scope

**In:** Phase 0 re-exports `pava_causal_no_creciente` from `src/reglas.py`;
Phase 1 deletes 22 dead imports and unifies tokens, `_latin1`, `_ahora` and
thresholds; Phase 2 makes `_sandbox_estres` receive `AppCtx` and removes
`ctx_from_dashboard()`; Phase 3 adds `app/_paths.py`; Phase 4 creates
`app/__init__.py`, moves modules into packages, replaces flat imports and
removes in-module `sys.path.insert`.

**Out:** any behavior, metric, threshold, rule or cache change; `models/`,
`app/cache/`, `src/`, notebooks, `scripts/`, `n8n/`; new features or
dependencies.

## Capabilities

**New:** None.

**Modified:** `ds02-dss-ui` — cache/registry location invariant, package layout
and import contract, updated orchestrator-facade paths.

## Approach

Five gated phases (0-4), each closed by `python -m pytest tests -q` and a
headless render. Phase 0 is a prerequisite; Phases 1-2 change no behavior;
Phase 3 enables Phase 4; Phase 4 is the structural move.

## Affected Areas

- `app/dashboard_ds02.py`: dead imports, tokens, entrypoint move.
- `app/ui_modulos/*`: tokens, thresholds, `AppCtx` sandbox, move to `app/ui/`.
- `app/*.py` (lib): `_paths.py`, unified helpers, move to `app/lib/`.
- `app/api.py`: move to `app/services/`, `_paths.py`.
- `src/reglas.py`: Phase 0 re-export.
- `tests/`: flat imports, `AppTest` and structural paths.
- `README.md`, `app/README.md`: start commands.

## Risks

- `app/cache/` or `app/registros_sesiones/` moves with its module (High): Phase 3 first, `_paths.py` constant, hash the tracked cache files.
- Module resolution shadows `src/mia/reglas.py` (Medium): Phase 0 fix; gate passes isolated and in suite.
- Test churn from moved paths (Medium): update `AppTest.from_file` and structural paths together.
- A flat import survives (Medium): grep gate for `sys.path.insert` and flat app imports.

## Rollback Plan

`git checkout -- app/ src/reglas.py tests/ README.md` and delete the new
`app/__init__.py`, `app/_paths.py`, `app/entrypoints/`, `app/ui/`, `app/lib/`
and `app/services/`. Cache and registries are path-invariant; `models/`,
`app/cache/` and `src/mia/` are never written.

## Dependencies

Repository virtualenv (Python 3.12) and `pytest`; `streamlit run` from the
repository root after Phase 4. No new runtime dependency.

## Success Criteria

- [ ] `python -m pytest tests -q` green, including `test_rules_gate.py` in full suite and isolation.
- [ ] `grep -rn "sys.path.insert" app/` finds no library module.
- [ ] `app/cache/` and `app/registros_sesiones/` keep their paths and content.
- [ ] `models/`, `app/cache/` and `src/mia/` hashes unchanged.
- [ ] Headless render succeeds with the documented command.
