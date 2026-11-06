# Delta for rul-prediction-ds02

**Change:** `2026-11-06-app-fixes-1`
**Capability:** `rul-prediction-ds02` (bundle C; seed 42 RMSE 4.338, manifest rules)

## ADDED Requirements

### Requirement: Multiseed evidence reconciliation

The system MUST reconcile multiseed citations without retraining: seed 42 SHALL come from `models/ds02_manifest.json` (RMSE 4.338 / MAE 3.227 / R2 0.9461 / NASA 2336.2) and seeds 7/123 from `resultados/bundle_c_multiseed.csv` (4.429 / 4.336). Regenerating with `--desde-csv` SHALL yield three rows with mean RMSE 4.368±0.053 and NASA 2355.2±24.6. Citations in README, AGENT, README.en, ADR-011 and LEARNING_LOG MUST read 4.368±0.053 (NB06 window test); NB05 OOF 4.330±0.053 stays labelled OOF. NASA is a SUM, no 125-cycle clamp on DS02.

#### Scenario: Three-row table matches manifest

- GIVEN the regenerated CSV
- WHEN row 42 is compared with the manifest
- THEN RMSE equals 4.338 within 1e-9
- AND `len(table) == 3` with seeds `[42, 7, 123]`

#### Scenario: Citations agree

- GIVEN docs and the CSV
- WHEN the multiseed mean is read
- THEN README/AGENT/README.en/ADR-011/LEARNING_LOG cite 4.368±0.053
- AND no notebook output is edited
