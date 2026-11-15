# Spec delta: app-ux-bundle-fix — `ds02-dss-ui`

**Change:** `app-ux-bundle-fix`
**Status:** Proposed
**Capability:** `ds02-dss-ui` (delta; no change to `src/ds02_rul/`, `src/mia/`, `models/`).

## ADDED Requirements

### Requirement: Wall-to-Motor navigation via selected_unit

Clicking `Ver gemelo` on a cached-fleet card SHALL set `session_state["selected_unit"]`,
`session_state["unit"]` and `session_state["cycle"]` to that card's unit/cycle,
and SHALL point the user at the Motor tab (toast). Clicking it on a registered
twin SHALL behave as today (twin detail flow).

#### Scenario: Ver gemelo selects the unit in the Motor tab

- GIVEN the wall shows a cached card for unit 14 at cycle 25
- WHEN `Ver gemelo` is clicked
- THEN `session_state["selected_unit"] == 14`, `session_state["unit"] == 14` and
  the Motor tab header names unit 14

#### Scenario: Twin card keeps twin flow

- GIVEN a card for a registered twin
- WHEN `Ver gemelo` is clicked
- THEN the twin-detail flow is used (no `selected_unit` overwrite of a cache unit)

### Requirement: Visible n8n panel with last send and test button

The sidebar SHALL show an n8n panel with webhook state (configured/not), the last
send (decision, ok, status, timestamp) recorded from the Casos call site, and a
test-send button that calls `enviar_decision` with a synthetic APTO payload and
records the result. The panel MUST NOT crash when `N8N_WEBHOOK_URL` is unset.

#### Scenario: Panel shows state without a URL

- GIVEN no `N8N_WEBHOOK_URL` in the environment
- WHEN the app renders
- THEN the panel shows the webhook as not configured and no exception occurs

#### Scenario: Test button records the last send

- GIVEN a mocked successful send
- WHEN the test button is pressed
- THEN the last-send record shows decision APTO, ok=true and a timestamp

### Requirement: URL guard — no /app/terminal under app/

No file under `app/` SHALL contain the literal `/app/terminal`; the app root path
is `/`. The suite SHALL assert this as a regression guard.

#### Scenario: Guard passes

- GIVEN the `app/` tree
- WHEN scanning text files for `/app/terminal`
- THEN zero matches are found

### Requirement: Conservador/Agresivo presets

The preset selector SHALL include `Conservador (+10/+10)` and `Agresivo (−10/−10)`
in addition to Normal/Prudente/Permisivo, keeping hangar < apto for every preset.

#### Scenario: Presets stay ordered

- GIVEN the five presets and defaults 30/25
- WHEN each preset resolves
- THEN hangar < apto holds and Conservador raises both thresholds by 10

### Requirement: Contrast CSV, queue filter, work-order preview

Flota SHALL offer: (a) a contrast CSV export (per-window raw vs corrected lower
bound and decision); (b) a state filter over the hangar queue; (c) a preview
table of the work order (units, L_inf, action) before any download.

#### Scenario: Contrast CSV covers both readings

- GIVEN raw windows and the decided frame
- WHEN the contrast CSV is built
- THEN it carries unit, cycle, lower_raw, lower_corregida, decision columns

#### Scenario: Queue filter narrows the queue

- GIVEN queue records in AOG_DERIVADO and EN_TALLER
- WHEN the filter selects only AOG_DERIVADO
- THEN only AOG records are listed

#### Scenario: Work-order preview lists blocked units

- GIVEN an order with blocked units
- WHEN the preview renders
- THEN each blocked unit appears with its L_inf and action

### Requirement: Sparkline, reading indicator, T24/T2/T50 radiography, trajectory CSV

Each wall card SHALL render a sparkline of its L_inf series; the header SHALL
show whether the reading is raw (`cruda`) or corrected (`corregida`); the Motor
tab SHALL include a T24/T2/T50 radiography; and the Motor tab SHALL offer a
trajectory CSV (cycle, pred, lower, upper, decision) for the selected unit.

#### Scenario: Sparkline and indicator render

- GIVEN any fleet card and either toggle state
- WHEN Flota renders
- THEN a sparkline exists per card and the header indicator names the active reading

#### Scenario: T24/T2/T50 channels are drawn

- GIVEN telemetry for the selected unit
- WHEN the Motor tab renders
- THEN the radiography includes the T24, T2 and T50 channels

#### Scenario: Trajectory CSV is well-formed

- GIVEN a unit curve
- WHEN the trajectory CSV is built
- THEN it parses as CSV with one row per cycle

### Requirement: Second sandbox sensor

The sandbox SHALL let the user pick the perturbed sensor among T48 and one
additional sensor (default T48), and the cached scoring helper SHALL include the
sensor in its cache key.

#### Scenario: Second sensor perturbs that channel

- GIVEN sensor T24 selected with drift > 0 %
- WHEN the tramo is scored
- THEN T24 (not T48) carries the drift factor

### Requirement: Six-rule view

The Auditoría tab SHALL list the six decision rules from `src/mia/reglas.py`
(`REGLAS_DECISION`) with priority and rationale, read-only.

#### Scenario: All six rules are listed

- GIVEN `REGLAS_DECISION` with six entries
- WHEN the Auditoría tab renders
- THEN each rule name appears in the view

## MODIFIED Requirements

None.

## REMOVED Requirements

None.

## RENAMED Requirements

None.
