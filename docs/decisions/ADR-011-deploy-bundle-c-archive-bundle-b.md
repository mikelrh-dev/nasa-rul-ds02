# ADR-011: Deploy bundle C as the single champion; archive bundle B

## Status

Accepted — deployed 2026-11-04 on branch `clase-modelo-c`.

## Date

2026-11-04

## Context

Two bundles coexisted in the repository:

- **B** — hybrid (BiLSTM + LightGBM + stacking + causal EMA) trained on the clean
  HDF5, `models/`, RMSE 4.251 / NASA 2305.1 on the 6.196 test windows.
- **C** — the same pipeline trained on the imputed base (MAR T30 dropout handled
  with a physical pattern + causal ffill using fit-unit medians), deployed from
  `src/clase/models/`, RMSE 4.338 / NASA 2336.2 (seed 42), multiseed 4.368 ± 0.053.

The class deliverable is defended as **one** model. The rubric asks for missing
values handled with criteria and for the presented model to be the explained one.
Keeping B as champion meant defending a model that does not use the imputation
the coursework builds, and leaving the class bundle as a "losing experiment" in a
subdirectory.

Both artifacts already existed and their SHA-256 matched their own manifest when
the decision was taken (verified 2026-11-04). Nothing is retrained by this ADR.

## Decision

Deploy C and only C. **R6=C (manifest 4.338 manda)** — the manifest
(`models/ds02_manifest.json`, RMSE 4.338, seed 42) is the authoritative
reference for the deployed bundle; bundle B is archived, not champion.

1. `models/` holds the C bundle (`ensemble.joblib`, `bilstm_ds02.keras`,
   `scaler.joblib`, `ds02_manifest.json`). Its manifest declares
   `dataset: "DS02"` plus `dataset_variant` naming the imputed base, and records B
   under `historical_reference` so the comparison stays auditable.
2. The B artifacts (`ensemble.joblib`, `bilstm_ds02.keras`, `scaler.joblib`,
   `ds02_manifest.json`) are preserved in `archive/models_b/`; the B evidence
   chain (`notebooks/ds02_ensemble/`, `scripts/build_02_notebook.py`,
   `src/clase/evaluar_b_en_adaptada.py`, `tests/test_clase_b_robusto.py`) moves to
   `archive/` rather than being deleted.
3. `src/clase/train_ensemble_adaptado.py` writes to `models/`, and
   `src/clase/evaluar_c_multisemilla.py` replaces the B-under-dropout evaluator.
4. `scripts/build_ui_cache.py` builds from the imputed base by default
   (`--base adaptada`), so the app shows the population the manifest signs;
   `--base limpia` keeps the historical path.

## Consequences

- **Measured cost, stated plainly.** On the same 6.196 windows C is +0.087 RMSE and
  +31.1 NASA above B. The multiseed band of C (4.368 ± 0.053) is the noise floor
  that any future comparison must respect.
- **The manifest is the truth, not a run.** TensorFlow on CPU is not bit
  deterministic; re-running the training can move the headline figure (4.229 and
  4.338 were both observed for the same code). Re-running to "get the good number"
  would be selecting a measurement, not measuring.
- **Rules band still calibrated on B (estado en 2026-11-04).** `src/mia/calibracion_banda.json` was fitted on
  B's OOF rows; recalibrating it requires C OOF and is out of scope here. Declared
  as a known limitation.
- **Addendum posterior:** `src/mia/calibracion_banda.json#procedencia` declara recalibración sobre bundle C adaptada (14 915 filas OOF puras step-3, R2b PAVA causal, `nb2_selection.joblib`). Si esa recalibración es vigente, sustituye al punto anterior; ver `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md`.
- **Cache must be regenerated** (`python scripts/build_ui_cache.py`) before the app
  loads: `load_ensemble` checks the bundle hash against
  `app/cache/cache_manifest.json`, which still signs the previous ensemble.
- The notebooks 03–06 read the deployed bundle through `src/clase/puente_c.py`,
  which rebuilds the windows and never trains.

## Alternatives considered

- **Keep B as champion (status quo).** Rejected: the defended model would not be
  the model the coursework builds, and the class bundle would be presented as a
  loser while being the one explained on every slide.
- **Retrain C and re-manifest whatever comes out.** Rejected: the result would be
  chosen for its number (4.229 passes a 4.25 threshold, 4.338 does not) instead of
  being measured once. It also invalidates the existing artifacts whose hashes
  match.
- **Ship both as co-champions.** Rejected: two champions is no champion; the app,
  the rules layer and the cache can only sign one bundle.
- **Delete the B code instead of archiving it.** Rejected: the comparison in
  ADR-010-era documents and in `historical_reference` cites those numbers; keeping
  the code makes the historical claim checkable.

## Verification

- `models/ds02_manifest.json`: `dataset == "DS02"`, `dataset_variant` set,
  `historical_reference` populated; `artifacts.ensemble_sha256` and
  `artifacts.bilstm_sha256` recomputed and matching the installed files.
- `pytest tests/test_artifact_contract.py` green against the C bundle.
- No active `.py` or `.ipynb` references `notebooks/ds02_ensemble/` or
  `src/clase/models/` as a production path.

## Rollback

Restore the four files from `archive/models_b/` into `models/`, restore the
archived notebook chain, and regenerate `app/cache/`; the repository returns to
the pre-decision state without re-training anything.
