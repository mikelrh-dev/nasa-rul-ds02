# Archive report: 2026-11-13-cierre-hallazgos-app-n8n

**Change**: `2026-11-13-cierre-hallazgos-app-n8n`
**Archived to**: `openspec/changes/archive/2026-11-13-cierre-hallazgos-app-n8n/`
**Date**: 2026-11-13
**Mode**: openspec
**Archive type**: intentional-with-warnings (user/orchestrator authorised completing the loop)

## Specs synced

| Domain | Action | Details |
|--------|--------|---------|
| ds02-dss-ui | Updated | 4 ADDED requirements appended (32 → 36); 0 modified/removed/renamed. Pure append: `git diff --numstat` = 52 insertions, 0 deletions. |
| ds02-n8n-decision | Updated | 4 ADDED requirements appended + 1 MODIFIED requirement replaced in place (5 → 9). `git diff --numstat` = 67 insertions, 2 deletions (the 2 changed lines belong to the replaced requirement). |

Merge was mechanical (a script spliced the delta requirement blocks read from disk into
the main spec; no artifact bytes passed through the model). All 9 delta requirement
blocks were verified present verbatim in the merged main specs, and every requirement
not mentioned by the deltas is preserved.

## Archive contents

- proposal.md ✅
- specs/ds02-dss-ui/spec.md ✅
- specs/ds02-n8n-decision/spec.md ✅
- design.md ✅
- tasks.md ✅ (13/13 complete)
- verify-report.md ✅ (PASS WITH WARNINGS)

## Source of truth updated

- `openspec/specs/ds02-dss-ui/spec.md`
- `openspec/specs/ds02-n8n-decision/spec.md`

## Mechanical copy evidence (MANDATORY readback)

Move: `git mv openspec/changes/2026-11-13-cierre-hallazgos-app-n8n openspec/changes/archive/2026-11-13-cierre-hallazgos-app-n8n` → `git mv OK`, source gone.

Verbatim `diff -r` of the pre-move recursive snapshot vs. the archived tree:

```text
$ diff -r "$snapshot_root/source" "openspec/changes/archive/2026-11-13-cierre-hallazgos-app-n8n"
diff_exit=0
```

The `diff -r` output is empty (no differences). `archive-report.md` is additive-only and
excluded from the comparison because it did not exist in the source snapshot.

## Final state

- Change-scope tests: `tests/test_dss_ui.py tests/test_n8n_decision.py tests/test_engine_flow.py` → **81 passed, 0 failed** (exit 0).
- Full repo gate: `scripts/operativo/verify_gate.py` → **GATE FAILED (exit 1)**, `3 failed, 458 passed`. The 3 failures are the pre-existing MLflow/notebook checks
  (`tests/test_mlflow_backfill.py::test_notebooks_instrument_mlflow_live`,
  `tests/test_mlflow_live.py::test_all_notebooks_have_mlflow_header_and_log_cell`,
  `tests/test_mlflow_live.py::test_no_late_tfenable_onednn_opts`) over `notebooks/00_datos.ipynb`.
  This change touches neither `notebooks/`, `models/` nor `scripts/` (`git diff --stat a15eaf9..HEAD` is empty for those trees), and the proposal lists them under Out of Scope.
- Live n8n workflow `hLlkHl3X33roWPEQ`: `valid: true`, `errorCount: 0`; the live graph carries the 25/20 Gmail defaults, `Europe/Madrid` Calendar `timeZone`, the Postgres `idempotency_key` mapping and the `SIN_DECISION`-aware fallback.
- `models/`, `notebooks/` and `scripts/` untouched by this change.

## Task reconciliation

Tasks 5.1 and 5.2 were unchecked in the persisted `tasks.md` at verification start. Both
were executed during verification and marked `[x]` with the 5.1 caveat recorded in place:

- 5.1 full gate: executed; `GATE FAILED (exit 1)` due exclusively to the 3 pre-existing
  out-of-scope MLflow failures. The change-scope suite is green (81/81).
- 5.2 app + live flow: executed; the app renders under `AppTest` (including the
  invalid-threshold path) and the live n8n workflow validates with `errorCount: 0`.

Reconciliation reason: the orchestrator explicitly instructed completing the verify +
archive loop, and `verify-report.md` proves the change's work is complete. No
implementation task was left unchecked; 5.1/5.2 are verification-phase tasks.

## Intentional archive-with-warnings

The archive proceeds with warnings, per the orchestrator's explicit instruction:

1. The full repo gate is **not green** (3 pre-existing, out-of-scope MLflow failures).
   No green gate is claimed anywhere; the change-scope suite is green.
2. `apply-progress` is absent. In openspec mode `sdd-apply` does not persist it (only
   `engram`/`hybrid` do); Engram search returns nothing. TDD evidence is carried by the
   `tasks.md` RED/GREEN pairs and the test files.
3. `gentle-ai sdd-verify-validate` is unavailable in this environment, so the
   `verify-report.md` was not machine-admitted.

No CRITICAL finding is recorded against this change's requirements or scenarios.

## SDD cycle complete

Planned, implemented, verified and archived. Ready for the next change.
