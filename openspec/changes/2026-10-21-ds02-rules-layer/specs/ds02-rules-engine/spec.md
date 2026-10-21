# Spec delta: the DS02 rules layer

**Change:** `2026-10-21-ds02-rules-layer`
**Capability:** `ds02-rules-engine` (new)
**Status:** Proposed
**Sources of truth:** `mia/reglas.py`, `mia/motor.py`, `mia/calibracion_banda.json`,
`INFORME_reglas_oof.md` §3, §5, §7 and §13

The rules layer is an independent post-processing pass over the RUL prediction.
It never retrains, refits or writes an artifact. Correction runs first (pass B);
decision runs second (pass A). This delta specifies the behaviour that shipped and adds one executable gate that keeps the recorded evidence honest.

## Engine contract at a glance

Each rule is a five-tuple `(name, condition, effect, priority, because)`. Within a
pass the engine applies the highest-priority rule whose condition holds, once per
rule, until no rule applies. It returns `{"decision", "usadas", "porque"}`.

| Rule id | Pass | Priority | Fires when | Effect |
| --- | --- | --- | --- | --- |
| `R2b_ISOTONICO_CAUSAL` | B | 2 | a unit history and a `rul_punto` exist | corrected point |
| `R6_BANDA` | B | 1 | a `rul_punto` exists | recalibrated band |
| `R1_SEGURIDAD` | A | 10 | `alertas_datos` is non-empty | `SIN_DECISION` |
| `R9_HANGAR` | A | 3 | valid data and `limite_inferior < hangar` | `HANGAR` |
| `R8_INSPECCION` | A | 2 | valid data and `hangar <= limite_inferior < apto` | `INSPECCION` |
| `R7_APTO` | A | 1 | valid data and `limite_inferior >= apto` | `APTO` |

---

## ADDED

### Requirement RULES-01: The correction pass returns the extremum of the causal prefix fit

The engine SHALL correct a unit's point estimate with `R2b_ISOTONICO_CAUSAL`,
defined as follows. The rows of one unit SHALL be ordered by `(cycle, start_index)`.
At position `t`, the engine SHALL compute the non-increasing weighted isotonic
regression (PAVA) of the prefix `y_1..y_t` and SHALL return the value of the last
block of that fit.

The value returned at `t` MUST depend only on positions `<= t`. The rule MUST NOT
read a later cycle; causality is part of the contract, not an implementation detail.

The PAVA fit of every prefix SHALL be non-increasing. That invariant does **not**
transfer to the series returned across `t`: when a high point joins the last block,
the extremum rises. The measured maximum positive increment over the 14 915 pure
OOF rows is **+1.328848** cycles. The rule name SHALL remain
`R2b_ISOTONICO_CAUSAL` and MUST NOT be replaced by a monotonicity claim.

Applying the rule SHALL replace `rul_punto` with the corrected value and set
`corregido_por_isotonico` to `True`.

#### Scenario: A value never depends on the future

- GIVEN a series and an extended series that shares its first two positions
- WHEN both are corrected
- THEN the first two returned values are identical
- AND the value at `t` equals the last block of the fit of the prefix `1..t`

#### Scenario: The fit is non-increasing while the returned series can rise

- GIVEN the series `[1.0, 2.0, 3.0, 0.5]`
- WHEN it is corrected
- THEN the returned series is `[1.0, 1.5, 2.0, 0.5]`
- AND at least one consecutive increment is positive
- AND the fit of each prefix is non-increasing across its positions

#### Scenario: The bridge applies the rule per unit in cycle order

- GIVEN the cached windows of a unit
- WHEN the correction is applied
- THEN rows are ordered by `(cycle, start_index)`
- AND the corrected value equals the PAVA result of that ordered series
- AND no row is dropped or duplicated

**Checks:** `tests/test_mia_rules.py::test_la_monotonia_es_causal`,
`tests/test_mia_rules.py::test_el_extremo_puede_subir_y_no_es_monotono_estricto`,
`tests/test_ui_rules.py::test_el_punto_corregido_es_el_ajuste_isotonico_causal`,
and the monotonicity table of `scripts/freeze_rules_evidence.py`.

### Requirement RULES-02: The strictly monotone variant is R2 and was rejected

The strictly non-increasing envelope of the returned series is, by identity,
`np.minimum.accumulate(serie)` — that is the running-min rule R2. The engine SHALL
NOT substitute that envelope for R2b, and SHALL NOT present it as an equivalent
variant. `min(PAVA)` reproduces R2 on all four recorded figures:

| Variant | OOF RMSE | OOF NASA | Test RMSE | Test NASA |
| --- | --- | --- | --- | --- |
| R2 running-min | 10.737 | 21053.0 | 3.964 | 1906.6 |
| R2b extremum of the prefix fit | 9.623 | 18713.9 | 4.173 | 2182.9 |
| `min(PAVA)` | 10.737 | 21053.0 | 3.964 | 1906.6 |

The gain of R2b therefore comes exactly from allowing the point to rise. Any text
that sells R2b as strict monotonicity describes a rule that was not measured. If
strict monotonicity is wanted, the rule is R2 and it is a separate decision, not a
relabelling of this one.

#### Scenario: The envelope collapses to the running minimum

- GIVEN any series corrected by R2b
- WHEN its strictly non-increasing envelope is taken
- THEN the envelope equals `np.minimum.accumulate(serie)` of the raw series
- AND it reproduces the R2 figures in the table above

**Checks:** `tests/test_mia_rules.py::test_la_envolvente_monotono_es_el_running_min`,
`tests/test_ui_rules.py::test_la_lectura_cruda_sigue_siendo_la_envolvente_monotono`,
and the R2/R2b rows of the gate table.

### Requirement RULES-03: R6 recalibrates the band over the corrected point

After R2b, `R6_BANDA` SHALL compute the band from the corrected `rul_punto` using
only the coefficients frozen in `mia/calibracion_banda.json`. It MUST NOT refit,
retrain or recompute quantiles at inference time.

The bin SHALL be selected from `edges` as a left-closed, right-open interval, with
the last bin open to the right. The bounds SHALL be
`lower = min(point + q_low, point)` and `upper = max(point + q_high, point)`. For a
non-negative point, `lower` SHALL be clipped to at least zero. Every result SHALL
satisfy `lower <= point <= upper`; for a non-negative point it SHALL also satisfy
`lower >= 0`. A band that excluded its own point SHALL be treated as a bug.

The scalar and vectorised forms SHALL return the same numbers for the same input,
so the UI path and the single-case path cannot diverge.

#### Scenario: The invariant holds over the whole range

- GIVEN points `-5.0, 0.0, 12.5, 25.0, 49.9, 60.0, 88.0`
- WHEN each band is computed, scalar and vectorised
- THEN `lower <= point <= upper` for every point
- AND `lower >= 0` for every non-negative point
- AND the scalar and vector results match

#### Scenario: The corrected cached windows stay coherent

- GIVEN the 6 196 cached test windows
- WHEN the correction and R6 are applied
- THEN every corrected point lies inside its band
- AND every lower bound is non-negative
- AND the recorded test coverage is 1.0000

**Checks:** `tests/test_mia_rules.py::test_la_banda_recalibrada_contiene_al_punto_y_no_baja_de_cero`,
`tests/test_mia_rules.py::test_la_version_vectorizada_y_la_escalar_coinciden`,
`tests/test_ui_rules.py::test_la_banda_corregida_contiene_al_punto`.

### Requirement RULES-04: The decision pass uses the lower bound, and safety outranks thresholds

Pass A SHALL select the applicable rule with the highest priority and apply its
effect once. The decision SHALL be read from `limite_inferior`, never from
`rul_punto` alone.

- `R1_SEGURIDAD` (priority 10) SHALL fire when `alertas_datos` is non-empty and
  SHALL set the decision to `SIN_DECISION` with a `motivo` naming every alert.
- `R9_HANGAR` (priority 3) SHALL fire on valid data when
  `limite_inferior < umbrales.hangar`.
- `R8_INSPECCION` (priority 2) SHALL fire on valid data when
  `umbrales.hangar <= limite_inferior < umbrales.apto`.
- `R7_APTO` (priority 1) SHALL fire on valid data when
  `limite_inferior >= umbrales.apto`.

The threshold rules MUST be gated on valid data (`not alertas_datos`), so safety
wins both by priority and by condition. An impossible datum SHALL yield no
decision even when its lower bound would have produced a maintenance state. The
default thresholds SHALL be `apto = 30` and `hangar = 25`, configurable through
`caso["umbrales"]`.

#### Scenario: Safety beats a threshold that would otherwise fire

- GIVEN a case whose lower bound lies in the inspection range
- WHEN its alerts are empty
- THEN the decision is `INSPECCION`
- AND when one alert is added the decision becomes `SIN_DECISION`

#### Scenario: Safety does not need a history

- GIVEN an impossible datum with a populated unit history
- WHEN the engine runs
- THEN the decision is `SIN_DECISION`
- AND `R1_SEGURIDAD` is listed among the rules used

#### Scenario: Every decision state is reachable

- GIVEN the measured cases
- WHEN the engine runs
- THEN `APTO`, `INSPECCION`, `HANGAR` and `SIN_DECISION` all occur
- AND no threshold rule fires on invalid data

**Checks:** `tests/test_mia_rules.py::test_la_seguridad_gana_a_los_umbrales`,
`tests/test_mia_rules.py::test_la_seguridad_no_depende_del_historial`,
`tests/test_mia_rules.py::test_hay_casos_para_cada_estado_y_para_sin_decision`.

### Requirement RULES-05: The calibration artifact is frozen and carries its provenance

`mia/calibracion_banda.json` SHALL be consumed as-is. The file SHALL declare:

| Field | Required value |
| --- | --- |
| `method` | `split-conformal, per predicted-RUL bin, asymmetric` |
| `debias` | `false` |
| `target_coverage` | `0.9` |
| `alpha_each_side` | `0.05` |
| `edges` | `[0.0, 25.0, 50.0, 75.0, null]` |
| `n_calibration` | `14 915` |
| `global_quantiles` | `[-19.1707, 17.1004]` |

The artifact SHALL contain exactly four bins:

| Index | Predicted-RUL range | n | q_low | q_high |
| --- | --- | --- | --- | --- |
| 0 | `[0, 25)` | 5 291 | -4.1928 | 7.1817 |
| 1 | `[25, 50)` | 5 283 | -10.7393 | 16.6639 |
| 2 | `[50, 75)` | 3 922 | -21.6779 | 19.7588 |
| 3 | `[75, ∞)` | 419 | -21.2133 | -15.3651 |

The `procedencia` block SHALL contain all seven fields, non-empty:
`metodo`, `filas_calibracion`, `unidades_calibracion`, `excluida`,
`instrumento`, `cache_origen` and `regla_correccion`. It SHALL record 14 915 rows,
the calibration units `[2, 5, 10, 18, 20]`, unit 16 as excluded because the
shipped meta was fitted on it (in-sample), the instrument
`select_beta_grouped(oof, span=5, use_cycle_feature=False)['oof_calib']`, the
source cache `_p1_oof_cache.npz`, and the correction rule as the causal PAVA
extremum.

The recorded OOF coverage of this band over the corrected point is **0.9012**.

#### Scenario: The frozen calibration is the pure one

- GIVEN the committed JSON
- WHEN it is read
- THEN `filas_calibracion` is 14 915 and the unit list is `[2, 5, 10, 18, 20]`
- AND unit 16 is absent from that list
- AND there are four bins and a target coverage of 0.9

#### Scenario: Provenance is complete

- GIVEN the committed JSON
- WHEN its `procedencia` block is inspected
- THEN all seven fields are present and non-empty
- AND it names the source cache and the in-sample exclusion

**Checks:** `tests/test_mia_rules.py::test_la_calibracion_congelada_es_la_pura`,
`tests/test_mia_rules.py::test_la_cobertura_pura_es_la_nominal`, and the
calibration check of `scripts/freeze_rules_evidence.py`.

### Requirement RULES-06: The reproducibility gate fails loudly

The repository SHALL provide `scripts/freeze_rules_evidence.py`. With
`_p1_oof_cache.npz` present, the script SHALL rebuild the OOF instrument through
`select_beta_grouped(..., span=5, use_cycle_feature=False)`, keep units
`[2, 5, 10, 18, 20]`, order each unit by cycle, apply R2b per unit, and print the
monotonicity table. It SHALL verify the committed values at the precision they are
recorded:

| Figure | Required value |
| --- | --- |
| Baseline OOF RMSE / NASA | 9.491 / 19257.1 |
| R2 OOF RMSE / NASA | 10.737 / 21053.0 |
| R2 changed rows | 13 000 |
| R2b OOF RMSE / NASA | 9.623 / 18713.9 |
| R2b changed rows | 10 715 |
| Envelope identity | `min(R2b) == R2` |
| Maximum positive increment | +1.328848 |
| Calibration bins, counts and quantiles | as in RULES-05 |
| OOF coverage | 0.9012 |

When every check passes the script SHALL exit 0. When the cache is absent,
unreadable, or any figure drifts, it SHALL print the expected and observed values
and SHALL exit non-zero. It MUST NOT skip, warn-and-continue, or exit 0 on a
missing input; absence of the cache is a failure, not a reason to pass.

Because `_p1_oof_cache.npz` holds only development/OOF rows, the script SHALL NOT
claim to regenerate the test-panel figures. Those remain recorded evidence anchored
by the frozen manifest and `app/cache`.

#### Scenario: A missing cache fails the gate

- GIVEN a tree without `_p1_oof_cache.npz`
- WHEN the script runs
- THEN the exit code is non-zero
- AND the message names the missing path
- AND no output describes the check as skipped

#### Scenario: Drift fails the gate

- GIVEN a cache whose recomputed R2b RMSE is not 9.623
- WHEN the script runs
- THEN the exit code is non-zero
- AND the output prints the expected and observed values

#### Scenario: A matching tree passes

- GIVEN the committed cache and tree
- WHEN the script runs
- THEN every check passes
- AND the monotonicity table is printed
- AND the exit code is 0

**Checks:** `python scripts/freeze_rules_evidence.py` from the repository root, and
the suite test that invokes it.

### Requirement RULES-07: The layer is post-processing only

The change SHALL NOT retrain, refit or rewrite any model. It MUST leave
`models/` byte-identical, including `ensemble.joblib`, `bilstm_ds02.keras`,
`scaler.joblib` and `ds02_manifest.json`, and MUST NOT alter `src/ds02_rul/` or
`app/cache/`. No frozen metric may change; the manifest reference row SHALL remain
RMSE 4.289, MAE 3.179, R² 0.9473 and NASA 2310.6 over the 6 196 windows.

The only new production executable code SHALL be the gate script. The rules layer
SHALL keep its current behaviour; `mia/reglas.py` may receive documentation
changes only.
The correction toggle SHALL stay off by default, and the raw cached reading SHALL
remain the one that reproduces the frozen manifest.

#### Scenario: The artifacts are untouched

- GIVEN a full correction pass over the cache
- WHEN the four model files are hashed before and after
- THEN every SHA-256 is unchanged
- AND no file under `models/` is created or deleted

#### Scenario: The manifested metrics still hold

- GIVEN the toggle off
- WHEN the live metrics are computed from the cache
- THEN each per-engine RMSE matches the manifest within `5e-3`
- AND no manifest value is edited to match the live figure

#### Scenario: The change adds no model behaviour

- GIVEN the change applied
- WHEN the diff is inspected
- THEN the only new production executable file is `scripts/freeze_rules_evidence.py`
- AND `src/`, `models/` and `app/cache/` are byte-identical
- AND the toggle default is still off

**Checks:** `tests/test_dss_ui.py::test_reading_the_ui_leaves_the_frozen_artifacts_untouched`,
`tests/test_ui_rules.py::test_el_tablero_sigue_entregando_las_mismas_metricas_crudas`,
`tests/test_artifact_contract.py::test_manifest_declares_ds02_shape`.
