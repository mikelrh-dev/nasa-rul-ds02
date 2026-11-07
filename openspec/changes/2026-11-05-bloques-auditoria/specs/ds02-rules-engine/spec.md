# Spec delta: seis reglas de decisión y corrección opcional R6

**Change:** `2026-11-05-bloques-auditoria`
**Capability:** `ds02-rules-engine`
**Status:** Applied
**Sources of truth:** `src/mia/reglas.py`, `src/mia/motor.py`,
`src/mia/calibracion_banda.json`, `models/ds02_manifest.json`,
`app/dashboard_ds02.py`

## MODIFIED

### Engine contract at a glance

The Pass A decision set now has six rules. The two additions are fail-closed
defensive records: they fire only where no previous operational rule could fire.

| Rule id | Pass | Priority | Fires when | Effect |
| --- | --- | --- | --- | --- |
| `R1_SEGURIDAD` | A | 10 | `alertas_datos` is non-empty | `SIN_DECISION` |
| `R10_DATOS_INSUFICIENTES` | A | 9 | valid data, missing `limite_inferior` or thresholds | `SIN_DECISION` with reason |
| `R11_UMBRALES_INCOHERENTES` | A | 8 | valid data, present but unordered thresholds | `SIN_DECISION` with reason |
| `R9_HANGAR` | A | 3 | valid data and `limite_inferior < hangar` | `HANGAR` |
| `R8_INSPECCION` | A | 2 | valid data and `hangar <= limite_inferior < apto` | `INSPECCION` |
| `R7_APTO` | A | 1 | valid data and `limite_inferior >= apto` | `APTO` |

The correction rules `R2b_ISOTONICO_CAUSAL` and `R6_BANDA` still do not count as
decision rules. `R10` and `R11` do not change any decision previously produced by
`R1`, `R9`, `R8` or `R7`.

#### Scenario: incomplete file is explained, not silent

- GIVEN valid data without `limite_inferior` or without usable thresholds
- WHEN the motor runs
- THEN the decision is `SIN_DECISION`
- AND `R10_DATOS_INSUFICIENTES` appears in `usadas`
- AND the recorded `motivo` names the missing field class

#### Scenario: inverted thresholds do not produce an arbitrary state

- GIVEN valid data and thresholds with `hangar >= apto`
- WHEN the motor runs
- THEN the decision is `SIN_DECISION`
- AND `R11_UMBRALES_INCOHERENTES` appears in `usadas`

### R6 remains optional

`R6_BANDA` still applies only when the rules correction is explicitly enabled
(`aplicar_reglas`). With the toggle off, decisions use the artifact band through
the cached `lower` values. The operational dashboard states which band is active.

#### Scenario: default band is unchanged

- GIVEN the toggle off
- WHEN the dashboard and batch paths decide
- THEN they use the cached artifact `lower` values
- AND enabling the correction switches to R2b/R6 with the 14 915-row band

## Related capabilities

Cites, without modifying, `rul-prediction-ds02` (artifact band) and `ds02-dss-ui`
(band label and correction toggle).
