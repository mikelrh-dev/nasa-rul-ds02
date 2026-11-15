# Proposal: Split dashboard monolith into ui_modulos

**Change:** `dashboard-split-monolito` — Complexity 8/10
**Capability:** [`ds02-dss-ui`](../../specs/ds02-dss-ui/spec.md) (affected, behavior unchanged) · `rul-prediction-ds02` untouched

## Intent

`app/dashboard_ds02.py` (3749 lines measured, ~689 `st.*`, 38 inputs, 25 buttons) centralizes data, tabs, sandbox and audit. Extracting per-tab modules without behavior change removes the merge hotspot (2 agents already editing dashboard) and makes review possible.

## Scope

### In Scope
- Split `app/dashboard_ds02.py` into `app/ui_modulos/` (tab modules, sandbox, audit, flota, motor) with thin re-export facade; dashboard keeps module-level `windows/telemetry/frame_cache` hot path (L416-417, corregir+decidir L657-659) byte-identical.
- Unify duplicated `_sha256_cached` (`dashboard:312` vs `ui_data_loader:162`) in one source; unify `PREFIJO_ALTA` (`flota.py:31` vs `ui_alta.py:15`) in one source. Keep `frame_cache ttl=3600` and ola-2 SHAP cache untouched.
- No behavior, metric, or threshold change.

### Out of Scope
- No change to rules (`mia/`, `app/ui_rules.py`), models, cache build, or `frame_cache`/SHAP cache lifetimes.
- No new tab, widget, or visual redesign.

## Capabilities

### New Capabilities
None — pure structural refactor, no new spec.

### Modified Capabilities
None — `ds02-dss-ui` requirements (triage, fleet snapshot, audit) preserved verbatim; no delta spec.

## Approach

Extract leaf tabs first (`_tab_flota` ~L1117, `_tab_motor` ~L2012, `_tab_auditoria` ~L2370, `_sandbox_estres` L812-900), then shared helpers. Dashboard becomes orchestrator importing `ui_modulos.*`. Each slice is a work unit; stacked slices, not one 400+ line commit.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `app/dashboard_ds02.py` | Modified | Slim orchestrator; re-exports for compat |
| `app/ui_modulos/*` | New | Per-tab modules (flota, motor, auditoria, casos, sandbox) |
| `app/ui_data_loader.py` | Modified | Single `_sha256_cached` owner |
| `app/ui_alta.py`, `app/flota.py` | Modified | Single `PREFIJO_ALTA` owner |
| `models/`, `app/cache/`, `src/`, `mia/` | Unchanged | Byte-compatible: `*.joblib`, `*.keras`, `ds02_manifest.json`, Parquet + provenance SHA-256 preserved |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| 3.7k-line move breaks `st.cache_data`/session state wiring | High | Facade re-exports; `pytest tests -q` + headless render gate per slice |
| Concurrent edits by 2 agents collide | High | Freeze dashboard on non-overlapping branches; stacked PRs per tab |
| Budget >400 lines skips review | Med | Chain strategy: stacked PRs or recorded size-exception per `work-unit-commits` |

## Rollback Plan

Revert `ui_modulos` to direct import: delete `app/ui_modulos/`, restore `app/dashboard_ds02.py` from pre-split SHA (`git diff --stat` verify). No artifact rollback needed (no artifact change).

## Dependencies

- `pytest tests -q` green before/after; Streamlit headless render smoke.
- Coordination window with concurrent dashboard agents.

## Success Criteria

- [ ] `pytest tests -q` passes; dashboard renders headless with all tabs.
- [ ] `grep _sha256_cached` / `PREFIJO_ALTA` each resolve to one definition.
- [ ] `models/` + `app/cache/` hashes unchanged; `frame_cache ttl=3600` intact.
