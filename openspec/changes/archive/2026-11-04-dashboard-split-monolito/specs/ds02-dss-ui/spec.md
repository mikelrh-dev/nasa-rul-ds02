# Delta for ds02-dss-ui — dashboard-split-monolito (pure refactor)

Pure structural refactor, no behavior change. Per proposal: New capabilities None, Modified capabilities None. All existing `ds02-dss-ui` requirements are preserved verbatim; this delta records only the refactor invariants.

## ADDED Requirements

### Requirement: Dashboard orchestrator facade

`app/dashboard_ds02.py` MUST become a thin orchestrator: per-tab logic (flota, motor, auditoria, casos, sandbox) SHALL live in `app/ui_modulos/*`, and the dashboard SHALL re-export the moved names so existing imports keep working. The module-level hot path (`windows/telemetry/frame_cache`, corregir+decidir) MUST stay byte-identical in behavior.

#### Scenario: Import compatibility

- GIVEN the pre-split dashboard is importable
- WHEN `app/ui_modulos/*` is extracted
- THEN `import app.dashboard_ds02` still succeeds and all five tabs render

#### Scenario: No logic change

- GIVEN the complete test suite
- WHEN `pytest tests -q` runs
- THEN all pre-existing contract tests pass with no outcome change

### Requirement: Single SHA-256 helper

The system MUST have exactly one `_sha256_cached` definition, owned by `app/ui_data_loader.py`. The duplicate at `dashboard:312` versus `ui_data_loader:162` SHALL be removed; the dashboard MUST import the shared helper.

#### Scenario: One definition

- GIVEN the refactored tree
- WHEN `grep -rn "_sha256_cached"` searches `app/`
- THEN exactly one `def _sha256_cached` exists and both call sites resolve to it

#### Scenario: Identical digests

- GIVEN the same file, size and mtime
- WHEN hashed before and after unification
- THEN the hex digest is unchanged and `None` is still returned on `OSError`

### Requirement: Single PREFIJO_ALTA constant

The system MUST have exactly one `PREFIJO_ALTA` definition. The duplicates at `flota.py:31` and `ui_alta.py:15` SHALL be unified in one owner module; the other MUST import it.

#### Scenario: One definition

- GIVEN the refactored tree
- WHEN `grep -rn "PREFIJO_ALTA"` searches `app/`
- THEN exactly one assignment exists and `unit_id` mapping is unchanged

### Requirement: Cache and signature invariants preserved

`frame_cache` MUST keep `@st.cache_data(ttl=3600)` semantics, the ola-2 SHAP cache MUST keep its hit behavior, and PDF work-order exports MUST keep their artifact-hash signature. None of these lifetimes or keys SHALL change.

#### Scenario: Rerun without metric drift

- GIVEN an unchanged cache
- WHEN the dashboard re-runs
- THEN every metric equals its pre-refactor value

#### Scenario: SHAP cache hit

- GIVEN SHAP already computed for a unit
- WHEN the dashboard re-runs
- THEN the cached result is reused with no recomputation

#### Scenario: PDF never stale

- GIVEN a replaced artifact on disk
- WHEN a work-order PDF is exported
- THEN its `artefacto_sha256` reflects the file currently on disk

### Requirement: Artifact byte-compatibility

`models/`, `app/cache/`, `src/`, `mia/` and rules MUST stay byte-compatible: `*.joblib`, `*.keras`, `ds02_manifest.json`, Parquet tables and provenance SHA-256 SHALL NOT change, and module import SHALL NOT require TensorFlow.

#### Scenario: Hashes unchanged

- GIVEN recorded SHA-256 for `models/` and `app/cache/`
- WHEN the refactor is complete
- THEN every hash matches and no new file appears under `models/`

#### Scenario: Import without TensorFlow

- GIVEN TensorFlow uninstalled or unimportable
- WHEN `app/ui_modulos/*` is imported
- THEN the import succeeds and T12 figures still come only from `app/cache/`

### Requirement: Stacked-to-main local chain

The change SHALL be delivered as stacked local slices into `main`, confirmed by the user: each tab extraction is one reviewable work unit, never one >400-line commit, with `pytest tests -q` and a headless render gate per slice before moving to the next. No push occurs from this spec phase.

#### Scenario: Slice gating

- GIVEN a stacked slice is ready
- WHEN it lands on its parent stack branch
- THEN `pytest tests -q` is green and the headless render succeeds

## MODIFIED Requirements

None — no existing `ds02-dss-ui` requirement text or scenario changes.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
