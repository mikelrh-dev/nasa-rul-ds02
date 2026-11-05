# SHAP-C Explanation — Deployed Specification

**Capability:** `shap-c-explanation`
**Status:** Active
**Change:** `2026-11-05-shap-c-arreglos-auditoria`
**Date:** 2026-11-05

Per-branch SHAP explanations over bundle C (manifest `4.338`, read-only): the
BiLSTM on `(50,19)` windows via grouped Permutation SHAP (19 channel players,
exact by telescoping), the LightGBM (93 features) via TreeSHAP, and the meta
blend over `Z=[p_lstm,p_lgb]` via Permutation SHAP. The causal EMA is out of
scope and no causal claim is made. Ancillary audit fixes from the same change
(DOC-C-01, CACHE-DRIFT-01, SEC-API-01, SEC-DOCK-ST-01, DEP-CI-01, SEC-JOBLIB-01)
are recorded in the `rul-prediction-ds02` deployed spec.

---

## Requirements

### Requirement: SHAPC-BILSTM-01
The system MUST explain the bundle-C BiLSTM on `(50,19)` with grouped Permutation SHAP (19 channel players, exact by telescoping; DeepExplainer infeasible with Keras3 While-LSTM + shap 0.54.1, error 3.06 >> 1e-2) with bundle preprocessing; EMA out, no causal claim.
#### Scenario: Aditividad
- GIVEN one `(50,19)` window
- WHEN grouped Permutation SHAP runs
- THEN `base+sum(shap)` matches within `1e-2` (grouped permutation is exact by telescoping, observed 9.5e-07; error declared in metadata; TreeSHAP/Permutation branches keep `1e-5`)

### Requirement: SHAPC-LGBM-01
The system MUST TreeSHAP the bundle-C LightGBM (93 features) with branch additivity.
#### Scenario: Aditividad
- GIVEN one `(93,)` row
- WHEN TreeSHAP runs
- THEN `base+sum(shap)` matches within `1e-5`

### Requirement: SHAPC-META-01
The system MUST explain the meta blend over `Z=[p_lstm,p_lgb]`, no `cyc_norm`.
#### Scenario: Aditividad
- GIVEN one `Z` row
- WHEN meta-SHAP runs
- THEN values sum within `1e-5`

### Requirement: SHAPC-DATA-01
The system MUST use bundle C (manifest `4.338`) read-only, no retrain or `models/` write.
#### Scenario: NASA suma sin clamp
- GIVEN targets `>125`
- WHEN NASA computed
- THEN SUM of exponentials, no clamp

### Requirement: SHAPC-NB-01
The system MUST build the notebook only via `scripts/build_*.py`, never touching NB01-06.
#### Scenario: Sin causal
- GIVEN notebook runs
- WHEN it completes
- THEN shapes pass, no causal text
