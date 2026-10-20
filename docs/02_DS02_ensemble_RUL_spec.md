# N-CMAPSS DS02 — Hybrid Stacking Ensemble for RUL Prediction

| | |
|---|---|
| **Status** | Implemented, verified on test units; **not deployable outside the notebook process** (see §6) |
| **Date** | 2026-10-19 |
| **Source of truth** | `02_DS02_ensemble_RUL.ipynb` (17 cells, generated — not hand-written — by `scripts/build_02_notebook.py`) |
| **Dataset** | N-CMAPSS **DS02** (`archive/CCMaps/N-CMAPSS_DS02-006.h5`, 2.34 GB) |
| **Target** | Remaining Useful Life (RUL) per engine, in cycles |
| **Evaluation** | Test units **11, 14, 15** (3 engines), scored with RMSE / MAE / R² / NASA score |
| **Related** | `openspec/specs/rul-prediction-ds02/spec.md` · `openspec/changes/2026-10-19-ds02-production-hardening/` · `docs/decisions/` |

---

## 1. Executive summary

The pipeline predicts RUL for N-CMAPSS DS02 turbofan engines by **stacking two deliberately different base models** over the same 50-cycle window, then smoothing the result with a causal per-unit filter.

The two base models see the same data through different lenses:

- a **BiLSTM** (2 × bidirectional LSTM of 64 units, triple temporal pooling → 384 dims) that reads the *ordered trajectory* of 19 channels and is trained with a robust `Huber(delta=10.0)` loss;
- a **LightGBM** quantile regressor (`alpha=0.35`) that reads a *flat 93-dimensional summary* of the same window and is trained with an **asymmetric** objective chosen to match the NASA score.

Their errors are different enough that a learned meta-learner can exploit the difference, and a causal exponential moving average imposes the monotonicity that physical wear implies. The hybrid is **strictly better than both base models** on both headline metrics.

| Model | RMSE | MAE | R² | NASA score |
|---|---|---|---|---|
| LightGBM standalone (quantile 0.35, 93 feat) | 7.087 | 5.584 | 0.8562 | 5768.4 |
| BiLSTM 2-layer (triple pooling) | 5.693 | 4.449 | 0.9072 | 3822.2 |
| BiLSTM 2-layer + causal EMA (span 5) | 5.597 | 4.331 | 0.9103 | 3716.8 |
| **Hybrid stacking (beta = 1.00, EMA 5)** | **5.522** | 4.795 | **0.9127** | **3435.1** |

The architectural core of the solution is a **physical separation of degradation from flight regime**: the 14 sensors are residualised against a degree-2 Ridge model of the 4 operational-condition channels before either model sees them, so that LightGBM reads degradation rather than pilot manoeuvre. That single change moved the standalone tabular branch from RMSE 13.349 to 7.087.

**What is not production-ready.** The shipped `ensemble.joblib` **cannot be loaded outside the notebook that produced it** — verified, it raises `AttributeError: Can't get attribute 'HybridStackingEnsemble' on <module '__main__'>`. The `beta` shrinkage is also selected in-sample. Both are specified as remediation work in `openspec/changes/2026-10-19-ds02-production-hardening/`.

---

## 2. Architecture

### 2.1 Data flow

```mermaid
flowchart TD
    accTitle: DS02 hybrid stacking RUL pipeline
    accDescr: Data flow from the N-CMAPSS DS02 HDF5 file through ingestion, unit partitioning, physical residualization of the sensors on the flight regime, the two base models, the stacking meta-learner, beta shrinkage and causal EMA smoothing to the final RUL estimate.

    h5["N-CMAPSS_DS02-006.h5<br/>A, W, X_s, Y"] --> ingest["Ingestion<br/>STRIDE 100 downsampling"]
    ingest --> units["Unit partition<br/>fit 2, 5, 10, 18, 20 - holdout 16 - test 11, 14, 15"]
    units --> concat["X_train_full<br/>18 channels = W(4) + Xs(14)"]

    concat --> gscaler["Global StandardScaler<br/>18 channels"]
    concat --> wscaler["W StandardScaler"]
    wscaler --> poly2["PolynomialFeatures degree 2<br/>4 channels to 14 terms"]
    poly2 --> ridge["14 x Ridge alpha 1.0<br/>fit on all six dev units"]
    concat --> ridge
    ridge --> resid["Residual sensors<br/>Xs minus Ridge of Poly2 of W"]
    resid --> rscaler["Residual StandardScaler"]

    rscaler --> tabfeat["Tabular features 93<br/>cyc_norm 1 - W 8 - Xs 84"]
    rscaler --> seqfeat["Sequence 19 channels<br/>18 scaled plus cyc_norm<br/>window 50"]

    tabfeat --> lgb["LightGBM quantile 0.35<br/>depth 4, leaves 15, 300 trees"]
    seqfeat --> bilstm["BiLSTM 2 x 64 bidirectional<br/>Huber delta 10, 384-dim pooled head"]

    meta["Meta-learner on unit 16<br/>RidgeCV plus shallow LGBM<br/>inputs pred_lstm, pred_lgb, cyc_norm"]
    beta["Beta shrinkage<br/>p_lstm plus beta times p_meta minus p_lstm<br/>beta = 1.00"]
    ema["Causal EMA span 5<br/>per unit, ordered by cycle"]
    clip["Clip at 0"]
    rul["RUL per window"]

    lgb --> meta
    bilstm --> meta
    meta --> beta
    bilstm --> beta
    beta --> ema
    ema --> clip
    clip --> rul

    classDef source fill:#dbeafe,stroke:#2563eb,stroke-width:2px,color:#1e3a5f
    classDef prep fill:#fef9c3,stroke:#ca8a04,stroke-width:2px,color:#713f12
    classDef model fill:#dcfce7,stroke:#16a34a,stroke-width:2px,color:#14532d
    classDef out fill:#f3e8ff,stroke:#7e22ce,stroke-width:2px,color:#3b0764

    class h5,ingest,units source
    class concat,gscaler,wscaler,poly2,ridge,resid,rscaler,tabfeat,seqfeat,meta,beta,ema prep
    class lgb,bilstm model
    class clip,rul out
```

### 2.2 Evolution across four iterations

_The timeline below records the four experimental iterations of the DS02 pipeline and the test-set RMSE of each participating model. It is a chronology, not a flowchart: each row is a complete re-design of the feature and model stage._

```mermaid
timeline
    title DS02 RUL pipeline evolution across four iterations
    Iteration 1 - Baseline : Sensors only, 4 basic statistics : Fixed blend 0.6 LGBM plus 0.4 BiLSTM : LGBM 10.82, BiLSTM 6.939, blend 8.091
    Iteration 2 - Regime integration : W plus Xs, 126 features : Inverse-variance blend : LGBM 10.917, BiLSTM 6.874, blend 7.180
    Iteration 3 - Noise pruning : 78 features, depth-4 LightGBM : Residual corrector attempt : LGBM 13.349, BiLSTM 5.701, hybrid 5.701
    Iteration 4 - Current SOTA : Ridge residualization, 93 features : 19-channel BiLSTM, stacking, causal EMA : LGBM 7.087, BiLSTM 5.693, hybrid 5.522
```

### 2.3 Layer responsibilities

| Layer | Object | Responsibility |
|---|---|---|
| Ingestion | `load_rul_dataset()` | Locate the DS02 HDF5 (with an FD001 text fallback), read `A/W/X_s/Y` for dev and test, decode the 4 + 14 channel names |
| Unit partition | `val_mask` / `train_fit_mask` | Reserve unit 16; fit on units 2, 5, 10, 18, 20 |
| Preprocessing | `scaler`, `scaler_w`, `poly_w`, `sensor_ridges`, `res_scaler` | Standardise, and physically separate degradation from flight regime |
| Windowing | `create_dataset_windows_residual()` | Build 50-cycle windows plus the 93-dimensional tabular summary |
| Base model A | `lgb_standalone` | Quantile gradient boosting over the tabular summary |
| Base model B | `bilstm_model` | Bidirectional recurrent model over the ordered 19-channel sequence |
| Stacking | `ridge_meta`, `lgb_meta`, `opt_beta` | Learn how to combine the two predictions, with a shrinkage bound |
| Smoothing | `causal_ema_by_unit()` | Impose monotone wear causally, per unit |
| Packaging | `HybridStackingEnsemble` | Reassemble the whole path for inference; persisted with `joblib` |

---

## 3. Pipeline specification

### 3.1 Ingestion

| Aspect | Value |
|---|---|
| Primary source | `archive/CCMaps/N-CMAPSS_DS02-006.h5` (candidate paths are probed in order) |
| Fallback source | C-MAPSS **FD001** text files (`train_FD001.txt` / `test_FD001.txt` / `RUL_FD001.txt`) |
| HDF5 keys | `A_dev, W_dev, X_s_dev, Y_dev` and `A_test, W_test, X_s_test, Y_test` |
| `W` channels (4) | `alt`, `Mach`, `TRA`, `T2` — operating conditions |
| `Xs` channels (14) | `T24, T30, T48, T50, P15, P2, P21, P24, Ps30, P40, P50, Nf, Nc, Wf` — physical sensors |
| Trajectory columns | `A_var = ['unit', 'cycle', 'Fc', 'hs']` — the pipeline reads **only** `unit` (column 0) and `cycle` (column 1) |
| Down-sampling | `STRIDE = 100` on every array (`A_train[::100]`, `W_train[::100]`, …) |
| Combined signal | `X_train_full = np.hstack([W_train_raw, Xs_train_raw])` → 18 channels |
| Clipping to 125 | **DS02 path: none.** The `clip(upper=125)` exists only in the FD001 fallback |
| Dev population | 6 units — 2, 5, 10, 16, 18, 20 — 52 635 sampled rows |
| Test population | 3 units — 11, 14, 15 |
| `Y_dev` (RUL) range | 0 … 88 over the sampled dev set |

The 100x down-sampling is a compute-budget decision, not a modelling one: it is what makes a 2.34 GB dataset trainable on CPU in minutes. It also has a consequence that the code's naming hides.

**The "50-cycle window" is not 50 flight cycles.** The raw trajectory holds roughly 11 400 rows per flight cycle, and `STRIDE = 100` keeps one row in every hundred, so the sampled series advances about **114 samples per flight cycle** (unit 2: 8 532 samples spread over 75 cycles; unit 5: 10 334 over 89; unit 20: 7 682 over 66). A window of `WINDOW_SIZE = 50` therefore spans about **0.44 flight cycles** of engine life — roughly 5 000 raw trajectory steps, not 5 000 cycles. `WINDOW_SIZE = 50` and the phrase *"50 ciclos"* in the code comments both overstate the temporal reach of the model by more than two orders of magnitude. `cyc_norm = cycle / 100.0` is the single feature that carries the true flight-cycle count, which is exactly why reinstating it in iteration 4 mattered (ADR-002, iteration 3 lesson 4).

`A_dev` also carries `Fc` (flight condition; constant `3` — cruise — across the sampled dev set) and `hs` (health status, 0/1). **Neither is read by the pipeline** — the notebook only ever takes `A[:, 0]` and `A[:, 1]` — so no label-derived channel can enter the features. This is worth stating because `hs` is exactly the kind of column that would silently leak the answer.

#### 3.1.1 Provenance of the shipped artefact

The notebook's recorded output states the source directly:

```
[DATASET FOUND] Ingestando N-CMAPSS DS02-006 desde: archive/CMaps/N-CMAPSS_DS02-006.h5
```

That is confirmed independently by the persisted `ensemble.joblib`, whose fitted objects carry the fingerprint of the dataset they were built on:

| Read from the artefact | Value | What it proves |
|---|---|---|
| `scaler.n_features_in_` | **18** | 4 `W` + 14 `Xs`. The FD001 fallback path would produce 16 (2 settings + 14 sensors) |
| `ensemble.n_op` | **4** | The FD001 fallback uses only 2 operational columns (`setting1`, `setting2`) |
| `scaler.mean_[:4]` | `[21901.0168, 0.6238, 68.5486, 475.0096]` | Altitude ≈ 21 901 ft, Mach ≈ 0.624, throttle ≈ 68.5 %, T2 ≈ 475.0 °R — unambiguously DS02's physical units; FD001's settings are categorical 0/1 |
| `poly_w.n_features_in_ → n_output_features_` | 4 → 14 | Degree-2 basis over the 4 condition channels |
| `sensor_ridges` | 14 × `Ridge(alpha=1.0)`, 14 features each | One independent residual model per sensor |
| `lgb_standalone.n_features_in_` | **93** | The tabular feature contract |
| `lgb_standalone.objective / alpha` | `quantile` / `0.35` | The asymmetric objective (ADR-003) |
| `ridge_meta.n_features_in_` / `lgb_meta.n_features_in_` | 3 / 3 | `[pred_lstm, pred_lgb, cyc_norm]` |
| `bilstm_model.input_shape` / params | `(None, 50, 19)` / **154 253** | The recurrent contract (ADR-004) |
| `bilstm_model.layers` | `Input → BatchNorm → BiLSTM → Dropout → BiLSTM → Dropout → Lambda → GAP → GMP → Concat → Dropout → Dense → Dense` | The triple-pooling head, including the `Lambda` of §6.2 |
| `window_size` / `beta` / `ema_span` | 50 / 1.0 / 5 | The recorded configuration |

**Provenance hazard.** The FD001 fallback is silent. If the DS02 HDF5 is ever moved or renamed, `load_rul_dataset()` falls back to the C-MAPSS text files and the notebook trains and saves an **FD001** model to the **same** `ensemble.joblib` path, with the **same** `paradigm` metadata string
(`"Hybrid Stacking (BiLSTM dual-pooling + LGBM residualizado + RidgeCV/LGBM meta + EMA5)"`).
The two artefacts are distinguishable only by inspecting `n_features_in_` (18 vs 16) and `n_op` (4 vs 2) — nothing in the file name, the metadata or the console output says so. This is the concrete reason the provenance manifest of OpenSpec task 2.5 is a requirement and not a nicety.

### 3.2 Unit partition

| Partition | Units | Rows |
|---|---|---|
| Fit (base models + meta-learner) | 2, 5, 10, 18, 20 | — |
| Holdout (validation, meta-learner fit, beta grid) | **16** | 2 535 windows |
| Test (read once) | 11, 14, 15 | 6 196 windows |

```python
unique_train_units = np.unique(meta_train['unit'])
VAL_UNIT = 16.0 if 16.0 in unique_train_units else unique_train_units[-1]
val_mask = (meta_train['unit'] == VAL_UNIT).values
train_fit_mask = ~val_mask
```

### 3.3 Preprocessing and physical residualization

```python
scaler    = StandardScaler().fit(X_train_full)          # 18 channels
scaler_w  = StandardScaler().fit(W_train_raw)            # 4 channels
poly_w    = PolynomialFeatures(degree=2, include_bias=False).fit(W_train_scaled)   # 4 -> 14 terms

for j in range(14):
    r = Ridge(alpha=1.0).fit(P_train, Xs_train_raw[:, j])
    res_train[:, j] = Xs_train_raw[:, j] - r.predict(P_train)     # Xs - Ridge(Poly2(W))

res_scaler = StandardScaler().fit(res_train)
```

| Property | Value |
|---|---|
| Residual models | 14 independent `Ridge(alpha=1.0)` |
| Polynomial basis | degree 2, no bias → 14 terms from 4 channels |
| Fit population | **all six dev units**, before the unit-16 split (unsupervised — no RUL label is read) |
| Residual definition | `Xs_raw - Ridge(Poly2(W_standardised))`, then standardised |

### 3.4 Tabular feature contract — 93 features

| Group | Count | Definition |
|---|---|---|
| `cyc_norm` | 1 | `cycle / 100.0` — accumulated cycle, the wear proxy the pruned iteration 3 lost |
| `op_feat` | 8 | `op.mean(axis=0)` ⊕ `op[-1]` over the 4 residualised-then-scaled W channels |
| `xs_feat` | 84 | 6 descriptors × 14 residual sensors: `mean`, `last`, `std`, `xs[-10:].mean`, `last - first`, `xs[-5:].mean - xs[:5].mean` |
| **Total** | **93** | `X_train_tab (17450, 93)`, `X_test_tab (6196, 93)` |

The last two descriptors are the short-horizon slopes: they carry the direction and rate of change of the degradation over the window, which is what distinguishes a healthy engine from a degrading one with the same current level.

### 3.5 LightGBM branch

```python
LGBMRegressor(objective='quantile', alpha=0.35, n_estimators=300, learning_rate=0.02,
              num_leaves=15, max_depth=4, min_child_samples=50,
              reg_alpha=1.0, reg_lambda=5.0, colsample_bytree=0.8, subsample=0.8,
              random_state=42, verbose=-1)
```

Trained on `X_train_tab[train_fit_mask]`. Fit time 0.48 s.

### 3.6 BiLSTM branch

| Aspect | Value |
|---|---|
| Input shape | `(50, 19)` — 18 globally-scaled channels + `cyc_norm` appended per timestep |
| Input normalisation | `BatchNormalization` on the input tensor |
| Recurrent stack | `Bidirectional(LSTM(64, return_sequences=True))` × 2, `Dropout(0.2)` after each |
| Temporal pooling | `Concatenate([Lambda(z[:, -1, :]), GlobalAveragePooling1D(), GlobalMaxPooling1D()])` → 128 + 128 + 128 = **384** |
| Head | `Dropout(0.2)` → `Dense(32, relu)` → `Dense(1)` |
| Parameters | 154 253 total / 154 215 trainable / 38 non-trainable |
| Loss | `Huber(delta=10.0)` — robust to the occasional extreme sensor excursion |
| Optimiser | `Adam(learning_rate=0.001)` |
| Schedule | `batch_size=128`, `epochs=22`, `EarlyStopping(monitor='val_loss', patience=5, restore_best_weights=True)`, `ReduceLROnPlateau(factor=0.5, patience=2)` |
| Validation | `validation_data = (X_train_seq[val_mask], y_train[val_mask])` — unit 16 |
| Seed | `SEED = 42` (`np.random.seed` + `tf.random.set_seed`) |
| Recorded run | early stop at epoch 11, best epoch 6, 147.99 s |

The three pooling branches are complementary: `last_step` carries the current state, `GlobalAveragePooling1D` carries the trajectory level, and `GlobalMaxPooling1D` carries the extreme transient thermal events.

### 3.7 Stacking and beta shrinkage

```python
Z_val = np.column_stack([pred_lstm_val, pred_lgb_val, cyc_val])      # cyc_val = cycle / 100
ridge_meta = RidgeCV(alphas=np.logspace(-2, 3, 20)).fit(Z_val, y_val)
lgb_meta   = LGBMRegressor(max_depth=3, num_leaves=7, n_estimators=120,
                           learning_rate=0.03, min_child_samples=20,
                           random_state=42).fit(Z_val, y_val)
p_meta_val = 0.5 * ridge_meta.predict(Z_val) + 0.5 * lgb_meta.predict(Z_val)
```

`beta` is selected over `np.linspace(0, 1, 21)` with the combined criterion
`rmse_val / rmse_lstm_val + nasa_val / nasa_lstm_val`, applied to the EMA-smoothed candidate
`pred_lstm_val + beta * (p_meta_val - pred_lstm_val)`.

| `beta` | val RMSE | val NASA | criterion |
|---|---|---|---|
| 0.00 (BiLSTM only) | 4.091 | 1062.6 | 1.937 |
| 0.05 | 3.883 | 992.8 | 1.825 |
| 0.10 | 3.675 | 925.1 | 1.713 |
| **1.00 (selected)** | **0.308** | **55.9** | — |

The BiLSTM's own validation figures are RMSE 4.221 / NASA 1097.5. The `beta = 1.00` row is **not** a 13x modelling gain — it is the meta-learner scoring its own training rows. See §6.3.

### 3.8 Causal EMA smoothing

```python
def causal_ema_by_unit(pred, units, cycles, span=5):
    out = np.zeros_like(np.asarray(pred, dtype=np.float64))
    for u in np.unique(units):
        idx = np.where(units == u)[0]
        idx = idx[np.argsort(cycles[idx])]
        out[idx] = pd.Series(pred[idx]).ewm(span=span, adjust=False).mean().values
    return out
```

`adjust=False` makes it a causal recursion; the per-unit grouping plus the cycle sort make it correct for a live stream. The final prediction is `np.clip(p, 0.0, None)`.

### 3.9 Metrics

```python
def calculate_nasa_score(y_true, y_pred):
    d = np.asarray(y_pred).ravel() - np.asarray(y_true).ravel()
    score = np.where(d < 0, np.exp(-d / 13.0) - 1.0, np.exp(d / 10.0) - 1.0)
    return float(np.sum(score))
```

| Property | Value |
|---|---|
| NASA score | **Sum**, not mean — it scales with the number of evaluated engines and is not comparable across different evaluation sets |
| Asymmetry | Over-estimates are penalised at `1/10` per cycle, under-estimates at `1/13` |
| Tail behaviour | Exponential, so a single large over-estimate dominates the score of the whole set |
| Clamp to 125 | **None on the DS02 path** (only the FD001 fallback clamps RUL at ingestion) |
| RMSE / MAE / R² | `sqrt(mean_squared_error)`, `mean_absolute_error`, `r2_score` |

### 3.10 Persistence

| Artefact | Contents | Location |
|---|---|---|
| `scaler.joblib` | `StandardScaler` fit on the 18-dimensional `X_train_full` | repo root and `models/` |
| `ensemble.joblib` | `HybridStackingEnsemble`: `bilstm_model` (Keras), `lgb_standalone`, `ridge_meta`, `lgb_meta`, `residualizer` (`poly_w` + 14 Ridge models + `res_scaler`), `scaler`, `scaler_w`, `n_op=4`, `window_size=50`, `beta=1.0`, `ema_span=5` | repo root and `models/` |

The notebook reloads both artefacts and runs a one-sample inference check: **estimated RUL 61.25 cycles against a real 58.00**.

The Keras model is pickled **inside** `ensemble.joblib`; there is no separate `.keras` or `.h5` file for the DS02 network.

---

## 4. Architecture Decision Records

Full records live in `docs/decisions/`. Each is written against the ADR template: status, date, context, decision, alternatives considered, consequences.

| ADR | Title | Status | Decision in one line |
|---|---|---|---|
| [ADR-001](decisions/ADR-001-reject-linear-blending-adopt-learned-stacking.md) | Reject linear blending in favour of a learned stacking meta-learner | Accepted | A convex blend cannot beat its best component while the branch errors are positively correlated; replace it with `RidgeCV` + shallow-GBDT stacking under a bounded `beta` shrinkage |
| [ADR-002](decisions/ADR-002-residualize-sensors-on-operational-conditions.md) | Residualise the sensors on the flight regime with a degree-2 Ridge | Accepted | Subtract `Ridge(Poly2(W))` from each sensor so the models read degradation, not manoeuvre |
| [ADR-003](decisions/ADR-003-asymmetric-quantile-objective-for-nasa-score.md) | Asymmetric quantile objective (alpha = 0.35) | Accepted | The NASA penalty is exponential and asymmetric; train the tabular branch on the 35th conditional quantile to bias over-estimates away |
| [ADR-004](decisions/ADR-004-gradient-boosting-and-ridge-over-classical-models.md) | Gradient boosting and ridge over classical models | Accepted | LightGBM and RidgeCV are retained; Random Forest, k-NN and AdaBoost are rejected on inductive-bias and measured grounds |
| [ADR-005](decisions/ADR-005-reserve-unit-16-as-stacking-holdout.md) | Reserve unit 16 as the stacking holdout | Accepted | A learned meta-learner needs out-of-sample rows; unit 16 is the most representative of the available units |
| [ADR-006](decisions/ADR-006-causal-ema-smoothing-of-final-prediction.md) | Causal per-unit EMA on the final prediction | Accepted | Wear is monotone in cycle; smooth the output causally so the exponential NASA penalty is not paid on discontinuity noise |

**Two decisions carry the most weight.** ADR-002 is what turned the tabular branch from a liability into a contributor (13.349 → 7.087 RMSE), because it is the only one that changed what the data *means* rather than how it is fitted. ADR-001 is what turned the ensemble from a liability into the final system, because it recognises that averaging is not combining.

---

## 5. Evolution across the four iterations

| | Iteration 1 — Baseline | Iteration 2 — Regime integration | Iteration 3 — Noise pruning | Iteration 4 — Current SOTA |
|---|---|---|---|---|
| **Regime `W`** | ignored | concatenated, 18 channels | pruned to `mean` + `last` | residualised out via `Ridge(Poly2(W))` |
| **Tabular features** | 4 statistics of `Xs` | 126 features (7 statistics × 18 channels) | 78 features (`W` mean/last + 5 descriptors of `Xs`) | **93 features** (1 `cyc_norm` + 8 `W` + 84 residualised `Xs`) |
| **LightGBM** | baseline | overfit on manoeuvre noise | `max_depth=4, num_leaves=15` | `quantile 0.35`, depth 4, leaves 15, 300 trees, `min_child_samples=50` |
| **BiLSTM** | stalled in the first 5 epochs | `BatchNorm` + `Huber(delta=10.0)` | — | 19 channels, 2×64 bidirectional, triple pooling, `Huber(delta=10.0)` |
| **Combination** | fixed `0.6 / 0.4` | inverse-variance `0.23 / 0.77` | champion-challenger, residual corrector attempted | learned meta-learner + `beta` shrinkage + causal EMA |
| **LightGBM RMSE** | 10.82 | 10.917 | 13.349 | **7.087** |
| **BiLSTM RMSE** | 6.939 | 6.874 | 5.701 | **5.693** |
| **Ensemble RMSE** | 8.091 | 7.180 | 5.701 | **5.522** |
| **NASA score** | blend 6747 | blend 5542.1 | hybrid 3522.6 | **hybrid 3435.1** |
| **Verdict** | ensemble destroys the BiLSTM | ensemble still destroys the BiLSTM | tabular branch still loses | **hybrid beats both** |

### What each iteration taught

1. **Averaging is not combining.** In iterations 1 and 2 the blend was worse than its own best member. The cause was structural — a convex combination needs *negatively* correlated errors, and both branches were reading the same contaminated signal. Fixing the weights could never have worked; the data had to be separated first.
2. **Giving the model the nuisance variable is not the same as removing it.** Iteration 2 fed `W` to the trees and the manoeuvre noise became split candidates — the tabular MSE was 3.4x the BiLSTM's. Pruning (iteration 3) helped but was a heuristic over a symptom.
3. **The right move was a physical model, not a feature diet.** Iteration 4 asks the data a specific question — "how much of this sensor is explained by the flight regime?" — and subtracts the answer. That single change is worth 6.3 RMSE on the tabular branch.
4. **The accumulated cycle matters.** Iteration 3 dropped `cycle` when pruning, and the tabular branch lost its wear proxy. Iteration 4 reinstates it as `cyc_norm`, in the tabular features *and* as a channel of the recurrent input.
5. **A residual corrector over overfitted residuals cannot be validated.** In iteration 3 the grid search returned `alpha = 0.00` — a technical tie, because the corrector had been trained on the same overfitted residuals it was scored against. The lesson generalises to the `beta` selection still outstanding in iteration 4 (§6.3).

### Evidence behind the final design

| Probe | What it tested | Outcome | Adopted |
|---|---|---|---|
| `scripts/probe_q35.py` | quantile vs median vs L2 LightGBM recipes | The `alpha=0.35` recipe is confirmed and hard-coded in the notebook | Yes |
| `scripts/probe_cyclech.py` | BiLSTM with/without the normalised-cycle channel | `cyclech_s42` RMSE 5.447, R² 0.9150, NASA 3574.9 vs dual-pooling baseline 5.789 | Yes — but see the seed variance in §6.5 |
| `scripts/probe_variants2.py` | pooling variants on unit 16 | `dual_w32_u16_s42` RMSE 5.721, R² 0.9063, NASA 3297.6 | Yes — width 64, triple pooling |
| `scripts/probe_variants.log` | which unit to hold out | unit 16: RMSE 5.789 / NASA 3211.4 vs unit 20: 7.113 and 7.838 | Yes — unit 16 |
| `scripts/verify_blend.py` | the EMA + blend construction over saved prediction arrays | Confirms the blend and smoothing behaviour | Yes |

---

## 6. Technical audit and known limitations

Everything in this section was verified against the current files, not inferred.

### 6.1 The persisted ensemble cannot be loaded outside the notebook — **blocking**

`HybridStackingEnsemble` and `SensorResidualizer` are defined **inside the notebook** (cell 11), so `joblib.dump` records them as `__main__.HybridStackingEnsemble` and `__main__.SensorResidualizer`.

Verified by loading the shipped artefact in a clean process, on both interpreters present on this machine:

```
AttributeError: Can't get attribute 'HybridStackingEnsemble' on <module '__main__'>
```

- Python 3.12.10 (`.venv`) — fails
- Python 3.10.0 (the notebook's kernel) — fails

Raw-pickle reference counts inside `ensemble.joblib`: `__main__` × 1, `HybridStackingEnsemble` × 1, `SensorResidualizer` × 1, `keras` × 86, `lambda` × 15, `ds02_ensemble` × 0.

**Remediation.** Extract the classes into an importable module and re-persist the artefact so the pickle records a module-qualified name. A previous attempt at exactly this existed — `__pycache__/ds02_ensemble.cpython-312.pyc` (compiled 2026-10-19 22:07) contains `causal_ema_by_unit`, `SensorResidualizer` and `HybridStackingEnsemble` with the same signatures, and its module docstring states the intent: *"Kept in a module (instead of inside the notebook) so `ensemble.joblib` can be loaded from any process, not only from the notebook kernel that trained it."* **The `.py` source is gone** (§6.7) and the shipped artefact was written at 22:05, i.e. *before* the module existed, so it does not reference it.

### 6.2 The Keras `Lambda` binds the artefact to one Python minor version — **blocking for deployment**

```python
layers.Lambda(lambda z: z[:, -1, :], name="last_step")
```

Keras serialises a bare `Lambda` as **marshalled Python bytecode**, and `marshal`'s code-object format is version-specific. The consequence is not theoretical — it was reproduced on the shipped artefact, with the `__main__` dependency shimmed away so that this is the *only* remaining obstacle:

| Interpreter | Result |
|---|---|
| **Python 3.10.0** (the kernel that trained it) | Loads. The full ensemble is reconstructed and every fitted object is readable. |
| **Python 3.12.10** (the repository `.venv`) | **Fails** — `ValueError: bad marshal data (unknown type code)` |

The failing frame is unambiguous:

```
File "keras/src/layers/core/lambda_layer.py", line 202, in from_config
    fn = python_utils.func_load(
File "keras/src/utils/python_utils.py", line 95, in func_load
    code = marshal.loads(raw_code)
ValueError: bad marshal data (unknown type code)
```

So the artefact has **two independent** portability failures, stacked on top of each other:

1. it references `__main__` (§6.1), and
2. even once that is shimmed, the `Lambda`'s bytecode cannot cross a Python minor-version boundary.

Together they mean `ensemble.joblib` is loadable **only** by Python 3.10 *and* only by a process that has already defined `HybridStackingEnsemble` and `SensorResidualizer` in `__main__`. The repository's own virtualenv is Python 3.12, so the artefact is not loadable in the environment the project ships.

The same artefact also embeds the Keras model **inside** the `joblib` pickle rather than in the native `.keras` format, and there is no separate `.keras`/`.h5` file for the DS02 network at all (the `.h5` files under `models/` all belong to the FD001 pipeline).

**Remediation.** Replace the `Lambda` with a layer that serialises by value — `keras.ops.slice(x, (None, -1, None))` wrapped in a small `@keras.saving.register_keras_serializable` function, or an equivalent native op — and persist the network separately as `bilstm_ds02.keras`, referenced by the ensemble rather than embedded in it. The acceptance check must be a **round-trip across interpreters**, not a round-trip inside one: load the artefact under a different Python minor version than the one that wrote it.

#### 6.2.1 The remediation is proven, and it does **not** require retraining

The failure lives entirely in the **serialisation** of the graph, not in the model. The weights are architecture-independent, so the artefact can be re-packaged losslessly. This was demonstrated end to end, with **zero gradient steps**:

| Step | Interpreter | Result |
|---|---|---|
| 1. Extract the 20 weight arrays and the fitted scikit-learn / LightGBM objects from the 3.10 artefact | 3.10 | Done — no training involved |
| 2. Rebuild the graph with a registered, Lambda-free `LastStepPooling` layer and `set_weights(...)` | 3.12 | 154 253 params, **no `Lambda` in the graph** |
| 3. Compare the BiLSTM branch against the 3.10 reference on a fixed input | 3.12 vs 3.10 | `48.41839` vs `48.41839` — **max abs diff `0.000e+00`** |
| 4. Rebuild the ensemble object with module-qualified classes and re-pickle | 3.12 | `__main__` references in the pickle: **0**; `ds02_classes` references: 2 |
| 5. Compare the **full ensemble** against the 3.10 reference | 3.12 vs 3.10 | `13.34583435` vs `13.34583435` — **max abs diff `0.000e+00`** |
| 6. Save the network natively | 3.12 | `bilstm_ds02.keras`, 670 KB |
| 7. Load the re-packaged artefact in a **fresh 3.12 process with no shims** | 3.12 | `joblib.load` → `ds02_classes.HybridStackingEnsemble`; `load_model` → 154 253 params, no `Lambda`; prediction identical |

Two consequences worth being explicit about:

- **Re-packaging fixes deployability, not statistical honesty.** `opt_beta = 1.00` is still selected in-sample (§6.3) and the results are still single-seed (§6.5). Those need a genuine re-run.
- The re-packaged artefact is written by Python 3.12's scikit-learn 1.9.1, so it carries **no** estimator version skew. The original carries an `InconsistentVersionWarning` (1.5.1 → 1.9.1) that the re-packaging eliminates.

The one check that still needs the real data pipeline is the notebook's own `61.25` vs `58.00` sample assertion, which requires `X_test_raw[:1]`. Persisting that window alongside the manifest closes the loop.

### 6.3 The `beta` shrinkage is selected in-sample — **correctness**

`ridge_meta` and `lgb_meta` are fit on the unit-16 rows, and the `beta` grid is then scored on **those same rows**. The recorded validation RMSE at `beta = 1.00` is 0.308 against the BiLSTM's 4.221 — the meta-learner is scoring its own training data.

Consequences:

- The selected `beta = 1.00` expresses full trust in a meta-learner that was never validated out of sample.
- The "out-of-sample stacking" property holds for the **base models** (they never saw unit 16), but **not** for the `beta` selection.
- The test-set result (RMSE 5.522, NASA 3435.1) is still a genuine out-of-sample number — the test units were never touched by any fit or selection. The defect degrades the *choice* of `beta`, not the honesty of the test score.

**Remediation.** Select `beta` by grouped cross-validation over the **fit units** (2, 5, 10, 18, 20) using out-of-fold base predictions, or by a nested split inside unit 16. Report the spread of the selected `beta` rather than a single value.

### 6.4 The scaler and the residualisation models are fit on all six dev units — **documented, no test leakage**

`scaler`, `scaler_w`, `poly_w`, the 14 Ridge models and `res_scaler` are all fit on the **complete dev set — units 2, 5, 10, 18, 20 and 16 — before the unit-16 split is applied** (notebook cell 5, lines preceding the partition in cell 7).

| Question | Answer |
|---|---|
| Do these objects ever see an RUL label? | **No.** Every one of them is an unsupervised transform. |
| Do they ever touch the test units 11, 14, 15? | **No.** The test partition is loaded separately and never enters any fit. |
| Is there leakage onto the test set? | **No.** |
| Is the unit-16 holdout fully clean? | **Not entirely.** Unit 16 contributed to the scaler and residualiser statistics, so the unit-16 validation metrics are mildly optimistic — and `beta` is selected on exactly those metrics. |

This is a deliberate, defensible choice: the transforms are label-free, and excluding unit 16 from the scaler would make the production inference path inconsistent with the training one for no leakage benefit. But it must be stated, because "the holdout is clean" is exactly the kind of claim a reader should be able to check, and because it is the same holdout that `beta` is tuned on.

**Remediation (optional, low priority).** Either fit the unsupervised transforms on the five fit units only, or state the transductive choice in the artefact manifest so a consumer knows the scaler saw unit 16.

### 6.5 Seed variance is larger than most of the reported gains — **reproducibility**

The BiLSTM is the champion and the source of most of the accuracy, and it is not stable across seeds:

| Run | RMSE | R² | NASA |
|---|---|---|---|
| `cyclech_s42` | 5.447 | 0.9150 | 3574.9 |
| `cyclech_s7` | 6.564 | 0.8766 | 4956.2 |
| `dual_u16_s7` | 6.549 | — | 3875.6 |
| `dual_w32_u16_s42` | 5.721 | 0.9063 | 3297.6 |

A ~1.1 RMSE / ~1 400 NASA swing between seeds 42 and 7 is **larger than the entire claimed ensemble improvement** over the BiLSTM alone (5.693 → 5.522 RMSE, 3 822.2 → 3 435.1 NASA). Every number in this document comes from a single seed, `SEED = 42`.

**Remediation.** Report mean ± standard deviation over at least three seeds before any claim of improvement is made about a change smaller than the seed spread. This is a hard gate on the production-hardening change, not a nice-to-have.

### 6.6 The executed artefact and the repository environment disagree — **reproducibility**

| | Notebook execution environment | Repository `.venv` |
|---|---|---|
| Python | 3.10.0 (system) | 3.12.10 |
| TensorFlow | 2.21.0 | 2.21.0 |
| LightGBM | **4.6.0** | **4.7.0** |
| scikit-learn | **1.5.1** | **1.9.1** |
| numpy / pandas | — | 2.5.4 / 3.0.6 |

**Root cause, and it is not a code bug.** There is **no kernelspec registered for the `.venv`** on this machine:

```
C:\Users\mikel\AppData\Roaming\jupyter\kernels\
  ai4beg  bigapi  fraud-detector  ml-beginners  pia  smartstore-os  streamlit
```

The only `python3` kernelspec available is the one shipped with the *system* Python 3.10
(`…\Python310\share\jupyter\kernels\python3`). So whatever kernel the notebook asks for resolves
to **Python 3.10**, never to the virtualenv. The DS02 notebook carries **no `kernelspec` at
all** and its own `language_info.version` records `3.10.0` — the notebook documented the truth
about itself. The FD001 notebook is worse: its `kernelspec.display_name` reads
`.venv (3.12.10)` while its `kernelspec.name` is `python3`, so the **label lies** and the
resolution still lands on 3.10.

The consequence is that the project has never been able to run its notebooks in its own
environment, which is the upstream cause of the version skew above and of the `.keras` /
interpreter-binding failure in §6.2.

**Remediation.** Register the virtualenv as a kernel and point the notebooks at it by name:

```powershell
& .\.venv\Scripts\python.exe -m ipykernel install --user --name ds02-venv --display-name ".venv (3.12.10)"
```

then set `kernelspec.name` to `ds02-venv` in both notebooks. The misleading `display_name` on
the FD001 notebook must be corrected at the same time, otherwise the next reader repeats the
same false assumption.

### 6.7 A lost module and no version control — **process risk**

`__pycache__/ds02_ensemble.cpython-312.pyc` was compiled on 2026-10-19 at 22:07:22 from `C:\Users\mikel\Desktop\Pruebas\nasa\ds02_ensemble.py`. That file **no longer exists**, and no copy exists anywhere under `C:\Users\mikel`. The repository is **not** a git repository.

The work is recoverable from the bytecode — a sourceless `.pyc` can still be imported — but it is not maintainable and it must be rewritten properly rather than decompiled. The loss is the same class of problem as §6.1: a module was created to make the artefact loadable, and the module is exactly what disappeared.

**Remediation.** Put the repository under version control before doing any further work on the pipeline, and treat the extraction in §6.1 as the first committed change.

### 6.8 Two latent traps in the inference API

- **`units=None` silently disables per-unit smoothing.** `HybridStackingEnsemble.predict(X_raw_windows, cycles, units=None)` substitutes a single pseudo-unit when `units` is omitted, which collapses the whole batch into one EMA series. The EMA then smooths across unrelated engines instead of within each engine, producing plausible-looking but wrong numbers. The argument must become mandatory in the deployable API.
- **`scaler_w` is persisted but never used at inference.** The inference path derives the `W` block from the global 18-column `scaler` (`X_scaled[:, :, :n_op]`), while `poly_w` was fit on `scaler_w`-normalised `W`. The two are **numerically identical** — a `StandardScaler` computes per-column statistics, so both produce the same means and scales — so this is redundancy, not a defect. It is still a trap: a maintainer who "fixes" the inference path to use `scaler_w` would change nothing, and one who assumes the current code uses it would misread the whole residualisation stage.

### 6.9 Compute budget

The pipeline is CPU-only (TensorFlow reports no GPU on native Windows). Recorded cost: LightGBM 0.48 s; BiLSTM 147.99 s for 11 epochs. The probe history contains at least one **compute-starved** run in which a single epoch took 1 553 s, and `scripts/probe_variants2.py` was truncated for the same reason. Comparisons across runs with different wall-clock budgets are therefore not valid, and a starved run must be flagged rather than silently compared.

### 6.10 Misleading window naming

`WINDOW_SIZE = 50` and the phrase *"50 ciclos"* in the code comments describe **50 samples of the 100x-down-sampled series**, which is roughly **0.44 flight cycles** of engine life (§3.1). Any future change that reasons about "how much history does the model see" from the name alone will be wrong by two orders of magnitude, and the same wording is repeated in the notebook's own conclusions cell.

**Remediation.** Rename to `WINDOW_SAMPLES` (or `SAMPLED_POINTS_PER_WINDOW`) and state the equivalent flight-cycle reach in the docstring, so the temporal horizon is explicit rather than implied by a misleading integer.

### 6.11 Summary of debt

| # | Issue | Severity | Blocks deployment? | Tracked in |
|---|---|---|---|---|
| 6.1 | `ensemble.joblib` unloadable outside the notebook | High | Yes | OpenSpec change, phase 1 |
| 6.2 | Keras `Lambda` binds the artefact to one Python minor version | Reproduced: loads on 3.10, `ValueError: bad marshal data` on 3.12 | Yes | OpenSpec change, phase 2 |
| 6.3 | `beta` selected in-sample | High | No (test score is honest) | OpenSpec change, phase 3 |
| 6.4 | Unsupervised transforms fit on all six dev units | Low | No | Documented here; OpenSpec delta |
| 6.5 | Single-seed results | High | No | OpenSpec change, phase 4 |
| 6.6 | Execution environment ≠ repository environment | Medium | No | OpenSpec change, phase 4 |
| 6.7 | Lost module, no version control | High | No | OpenSpec change, phase 0 |
| 6.8 | `units=None` trap; redundant `scaler_w` | Medium | No | OpenSpec change, phases 1 and 5 |
| 6.9 | Compute starvation invalidates cross-run comparison | Medium | No | OpenSpec change, phase 4 |
| 6.10 | `WINDOW_SIZE = 50` misrepresents the temporal horizon | Low | No | Documented here |
| 6.11 | Silent FD001 fallback can overwrite the artefact with a different dataset | `load_rul_dataset()` falls back to C-MAPSS text files and writes to the same `ensemble.joblib` with the same `paradigm` string | No | OpenSpec change, phase 2 (manifest) |

---

## 7. Reproduction guide

```powershell
# 1. Regenerate the notebook from its builder. Never hand-edit the .ipynb.
& .\.venv\Scripts\python.exe scripts\build_02_notebook.py

# 2. Execute it (all 8 code cells, ~3 min on CPU)
& .\.venv\Scripts\jupyter.exe nbconvert --to notebook --execute `
    02_DS02_ensemble_RUL.ipynb --output 02_DS02_ensemble_RUL.executed.ipynb

# 3. Artefacts land at the repo root and under models/
Get-ChildItem ensemble.joblib, scaler.joblib, models\ensemble.joblib, models\scaler.joblib
```

> The recorded outputs in the committed notebook were produced under **Python 3.10**, not under `.venv` (§6.6). Re-running under `.venv` is the first step of the reproducibility remediation and may shift the metrics slightly.

**Inputs required**

| Input | Path | Size |
|---|---|---|
| DS02 dataset | `archive/CCMaps/N-CMAPSS_DS02-006.h5` | 2.34 GB |
| FD001 fallback (optional) | `archive/CMaps/train_FD001.txt`, `test_FD001.txt`, `RUL_FD001.txt` | small |

**Notebooks are generated, not authored.** `scripts/build_02_notebook.py` (754 lines) is a pure `nbformat` builder: it emits the 8 code cells and 9 markdown cells as verbatim triple-quoted strings and writes the `.ipynb`. It does not execute the notebook and does not read or write any artefact. Any edit to the notebook's content belongs in the builder.

---

## 8. Artefact inventory

| Path | Size | Role | Produced by |
|---|---|---|---|
| `02_DS02_ensemble_RUL.ipynb` | 1.20 MB | The pipeline, 17 cells, all code cells executed | `scripts/build_02_notebook.py` |
| `scripts/build_02_notebook.py` | 31.7 KB | Notebook generator (source of truth) | hand-written |
| `ensemble.joblib` | 2.35 MB | Trained hybrid ensemble — **currently unloadable outside the notebook** | notebook cell 15 |
| `scaler.joblib` | 1.0 KB | 18-channel `StandardScaler` | notebook cell 15 |
| `models/ensemble.joblib`, `models/scaler.joblib` | — | Copies of the two above | notebook cell 15 |
| `archive/CCMaps/N-CMAPSS_DS02-006.h5` | 2.34 GB | Source dataset | — |
| `scripts/probe_q35.py` | 3.4 KB | Quantile-objective experiment | — |
| `scripts/probe_cyclech.py` | 3.3 KB | Cycle-channel experiment | — |
| `scripts/probe_variants2.py` | 3.2 KB | Pooling-variant experiment | — |
| `scripts/verify_blend.py` | 2.2 KB | Blend + EMA verification over saved predictions | — |
| `scripts/pred_cyclech_s42.npy`, `pred_dual_*.npy`, `pred_lgb_q35.npy` | 24–49 KB | Saved prediction arrays reused by the probes | probes |
| `__pycache__/ds02_ensemble.cpython-312.pyc` | 7.4 KB | **Orphaned bytecode** of the lost extraction module | §6.7 |

---

## 9. Open items

| # | Item | Why it matters |
|---|---|---|
| 1 | Put the repository under version control | A source file was already lost (§6.7); there is no rollback |
| 2 | Extract the inference classes into a module and re-persist | The artefact cannot be loaded at all today (§6.1) |
| 3 | Replace the `Lambda` pooling and persist a native `.keras` | Required for a stable, version-independent deployment artefact (§6.2) |
| 4 | Select `beta` out-of-sample | The current value is chosen on the meta-learner's own training rows (§6.3) |
| 5 | Re-run the whole pipeline over ≥ 3 seeds and report mean ± std | The seed spread exceeds the reported ensemble gain (§6.5) |
| 6 | Pin the execution environment and re-run inside it | The recorded metrics were produced under a different interpreter and library set (§6.6) |
| 7 | Measure the branch error complementarity | The whole stacking layer rests on an inference, not a measurement (ADR-004) |
| 8 | Make `units` mandatory in the inference API | `units=None` silently disables per-unit smoothing (§6.8) |
| 9 | Expose a DS02 inference entry point | `scripts/predict.py` serves the FD001 v3 bundle and is unrelated to this pipeline |
