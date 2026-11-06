# Capability spec: DS02 maintenance decision-support surface

**Capability:** `ds02-dss-ui`
**Deployed:** 2026-10-21
**Change:** [`2026-10-21-ds02-streamlit-dss`](../../changes/2026-10-21-ds02-streamlit-dss/proposal.md)
**Status:** Active

The Streamlit surface that turns the frozen DS02 bundle into a maintenance
decision: a fleet hangar governed by the conformal lower bound, the RUL curve with
its calibrated band, the physical sensor radiography, and the engine-14 audit.
It consumes `app/cache/` and `models/ds02_manifest.json` and never trains,
refits or rewrites an artifact.

---

## Requirements

### Requirement: Frozen artifacts are read-only

The UI SHALL consume the shipped DS02 artifacts and SHALL NOT retrain, refit,
rewrite or delete any file under `models/`, nor alter anything under
`src/ds02_rul/`.

#### Scenario: models/ is only opened for reading

- GIVEN the dashboard is started, used and stopped
- WHEN the run finishes
- THEN `models/ensemble.joblib`, `models/bilstm_ds02.keras`, `models/scaler.joblib`
  and `models/ds02_manifest.json` keep their recorded SHA-256
- AND no new file appears under `models/`

#### Scenario: The model is not loaded to draw the UI

- GIVEN the precomputed cache exists
- WHEN the application renders
- THEN TensorFlow and Keras are not imported
- AND every figure comes from `app/cache/`

### Requirement: Precomputed telemetry cache

The system SHALL provide a reproducible offline script that scores the DS02 test
split with the frozen bundle and writes two Parquet tables under `app/cache/`:
one row per scored window (unit, cycle, window start, ground truth, point
estimate, conformal lower bound, conformal upper bound) and one row per
downsampled telemetry row (unit, cycle, the four operating conditions and the
fourteen physical channels). It SHALL also write a provenance manifest recording
the artifact hash, the window/step contract and the per-unit window counts.

The cache SHALL reflect what the frozen bundle predicts: regenerating it SHALL NOT
change the numbers, and the band SHALL satisfy `lower <= point <= upper` for every
row with `lower >= 0`.

#### Scenario: Window counts match the evaluation contract

- GIVEN the DS02 test split at `STRIDE = 100`, window 50, step 2
- WHEN the cache is built
- THEN unit 11 has 3 293 windows, unit 14 has 760, unit 15 has 2 143
- AND the table holds 6 196 rows in total

#### Scenario: Regeneration is idempotent

- GIVEN an existing cache
- WHEN the script runs again
- THEN the same 6 196 rows are written with the same per-unit counts
- AND the metric block in the provenance manifest is unchanged

### Requirement: Conformal-governed triage

The maintenance state SHALL be decided by the conformal **lower** bound
(`L_inf`), never by the point estimate alone, and the thresholds SHALL be
configurable with defaults calibrated to the measured scale of this band:
airworthy `L_inf >= 30`, preventive `25 <= L_inf < 30`, AOG `L_inf < 25`.

At least one state MUST be reachable at the first scored cycle of every test
engine; a rule where no engine can ever be airworthy SHALL be rejected.

#### Scenario: States follow the lower bound

- GIVEN defaults of 30 and 25
- WHEN `L_inf` is 35.7, 30.0, 29.9, 25.0 and 24.9
- THEN the states are airworthy, airworthy, preventive, preventive, AOG

#### Scenario: The fleet starts airworthy

- GIVEN the first scored cycle of units 11, 14 and 15
- WHEN their lower bounds 35.7, 33.0 and 35.8 are classified
- THEN all three are airworthy
- AND no unit is grounded at cycle 1

#### Scenario: A blocked unit is blocked for the right reason

- GIVEN a unit whose lower bound falls below 25 while its point estimate is still
  above 25
- WHEN the state is computed
- THEN the unit is AOG
- AND the UI reports that the decision came from the lower bound, not from the
  point estimate

### Requirement: Fleet snapshot

The fleet tab SHALL show every test unit at the simulated cycle, clamping each
unit to its own last scored cycle, and SHALL show the count of grounded units for
that cycle. It SHALL also report the number of monitored units, the scored
windows, and the live mean absolute error inside the critical band.

A unit with no scored window at or before the simulated cycle SHALL be reported as
having no data, and SHALL NOT be assigned one of the three maintenance states.

#### Scenario: An engine that has not flown is not given a state

- GIVEN a fleet clock earlier than unit 14's first scored cycle
- WHEN the snapshot is built
- THEN unit 14 is reported as having no data
- AND it is neither airworthy nor grounded

#### Scenario: Shorter engines are clamped, not extrapolated

- GIVEN unit 11 ends at cycle 59 and the simulation is set to cycle 76
- WHEN the snapshot is built
- THEN unit 11 is reported at cycle 59 with its last state
- AND no value is invented beyond its life

#### Scenario: Grounded count follows the snapshot

- GIVEN a simulated cycle where two units are AOG
- WHEN the snapshot is displayed
- THEN the grounded-units KPI equals 2
- AND the maintenance queue lists those two units

### Requirement: Work-order export

The fleet tab SHALL offer a download for the grounded units as JSON and as CSV.
The export SHALL contain only units in the AOG state at the simulated cycle and
SHALL carry provenance: the artifact hash, the thresholds in force, the simulated
cycle and the per-unit lower bound that triggered the decision.

#### Scenario: Only grounded units are exported

- GIVEN one unit in AOG and two airworthy
- WHEN the work order is generated
- THEN the JSON has exactly one entry
- AND it names the unit, its cycle, its lower bound and its state

#### Scenario: Provenance travels with the order

- GIVEN a generated order
- WHEN it is inspected
- THEN it records the frozen artifact hash and the thresholds used
- AND it records nothing that could not be recomputed from the cache

### Requirement: Live metrics from cached predictions

Every metric shown SHALL be computed from the cached predictions and their
ground truth: window-weighted RMSE, macro-RMSE, per-engine RMSE, MAE and bias, and
the MAE per true-RUL band `[0, 25)`, `[25, 50)`, `[50, 75)`. The UI SHALL NOT
hardcode any metric value.

The manifest SHALL be displayed separately, clearly labelled as the frozen
artifact contract, so a reader can tell a live computation from a recorded one.

#### Scenario: Per-engine cards agree with the cache

- GIVEN the cached windows of unit 14
- WHEN its RMSE card is rendered
- THEN the value equals `sqrt(mean((pred - y_true)**2))` over those rows
- AND it is not taken from a literal in the source

#### Scenario: Manifest figures are labelled as recorded

- GIVEN the manifest audit card
- WHEN it shows the macro per-engine RMSEs
- THEN the values are the ones stored in `models/ds02_manifest.json`
- AND the card states that they come from the frozen contract, not from the cache

#### Scenario: The bands do not silently disagree

- GIVEN the live per-engine RMSE and the manifest's macro per-engine RMSE for the
  same unit
- WHEN both are visible
- THEN the difference, if any, is explained as regeneration drift
- AND neither figure is edited to match the other

### Requirement: Physical sensor radiography

The sensor tab SHALL use the dataset's real channel names — `T24, T30, T48, T50,
P15, P2, P21, P24, Ps30, P40, P50, Nf, Nc, Wf` for the physical sensors and
`alt, Mach, TRA, T2` for the operating conditions — grouped by physical meaning in
the selector. It SHALL plot the per-cycle evolution of the selected channels and
SHALL mark the critical band where the true RUL is below the AOG threshold — the
same `[0, 25)` band the metrics use.

#### Scenario: Names come from the file, not from FD001

- GIVEN the operating-condition and sensor selectors
- WHEN they are populated
- THEN the labels are the DS02 channel names
- AND no FD001 `s1 … s21` label appears

#### Scenario: The critical region is visible

- GIVEN a selected sensor series
- WHEN the chart is drawn
- THEN the cycles whose true RUL is below the AOG threshold are shaded
- AND the drift of the signal into that region is readable

### Requirement: Engine-14 honesty panel

The audit tab SHALL present engine 14 with measured facts, not narrative: its
window count, its sampling density relative to the fit engines, its live RMSE,
MAE and bias, and the error by RUL band. It SHALL state that the density
hypothesis was **tested and discarded** (`docs/informes/informe-2026-10-21-p0-p1-prior-de-vida.md`, bias
change −0.93 / −0.03 / +0.34 cycles) and that the evidence points to the
life-prior level shift instead, which the lower-bound triage absorbs.

#### Scenario: Discarded hypotheses are labelled as discarded

- GIVEN the root-cause panel
- WHEN it describes sampling density
- THEN it reports the measurement that refuted it
- AND it does not present density as the cause

#### Scenario: The safety argument is stated

- GIVEN a unit that is AOG while its true RUL is still above the threshold
- WHEN the panel explains the decision
- THEN it states that the lower bound is deliberately conservative
- AND it reports how many cycles early the alarm fires

### Requirement: Dataset isolation

The DS02 UI SHALL NOT read FD001 artifacts. `models/alarm_policy.json` and
`models/test_eval_ultima_ventana.csv` are FD001/v3 products and SHALL NOT be used
by this surface.

#### Scenario: No FD001 artifact is referenced

- GIVEN the UI source and the loader
- WHEN they are searched for `alarm_policy` and `test_eval_ultima_ventana`
- THEN neither string appears
- AND a test enforces this

### Requirement: Themed and accessible surface

The appearance SHALL come from `.streamlit/config.toml` (colors, fonts,
radii, chart palettes, padding), not from injected CSS. The charts SHALL use the
same design tokens as the widgets so the surface reads as one piece.

Every chart and every data grid SHALL carry a keyword `alt=` describing its
takeaway, so assistive technologies can name it.

#### Scenario: The theme is configuration, not CSS

- GIVEN the application source
- WHEN it is searched for `unsafe_allow_html` or `<style`
- THEN neither appears
- AND `.streamlit/config.toml` defines the dark base, the accent, the fonts and
  both 10-color chart palettes

#### Scenario: Every chart and grid is named

- GIVEN a rendered page
- WHEN the charts and dataframes are inspected
- THEN each one has a non-empty `alt`
- AND the `alt` describes the takeaway rather than repeating the axis labels

### Requirement: Verification

The change SHALL keep the existing artifact-contract suite green and SHALL add
tests for the triage thresholds, the cache contract, the work-order contract and
the dataset-isolation guard. The application SHALL render without an exception in
a headless run.

#### Scenario: The suite passes

- GIVEN the repository virtualenv
- WHEN `pytest tests -q` runs
- THEN the ten pre-existing contract tests still pass
- AND the new UI tests pass

#### Scenario: The app renders headless

- GIVEN the cache and no browser
- WHEN the Streamlit app is executed by the test harness
- THEN no exception is raised
- AND the five tabs are present

#### Scenario: The app renders in a real browser

- GIVEN the server running and a headless browser pointed at it
- WHEN the page finishes loading
- THEN the title, the tab labels and the fleet timeline are present in the DOM
- AND the configured background color is applied

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

### Requirement: Session-scoped twin, hangar and altas persistence

The dashboard MUST load and save `twins`, `hangar` and `altas` through the
per-session registry of `fleet-registries-session`, keyed by the validated
`session_id`. Existing twins/hangar/altas behavior MUST be preserved:
adding a twin registers it once, hangar membership and altas edits survive
a reload within the same session, and another session never observes them.

#### Scenario: Hangar flow survives reload in own session

- GIVEN a session where an engine was added to the hangar
- WHEN the dashboard reloads
- THEN the hangar still lists exactly that engine
- AND `twins` and `altas` are unchanged for that session

#### Scenario: Twins and altas editing are preserved

- GIVEN an existing twin and an `altas` record in a session
- WHEN the operator edits the altas record and saves
- THEN the session file holds the edited record after reload
- AND no duplicate twin is registered

#### Scenario: Work-order and metrics surfaces are untouched

- GIVEN the cache under `app/cache/` and frozen `models/` artifacts
- WHEN the session-scoped persistence is exercised
- THEN work-order export, charts and live metrics render as before
- AND `models/`, `app/cache/` and `src/ds02_rul/` stay byte-compatible

## Related capabilities

The fifth tab, which scores a unit the operator brings, is specified by
[`ds02-live-evaluation`](../ds02-live-evaluation/spec.md) and inherits this
surface's theme, `alt=` and read-only rules.

---

## Requirements (2026-11-06-app-fixes-1)

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
