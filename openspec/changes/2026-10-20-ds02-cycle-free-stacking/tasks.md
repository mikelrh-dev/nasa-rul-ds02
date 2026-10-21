# Tasks: remove the cycle counter from the stacking layer

**Change:** `2026-10-20-ds02-cycle-free-stacking`
**Status:** Implemented
**Spec:** [spec.md](spec.md) · [proposal](proposal.md)

| # | Task | Status | Acceptance check |
| --- | --- | --- | --- |
| 1.1 | Drop `hold_cycles / 100.0` from `Z_hold` in the builder (cell 8) | Done | `Z_hold = np.column_stack([result['p_lstm_hold'], result['p_lgb_hold']])` |
| 1.2 | Drop the cycle column from `Zs` in the three-seed sweep (cell 11) | Done | `Zs = np.column_stack([out['p_lstm_hold'], out['p_lgb_hold']])` |
| 1.3 | `select_beta_grouped(..., use_cycle_feature=False)` (cell 7) | Done | selection and artefact share the two-column design |
| 1.4 | `build_manifest` records `meta_features` in `model_shape` and `inference_contract` | Done | `models/ds02_manifest.json` has both fields, value `2` |
| 1.5 | Keep `hold_cycles` computed in the builder so the removal stays auditable | Done | variable still assigned, unused by `Z_hold` |
| 2.1 | Regenerate the notebook from the builder | Done | `python scripts/build_02_notebook.py` → 34 cells |
| 2.2 | Execute the notebook end to end and keep the outputs | Done | all 20 code cells executed; artifacts rewritten at 16:14 |
| 2.3 | Contract tests still pass | Done | `pytest tests -q` → 10 passed |
| 3.1 | Reload check: `n_features_in_ == 2`, weights split across both branches | Done | `ridge_meta.n_features_in_ == 2`, coef `[0.1205, 0.7923]`, importances `[148, 572]` |
| 3.2 | Reload check: `load_ensemble` in a clean process, bit-identical predictions | Done | `[RELOAD OK]` and `reloaded == in-memory: True` |
| 4.1 | Update the deployed spec (`openspec/specs/.../spec.md`) | Done | meta-features requirement and the two scenarios rewritten |
| 4.2 | Update `docs/02_DS02_ensemble_RUL_spec.md` §1, §6, §7, §8, §9 | Done | §6.12 added; §8/§9 closed; metrics refreshed |
| 4.3 | Update `README.md` metrics, ablation and interface output | Done | headline table, ablation section, `60.21` CLI output |
| 5.1 | Delete the temporary audit scripts and logs | Done | `scripts/_*.py`, `models/_meta_cycle_fix_seeds.*`, `VERIFICACION_meta_cycle_fix.md` |

## Deviations from the original plan

| Planned | Actual | Reason |
| --- | --- | --- |
| Edit `VERIFICACION_meta_cycle_fix.md` to correct the `4.317` figure | Deleted instead | The user superseded the audit document; the real numbers come from the regenerated notebook (`4.230` at seed 42, `4.301 ± 0.068` over three seeds) |
| Re-run `scripts/_verify_meta_cycle_fix_seeds_v2.py` for the seed spread | Not run | The notebook's own three-seed cell already measures it; a separate script would duplicate the BiLSTM fits for no extra information |
| One-line fix | Three call sites plus a manifest field | `ensemble.py` was already width-agnostic, so `predict()` needed no change; the training-time design lived in the builder |
