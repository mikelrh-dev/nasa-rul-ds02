# Delta for ds02-live-evaluation

**Change:** `2026-11-06-app-fixes-2`
**Capability:** `ds02-live-evaluation` (fifth tab, same frozen bundle)

## ADDED Requirements

### Requirement: Spanish thousands separator in live and batch text

Live and batch validation messages (`app/ui_inference.py`, `app/ui_batch.py`) MUST format thousands with `.` via `fmt_miles` so a cap of 5000 reads `5.000`, never `5,000`. The NASA score remains a SUM with no 125-cycle clamp on DS02; formatting changes no validation outcome.

#### Scenario: Cap message uses dot

- GIVEN `MAX_FILAS` 5000
- WHEN `preflight` rejects an over-cap table
- THEN the error contains `5.000` and not `5,000`
