```yaml
schema: gentle-ai.verify-result/v1
evidence_revision: sha256:f9f224c4e28563e30da1fb1a3d3024fa14fdcf58b218447b12d91ef5bb3c69bd
verdict: pass
blockers: 0
critical_findings: 0
requirements: 9/9
scenarios: 10/10
test_command: .venv/Scripts/python.exe -m pytest tests/test_dss_ui.py tests/test_n8n_decision.py tests/test_engine_flow.py -q
test_exit_code: 0
test_output_hash: sha256:f9f224c4e28563e30da1fb1a3d3024fa14fdcf58b218447b12d91ef5bb3c69bd
build_command: .venv/Scripts/python.exe -m py_compile app/entrypoints/dashboard_ds02.py app/lib/dashboard_helpers.py app/ui/_tab_auditoria.py app/ui/_tab_flota.py tests/test_dss_ui.py tests/test_n8n_decision.py tests/test_engine_flow.py
build_exit_code: 0
build_output_hash: sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

## Verification Report

**Change**: `2026-11-13-cierre-hallazgos-app-n8n`
**Branch**: `refactor/estructura-ds02-clase-2026-11-10`
**Version**: N/A (delta specs; `ds02-dss-ui` 4 ADDED, `ds02-n8n-decision` 4 ADDED + 1 MODIFIED)
**Mode**: Strict TDD (`strict_tdd: true` in `openspec/config.yaml`; pytest runner available)
**Date**: 2026-11-13
**Scope**: proposal + specs (`ds02-dss-ui`, `ds02-n8n-decision`) + design + tasks. Apply commit `6df719e`.

> Validator note: `gentle-ai sdd-verify-validate` is not available in this environment
> (`gentle-ai 4.0.0` → `Error: unknown command "sdd-verify-validate"`). This report is
> persisted per the direct verify request, without machine admission. Every hash below
> is a real digest of a real command output from this run, not a fabricated value.

### Completeness

| Metric | Value |
|--------|-------|
| Tasks total (tasks.md) | 13 |
| Tasks complete (`[x]`) | 13 |
| Tasks incomplete | 0 |
| Requirements (deltas) | 9 (ds02-dss-ui: 4 ADDED; ds02-n8n-decision: 4 ADDED + 1 MODIFIED) |
| Scenarios (deltas) | 10 (ds02-dss-ui: 4; ds02-n8n-decision: 6) |

Task breakdown: Phase 1: 1.1–1.3 (3); Phase 2: 2.1–2.4 (4); Phase 3: 3.1–3.4 (4);
Phase 4: 4.1–4.3 (3); Phase 5: 5.1–5.2 (2). Phases 1–4 were already `[x]` in the apply
commit; 5.1 and 5.2 were executed by this verification and marked `[x]` afterwards
(see "Task reconciliation" below).

### Build & Tests Execution

**Build**: OK (`py_compile` exit 0, no output)

```text
$ .venv/Scripts/python.exe -m py_compile app/entrypoints/dashboard_ds02.py app/lib/dashboard_helpers.py app/ui/_tab_auditoria.py app/ui/_tab_flota.py tests/test_dss_ui.py tests/test_n8n_decision.py tests/test_engine_flow.py
py_compile_exit=0
```

**Tests (change scope)**: 81 passed, 0 failed, 0 skipped (exit 0)

```text
$ .venv/Scripts/python.exe -m pytest tests/test_dss_ui.py tests/test_n8n_decision.py tests/test_engine_flow.py -q
........................................................................ [ 88%]
.........                                                                [100%]
81 passed, 26 warnings in 23.98s
pytest_exit=0
```

Per-file collection: `tests/test_dss_ui.py` 37, `tests/test_n8n_decision.py` 33,
`tests/test_engine_flow.py` 11 (37 + 33 + 11 = 81).

**Full repo gate**: 458 passed, 3 failed, exit 1 — **GATE FAILED**, reproduces the
pre-existing MLflow condition documented in the proposal's Out of Scope.

```text
$ .venv/Scripts/python.exe scripts/operativo/verify_gate.py
...
FAILED tests/test_mlflow_backfill.py::test_notebooks_instrument_mlflow_live
FAILED tests/test_mlflow_live.py::test_all_notebooks_have_mlflow_header_and_log_cell
FAILED tests/test_mlflow_live.py::test_no_late_tfenable_onednn_opts
3 failed, 458 passed in 270.98s (0:04:30)
=== VERIFICATION GATE ===
target: tests (full suite)
GATE FAILED (exit 1)
gate_exit=1
gate_output_hash=sha256:22dc4c80d661f560992e51c1cb109d66c9f2af0e3d594db149520af2a423f8f4
```

The 3 failures are static checks over `notebooks/00_datos.ipynb`. They are unrelated to
this change and pre-existing:

- `git diff --stat a15eaf9..HEAD -- notebooks/ models/ scripts/` → empty (this change
  touches none of those trees).
- `git log --oneline a15eaf9~1..HEAD -- notebooks/` → empty (no notebook commit in the
  change).
- Re-running the 3 tests in isolation at HEAD reproduces the same 3 failures
  (`3 failed in 3.03s`), and the proposal lists them explicitly under Out of Scope
  ("Los tres fallos de test de MLflow preexistentes (ajenos a este cambio)").

**Coverage**: not available (no coverage threshold configured; not measured).

### Spec Compliance Matrix (requirement → scenario → test → result)

#### ds02-dss-ui (4 ADDED requirements)

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Auditoría no rompe con un manifiesto sin bilstm_sha256 | Manifiesto sin bilstm_sha256 | `tests/test_dss_ui.py::test_auditar_hashes_no_rompe_sin_bilstm_sha256` (+ triangulate `test_auditar_hashes_toma_el_hash_del_manifiesto`) | ✅ COMPLIANT |
| Umbral inválido mantiene la app operable | Umbral invertido | `tests/test_dss_ui.py::test_umbral_invertido_mantiene_la_app_operable` (+ triangulate `test_umbral_valido_no_muestra_el_error_de_rango`) | ✅ COMPLIANT |
| «Ver gemelo» abre la ficha de un gemelo registrado | Gemelo registrado | `tests/test_engine_flow.py::test_ver_gemelo_selecciona_la_ficha_del_registrado` | ✅ COMPLIANT |
| Test del panel n8n con huella única | Dos pulsaciones | `tests/test_dss_ui.py::test_probar_n8n_huella_unica_por_pulsacion` | ✅ COMPLIANT |

#### ds02-n8n-decision (4 ADDED + 1 MODIFIED requirement)

| Requirement | Scenario | Test | Result |
|-------------|----------|------|--------|
| Umbrales del correo HANGAR desde el payload | Umbrales 25/20 | `tests/test_n8n_decision.py::test_gmail_umbrales_por_defecto_25_20`, `test_gmail_umbrales_ordenados_y_citados_en_el_texto` | ✅ COMPLIANT |
| Evento de Calendar con zona horaria | Zona y título | `tests/test_n8n_decision.py::test_calendar_declara_zona_europe_madrid`, `test_flujo_no_se_queda_con_la_zona_por_defecto` | ✅ COMPLIANT |
| idempotency_key en el insert de Postgres | Mapeo de la clave | `tests/test_n8n_decision.py::test_postgres_mapea_idempotency_key`, `test_postgres_schema_conoce_idempotency_key` | ✅ COMPLIANT |
| Fallback que distingue SIN_DECISION | SIN_DECISION | `tests/test_n8n_decision.py::test_fallback_set_distingue_sin_decision`, `test_fallback_telegram_distingue_sin_decision` | ✅ COMPLIANT |
| Flujo n8n importable con Switch de 3 ramas (MODIFIED) | Flujo válido y con las 3 ramas | `tests/test_n8n_decision.py::test_flujo_json_valido_con_3_ramas` | ✅ COMPLIANT |
| Flujo n8n importable con Switch de 3 ramas (MODIFIED) | El fallback recoge valores raros | `test_switch_fallback_output_extra`, `test_sin_decision_cae_en_el_fallback_no_en_una_regla`, `test_switch_tiene_4_salidas_conectadas`, `test_cada_rama_del_switch_avisa_por_telegram`, `test_fallback_no_ejecuta_acciones_y_avisa` | ✅ COMPLIANT |

**Compliance summary**: 10/10 scenarios compliant (each covered by at least one test
that passed at runtime in this run).

### Correctness (Static Evidence)

| Requirement | Status | Notes |
|-------------|--------|-------|
| Auditoría no rompe sin bilstm_sha256 | ✅ Implemented | `app/ui/_tab_auditoria.py`: expected hash read from `models/ds02_manifest.json` (`artifacts.bilstm_sha256`) with `provenance` fallback; explicit `None` guard before `[:12]`; warning instead of `TypeError` |
| Umbral inválido mantiene la app operable | ✅ Implemented | `app/entrypoints/dashboard_ds02.py`: `st.stop()` removed; `st.error` + preset restored into `session_state` and local thresholds; `app/ui/_tab_flota.py`: `max_value=threshold_apto - 1` on the hangar input |
| «Ver gemelo» abre la ficha | ✅ Implemented | `app/ui/_tab_flota.py`: `st.session_state["gemelo_detalle_sel"] = tarjeta["gemelo"]` in the `Ver gemelo` handler |
| Test del panel con huella única | ✅ Implemented | `app/lib/dashboard_helpers.py`: `probar_n8n()` uses `str(uuid.uuid4())` instead of the fixed `"test-panel"` |
| Umbrales Gmail 25/20 | ✅ Implemented | `n8n/flujo.json` HANGAR Gmail: `umA = (um.apto ?? 25)`, `umH = (um.hangar ?? 20)` |
| Calendar timeZone | ✅ Implemented | `n8n/flujo.json` HANGAR Google Calendar: `"timeZone": "Europe/Madrid"` + non-empty `summary` |
| idempotency_key en Postgres | ✅ Implemented | `n8n/flujo.json` HANGAR Postgres insert: `idempotency_key` column mapping + schema entry |
| Fallback distingue SIN_DECISION | ✅ Implemented | `n8n/flujo.json` FALLBACK Set + Telegram: ternary separating `SIN_DECISION` from unrecognized values |
| Flujo n8n con fallback (MODIFIED) | ✅ Implemented | `n8n/flujo.json`: Switch `fallbackOutput: "extra"`, `renameFallbackOutput: "SIN_DECISION"`, 4 connected outputs |

### Coherence (Design)

| Decision | Followed? | Notes |
|----------|-----------|-------|
| H1 reads the hash from the manifest | Yes | `manifest.artifacts.bilstm_sha256` with `provenance` fallback; no cache regeneration |
| H3 does not use `st.stop()` | Yes | `st.error` + preset restore; app keeps rendering sidebar and tabs |
| H2/H4/H5/H6a fixed in the flow JSON | Yes | `n8n/flujo.json` edited; live instance updated via n8n-mcp |
| H5 maps only, no UNIQUE/upsert | Yes | Column mapped; no DB migration (out of scope) |
| H6b fixes the twin selection | Yes | `gemelo_detalle_sel` set in the handler |
| No architecture/data change | Yes | Only `app/`, `n8n/`, `tests/` and the change folder touched |

### TDD Compliance (Strict TDD active)

The artifact store is `openspec`, so `apply-progress` is not persisted as a file
(`sdd-apply` persists it only in `engram`/`hybrid` mode). The TDD cycle evidence is
carried by `tasks.md` (explicit RED → GREEN → verify task per phase) plus the test
files, which is the openspec-mode convention. `apply-progress` was also searched in
Engram and is absent.

| Check | Result | Details |
|-------|--------|---------|
| TDD Evidence reported | ⚠️ | Not in an `apply-progress` artifact (not persisted in openspec mode); RED/GREEN pairs present in `tasks.md` phases 1–4 |
| All tasks have tests | ✅ | 4/4 phases have a RED task creating/extending a test file |
| RED confirmed (tests exist) | ✅ | `tests/test_dss_ui.py`, `tests/test_n8n_decision.py`, `tests/test_engine_flow.py` all exist and were extended by `6df719e` |
| GREEN confirmed (tests pass) | ✅ | 81/81 change-scope tests pass on execution (exit 0) |
| Triangulation adequate | ✅ | H1, H2, H3, H4, H5 and H6a each have a second test asserting a different expected value (manifest fallback, ordered defaults, valid pair, no default zone, schema column, Telegram text) |
| Safety Net for modified files | ✅ | `tests/test_dss_ui.py` and `tests/test_engine_flow.py` were modified, not created; the full pre-existing suite was run (458 passed) with no new failure attributable to this change |

**TDD Compliance**: 5/6 checks passed (the one ⚠️ is the missing openspec-mode
`apply-progress` artifact, not a missing test or a failing test).

### Test Layer Distribution

| Layer | Tests | Files | Tools |
|-------|-------|-------|-------|
| Unit | 33 | 1 | pytest (structural JSON assertions over `n8n/flujo.json`) |
| Integration | 48 | 2 | pytest + `streamlit.testing.v1.AppTest` (`tests/test_dss_ui.py`, `tests/test_engine_flow.py`) |
| E2E | 0 | 0 | not installed (`testing.e2e: false` in `openspec/config.yaml`) |
| **Total** | **81** | **3** | |

### Changed File Coverage

Coverage analysis skipped — no coverage tool detected (no `coverage`/`pytest-cov`
threshold configured in `openspec/config.yaml`).

### Assertion Quality

Audit of the tests added/modified by `6df719e` (H1/H3/H6c in `tests/test_dss_ui.py`,
H2/H4/H5/H6a in `tests/test_n8n_decision.py`, H6b in `tests/test_engine_flow.py`):

- No tautologies (`expect(true).toBe(true)`-style) found.
- No assertions without a production-code call: every test either renders the app via
  `AppTest` (real Streamlit script execution) or parses the real `n8n/flujo.json`.
- No ghost loops: the only loop-shaped assertion (`test_probar_n8n_huella_unica_por_pulsacion`)
  asserts a fixed 2-element collection and checks `len(set(...)) == 2`.
- No smoke-test-only cases: `test_auditar_hashes_no_rompe_sin_bilstm_sha256` asserts the
  two audit subheaders are still present, not just "no crash".
- No implementation-detail coupling: assertions target behaviour (selectbox value,
  session state, chart `alt`, JSON node fields), not CSS classes or mock call counts.

**Assertion quality**: ✅ All assertions verify real behaviour (0 CRITICAL, 0 WARNING).

### Quality Metrics

**Linter**: ➖ Not available (no linter configured/detected).
**Type Checker**: ➖ Not available (no `mypy`/`pyright` configuration detected).
**Compile**: ✅ `py_compile` exit 0 on all changed Python files.

### Live Flow Verification (task 5.2)

`n8n_validate_workflow` on the live workflow `hLlkHl3X33roWPEQ` ("DS02 Decision MIA-3"):

```text
valid: true
errorCount: 0
warningCount: 8   (strict profile; all pre-existing error-handling / typeVersion suggestions)
totalNodes: 13, enabledNodes: 13, validConnections: 12, invalidConnections: 0
```

`n8n_get_workflow` (filtered) confirms the live graph carries this change's fixes:

- HANGAR Gmail: `const umA = (um.apto ?? 25); const umH = (um.hangar ?? 20);`
- HANGAR Google Calendar: `"timeZone": "Europe/Madrid"`, non-empty `summary`
- HANGAR Postgres insert: `idempotency_key` column mapping + schema entry
- FALLBACK Set / Telegram: ternary separating `SIN_DECISION` from unrecognized values
- Switch: `fallbackOutput: "extra"`, `renameFallbackOutput: "SIN_DECISION"`

### Issues Found

**CRITICAL**: None.

**WARNING**:
- The full repo gate is **not green**: `scripts/operativo/verify_gate.py` →
  `GATE FAILED (exit 1)`, `3 failed, 458 passed`. All 3 failures are the pre-existing
  MLflow/notebook checks listed in the proposal's Out of Scope; this change touches
  neither `notebooks/`, `models/` nor `scripts/` (`git diff --stat a15eaf9..HEAD` empty
  for those trees). No green gate is claimed anywhere in this report.
- `apply-progress` is absent. In `openspec` mode `sdd-apply` does not persist it (only
  `engram`/`hybrid` do); Engram search also returns nothing. TDD evidence is carried by
  `tasks.md` RED/GREEN pairs + the test files. Recorded as a gap in the audit trail, not
  as a defect of the implementation.
- `gentle-ai sdd-verify-validate` is unavailable in this environment; this report was
  not machine-admitted.

**SUGGESTION**:
- Fix the 3 pre-existing MLflow notebook checks before the defense so the full gate is
  green; they are outside this change's scope.
- Persist `apply-progress` (e.g. hybrid mode) for future strict-TDD changes so the TDD
  Cycle Evidence table is machine-readable.

### Task reconciliation

Tasks 5.1 and 5.2 were unchecked at verification start. Both were executed by this
verification:

- 5.1 `python scripts/verify_gate.py` → executed; result is `GATE FAILED (exit 1)` due
  exclusively to the 3 pre-existing out-of-scope MLflow failures (evidence above). The
  change-scope suite is green (81/81).
- 5.2 App + live flow → executed: the app renders under `AppTest` in the change-scope
  tests (including the invalid-threshold path), and the live n8n workflow validates with
  `errorCount: 0` and carries all four flow fixes.

Both are marked `[x]` in `tasks.md` with the 5.1 caveat recorded in place, per the
orchestrator's explicit instruction to complete the loop. The reconciliation reason is
recorded here and in `archive-report.md`.

### Verdict

**PASS WITH WARNINGS** — all 9 delta requirements and 10 scenarios are compliant
(81/81 change-scope tests pass, exit 0; build/compile clean). The full repo gate is red
only because of 3 pre-existing, out-of-scope MLflow notebook failures that this change
does not touch; no green gate is claimed. Archive proceeds as an intentional
archive-with-warnings under the orchestrator's explicit instruction.
