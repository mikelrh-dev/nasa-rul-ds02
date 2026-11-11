# Spec delta: app/ readability restructure

**Change:** `2026-11-11-app-reestructuracion-legibilidad`
**Status:** Proposed
**Capability:** `ds02-dss-ui` (Modified). `ds02-rules-engine`: None.

This is a behavior-preserving refactor. The only requirement changes are the
cache/registry location invariant, the package layout and import contract, and
the orchestrator-facade paths. No metric, threshold, rule, cache row or frozen
artifact changes.

## ADDED Requirements

### Requirement: Stable cache and registry location invariant

The DS02 cache SHALL stay at `<repository>/app/cache/`, and the fleet registries
SHALL stay at `<repository>/app/registros_flota.json` and
`<repository>/app/registros_sesiones/`, regardless of where the owning module
lives. Path constants SHALL be owned by a single `app/_paths.py` module anchored
to a repository-root constant, and SHALL NOT be derived from `__file__` of a
movable module.

#### Scenario: The cache path survives the move

- GIVEN the cache at `app/cache/`
- WHEN `app/ui_data_loader.py` is moved to `app/lib/ui_data_loader.py`
- THEN `CACHE_DIR` still resolves to `<repository>/app/cache/`
- AND the three tracked cache files keep their paths

#### Scenario: The session registry survives the move

- GIVEN the session registry directory at `app/registros_sesiones/`
- WHEN `app/hangar.py` is moved to `app/lib/hangar.py`
- THEN `session_registry_path` still resolves under
  `<repository>/app/registros_sesiones/`

#### Scenario: No new cache directory

- GIVEN the refactored tree
- WHEN the app starts
- THEN no directory other than `app/cache/` is created for the cache

### Requirement: Package layout and import contract

The application SHALL be organised as a package: `app/entrypoints/` for the
Streamlit entrypoints, `app/ui/` for the tab and sidebar fragments, `app/lib/`
for pure helpers and data layers, and `app/services/` for the FastAPI surface.
`app/__init__.py` SHALL exist. Application modules SHALL import each other
through package paths and SHALL NOT mutate `sys.path`; the single allowed
bootstrap is the entrypoint adding the repository root.

#### Scenario: No sys.path mutation in library modules

- GIVEN the `app/lib/`, `app/ui/` and `app/services/` trees
- WHEN they are searched for `sys.path.insert`
- THEN zero matches are found

#### Scenario: Package imports resolve

- GIVEN the repository root on `sys.path`
- WHEN `app.lib.ui_data_loader` and `app.ui._tab_flota` are imported
- THEN each import succeeds and neither requires TensorFlow

## MODIFIED Requirements

### Requirement: Dashboard orchestrator facade

`app/entrypoints/dashboard_ds02.py` MUST be a thin orchestrator: per-tab logic
(flota, motor, auditoria, casos, sandbox) SHALL live in `app/ui/*`, and the
dashboard SHALL construct the `AppCtx` and pass it to every tab. The module-level
hot path (`windows/telemetry/frame_cache`, corregir+decidir) SHALL stay
byte-identical in behavior.

#### Scenario: Import compatibility

- GIVEN the package layout
- WHEN `app/entrypoints/dashboard_ds02.py` is imported
- THEN the import succeeds and all four tabs render

#### Scenario: No logic change

- GIVEN the complete test suite
- WHEN `pytest tests -q` runs
- THEN all pre-existing contract tests pass with no outcome change

## REMOVED Requirements

None.

## RENAMED Requirements

None.

## No delta

- `ds02-rules-engine`: None. Phase 0 adds `pava_causal_no_creciente` to the
  `src/reglas.py` re-export shim; it changes no rule, threshold or recorded
  figure. The deployed spec is absent from `openspec/specs/` (it lives in the
  active change `2026-10-21-ds02-rules-layer`), so no delta is opened here.
- `rul-prediction-ds02`, `ds02-live-evaluation`, `fleet-registries-session`,
  `shap-c-explanation`, `ds02-n8n-decision`: None; the change writes no
  artifact and changes no contract they own.
