# Proposal: Cerrar contratos de documentación y rúbrica (sin n8n)

**Change:** `2026-11-15-rubrica-contratos-docs`
**Branch:** `refactor/estructura-ds02-clase-2026-11-10`
**Date:** 2026-11-15
**Capability:** `rul-prediction-ds02` (MODIFIED + ADDED requirements)
**Deployed spec:** `openspec/specs/rul-prediction-ds02/spec.md`

## Intent

The 2026-11-15 rubric audit found that the repository no longer matches its own
published documentation and its own test contracts:

1. The deployed requirement `Multiseed evidence reconciliation` orders citations of
   `4.368 ± 0.053` and seeds `7=4.429 / 123=4.336`, which do not match the current
   CSV (`4.371 / 4.291`) nor the vigente aggregation (`4.333 ± 0.040`).
2. `README.md` lost the rubric anchors for SAA-1/SAA-2 ("IA débil" vs strong AI,
   supervised vs unsupervised) and the model table has no training-time column.
3. Documented thresholds read `30/25` while the code and ADR-013 say `25/20`.
4. `notebooks/00_datos.ipynb` breaks the notebook instrumentation contract, leaving
   the suite red (495 passed / 3 failed) and `verify_gate.py` failing.
5. `pyarrow` is imported by `src/clase/dataset_clase.py` but not pinned.
6. `e00-cifras-autoritativas.md` and `src/clase/README.md` carry stale figures and
   dead paths.

## Scope

### In Scope

- `README.md`: restore the "Qué hemos construido" anchors (weak AI vs strong AI,
  supervised vs unsupervised), add the training-time column, align thresholds to
  `25/20`, publish the current multiseed row set and the MLflow view command.
- `README.en.md`, `src/clase/README.md`, `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md` (local, gitignored):
  align the same figures and remove dead paths.
- `requirements.txt` + `pyproject.toml`: pin `pyarrow` to the installed version.
- `notebooks/00_datos.ipynb`: MLflow header in cell 0, TF variables before any TF
  import, live-log cell (`log_live_run`, `persist_timings`), no late TF variable.
- `tests/test_mlflow_live.py`: notebook count `7 -> 8`; new regression test
  `tests/test_rubrica_doc_contract.py` locking anchors, thresholds and pins.
- `openspec/specs/rul-prediction-ds02/spec.md`: MODIFIED multiseed requirement and
  ADDED documentation-contract requirements.

### Out of Scope

- Any change to `n8n/` flows, credentials, auth or the vault's "own action" claim
  (owner-led).
- MLflow `meta.yaml` normalisation and empty `artifacts/` `.gitkeep` (cosmetic).
- Retraining, re-running backfill, or changing any recorded metric or model artifact.
- Versioning `data/` (declared limitation only).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `rul-prediction-ds02`: replace the stale multiseed reconciliation requirement;
  add documentation-consistency requirements (anchors, thresholds, dependency pins,
  notebook instrumentation coverage).

## Approach

Documentation-first, with a RED-GREEN contract test that fails on the current tree
and passes after the edits. The notebook change copies the existing NB01 header and
live-log pattern; no cell is executed during the change. Model artifacts, metrics
and the MLflow store stay byte-identical.

## Affected Areas

| Area | Impact | Description |
|---|---|---|
| `README.md`, `README.en.md`, `src/clase/README.md` | Modified | Anchors, time column, thresholds, multiseed, dead paths |
| `MLProyectVault/50-Evidencia/e00-cifras-autoritativas.md` | Modified | Current CSV rows, coverage `0.901643`, thresholds |
| `requirements.txt`, `pyproject.toml` | Modified | Pin `pyarrow` |
| `notebooks/00_datos.ipynb` | Modified | Header, TF env, live-log cell (not executed) |
| `tests/test_mlflow_live.py`, `tests/test_rubrica_doc_contract.py` | Modified/New | Count 8; regression contract |
| `openspec/specs/rul-prediction-ds02/spec.md` | Modified | Multiseed + documentation contracts |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Editing the notebook breaks another contract | Low | Copy NB01's exact header/live-log pattern; run the full gate |
| Threshold alignment hides a real regime change | Low | Code and ADR-013 stay untouched; only docs move to `25/20` |
| Staging unrelated dirty files | Medium | Stage only the explicit paths of this change per commit |

## Rollback Plan

Each phase is one local commit; revert the offending commit (`git revert <sha>`)
individually. No artifact under `models/`, `mlruns/` or `data/` is written, so the
rollback cannot alter models, metrics or the store. All five model artifacts and the
manifest stay byte-compatible; the notebook remains executable but is not re-run.

## Dependencies

- Python 3.12 `.venv`, pytest, nbformat (already pinned).
- `MLFLOW_ALLOW_FILE_STORE=true` when starting the tracking server (documented).

## Success Criteria

- [ ] `python -m pytest tests -q` passes with zero failures (previously 3 failed).
- [ ] `python scripts/operativo/backfill_mlflow.py --check` exits 0 (17 runs).
- [ ] New contract test asserts README anchors, `25/20` consistency and the pyarrow pin.
- [ ] `git status --porcelain` shows no unexpected new/modified paths beyond this change.
