# Delta for ds02-dss-ui

**Change:** `2026-11-06-app-fixes-1`
**Capability:** `ds02-dss-ui` (frozen bundle, `app/cache/`, conformal lower-bound triage)

## ADDED Requirements

### Requirement: Fleet reset removes twin and hangar

The system MUST treat Incorporar and Reset as symmetric: Incorporar adds one wall card in `tarjetas_cache` plus one in `tarjetas_gemelos`; Reset for that matricula MUST delete the alta, its twin and its hangar record from the session registry (session and disk). After Reset the wall MUST return to 3 cards (units 11, 14, 15).

#### Scenario: Incorporar then Reset restores 3

- GIVEN the base wall of 3 cache units
- WHEN an alta is incorporated then removed by Reset
- THEN the wall count goes 3→5→3
- AND `twins` and `hangar` no longer hold the matricula

#### Scenario: Cache fleet untouched

- GIVEN altas plus twins/hangar in one session
- WHEN Reset removes one matricula
- THEN units 11/14/15 cards remain
- AND another session registry is unchanged

### Requirement: Preset thresholds restore

The system MUST resync the threshold spinbuttons to the preset values whenever the preset changes: Normal 30/25, Prudente 35/30, Permisivo 25/20 (defaults 30/25 from provenance). Story-mode step 4 (current +5/−5, i.e. 35/20 from Normal) MUST NOT permanently contaminate Normal. Streamlit `value=` SHALL be overridden via `session_state` before the widget is read.

#### Scenario: Prudente then Normal restores 30/25

- GIVEN preset Normal at 30/25
- WHEN the operator selects Prudente then returns to Normal
- THEN the spinbuttons read 35/30 then 30/25
- AND the triage uses the resynced values

#### Scenario: History step does not stick

- GIVEN Normal at 30/25
- WHEN story step 4 applies 35/20 then the preset is cycled away and back
- THEN Normal reads 30/25 again
