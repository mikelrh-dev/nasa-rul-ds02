# Delta for ds02-dss-ui

**Change:** `2026-11-06-app-fixes-2`
**Capability:** `ds02-dss-ui` (frozen bundle, `app/cache/`, conformal lower-bound triage)

## MODIFIED Requirements

### Requirement: Fleet reset removes twin and hangar

The system MUST treat Incorporar and Reset as symmetric with no double-count: Incorporar adds one wall card in `tarjetas_cache` via `frame_con_altas` and the gemelo MUST NOT be duplicated in `tarjetas_gemelos` for the same matricula (it stays in Gemelos registrados). Reset for that matricula MUST delete the alta, its twin and its hangar record from the session registry (session and disk). After Incorporar the wall MUST be 4 cards; after Reset the wall MUST return to 3 cards (units 11, 14, 15).
(Previously: Incorporar added one card in `tarjetas_cache` plus one in `tarjetas_gemelos` for 3→5→3.)

#### Scenario: Incorporar then Reset restores 3

- GIVEN the base wall of 3 cache units
- WHEN an alta is incorporated then removed by Reset
- THEN the wall count goes 3→4→3
- AND `twins` and `hangar` no longer hold the matricula
- AND cache and gemelos labels are disjoint after Incorporar

#### Scenario: Cache fleet untouched

- GIVEN altas plus twins/hangar in one session
- WHEN Reset removes one matricula
- THEN units 11/14/15 cards remain
- AND another session registry is unchanged

## ADDED Requirements

### Requirement: Preset and correction refresh full app

The system MUST refresh the whole app when the fleet preset, its thresholds, or the correction toggle change: changing the preset or `aplicar_reglas` MUST trigger a full-scope rerun so `banda_en_uso`, `correccion_en_uso` and the triage recompute in the same pass. The `@st.fragment` on `app/ui_modulos/_tab_flota.py:139` MUST be kept for wall pagination.

#### Scenario: Preset change shows thresholds and band in one run

- GIVEN preset Normal at 30/25 with `aplicar_reglas` off
- WHEN the operator selects `Prudente (+5)` and the app runs once
- THEN the spinbuttons read 35/30 and the band caption is updated

#### Scenario: Toggle flips correction in the same pass

- GIVEN `aplicar_reglas` off
- WHEN the operator turns the toggle on and the app runs once
- THEN the correction caption switches to `R2b`+`R6` without a second widget interaction

### Requirement: Toggle label hit-area

The correction toggle MUST fire on a click on its label text. If the click does not fire, the label SHALL be shortened to `Correccion reglas (R2b+R6)` to enlarge the hit area. The widget SHALL carry an `on_change` that requests a full-scope rerun.

#### Scenario: Label click fires toggle

- GIVEN the Flota tab with the correction toggle off
- WHEN the operator clicks the toggle label text
- THEN the toggle value flips and the band caption updates

### Requirement: R9 evaluated row in Motor

The Motor view MUST render an evaluated-not-triggered row for `R9_HANGAR` by evaluating `src/mia/reglas.py:si_R9_HANGAR` on `L_inf` separately from the winning rule. When APTO, the row MUST read `evaluada, no dispara` and MUST NOT claim `dispara`; `src/mia/motor.py` MUST NOT be modified. NASA score remains a SUM with no 125-cycle clamp on DS02; this view changes no metric.

#### Scenario: APTO shows R9 evaluated but not triggered

- GIVEN `L_inf` 35.2 with thresholds 30/25
- WHEN the Motor view renders
- THEN the winning rule is `R7_APTO` and the row reads `R9 evaluada: No`
- AND the text contains `evaluada, no dispara` and not `dispara` as a claim

#### Scenario: Hangar shows R9 winning

- GIVEN `L_inf` 20 with thresholds 30/25
- WHEN the Motor view renders
- THEN the winning rule is `R9_HANGAR`

### Requirement: Spanish thousands separator

Spanish UI integers MUST use `.` as the thousands separator via `fmt_miles` in `app/ui_data_loader.py` (`f"{n:,}".replace(",",".")`). Live/batch error and warning text SHALL use the same helper. Formatting MUST NOT change any metric.

#### Scenario: Format uses dot

- GIVEN the integer 6196
- WHEN `fmt_miles` renders it
- THEN the output is `6.196` and never `6,196`
