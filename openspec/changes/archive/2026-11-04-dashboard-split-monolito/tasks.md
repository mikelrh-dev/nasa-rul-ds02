# Tasks: Split dashboard monolith into ui_modulos

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1800–2400 (moved lines count as +/−) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR1 foundation → PR2 sandbox → PR3 flota → PR4 motor → PR5 auditoria |
| Delivery strategy | auto-chain |
| Chain strategy | stacked-to-main |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | PR | Focused test | Runtime harness | Rollback boundary |
|------|------|----|--------------|-----------------|-------------------|
| 1 | Facade + shared helpers | PR1 | `python -m pytest tests -q` | Headless `AppTest` render | Delete `__init__.py`; restore imports |
| 2 | Sandbox | PR2 | `python -m pytest tests -q` | Headless render, all tabs | Remove `sandbox_estres.py`; restore hunk |
| 3 | Flota | PR3 | `python -m pytest tests -q` | Headless render, all tabs | Remove `tab_flota.py`; restore hunk |
| 4 | Motor | PR4 | `python -m pytest tests -q` | Headless render, all tabs | Remove `tab_motor.py`; restore hunk |
| 5 | Auditoria + compat | PR5 | `python -m pytest tests -q` | Headless render, all tabs | Remove `tab_auditoria.py`; restore hunk |

## Phase 1: Foundation and Facade

- [x] 1.1 Create `app/ui_modulos/__init__.py` re-exporting moved names. Acceptance: `import app.dashboard_ds02` succeeds.
- [x] 1.2 Unify `_sha256_cached`: sole definition in `app/ui_data_loader.py`; dashboard imports it. Acceptance: one `def` in `app/`; digest and `OSError→None` unchanged.
- [x] 1.3 Unify `PREFIJO_ALTA`: one owner module, other imports it. Acceptance: one assignment; `unit_id` mapping unchanged.
- [x] 1.4 Freeze invariants: keep `frame_cache ttl=3600`, ola-2 SHAP cache, PDF `artefacto_sha256`. Acceptance: cache/PDF tests unchanged.

## Phase 2: Core Extraction

- [x] 2.1 Extract `_sandbox_estres` to `app/ui_modulos/_sandbox_estres.py`; dashboard calls and re-exports it.
- [x] 2.2 Extract `_tab_flota` to `app/ui_modulos/tab_flota.py`; dashboard calls and re-exports it.
- [x] 2.3 Extract `_tab_motor` to `app/ui_modulos/tab_motor.py`; dashboard calls and re-exports it.
- [x] 2.4 Extract `_tab_auditoria` to `app/ui_modulos/tab_auditoria.py`; dashboard calls and re-exports it.

## Phase 3: Integration and Invariants

- [x] 3.1 Keep module-level `windows/telemetry/frame_cache` and corregir+decidir byte-identical in behavior in dashboard.
- [x] 3.2 Verify `ui_modulos` imports without TensorFlow; T12 figures come only from `app/cache/`.
- [x] 3.3 Verify `models/` and `app/cache/` hashes unchanged; no new files under `models/`.

## Phase 4: Testing and Verification

- [x] 4.1 Per slice, before the next: run `python -m pytest tests -q` and headless render of all tabs.
- [x] 4.2 Final gate: full pytest green; one `_sha256_cached` and one `PREFIJO_ALTA` definition.
- [x] 4.3 No commit, no push in this phase; stacked local slices only.

## Phase 5: Auditoria Extraction (PR5)

- [x] 5.1 Extract `_tab_auditoria` to `app/ui_modulos/_tab_auditoria.py` with lazy `dashboard_ds02` fallback; dashboard calls and re-exports it. Acceptance: body byte-identical to pre-split fragment; `import app.dashboard_ds02` succeeds.
- [x] 5.2 Preserve invariants: `frame_cache ttl=3600`, ola-2 SHAP cache, PDF `artefacto_sha256` byte-compatible. Acceptance: one `def _sha256_cached` in `app/`; `frame_cache`/`_informe_pdf_cached` unchanged in dashboard.
- [x] 5.3 Verify PR5 slice: run `python -m pytest tests/test_dss_ui.py tests/test_live_eval.py tests/test_mejoras_streamlit.py -q` and headless render of all tabs; no commit, no push. Acceptance: focused tests green and headless render without exception.
