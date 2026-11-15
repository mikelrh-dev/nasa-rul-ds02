# Tasks: app-ux-bundle-fix

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 220-320 |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Delivery strategy | size:exception |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Whole bundle (single entrypoint) | PR 1 | `python -m pytest tests/test_app_ux_bundle.py -q` | `python -m pytest tests -q` | `git checkout -- app/dashboard_ds02.py app/ui_modulos/` |

## Phase 1: RED tests

- [x] 1.1 `tests/test_app_ux_bundle.py`: `/app/terminal` guard, presets ordered, contrast CSV columns, queue-filter helper, trajectory CSV parse, 6-rule list, sandbox sensor in cache key. Acceptance: tests fail before apply.
- [x] 1.2 AppTest scenario: `Ver gemelo` sets `selected_unit`; n8n panel renders without env URL. Acceptance: AppTest passes pre-change where feasible, fails on `selected_unit`.

## Phase 2: Core implementation

- [x] 2.1 `app/dashboard_ds02.py`: add `Conservador (+10/+10)` / `Agresivo (−10/−10)` presets; consume `selected_unit` in deferred writes; n8n panel + `n8n_ultimo` state; header reading badge (cruda/corregida). Acceptance: Phase-1 tests green.
- [x] 2.2 `app/ui_modulos/_tab_flota.py`: `Ver gemelo` sets `selected_unit` + routes to Motor; wall sparkline per card; queue state filter; work-order preview table; contrast CSV download. Acceptance: AppTest scenario green.
- [x] 2.3 `app/ui_modulos/_tab_motor.py`: T24/T2/T50 radiography; trajectory CSV download. Acceptance: radiography channels + CSV parse tests green.
- [x] 2.4 `app/ui_modulos/_sandbox_estres.py` + dashboard helper: sensor selector (T48/T24) threaded through `_sandbox_puntua_cached`. Acceptance: sensor-in-key test green.
- [x] 2.5 `app/ui_modulos/_tab_auditoria.py`: six-rule view from `REGLAS_DECISION`. Acceptance: 6-rule list test green.

## Phase 3: Verification

- [x] 3.1 `python -m pytest tests/test_app_ux_bundle.py -q` green; `python -m pytest tests -q` green. Acceptance: exit 0, counts recorded.
- [x] 3.2 `verify-report.md` with PASS verdict and command evidence. Acceptance: all spec scenarios mapped to passing tests.
