# Spec delta: DS02 task-first UX (Streamlit)

**Change:** `2026-10-24-ds02-task-first-ux`
**Status:** Proposed
**Capability:** `ds02-dss-ui` (modification)

---

## ADDED

### Requirement: Single engine identity

The surface SHALL use one registry, `app/flota.py`, as the sole source of engine
names. Every view (wall, twins, hangar, orders) SHALL key an engine by its
registry key, and the registry SHALL be persisted in `app/registros_flota.json`
alongside `twins` and `hangar`.

- Cache engines (`11`, `14`, `15`) SHALL keep keys `U11`, `U14`, `U15` with
  labels taken from `L.UNIT_LABELS` and SHALL NOT be rewritten.
- An alta SHALL take its normalised matricula as its key (e.g. `EC-MKR`).
- A registered twin SHALL take its `engine_id` as its key (e.g. `ESN-DEMO-01`).
- `clave_de` SHALL degrade to `f"U{int(u)}"` for floats absent from the
  registry, so the cache keeps working without explicit entries.
- Alta ids SHALL never be reused: the counter SHALL live in the persisted
  registry and only grow (`max(existing ids) + 1`, prefix `-1000`).
- An alta SHALL create its twin from the cached windows, so it appears in
  "Gemelos registrados" with a saved series.

#### Scenario: One key per engine across all four views

- GIVEN engines `U11`, `U14`, `U15`, an alta `EC-MKR` and a twin `ESN-DEMO-01`
- WHEN each view renders for the same engine
- THEN the wall, the twin store, the hangar and the work order all use the same
  registry key
- AND no view falls back to a second key

#### Scenario: Alta persists and survives a reload

- GIVEN an alta `EC-MKR` created in the session
- WHEN the page is reloaded
- THEN `EC-MKR` is still present in the fleet register and in the hangar
- AND the toast names the key under which it appears

#### Scenario: Alta ids never collide

- GIVEN altas `AAA-111` and `BBB-222` created and `AAA-111` removed
- WHEN a third alta `CCC-333` is created
- THEN its id differs from every id ever issued
- AND no two engines share a `unit_id`

#### Scenario: Alta creates a twin

- GIVEN an alta created from a cached unit
- WHEN the alta completes
- THEN a twin exists with the cached windows already scored
- AND the engine appears in "Gemelos registrados" with a saved series

### Requirement: Turn-advance simulator

The surface SHALL advance the shared fleet clock and SHALL gate each engine by
state, reading the precomputed cache. The simulator SHALL be a pure module with
no Streamlit import, and SHALL NOT call the model.

The fleet clock SHALL advance for every engine that is not held. An engine whose
conformal lower bound has crossed the AOG threshold SHALL be held and SHALL NOT
advance further with the fleet.

The simulator SHALL derive every number from `app/cache/`: `pred`, `lower` and
`upper` are already scored per cycle. It SHALL NOT re-score windows, because the
point estimate is EMA-smoothed causally and the cache is built at `step=2`
while live scoring uses `step=1`; the two do not agree.

A reset SHALL replay the recorded life from the first scored cycle and SHALL be
labelled as a replay, not as a repair.

#### Scenario: Advancing does not call the model

- GIVEN a fleet at cycle N
- WHEN the advance control is pressed
- THEN the fleet reads the scored rows for the next cycles from `app/cache/`
- AND no inference call is made

#### Scenario: A held engine stops advancing

- GIVEN an engine whose `L_inf` has crossed the AOG threshold
- WHEN the fleet advances
- THEN that engine does not advance
- AND the others do

#### Scenario: The reset is honest

- GIVEN an engine reset after a workshop visit
- WHEN it returns to service
- THEN the interface labels the action as replaying the recorded life
- AND it does not claim the engine was repaired

### Requirement: Task-first information architecture

The surface SHALL present three task tabs, in this order: **Flota**, **Motor**,
**Evidencia**. Each tab SHALL answer one question:

- **Flota**: which engines are at risk today and what to do next.
- **Motor**: what is happening to this engine and why.
- **Evidencia**: how the number was produced and how trustworthy it is.

The five internal-layer tabs (hangar, RUL, sensors, audit, live) SHALL be folded
into these three and SHALL NOT be top-level tabs.

#### Scenario: Three tabs, one question each

- GIVEN a rendered page
- WHEN the tabs are inspected
- THEN there are exactly three tabs
- AND their labels contain "Flota", "Motor" and "Evidencia"

#### Scenario: No internal-layer tab is top level

- GIVEN the rendered page
- WHEN the tab labels are inspected
- THEN no top-level tab is named only "RUL", "Sensores", "Auditoría" or
  "Evaluar"

### Requirement: Landing entry

The first tab SHALL open with a single card that states, in plain language, (a)
what the system decides (the conformal lower bound governs; the point estimate is
a conservative quantile, `alpha = 0.35` per ADR-003), (b) the current fleet state
(monitored units, grounded units), and (c) one primary action to start.

The application SHALL open with a demo engine already selected when the registry
is empty and no demo seed has run in the session. The seed SHALL be session state
only and SHALL NOT be written to disk.

A guided script SHALL be available with a "next step" control that advances four
steps and then releases control to the user.

#### Scenario: The entry is self-explanatory

- GIVEN a first-time visitor with no prior knowledge of the project
- WHEN the application opens
- THEN the decision rule, the fleet state and the primary action are visible
  without opening documentation
- AND the time to understand is under 10 seconds

#### Scenario: Demo seed does not touch disk

- GIVEN an empty registry on first load
- WHEN the application renders
- THEN one cached engine is selected
- AND `app/registros_flota.json` is not created by the seed

#### Scenario: Guided script releases control

- GIVEN the guided script at its last step
- WHEN "next step" is pressed again
- THEN control returns to the user
- AND the fleet remains usable in free mode

### Requirement: Decision metric labelling

The decision metric SHALL be labelled "RUL p35 (conservative)" with a one-line
`help=` explaining that it is a conservative quantile and that the lower bound
governs the decision. Model-quality metrics (MAE, Macro-RMSE, coverage, bias)
SHALL live in Evidencia, not on the decision screen. The duplicate literal
"Unidades en hangar" SHALL appear once.

The two SHA values (window fingerprint and ensemble hash) SHALL live in a
"Provenance and contract" expander in Evidencia, and the window fingerprint
SHALL NOT be called "Huella" in the twin table.

#### Scenario: One KPI per concept on the decision screen

- GIVEN the decision screen
- WHEN its metrics are inspected
- THEN there is one KPI per concept (monitored units, grounded units, state of
  the selected engine)
- AND no quality metric appears there

#### Scenario: The quantile is named at the point of use

- GIVEN the badge showing the point estimate
- WHEN it is rendered
- THEN its label contains "RUL p35"
- AND a help tooltip explains the conservative quantile

### Requirement: Hangar as fleet register

The hangar SHALL display every engine in the registry with its lifecycle state,
not only AOG candidates. The derivation queue SHALL be a filter on top of the
register, not a separate list. The manual fallback
`registros.get(etiqueta) or registros.get(f"U{int(unit)}")` SHALL be removed.

#### Scenario: All engines are listed

- GIVEN a registry with cache, alta and twin engines
- WHEN the hangar renders
- THEN every engine appears with its lifecycle state
- AND the queue filter shows only AOG candidates without duplicating logic

## MODIFIED

### Requirement: Fleet snapshot (deployed)

The deployed requirement is retained. The fleet tab it describes is now the
**Flota** tab, and the snapshot SHALL cover every engine in the registry — cache,
alta and registered twin — not only the cache units. The clamping rule (a unit is
reported at its own last scored cycle, never extrapolated) and the no-data rule
are unchanged.

### Requirement: Work-order export (deployed)

The deployed requirement is retained. The work-order download SHALL live in the
**Motor** tab, next to the engine card it documents, rather than in the fleet tab:
the order belongs to the engine, not to the fleet. The export contract is
unchanged — only AOG units, with the artifact hash, the thresholds in force, the
simulated cycle and the per-unit lower bound that triggered the decision.

### Requirement: Physical sensor radiography (deployed)

The deployed requirement is retained. The surface that carries it is no longer a
top-level "sensor tab": it is the sensor section of **Evidencia**. The content
rules are unchanged — the dataset's own channel names (`T24, T30, T48, T50, P15,
P2, P21, P24, Ps30, P40, P50, Nf, Nc, Wf` and the four operating conditions),
grouped by physical meaning, plotting per-cycle evolution and shading the
critical `[0, 25)` band.

### Requirement: Engine-14 honesty panel (deployed)

The deployed requirement is retained. The panel is no longer a top-level "audit
tab": it is the audit section of **Evidencia**. Its content rules are unchanged —
measured facts, not narrative, and the sampling-density hypothesis labelled as
tested and discarded.

### Requirement: Themed and accessible surface (deployed)

The deployed requirement is retained. In addition, the entry card, the three tab
labels and the provenance expander SHALL satisfy the same rules: no injected
CSS, and every chart and grid SHALL carry a non-empty `alt=`.

### Requirement: Verification (deployed)

The deployed requirement is retained with the following change: the headless
render assertion SHALL expect **three** tabs whose labels contain "Flota",
"Motor" and "Evidencia", and the test list updated deliberately (tab-count
tests in `tests/test_dss_ui.py` and `tests/test_ui_rules.py`, and the
"El taller" label assertion in `tests/test_dss_interaction.py`) SHALL be recorded
in the same work unit. The demo-seed test impact is part of that record: because
`tests/conftest.py` empties the registry before every test, the seed fires in
every test, so the affected assertions SHALL be listed explicitly rather than
discovered by a red suite.

#### Scenario: The app renders headless

- GIVEN the cache and no browser
- WHEN the Streamlit app is executed by the test harness
- THEN no exception is raised
- AND three tabs are present with labels containing "Flota", "Motor" and
  "Evidencia"

## REMOVED

None.

## Related capabilities

The live-evaluation capability remains specified by
[`ds02-live-evaluation`](../../specs/ds02-live-evaluation/spec.md) and inherits this
surface's theme, `alt=` and read-only rules. Its content moves into Evidencia as
a section, so it is no longer a top-level tab: the deployed phrase "the fifth
tab" is superseded by this change.
