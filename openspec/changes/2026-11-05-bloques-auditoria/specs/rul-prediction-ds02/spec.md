# Spec delta: el manifiesto distingue la banda del artefacto, la banda R6 y la historia

**Change:** `2026-11-05-bloques-auditoria`
**Capability:** `rul-prediction-ds02`
**Status:** Applied
**Sources of truth:** `models/ds02_manifest.json`,
`src/mia/calibracion_banda.json`, `src/ds02_rul/conformal.py`,
`archive/models_b/ds02_manifest.json`

## MODIFIED

### Requirement: Calibration provenance is recorded

A shipped C manifest SHALL record two different bands with different roles:

1. `conformal`: the artifact's internal calibration, 17 450 rows, including
   holdout unit 16. This is the band used by `ensemble.predict_interval`,
   cached app windows, new-case scoring and live batches.
2. `conformal_decision`: the optional R6 correction band, 14 915 pure OOF rows
   over units `[2, 5, 10, 18, 20]`, read from `src/mia/calibracion_banda.json`
   and used only when `aplicar_reglas` is enabled.

The two blocks SHALL NOT be merged or relabeled as interchangeable.

#### Scenario: correction band is tied to its JSON

- GIVEN the shipped manifest
- WHEN `conformal_decision.n_calibration` is compared with
  `src/mia/calibracion_banda.json`
- THEN both values are 14 915
- AND the bin counts sum to the JSON calibration size
- AND unit 16 is absent from the correction band

#### Scenario: artifact band is not rewritten to match

- GIVEN the shipped manifest
- WHEN `conformal.n_calibration` is read
- THEN it remains 17 450
- AND the manifest explicitly documents that unit 16 trained the meta-learner

### Requirement: Historical comparison stays auditable

The C manifest SHALL retain bundle B as its non-current historical reference,
including source, reference metrics, multiseed summary and bundle-B SHA. This
does not make B a candidate and does not change the deployed champion.

- Model: Hybrid stacking + EMA causal 5, bundle B, clean HDF5
- Reference row: RMSE 4.251, NASA 2,305.1, 6,196 windows
- Multiseed: mean 4.340, std 0.101; seeds `[42, 7, 123]`
- Source: `archive/models_b/ds02_manifest.json`

#### Scenario: historical values are traceable

- GIVEN the shipped manifest
- WHEN `historical_reference` is inspected
- THEN it names bundle B and its archive manifest
- AND the deployed `reference_row` remains bundle C, RMSE 4.338
