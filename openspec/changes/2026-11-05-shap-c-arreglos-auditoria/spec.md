# Delta — 2026-11-05-shap-c-arreglos-auditoria

**Change:** `2026-11-05-shap-c-arreglos-auditoria` · `rul-prediction-ds02` (modified), `shap-c-explanation` (new). Sin REMOVED/RENAMED.

## ADDED Requirements

### Requirement: SHAPC-BILSTM-01
The system MUST DeepSHAP the bundle-C BiLSTM on `(50,19)` with bundle preprocessing; EMA out, no causal claim.
#### Scenario: Aditividad
- GIVEN one `(50,19)` window
- WHEN DeepSHAP runs
- THEN `base+sum(shap)` matches within `1e-5`

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

### Requirement: DOC-C-01
The system MUST record manifest `4.338` current, ADR-011 `R6=C`, multiseed historical.
#### Scenario: Vigente
- GIVEN docs read
- WHEN checked
- THEN `4.338`, `R6=C`, historical noted

### Requirement: CACHE-DRIFT-01
The system MUST check `manifest_sha256`, freeze `_p1_oof_cache`, version drift evidence.
#### Scenario: Drift
- GIVEN stale `manifest_sha256`
- WHEN cache validates
- THEN loud failure, no reuse

### Requirement: SEC-API-01
The system MUST use `compare_digest`, open `/health`, rate-limit writes, bind `127.0.0.1`.
#### Scenario: Health
- GIVEN API on `127.0.0.1`
- WHEN `/health` probed
- THEN succeeds unauthenticated

### Requirement: SEC-DOCK-ST-01
The system MUST bind Docker/Streamlit only to `127.0.0.1`.
#### Scenario: Bind
- GIVEN services start
- WHEN config inspected
- THEN no `0.0.0.0` exists

### Requirement: DEP-CI-01
The system MUST pin `pyproject.toml` deps and run CI `python -m pytest tests -q`.
#### Scenario: CI
- GIVEN clean checkout
- WHEN CI runs
- THEN pinned install, pytest executes

### Requirement: SEC-JOBLIB-01
The system MUST guard `joblib.load` in `clase/`, `scripts/` against unverified payloads.
#### Scenario: Bloqueo
- GIVEN no valid checksum
- WHEN load attempted
- THEN refused pre-deserialization

## MODIFIED Requirements

### Requirement: Artifact persistence and reload
The capability SHALL persist canonical artifacts under `models/` only (`ensemble.joblib`, `scaler.joblib`, `bilstm_ds02.keras`, `ds02_manifest.json` with `manifest_sha256`); root copies are gitignored leftovers, never contract. Reload single-sample check: RUL **61.25** vs true **58.00**.
(Previously: written twice, root and models/, without canonical models/ + manifest_sha256.)

#### Scenario: Canónicos
- GIVEN completed run
- WHEN persistence ends
- THEN four `models/` artifacts exist

#### Scenario: Reload
- GIVEN artifacts written
- WHEN one window rescored
- THEN RUL `61.25`, paradigm recovered

#### Scenario: Firma
- GIVEN reloaded ensemble
- WHEN queried
- THEN `predict(X,cycles,units)`, clipped zero

### Requirement: Recorded SOTA results
The capability SHALL record units `[11,14,15]` metrics exactly; the hybrid MUST beat the BiLSTM on RMSE and NASA. Below is the historical reference; current contract is bundle C `4.338` (`R6=C`), multiseed historical. NASA is SUM, no `125` clamp.

| Model | RMSE | MAE | R² | NASA |
| --- | --- | --- | --- | --- |
| LightGBM | 7.087 | 5.584 | 0.8562 | 5768.4 |
| BiLSTM | 5.693 | 4.449 | 0.9072 | 3822.2 |
| BiLSTM+EMA | 5.597 | 4.331 | 0.9103 | 3716.8 |
| **Hybrid** | **5.522** | 4.795 | **0.9127** | **3435.1** |

(Previously: single-seed table as current, without bundle-C 4.338 / historical status.)

#### Scenario: Hybrid gana
- GIVEN recorded rows
- WHEN hybrid vs BiLSTM
- THEN `5.522`<`5.597`, `3435.1`<`3716.8`

#### Scenario: Caveat
- GIVEN any result published
- WHEN disclosed
- THEN seeds 42 (`5.447`), 7 (`6.564`) shown
